from google.appengine.ext import db

class Share(db.Model):
  phrase = db.StringProperty()
  bookmarklet = db.StringProperty()

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