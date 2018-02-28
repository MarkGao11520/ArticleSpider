# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/spider-middleware.html

import settings

from fake_useragent import UserAgent
from scrapy.http import HtmlResponse

from tools.crawel_xici_ip import GetIP


# 随机更换user-agent
class RandomUserAgentMiddlware(object):
    def __init__(self, crawler):
        super(RandomUserAgentMiddlware, self).__init__()
        self.ua = UserAgent()
        self.ua_type = crawler.settings.get("RANDOM_UA_TYPE", "random")

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_request(self, request, spider):

        def get_ua():
            return getattr(self.ua, self.ua_type)
        try:
            request.headers.setdefault('User-Agent', get_ua())
        except Exception:
            print('-------------------------')


# 动态设置ip代理
class RandomProxyMiddleware(object):

    def process_request(self, request, spider):
        get_ip = GetIP()
        request.meta["proxy"] = get_ip.get_random_ip()


# 使用selenium代理请求
class JSPageMiddleware(object):

    def process_request(self, request, spider):
        if spider.name in settings.SELENIUM_PROXY_SPIDER:
            spider.browser.get(request.url)
            print("访问:{0}".format(request.url))

            return HtmlResponse(url=spider.browser.current_url, body=spider.browser.page_source, encoding="utf-8", request=request)
