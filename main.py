#!/usr/bin/env python
# -*- coding:utf8 -*-
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
from google.appengine.api import mail
from functools import wraps
from google.appengine.ext.webapp.util import login_required

orig_path=os.path.join(os.path.dirname(__file__),r'htmlfiles/')

class MainHandler(webapp.RequestHandler):
    def get(self):
        self.redirect('/m')

class ReviewRss(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type']="text/xml"
        uid=self.request.path[4:-4]
        userprefs=UserPrefs.gql("WHERE user_id=:1",uid).fetch(1)
        if len(userprefs)==1:
            userpref=userprefs[0]
        else:
            return
        #get review records
        userpref.reviewed=True
        userpref.put()
        reviewrecords=ReviewRecord.gql("WHERE user = :1 AND reviewdate <= :2",userpref.user,get_user_date(user_id=uid))
        if len(reviewrecords)==0:#不存在今天的复习条目
            return
        now=datetime.datetime.now()+datetime.timedelta(0,0,0,0,0,userpref.tz_offset)
        now=now.strftime('%Y-%m-%d %X')
        tv= {
            'FeedTitle':'%s 的复习记录'.decode('utf8') % userpref.user.nickname(),
            'EntryTitle':get_user_date(uid).strftime('%Y-%m-%d'),
            'reviewrecords':reviewrecords,
            'nowtime':now
        }
        path=os.path.join(orig_path,'review.rss')
        self.response.out.write(template.render(path,tv))

def main():
    application = webapp.WSGIApplication([('/', MainHandler),('/rv/.*.rss',ReviewRss)], debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
