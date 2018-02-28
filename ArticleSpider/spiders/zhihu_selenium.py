# -*- coding: utf-8 -*-
import json
import re
import scrapy
import settings
import time

# 兼容python2和python3的版本
try:
    import urlparse as parse
except:
    from urllib import parse

from scrapy.loader import ItemLoader
from items import ZhihuAnswerItem, ZhihuQuestionItem
from selenium import webdriver
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals
from scrapy_redis.spiders import RedisSpider
from scrapy_redis.defaults import START_URLS_AS_SET
from scrapy_redis.utils import bytes_to_str
from zheye import zheye


# 知乎爬虫_使用selenium
class ZhihuSpider(RedisSpider):
    name = 'zhihu_selenium'
    allowed_domains = ['www.zhihu.com']
    redis_key = "zhihu:start_url"

    start_urls = ['https://www.zhihu.com']

    # question的回答分页列表的REST_API
    start_answer_url = 'https://www.zhihu.com/api/v4/questions/{' \
                       '0}/answers?sort_by=default&include=data%5B%2A%5D.is_normal%2Cadmin_closed_comment' \
                       '%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason' \
                       '%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent' \
                       '%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time' \
                       '%2Cupdated_time%2Creview_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author' \
                       '%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B%2A%5D.mark_infos%5B%2A%5D' \
                       '.url%3Bdata%5B%2A%5D.author.follower_count%2Cbadge%5B%3F%28type%3Dbest_answerer%29%5D.topics' \
                       '&limit={1}&offset={2} '

    # 请求头伪造
    headers = {
        "HOST": "www.zhihu.com",
        "Referer": "https://www.zhihu.com",
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0"
    }

    # 自定义配置
    custom_settings = {
        "AUTOTHROTTLE_ENABLED": True,
        "DOWNLOAD_DELAY": 0.8,
    }

    def __init__(self):
        self.browser = webdriver.Chrome(executable_path=settings.SELENIUM_DRIVER_PATH)
        super(ZhihuSpider, self).__init__()
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self):
        # 当爬虫退出的时候关闭chrome
        print("spider closed")
        self.browser.quit()

    # 深度优先遍历
    def parse(self, response):
        """
        提取出html页面中的所有url 并跟踪这些url进行一步爬取
        如果提取的url中格式伪/question/xx 就下载之后直接进入解析函数
        """

        # 获取所有a 标签 href属性
        all_urls = response.css("a::attr(href)").extract()
        # 组装绝对路径url
        all_urls = [parse.urljoin(response.url, url) for url in all_urls]
        # 去掉非https的url
        all_urls = filter(lambda x: True if x.startswith("https") else False, all_urls)
        # 遍历所有的url
        for url in all_urls:
            # 匹配问题url
            match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", url)
            if match_obj:
                # 如果提取到question相关的页面则下载后交由回答提取函数进行处理
                request_url = match_obj.group(1)
                yield scrapy.Request(request_url, headers=self.headers, callback=self.parse_question)
            else:
                # 如果不是question则直接进一步跟踪
                yield scrapy.Request(url, headers=self.headers, callback=self.parse)

    # 处理question页面，从页面中提取出具体的question item
    def parse_question(self, response):
        match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", response.url)
        if match_obj:
            question_id = int(match_obj.group(2))

        if "QuestionHeader-title" in response.text:
            # 处理新版本
            item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)
            item_loader.add_css("title", "h1.QuestionHeader-title::text")
            item_loader.add_css("content", ".QuestionHeader-detail")
            item_loader.add_value("url", response.url)
            item_loader.add_value("zhihu_id", question_id)
            item_loader.add_css("answer_num", ".List-headerText span::text")
            item_loader.add_css("comments_num", ".QuestionHeader-Comment button::text")
            item_loader.add_css("watch_user_num", ".NumberBoard-value::text")
            item_loader.add_css("topics", ".QuestionHeader-topics .Popover div::text")

            question_item = item_loader.load_item()
        else:
            # 处理知乎旧版本
            item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)
            item_loader.add_value("url", response.url)
            item_loader.add_value("zhihu_id", question_id)
            item_loader.add_xpath("title", "//*[@id='zh-question-title']/h2/a/text()|"
                                           "//*[@id='zh-question-title']/h2/a/text()")
            # item_loader.add_css("title",".zh-question-title h2 a::text")
            item_loader.add_css("content", "#zh-question-detail")
            item_loader.add_css("answer_num", "#zh-question-answer-num::text")
            item_loader.add_css("comments_num", "#zh-question-meta-wrap a[name='addcomment']::text")
            item_loader.add_xpath("watch_user_num", "//[@id='zh-question-side-header-wrap']/text()|"
                                                    "//[@class='zh-question-followers-sidebar']/div/a/strong/text()")
            # item_loader.add_css("watch_user_num","#zh-question-side-header-wrap::text")
            item_loader.add_css("topics", ".zm-tag-editor-labels a::text")

            question_item = item_loader.load_item()

        # 提取第一页回答列表，交给parse_answer
        yield scrapy.Request(self.start_answer_url.format(question_id, 20, 0),
                             headers=self.headers, callback=self.parse_answer)
        # 处理item
        yield question_item

    # 处理回答url
    def parse_answer(self, response):
        # 回答列表返回json结果，所以将字符串转换为json结构
        ans_json = json.loads(response.text)
        # 获取是否为最后一页
        is_end = ans_json["paging"]["is_end"]
        # 获取下一页url
        next_url = ans_json["paging"]["next"]

        # 提取answer字段
        for answer in ans_json["data"]:
            answer_item = ZhihuAnswerItem()
            answer_item["zhihu_id"] = answer["id"]
            answer_item["url"] = answer["url"]
            answer_item["question_id"] = answer["question"]["id"]
            answer_item["author_id"] = answer["author"]["id"] if "id" in answer["author"] else None
            answer_item["content"] = answer["content"] if "content" in answer else None
            answer_item["praise_num"] = answer["voteup_count"]
            answer_item["comments_num"] = answer["comment_count"]
            answer_item["create_time"] = answer["created_time"]
            answer_item["update_time"] = answer["updated_time"]
            # 处理item
            yield answer_item

        # 如果不是最后一页，则处理下一页
        if not is_end:
            yield scrapy.Request(next_url, headers=self.headers, callback=self.parse_answer)

    # spider的主入口
    def start_requests(self):
        cookie_dict = {}
        # 1.加载要操作的页面
        self.browser.get("https://www.zhihu.com/signin")

        # 2.登录操作
        self.browser.find_element_by_css_selector("input[name='username']").send_keys(settings.ZHIHU_PHONE_NUMBER)
        self.browser.find_element_by_css_selector("input[name='password']").send_keys(settings.ZHIHU_PASSWORD)
        self.browser.find_element_by_css_selector("button[type='submit']").click()

        # 3.等待browser处理完成
        time.sleep(2)

        # 4.将cookie写入字典
        for i in self.browser.get_cookies():
            cookie_dict[i["name"]] = i["value"]

        # browser.close()
        return self.next_request(cookie_dict)
        # return [scrapy.Request(url=self.start_urls[0], headers=self.headers, cookies=cookie_dict,
        # callback=self.parse)]

    # 登录成功后从redis中拿数据
    def next_request(self, cookie_dict):
        """Returns a request to be scheduled or none."""
        use_set = self.settings.getbool('REDIS_START_URLS_AS_SET', START_URLS_AS_SET)
        fetch_one = self.server.spop if use_set else self.server.lpop
        # XXX: Do we need to use a timeout here?
        found = 0
        # TODO: Use redis pipeline execution.
        while found < self.redis_batch_size:
            data = fetch_one(self.redis_key)
            if not data:
                # Queue empty.
                break
            req = self.make_request_from_data(data)
            if req:
                url = bytes_to_str(data, self.redis_encoding)
                yield [scrapy.Request(url=url, headers=self.headers, cookies=cookie_dict, callback=self.parse)]
                found += 1
            else:
                self.logger.debug("Request not made from data: %r", data)

        if found:
            self.logger.debug("Read %s requests from '%s'", found, self.redis_key)

        if found:
            self.logger.debug("Read %s requests from '%s'", found, self.redis_key)
