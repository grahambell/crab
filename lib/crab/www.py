import os
import mimetypes
import urllib

from BaseHTTPServer import BaseHTTPRequestHandler
from mako import exceptions
from mako.template import Template
from mako.lookup import TemplateLookup

class CrabWWW(BaseHTTPRequestHandler):
    @staticmethod
    def initialize():
        CrabWWW.templ = TemplateLookup(directories = ['templ'])

        # Pre-load resource files

        CrabWWW.res = {}
        CrabWWW.restype = {}

        for file in os.listdir("res"):
            if not (os.path.isdir(file) or file.startswith(".")):
              f = None
              try:
                  f = open("res/" + file)
                  CrabWWW.res[file] = f.read()

                  (type, enc) = mimetypes.guess_type(file)
                  CrabWWW.restype[file] = type
              except:
                  pass
              finally:
                  if f != None:
                      f.close()

    def do_GET(self):
        path = urllib.unquote(self.path).split("/")

        # Need to check that these file path components exist!
        if path[1] == "res":
            file = path[2]

            if file in self.res:
                self.send_response(200)
                self.send_header("Content-type", self.restype[file])
                self.end_headers()
                self.wfile.write(self.res[file])
            else:
                self.send_error(404, "resource not found")
        else:
            self.write_template('index.html')

    def write_template(self, name, dict = {}):
        try:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            template = self.templ.get_template(name)
            self.wfile.write(template.render(**dict))
        except:
            self.wfile.write(exceptions.html_error_template().render())
