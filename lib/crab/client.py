import ConfigParser
import json
import os
import socket
import urllib
from httplib import HTTPConnection, HTTPException

from crab import CrabError, CrabStatus

class CrabClient:
    def __init__(self, command=None, id=None):
        self.command = command
        self.id = id
        self.config = ConfigParser.ConfigParser()
        self.config.read('crab.ini')

    def start(self):
        self.write_json(self.get_url('start'),
                        {'command': self.command})

    def finish(self, status=CrabStatus.UNKNOWN,
               stdoutdata='', stderrdata=''):
        self.write_json(self.get_url('finish'),
                        {'command': self.command,
                         'status':   status,
                         'stdout':   stdoutdata,
                         'stderr':   stderrdata})

    def fail(self, status=CrabStatus.FAIL, message=''):
        self.finish(status, stderrdata=message)

    def send_crontab(self, crontab, timezone=None):
        self.write_json(self.get_url('crontab'),
                        {'crontab': crontab.split('\n'),
                         'timezone': timezone})

    def fetch_crontab(self):
        data = self.read_json(self.get_url('crontab'))
        return '\n'.join(data['crontab'])

    def get_host(self):
        try:
            return self.config.get('client', 'hostname')
        except ConfigParser.Error:
            return socket.gethostname()

    def get_user(self):
        if self.config.has_option('client', 'username'):
            return self.config.get('client', 'username')
        else:
            return os.getlogin()

    def get_url(self, action):
        url = ('/api/0/' + action +
               '/' + urllib.quote(self.get_host(), '') +
               '/' + urllib.quote(self.get_user(), ''))

        if self.id is not None:
            url = url + '/' + urllib.quote(self.id, '')

        return url

    def get_conn(self):
        host = 'localhost'
        port = 8000
        if self.config.has_option('server', 'host'):
            host = self.config.get('server', 'host')
        if self.config.has_option('server', 'port'):
            port = self.config.get('server', 'port')
        return HTTPConnection(host, port)

    def read_json(self, url):
        try:
            conn = self.get_conn()
            conn.request('GET', url)

            res = conn.getresponse()
            if res.status != 200:
                raise CrabError('server error : ' + res.reason)

            return json.load(res)

        except HTTPException as err:
            raise CrabError('HTTP error : ' + str(err))

        except socket.error as err:
            raise CrabError('socket error : ' + str(err))

        except ValueError as err:
            raise CrabError('did not understand response : ' + str(err))

    def write_json(self, url, obj):
        try:
            conn = self.get_conn()
            conn.request('PUT', url, json.dumps(obj))

            res = conn.getresponse()

            if res.status != 200:
                raise CrabError('server error : ' + res.reason)

        except HTTPException as err:
            raise CrabError('HTTP error : ' + str(err))

        except socket.error as err:
            raise CrabError('socket error : ' + str(err))

