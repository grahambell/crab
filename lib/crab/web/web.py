# Copyright (C) 2012 Science and Technology Facilities Council.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import json
import mimetypes
import os
import re
import time

import cherrypy
from cherrypy import HTTPError, HTTPRedirect
from mako import exceptions
from mako.lookup import TemplateLookup
from mako.template import Template

from crab import CrabError, CrabStatus
from crab.util.filter import CrabEventFilter

class CrabWebQuery:
    """CherryPy handler class for the JSON query part of the crab web
    interface."""

    def __init__(self, store, monitor, service):
        """Constructor: saves the given storage backend and reference
        to the monitor thread."""

        self.store = store
        self.monitor = monitor
        self.service = service

    @cherrypy.expose
    def jobstatus(self, startid, warnid, finishid):
        """CherryPy handler returning the job status dict fetched
        from the monitor thread."""

        try:
            s = self.monitor.wait_for_event_since(int(startid),
                                                  int(warnid), int(finishid))
            s['service'] = dict((s, self.service[s].is_alive())
                                for s in self.service)
            return json.dumps(s)
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

    def __init__(self, config, store, monitor, service):
        """Constructor for CrabWeb class.

        Stores a reference to the given storage backend, and extracts
        the home directory from the config dict.  Prepares the template
        engine and instantiates a CrabWebQuery object which CherryPy
        can find as 'query'."""
        self.store = store
        home = config['crab']['home']
        self.templ = TemplateLookup(directories=[home + '/templ'])
        self.query = CrabWebQuery(store, monitor, service)

    @cherrypy.expose
    def index(self):
        """Displays the main crab dashboard."""

        try:
            jobs = self.store.get_jobs()
            return self._write_template('joblist.html', {'jobs': jobs})

        except CrabError as err:
            raise HTTPError(message=str(err))

    @cherrypy.expose
    def job(self, id_, command=None,
            submit_config=None, submit_relink=None,
            finishid=None, orphan=None, graceperiod=None, timeout=None):
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
            filter = CrabEventFilter(self.store, info['timezone'],
                                     squash_start=True)

            # Try to convert the times to the timezone shown on the page.
            info['installed'] = filter.in_timezone(info['installed'])
            info['deleted'] = filter.in_timezone(info['deleted'])

            # Filter the events.
            events = filter(events)

            # Fetch configuration.
            config = self.store.get_job_config(id_)

            return self._write_template('job.html',
                       {'id': id_, 'info': info, 'config': config,
                        'events': events})

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
            pair = self.store.get_job_output(finishid,
                    info['host'], info['user'], id_)

            if pair is None:
                raise HTTPError(404, 'No output found for the given job run.')

            (stdout, stderr) = pair
            return self._write_template('joboutput.html',
                       {'id': id_, 'info': info,
                        'stdout': stdout, 'stderr': stderr})

        elif command == 'config':
            if submit_relink:
                try:
                    orphan = int(orphan)
                except ValueError:
                    raise HTTPError(400, 'Orphan number not a number')

                self.store.relink_job_config(orphan, id_)
                raise HTTPRedirect("/job/" + str(id_))

            elif submit_config:
                try:
                    if timeout == '':
                        timeout = None
                    elif timeout is not None:
                        timeout = int(timeout)
                    if graceperiod == '':
                        graceperiod = None
                    elif graceperiod is not None:
                        graceperiod = int(graceperiod)
                except ValueError:
                    raise HTTPError(400, 'Time not a number')

                self.store.write_job_config(id_, graceperiod, timeout)
                raise HTTPRedirect("/job/" + str(id_))

            else:
                config = self.store.get_job_config(id_)

                if config is None:
                    orphan = self.store.get_orphan_configs()
                else:
                    orphan = None

                return self._write_template('jobconfig.html',
                           {'id': id_, 'info': info, 'config': config,
                            'orphan': orphan})

        else:
            raise HTTPError(404)

    @cherrypy.expose
    def user(self, user):
        """Displays crontabs belonging to a particular user."""
        return self._user_host_crontabs(user=user)

    @cherrypy.expose
    def host(self, host):
        """Displays crontabs belonging to a particular user."""
        return self._user_host_crontabs(host=host)

    def _user_host_crontabs(self, host=None, user=None):
        """Displays crontab listing, either by host or user."""

        jobs = {}
        raw = {}
        info = {'jobs': jobs, 'raw': raw}

        if host is None and user is not None:
            by_user = False
            info['user'] = user
            info['host'] = None
        elif host is not None and user is None:
            by_user = True
            info['host'] = host
            info['user'] = None
        else:
            raise HTTPError(500)

        for job in self.store.get_jobs(host, user, include_deleted=True):
            if by_user:
                key = job['user']
            else:
                key = job['host']

            if key in jobs:
                jobs[key].append(job)
            else:
                jobs[key] = [job]
                raw[key] = self.store.get_raw_crontab(job['host'], job['user'])

        return self._write_template('crontabs.html', info)

    def _write_template(self, name, dict={}):
        """Returns the output from the named template when rendered
        with the given dict.

        Traps template errors and uses mako.exceptions to display them."""

        try:
            template = self.templ.get_template(name)
            return template.render(**dict)
        except:
            return exceptions.html_error_template().render()

