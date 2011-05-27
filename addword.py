#!/usr/bin/env python
import cgi
import os
from store import *
from generic import *
from google.appengine.api import users
from google.appengine.ext import webapp,db
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template

orig_path=os.path.join(os.path.dirname(__file__),r'htmlfiles/')
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

def main():
    application = webapp.WSGIApplication([('/m/addword',Addword)], debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
