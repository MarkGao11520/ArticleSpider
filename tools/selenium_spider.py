# coding:utf8
from selenium import webdriver

# browser.get("https://passport.lagou.com/login/login.html")
#
# browser.find_element_by_css_selector(".active div[data-controltype='Phone']>input").send_keys("17602686137")
# browser.find_element_by_css_selector(".active div[data-controltype='Password']>input").send_keys("AIjd1314")
# browser.find_element_by_css_selector(".active div[data-propertyname='submit']>input").click()
#
#
# cookies = browser.get_cookies()[0]
#
#
# my_cookies = ()
# print(cookies)
# for cookie in cookies:
#     print(cookie)
#     # print(browser.get_cookie(cookie))
#     my_cookies[cookie] = 'aaa'
#
# print(my_cookies)
#
# # print(browser.page_source)
# # browser.quit()

chrome_opt = webdriver.ChromeOptions()
prefs = {"profile.managed_default_content_settings.images": 2}
chrome_opt.add_experimental_option("prefs", prefs)
browser = webdriver.Chrome(executable_path="/Users/gaowenfeng/Downloads/chromedriver", chrome_options=chrome_opt)
browser.get("https://www.taobao.com")
