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
    "HOST": "www.zhihu.com",
    "Referer": "https://www.zhihu.com",
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

def get_xsrf():
    #获取xsrf code
    response = session.get("https://www.zhihu.com", headers=header)
    match_obj = re.match('.*name="_xsrf" value="(.*?)"', response.text.replace("\n",""))
    if match_obj:
        return (match_obj.group(1))
    else:
        return ""

def get_index():
    response = session.get("https://www.zhihu.com",headers=header)
    with open('index_page.html','wb') as f:
        f.write(response.text.encode('utf-8'))
    print('ok')

def get_captcha():
    from zheye import zheye

    z = zheye()
    randomNum = str(int(time.time() * 1000))
    r = session.get('https://www.zhihu.com/captcha.gif?r={}&type=login&lang=cn'.format(randomNum), headers=header, stream=True)
    if r.status_code == 200:
        with open('pic_captcha.gif', 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)
        positions = z.Recognize('pic_captcha.gif')

    captcha = {}
    pos = positions
    tmp = []
    captcha['img_size'] = [200,44]
    captcha['input_points'] = []
    for poss in pos:
        tmp.append(float(format(poss[1] / 2, '0.2f')))
        tmp.append(float(format(poss[0] / 2)))
        captcha['input_points'].append(tmp)
        tmp = []
    return json.dumps(captcha)

def zhihu_login(account,password):
    captcha = get_captcha()
    # 知乎登录
    if re.match("^1\d{10}",account):
        print("手机号码登录")
        post_url = "https://www.zhihu.com/login/phone_num"
        post_data = {
            "_xsrf": get_xsrf(),
            "password": password,
            "phone_num": account,
            'captcha': captcha,
            'captcha_type': 'cn'
        }
    else:
        if "@" in account:
            print("邮箱方式登录")
            post_url = "https://www.zhihu.com/login/email"
            post_data = {
                "_xsrf": get_xsrf(),
                "password": password,
                "phone_num": account,
                'captcha': captcha,
                'captcha_type': 'cn'
            }
                                                                                                     
    response_text = session.post(post_url, headers=header, params=post_data)
    session.cookies.save()

zhihu_login("17602686137", "AIjd1314")
# get_index()
# is_login()
