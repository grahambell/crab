import os
import mimetypes
import urllib
import re

from BaseHTTPServer import BaseHTTPRequestHandler
from mako import exceptions
from mako.template import Template
from mako.lookup import TemplateLookup

from crab import CrabError

class CrabWeb(BaseHTTPRequestHandler):
    @staticmethod
    def initialize():
        CrabWeb.templ = TemplateLookup(directories = ['templ'])

        # Pre-load resource files

        CrabWeb.res = {}
        CrabWeb.restype = {}

        for file in os.listdir("res"):
            if not (os.path.isdir(file) or file.startswith(".")):
              f = None
              try:
                  f = open("res/" + file)
                  CrabWeb.res[file] = f.read()

                  (type, enc) = mimetypes.guess_type(file)
                  CrabWeb.restype[file] = type

              except:
                  pass

              finally:
                  if f != None:
                      f.close()

    def do_GET(self):
        path = urllib.unquote(self.path).split("/")[1:]
        number = re.compile("^\d+$")

        # Display home dashboard page

        if len(path) == 0 or path[0] == "":
            try:
                jobs = self.store.get_jobs()
                self.write_template('index.html', {"jobs": jobs})

            except CrabError as err:
                self.send_error(500, str(err))


        # Display job info

        elif path[0] == "job" and len(path) > 1 and number.search(path[1]):
            jobid = path[1]

            try:
                if len(path) == 2:
                    info = self.store.get_job_info(jobid)
                    if len(info) != 1:
                        raise CrabError("could not find job")

                    actions = self.store.get_starts_finishes(jobid)
                    self.write_template('job.html',
                        {"jobid": jobid, "info": info[0], "actions": actions})

                elif path[2] == "output":
                    if len(path) > 3 and number.search(path[3]):
                        finishid = path[3]

                    else:
                        finishes = self.store.get_job_finishes(jobid)

                        if len(finishes) == 0:
                            raise CrabError("no job output records found")

                        finishid = finishes[0]["id"]


                    (stdout, stderr) = self.store.get_job_output(finishid)
                    self.write_template('joboutput.html', {"jobid": jobid,
                            "stdout": stdout, "stderr": stderr})

                else:
                    self.send_error(404, "unknown request")

            except CrabError as err:
                self.send_error(500, str(err))


        # Provide a resource file

        elif path[0] == "res":
            file = path[1]

            if file in self.res:
                self.send_response(200)
                self.send_header("Content-type", self.restype[file])
                self.end_headers()
                self.wfile.write(self.res[file])

            else:
                self.send_error(404, "resource not found")


        # Otherwise 404 error

        else:
            self.send_error(404, "unknown request")

    def write_template(self, name, dict = {}):
        try:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            template = self.templ.get_template(name)
            self.wfile.write(template.render(**dict))
        except:
            self.wfile.write(exceptions.html_error_template().render())
