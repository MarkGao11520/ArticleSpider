# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
import datetime
import redis
from scrapy.loader.processors import MapCompose, TakeFirst, Join
from scrapy.loader import ItemLoader

from utils.common import extract_num
from settings import SQL_DATETIME_FORMAT, SQL_DATE_FORMAT
from models.es_types import JobboleType, ZhihuAnswerType, ZhihuQuestionType, LagouType
from w3lib.html import remove_tags

from elasticsearch_dsl.connections import connections
es = connections.create_connection(JobboleType._doc_type.using)

redis_cli = redis.StrictRedis(host="localhost")


# 追加姓名
def add_jobbole(value):
    return value + '-mark'


# 日期格式化
def date_covert(value):
    # TODO create_date转换抛异常
    try:
        create_date = datetime.datetime.strptime(value, "%Y/%m/%d").date()
    except Exception as e:
        create_date = datetime.datetime.now().date()

    return create_date


# "/"替换成""
def replace_splash(value):
    return value.replace("/", "")


# 去掉空格
def handle_strip(value):
    return value.strip()


# 去掉评论tag
def remove_comment_tags(value):
    # 去掉tags中提取的评论
    if "评论" in value:
        return ""
    else:
        return value


# 直接返回不做处理
def return_value(value):
    return value


# 处理job地址
def handle_jobaddr(value):
    addr_list = value.split("\n")
    addr_list = [item.strip() for item in addr_list if item.strip() != "查看地图"]
    return "".join(addr_list)


# 根据字符串生成搜索建议数组
def gen_suggest(index, info_tuple):
    used_words = set()
    suggests = []
    for text, weight in info_tuple:
        if text:
            # 调用es的analyze接口分析字符串
            words = es.indices.analyze(index=index, analyzer="ik_max_word", params={'filter': ["lowercase"]}, body=text)
            analyzed_words = set([r["token"] for r in words["tokens"] if len(r["token"]) > 1])
            new_words = analyzed_words - used_words
        else:
            new_words = set()
        if new_words:
            suggests.append({"input": list(new_words), "weight": weight})

    return suggests


# 自定义output_processor
class ArticleItemLoader(ItemLoader):
    default_output_processor = TakeFirst()


# 自定义output_processor
class LagouJobItemLoader(ItemLoader):
    # 自定义itemloader
    default_output_processor = TakeFirst()


# 伯乐在线 Item
class JobBoleArticleItem(scrapy.Item):
    title = scrapy.Field(
        input_processor=MapCompose(lambda x: x + "-jobbole", add_jobbole)
    )
    create_date = scrapy.Field(
        input_processor=MapCompose(date_covert)
    )
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    front_image_url = scrapy.Field(
        output_processor=MapCompose(return_value)
    )
    front_image_path = scrapy.Field()
    praise_nums = scrapy.Field(
        input_processor=MapCompose(extract_num)
    )
    common_nums = scrapy.Field(
        input_processor=MapCompose(extract_num)
    )
    fav_nums = scrapy.Field(
        input_processor=MapCompose(extract_num)
    )
    tags = scrapy.Field(
        input_processor=MapCompose(remove_comment_tags),
        output_processor=Join(",")
    )
    content = scrapy.Field()

    # 持久化到mysql
    def get_insert_sql(self):
        insert_sql = """
            insert into jobbole_article
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE content=VALUES(fav_nums)
        """
        params = (self["title"], self["create_date"], self["url"], self["url_object_id"], self["front_image_url"][0],
                  self["front_image_path"], self["praise_nums"], self["common_nums"], self["fav_nums"], self["tags"],
                  self["content"])

        return insert_sql, params

    # 持久化到es
    def save_to_es(self):
        article = JobboleType()
        article.title = self['title']
        article.create_date = self["create_date"]
        article.content = remove_tags(self["content"])
        article.front_image_url = self['front_image_url']
        if "front_image_path" in self:
            article.front_image_path = self['front_image_path']
        article.praise_nums = self['praise_nums']
        article.fav_nums = self['fav_nums']
        article.common_nums = self['common_nums']
        article.url = self['url']
        article.tags = self['tags']
        article.meta.id = self['url_object_id']

        article.suggest = gen_suggest(JobboleType._doc_type.index, ((article.title, 10), (article.tags, 7)))

        article.save()
        redis_cli.incr("jobbole_count")
        return


