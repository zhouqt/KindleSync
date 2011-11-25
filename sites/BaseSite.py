#!/usr/bin/env python
#-*-coding:utf-8 -*-

site_type_config = {
#    'site_name': {
#        'base_url': r'http://base.url',
#        'title_html_tag': 'tag',
#        'title_html_attr': {'class': 'attr'},
#        'title_filter_re': '第.*?章',
#        'post_html_tag': 'tag',
#        'post_html_attr': {'class': 'attr'},
#    },
}

class SiteError(Exception):
    pass

class SiteConfigError(SiteError):
    pass

class SiteConfigNotFoundError(SiteConfigError):
    def __init__(self, source_type):
        SiteConfigError.__init__(self, source_type)
        self.source_type = source_type

    def __str__(self):
        return 'Could not find site config for type "%s"' % self.source_type


class Site(object):
    """
    Here is an example of Site definiton, and it's interfaces
    """

    def __init__(self, config):
        pass


    def check_post(self):
        pass


    def get_content(self, page):
        pass


    def get_titles(self, page, check_post_func=None):
        pass
