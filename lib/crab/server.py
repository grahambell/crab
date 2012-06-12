import json
import socket
import urllib

import cherrypy
from cherrypy import HTTPError

from crab import CrabError, CrabStatus

class CrabServer:
    def __init__(self, store):
        self.store = store

    @cherrypy.expose
    def crontab(self, host, user):
        if cherrypy.request.method == 'GET':
            try:
                crontab = self.store.get_crontab(host, user)
                return json.dumps({'crontab': crontab})
            except CrabError as err:
                raise HTTPError(message='read error : ' + str(err))

        elif cherrypy.request.method == 'PUT':
            try:
                data = self.read_json()
                crontab = data.get('crontab')

                if crontab is None:
                    raise CrabError('no crontab received')

                self.store.save_crontab(host, user, crontab,
                                        timezone=data.get('timezone'))

            except CrabError as err:
                raise HTTPError(message='write error : ' + str(err))

    @cherrypy.expose
    def start(self, host, user, id=None):
        try:
            data = self.read_json()
            command = data.get('command')

            if command is None:
                raise CrabError('cron command not specified')

            self.store.log_start(host, user, id, command)

        except CrabError as err:
            raise HTTPError(message='log error : ' + str(err))

    @cherrypy.expose
    def finish(self, host, user, id=None):
        try:
            data = self.read_json()
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

    def read_json(self):
        try:
            return json.load(cherrypy.request.body)
        except ValueError:
            raise HTTPError('Did not understand JSON')

