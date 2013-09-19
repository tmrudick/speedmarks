import os
import webapp2
import words

# Database
from models import *
from google.appengine.ext import db
from google.appengine.ext.db import BadKeyError

# Templating
import jinja2

JINJA_ENVIRONMENT = jinja2.Environment(
  loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
  extensions=['jinja2.ext.autoescape'])

class Root(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('views/index.html')
        self.response.write(template.render({}))

class Links(webapp2.RequestHandler):
    def get(self, bookmarklet):
      links = db.GqlQuery("SELECT * FROM Link WHERE bookmarklet = :1 ORDER BY created_time DESC", bookmarklet).fetch(100)

      for link in links:
        if len(link.title) > 80:
          link.title = link.title[0:80] + '...'
        if len(link.url) > 80:
          link.url = link.url[0:80] + '...'

      template = JINJA_ENVIRONMENT.get_template('views/list.html')
      self.response.write(template.render({'links': links, 'bookmarklet': bookmarklet}))

class CreateLink(webapp2.RequestHandler):
    def get(self, bookmarklet):
      if self.request.get('url') == "":
        template = JINJA_ENVIRONMENT.get_template('views/error.html')
        self.response.write(template.render({}))
        return

      link = Link()
      link.url = self.request.get('url')
      link.title = self.request.get('title')
      link.bookmarklet = bookmarklet

      link.put()

      self.redirect(str(link.url))

class DeleteLink(webapp2.RequestHandler):
  def get(self, bookmarklet, link_key):
    try:
      link = db.get(link_key)
    except BadKeyError:
      template = JINJA_ENVIRONMENT.get_template('views/error.html')
      self.response.write(template.render({}))
      return

    if link.bookmarklet == bookmarklet:
      link.delete()

    self.redirect(str('/%s' % bookmarklet))

class RedirectToLink(webapp2.RequestHandler):
  def get(self, bookmarklet, link_key):
    try:
      link = db.get(link_key)
    except BadKeyError:
      template = JINJA_ENVIRONMENT.get_template('views/error.html')
      self.response.write(template.render({}))
      return

    if link == None:
      template = JINJA_ENVIRONMENT.get_template('views/error.html')
      self.response.write(template.render({}))
    else:
      if not link.save_for_later:
        link.delete()

      self.redirect(str(link.url))

class SaveLink(webapp2.RequestHandler):
  def get(self, bookmarklet, link_key):
    try:
      link = db.get(link_key)
    except BadKeyError:
      template = JINJA_ENVIRONMENT.get_template('views/error.html')
      self.response.write(template.render({}))
      return

    link.save_for_later = not link.save_for_later
    link.save()

    self.redirect(str('/%s' % bookmarklet))

class ShareNewLink(webapp2.RequestHandler):
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

    self.redirect(str('/%s' % bookmarklet))

class ShareExistingLink(webapp2.RequestHandler):
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

    self.redirect(str('/%s' % bookmarklet))

class Options(webapp2.RequestHandler):
  def get(self, bookmarklet):
    share = db.GqlQuery("SELECT * FROM Share WHERE bookmarklet = :1", bookmarklet).get()

    share_phrase = ""

    if share:
      share_phrase = share.phrase

    self.response.write(share_phrase)

  def post(self, bookmarklet):
    allow_sharing = self.request.get('allow')

    share = db.GqlQuery("SELECT * FROM Share WHERE bookmarklet = :1", bookmarklet).get()

    if allow_sharing == 'true':
      phrase = words.generatePhrase(2)
      dbPhrase = db.GqlQuery("SELECT * FROM Share WHERE phrase = :1", phrase).get()

      while dbPhrase:
        phrase = words.generatePhrase(2)
        dbPhrase = db.GqlQuery("SELECT * FROM Share WHERE phrase = :1", phrase).get()

      if not share:
        share = Share()
        share.bookmarklet = bookmarklet

      share.phrase = phrase
      share.save()

      self.response.write(phrase)
    else:
      if share:
        share.delete()
      self.response.write("")

class Help(webapp2.RequestHandler):
  def get(self):
    template = JINJA_ENVIRONMENT.get_template('views/help.html')
    self.response.write(template.render({}))

app = webapp2.WSGIApplication(
                                     [('/', Root),
                                     (r'/help', Help),
                                     (r'/(.*)/create', CreateLink),
                                     (r'/(.*)/delete/(.*)', DeleteLink),
                                     (r'/(.*)/options', Options),
                                     (r'/(.*)/save/(.*)', SaveLink),
                                     (r'/(.*)/share', ShareNewLink),
                                     (r'/(.*)/share/(.*)', ShareExistingLink),
                                     (r'/(.*)/(.*)', RedirectToLink),
                                     (r'/(.*)', Links)],
                                     debug=True)
