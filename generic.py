# -*- coding:utf8 -*-
import os
import datetime
from store import *
from google.appengine.api import users
from google.appengine.ext.webapp import template
from google.appengine.api import urlfetch
from functools import wraps

#得到单词的音标
def GetPS(word):
    url='http://dict.cn/ws.php?utf8=true&q=%s' % word
    try:
        explanation=urlfetch.fetch(url).content
    except:
        return 'None'
    if explanation.find(r'<pron>')==-1:
        return 'None'
    explanation=explanation[explanation.find(r'<pron>')+6:explanation.find(r'</pron>')]
    return explanation
    #url='http://dict-co.iciba.com/api/dictionary.php?w=%s' % word
    #explanation=urlfetch.fetch(url).content
    #if explanation.find(r'<ps>')==-1:
    #    return 'None'
    #explanation=explanation[explanation.find(r'<ps>')+4:explanation.find(r'</ps>')]
    #return explanation

def requires_admin(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if not users.get_current_user():
            self.redirect(users.create_login_url(self.request.uri))
            return
        elif not users.is_current_user_admin():
            return self.error(403)
        else:
            return method(self, *args, **kwargs)
    return wrapper

