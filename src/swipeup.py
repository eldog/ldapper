#!/usr/bin/env python

import urllib2
import sys

from utils import abspath

_LIB_DIR = "../lib/"
_lib_path = abspath(_LIB_DIR)

if _lib_path not in sys.path:
    sys.path.append(_lib_path)

from msr605 import MSR605

del _LIB_DIR, _lib_path
_HOST = 'localhost'
_PORT = '8080'
_API = 'lookup/'
_QUERY = 'uman_mag_stripe'
def main():
    with MSR605() as msr605:
        while True:
            print('Ready to swipe up')
            mag_strip = msr605.read()[1].fields[0]
            print('mag stripe was %s' % mag_strip)
            response = urllib2.urlopen('http://%s:%s/%s?%s=%s' % 
                                       (_HOST,
                                        _PORT,
                                        _API,
                                        _QUERY,
                                        mag_strip))
            print response.read()

if __name__ == '__main__':
    main()

