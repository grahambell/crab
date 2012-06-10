import mimetypes
import os
import re
import urllib

import cherrypy
from cherrypy import HTTPError
from mako import exceptions
from mako.lookup import TemplateLookup
from mako.template import Template

from crab import CrabError

class CrabWeb:
    def __init__(self, store):
        self.store = store
        self.templ = TemplateLookup(directories = ['templ'])

    class SomeClassOrOther:
        pass

    res = SomeClassOrOther()
    res._cp_config ={"tools.staticdir.on": True,
                     "tools.staticdir.dir": os.getcwd() + "/res"}

    @cherrypy.expose
    def index(self):
        try:
            jobs = self.store.get_jobs()
            return self.write_template('index.html', {"jobs": jobs})

        except CrabError as err:
            raise HTTPError(message=str(err))

    @cherrypy.expose
    def job(self, jobid, command=None, finishid=None):
        if not re.match("^\d+$", jobid):
                raise HTTPError(404, "Not a number")

        if command is None:
            info = self.store.get_job_info(jobid)
            if len(info) != 1:
                raise HTTPError(404, "Job not found")

            actions = self.store.get_starts_finishes(jobid)
            return self.write_template('job.html',
                    {"jobid": jobid, "info": info[0], "actions": actions})

        elif command == "output":
            if finishid is None:
                finishes = self.store.get_job_finishes(jobid)

                if len(finishes) == 0:
                    raise HTTPError(404, "No job output found")

                finishid = finishes[0]["id"]

            elif not re.match("^\d+$", finishid):
                raise HTTPError(404, "Not a number")

            # TODO: check that the given finishid is for the correct jobid.
            (stdout, stderr) = self.store.get_job_output(finishid)
            return self.write_template('joboutput.html', {"jobid": jobid,
                            "stdout": stdout, "stderr": stderr})

        else:
            raise HTTPError(404)

    def write_template(self, name, dict = {}):
        try:
            template = self.templ.get_template(name)
            return template.render(**dict)
        except:
            return exceptions.html_error_template().render()
