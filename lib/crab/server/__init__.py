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

from codecs import latin_1_encode, latin_1_decode
import json
import socket

import cherrypy
from cherrypy import HTTPError

from crab import CrabError, CrabStatus

class CrabServer:
    """Crab server class, used for interaction with the client."""

    def __init__(self, store):
        """Constructor for CrabServer.

        Saves a reference to the given storage backend."""

        self.store = store

    @cherrypy.expose
    def crontab(self, host, user, raw=False):
        """CherryPy handler for the crontab action.

        Allows the client to PUT a new crontab, or use a GET
        request to see a crontab-style representation of the
        job information held in the the storage backend."""

        if cherrypy.request.method == 'GET':
            try:
                if raw:
                    crontab = self.store.get_raw_crontab(host, user)
                else:
                    crontab = self.store.get_crontab(host, user)
                return json.dumps({'crontab': crontab})
            except CrabError as err:
                cherrypy.log.error('CrabError: read error: ' + str(err))
                raise HTTPError(message='read error: ' + str(err))

        elif cherrypy.request.method == 'PUT':
            try:
                data = self._read_json()
                crontab = data.get('crontab')

                if crontab is None:
                    raise CrabError('no crontab received')

                warning = self.store.save_crontab(host, user, crontab,
                             timezone=data.get('timezone'))

                return json.dumps({'warning': warning})

            except CrabError as err:
                cherrypy.log.error('CrabError: write error: ' + str(err))
                raise HTTPError(message='write error: ' + str(err))

    @cherrypy.expose
    def start(self, host, user, crabid=None):
        """CherryPy handler allowing clients to report jobs starting."""

        try:
            data = self._read_json()
            command = data.get('command')

            if command is None:
                raise CrabError('cron command not specified')

            self.store.log_start(host, user, crabid, command)

        except CrabError as err:
            cherrypy.log.error('CrabError: log error: ' + str(err))
            raise HTTPError(message='log error: ' + str(err))

    @cherrypy.expose
    def finish(self, host, user, crabid=None):
        """CherryPy handler allowing clients to report jobs finishing."""

        try:
            data = self._read_json()
            command = data.get('command')
            status = data.get('status')

            if command is None or status is None:
                raise CrabError('insufficient information to log finish')

            if status not in CrabStatus.VALUES:
                raise CrabError('invalid finish status')

            self.store.log_finish(host, user, crabid, command, status,
                                  data.get('stdout'), data.get('stderr'))

        except CrabError as err:
            cherrypy.log.error('CrabError: log error: ' + str(err))
            raise HTTPError(message='log error: ' + str(err))

    def _read_json(self):
        """Attempts to interpret the HTTP PUT body as JSON and return
        the corresponding Python object.

        There could be a correpsonding _write_json method, but there
        is little need as the caller can just do: return json.dumps(...)
        and the CherryPy handler needs to pass the response back with
        return."""

        message = latin_1_decode(cherrypy.request.body.read(), 'replace')[0]

        try:
            return json.loads(message)
        except ValueError:
            cherrypy.log.error('CrabError: Failed to read JSON: ' + message)
            raise HTTPError(400, message='Did not understand JSON')