# 知乎问题的 item
class ZhihuQuestionItem(scrapy.Item):
    # 知乎的问题 item
    zhihu_id = scrapy.Field()
    topics = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    answer_num = scrapy.Field()
    comments_num = scrapy.Field()
    watch_user_num = scrapy.Field()
    click_num = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        # 插入知乎question表的sql语句
        insert_sql = """
            insert into zhihu_question ( `comments_num`, `answer_num`, `click_num`, `zhihu_id`, `watch_user_num`, `url`, `title`, `topics`, `content`) 
            values ( %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE content=VALUES(content), answer_num=VALUES(answer_num), comments_num=VALUES(comments_num),
              watch_user_num=VALUES(watch_user_num), click_num=VALUES(click_num)
        """
        zhihu_id = self["zhihu_id"][0]
        topics = ",".join(self["topics"])
        url = self["url"][0]
        title = "".join(self["title"])
        content = "".join(self["content"])
        answer_num = extract_num("".join(self["answer_num"]))
        comments_num = extract_num("".join(self["comments_num"]))
        if len(self["watch_user_num"]) == 2:
            watch_user_num = int(self["watch_user_num"][0])
            click_num = int(self["watch_user_num"][1])
        else:
            watch_user_num = int(self["watch_user_num"][0])
            click_num = 0
        # crawl_time = datetime.datetime.now().strftime(SQL_DATETIME_FORMAT)

        params = (comments_num, answer_num, click_num, zhihu_id, watch_user_num, url, title, topics, content)

        return insert_sql, params

    def save_to_es(self):
        try:
            if len(self["watch_user_num"]) == 2:
                watch_user_num = int(self["watch_user_num"][0])
                click_num = int(self["watch_user_num"][1])
            else:
                watch_user_num = int(self["watch_user_num"][0])
                click_num = 0
        except:
            watch_user_num = 0
            click_num = 0

        zhihu_id = self["zhihu_id"][0]
        topics = ",".join(self["topics"])
        url = self["url"][0]
        title = "".join(self["title"])
        content = "".join(self["content"])
        answer_num = extract_num("".join(self["answer_num"]))
        comments_num = extract_num("".join(self["comments_num"]))
        crawl_time = datetime.datetime.now().strftime(SQL_DATE_FORMAT)
        article = ZhihuQuestionType()
        article.meta.id = zhihu_id
        article.topics = topics
        article.url = url
        article.title = title
        article.content = content
        article.answer_num = answer_num
        article.comments_num = comments_num
        article.watch_user_num = watch_user_num
        article.click_num = click_num
        article.crawl_time = crawl_time

        article.suggest = gen_suggest(ZhihuQuestionType._doc_type.index, ((article.title, 10), (article.content, 9)))

        redis_cli.incr("zhihu_count")
        article.save()
        return


