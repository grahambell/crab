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

def utc_to_timezone(datetime_, zoneinfo):
    """Convert UTC datetime string as output by SQLite to an equivalent string
    in the specified timezone.

    Includes the zone code to indicate that the conversion has been
    performed."""

    if datetime_ is None:
        return None
    return datetime.datetime.strptime(datetime_, '%Y-%m-%d %H:%M:%S').replace(
        tzinfo=pytz.UTC).astimezone(zoneinfo).strftime('%Y-%m-%d %H:%M:%S %Z')

class CrabWebQuery:
    """CherryPy handler class for the JSON query part of the crab web
    interface."""

    def __init__(self, store, monitor):
        """Constructor: saves the given storage backend and reference
        to the monitor thread."""

        self.store = store
        self.monitor = monitor

    @cherrypy.expose
    def jobstatus(self, startid, warnid, finishid):
        """CherryPy handler returning the job status dict fetched
        from the monitor thread."""

        try:
            return json.dumps(self.monitor.wait_for_event_since(int(startid),
                                                   int(warnid), int(finishid)))
        except ValueError:
            raise HTTPError(404, 'Query parameter not an integer')


    @cherrypy.expose
    def jobinfo(self, id_):
        """CherryPy handler returning the job information for the given job."""
        try:
            info = self.store.get_job_info(int(id_))
        except ValueError:
            raise HTTPError(404, 'Job ID not a number')
        if info is None:
            raise HTTPError(404, 'Job not found')

        info["id"] = id_
        return json.dumps(info)

class CrabWeb:
    """CherryPy handler for the HTML part of the crab web interface."""

    def __init__(self, config, store, monitor):
        """Constructor for CrabWeb class.

        Stores a reference to the given storage backend, and extracts
        the home directory from the config dict.  Prepares the template
        engine and instantiates a CrabWebQuery object which CherryPy
        can find as 'query'."""
        self.store = store
        home = config['crab']['home']
        self.templ = TemplateLookup(directories=[home + '/templ'])
        self.query = CrabWebQuery(store, monitor)

    @cherrypy.expose
    def index(self):
        """Displays the main crab dashboard."""

        try:
            jobs = self.store.get_jobs()
            return self._write_template('joblist.html', {'jobs': jobs})

        except CrabError as err:
            raise HTTPError(message=str(err))

    @cherrypy.expose
    def job(self, id_, command=None, finishid=None):
        """Displays information about a current job.

        Currently also supports showing the job output.
        If command='output' but the finishid is not provided, then
        it will find the most recent output for the given job."""

        try:
            id_ = int(id_)
        except ValueError:
            raise HTTPError(404, 'Job number not a number')

        info = self.store.get_job_info(id_)
        if info is None:
            raise HTTPError(404, 'Job not found')

        if command is None:
            events = self.store.get_job_events(id_)

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
            return self._write_template('job.html',
                       {'id': id_, 'info': info, 'events':
                        [e for e in events if not CrabStatus.is_trivial(e['status'])]})

        elif command == 'output':
            if finishid is None:
                # If finishid is not specified, select the most recent
                # for this job.
                finishes = self.store.get_job_finishes(id_, limit=1)

                if len(finishes) == 0:
                    raise HTTPError(404, 'No job output found')

                finishid = finishes[0]['id']

            else:
                try:
                    finishid = int(finishid)
                except ValueError:
                    raise HTTPError(404, 'finish ID is not a number')


            # TODO: check that the given finishid is for the correct job.id.
            (stdout, stderr) = self.store.get_job_output(finishid,
                    info['host'], info['user'], id_)

            return self._write_template('joboutput.html',
                       {'id': id_, 'stdout': stdout, 'stderr': stderr})

        else:
            raise HTTPError(404)

    def _write_template(self, name, dict={}):
        """Returns the output from the named template when rendered
        with the given dict.

        Traps template errors and uses mako.exceptions to display them."""

        try:
            template = self.templ.get_template(name)
            return template.render(**dict)
        except:
            return exceptions.html_error_template().render()

