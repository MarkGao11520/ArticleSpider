# coding:utf8

__author__ = 'boddy'

from scrapy.cmdline import execute
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# execute(["scrapy","crawl","jobbole"])
execute(["scrapy","crawl","jobbole"])