# 知乎的回答 item
class ZhihuAnswerItem(scrapy.Item):
    zhihu_id = scrapy.Field()
    url = scrapy.Field()
    question_id = scrapy.Field()
    author_id = scrapy.Field()
    content = scrapy.Field()
    praise_num = scrapy.Field()
    comments_num = scrapy.Field()
    create_time = scrapy.Field()
    update_time = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        # 插入知乎question表的sql语句
        insert_sql = """
            insert into zhihu_answer ( `comments_num`, `author_id`, `content`, `zhihu_id`, `praise_num`, `question_id`, 
             `url`, `create_time`, `update_time`) 
            values ( %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE content=VALUES(content), comments_num=VALUES(comments_num), praise_num=VALUES(praise_num),
              update_time=VALUES(update_time)
        """

        create_time = datetime.datetime.fromtimestamp(self["create_time"]).strftime(SQL_DATE_FORMAT)
        update_time = datetime.datetime.fromtimestamp(self["update_time"]).strftime(SQL_DATE_FORMAT)

        params = (self["comments_num"], self["author_id"], self["content"], self["zhihu_id"], self["praise_num"],
                  self["question_id"], self["url"], create_time, update_time)

        return insert_sql, params

    def save_to_es(self):
        crawl_time = datetime.datetime.now().strftime(SQL_DATE_FORMAT)
        create_time = datetime.datetime.fromtimestamp(self["create_time"]).strftime(SQL_DATE_FORMAT)
        update_time = datetime.datetime.fromtimestamp(self["update_time"]).strftime(SQL_DATE_FORMAT)
        article = ZhihuAnswerType()
        article.meta.id = self['zhihu_id']
        article.url = self['url']
        article.question_id = self['question_id']
        article.content = remove_tags(self['content'])
        article.praise_num = self['praise_num']
        article.comments_num = self['comments_num']
        article.create_time = self["create_time"]
        article.update_time = self["update_time"]
        article.crawl_time = crawl_time

        article.save()
        return


# 拉钩item
class LagouJobItem(scrapy.Item):
    # 拉勾网职位
    title = scrapy.Field()
    url = scrapy.Field()
    salary = scrapy.Field()
    job_city = scrapy.Field(
        input_processor=MapCompose(replace_splash),
    )
    work_years = scrapy.Field(
        input_processor=MapCompose(replace_splash),
    )
    degree_need = scrapy.Field(
        input_processor=MapCompose(replace_splash),
    )
    job_type = scrapy.Field()
    publish_time = scrapy.Field()
    job_advantage = scrapy.Field()
    job_desc = scrapy.Field(
        input_processor=MapCompose(handle_strip),
    )
    job_addr = scrapy.Field(
        input_processor=MapCompose(remove_tags, handle_jobaddr),
    )
    company_name = scrapy.Field(
        input_processor=MapCompose(handle_strip),
    )
    company_url = scrapy.Field()
    crawl_time = scrapy.Field()
    crawl_update_time = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
            insert into lagou_job(title, url, salary, job_city, work_years, degree_need,
            job_type, publish_time, job_advantage, job_desc, job_addr, company_url, company_name, job_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE salary=VALUES(salary), job_city=VALUES(job_city), work_years=VALUES(work_years),
              degree_need=VALUES(degree_need), job_type=VALUES(job_type), publish_time=VALUES(publish_time), tags=VALUES(tags)
              , job_advantage=VALUES(job_advantage), job_desc=VALUES(job_desc), crawl_time=VALUES(crawl_time)
        """

        job_id = extract_num(self["url"])
        params = (self["title"], self["url"], self["salary"], self["job_city"], self["work_years"], self["degree_need"],
                  self["job_type"], self["publish_time"], self["job_advantage"], self["job_desc"], self["job_addr"],
                  self["company_url"],
                  self["company_name"], job_id)

        return insert_sql, params

    def save_to_es(self):
        crawl_time = datetime.datetime.now().strftime(SQL_DATE_FORMAT)
        job_id = extract_num(self["url"])
        article = LagouType()
        article.meta.id = job_id
        article.title = self['title']
        article.url = self['url']
        article.salary = self['salary']
        article.job_city = self['job_city']
        article.work_years = self['work_years']
        article.degree_need = self['degree_need']
        article.job_type = self['job_type']
        article.publish_time = self['publish_time']
        article.job_advantage = self['job_advantage']
        article.job_desc = self['job_desc']
        article.job_addr = self['job_addr']
        article.company_name = self['company_name']
        article.crawl_time = crawl_time
        article.crawl_update_time = crawl_time

        article.suggest = gen_suggest(LagouType._doc_type.index, ((article.title, 10), (article.company_name, 9), (article.job_desc, 8), (article.job_addr, 7)))

        redis_cli.incr("lagou_count")
        article.save()
