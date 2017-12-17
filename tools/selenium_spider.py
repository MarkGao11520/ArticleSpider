# coding:utf8
from selenium import webdriver

browser = webdriver.Chrome(executable_path="/Users/gaowenfeng/Downloads/chromedriver")

browser.get("https://passport.lagou.com/login/login.html")

browser.find_element_by_css_selector(".active div[data-controltype='Phone']>input").send_keys("17602686137")
browser.find_element_by_css_selector(".active div[data-controltype='Password']>input").send_keys("AIjd1314")
browser.find_element_by_css_selector(".active div[data-propertyname='submit']>input").click()



print(browser.page_source)