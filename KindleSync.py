#!/usr/bin/env python
#-*-coding:utf-8 -*-

import re
import smtplib

from BeautifulSoup import BeautifulSoup

from email.Header import Header
from email.MIMEBase import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email import base64mime

bot_name = "KindleBot"
from_addr = "<kindlebot@kindle.bot>"
to_addr = "<xxxx@kindle.com>"

input_encode = 'gbk'
output_encode = 'utf-8'

base_url = "http://tieba.baidu.com"
index_url = base_url + r'/name/of/tieba/'

# regexes
title_filter_re = '第.*?章'

strip_html_tag = True

#last_pid_file = os.getcwd() + "/last_pid"
last_pid_file = "/home/dotcloud/code/last_pid"

last_pid = 0
try:
    f = open(last_pid_file, 'r')
    last_pid = int(f.readline())
    f.close()
except:
    pass
newest_pid = last_pid

def check_old_post(p_link):
    tmp = p_link.split('/')
    p_id = 0
    if tmp:
        p_id = int(tmp[-1])

    global newest_pid, last_pid

    if p_id > newest_pid:
        newest_pid = p_id

    if p_id > last_pid:
        return False
    return True

def send_mail(subject, content, attachment=None):

    mail = MIMEMultipart()
    mail['From'] = bot_name + " " + from_addr
    mail['To'] = bot_name + " " + to_addr
    mail['Subject'] = Header(subject, output_encode)

    text = MIMEText(subject, 'plain', output_encode)
    mail.attach(text)

    att = MIMEBase('application', 'octet-stream')
    att.set_payload(content, output_encode)
    att.add_header('content-disposition', 'attachment',
                   filename=base64mime.header_encode(subject + '.txt', output_encode))
    mail.attach(att)

    server = smtplib.SMTP('localhost')
    print "Sending %s to kindle..." % subject
    server.sendmail(from_addr, to_addr, mail.as_string())
    server.quit()


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


def get_content(url):
    post_page = url_fetch(url)
    soup = BeautifulSoup(post_page, fromEncoding=input_encode)
    content_list = soup.findAll('p', {'class' : 'd_post_content'})

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

def main():
    title_page = url_fetch(index_url)
    soup = BeautifulSoup(title_page, fromEncoding=input_encode)
    title_list = soup.findAll("td", {"class" : "thread_title"})

    for title in title_list:
        post_link = title.a['href'].encode(output_encode)
        post_title = title.a.renderContents(output_encode)
        # ignore old post
        if check_old_post(post_link) is True:
            continue

        # choose title which we really need.
        if title_filter_re is not None:
            if not re.findall(title_filter_re, post_title):
                continue

        # shorten the title, amazon seems not like long title...
        post_title = re.sub('^.*?第', '第', post_title)

        # get the real content
        output = get_content(base_url + post_link)

        if output is not "":
            send_mail(post_title, output)

    if newest_pid != 0:
        open(last_pid_file, 'w').write(str(newest_pid))

if __name__ == "__main__":
    main()
