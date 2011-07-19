# -*- coding:utf8 -*-
import os
import datetime
from store import *
from google.appengine.api import users
from google.appengine.ext.webapp import template
from google.appengine.api import urlfetch

def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

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


