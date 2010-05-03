from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
import os
from google.appengine.ext.webapp import template
from google.appengine.ext.db import BadKeyError

class Link(db.Model):
  url = db.StringProperty()
  title = db.StringProperty()
  bookmarklet = db.StringProperty()
  created_time = db.DateTimeProperty(auto_now_add=True)
  save_for_later = db.BooleanProperty();

class DailyStatistic(db.Model):
  current_links = db.IntegerProperty()
  links_served = db.IntegerProperty()
  user_count = db.IntegerProperty()
  date = db.DateProperty(auto_now_add=True)

class SiteStatistics(db.Model):
  current_links = db.IntegerProperty()
  links_served = db.IntegerProperty()
  user_count = db.IntegerProperty()

class Root(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'views/index.html')
        self.response.out.write(template.render(path, {}))

class Links(webapp.RequestHandler):
    def get(self, bookmarklet):
      links = db.GqlQuery("SELECT * FROM Link WHERE bookmarklet = '" + bookmarklet + "' ORDER BY created_time DESC").fetch(100)
      
      for link in links:
        if len(link.title) > 80:
          link.title = link.title[0:80] + '...'
        if len(link.url) > 80:
          link.url = link.url[0:80] + '...'
      
      path = os.path.join(os.path.dirname(__file__), 'views/list.html')
      self.response.out.write(template.render(path, {'links': links}))      
      
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
      if not link.save_for_later:
        link.delete() 
      else:
        link.save_for_later = False
        link.save()
        
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

application = webapp.WSGIApplication(
                                     [('/', Root),
                                     (r'/(.*)/create', CreateLink),
                                     (r'/(.*)/(.*)/save', SaveLink),
                                     (r'/(.*)/(.*)', RedirectToLink),
                                     (r'/(.*)', Links)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()