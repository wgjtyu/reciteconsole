import os
from google.appengine.api import users
from google.appengine.ext.webapp import template
from google.appengine.api import urlfetch
orig_path=os.path.join(os.path.dirname(__file__),'htmlfiles//')

def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

def GetPS(word):
    url='http://dict.cn/ws.php?utf8=true&q=%s' % word
    explanation=urlfetch.fetch(url).content
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
    if users.get_current_user():
        userlogin=True
        url=users.create_logout_url(requesturi)
        if users.is_current_user_admin():
            useradmin=True
    tv= {
        'userlogin':userlogin,
        'useradmin':useradmin,
        'url':url
    }
    path=os.path.join(orig_path,'bottom.html')
    return template.render(path,tv)
