# # -*- coding: utf-8 -*-
# import json
# import re
# import scrapy
# import settings
# import time
#
# # 兼容python2和python3的版本
# try:
#     import urlparse as parse
# except:
#     from urllib import parse
#
# from scrapy.loader import ItemLoader
# from items import ZhihuAnswerItem, ZhihuQuestionItem
# from zheye import zheye
#
#
# # 知乎爬虫
# class ZhihuSpider(scrapy.Spider):
#     name = 'zhihu'
#     allowed_domains = ['www.zhihu.com']
#     start_urls = ['http://www.zhihu.com/']
#
#     # question的回答分页列表的REST_API
#     start_answer_url = 'https://www.zhihu.com/api/v4/questions/{' \
#                        '0}/answers?sort_by=default&include=data%5B%2A%5D.is_normal%2Cadmin_closed_comment' \
#                        '%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason' \
#                        '%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent' \
#                        '%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time' \
#                        '%2Cupdated_time%2Creview_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author' \
#                        '%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B%2A%5D.mark_infos%5B%2A%5D' \
#                        '.url%3Bdata%5B%2A%5D.author.follower_count%2Cbadge%5B%3F%28type%3Dbest_answerer%29%5D.topics' \
#                        '&limit={1}&offset={2} '
#
#     # 请求头伪造
#     headers = {
#         "HOST": "www.zhihu.com",
#         "Referer": "https://www.zhihu.com",
#         'User-Agent': ""
#     }
#
#     # 深度优先遍历
#     def parse(self, response):
#         """
#         提取出html页面中的所有url 并跟踪这些url进行一步爬取
#         如果提取的url中格式伪/question/xx 就下载之后直接进入解析函数
#         """
#
#         # 获取所有a 标签 href属性
#         all_urls = response.css("a::attr(href)").extract()
#         # 组装绝对路径url
#         all_urls = [parse.urljoin(response.url, url) for url in all_urls]
#         # 去掉非https的url
#         all_urls = filter(lambda x: True if x.startswith("https") else False, all_urls)
#         # 遍历所有的url
#         for url in all_urls:
#             # 匹配问题url
#             match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", url)
#             if match_obj:
#                 # 如果提取到question相关的页面则下载后交由回答提取函数进行处理
#                 request_url = match_obj.group(1)
#                 yield scrapy.Request(request_url, headers=self.headers, callback=self.parse_question)
#             else:
#                 # 如果不是question则直接进一步跟踪
#                 yield scrapy.Request(url, headers=self.headers, callback=self.parse)
#
#     # 处理question页面，从页面中提取出具体的question item
#     def parse_question(self, response):
#         match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", response.url)
#         if match_obj:
#             question_id = int(match_obj.group(2))
#
#         if "QuestionHeader-title" in response.text:
#             # 处理新版本
#             item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)
#             item_loader.add_css("title", "h1.QuestionHeader-title::text")
#             item_loader.add_css("content", ".QuestionHeader-detail")
#             item_loader.add_value("url", response.url)
#             item_loader.add_value("zhihu_id", question_id)
#             item_loader.add_css("answer_num", ".List-headerText span::text")
#             item_loader.add_css("comments_num", ".QuestionHeader-Comment button::text")
#             item_loader.add_css("watch_user_num", ".NumberBoard-value::text")
#             item_loader.add_css("topics", ".QuestionHeader-topics .Popover div::text")
#
#             question_item = item_loader.load_item()
#         else:
#             # 处理知乎旧版本
#             item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)
#             item_loader.add_value("url", response.url)
#             item_loader.add_value("zhihu_id", question_id)
#             item_loader.add_xpath("title", "//*[@id='zh-question-title']/h2/a/text()|"
#                                            "//*[@id='zh-question-title']/h2/a/text()")
#             # item_loader.add_css("title",".zh-question-title h2 a::text")
#             item_loader.add_css("content", "#zh-question-detail")
#             item_loader.add_css("answer_num", "#zh-question-answer-num::text")
#             item_loader.add_css("comments_num", "#zh-question-meta-wrap a[name='addcomment']::text")
#             item_loader.add_xpath("watch_user_num", "//[@id='zh-question-side-header-wrap']/text()|"
#                                                     "//[@class='zh-question-followers-sidebar']/div/a/strong/text()")
#             # item_loader.add_css("watch_user_num","#zh-question-side-header-wrap::text")
#             item_loader.add_css("topics", ".zm-tag-editor-labels a::text")
#
#             question_item = item_loader.load_item()
#
#         # 提取第一页回答列表，交给parse_answer
#         yield scrapy.Request(self.start_answer_url.format(question_id, 20, 0),
#                              headers=self.headers, callback=self.parse_answer)
#         # 处理item
#         yield question_item
#
#     # 处理回答url
#     def parse_answer(self, response):
#         # 回答列表返回json结果，所以将字符串转换为json结构
#         ans_json = json.loads(response.text)
#         # 获取是否为最后一页
#         is_end = ans_json["paging"]["is_end"]
#         # 获取下一页url
#         next_url = ans_json["paging"]["next"]
#
#         # 提取answer字段
#         for answer in ans_json["data"]:
#             answer_item = ZhihuAnswerItem()
#             answer_item["zhihu_id"] = answer["id"]
#             answer_item["url"] = answer["url"]
#             answer_item["question_id"] = answer["question"]["id"]
#             answer_item["author_id"] = answer["author"]["id"] if "id" in answer["author"] else None
#             answer_item["content"] = answer["content"] if "content" in answer else None
#             answer_item["praise_num"] = answer["voteup_count"]
#             answer_item["comments_num"] = answer["comment_count"]
#             answer_item["create_time"] = answer["created_time"]
#             answer_item["update_time"] = answer["updated_time"]
#             # 处理item
#             yield answer_item
#
#         # 如果不是最后一页，则处理下一页
#         if not is_end:
#             yield scrapy.Request(next_url, headers=self.headers, callback=self.parse_answer)
#
#     def start_requests(self):
#         # 入口将登陆界面下载后交给login方法处理
#         return [scrapy.Request('https://www.zhihu.com/#signin', headers=self.headers, callback=self.login)]
#
#     # 登陆方法
#     def login(self, response):
#         # 获取_xsrf隐藏字段
#         match_obj = re.match('.*name="_xsrf" value="(.*?)"', response.text, re.DOTALL)
#         xsrf = ''
#
#         # 判断是否取到值
#         if match_obj:
#             xsrf = (match_obj.group(1))
#         # 只有取到xsrf才进行下面的登录请求
#         if xsrf:
#             # post请求参数
#             post_data = {
#                 "_xsrf": xsrf,
#                 "phone_num": settings.ZHIHU_PHONE_NUMBER,
#                 "password": settings.ZHIHU_PASSWORD,
#                 "captcha": ""
#             }
#             # 获取当前时间戳
#             t = str(int(time.time() * 1000))
#             # 获取验证码图片url
#             captcha_url_cn = "https://www.zhihu.com/captcha.gif?r={0}&type=login&lang=cn".format(t)
#             # 处理知乎倒立汉字验证码识别登录
#             yield scrapy.Request(captcha_url_cn, headers=self.headers, meta={"post_data": post_data}, callback=self.login_after_captcha_cn)
#
#     # 知乎倒立汉字验证码识别登录
#     def login_after_captcha_cn(self, response):
#         # 创建captcha.jpg并将response中的图片写入
#         with open("captcha.jpg", "wb") as f:
#             f.write(response.body)
#             f.closed
#
#         # 创建zheye对象
#         z = zheye()
#         # 识别倒立验证码位置
#         positions = z.Recognize('captcha.jpg')
#         # 将位置信息进行包装，包装成二元数组
#         pos_arr = []
#         if len(positions) == 2:
#             if positions[0][1] > positions[1][1]:
#                 pos_arr.append([positions[1][1],positions[1][0]])
#                 pos_arr.append([positions[0][1],positions[0][0]])
#             else:
#                 pos_arr.append([positions[0][1],positions[0][0]])
#                 pos_arr.append([positions[1][1],positions[1][0]])
#         else:
#             pos_arr.append([positions[0][1], positions[0][0]])
#
#         # 登录请求
#         post_url = "https://www.zhihu.com/login/phone_num"
#         # 从meta中拿到上一个方法包装的请求数据
#         post_data = response.meta.get("post_data", {})
#         # 判断是两个字还是一个字
#         if len(positions) == 2:
#             post_data["captcha"] = '{"img_size": [200,44],"input_points": [[%.2f,%f],[%.2f,%f]]}' % (
#                 pos_arr[0][0] / 2, pos_arr[0][1] / 2, pos_arr[1][0] / 2, pos_arr[1][1] / 2)
#         else:
#             post_data["captcha"] = '{"img_size": [200,44],"input_points": [[%.2f,%f]]}' % (
#                 pos_arr[0][0] / 2, pos_arr[0][1] / 2)
#         post_data["captcha_type"] = "cn"
#
#         # 模拟登录请求，成功后进入check_login方法
#         return [scrapy.FormRequest(
#             url=post_url,
#             formdata=post_data,
#             headers=self.headers,
#             callback=self.check_login
#         )]
#
#     def login_after_captcha(self, respnse):
#         pass
#
#     # 验证服务器的返回数据判断是否成功
#     def check_login(self, response):
#         text_json = json.loads(response.text)
#         if "msg" in text_json and text_json["msg"] == "登录成功":
#             # 如果成功则正是开始进行下载，并设置header
#             for url in self.start_urls:
#                 yield scrapy.Request(url, dont_filter=True, headers=self.headers)
