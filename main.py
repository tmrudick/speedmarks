from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
import os
from google.appengine.ext.webapp import template
from google.appengine.ext.db import BadKeyError
from google.appengine.api import memcache
import words
from models import *

class Root(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'views/index.html')
        self.response.out.write(template.render(path, {}))

class Links(webapp.RequestHandler):
    def get(self, bookmarklet):
      links = db.GqlQuery("SELECT * FROM Link WHERE bookmarklet = :1 ORDER BY created_time DESC", bookmarklet).fetch(100)
      
      for link in links:
        if len(link.title) > 80:
          link.title = link.title[0:80] + '...'
        if len(link.url) > 80:
          link.url = link.url[0:80] + '...'
      
      path = os.path.join(os.path.dirname(__file__), 'views/list.html')
      self.response.out.write(template.render(path, {'links': links, 'bookmarklet': bookmarklet}))      
      
class CreateLink(webapp.RequestHandler):
    def get(self, bookmarklet):
      if self.request.get('url') == "":
        path = os.path.join(os.path.dirname(__file__), 'views/error.html')
        self.response.out.write(template.render(path, {}))
        return
      
      link = Link()
      link.url = self.request.get('url')
      link.title = self.request.get('title')
      link.bookmarklet = bookmarklet
      
      link.put()
            
      self.redirect(link.url)

class DeleteLink(webapp.RequestHandler):
  def get(self, bookmarklet, link_key):
    try:
      link = db.get(link_key)
    except BadKeyError:
      path = os.path.join(os.path.dirname(__file__), 'views/error.html')
      self.response.out.write(template.render(path, {}))
      return      
      
    if link.bookmarklet == bookmarklet:
      link.delete()
      
    self.redirect('/' + bookmarklet)
      
class RedirectToLink(webapp.RequestHandler):
  def get(self, bookmarklet, link_key):
    try:
      link = db.get(link_key)
    except BadKeyError:
      path = os.path.join(os.path.dirname(__file__), 'views/error.html')
      self.response.out.write(template.render(path, {}))
      return
      
    if link == None:
      path = os.path.join(os.path.dirname(__file__), 'views/error.html')
      self.response.out.write(template.render(path, {}))
    elif link.bookmarklet == bookmarklet:
      # Increment how many links we have served
      memcache.incr('links_served', initial_value=0)
      if not link.save_for_later:
        link.delete() 
        
      self.redirect(link.url)
    else:
      self.redirect('/')

class SaveLink(webapp.RequestHandler):
  def get(self, bookmarklet, link_key):
    try:
      link = db.get(link_key)
    except BadKeyError:
       path = os.path.join(os.path.dirname(__file__), 'views/error.html')
       self.response.out.write(template.render(path, {}))
       return
    
    link.save_for_later = not link.save_for_later   
    link.save()
    
    self.redirect('/' + bookmarklet)

class ShareNewLink(webapp.RequestHandler):
  def post(self, bookmarklet):
    url = self.request.get("url")
    title = self.request.get("title")
    share_phrase = self.request.get("share")
    
    other_bookmarklet = db.GqlQuery("SELECT * FROM Share WHERE phrase = :1", share_phrase).get()
    
    if other_bookmarklet:
      shared_link = Link()
      shared_link.bookmarklet = other_bookmarklet.bookmarklet
      shared_link.url = url
      shared_link.title = title
      shared_link.save()    
    
    self.redirect('/' + bookmarklet)

class ShareExistingLink(webapp.RequestHandler):
  def post(self, bookmarklet, link_key):
    # Find the link
    link = db.get(link_key)
    share_phrase = self.request.get("share")
    
    if link and link.bookmarklet == bookmarklet:
      # Find the other bookmarklet guid
      other_bookmarklet = db.GqlQuery("SELECT * FROM Share WHERE phrase = :1", share_phrase).get()
      
      if other_bookmarklet:
        shared_link = Link()
        shared_link.bookmarklet = other_bookmarklet.bookmarklet
        shared_link.url = link.url
        shared_link.title = link.title
        shared_link.save()
        
    self.redirect('/' + bookmarklet)
      
class Options(webapp.RequestHandler):
  def get(self, bookmarklet):
    share = db.GqlQuery("SELECT * FROM Share WHERE bookmarklet = :1", bookmarklet).get()
    
    share_phrase = ""
    
    if share:
      share_phrase = share.phrase

    self.response.out.write(share_phrase)

  def post(self, bookmarklet):
    allow_sharing = self.request.get('allow')
    
    share = db.GqlQuery("SELECT * FROM Share WHERE bookmarklet = :1", bookmarklet).get()
    
    if allow_sharing == 'true':
      phrase = words.generatePhrase(2)
      dbPhrase = db.GqlQuery("SELECT * FROM Share WHERE phrase = :1", phrase).get()

      while dbPhrase:
        memcache.incr('phrase_hits', initial_value=0)
        phrase = words.generatePhrase(2)
        dbPhrase = db.GqlQuery("SELECT * FROM Share WHERE phrase = :1", phrase).get()

      if not share:
        share = Share()
        share.bookmarklet = bookmarklet

      share.phrase = phrase
      share.save()

      self.response.out.write(phrase)
    else:
      if share:
        share.delete()
      self.response.out.write("")

class Help(webapp.RequestHandler):
  def get(self):
    path = os.path.join(os.path.dirname(__file__), 'views/help.html')
    self.response.out.write(template.render(path, {}))

application = webapp.WSGIApplication(
                                     [('/', Root),
                                     (r'/help', Help),
                                     (r'/(.*)/create', CreateLink),
                                     (r'/(.*)/options', Options),
                                     (r'/(.*)/save/(.*)', SaveLink),
                                     (r'/(.*)/share', ShareNewLink),
                                     (r'/(.*)/share/(.*)', ShareExistingLink),
                                     (r'/(.*)/(.*)', RedirectToLink),
                                     (r'/(.*)', Links)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()