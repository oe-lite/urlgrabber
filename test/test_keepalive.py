#!/usr/bin/python -t
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

# Copyright 2002-2004 Michael D. Stenner, Ryan D. Tomayko

"""keepalive.py tests"""

import sys
import os
import time
import urllib2

from urllib2 import URLError

from base_test_code import *

from urlgrabber import keepalive

class CorruptionTests(TestCase):
    def setUp(self):
        self.kh = keepalive.HTTPHandler()
        self.opener = urllib2.build_opener(self.kh)
        self.ref = ref_http
        self.fo = self.opener.open(self.ref)
        
    def tearDown(self):
        self.fo.close()
        self.kh.close_all()
        
    def test_readall(self):
        "download a file with a single call to read()"
        data = self.fo.read()
        self.assert_(data == reference_data)

    def test_readline(self):
        "download a file with multiple calls to readline()"
        data = ''
        while 1:
            s = self.fo.readline()
            if s: data = data + s
            else: break
        self.assert_(data == reference_data)

    def test_readlines(self):
        "download a file with a single call to readlines()"
        lines = self.fo.readlines()
        data = ''.join(lines)
        self.assert_(data == reference_data)

    def test_smallread(self):
        "download a file with multiple calls to read(23)"
        data = ''
        while 1:
            s = self.fo.read(23)
            if s: data = data + s
            else: break
        self.assert_(data == reference_data)

    def test_mixed_read(self):
        "download a file with mixed readline() and read(23) calls"
        data = ''
        while 1:
            s = self.fo.read(23)
            if s: data = data + s
            else: break
            s = self.fo.readline()
            if s: data = data + s
            else: break
        self.assert_(data == reference_data)

class HTTPErrorTests(TestCase):
    def setUp(self):
        self.kh = keepalive.HTTPHandler()
        self.opener = urllib2.build_opener(self.kh)
        
    def tearDown(self):
        self.kh.close_all()
        keepalive.HANDLE_ERRORS = 1

    def test_200_handler_on(self):
        "test that 200 works with fancy handler"
        keepalive.HANDLE_ERRORS = 1
        fo = self.opener.open(ref_http)
        data = fo.read()
        fo.close()
        self.assertEqual((fo.status, fo.reason), (200, 'OK'))

    def test_200_handler_off(self):
        "test that 200 works without fancy handler"
        keepalive.HANDLE_ERRORS = 0
        fo = self.opener.open(ref_http)
        data = fo.read()
        fo.close()
        self.assertEqual((fo.status, fo.reason), (200, 'OK'))

    def test_404_handler_on(self):
        "test that 404 works with fancy handler"
        keepalive.HANDLE_ERRORS = 1
        self.assertRaises(URLError, self.opener.open, ref_404)

    def test_404_handler_off(self):
        "test that 404 works without fancy handler"
        keepalive.HANDLE_ERRORS = 0
        fo = self.opener.open(ref_404)
        data = fo.read()
        fo.close()
        self.assertEqual((fo.status, fo.reason), (404, 'Not Found'))

    def test_403_handler_on(self):
        "test that 403 works with fancy handler"
        keepalive.HANDLE_ERRORS = 1
        self.assertRaises(URLError, self.opener.open, ref_403)

    def test_403_handler_off(self):
        "test that 403 works without fancy handler"
        keepalive.HANDLE_ERRORS = 0
        fo = self.opener.open(ref_403)
        data = fo.read()
        fo.close()
        self.assertEqual((fo.status, fo.reason), (403, 'Forbidden'))

class DroppedConnectionTests(TestCase):
    def setUp(self):
        self.kh = keepalive.HTTPHandler()
        self.opener = urllib2.build_opener(self.kh)
        self.snarfed_logs = []
        self.dbp = keepalive.DBPRINT
        keepalive.DBPRINT = self.logsnarf
        keepalive.DEBUG = 1
        
    def tearDown(self):
        self.kh.close_all()
        keepalive.DBPRINT = self.dbp
        keepalive.DEBUG = 0
        
    def logsnarf(self, message):
        self.snarfed_logs.append(message)
        
    def test_dropped_connection(self):
        "testing connection restarting (60-second delay, ctrl-c to skip)"
        fo = self.opener.open(ref_http)
        data1 = fo.read()
        fo.close()

        try: time.sleep(60)
        except KeyboardInterrupt: self.skip()
        
        fo = self.opener.open(ref_http)
        data2 = fo.read()
        fo.close()
        
        reference_logs = [
            'creating new connection to www.linux.duke.edu',
            'STATUS: 200, OK',
            'failed to re-use connection to www.linux.duke.edu',
            'creating new connection to www.linux.duke.edu',
            'STATUS: 200, OK'
            ]
        self.assert_(data1 == data2)
        self.assert_(self.snarfed_logs == reference_logs)
        
def suite():
    tl = TestLoader()
    return tl.loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    runner = TextTestRunner(stream=sys.stdout,descriptions=1,verbosity=2)
    runner.run(suite())
     