import json
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

class CrabWebResources:
    _cp_config = {'tools.staticdir.on': True,
                  'tools.staticdir.dir': os.getcwd() + '/res'}

class CrabWebQuery:
    def __init__(self, store, monitor):
        self.store = store
        self.monitor = monitor

    @cherrypy.expose
    def jobstatus(self):
        return json.dumps(self.monitor.get_job_status())

    @cherrypy.expose
    def jobinfo(self, jobid):
        try:
            info = self.store.get_job_info(int(jobid))
        except ValueError:
            raise HTTPError(404, 'Job ID not a number')
        if info is None:
            raise HTTPError(404, 'Job not found')

        info["id"] = jobid
        return json.dumps(info)

class CrabWeb:
    def __init__(self, store, monitor):
        self.store = store
        self.templ = TemplateLookup(directories=['templ'])
        self.query = CrabWebQuery(store, monitor)

    class SomeClassOrOther:
        pass

    res = CrabWebResources()

    @cherrypy.expose
    def index(self):
        try:
            jobs = self.store.get_jobs()
            return self.write_template('index.html', {'jobs': jobs})

        except CrabError as err:
            raise HTTPError(message=str(err))

    @cherrypy.expose
    def job(self, jobid, command=None, finishid=None):
        if not re.match('^\d+$', jobid):
            raise HTTPError(404, 'Not a number')

        if command is None:
            info = self.store.get_job_info(jobid)
            if info is None:
                raise HTTPError(404, 'Job not found')

            events = self.store.get_job_events(jobid)
            return self.write_template('job.html',
                       {'jobid': jobid, 'info': info, 'events': events})

        elif command == 'output':
            if finishid is None:
                finishes = self.store.get_job_finishes(jobid, limit=1)

                if len(finishes) == 0:
                    raise HTTPError(404, 'No job output found')

                finishid = finishes[0]['id']

            elif not re.match('^\d+$', finishid):
                raise HTTPError(404, 'Not a number')

            # TODO: check that the given finishid is for the correct jobid.
            (stdout, stderr) = self.store.get_job_output(finishid)
            return self.write_template('joboutput.html',
                       {'jobid': jobid, 'stdout': stdout, 'stderr': stderr})

        else:
            raise HTTPError(404)

    def write_template(self, name, dict={}):
        try:
            template = self.templ.get_template(name)
            return template.render(**dict)
        except:
            return exceptions.html_error_template().render()

