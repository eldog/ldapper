#!/usr/bin/env python

import json
import optparse
import os
import Queue
import pickle
import urllib
import urllib2
import sys
import threading

from utils import abspath

import Tkinter as tk

def remove_values_from_list(the_list, val):
    return [value for value in the_list if value != val]

_LIB_DIR = '../lib/'
_LIB32_DIR = '../lib32/'
_LIB64_DIR = '../lib64/'
if sys.maxsize > 2**32:
    print 'using 64bit libs'
    _plat_lib_path = abspath(_LIB64_DIR)
    sys.path = remove_values_from_list(sys.path, abspath(_LIB32_DIR))    
else:
    print 'using 32bit libs'
    _plat_lib_path = abspath(_LIB32_DIR)
    sys.path = remove_values_from_list(sys.path, abspath(_LIB64_DIR))
if _plat_lib_path not in sys.path:
    sys.path.append(_plat_lib_path)
_lib_path = abspath(_LIB_DIR)
if _lib_path not in sys.path:
    sys.path.append(_lib_path)
del _LIB_DIR, _lib_path, _LIB32_DIR, _LIB64_DIR, _plat_lib_path

import ldap
from msr605 import MSR605

_HOST = 'localhost'
_PORT = '8888'
_API = ''
_QUERY = 'uman_mag_stripe'
_LDAP_HOST = 'edir.man.ac.uk'
_LDAP_PORT = '389'

MAG_STRIP_FILE = 'mag_strip_set.pickle'

class Ldapper(object):

    def __init__(self, host, port):
        self._host = host
        self._port = port
        
    def lookup(self, uman_mag_stripe):
        ldap_conn = ldap.initialize(
                'ldap://%s:%s' % (self._host, self._port))
        try:
            ldap_result = ldap_conn.search_s('', ldap.SCOPE_SUBTREE,
                '(umanMagStripe=%s)' % uman_mag_stripe)
        except ldap.SERVER_DOWN:
            print 'error: unable to connect to LDAP server'
            return None
        if ldap_result:
            ldap_result = ldap_result[0][1]
        else:
            ldap_result = None
        return ldap_result


class ThreadLdapper(threading.Thread):
    
    def __init__(self, ldapper, mag_stripe_queue, response_queue):
        threading.Thread.__init__(self)
        self.ldapper = ldapper
        self.mag_stripe_queue = mag_stripe_queue
        self.response_queue = response_queue

    def run(self):
        while True:
            mag_stripe = self.mag_stripe_queue.get()
            response = self.ldapper.lookup(mag_stripe)
            if response:
                self.response_queue.put(response)
                self.mag_stripe_queue.task_done()


class CardReader(object):

    def read_card(self):
        with MSR605() as msr605:
            print('Ready to swipe up')
            try:
                mag_stripe = msr605.read()[1].fields[0]
            except IOError:
                print 'Failed to read try again'
                return None
            print('mag stripe was %s' % mag_stripe)
            return mag_stripe


class ThreadCardReader(threading.Thread):
    
    def __init__(self, card_reader, mag_stripe_queue):
        threading.Thread.__init__(self)
        self.card_reader = card_reader
        self.mag_stripe_queue = mag_stripe_queue

    def run(self):
        while True:
            mag_stripe = self.card_reader.read_card()
            if mag_stripe:
                self.mag_stripe_queue.put(mag_stripe)


class ThreadResponse(threading.Thread):

    def __init__(self, callbacks, response_queue):
        threading.Thread.__init__(self)
        self.response_queue = response_queue
        self.callbacks = callbacks

    def run(self):
        while True:
            response = self.response_queue.get()
            for callback in self.callbacks:
                callback(response)
            self.response_queue.task_done()


class _SwipeFrame(tk.Frame, object):

    def __init__(self, *args, **kwargs):
        super(_SwipeFrame, self).__init__(*args, **kwargs)
        
        self.button = tk.Button(self, text='exit', command=self.quit)
        self.button.grid(row=1, column=0, padx=5, pady=5, stick=tk.E)

        self.response_frame = _ResponseFrame(master=self)
        self.response_frame.grid(row=0, column=0, padx=5, 
                                 pady=5, stick=tk.EW)


class _ResponseFrame(tk.Frame, object):

    def __init__(self, *args, **kwargs):
        super(_ResponseFrame, self).__init__(*args, **kwargs)

        self.name_label = tk.Label(self, text='Name:')
        self.name_label.grid(row=0, column=0, padx=5, pady=5, stick=tk.W)
        self.name = tk.StringVar()
        self.name_entry = tk.Entry(self, textvariable=self.name,
                                   width=50)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5, stick=tk.W)

        self.email_label = tk.Label(self, text='Email:')
        self.email_label.grid(row=1, column=0, padx=5, pady=5, stick=tk.W)
        self.email = tk.StringVar()
        self.email_entry = tk.Entry(self, textvariable=self.email, 
                                    width=50)
        self.email_entry.grid(row=1, column=1, padx=5, pady=5, stick=tk.W)

        self.student_id_label = tk.Label(self, text='Student ID:')
        self.student_id_label.grid(row=2, column=0, padx=5, pady=5,
                                   stick=tk.W)
        self.student_id = tk.StringVar()
        self.student_id_entry = tk.Entry(self,
                                         textvariable=self.student_id,
                                         width=50)
        self.student_id_entry.grid(row=2, column=1, padx=5, pady=5,
                                   stick=tk.W)
        
    def json_update(self, json_response):
        print json.dumps(json_response)
        self.name.set(json_response['cn'][0])
        self.email.set(json_response['mail'][0])
        self.student_id.set(json_response['umanPersonID'][0])


class SwipeUpGUI(tk.Tk, object):
    
    def __init__(self, *args, **kwargs):
        super(SwipeUpGUI, self).__init__(*args, **kwargs)
        self.title('Swipe Up')
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        self.frame = _SwipeFrame(master=self)
        self.frame.grid(row=1, column=0, padx=5, pady=5)

def send_to_server(json_response):
    given_name = json_response['givenName'][0]
    surname = json_response['sn'][0]
    email = json_response['mail'][0]
    student_id = json_response['umanPersonID'][0]

    params = urllib.urlencode({'given_name' : given_name,
                               'surname' : surname,
                               'email' : email,
                               'student_id' : student_id})
    response = urllib2.urlopen('http://%s:%s/' % (_HOST, _PORT),
                               data=params)
    print response.read()
            
def main():
    parser = optparse.OptionParser(usage='%prog [-l] [-p]',
                                   version='%prog ver. 0.1 alpha 2011')
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

    mag_stripe_queue = Queue.Queue()
    response_queue = Queue.Queue()

    ldapper = Ldapper(options.host, options.port)
    ldapper_thread = ThreadLdapper(ldapper, mag_stripe_queue, 
                                   response_queue)
    ldapper_thread.setDaemon(True)
    ldapper_thread.start()

    card_thread = ThreadCardReader(CardReader(), mag_stripe_queue)
    card_thread.setDaemon(True)
    card_thread.start()

    swipe_gui = SwipeUpGUI()
    
    response_thread = ThreadResponse(
                        [
                            swipe_gui.frame.response_frame.json_update,
                            send_to_server
                        ],
                        response_queue)
    response_thread.setDaemon(True)
    response_thread.start()
    
    swipe_gui.mainloop()

if __name__ == '__main__':
    main()

