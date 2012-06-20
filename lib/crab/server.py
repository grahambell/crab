import json
import socket
import urllib

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
    def crontab(self, host, user):
        """CherryPy handler for the crontab action.

        Allows the client to PUT a new crontab, or use a GET
        request to see a crontab-style representation of the
        job information held in the the storage backend."""

        if cherrypy.request.method == 'GET':
            try:
                crontab = self.store.get_crontab(host, user)
                return json.dumps({'crontab': crontab})
            except CrabError as err:
                raise HTTPError(message='read error : ' + str(err))

        elif cherrypy.request.method == 'PUT':
            try:
                data = self._read_json()
                crontab = data.get('crontab')

                if crontab is None:
                    raise CrabError('no crontab received')

                self.store.save_crontab(host, user, crontab,
                                        timezone=data.get('timezone'))

            except CrabError as err:
                raise HTTPError(message='write error : ' + str(err))

    @cherrypy.expose
    def start(self, host, user, id=None):
        """CherryPy handler allowing clients to report jobs starting."""

        try:
            data = self._read_json()
            command = data.get('command')

            if command is None:
                raise CrabError('cron command not specified')

            self.store.log_start(host, user, id, command)

        except CrabError as err:
            raise HTTPError(message='log error : ' + str(err))

    @cherrypy.expose
    def finish(self, host, user, id=None):
        """CherryPy handler allowing clients to report jobs finishing."""

        try:
            data = self._read_json()
            command = data.get('command')
            status = data.get('status')

            if command is None or status is None:
                raise CrabError('insufficient information to log finish')

            if status not in CrabStatus.VALUES:
                raise CrabError('invalid finish status')

            self.store.log_finish(host, user, id, command, status,
                                  data.get('stdout'), data.get('stderr'))

        except CrabError as err:
            raise HTTPError(message='log error : ' + str(err))

    def _read_json(self):
        """Attempts to interpret the HTTP PUT body as JSON and return
        the corresponding Python object.

        There could be a correpsonding _write_json method, but there
        is little need as the caller can just do: return json.dumps(...)
        and the CherryPy handler needs to pass the response back with
        return."""

        try:
            return json.load(cherrypy.request.body)
        except ValueError:
            raise HTTPError('Did not understand JSON')

