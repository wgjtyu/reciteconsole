# -*- coding:utf8 -*-
import datetime
from datetime import date
from datetime import timedelta
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.api import taskqueue

#保存帮助内容
class HelpMSG(db.Model):
    content=db.StringProperty(multiline=True)

#用来保存用户配置数据
class UserPrefs(db.Model):
    user=db.UserProperty(auto_current_user_add=True)
    tz_offset=db.IntegerProperty(default=8)   #时区
    reviewed=db.BooleanProperty()
    sendreviewmail=db.BooleanProperty(default=True) #是否发送复习提示邮件
    recitenum=db.IntegerProperty() #记住的单词数量

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
    eword=db.StringProperty(multiline=False)#英文
    cword=db.StringProperty(multiline=False)#中文
    spell=db.StringProperty(multiline=False)#音标

    thesaurus=db.ListProperty(db.Key)#该单词所属的词库

    #在导入单词后可能因此导入重复的词，这个标记表示该单词已经经过人工检查,没有重复
    checked=db.BooleanProperty(default=False)
    
    adddate=db.DateTimeProperty(auto_now_add=True)
    addby=db.UserProperty()
    sentence=db.ListProperty(db.Key)#指向包含此单词的句子

class Thesaurus(db.Model):
    name=db.StringProperty(multiline=False)
    description=db.StringProperty()
    wordlist=db.ListProperty(db.Key)#单词列表
    updatelock=db.BooleanProperty()#更新锁定

class ReviewRecord(db.Model):
    witem=db.ReferenceProperty(WordItem)
    user=db.UserProperty(auto_current_user_add=True)
    reviewdate=db.DateProperty()
    rp=db.FloatProperty(default=0.0)
    reviewed=db.BooleanProperty()
    def create(self,worditem,delay,rp):
        self.witem=worditem.key()
        self.user=users.get_current_user()
        self.reviewdate=get_user_date()+timedelta(delay)
        self.reviewed=False
        self.rp=rp
        self.put()

class ReciteRecord(db.Model):
    witem=db.ReferenceProperty(WordItem)
    user=db.UserProperty()
    rp=db.FloatProperty()         #记忆程度
    recitedate=db.DateProperty()  #下次测试日期
    reval=db.IntegerProperty()    #距下次测试间隔
    recited=db.BooleanProperty()  #已经记住?
    rtotal=db.IntegerProperty()   #总共测试次数
    rfailure=db.IntegerProperty() #测试中失败的次数
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
        user_prefs=get_userprefs(self.user.user_id())
        self.rp=self.rp*0.7+0.3*delta
        self.rtotal=self.rtotal+1
        rc=ReviewRecord()
        if not self.recited:
            self.recited=False
        if delta:#记住
            self.reval=self.reval+int(1+self.rp)*2**int(self.rtotal-self.rfailure)
            if self.rp<0.75:
                rc.create(self.witem,self.reval/2,self.rp)#未熟记时才去复习
            else:
                if(self.recited==False):
                    self.recited=True
                    user_prefs.recitenum=user_prefs.recitenum+1
                    user_prefs.put()
        else:#没记住
            rc.create(self.witem,1,self.rp)
            self.reval=2
            self.rfailure=self.rfailure+1
            if self.recited==True and self.rp>=0.75:
                self.recited=False
                user_prefs.recitenum=user_prefs.recitenum-1
                user_prefs.put()
        self.recitedate=get_user_date()+timedelta(self.reval)
        self.put()

class LastRecite(db.Model):
    ritem=db.ReferenceProperty(ReciteRecord)
    user=db.UserProperty()

class Sentence(db.Model):
    content=db.StringProperty(multiline=False)#英文
    translation=db.StringProperty(multiline=False)#中文
