#!/usr/bin/env python

import json
import pickle
import urllib
import urllib2
import sys
import threading

from utils import abspath

_LIB_DIR = "../lib/"
_lib_path = abspath(_LIB_DIR)

if _lib_path not in sys.path:
    sys.path.append(_lib_path)

from msr605 import MSR605

del _LIB_DIR, _lib_path
_HOST = 'localhost'
_PORT = '8888'
_API = ''
_QUERY = 'uman_mag_stripe'

MAG_STRIP_FILE = 'mag_strip_set.pickle'

def fetch_ldap_details(mag_strip):
    try:
        response = urllib2.urlopen('http://%s:%s/' % 
            (_HOST, _PORT), data=urllib.urlencode({ _QUERY : mag_strip }))
    except urllib2.HTTPError, e:
        print e
        return False
    print response.read()
    return True

def main():
    try:
        with open(MAG_STRIP_FILE) as f:
            mag_strip_set = pickle.load(f)
            print 'Loaded set %s' % mag_strip_set
    except (IOError, EOFError):
        mag_strip_set = set()
    try:
        with MSR605() as msr605:
            while True:
                print('Ready to swipe up')
                try:
                    mag_strip = msr605.read()[1].fields[0]
                except IOError:
                    print 'Failed to read try again'
                    continue
                print('mag stripe was %s' % mag_strip)
                mag_strip_set.add(mag_strip)
                if fetch_ldap_details(mag_strip):
                    mag_strip_set.remove(mag_strip)
    except KeyboardInterrupt:
        pass
    with open(MAG_STRIP_FILE, 'w') as f:
        pickle.dump(mag_strip_set, f)
        print 'pickled set %s' % mag_strip_set

if __name__ == '__main__':
    main()

