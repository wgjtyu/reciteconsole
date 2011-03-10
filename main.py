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
import logging
from store import *
from generic import *
from google.appengine.api import users
from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import mail

orig_path=os.path.join(os.path.dirname(__file__),r'htmlfiles/')

class MainHandler(webapp.RequestHandler):
    def get(self):
        self.redirect('/m')

class DailyJobs(webapp.RequestHandler):
    def get(self):
        revieweduserprefs=UserPrefs.gql("WHERE reviewed=True")
        num=0
        for userpref in revieweduserprefs:
            reviewrecords=ReviewRecord.gql('WHERE user= :1 AND reviewdate < :2 AND reviewed=True',userpref.user,get_user_date(userpref.user.user_id()))
            if reviewrecords.count()==0:
                continue
            logging.info("USER:%s" % userpref.user.nickname())
            usernum=0
            for i in reviewrecords:
                userpref.reviewed=False
                userpref.put()
                usernum=usernum+1
                i.delete()
            logging.info("Deleted %d review logs" % usernum)
            num=num+usernum
            #呼叫发送复习记录邮件程序
        logging.info('Totally deleted %d review logs.' % num)
        self.response.out.write('Deleted %d logs.' % num)

def main():
    application = webapp.WSGIApplication([('/', MainHandler),('/dailyjobs',DailyJobs)], debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
