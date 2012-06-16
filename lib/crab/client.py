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

        self.config = ConfigParser.SafeConfigParser()
        self.config.add_section('server')
        self.config.set('server', 'host', 'localhost')
        self.config.set('server', 'port', '8000')
        self.config.add_section('client')
        self.config.set('client', 'hostname', socket.gethostname())
        self.config.set('client', 'username', os.getlogin())

        self.config.read(['/etc/crab/crab.ini',
                          os.path.expanduser('~/.crab/crab.ini')])

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

    def get_url(self, action):
        url = ('/api/0/' + action +
               '/' + urllib.quote(self.config.get('client', 'hostname'), '') +
               '/' + urllib.quote(self.config.get('client', 'username'), ''))

        if self.id is not None:
            url = url + '/' + urllib.quote(self.id, '')

        return url

    def get_conn(self):
        return HTTPConnection(self.config.get('server', 'host'),
                              self.config.get('server', 'port'))

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

