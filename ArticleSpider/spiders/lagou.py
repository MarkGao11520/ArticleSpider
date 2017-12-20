# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from items import LagouJobItem,LagouJobItemLoader
from selenium import webdriver
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals
import time

class LagouSpider(CrawlSpider):
    name = 'lagou'
    allowed_domains = ['www.lagou.com']
    start_urls = ['https://www.lagou.com']
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
    custom_settings = {
        "COOKIES_ENABLED": True,
        "DOWNLOAD_DELAY": 0.1,
    }

    # rules = (
    #     # 提取匹配 'category.php' (但不匹配 'subsection.php') 的链接并跟进链接(没有callback意味着follow默认为True)
    #     Rule(LinkExtractor(allow=('www.lagou.com/zhaopin/Java/',), )),
    #
    #     # 提取匹配 'item.php' 的链接并使用spider的parse_item方法进行分析
    #     Rule(LinkExtractor(allow=('www.lagou.com/jobs/',)), callback='parse_job'),
    # )

    rules = (
        Rule(LinkExtractor(allow=("zhaopin/.*",)), follow=True),
        Rule(LinkExtractor(allow=("gongsi/j/d+.html",)), follow=True),
        Rule(LinkExtractor(allow=(r'jobs/\d+.html',)), callback='parse_job'),
    )

    def __init__(self):
        # 初始化selenium
        # chrome_opt = webdriver.ChromeOptions()
        # prefs = {"profile.managed_default_content_settings.images": 2}
        # chrome_opt.add_experimental_option("prefs",prefs)
        # self.browser = webdriver.Chrome(executable_path="/Users/gaowenfeng/Downloads/chromedriver",chrome_options=chrome_opt)

        # from pyvirtualdisplay import Display
        # display = Display(visible=0, size=(800, 600))
        # display.start()

        self.browser = webdriver.Chrome(executable_path="/Users/gaowenfeng/Downloads/chromedriver")
        super(LagouSpider, self).__init__()
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self,spider):
        # 当爬虫退出的时候关闭chrome
        print("spider closed")
        self.browser.quit()

    def start_requests(self):
        cookie_dict = {}
        self.browser.get("https://passport.lagou.com/login/login.html")
        self.browser.find_element_by_css_selector(".active input[placeholder='请输入常用手机号/邮箱']").send_keys("18299536448")
        self.browser.find_element_by_css_selector(".active input[placeholder='请输入密码']").send_keys("zdj515158.")
        self.browser.find_element_by_css_selector(".active  input.btn_green").click()
        time.sleep(2)

        for i in self.browser.get_cookies():
            cookie_dict[i["name"]] = i["value"]

        return [scrapy.Request(url=self.start_urls[0], headers=self.headers, cookies=cookie_dict, callback=self.parse)]

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

