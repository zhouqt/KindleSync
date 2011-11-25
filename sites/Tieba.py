#!/usr/bin/env python
#-*-coding:utf-8 -*-

import re

from BeautifulSoup import BeautifulSoup

from sites import BaseSite

site_config = {
    'Tieba': {
        'base_url': r'http://tieba.baidu.com',
        'title_html_tag': 'td',
        'title_html_attr': {'class': 'thread_title'},
        'title_filter_re': '第.*?章',
        'post_html_tag': 'p',
        'post_html_attr': {'class': 'd_post_content'},
    },
    'Tieba2': {
        'base_url': r'http://tieba.baidu.com',
        'title_html_tag': 'div',
        'title_html_attr': {'class': 'th_lz'},
        'title_filter_re': '第.*?章',
        'post_html_tag': 'p',
        'post_html_attr': {'class': 'd_post_content'},
    },
}


class Tieba(object):
    def __init__(self, config):
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
        tmp = post_link.split('/')
        post_id = 0
        if tmp:
            post_id = int(tmp[-1])
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
        t_list = soup.findAll(html_tag, html_attr)

        newest_post = self.last_post
        title_list = []
        for title in t_list:
            post_link = title.a['href'].encode(output_encode)
            post_title = title.a.renderContents(output_encode)

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

            # shorten the title, amazon seems not like long title...
            post_title = re.sub('^.*?第', '第', post_title)

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
            post = content.renderContents(output_encode)
            if strip_html_tag is True:
                # replace <br> with \n.
                post = re.sub('\<br.*?\>', '\n', post)
                post = re.sub('\<.*?\>', '', post)
            #XXX: ignore the comment which size is less then 200,
            #     need a more beautiful method here.
            if len(post) > 500:
                output.append("- - - - - - ")
                output.append(post)
        return output


