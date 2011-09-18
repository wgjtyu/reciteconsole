#!/usr/bin/env python
# -*- coding:utf8 -*-
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import cgi
import datetime
import os
from store import *
from generic import *
from google.appengine.api import users
from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.ext.webapp.util import login_required

orig_path=os.path.join(os.path.dirname(__file__),r'htmlfiles/m/')

def GetHead():
    tv= {
        'user':users.get_current_user(),
    }
    path=os.path.join(orig_path,'head.html')
    return template.render(path,tv)

def GetBottom(requesturi):
    useradmin=False
    userlogin=False
    url=users.create_login_url(requesturi)
    rcnum=0
    rvnum=0
    if users.get_current_user():
        userlogin=True
        userprefs=get_userprefs()
        now=datetime.datetime.now()+datetime.timedelta(0,0,0,0,0,userprefs.tz_offset)
        now=now.strftime('%Y-%m-%d %X')
        url=users.create_logout_url(requesturi)
        reciterecords=ReciteRecord.gql('WHERE user=:1 and recitedate<=:2 limit 5',users.get_current_user(),get_user_date())
        rcnum=reciterecords.count()
        reviewrecords=ReviewRecord.gql("WHERE user = :1 AND reviewdate <= :2",users.get_current_user(),get_user_date())
        rvnum=reviewrecords.count()
        if users.is_current_user_admin():
            useradmin=True
    else:
        now=None
    tv= {
        'userlogin':userlogin,
        'useradmin':useradmin,
        'usertime':now,
        'url':url,
        'recitenum':rcnum,
        'reviewnum':rvnum
    }
    path=os.path.join(orig_path,'bottom.html')
    return template.render(path,tv)

class MainHandler(webapp.RequestHandler):
    def get(self):
        self.response.out.write(GetHead())
        userranking=memcache.get('uranking',namespace='sysfunction')
        if not userranking:
            userranking=db.GqlQuery("SELECT * FROM UserPrefs ORDER BY recitenum DESC LIMIT 5")
            memcache.set('uranking',userranking,60*10)
        template_values= {
                'userranking':userranking,
        }
        path=os.path.join(orig_path,'index.html')
        self.response.out.write(template.render(path,template_values))
        self.response.out.write(GetBottom(self.request.uri))

class UserInfo(webapp.RequestHandler):
    def post(self):
        if not users.get_current_user():
            self.redirect('/m')
        userprefs=get_userprefs()
        userprefs.tz_offset=int(self.request.get('timezone'))
        if 'rvmail' in self.request.get('rvmail'):
            sendreviewmail=True
        else:
            sendreviewmail=False
        userprefs.sendreviewmail=sendreviewmail
        userprefs.put()
        self.redirect('/m')
    @login_required
    def get(self):
        self.response.out.write(GetHead())
        if not users.get_current_user():
            self.redirect(users.create_login_url(self.request.uri))
        user=users.get_current_user()
        path=os.path.join(orig_path,'user.html')
        user_prefs=get_userprefs()
        tz_offset=user_prefs.tz_offset
        if user_prefs.sendreviewmail:
            rvmail='checked'
        else:
            rvmail=''
        if not user_prefs.recitenum:
            user_prefs.recitenum=0
            user_prefs.put()
        recitenum=user_prefs.recitenum
        tv={
            'tz_offset':tz_offset,
            'rvmail':rvmail,
            'recitenum':user_prefs.recitenum
        }
        self.response.out.write(template.render(path,tv))
        self.response.out.write(GetBottom(self.request.uri))

