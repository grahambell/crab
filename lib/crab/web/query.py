# Copyright (C) 2012-2014 Science and Technology Facilities Council.
# Copyright (C) 2015-2018 East Asian Observatory.
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

from datetime import datetime
from json import JSONEncoder

import cherrypy
from cherrypy import HTTPError
import pytz

from crab.util.datetime import format_datetime
from crab.web import CrabWebBase


class CrabWebQuery(CrabWebBase):
    """CherryPy handler class for the JSON query part of the crab web
    interface."""

    def __init__(self):
        """Constructor: saves the given storage backend."""

        super(CrabWebQuery, self).__init__(cherrypy.engine)

        def to_json(obj):
            if isinstance(obj, datetime):
                return format_datetime(obj)
            raise TypeError('Cannot JSON-encode object')

        self.json_encoder = JSONEncoder(default=to_json)

    @cherrypy.expose
    def jobstatus(self, startid, alarmid, finishid):
        """CherryPy handler returning the job status dict fetched
        from the monitor thread."""

        try:
            s = self.monitor.wait_for_event_since(
                int(startid), int(alarmid), int(finishid))

            s['service'] = dict(
                (s, self.service[s].is_alive())
                for s in self.service)

            return self.json_encoder.encode(s)

        except ValueError:
            raise HTTPError(400, 'Query parameter not an integer')

    @cherrypy.expose
    def jobinfo(self, id_):
        """CherryPy handler returning the job information for the given job."""
        try:
            info = self.store.get_job_info(int(id_))
        except ValueError:
            raise HTTPError(400, 'Job ID not a number')
        if info is None:
            raise HTTPError(404, 'Job not found')

        info['id'] = id_
        return self.json_encoder.encode(info)

    @cherrypy.expose
    def timezones(self):
        """CherryPy handler to return a list of timezones."""

        info = list(pytz.common_timezones)

        return self.json_encoder.encode(info)
