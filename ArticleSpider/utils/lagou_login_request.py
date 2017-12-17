# coding:utf8
import requests
try:
    import cookielib
except:
    import http.cookiejar as cookielib
import re
import time
import shutil
import json

__author__ = 'gwf'

session = requests.session()
session.cookies = cookielib.LWPCookieJar(filename="cookies.txt")
# try:
#     session.cookies.load(ignore_discard=True)
# except:
#     print("cookie未能加载")

agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
header = {
  #  'Accept': 'text/html,application/xhtml+xml,image/jxr,*/*',
  #  'Accept-Encoding': 'gzip,deflate',
    "HOST": "passport.lagou.com",
    "Referer": "https://passport.lagou.com/login/login.html",
    'User-Agent': agent
}

def is_login():
    # 通过个人中心页面返回状态码来判断是否为登录状态
    inbox_url = "https://www.zhihu.com/inbox"
    response = session.get(inbox_url, headers=header, allow_redirects=False)
    if response.status_code !=200:
        return False
    else:
        return True

# def get_xsrf():
#     #获取xsrf code
#     response = session.get("https://www.zhihu.com", headers=header)
#     match_obj = re.match('.*name="_xsrf" value="(.*?)"', response.text.replace("\n",""))
#     if match_obj:
#         return (match_obj.group(1))
#     else:
#         return ""

def get_index():
    response = session.get("https://www.zhihu.com",headers=header)
    with open('index_page.html','wb') as f:
        f.write(response.text.encode('utf-8'))
    print('ok')



def zhihu_login(account,password):
    # 知乎登录
    if re.match("^1\d{10}",account):
        print("手机号码登录")
        post_url = "https://passport.lagou.com/login/login.json"
        post_data = {
            "isValidate":"true",
            "password": password,
            "phone_num": account,
            'request_form_verifyCode': "",
            'submit': ""
        }
    else:
        if "@" in account:
            print("邮箱方式登录")
            post_url = "https://www.zhihu.com/login/email"
            post_data = {
                "isValidate":"true",
                "password": password,
                "username": account,
                'request_form_verifyCode': "",
            }
                                                                                                     
    response_text = session.post(post_url, headers=header, params=post_data)
    session.cookies.save()

zhihu_login("17602686137", "efa9bcd2e9e3b4ab298018eea326c193")
# get_index()
# is_login()
