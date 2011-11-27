#!/usr/bin/env python
#-*-coding:utf-8 -*-

import re

from BeautifulSoup import BeautifulSoup

from sites import BaseSite


site_config = {
    'Xiucaiwu': {
        'base_url': r'http://b10.xiucai.cc/',
        'title_html_tag': 'div',
        'title_html_attr': {'class': 'result'},
        'title_filter_re': None,
        'title_next_page': 'a',
        'title_next_page_re': {'title': '下一页'},
        'post_html_tag': 'p',
        'post_html_attr': {'class': 'read'},
        'input_encode': 'utf-8'
    },
}


class Xiucaiwu(BaseSite.BaseSite):
    def __init__(self, config):
        BaseSite.BaseSite.__init__(self, config)
        source_type = config.get("site_type")
        if source_type not in site_config.keys():
            raise BaseSite.SiteConfigNotFoundError(source_type)

        self.config = site_config.get(source_type).copy()
        self.config.update(config)
        f = self.config.get("last_post_file")
        self.last_post = 0
        if f:
            self.last_post = self.get_last_post(f)
        self.check_post_func = self.check_post


    def get_last_post(self, pid_file):
        last_pid = 0
        try:
            f = open(pid_file, 'r')
            last_pid = int(f.readline())
            f.close()
        except:
            pass
        return last_pid


    def check_post(self, post_link):
        post_id = 0
        tmp = re.findall(r"cid=(\d+)&", post_link)
        if tmp:
            post_id = int(tmp[0])
        return post_id


    def get_titles(self, page, check_post_func=None):
        """
        @param page: page of post title.

        @return a list contain post title and link.
        """
        html_tag = self.config.get("title_html_tag")
        html_attr = self.config.get("title_html_attr")
        title_filter_re = self.config.get("title_filter_re")
        input_encode = self.config.get("input_encode", "gbk")
        output_encode = self.config.get("output_encode", "utf-8")

        # force encode content in utf-8, ignore invalid character.
        page = str(page).decode(input_encode, 'ignore').encode(output_encode)

        soup = BeautifulSoup(page, fromEncoding=input_encode)
        titles = soup.find(html_tag, html_attr)
        t_list = titles.findChildren('a')

        newest_post = self.last_post
        title_list = []
        for title in t_list:
            post_link = title['href'].encode(output_encode)
            post_title = title.renderContents(output_encode)

            if not check_post_func:
                check_post_func = self.check_post_func

            if check_post_func:
                post_id = check_post_func(post_link)
                # ignore old post
                if post_id < self.last_post:
                    continue
                # remember the newest post we get.
                if post_id > newest_post:
                    newest_post = post_id

            # choose title which we really need.
            if title_filter_re is not None:
                if not re.findall(title_filter_re, post_title):
                    continue

            title_list.append((post_link, post_title))

        return newest_post, title_list


    def get_title_next_page(self, page):
        pass


    def get_content(self, page):
        """
        @param page: page of post title.

        @return list of plain post text.
        """
        html_tag = self.config.get("post_html_tag")
        html_attr = self.config.get("post_html_attr")
        strip_html_tag = self.config.get("strip_html_tag", True)
        input_encode = self.config.get("input_encode", 'gbk')
        output_encode = self.config.get("output_encode", 'utf-8')

        soup = BeautifulSoup(page, fromEncoding=input_encode)
        content_list = soup.findAll(html_tag, html_attr)

        # output is what I really want.
        output = []
        for content in content_list:
            # Remove 'a' tag in content.
            for a in content.findAll('a'):
                a.extract()
            post = content.renderContents(output_encode)
            if strip_html_tag is True:
                post = re.sub("本站.*?$|手机看书.*?$", "", post)
                # replace <br> with \n.
                post = re.sub('\<br.*?\>', '\n', post)
            print post
        return output
