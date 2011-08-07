import cgi
import urllib2

from django.utils import simplejson as json

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

_HOST = 'localhost'
_PORT = '8080'
_API = 'lookup/'
_QUERY = 'uman_mag_stripe'

class Member(db.Model):
    given_name = db.StringProperty()
    surname = db.StringProperty()
    email = db.EmailProperty()

def fetch_ldap_details(mag_strip):
    response = urllib2.urlopen('http://%s:%s/%s?%s=%s' % 
        (_HOST, _PORT, _API, _QUERY, mag_strip))
    return json.loads(response.read())

class SwipeReg(webapp.RequestHandler):
    def get(self):
        mag_stripe = self.request.get('uman_mag_stripe')
        if mag_stripe:
            details = fetch_ldap_details(mag_stripe)
            member = Member(given_name=details["givenName"][0],
                            surname=details["sn"][0],
                            email=details["mail"][0],
                            key_name=details["umanPersonID"][0])
            member.put()
        members = Member.all()
        for m in members:
            self.response.out.write('<b>%s</b><br/>' % str(m.given_name))

application = webapp.WSGIApplication([('/', SwipeReg)], debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()

