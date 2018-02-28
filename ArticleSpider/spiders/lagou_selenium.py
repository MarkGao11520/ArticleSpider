# -*- coding: utf-8 -*-
import time

import scrapy
import settings
from scrapy import signals
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.xlib.pydispatch import dispatcher
from selenium import webdriver

from items import LagouJobItem, LagouJobItemLoader
from scrapy_redis.spiders import RedisCrawlSpider
from scrapy_redis.defaults import START_URLS_AS_SET
from scrapy_redis.utils import bytes_to_str
from pyvirtualdisplay import Display


# 拉钩爬虫
class LagouSpider(RedisCrawlSpider):
    name = 'lagou_selenium'
    allowed_domains = ['www.lagou.com']
    # start_urls = ['https://www.lagou.com']
    # 请求头
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Host": "www.lagou.com",
        "Upgrade-Insecure-Requests": "1",
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0",
    }
    # 自定义配置
    custom_settings = {
        "AUTOTHROTTLE_ENABLED": True,
        # "DOWNLOAD_DELAY": 0.8,
    }

    # 爬取规则
    rules = (
        Rule(LinkExtractor(allow=("zhaopin/.*",)), follow=True),
        Rule(LinkExtractor(allow=("gongsi/j/d+.html",)), follow=True),
        Rule(LinkExtractor(allow=(r'jobs/\d+.html',)), callback='parse_job'),
    )

    # 构造函数
    def __init__(self):
        # 参数
        chrome_opt = webdriver.ChromeOptions()
        # 不加载图片
        # prefs = {"profile.managed_default_content_settings.images": 2}
        # chrome_opt.add_experimental_option("prefs",prefs)
        # 初始化selenium
        self.browser = webdriver.Chrome(executable_path=settings.SELENIUM_DRIVER_PATH, chrome_options=chrome_opt)

        super(LagouSpider, self).__init__()
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    # 爬取关闭事件
    def spider_closed(self,spider):
        # 当爬虫退出的时候关闭chrome
        print("spider closed")
        self.browser.quit()

    # 重写入口函数
    def start_requests(self):
        cookie_dict = {}
        self.browser.get("https://passport.lagou.com/login/login.html")
        self.browser.find_element_by_css_selector(".active input[placeholder='请输入常用手机号/邮箱']").send_keys(settings.LAGOU_PHONE_NUMBER)
        self.browser.find_element_by_css_selector(".active input[placeholder='请输入密码']").send_keys(settings.LAGOU_PASSWORD)
        self.browser.find_element_by_css_selector(".active  input.btn_green").click()
        time.sleep(2)

        for i in self.browser.get_cookies():
            cookie_dict[i["name"]] = i["value"]
        return self.next_requests(cookie_dict)

    # 登录成功后从redis中拿数据
    def next_requests(self,cookie_dict):
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

    # 爬虫工作内容网页并传给item
    def parse_job(self, response):

        item_loader = LagouJobItemLoader(item=LagouJobItem(), response=response)
        item_loader.add_css("title", ".job-name span::text")
        item_loader.add_value("url", response.url)
        item_loader.add_css("salary", ".salary::text")
        item_loader.add_xpath("job_city", "//*[@class='job_request']/p/span[2]/text()")
        item_loader.add_xpath("work_years", "//*[@class='job_request']/p/span[3]/text()")
        item_loader.add_xpath("degree_need", "//*[@class='job_request']/p/span[4]/text()")
        item_loader.add_xpath("job_type", "//*[@class='job_request']/p/span[5]/text()")

        item_loader.add_css("publish_time", ".publish_time::text")
        item_loader.add_css("job_advantage", ".job-advantage p::text")
        item_loader.add_css("job_desc", ".job_bt div")
        item_loader.add_css("job_addr", ".work_addr")

        item_loader.add_css("company_url", "#job_company dt a::attr(href)")
        item_loader.add_css("company_name", "#job_company dt a div h2::text")

        job_item = item_loader.load_item()

        return job_item

