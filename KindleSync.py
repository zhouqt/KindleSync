#!/usr/bin/env python
#-*-coding:utf-8 -*-

import re
import smtplib
import time

from BeautifulSoup import BeautifulSoup

from email.Header import Header
from email.MIMEBase import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email import base64mime


source_dict = [
    {
        'book_name': 'book1',
        'base_url'  : r'http://tieba.baidu.com',
        'title_url' : r'/name/of/tieba/',
        'type' : 'tieba',
        'title_html_tag' : 'td',
        'title_html_attr' : {'class' : 'thread_title'},
        'title_filter_re' : '第.*?章',
        'post_html_tag' : 'p',
        'post_html_attr' : {'class' : 'd_post_content'},
        'strip_html_tag' : True,
        'save_newest_pid': True,
        'last_post_id_file' : 'last_pid_1',
        'from_addr' : '<kindlebot@kindle.bot>',
        'to_addr' : ['<xxxx@kindle.com>'],
    },
    {
        'book_name': 'book2',
        'base_url'  : r'http://tieba.baidu.com',
        'title_url' : r'/name/of/tieba/',
        'type' : 'tieba',
        'title_html_tag' : 'div',
        'title_html_attr' : {'class' : 'th_lz'},
        'title_filter_re' : '第.*?章',
        'post_html_tag' : 'p',
        'post_html_attr' : {'class' : 'd_post_content'},
        'strip_html_tag' : True,
        'save_newest_pid': True,
        'last_post_id_file' : 'last_pid_2',
        'from_addr' : '<kindlebot@kindle.bot>',
        'to_addr' : ['<xxxx@kindle.com>'],
   }
]

def get_last_post_id(pid_file):
    last_pid = 0
    try:
        f = open(pid_file, 'r')
        last_pid = int(f.readline())
        f.close()
    except:
        pass
    return last_pid


def get_post_id(post_link):
    tmp = post_link.split('/')
    post_id = 0
    if tmp:
        post_id = int(tmp[-1])
    return post_id


def send_mail(from_addr, to_addr, subject, content, attachment=None,
              output_encode='utf-8'):

    mail = MIMEMultipart()
    mail['From'] = from_addr
    mail['To'] = ";".join(to_addr)
    mail['Subject'] = Header(subject, output_encode)

    text = MIMEText(content, 'plain', output_encode)
    mail.attach(text)

    for name, attach in attachment:
        att = MIMEBase('application', 'octet-stream')
        att.set_payload(attach, output_encode)
        name_encoded = base64mime.header_encode(name, output_encode)
        att.add_header('content-disposition', 'attachment',
                       filename="%s" % name_encoded)
        mail.attach(att)

    print "Sending %s to %s..." % (subject, to_addr),
    try:
        server = smtplib.SMTP('localhost')
        server.sendmail(from_addr, to_addr, mail.as_string())
        server.quit()
        print 'Done.'
        return True
    except Exception, e:
        print 'Failed.\n %s' % e
        return False


def url_fetch(url):
    try:
        import pycurl
        import StringIO
        c = pycurl.Curl()
        c.setopt(pycurl.URL, url)
        b = StringIO.StringIO()
        c.setopt(pycurl.WRITEFUNCTION, b.write)
        c.setopt(pycurl.FOLLOWLOCATION, 1)
        c.setopt(pycurl.MAXREDIRS, 5)
        c.perform()
        data = b.getvalue()
    except ImportError:
        # if no module pycurl in current system, use urllib instead.
        import urllib
        f = urllib.urlopen(url)
        data = f.read()
        f.close()

    return data


def get_content(url, html_tag, html_attr, strip_html_tag=True,
                input_encode='gbk', output_encode='utf-8'):
    """
    @param url: page of post title.
    @param html_tag: html tag I should get.
    @param html_attr: the html which has this attr will be picked up.
    @param strip_html_tag: whether I should remove all html tag.

    @return string of plain post text.
    """
    page = url_fetch(url)
    soup = BeautifulSoup(page, fromEncoding=input_encode)
    content_list = soup.findAll(html_tag, html_attr)

    # output is what I really want.
    output = ""
    for content in content_list:
        post = content.renderContents(output_encode)
        if strip_html_tag is True:
            # replace <br> with \n.
            post = re.sub('\<br.*?\>', '\n', post)
            post = re.sub('\<.*?\>', '', post)
        #XXX: ignore the comment which size is less then 200,
        #     need a more beautiful method here.
        if len(post) > 500:
            output += "\n- - - - - - \n"
            output += post
    return output


def get_title_list(url, html_tag, html_attr, title_filter_re=None,
                   last_post_id=None, get_post_id_func=get_post_id,
                   input_encode='gbk', output_encode='utf-8'):
    """
    @param url: page of post title.
    @param html_tag: html tag I should get.
    @param html_attr: the html which has this attr will be picked up.
    @param title_filter_re: filter for title.
    @param save_newest_pid: save newest post id, so I can get the latest post.

    @return a list contain post title and link.
    """
    page = url_fetch(url)
    # force encode content in utf-8, ignore invalid character.
    page = str(page).decode(input_encode, 'ignore').encode(output_encode)
    soup = BeautifulSoup(page, fromEncoding=input_encode)
    t_list = soup.findAll(html_tag, html_attr)

    newest_post_id = last_post_id
    title_list = []
    for title in t_list:
        post_link = title.a['href'].encode(output_encode)
        post_title = title.a.renderContents(output_encode)
        # ignore old post
        post_id = get_post_id_func(post_link)
        if post_id < last_post_id:
            continue

        # remember the newest post we get.
        if post_id > newest_post_id:
            newest_post_id = post_id
        # choose title which we really need.
        if title_filter_re is not None:
            if not re.findall(title_filter_re, post_title):
                continue

        # shorten the title, amazon seems not like long title...
        post_title = re.sub('^.*?第', '第', post_title)

        title_list.append((post_link, post_title))

    return newest_post_id, title_list


def main():

    for src in source_dict:
        url = src.get('base_url') + src.get('title_url')
        last_post_id = get_last_post_id(src.get('last_post_id_file'))
        newest_post_id, title_list = get_title_list(url,
                                    src.get('title_html_tag'),
                                    src.get('title_html_attr'),
                                    src.get('title_filter_re'),
                                    last_post_id,
                                    get_post_id,
                                    src.get('input_encode', 'gbk'),
                                    src.get('output_encode', 'utf-8'))

        output = ''
        for post_link, post_title in title_list:
            # get the real content
            output += '\n%s\n' % post_title
            url = src.get('base_url') + post_link
            output += get_content(url,
                                 src.get('post_html_tag'),
                                 src.get('post_html_attr'),
                                 src.get('strip_html_tag', True),
                                 src.get('input_encode', 'gbk'),
                                 src.get('output_encode', 'utf-8'))

        if output != "":
            send_mail(src.get('from_addr'),
                      src.get('to_addr'),
                      'Convert',
                      '',
                      [('%s-%s.txt' % src.get('book_name'),
                          time.strftime('%F-%R'), output)],
                      src.get('output_encode', 'utf-8'))

        if (src.get('save_newest_pid', True) is True) and \
           (newest_post_id > last_post_id):
            open(src.get('last_post_id_file'), 'w').write(str(newest_post_id))


if __name__ == "__main__":
    main()
