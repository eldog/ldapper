import cgi
import datetime
import urllib2

from django.utils import simplejson as json

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

_HOST = 'localhost'
_PORT = '8080'
_API = 'lookup/'
_QUERY = 'uman_mag_stripe'

class DictableModel(db.Model):
    def dump(self):
        values = {}
        for name, prop in self.properties().iteritems():
            value = prop.__get__(self, self.__class__)
            if isinstance(value, datetime.datetime):
                value = str(value)
            values[name] = value
        return values


class JsonableModel(DictableModel):
    def dump(self):
        return json.dumps(super(JsonableModel, self).dump())


class Member(JsonableModel):
    given_name = db.StringProperty()
    surname = db.StringProperty()
    email = db.EmailProperty()
    student_id = db.StringProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now=True)


def fetch_ldap_details(mag_strip):
    response = urllib2.urlopen('http://%s:%s/%s?%s=%s' % 
        (_HOST, _PORT, _API, _QUERY, mag_strip))
    return json.loads(response.read())

class SwipeReg(webapp.RequestHandler):
    def post(self):
        mag_stripe = self.request.get('uman_mag_stripe')
        if mag_stripe:
            details = fetch_ldap_details(mag_stripe)
            member = Member(given_name=details["givenName"][0],
                            surname=details["sn"][0],
                            email=details["mail"][0],
                            student_id=details["umanPersonID"][0],
                            key_name=details["umanPersonID"][0])
            member.put()
            self.response.out.write(member.dump())

    def get(self):
        members = Member.all()
        for m in members:
            self.response.out.write('<b>%s</b><br/>' % str(m.given_name))


application = webapp.WSGIApplication([('/', SwipeReg)], debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()

