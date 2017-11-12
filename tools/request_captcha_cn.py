# coding:utf8

# /captcha.gif?r=1510475952138&type=login&lang=cn

from zheye import zheye
z = zheye()

import requests
import shutil

h = {
    'Accept': 'text/html,application/xhtml+xml,image/jxr,*/*',
    'Accept-Encoding': 'gzip,deflate',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
}
import time

lp = []
lpp = []
s =requests.session()
web_data = s.get('http://www.zhihu.com',headers=h).text.replace("\n","")
import re
match_obj = re.match('.*name="_xsrf" value="(.*?)"',web_data)
xsrf = ''
if match_obj:
    xsrf = (match_obj.group(1))
randomNum = str(int(time.time() * 1000))
r = s.get('https://www.zhihu.com/captcha.gif?r={}&type=login&lang=cn'.format(randomNum), headers=h, stream=True)
if r.status_code == 200:
    with open('pic_captcha.gif','wb') as f:
        r.raw.decode_content = True
        shutil.copyfileobj(r.raw,f)
    positions = z.Recognize('pic_captcha.gif')
    print(positions)

captcha = {}
pos = positions
tmp = []
captcha['input_points'] = []
for poss in pos:
    tmp.append(float(format(poss[1] / 2,'0.2f')))
    tmp.append(float(format(poss[0] / 2,'.f')))
    captcha['input_points'].append(tmp)
    tmp = []

params = {
    '_xsrf': xsrf,
    'password': 'AIjd1314',
    'phone_num': '17602686137',
    'captcha': '{"img_size": [200,44],"input_points": [[%.2f,%f],[%.2f,%f]]}' %
               (pos[0][1]/ 2,pos[0][0] /2,pos[1][1]/ 2,pos[1][0] /2),
    'captcha_type': 'cn'
}


r = s.post('https://www.zhihu.com/login/phone_num', headers = h, params=params)
import json
print(json.dumps(params))
print(json.dumps(captcha))
re_text = json.loads(r.text)
print(r.text)

