#!/usr/bin/env python
# -*- coding:utf8 -*-
import cgi
import datetime
import os
from store import *
from generic import *
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template

class Admin(webapp.RequestHandler):
    def post(self):
        if not users.is_current_user_admin():
            self.redirect('/m/')
        vemail=self.request.get('validuser')
        if vemail.__len__()!=0:
            validuser=ValidUser()
            validuser.email=vemail
            validuser.put()
            self.redirect('/m/admin')
    def get(self):
        tv= {}
        if not users.is_current_user_admin():
            self.redirect('/m/')
        self.response.out.write(GetHead())
        path=os.path.join(orig_path,'admin.html')
        self.response.out.write(template.render(path,tv))
        self.response.out.write(GetBottom(self.request.uri))

def main():
    app=webapp.WSGIApplication([('/m/admin',Admin)],debug=True)
    util.run_wsgi_app(app)

if __name__=='__main__':
    main()
