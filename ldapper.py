#!/usr/bin/env python
import json
import optparse
import os
import subprocess
import sys

def abspath(path):
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), _LIB_DIR))

def remove_values_from_list(the_list, val):
    return [value for value in the_list if value != val]

_LIB_DIR = 'lib/'
_LIB32_DIR = 'lib32/'
_LIB64_DIR = 'lib64/'
if sys.maxsize > 2 *32:
    _plat_lib_path = abspath(_LIB64_DIR)
    sys.path = remove_values_from_list(sys.path, abspath(_LIB32_DIR))    
else:
    _plat_lib_path = abspath(_LIB32_DIR)
    sys.path = remove_values_from_list(sys.path, abspath(_LIB64_DIR))
if _plat_lib_path not in sys.path:
    sys.path.append(_plat_lib_path)
_lib_path = abspath(_LIB_DIR)
if _lib_path not in sys.path:
    sys.path.append(_lib_path)
del _LIB_DIR, _lib_path, _LIB32_DIR, _LIB64_DIR, _plat_lib_path

import cherrypy
import ldap

_LDAP_HOST = 'edir.man.ac.uk'
_LDAP_PORT = '389'

class Ldapper(object):
    def __init__(self, host, port):
        self._host = host
        self._port = port
        
    @cherrypy.expose
    def lookup(self, uman_id=None):
        if not uman_id:
            raise cherrypy.HTTPError(400, 'No uman id given')
        cherrypy.response.headers['Content-Type'] = 'application/json'
        ldap_conn = ldap.initialize(
            'ldap://%s:%s' % (self._host, self._port))
        try:
            ldap_result = ldap_conn.search_s(
                '', ldap.SCOPE_SUBTREE, '(umanPersonID=%s)' % uman_id)
        except ldap.SERVER_DOWN:
            raise cherrypy.HTTPError(500, 'Unable to contact LDAP server')
        if ldap_result:
            ldap_result = ldap_result[0][1]
        else:
            ldap_result = None
        return json.dumps(ldap_result)

def main():
    parser = optparse.OptionParser(usage='%prog [-l] [-p]',
                                   version='%prog ver. 0.1 2011')
    parser.add_option('-l', '--ldap-host', dest='host',
                      help='the address of the ldap host')
    parser.add_option('-p', '--port', dest='port',
                      help='the port to contact the ldap host on')
    (options, args) = parser.parse_args()
    if not options.host:
        options.host = _LDAP_HOST
    if not options.port:
        options.port = _LDAP_PORT 
    print 'Ldapper will connect to %s:%s' % (options.host, options.port)
    cherrypy.quickstart(Ldapper(options.host, options.port)) 

if __name__ == '__main__':
    main()
   
