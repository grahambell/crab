import ConfigParser
# Workaround lack of JSON in Python 2.4
try:
    import json
except ImportError:
    import simplejson as json
import os
import socket
import urllib
from httplib import HTTPConnection, HTTPException

from crab import CrabError, CrabStatus

class CrabClient:
    """Crab client class, used for interaction with the server."""

    def __init__(self, command=None, jobid=None):
        """Constructor for CrabClient.

        This causes the client to configure itself,
        by looking for the crab.ini file.  If the environment
        variables CRABHOST or CRABPORT exist, these override
        settings from the configuration files.

        If the client has been started to report on the status of a
        job, then the command must be supplied, and the jobid should
        be given if known.
        """
        self.command = command
        self.jobid = jobid

        self.config = ConfigParser.SafeConfigParser()
        self.config.add_section('server')
        self.config.set('server', 'host', 'localhost')
        self.config.set('server', 'port', '8000')
        self.config.add_section('client')
        self.config.set('client', 'hostname', socket.gethostname())
        self.config.set('client', 'username', os.getlogin())

        self.config.read(['/etc/crab/crab.ini',
                          os.path.expanduser('~/.crab/crab.ini')])

        if os.environ.has_key('CRABHOST'):
            self.config.set('server', 'host', os.environ['CRABHOST'])
        if os.environ.has_key('CRABPORT'):
            self.config.set('server', 'port', os.environ['CRABPORT'])

    def start(self):
        """Notify the server that the job is starting."""

        self._write_json(self._get_url('start'),
                        {'command': self.command})

    def finish(self, status=CrabStatus.UNKNOWN,
               stdoutdata='', stderrdata=''):
        """Notify the server that the job is finishing."""

        self._write_json(self._get_url('finish'),
                        {'command': self.command,
                         'status':   status,
                         'stdout':   stdoutdata,
                         'stderr':   stderrdata})

    def fail(self, status=CrabStatus.FAIL, message=''):
        """Notify the server that the job has failed.

        This is a convenience method calling CrabClient.finish."""

        self.finish(status, stderrdata=message)

    def send_crontab(self, crontab, timezone=None):
        """Takes the crontab as a string, breaks it into lines,
        and transmits it to the server."""

        self._write_json(self._get_url('crontab'),
                        {'crontab': crontab.split('\n'),
                         'timezone': timezone})

    def fetch_crontab(self):
        """Retrieves crontab lines from the server, and returns
        them as a single string."""

        data = self._read_json(self._get_url('crontab'))
        return '\n'.join(data['crontab'])

    def _get_url(self, action):
        """Creates the URL to be used to perform the given server action."""

        url = ('/api/0/' + action +
               '/' + urllib.quote(self.config.get('client', 'hostname'), '') +
               '/' + urllib.quote(self.config.get('client', 'username'), ''))

        if self.jobid is not None:
            url = url + '/' + urllib.quote(self.jobid, '')

        return url

    def _get_conn(self):
        """Opens an HTTP connection to the configured server."""

        return HTTPConnection(self.config.get('server', 'host'),
                              self.config.get('server', 'port'))

    def _read_json(self, url):
        """Performs an HTTP GET on the given URL and interprets the
        response as JSON."""

        try:
            conn = self._get_conn()
            conn.request('GET', url)

            res = conn.getresponse()
            if res.status != 200:
                raise CrabError('server error : ' + res.reason)

            return json.load(res)

        #except HTTPException as err:
        except HTTPException, err:
            raise CrabError('HTTP error : ' + str(err))

        #except socket.error as err:
        except socket.error, err:
            raise CrabError('socket error : ' + str(err))

        #except ValueError as err:
        except ValueError, err:
            raise CrabError('did not understand response : ' + str(err))

    def _write_json(self, url, obj):
        """Converts the given object to JSON and sends it with an
        HTTP PUT to the given URL."""

        try:
            conn = self._get_conn()
            conn.request('PUT', url, json.dumps(obj))

            res = conn.getresponse()

            if res.status != 200:
                raise CrabError('server error : ' + res.reason)

        #except HTTPException as err:
        except HTTPException, err:
            raise CrabError('HTTP error : ' + str(err))

        #except socket.error as err:
        except socket.error, err:
            raise CrabError('socket error : ' + str(err))

