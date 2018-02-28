# -*- coding: utf-8 -*-

from urllib import parse

from scrapy import signals
from scrapy.http import Request
from scrapy.xlib.pydispatch import dispatcher

from items import JobBoleArticleItem, ArticleItemLoader
from scrapy_redis.spiders import RedisSpider
from utils.common import get_md5


# 伯乐在线爬虫
class JobboleSpider(RedisSpider):
    name = 'jobbole'
    # 起始爬取键
    redis_key = 'jobbole:start_urls'
    allowed_domains = ['blog.jobbole.com']

    # start_urls = ['http://blog.jobbole.com/all-posts/']

    custom_settings = {
        "COOKIES_ENABLED": False,
        "DOWNLOAD_DELAY": 0
    }

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
            yield Request(url=parse.urljoin(response.url, post_url), meta={"front_image_url": image_url},
                          callback=self.parse_detail)

        # 提取下一页并交给scrapy进行下载，下载完成后交给parse
        next_url = response.css(".next.page-numbers::attr(href)").extract_first("")
        if next_url:
            yield Request(url=parse.urljoin(response.url, next_url), callback=self.parse)

    # 处理具体的文章链接，提取内容放入item
    def parse_detail(self, response):

        # 通过item Loader加载item
        front_image_url = response.meta.get("front_image_url", "")  # 文章封面图
        item_loader = ArticleItemLoader(item=JobBoleArticleItem(), response=response)
        item_loader.add_value("url", response.url)
        item_loader.add_value("url_object_id", get_md5(response.url))
        item_loader.add_value("front_image_url", [front_image_url])
        item_loader.add_css("title", ".entry-header h1::text")
        item_loader.add_css("create_date", "p.entry-meta-hide-on-mobile::text")
        item_loader.add_css("praise_nums", ".vote-post-up h10::text")
        item_loader.add_css("common_nums", "a[href='#article-comment'] span::text")
        item_loader.add_css("fav_nums", ".bookmark-btn::text")
        item_loader.add_css("tags", "p.entry-meta-hide-on-mobile a::text")
        item_loader.add_css("content", "div.entry")

        article_item = item_loader.load_item()

        yield article_item
