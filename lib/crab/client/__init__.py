# Copyright (C) 2012-2014 Science and Technology Facilities Council.
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
from time import sleep
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

    def __init__(self, command=None, crabid=None):
        """Constructor for CrabClient.

        This causes the client to configure itself,
        by looking for the crab.ini file.  If the environment
        variables CRABHOST or CRABPORT exist, these override
        settings from the configuration files.

        If the client has been started to report on the status of a
        job, then the command must be supplied, and the crabid should
        be given if known.
        """
        self.command = command
        self.crabid = crabid

        self.config = SafeConfigParser()
        self.config.add_section('server')
        self.config.set('server', 'host', 'localhost')
        self.config.set('server', 'port', '8000')
        self.config.set('server', 'timeout', '30')
        self.config.set('server', 'max_tries', '1')
        self.config.set('server', 'retry_delay', '5')
        self.config.add_section('client')
        self.config.set('client', 'use_fqdn', 'false')

        env = os.environ

        # Read configuration files -- first system and then user.
        sysconfdir = env.get('CRABSYSCONFIG', '/etc/crab')
        userconfdir = env.get('CRABUSERCONFIG', os.path.expanduser('~/.crab'))

        self.configfiles = self.config.read([
            os.path.join(sysconfdir, 'crab.ini'),
            os.path.join(userconfdir, 'crab.ini')])

        # Override configuration as specified by environment variables.
        if 'CRABHOST' in env:
            self.config.set('server', 'host', env['CRABHOST'])
        if 'CRABPORT' in env:
            self.config.set('server', 'port', env['CRABPORT'])
        if 'CRABUSERNAME' in env:
            self.config.set('client', 'username', env['CRABUSERNAME'])
        if 'CRABCLIENTHOSTNAME' in env:
            self.config.set('client', 'hostname', env['CRABCLIENTHOSTNAME'])

        # Add computed defaults for some values if they have not already
        # been determined.  This avoids the need to perform these operations
        # if the value is already known and would allow the way in which this
        # is done to be customized based on other values.
        if not self.config.has_option('client', 'hostname'):
            if self.config.getboolean('client', 'use_fqdn'):
                self.config.set('client', 'hostname', socket.getfqdn())
            else:
                self.config.set('client', 'hostname',
                                socket.gethostname().split('.', 1)[0])

        if not self.config.has_option('client', 'username'):
            self.config.set('client', 'username', pwd.getpwuid(os.getuid())[0])

    def start(self):
        """Notify the server that the job is starting.

        Return the decoded server response, which may include
        an inhibit dictionary item."""

        return self._write_json(self._get_url('start'),
                                {'command': self.command},
                                read=True)

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
            return ''
        else:
            return '\n'.join(data['crontab'])

    def get_info(self):
        info = []
        info.append('Server: ' + self.config.get('server', 'host') +
                    ':' + self.config.get('server', 'port'))
        info.append('Client: ' + self.config.get('client', 'username') +
                    '@' + self.config.get('client', 'hostname'))
        if int(self.config.get('server', 'max_tries')) < 2:
            retry_info = '1 try'
        else:
            retry_info = (
                self.config.get('server', 'max_tries') +
                ' tries with ' +
                self.config.get('server', 'retry_delay') +
                's delay')
        info.append('Connection: ' +
                    self.config.get('server', 'timeout') +
                    's timeout, ' +
                    retry_info)
        info.append('Files: ' + ', '.join(self.configfiles))
        return '\n'.join(info)

    def _get_url(self, action):
        """Creates the URL to be used to perform the given server action."""

        url = ('/api/0/' + action +
               '/' + urlquote(self.config.get('client', 'hostname'), '') +
               '/' + urlquote(self.config.get('client', 'username'), ''))

        if self.crabid is not None:
            url = url + '/' + urlquote(self.crabid, '')

        return url

    def _get_conn(self):
        """Opens an HTTP connection to the configured server."""

        # Try first to construct the connection with a timeout.  However
        # this feature was added in Python 2.6, so for older versions of
        # Python, we must catch the TypeError and construct the object
        # without a timeout.
        try:
            conn = HTTPConnection(self.config.get('server', 'host'),
                                  self.config.get('server', 'port'),
                                  timeout=int(self.config.get(
                                                  'server', 'timeout')))
        except TypeError:
            conn = HTTPConnection(self.config.get('server', 'host'),
                                  self.config.get('server', 'port'))

        # Now attempt to open the connection, allowing for the configured
        # number of tries.
        max_tries = int(self.config.get('server', 'max_tries'))
        retry_delay = int(self.config.get('server', 'retry_delay'))

        n_try = 0
        while True:
            n_try += 1

            try:
                conn.connect()

            except:
                if n_try < max_tries:
                    sleep(retry_delay)
                    continue
                raise

            return conn

    def _read_json(self, url):
        """Performs an HTTP GET on the given URL and interprets the
        response as JSON."""

        conn = None

        try:
            try:
                conn = self._get_conn()
                conn.request('GET', url)

                res = conn.getresponse()

                if res.status != 200:
                    raise CrabError('server error: ' + self._read_error(res))

                return json.loads(latin_1_decode(res.read(), 'replace')[0])

            # except HTTPException as err:
            except HTTPException:
                err = sys.exc_info()[1]
                raise CrabError('HTTP error: ' + str(err))

            # except socket.error as err:
            except socket.error:
                err = sys.exc_info()[1]
                raise CrabError('socket error: ' + str(err))

            # except ValueError as err:
            except ValueError:
                err = sys.exc_info()[1]
                raise CrabError('did not understand response: ' + str(err))

        finally:
            if conn is not None:
                conn.close()

    def _write_json(self, url, obj, read=False):
        """Converts the given object to JSON and sends it with an
        HTTP PUT to the given URL.

        Optionally attempts to read JSON from the response."""

        conn = None

        try:
            try:
                conn = self._get_conn()
                conn.request('PUT', url, json.dumps(obj))

                res = conn.getresponse()

                if res.status != 200:
                    raise CrabError('server error: ' + self._read_error(res))

                if read:
                    response = latin_1_decode(res.read(), 'replace')[0]

                    # Check we got a response before attempting to decode
                    # it as JSON.  (Some messages did not have responses
                    # for previous server versions.)
                    if response:
                        return json.loads(response)
                    else:
                        return {}

            # except HTTPException as err:
            except HTTPException:
                err = sys.exc_info()[1]
                raise CrabError('HTTP error: ' + str(err))

            # except socket.error as err:
            except socket.error:
                err = sys.exc_info()[1]
                raise CrabError('socket error: ' + str(err))

            # except ValueError as err:
            except ValueError:
                err = sys.exc_info()[1]
                raise CrabError('did not understand response: ' + str(err))

        finally:
            if conn is not None:
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
