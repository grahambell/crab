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
# ConfigParser renamed in Python 3
try:
    from configparser import SafeConfigParser
except:
    from ConfigParser import SafeConfigParser
# Workaround lack of JSON in Python 2.4
try:
    import json
except ImportError:
    import simplejson as json
import os
import pwd
import re
import socket
import sys
# urllib.quote moved into urllib.parse.quote in Python 3
try:
    from urllib.parse import quote as urlquote
except:
    from urllib import quote as urlquote
import urllib
# httplib renamed in Python 3
try:
    from http.client import HTTPConnection, HTTPException
except:
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

        self.config = SafeConfigParser()
        self.config.add_section('server')
        self.config.set('server', 'host', 'localhost')
        self.config.set('server', 'port', '8000')
        self.config.add_section('client')
        self.config.set('client', 'hostname', socket.gethostname())
        self.config.set('client', 'username', pwd.getpwuid(os.getuid())[0])

        if 'CRABSYSCONFIG' in os.environ:
            sysconfdir = os.environ['CRABSYSCONFIG']
        else:
            sysconfdir = '/etc/crab'

        self.configfiles = self.config.read([
                          os.path.join(sysconfdir, 'crab.ini'),
                          os.path.expanduser('~/.crab/crab.ini')])

        if 'CRABHOST' in os.environ:
            self.config.set('server', 'host', os.environ['CRABHOST'])
        if 'CRABPORT' in os.environ:
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

    def send_crontab(self, crontab, timezone=None):
        """Takes the crontab as a string, breaks it into lines,
        and transmits it to the server.

        Returns a list of warnings."""

        data = self._write_json(self._get_url('crontab'),
                                {'crontab': crontab.split('\n'),
                                 'timezone': timezone},
                                read=True)

        return data['warning']

    def fetch_crontab(self, raw=False):
        """Retrieves crontab lines from the server, and returns
        them as a single string."""

        url = self._get_url('crontab')
        if raw:
            url = url + '?raw=true'
        data = self._read_json(url)

        if data['crontab'] is None:
            return  ''
        else:
            return '\n'.join(data['crontab'])

    def get_info(self):
        info = []
        info.append('Server: ' + self.config.get('server', 'host')
                         + ':' + self.config.get('server', 'port'))
        info.append('Client: ' + self.config.get('client', 'username')
                         + '@' + self.config.get('client', 'hostname'))
        info.append('Files: '  + ', '.join(self.configfiles))
        return '\n'.join(info)

    def _get_url(self, action):
        """Creates the URL to be used to perform the given server action."""

        url = ('/api/0/' + action +
               '/' + urlquote(self.config.get('client', 'hostname'), '') +
               '/' + urlquote(self.config.get('client', 'username'), ''))

        if self.jobid is not None:
            url = url + '/' + urlquote(self.jobid, '')

        return url

    def _get_conn(self):
        """Opens an HTTP connection to the configured server."""

        return HTTPConnection(self.config.get('server', 'host'),
                              self.config.get('server', 'port'))

    def _read_json(self, url):
        """Performs an HTTP GET on the given URL and interprets the
        response as JSON."""

        try:
            try:
                conn = self._get_conn()
                conn.request('GET', url)

                res = conn.getresponse()

                if res.status != 200:
                    raise CrabError('server error: ' + self._read_error(res))

                return json.loads(latin_1_decode(res.read(), 'replace')[0])

            #except HTTPException as err:
            #except HTTPException, err:
            except HTTPException:
                err = sys.exc_info()[1]
                raise CrabError('HTTP error: ' + str(err))

            #except socket.error as err:
            #except socket.error, err:
            except socket.error:
                err = sys.exc_info()[1]
                raise CrabError('socket error: ' + str(err))

            #except ValueError as err:
            #except ValueError, err:
            except ValueError:
                err = sys.exc_info()[1]
                raise CrabError('did not understand response: ' + str(err))

        finally:
            conn.close()

    def _write_json(self, url, obj, read=False):
        """Converts the given object to JSON and sends it with an
        HTTP PUT to the given URL.

        Optionally attempts to read JSON from the response."""

        try:
            try:
                conn = self._get_conn()
                conn.request('PUT', url, json.dumps(obj))

                res = conn.getresponse()

                if res.status != 200:
                    raise CrabError('server error: ' + self._read_error(res))

                if read:
                    return json.loads(latin_1_decode(res.read(), 'replace')[0])

            #except HTTPException as err:
            #except HTTPException, err:
            except HTTPException:
                err = sys.exc_info()[1]
                raise CrabError('HTTP error: ' + str(err))

            #except socket.error as err:
            #except socket.error, err:
            except socket.error:
                err = sys.exc_info()[1]
                raise CrabError('socket error: ' + str(err))

            #except ValueError as err:
            #except ValueError, err:
            except ValueError:
                err = sys.exc_info()[1]
                raise CrabError('did not understand response: ' + str(err))

        finally:
            conn.close()

    def _read_error(self, res):
        """Determine the error message to show based on an
        unsuccessful HTTP response.

        Currently use the HTTP status phrase or the first
        paragraph of the body, if found with a regular expression."""

        message = res.reason

        try:
            body = latin_1_decode(res.read(), 'replace')[0]
            match = re.search('<p>([^<]*)', body)
            if match:
                message = match.group(1)
        except:
            pass

        return message
