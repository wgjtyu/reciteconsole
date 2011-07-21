#!/usr/bin/env python
# -*- coding:utf8 -*-
import cgi
import datetime
import os
import logging
from store import *
from generic import *
from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template

class Admin(webapp.RequestHandler):
    def post(self):
        vemail=self.request.get('validuser')
        if vemail.__len__()!=0:
            validuser=ValidUser()
            validuser.email=vemail
            validuser.put()
            self.redirect('/m/admin')
    def get(self):
        stat_items=memcache.get_stats().iteritems()
        memlog=''
        for item in stat_items:
            memlog=memlog+'%s=%d ' % item
        tv= {
            'memlog':memlog
            }
        self.response.out.write(GetHead())
        path=os.path.join(orig_path,'admin.html')
        self.response.out.write(template.render(path,tv))
        self.response.out.write(GetBottom(self.request.uri))

class DailyJobs(webapp.RequestHandler):
    def get(self):
        revieweduserprefs=UserPrefs.gql("WHERE reviewed=True")
        num=0
        for userpref in revieweduserprefs:
            reviewrecords=ReviewRecord.gql('WHERE user= :1 AND reviewdate < :2 AND reviewed=True',userpref.user,get_user_date(userpref.user.user_id()))
            if reviewrecords.count()==0:
                continue
            logging.info("USER:%s" % userpref.user.nickname())
            reviewnum=0
            userpref.reviewed=False
            userpref.sendreviewmail=False
            userpref.put()
            for i in reviewrecords:
                reviewnum=reviewnum+1
                i.delete()
            logging.info("Deleted %d review logs" % reviewnum)
            num=num+reviewnum

            #呼叫发送复习记录邮件程序
            if userpref.sendreviewmail==False:
                continue
            userpref.reviewed=True
            userpref.put()
            sendreviewrecords=ReviewRecord.gql('WHERE user=:1 AND reviewdate=:2',userpref.user,get_user_date(userpref.user.user_id()))
            messagebody=''
            for i in sendreviewrecords:
                messagebody=messagebody+i.witem.eword+'['+i.witem.spell+']'+i.witem.cword
                i.reviewed=True
                i.put()
            mail.send_mail(
                    sender='ReciteConsole<wgjtyu@gmail.com>',
                    to=userpref.user.email(),
                    subject="Today's Review Records",
                    body=messagebody)
            logging.info('also send review records to his mailbox')
        logging.info('Totally deleted %d review logs.' % num)
        self.response.out.write('Deleted %d logs.' % num)

def main():
    app=webapp.WSGIApplication([('/m/admin',Admin),('/dailyjobs',DailyJobs)],debug=True)
    util.run_wsgi_app(app)

if __name__=='__main__':
    main()
