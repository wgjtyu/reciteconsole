# -*- coding:utf8 -*-
import datetime
from datetime import date
from datetime import timedelta
from google.appengine.ext import db
from google.appengine.api import users

#保存帮助内容
class HelpMSG(db.Model):
    content=db.StringProperty(multiline=True)

#在建立用户数据时判断用户是否可以登录
class ValidUser(db.Model):
    email=db.EmailProperty()

#用来保存用户数据
class UserData(db.Model):
    userid=db.StringProperty()

class WordItem(db.Model):
    eword=db.StringProperty(multiline=False)
    cword=db.StringProperty(multiline=False)
    spell=db.StringProperty(multiline=False)
    adddate=db.DateTimeProperty(auto_now_add=True)
    addby=db.UserProperty()

class ReviewRecord(db.Model):
    witem=db.ReferenceProperty(WordItem)
    user=db.UserProperty()
    reviewdate=db.DateProperty()
    reviewed=db.BooleanProperty()
    def create(self,worditem,delay):
        self.witem=worditem.key()
        self.user=users.get_current_user()
        self.reviewdate=date.today()+timedelta(delay)
        self.reviewed=False
        self.put()

class ReciteRecord(db.Model):
    witem=db.ReferenceProperty(WordItem)
    user=db.UserProperty()
    rp=db.FloatProperty()
    recitedate=db.DateProperty()
    reval=db.IntegerProperty()
    rtotal=db.IntegerProperty() #total recite times
    rfailure=db.IntegerProperty() #failure times
    def create(self,worditem):
        self.witem=worditem.key()
        self.user=users.get_current_user()
        self.rp=0.0
        self.recitedate=date.today()
        self.reval=2
        self.rtotal=0
        self.rfailure=0
        self.put()
    def set(self,delta):
        self.rp=self.rp*0.7+0.3*delta
        self.rtotal=self.rtotal+1
        if delta:
            #this formula should be check again!
            self.reval=self.reval+int(1+self.rp)*2**int(self.rtotal-self.rfailure)
        else:
            rc=ReviewRecord()
            rc.create(self.witem,0)
            self.reval=1
            self.rfailure=self.rfailure+1
        self.recitedate=date.today()+timedelta(self.reval)
        self.put()

class LastRecite(db.Model):
    ritem=db.ReferenceProperty(ReciteRecord)
    user=db.UserProperty()

class LastReview(db.Model):
    ritem=db.ReferenceProperty(ReciteRecord)
    user=db.UserProperty()
