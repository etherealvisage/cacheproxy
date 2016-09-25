#!/usr/bin/env python2
import SocketServer
import SimpleHTTPServer
import urllib
import urllib2
import urlparse
import os

PORT = 1235

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
    basepath = ''
    def retrieve(self):
        try:
            req = urllib2.urlopen(self.path)
        except urllib2.HTTPError as e:
            #checksLogger.error('HTTPError = ' + str(e.code))
            self.send_response(e.code)
            return

        print("Retrieving...")

        # Only cache 200's
        #if req.getcode() != 200:
            #self.send_response(req.getcode(), req.read())
            #return

        tag = req.headers["Last-Modified"]
        cached = open(os.path.join(self.basepath, "content"), "w")
        while True:
            data = req.read(1024)
            cached.write(data)
            self.wfile.write(data)
            if len(data) != 1024:
                break
        cached.close()

        open(os.path.join(self.basepath, "tag"), "w").write(tag)

        #cached_r = open(os.path.join(self.basepath, "content"), "r")
        #self.copyfile(cached_r, self.wfile)

    def do_GET(self):
        parsed = urlparse.urlparse(self.path)
        print(parsed.netloc)
        print(parsed.path)
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
                cached_r = open(os.path.join(self.basepath, "content"), "r")
                self.copyfile(cached_r, self.wfile)
                return
        except:
            pass

        self.retrieve()

httpd = SocketServer.ForkingTCPServer(('', PORT), Proxy)
print("serving at port", PORT)
httpd.serve_forever()
