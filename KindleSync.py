#!/usr/bin/env python
#-*-coding:utf-8 -*-

import os
import sys
import smtplib
import time
import imp

from email.Header import Header
from email.MIMEBase import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email import base64mime

dirname = os.path.dirname(sys.modules[__name__].__file__)
sites_dir = os.path.abspath(os.path.join(dirname, 'sites'))
sys.path.insert(0, sites_dir)

from sites import SiteDispatcher
from sites import BaseSite
from config import default_config, source_list

def parse_config(site_config, source):
    cfg = default_config.copy()
    source_type = source.get('site_type')
    if source_type not in site_config.keys():
        raise BaseSite.SiteConfigNotFoundError(source_type)

    # Apply site config.
    cfg.update(site_config[source_type])
    # Apply this source's config
    cfg.update(source)

    return cfg


def send_mail(from_addr, to_addr, subject, content, attachment=None,
              output_encode='utf-8'):

    mail = MIMEMultipart()
    mail['From'] = from_addr
    mail['To'] = ';'.join(to_addr)
    mail['Subject'] = Header(subject, output_encode)

    text = MIMEText(content, 'plain', output_encode)
    mail.attach(text)

    att_names = []
    for name, attach in attachment:
        att_names.append(name)
        att = MIMEBase('application', 'octet-stream')
        att.set_payload(attach, output_encode)
        name_encoded = base64mime.header_encode(name, output_encode)
        att.add_header('content-disposition', 'attachment',
                       filename='%s' % name_encoded)
        mail.attach(att)

    print 'Sending %s to %s...' % (subject, to_addr),
    try:
        server = smtplib.SMTP('localhost')
        server.sendmail(from_addr, to_addr, mail.as_string())
        server.quit()
        print 'Done.'
        print 'Attachment list:\n %s' % '\n '.join(att_names)
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


def load_module(site_type):
    # Load site module.
    module_path = os.path.join(sites_dir, '%s.py' % site_type)
    if not os.path.isfile(module_path):
        raise BaseSite.SiteConfigNotFoundError(site_type)
    f, p, d = imp.find_module(site_type, [sites_dir])
    site_module = imp.load_module(site_type, f, p, d)
    f.close()

    # Get the site config
    site_config = site_module.site_config
    # Get the site class
    SiteClass = getattr(site_module, site_type)

    return site_config, SiteClass


def main():
    for s in source_list:
        site_config, SiteClass = load_module(s.get('site_type'))

        src = parse_config(site_config, s)
        site = SiteClass(src)

        page = url_fetch(src.get('base_url') + src.get('title_url'))
        newest_post, title_list = site.get_titles(page)

        # Sort the title for better read experience.
        title_list = sorted(title_list, key=lambda l: l[0])

        output = ''
        for post_link, post_title in title_list:
            # get the real content
            output += '\n%s\n' % post_title
            page = url_fetch(src.get('base_url') + post_link)
            output += '\n'.join(site.get_content(page))

        if output != '':
            file_name = '%s-%s.txt' % (src.get('book_name'),
                                       time.strftime('%F-%R'))
            send_mail(src.get('from_addr'),
                      src.get('to_addr'),
                      'Convert',
                      '',
                      [(file_name, output)],
                      src.get('output_encode', 'utf-8'))

        if (src.get('save_newest_pid', True) is True) and \
           (newest_post_id > last_post_id):
            open(src.get('last_post_id_file'), 'w').write(str(newest_post_id))


if __name__ == '__main__':
    main()
