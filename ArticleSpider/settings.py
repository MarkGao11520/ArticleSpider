# -*- coding: utf-8 -*-

import os
import sys
# Scrapy settings for ArticleSpider project

# 项目名
BOT_NAME = 'ArticleSpider'

# 爬虫模块名称
SPIDER_MODULES = ['ArticleSpider.spiders']
NEWSPIDER_MODULE = 'ArticleSpider.spiders'

# 默认会过滤掉不符合ROBOTSTXT协议的url
ROBOTSTXT_OBEY = False

# 下载服务管理器
DOWNLOADER_MIDDLEWARES = {
   'ArticleSpider.middlewares.RandomUserAgentMiddlware': 2,
   # 'ArticleSpider.middlewares.JSPageMiddleware': 1,
   'ArticleSpider.middlewares.MyCustomDownloaderMiddleware': None,
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

# 项目地址
project_dir = os.path.abspath(os.path.dirname(__file__))

# 图片下载访问属性
IMAGES_URLS_FIELD = "front_image_url"
# 图片存储路径
IMAGES_STORE = os.path.join(project_dir, "images")

# 项目地址上层目录
BASE_DIR = os.path.dirname(project_dir)
sys.path.insert(0, os.path.join(BASE_DIR, "ArticleSpider"))

# UserAgent 类型
RANDOM_UA_TYPE = "random"

# 是否打印debug日志
AUTOTHROTTLE_DEBUG = False

# 数据库配置
MYSQL_HOST = "127.0.0.1"
MYSQL_DBNAME = "article_spider"
MYSQL_USER = "root"
MYSQL_PASSWORD = "root"

# 数据库格式化
SQL_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%s"
SQL_DATE_FORMAT = "%Y-%m-%d"

