# -*- coding: utf-8 -*-
#  re_selector = response.xpath("/html/body/div[1]/div[3]/div[1]/div[1]/h1")
#  re2_selector = response.xpath('//*[@id="post-88673"]/div[1]/h1/text()')
import scrapy
import re


class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['blog.jobbole.com']
    start_urls = ['http://blog.jobbole.com/88673']

    def parse(self, response):

        title = response.xpath('//div[@class="entry-header"]/h1/text()')
        create_date = response.xpath("//p[@class='entry-meta-hide-on-mobile']/text()").extract()[0].strip().replace("·","").strip();
        praise_numbers = response.xpath("//span[contains(@class,'vote-post-up')]/h10/text()").extract();
        fav_nums = response.xpath("//span[contains(@class,'bookmark-btn')]/text()").extract()[0];
        match_re = re.match(r".*(\d+).*", fav_nums)
        if match_re:
            fav_nums = match_re.group(1)

        comment_nums = response.xpath("//a[@href='#article-comment']/span/text()").extract()[0];
        match_re = re.match(r".*(\d+).*", comment_nums)
        if match_re:
            comment_nums = match_re.group(1)

        content = response.xpath("//div[@class='entry']").extract()[0]

        tag_list = response.xpath("//p[@class='entry-meta-hide-on-mobile']/a").extract()

        tag_list = [element for element in tag_list if not element.strip().endswith("评论")]

        tags = ",".join(tag_list)

        # 通过css选择器提取字段
        title = response.css(".entry-header h1::text").extract()[0]
        pass