class Recite(webapp.RequestHandler):
    def post(self):
        lastrecites=db.GqlQuery("SELECT * FROM LastRecite Where user=:1",users.get_current_user())
        for i in lastrecites:
            if self.request.get(i.ritem.witem.eword)=='on': #remember
                delta=1
            elif self.request.get(i.ritem.witem.eword)=='off': #forgot
                delta=0
            else:
                continue
            i.ritem.set(delta)
        self.redirect("/m/recite")
    @login_required
    def get(self):
        self.response.out.write(GetHead())
        reciterecords=ReciteRecord.gql('WHERE user=:1 and recitedate<=:2 limit 5',users.get_current_user(),get_user_date())
        if reciterecords.count()==0:
            wordquery=WordItem.all()
            i=5
            for word in wordquery:
                if i==0:
                    break
                if word.reciterecord_set.count()!=0:
                    unrecite=True
                    for wrc in word.reciterecord_set:
                        if wrc.user==users.get_current_user():
                            unrecite=False
                            break
                if word.reciterecord_set.count()==0 or unrecite:
                    reciterecord=ReciteRecord()
                    reciterecord.create(word)
                    i=i-1
            reciterecords=ReciteRecord().gql('WHERE user=:1 and recitedate<=:2 limit 5',users.get_current_user(),get_user_date())
        noreciterecord=False
        if reciterecords.count()==0:
            noreciterecord=True
        tv= {
            "noreciterecord":noreciterecord,
            "reciterecords":reciterecords,
        }
        lastrecites=db.GqlQuery("SELECT * FROM LastRecite WHERE user=:1",users.get_current_user())
        for i in lastrecites:
            i.delete()
        for i in reciterecords:
            lastrecite=LastRecite()
            lastrecite.ritem=i.key()
            lastrecite.user=users.get_current_user()
            lastrecite.put()
        path=os.path.join(orig_path,'recite.html')
        self.response.out.write(template.render(path,tv))
        self.response.out.write(GetBottom(self.request.uri))

class Review(webapp.RequestHandler):
    @login_required
    def get(self):
        userprefs=get_userprefs()
        userprefs.reviewed=True
        userprefs.put()
        self.response.out.write(GetHead())
        reviewrecords=ReviewRecord.gql("WHERE user = :1 AND reviewdate <= :2",users.get_current_user(),get_user_date())
        noreviewrecord=False
        for i in reviewrecords:
            if i.reviewed==False:
                i.reviewed=True
                if i.reviewdate<get_user_date():
                    i.reviewdate=get_user_date()
            if not (i.witem.spell and i.witem.spell!='None'):
                i.witem.spell=GetPS(i.witem.eword).decode('utf8')#得到拼写
                if i.witem.spell==None:
                    i.witem.spell='None'
                i.witem.put()
            i.put()
        if reviewrecords.count()==0:
            noreviewrecord=True
        tv= {
            "noreviewrecord":noreviewrecord,
            "reviewrecords":reviewrecords,
        }
        path=os.path.join(orig_path,'review.html')
        self.response.out.write(template.render(path,tv))
        self.response.out.write(GetBottom(self.request.uri))

class GuestBook(webapp.RequestHandler):
    def post(self):
        greeting=Greeting()
        if users.get_current_user():
            greeting.author=users.get_current_user()
        greeting.content=self.request.get('content')
        greeting.put()
        self.redirect('/guestbook')
    def get(self):
        greetings=db.GqlQuery("SELECT * FROM Greeting ORDER BY date DESC LIMIT 10")
        if users.get_current_user():
            url=users.create_logout_url(self.request.uri)
            userlogin=True
            useradmin=users.is_current_user_admin()
        else:
            url=users.create_login_url(self.request.uri)
            userlogin=False
            useradmin=False
        template_values= {
            'greetings':greetings,
        }
        self.response.out.write(GetHead())
        path=os.path.join(orig_path,'guestbook.html')
        self.response.out.write(template.render(path,template_values))
        self.response.out.write(GetBottom(self.request.uri))

class Query(webapp.RequestHandler):
    def get(self):
        if not users.get_current_user():
            self.redirect('/m')
        self.response.out.write(GetHead())
        self.response.out.write(GetBottom(self.request.uri))

class Help(webapp.RequestHandler):
    def get(self):
        self.response.out.write(GetHead())
        path=os.path.join(orig_path,'help.html')
        helpmsg=HelpMSG.all().get()
        if helpmsg:
            template_values={
                'helpcontent':helpmsg.content,
            }
        else:
            template_values={
            }
        self.response.out.write(template.render(path,template_values))
        self.response.out.write(GetBottom(self.request.uri))

def main():
    application = webapp.WSGIApplication([('/m', MainHandler),('/m/recite',Recite),('/m/review',Review),('/m/query',Query),('/m/help',Help),('/m/user',UserInfo)], debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
