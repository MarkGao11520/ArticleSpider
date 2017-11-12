# coding:utf8

from zheye import zheye
z = zheye()
positions = z.Recognize('captcha_cn.gif')
print(positions)