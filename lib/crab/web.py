import datetime
import json
import mimetypes
import os
import pytz
import re
import time
import urllib

import cherrypy
from cherrypy import HTTPError
from mako import exceptions
from mako.lookup import TemplateLookup
from mako.template import Template

from crab import CrabError, CrabStatus

# Convert UTC datetime string as output by SQLite to an equivalent string
# in the specified timezone, including the zone code to indicate that
# the conversion has been performed.
def utc_to_timezone(datetime_, zoneinfo):
    if datetime_ is None:
        return None
    return datetime.datetime.strptime(datetime_, '%Y-%m-%d %H:%M:%S').replace(
        tzinfo=pytz.UTC).astimezone(zoneinfo).strftime('%Y-%m-%d %H:%M:%S %Z')

class CrabWebQuery:
    def __init__(self, store, monitor):
        self.store = store
        self.monitor = monitor

    @cherrypy.expose
    def jobstatus(self, startid, warnid, finishid):
        try:
            return json.dumps(self.monitor.wait_for_event_since(int(startid),
                                                   int(warnid), int(finishid)))
        except ValueError:
            raise HTTPError(404, 'Query parameter not an integer')


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
    def __init__(self, config, store, monitor):
        self.store = store
        home = config['crab']['home']
        self.templ = TemplateLookup(directories=[home + '/templ'])
        self.query = CrabWebQuery(store, monitor)

    class SomeClassOrOther:
        pass

    @cherrypy.expose
    def index(self):
        try:
            jobs = self.store.get_jobs()
            return self.write_template('joblist.html', {'jobs': jobs})

        except CrabError as err:
            raise HTTPError(message=str(err))

    @cherrypy.expose
    def job(self, jobid, command=None, finishid=None):
        try:
            jobid = int(jobid)
        except ValueError:
            raise HTTPError(404, 'Job number not a number')

        info = self.store.get_job_info(jobid)
        if info is None:
            raise HTTPError(404, 'Job not found')

        if command is None:
            events = self.store.get_job_events(jobid)

            # Try to convert the times to the timezone shown on the page.
            if info['timezone'] is not None:
                try:
                    tz = pytz.timezone(info['timezone'])
                    info['installed'] = utc_to_timezone(info['installed'], tz)
                    info['deleted'] = utc_to_timezone(info['deleted'], tz)
                    for event in events:
                        event['datetime'] = utc_to_timezone(event['datetime'],
                                                            tz)
                except pytz.UnknownTimeZoneError:
                    pass

            # Filter out LATE events as they are not important, and if
            # shown in green, might make a failing cron job look better
            # than it is because each job will be marked LATE before MISSED.
            return self.write_template('job.html',
                       {'jobid': jobid, 'info': info, 'events':
                        [e for e in events if not CrabStatus.is_trivial(e['status'])]})

        elif command == 'output':
            if finishid is None:
                # If finishid is not specified, select the most recent
                # for this job.
                finishes = self.store.get_job_finishes(jobid, limit=1)

                if len(finishes) == 0:
                    raise HTTPError(404, 'No job output found')

                finishid = finishes[0]['id']

            else:
                try:
                    finishid = int(finishid)
                except ValueError:
                    raise HTTPError(404, 'finish ID is not a number')


            # TODO: check that the given finishid is for the correct jobid.
            (stdout, stderr) = self.store.get_job_output(finishid,
                    info['host'], info['user'], jobid)

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

