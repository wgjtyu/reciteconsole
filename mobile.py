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

orig_path=os.path.join(os.path.dirname(__file__),r'htmlfiles/')

class MainHandler(webapp.RequestHandler):
    def get(self):
        self.response.out.write(GetHead())
        template_values= {
        }
        path=os.path.join(orig_path,'index.html')
        self.response.out.write(template.render(path,template_values))
        self.response.out.write(GetBottom(self.request.uri))

class UserInfo(webapp.RequestHandler):
    def post(self):
        userprefs=get_userprefs()
        userprefs.tz_offset=int(self.request.get('timezone'))
        userprefs.put()
        self.redirect('/m')
    def get(self):
        self.response.out.write(GetHead())
        if not users.get_current_user():
            self.redirect(users.create_login_url(self.request.uri))
        user=users.get_current_user()
        path=os.path.join(orig_path,'user.html')
        tz_offset=get_userprefs().tz_offset
        tv={
            'tz_offset':tz_offset
        }
        self.response.out.write(template.render(path,tv))
        self.response.out.write(GetBottom(self.request.uri))

class Addword(webapp.RequestHandler):
    def post(self):
        if not users.is_current_user_admin():
            self.redirect('/m')
        wordset=self.request.get('wordrecord')
        l=0
        if wordset.__len__()==0:
            self.redirect('/addword')
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
            template_values= {
                'addsucc':True,
            }
        path=os.path.join(orig_path,'addword.html')
        self.response.out.write(GetHead())
        self.response.out.write(template.render(path,template_values))
        self.response.out.write(GetBottom(self.request.uri))
    def get(self):
        if not users.get_current_user():
            self.redirect('/m')
        quiturl=users.create_logout_url(self.request.uri)
        template_values= {
            'addsucc':False,
            'quiturl':quiturl
        }
        path=os.path.join(orig_path,'addword.html')
        self.response.out.write(GetHead())
        self.response.out.write(template.render(path,template_values))
        self.response.out.write(GetBottom(self.request.uri))

class Recite(webapp.RequestHandler):
    def post(self):
        if not users.get_current_user():
            self.redirect("/m")
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
    def get(self):
        if not users.get_current_user():
            self.redirect("/m")
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
    def post(self):
        pass
    def get(self):
        if not users.get_current_user():
            self.redirect('/m')
        userprefs=get_userprefs()
        #if userprefs.userprefs.reviewed==False:
        userprefs.reviewed=True
        userprefs.put()
        self.response.out.write(GetHead())
        #try:
            #reviewrecords=ReviewRecord.gql("WHERE user = :1 AND reviewdate <= :2 ORDER BY rp DESC",users.get_current_user(),get_user_date())
        #except BadArgumentError:
        reviewrecords=ReviewRecord.gql("WHERE user = :1 AND reviewdate <= :2",users.get_current_user(),get_user_date())
        noreviewrecord=False
        for i in reviewrecords:
            if i.reviewed==False:
                i.reviewed=True
                if i.reviewdate<get_user_date():
                    i.reviewdate=get_user_date()
            if not (i.witem.spell and i.witem.spell!='None'):
                i.witem.spell=GetPS(i.witem.eword).decode('utf8')#得到拼写
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
    application = webapp.WSGIApplication([('/m', MainHandler),('/m/addword',Addword),('/m/recite',Recite),('/m/review',Review),('/m/query',Query),('/m/help',Help),('/m/user',UserInfo)], debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
