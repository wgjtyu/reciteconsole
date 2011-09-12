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
            tsu=db.get(self.request.get('tsuname'))
            if wordset.__len__()==0:
                self.redirect('/admin.addw')
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
            if parm=="addt":#添加词库
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
            tsus=db.GqlQuery("SELECT * FROM Thesaurus")
            tv={
                    "Tsus":tsus
                }
            path=os.path.join(orig_path,'addw.html')
            return template.render(path,tv)

        def mtsu():
            #TODO:显示单词列表
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
            body=None
        elif parm=="musr":
            body=None
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

class AddRcWord(webapp.RequestHandler):
    def post(self):
        user=users.User(self.request.get('user_email'))
        tsu=db.get(self.request.get('tsukey'))
        def work():
            for w in tsu.wordlist:
                reciterecords=ReciteRecord.gql('WHERE user=:1 and witem=:2',user)
                if reciterecords.count()==0:
                    # w not in user's reciterecords
                    # insert w into user's reciterecords
                    reciterecord=ReciteRecord()
                    reciterecord.create_w_u(word,user)
        db.run_in_transaction(work)

def main():
    app=webapp.WSGIApplication([('/admin.*',Admin),('/dailyjobs',DailyJobs),('/addrcword',AddRcWord)],debug=True)
    util.run_wsgi_app(app)

if __name__=='__main__':
    main()
