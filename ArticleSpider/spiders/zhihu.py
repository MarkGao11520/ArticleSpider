# -*- coding: utf-8 -*-
import json
import re

import scrapy


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']

    agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
    headers = {
        "HOST": "www.zhihu.com",
        "Referer": "https://www.zhihu.com",
        'User-Agent': agent
    }

    def parse(self, response):
        pass

    def parse_detail(self,response):
        pass

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
            yield scrapy.Request(captcha_url_cn,headers=self.headers,meta={"post_data":post_data},callback=self.login_after_captcha_cn)
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

    def check_login(self,response):
        # 验证服务器的返回数据判断是否成功
        text_json = json.loads(response.text)
        if "msg" in text_json and text_json["msg"] == "登录成功":
            for url in self.start_urls:
                yield scrapy.Request(url,dont_filter=True,headers=self.headers)
