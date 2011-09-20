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
            if wordset.__len__()==0:
                self.response.out.write('none word')
                self.redirect('/admin.addw')
            tsu=db.get(self.request.get('tsukey'))
            worditems=wordset.split('\n')
            for i in worditems:
                w=i.split('|')
                if w.__len__()!=2:
                    continue
                worditem=WordItem()
                worditem.eword=w[0]
                worditem.cword=w[1]
                worditem.addby=users.get_current_user()
                worditem.thesaurus.append(tsu.key())
                worditem.put()
                tsu.wordlist.append(worditem.key())
            tsu.updatelock=True
            taskqueue.add(url='/chkrcword',params={'thesaurus':tsu.key()})
            tsu.put()

        def mtsu():
            parm=self.request.path[12:16]
            if parm=="addt":#添加词库
                tsun=self.request.get("tsuname")
                if tsun!="":
                    tsu=Thesaurus()
                    tsu.name=tsun
                    tsu.updatelock=True
                    tsu.put()

        def chkw():#post
            rdkey=self.request.path[12:]
            #取得删除的词
            delw=db.get(self.request.get('delword'))
            #取得替换的词
            oldw=db.get(self.request.get('rudword'))
            #删除重复的单词，还要修改词库引用关系
            for tsu in delw.thesaurus:
                gtsu=db.get(tsu)
                gtsu.wordlist.remove(delw.key())
                if tsu not in oldw.thesaurus:
                    oldw.thesaurus.append(tsu)
                    gtsu.wordlist.append(oldw.key())
                gtsu.put()
            oldw.put()
            db.delete(delw)
            db.delete(rdkey)

        parm=self.request.path[7:11]
        if parm=="addw":
            addw()
            self.redirect('/admin.addw')
        elif parm=="mtsu":
            mtsu()
            self.redirect('/admin.mtsu')
        elif parm=="chkw":
            chkw()
            self.redirect('/admin.chkw')
        elif parm=="musr":
            self.redirect('/admin.musr')
        #self.redirect(self.request.uri)

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
                tsukey=self.request.path[17:]
                tsus=db.get(tsukey)
                wl=db.get(tsus.wordlist)
                tv={
                        "wordlist":wl
                   }
                path=os.path.join(orig_path,'mtsu.list.html')
                return template.render(path,tv)
            tsus=db.GqlQuery("SELECT * FROM Thesaurus")
            tv={
                    "Tsus":tsus
               }
            path=os.path.join(orig_path,'mtsu.html')
            return template.render(path,tv)

        def chkw():
            query=ReduplicateWord.all()
            rw=query.fetch(1)
            if len(rw)==1:
                wl=db.get(rw[0].wordlist)
                nw=db.get(db.Key(rw[0].newword))
                tv={
                        "rwkey":rw[0].key(),
                        "wordlist":wl,
                        "newword":nw,
                        "nordw":False
                   }
            else: 
                tv={
                        "nordw":True
                   }
            path=os.path.join(orig_path,'chkw.html')
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
            body=chkw()
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
        #从email构造出User对象
        user=users.User(self.request.get('user_email'))
        tsu=db.get(self.request.get('tsukey'))
        log="Add %s to %s 's ReciteRecord" % (tsu.name,user.email())
        logging.info(log)
        self.response.out.write(log)
        #def work():
        for w in tsu.wordlist:
            reciterecords=ReciteRecord.gql('WHERE user=:1 and witem=:2',user,w)
            if reciterecords.count()==0:
                # w not in user's reciterecords,insert w into user's reciterecords
                reciterecord=ReciteRecord()
                reciterecord.create_w_u(db.get(w),user)
        #db.run_in_transaction(work)

class ChkRcWord(webapp.RequestHandler):#检查词库中单词是否有重复
    def post(self):
        tsu=db.get(self.request.get('thesaurus'))
        for w in tsu.wordlist:
            #TODO:这里对数据库调用次数太多，可以一次性get整个列表
            word=db.get(w)
            witems=WordItem.gql('WHERE eword=:1',word.eword)
            if witems.count()!=1:
                r=ReduplicateWord()
                r.newword=str(word.key())
                for witem in witems:
                    if witem.key()!=word.key():
                        r.wordlist.append(witem.key())
                r.put()

def main():
    app=webapp.WSGIApplication([('/admin.*',Admin),('/dailyjobs',DailyJobs),('/addrcword',AddRcWord),('/chkrcword',ChkRcWord)],debug=True)
    util.run_wsgi_app(app)

if __name__=='__main__':
    main()
