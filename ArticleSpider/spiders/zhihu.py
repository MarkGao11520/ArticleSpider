# -*- coding: utf-8 -*-
import json
import re

try:
    import urlparse as parse
except:
    from urllib import parse

import scrapy
from scrapy.loader import ItemLoader
from items import ZhihuAnswerItem, ZhihuQuestionItem


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']

    # question的第一页 answer url
    start_answer_url = 'https://www.zhihu.com/api/v4/questions/{0}/answers?sort_by=default&include=data%5B%2A%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B%2A%5D.mark_infos%5B%2A%5D.url%3Bdata%5B%2A%5D.author.follower_count%2Cbadge%5B%3F%28type%3Dbest_answerer%29%5D.topics&limit={1}&offset={2}'

    agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
    headers = {
        "HOST": "www.zhihu.com",
        "Referer": "https://www.zhihu.com",
        'User-Agent': agent
    }

    def parse(self, response):
        """
        提取出html页面中的所有url 并跟踪这些url进行一步爬取
        如果提取的url中格式伪/question/xx 就下载之后直接进入解析函数
        """

        all_urls = response.css("a::attr(href)").extract()
        all_urls = [parse.urljoin(response.url, url) for url in all_urls]
        all_urls = filter(lambda x: True if x.startswith("https") else False, all_urls)
        for url in all_urls:
            match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", url)
            if match_obj:
                # 如果提取到question相关的页面则下载后交由提取函数进行处理
                request_url = match_obj.group(1)
                yield scrapy.Request(request_url, headers=self.headers, callback=self.parse_question)
            else:
                # 如果不是question则直接进一步跟踪
                # pass
                yield scrapy.Request(url, headers=self.headers, callback=self.parse)

    def parse_question(self, response):
        # 处理question页面，从页面中提取出具体的question item
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

        yield scrapy.Request(self.start_answer_url.format(question_id, 20, 0),headers=self.headers, callback=self.parse_answer)
        yield question_item

    def parse_answer(self, response):
        # 处理question的answer
        ans_json = json.loads(response.text)
        is_end = ans_json["paging"]["is_end"]
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

            yield answer_item

        if not is_end:
            yield scrapy.Request(next_url, headers=self.headers, callback=self.parse_answer)

    def start_requests(self):
        # 入口
        return [scrapy.Request('https://www.zhihu.com/#signin', headers=self.headers, callback=self.login)]

    def login(self, response):
        match_obj = re.match('.*name="_xsrf" value="(.*?)"', response.text,re.DOTALL)
        xsrf = ''
        if match_obj:
            xsrf = (match_obj.group(1))
        if xsrf:
            post_data = {
                "_xsrf": xsrf,
                "phone_num": "17602686137",
                "password": "AIjd1314",
                "captcha": ""
            }
            import time
            t = str(int(time.time() * 1000))
            # captcha_url = "https://www.zhihu.com/captcha.gif?r={0}&type=login".format(t)
            captcha_url_cn = "https://www.zhihu.com/captcha.gif?r={0}&type=login&lang=cn".format(t)
            yield scrapy.Request(captcha_url_cn, headers=self.headers, meta={"post_data":post_data}, callback=self.login_after_captcha_cn)
            # yield scrapy.Request(captcha_url,headers=self.headers,meta={"post_data":post_data},callback=self.login_after_captcha)

    def login_after_captcha_cn(self,response):
        # 知乎倒立汉字验证码识别登录
        with open("captcha.jpg","wb") as f:
            f.write(response.body)
            f.closed

        from zheye import zheye
        z = zheye()
        positions = z.Recognize('captcha.jpg')

        pos_arr = []
        if len(positions) == 2:
            if positions[0][1] > positions[1][1]:
                pos_arr.append([positions[1][1],positions[1][0]])
                pos_arr.append([positions[0][1],positions[0][0]])
            else:
                pos_arr.append([positions[0][1],positions[0][0]])
                pos_arr.append([positions[1][1],positions[1][0]])
        else:
            pos_arr.append([positions[0][1], positions[0][0]])

        post_url = "https://www.zhihu.com/login/phone_num"
        post_data = response.meta.get("post_data",{})
        if len(positions) == 2:
            post_data["captcha"] = '{"img_size": [200,44],"input_points": [[%.2f,%f],[%.2f,%f]]}' % (
                pos_arr[0][0] / 2, pos_arr[0][1] / 2, pos_arr[1][0] / 2, pos_arr[1][1] / 2)
        else:
            post_data["captcha"] = '{"img_size": [200,44],"input_points": [[%.2f,%f]]}' % (
                pos_arr[0][0] / 2, pos_arr[0][1] / 2)
        post_data["captcha_type"] = "cn"

        return [scrapy.FormRequest(
            url=post_url,
            formdata=post_data,
            headers=self.headers,
            callback=self.check_login
        )]

    def login_after_captcha(self, respnse):
        pass

    def check_login(self, response):
        # 验证服务器的返回数据判断是否成功
        text_json = json.loads(response.text)
        if "msg" in text_json and text_json["msg"] == "登录成功":
            for url in self.start_urls:
                yield scrapy.Request(url, dont_filter=True, headers=self.headers)
