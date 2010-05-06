from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
import os
from google.appengine.ext.webapp import template
from google.appengine.ext.db import BadKeyError
from google.appengine.api import memcache
import words
import models

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

class CreatePhrase(webapp.RequestHandler):
  def post(self, bookmarklet):
    phrase = words.generatePhrase(3)
    dbPhrase = db.GqlQuery("SELECT * FROM Share WHERE phrase = :1", phrase).get()
    
    while dbPhrase:
      memcache.incr('phrase_hits', initial_value=0)
      phrase = words.generatePhrase(3)
      dbPhrase = db.GqlQuery("SELECT * FROM Share WHERE phrase = :1", phrase).get()
    
    share = db.GqlQuery("SELECT * FROM Share WHERE bookmarklet = :1", bookmarklet).get()
    if not share:
      share = Share()
      share.bookmarklet = bookmarklet
    
    share.phrase = phrase
    share.save()
    
    self.response.out.write(phrase)

class ShareLink(webapp.RequestHandler):
  def get(self, bookmarklet, link_key, share_phrase):
    # Find the link
    link = db.get(link_key)
    
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

    path = os.path.join(os.path.dirname(__file__), 'views/options.html')
    self.response.out.write(template.render(path, {'bookmarklet': bookmarklet, 'phrase': share_phrase}))

  def post(self, bookmarklet):
    # Do I need this?
    pass

application = webapp.WSGIApplication(
                                     [('/', Root),
                                     (r'/(.*)/create', CreateLink),
                                     (r'/(.*)/phrase', CreatePhrase),
                                     (r'/(.*)/options', Options),
                                     (r'/(.*)/(.*)/save', SaveLink),
                                     (r'/(.*)/(.*)/share/(.*)', ShareLink),
                                     (r'/(.*)/(.*)', RedirectToLink),
                                     (r'/(.*)', Links)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()