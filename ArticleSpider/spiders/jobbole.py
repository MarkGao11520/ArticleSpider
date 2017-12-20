# -*- coding: utf-8 -*-
#  re_selector = response.xpath("/html/body/div[1]/div[3]/div[1]/div[1]/h1")
#  re2_selector = response.xpath('//*[@id="post-88673"]/div[1]/h1/text()')
# import re
# import datetime

import scrapy
from scrapy.http import Request
from urllib import parse

from items import JobBoleArticleItem, ArticleItemLoader
from scrapy.xlib.pydispatch import dispatcher
from utils.common import get_md5
from scrapy import signals


class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['blog.jobbole.com']
    start_urls = ['http://blog.jobbole.com/all-posts/']

    # 收集伯乐在线所有404的url以及404页面数
    handle_httpstatus_list = [404]

    def __init__(self):
        self.fail_urls = []
        dispatcher.connect(self.handle_spider_closed, signals.spider_closed)

    def handle_spider_closed(self, spider):
        self.crawler.stats.set_value("failed_urls", ",".join(self.fail_urls))

    def parse(self, response):
        """
        1.获取文字页表类中的文章url并交给解析函数进行具体字段的解析
        2.获取下一页的url并交给scrapy进行下载，下载完成后交给parse
        """

        # 解析列表页中的所有文章url并交给scrapy 下载后并进行解析
        if response.status == 404:
            self.fail_urls.append(response.url)
            self.crawler.stats.inc_value("failed_url")

        post_nodes = response.css("#archive .floated-thumb .post-thumb a")
        for post_node in post_nodes:
            image_url = post_node.css("img::attr(src)").extract_first("")
            post_url = post_node.css("::attr(href)").extract_first("")
            yield Request(url=parse.urljoin(response.url,post_url),meta={"front_image_url":image_url},callback=self.parse_detail)

        #提取下一页并交给scrapy进行下载
        next_url = response.css(".next.page-numbers::attr(href)").extract_first("")
        if next_url:
            yield Request(url=parse.urljoin(response.url,next_url),callback=self.parse)

    def parse_detail(self,response):
        # article_item = JobBoleArticleItem()
        # # 提取文字的具体字段
        #
        # # 通过xpath提取字段
        # # title = response.xpath('//div[@class="entry-header"]/h1/text()').extract_first("")
        # # create_date = response.xpath("//p[@class='entry-meta-hide-on-mobile']/text()").extract_first("").strip().replace("·","").strip();
        # # praise_numbers = response.xpath("//span[contains(@class,'vote-post-up')]/h10/text()").extract_first("");
        # # fav_nums = response.xpath("//span[contains(@class,'bookmark-btn')]/text()").extract_first("");
        # # match_re = re.match(".*?(\d+).*", fav_nums)
        # # if match_re:
        # #     fav_nums = match_re.group(1)
        # # comment_nums = response.xpath("//a[@href='#article-comment']/span/text()").extract_first("");
        # # match_re = re.match(".*?(\d+).*", comment_nums)
        # # if match_re:
        # #     comment_nums = match_re.group(1)
        # # content = response.xpath("//div[@class='entry']").extract_first("")
        # # tag_list = response.xpath("//p[@class='entry-meta-hide-on-mobile']/a/text()").extract()
        # # tag_list = [element for element in tag_list if not element.strip().endswith("评论")]
        # # tags = ",".join(tag_list)
        #
        # # 通过css选择器提取字段
        # title = response.css(".entry-header h1::text").extract_first("")
        # create_date = response.css("p.entry-meta-hide-on-mobile::text").extract_first("").strip().replace("·","").strip()
        # praise_nums = response.css(".vote-post-up h10::text").extract_first("")
        # fav_nums = response.css(".bookmark-btn::text").extract_first("")
        # match_re = re.match(".*?(\d+).*",fav_nums)
        # if match_re:
        #     fav_nums = int(match_re.group(1))
        # else:
        #     fav_nums = 0
        # comment_nums = response.css("a[href='#article-comment'] span::text").extract_first("")
        # match_re = re.match(".*?(\d+).*", comment_nums)
        # if match_re:
        #     comment_nums = int(match_re.group(1))
        # else:
        #     comment_nums = 0
        # content = response.css("div.entry").extract_first("")
        # tag_list = response.css("p.entry-meta-hide-on-mobile a::text").extract()
        # tag_list = [element for  element in tag_list if not element.strip().endswith("评论")]
        # tags = ",".join(tag_list)
        #
        # article_item["url_object_id"] = get_md5(response.url)
        # article_item["title"] = title
        # article_item["url"] = response.url
        # try:
        #     create_date = datetime.datetime.strptime(create_date,"%Y/%m/%d").date()
        # except Exception as e:
        #     create_date = datetime.datetime.now()
        # article_item["create_date"] = create_date
        # article_item["front_image_url"] = [front_image_url]
        # article_item["praise_nums"] = praise_nums
        # article_item["common_nums"] = comment_nums
        # article_item["fav_nums"] = fav_nums
        # article_item["tags"] = tags
        # article_item["content"] = content

        # 通过item Loader加载item
        front_image_url = response.meta.get("front_image_url","")  # 文章封面图
        item_loader = ArticleItemLoader(item=JobBoleArticleItem(),response=response)
        item_loader.add_value("url",response.url)
        item_loader.add_value("url_object_id",get_md5(response.url))
        item_loader.add_value("front_image_url",[front_image_url])
        item_loader.add_css("title",".entry-header h1::text")
        item_loader.add_css("create_date","p.entry-meta-hide-on-mobile::text")
        item_loader.add_css("praise_nums",".vote-post-up h10::text")
        item_loader.add_css("common_nums","a[href='#article-comment'] span::text")
        item_loader.add_css("fav_nums",".bookmark-btn::text")
        item_loader.add_css("tags","p.entry-meta-hide-on-mobile a::text")
        item_loader.add_css("content","div.entry")

        article_item = item_loader.load_item()

        yield article_item
