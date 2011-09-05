#!/usr/bin/env python
# -*- coding:utf8 -*-
import cgi
import datetime
import os
import logging
from store import *
from generic import *
from mobile import *
from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template

orig_path=os.path.join(os.path.dirname(__file__),r'htmlfiles/admin/')

class Admin(webapp.RequestHandler):
    def post(self):
        def addw():
            wordset=self.request.get('wordrecord')
            l=0
            if wordset.__len__()==0:
                self.redirect('/admin')
            worditems=wordset.split('\n')
            for i in worditems:
                w=i.split('|')
                if w.__len__()!=2:
                    break
                worditem=WordItem()
                worditem.eword=w[0]
                worditem.cword=w[1]
                worditem.addby=users.get_current_user()
                worditem.put()

        def mtsu():
            parm=self.request.path[12:16];
            if parm=="addt":
                tsun=self.request.get("tsuname")
                if tsun!="":
                    tsu=Thesaurus()
                    tsu.name=tsun
                    tsu.put()

        parm=self.request.path[7:11]
        if parm=="addw":
            addw()#未完成
            self.redirect('/admin.addw')
        elif parm=="mtsu":
            mtsu()
            self.redirect('/admin.mtsu')
        elif parm=="chkw":
            self.redirect('/admin.chkw')
        elif parm=="musr":
            self.redirect('/admin.musr')

    def get(self):
        def addw():
            tv={}
            path=os.path.join(orig_path,'addw.html')
            return template.render(path,tv)

#TODO:显示单词列表
        def mtsu():
            parm=self.request.path[12:16]
            if parm=="list":
                pass
            tsus=db.GqlQuery("SELECT * FROM Thesaurus")
            tv={
                    "Tsus":tsus
               }
            path=os.path.join(orig_path,'mtsu.html')
            return template.render(path,tv)

        def stat():
            stat_items=memcache.get_stats().iteritems()
            memlog=''
            for item in stat_items:
                memlog=memlog+'%s=%d ' % item
            tv= {
                'memlog':memlog
            }
            path=os.path.join(orig_path,'stat.html')
            return template.render(path,tv)

        path=os.path.join(orig_path,'index.html')
        parm=self.request.path[7:11]
        if parm=="addw":
            body=addw()
        elif parm=="mtsu":
            body=mtsu()
        elif parm=="chkw":
            body=NONE
        elif parm=="musr":
            body=NONE
        else:
            body=stat()
        tv={
           'adminbody':body
           }
        self.response.out.write(template.render(path,tv))

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
                    sender='ReciteConsole <rc@reciteconsole.appspotmail.com>',
                    to=userpref.user.email(),
                    subject="Today's Review Records",
                    body=messagebody)
            logging.info('also send review records to his mailbox')
        logging.info('Totally deleted %d review logs.' % num)
        self.response.out.write('Deleted %d logs.' % num)

def main():
    app=webapp.WSGIApplication([('/admin.*',Admin),('/dailyjobs',DailyJobs)],debug=True)
    util.run_wsgi_app(app)

if __name__=='__main__':
    main()
