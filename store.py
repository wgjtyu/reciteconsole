# -*- coding:utf8 -*-
import datetime
from datetime import date
from datetime import timedelta
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import memcache

#保存帮助内容
class HelpMSG(db.Model):
    content=db.StringProperty(multiline=True)

#用来保存用户数据
class UserPrefs(db.Model):
    user=db.UserProperty(auto_current_user_add=True)
    tz_offset=db.IntegerProperty(default=0)
    reviewed=db.BooleanProperty()

    def cache_set(self):
        memcache.set(self.key().name(),self,namespace=self.key().kind())

    def put(self):
        self.cache_set()
        db.Model.put(self)

def get_user_date(user_id=None):
    userprefs=get_userprefs(user_id)
    now=datetime.datetime.now()+datetime.timedelta(0,0,0,0,0,userprefs.tz_offset)
    today=now.date()
    return today

def get_userprefs(user_id=None):
    if not user_id:
        user=users.get_current_user()
        if not user:
            return None
        user_id=user.user_id()
        userprefs=memcache.get(user_id,namespace='UserPrefs')
    if not userprefs:
        key=db.Key.from_path('UserPrefs',user_id)
        userprefs=db.get(key)
        if userprefs:
            userprefs.cache_set()
        else:
            userprefs=UserPrefs(key_name=user_id)
    return userprefs

class WordItem(db.Model):
    eword=db.StringProperty(multiline=False)
    cword=db.StringProperty(multiline=False)
    spell=db.StringProperty(multiline=False)
    adddate=db.DateTimeProperty(auto_now_add=True)
    addby=db.UserProperty()

class ReviewRecord(db.Model):
    witem=db.ReferenceProperty(WordItem)
    user=db.UserProperty(auto_current_user_add=True)
    reviewdate=db.DateProperty()
    reviewed=db.BooleanProperty()
    def create(self,worditem,delay):
        self.witem=worditem.key()
        self.user=users.get_current_user()
        self.reviewdate=get_user_date()+timedelta(delay)
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
        self.recitedate=get_user_date()
        self.reval=2
        self.rtotal=0
        self.rfailure=0
        self.put()
    def set(self,delta):
        self.rp=self.rp*0.7+0.3*delta
        self.rtotal=self.rtotal+1
        rc=ReviewRecord()
        if delta:
            self.reval=self.reval+int(1+self.rp)*2**int(self.rtotal-self.rfailure)
            rc.create(self.witem,self.reval/2)
        else:
            rc.create(self.witem,0)
            self.reval=1
            self.rfailure=self.rfailure+1
        self.recitedate=get_user_date()+timedelta(self.reval)
        self.put()

class LastRecite(db.Model):
    ritem=db.ReferenceProperty(ReciteRecord)
    user=db.UserProperty()

class LastReview(db.Model):
    ritem=db.ReferenceProperty(ReciteRecord)
    user=db.UserProperty()
