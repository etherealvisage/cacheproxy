#!/usr/bin/env python2
import SocketServer
import SimpleHTTPServer
import urllib
import urllib2
import urlparse
import os

PORT = 4000

class HeadRequest(urllib2.Request):
    def get_method(self):
        return "HEAD"

from BaseHTTPServer import BaseHTTPRequestHandler
from StringIO import StringIO

class HTTPRequestParser(BaseHTTPRequestHandler):
    def __init__(self, request_text):
        self.rfile = StringIO(request_text)
        self.raw_requestline = self.rfile.readline()
        self.error_code = self.error_message = None
        self.parse_request()

    def send_error(self, code, message):
        self.error_code = code
        self.error_message = message

# TODO: what if file doesn't download correctly?
class Proxy(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def __init__(self, a, b, c):
        SimpleHTTPServer.SimpleHTTPRequestHandler.__init__(self,a,b,c)
        #super(Proxy, self).__init(a,b,c)
        self.protocol_version = 'HTTP/1.1'

    basepath = ''
    def retrieve(self):
        try:
            req = urllib2.urlopen(self.path)
        except urllib2.HTTPError as e:
            #checksLogger.error('HTTPError = ' + str(e.code))
            self.send_response(e.code)
            self.send_header('x-cacheproxy-message', '404 from original server')
            self.end_headers()
            return

        print("Retrieving...")

        # Only cache 200's
        #if req.getcode() != 200:
            #self.send_response(req.getcode(), req.read())
            #return

        tag = req.headers["Last-Modified"]
        cached = open(os.path.join(self.basepath, "content"), "w")
        self.send_response(200)
        self.send_header('content-length', req.headers['content-length'])
        self.end_headers()
        while True:
            data = req.read(1024)
            cached.write(data)
            self.wfile.write(data)
            if len(data) != 1024:
                break
        cached.close()

        open(os.path.join(self.basepath, "tag"), "w").write(tag)

    def do_HEAD(self):
        print("HEAD " + str(self.path) + " invoked")
        try:
            headresponse = urllib2.urlopen(HeadRequest(self.path))
        except urllib2.HTTPError as e:
            self.send_response(e.code)
            self.end_headers()
            return
        self.send_response(200)
        for header in headresponse.headers:
            self.send_header(header, headresponse.headers[header])
        self.end_headers()

    def do_GET(self):
        print("GET " + str(self.path) + " invoked")
        parsed = urlparse.urlparse(self.path)
        self.basepath = '/'.join(['cache', parsed.netloc, parsed.path, ''])
        try:
            os.makedirs(self.basepath)
            # didn't exist! Time to create
            self.retrieve()
            return
        except:
            pass
        try:
            tag = open(os.path.join(self.basepath, "tag"), "r").readlines()[0]
            headresponse = urllib2.urlopen(HeadRequest(self.path))
            if headresponse.headers['Last-Modified'] == tag:
                print("\tProviding cached copy!")
                cached_r_name = os.path.join(self.basepath, "content")
                cached_r = open(cached_r_name, "r")
                self.send_response(200)
                self.send_header('content-length', os.path.getsize(cached_r_name))
                self.end_headers()
                self.copyfile(cached_r, self.wfile)
                return
        except:
            pass

        self.retrieve()

httpd = SocketServer.ForkingTCPServer(('', PORT), Proxy)
httpd.allow_reuse_address = True
print("serving at port", PORT)
httpd.serve_forever()
