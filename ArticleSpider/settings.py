# -*- coding: utf-8 -*-

import os
import sys

#############################项目配置开始######################################

# 项目名
BOT_NAME = 'ArticleSpider'

# 爬虫模块名称
SPIDER_MODULES = ['ArticleSpider.spiders']
NEWSPIDER_MODULE = 'ArticleSpider.spiders'

# 项目地址
project_dir = os.path.abspath(os.path.dirname(__file__))
# 项目地址上层目录
BASE_DIR = os.path.dirname(project_dir)
sys.path.insert(0, os.path.join(BASE_DIR, "ArticleSpider"))

# 默认会过滤掉不符合ROBOTSTXT协议的url
ROBOTSTXT_OBEY = False

#############################项目配置结束######################################

#############################组件配置开始######################################

# 下载服务管理器
DOWNLOADER_MIDDLEWARES = {
    'ArticleSpider.middlewares.RandomUserAgentMiddlware': 100,
    # 'ArticleSpider.middlewares.RandomProxyMiddleware': 200,
    # 'ArticleSpider.middlewares.JSPageMiddleware': 300,
}

# ITEM 管道
ITEM_PIPELINES = {
    # 'scrapy.pipelines.images.ImagesPipeline': 1,
    # 'ArticleSpider.pipelines.ArticleImagePipeline': 1,
    # 'ArticleSpider.pipelines.JsonExporterPipeline': 2,
    # 'ArticleSpider.pipelines.MysqlTwistedPipeline': 2,
    'scrapy_redis.pipelines.RedisPipeline': 300,
    'ArticleSpider.pipelines.ElasticsearchPipeline': 400,
}

# 指定scrapy_redis分布式爬虫调度器
SCHEDULER = "scrapy_redis.scheduler.Scheduler"

# 指定scrapy_redis分布式爬虫去重器
DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"

#############################组件配置结束######################################

#############################反爬虫配置开始######################################

# 是否启用cookie
COOKIES_ENABLED = True

# 是否开启自动下载延迟扩展
# AUTOTHROTTLE_ENABLED = True

# 起用AutoThrottle调试(debug)模式，展示每个接收到的response
AUTOTHROTTLE_DEBUG = True

# DOWNLOAD_DELAY = 3

#############################反爬虫配置结束######################################


#############################自定义属性开始######################################
# 图片下载访问属性
IMAGES_URLS_FIELD = "front_image_url"
# 图片存储路径
IMAGES_STORE = os.path.join(project_dir, "images")

# 数据库配置
MYSQL_HOST = "127.0.0.1"
MYSQL_DBNAME = "article_spider"
MYSQL_USER = "root"
MYSQL_PASSWORD = "root"

# 数据库格式化
SQL_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%s"
SQL_DATE_FORMAT = "%Y-%m-%d"

# selenium_driver路径
SELENIUM_DRIVER_PATH = BASE_DIR + "/" + "chromedriver"
# selenium代理爬虫
SELENIUM_PROXY_SPIDER = ['lagou']

# 知乎登录账号
ZHIHU_PHONE_NUMBER = "17602686137"
ZHIHU_PASSWORD = "AIjd1314"

# 拉钩登录账号
LAGOU_PHONE_NUMBER = "18299536448"
LAGOU_PASSWORD = "zdj515158."



#############################自定义属性结束######################################

