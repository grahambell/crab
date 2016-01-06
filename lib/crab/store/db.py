# Copyright (C) 2012-2014 Science and Technology Facilities Council.
# Copyright (C) 2015-2016 East Asian Observatory.
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

from __future__ import print_function

from datetime import datetime
from threading import Lock

import pytz

from crab import CrabError, CrabStatus
from crab.store import CrabStore


class CrabDBLock():
    def __init__(self, conn, error_class, cursor_args={}, ping=False):
        self.lock = Lock()
        self.conn = conn
        self.error_class = error_class
        self.cursor_args = cursor_args
        self.ping = ping

    def __enter__(self):
        self.lock.acquire(True)

        # Open a cursor, but be sure to release the lock again if this
        # fails.
        try:
            if self.ping:
                self.conn.ping(reconnect=True, attempts=2, delay=5)

            self.cursor = self.conn.cursor(**self.cursor_args)

        except self.error_class as err:
            self.lock.release()
            raise CrabError('database error (opening cursor): ' + str(err))

        except:
            self.lock.release()
            raise

        return self.cursor

    def __exit__(self, type_, value, tb):
        new_exception = None

        # Use try-finally block to ensure we release the lock whatever
        # happens (for extra safety -- the try-except blocks should
        # allow us to keep going anyway).
        try:
            # Close and delete cursor.
            try:
                self.cursor.close()
                del self.cursor

            except Exception as err:
                new_exception = CrabError(
                    'database error (closing cursor): ' + str(err))

            # Commit the transaction, or roll back if an exception occurred
            # during the transaction.
            try:
                if type_ is None:
                    self.conn.commit()
                else:
                    self.conn.rollback()

            except Exception as err:
                new_exception = CrabError(
                    'database error (ending transaction): ' + str(err))

        finally:
            self.lock.release()

        # If an exception happened during the transaction, raise if it was
        # database error, otherwise leave it alone (do nothing).  If there
        # wasn't an exception, but we have a new one, raise it.
        if type_ is not None:
            if issubclass(type_, self.error_class):
                raise CrabError('database error: ' + str(value))

        elif new_exception is not None:
            raise new_exception


class CrabStoreDB(CrabStore):
    """Crab storage backend using a database.

    Currently written for SQLite but since it uses the Python DB API
    it should be possible to generalize it by altering the queries
    based on the database type where necessary."""

    def __init__(self, lock, outputstore=None):
        """Constructor for CrabDB.

        Records the reference to the database connection for future reference.

        A separate storage backend can be provided for the storage of
        job output.  An outputstore should implement write_job_output
        and get_job_output, and if provided will be used instead of
        writing the stdout and stderr from the cron jobs to the database.
        The outputstore should only raise instances of CrabError."""

        self.lock = lock
        self.outputstore = outputstore

    def _get_jobs(self, c, host, user, include_deleted=False,
                  crabid=None, command=None, without_crabid=False):
        """Private/protected version of get_jobs which does not
        acquire the lock, and takes more search parameters."""

        params = []
        conditions = []

        if not include_deleted:
            conditions.append('deleted IS NULL')

        if host is not None:
            conditions.append('host=?')
            params.append(host)

        if user is not None:
            conditions.append('user=?')
            params.append(user)

        if crabid is not None:
            conditions.append('crabid=?')
            params.append(crabid)

        if command is not None:
            conditions.append('command=?')
            params.append(command)

        if without_crabid:
            if crabid is not None:
                raise CrabError(
                    '_get_jobs called with crabid and without_crabid')

            conditions.append('crabid IS NULL')

        if conditions:
            where_clause = 'WHERE ' + ' AND '.join(conditions)
        else:
            where_clause = ''

        return self._query_to_dict_list(
            c,
            'SELECT id, host, user, crabid, command, time, timezone, '
            'installed AS "installed [timestamp]", '
            'deleted AS "deleted [timestamp]" '
            'FROM job ' + where_clause + ' '
            'ORDER BY host ASC, user ASC, crabid ASC, installed ASC', params)

    def _insert_job(self, c, host, user, crabid, time, command, timezone):
        """Inserts a job record into the database."""

        c.execute('INSERT INTO job (host, user, crabid, ' +
                  'time, command, timezone)' +
                  'VALUES (?, ?, ?, ?, ?, ?)',
                  [host, user, crabid, time, command, timezone])

        return c.lastrowid

    def _delete_job(self, c, id_):
        """Marks a job as deleted in the database."""

        c.execute('UPDATE job SET deleted=CURRENT_TIMESTAMP ' +
                  'WHERE id=?',
                  [id_])

    def _update_job(self, c, id_,
                    crabid=None, command=None, time=None, timezone=None):
        """Marks a job as not deleted, and updates its information.

        Only fields not given as None are updated."""

        fields = ['installed=CURRENT_TIMESTAMP', 'deleted=NULL']
        params = []

        if crabid is not None:
            fields.append('crabid=?')
            params.append(crabid)

        if command is not None:
            fields.append('command=?')
            params.append(command)

        if time is not None:
            fields.append('time=?')
            params.append(time)

        if timezone is not None:
            fields.append('timezone=?')
            params.append(timezone)

        params.append(id_)

        c.execute('UPDATE job SET ' + ', '.join(fields) + ' '
                  'WHERE id=?', params)

    def _log_start(self, c, id_, command):
        """Inserts a job start record into the database.

        Private method to perform only the actual insertion.  The lock
        should already have been acquired."""

        c.execute('INSERT INTO jobstart (jobid, command) '
                  'VALUES (?, ?)',
                  [id_, command])

    def _log_finish(self, c, id_, command, status):
        """Inserts a job finish record into the database.

        Private method to perform only the actual insertion.  The lock
        should already have been acquired.

        Returns the finish record ID."""

        c.execute('INSERT INTO jobfinish (jobid, command, status) ' +
                  'VALUES (?, ?, ?)',
                  [id_, command, status])

        return c.lastrowid

    def log_alarm(self, id_, status):
        """Inserts an alarm regarding a job into the database.

        This is for alarms generated interally by crab, for example
        from the monitor thread.  Such alarms are currently stored
        in an separate table and do not have any associated output
        records."""

        with self.lock as c:
            c.execute('INSERT INTO jobalarm (jobid, status) VALUES (?, ?)',
                      [id_, status])

    def get_job_info(self, id_):
        """Retrieve information about a job by ID number."""

        with self.lock as c:
            return self._query_to_dict(
                c,
                'SELECT host, user, command, crabid, time, timezone, '
                'installed AS "installed [timestamp]", '
                'deleted AS "deleted [timestamp]" '
                'FROM job WHERE id = ?', [id_])

    def _get_job_config(self, c, id_):
        """Private/protected version of get_job_config which does
        not acquire the lock."""

        return self._query_to_dict(
            c,
            'SELECT id AS configid, graceperiod, timeout, ' +
            'success_pattern, warning_pattern, fail_pattern, ' +
            'note, inhibit ' +
            'FROM jobconfig WHERE jobid = ?', [id_])

    def write_job_config(
            self, id_, graceperiod=None, timeout=None,
            success_pattern=None, warning_pattern=None, fail_pattern=None,
            note=None, inhibit=False):
        """Writes configuration data for a job by ID number.

        Returns the configuration ID number."""

        with self.lock as c:
            row = self._query_to_dict(
                c,
                'SELECT id as configid FROM jobconfig '
                'WHERE jobid = ?', [id_])

            if row is None:
                c.execute(
                    'INSERT INTO jobconfig (jobid, graceperiod, '
                    'timeout, success_pattern, warning_pattern, '
                    'fail_pattern, note, inhibit) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                    [id_, graceperiod, timeout,
                     success_pattern, warning_pattern, fail_pattern,
                     note, inhibit])

                return c.lastrowid

            else:
                configid = row['configid']
                if configid is None:
                    raise CrabError('job config: got null id')

                c.execute(
                    'UPDATE jobconfig SET graceperiod=?, timeout=?, '
                    'success_pattern=?, warning_pattern=?, '
                    'fail_pattern=?, note=?, inhibit=? '
                    'WHERE id=?',
                    [graceperiod, timeout,
                     success_pattern, warning_pattern, fail_pattern,
                     note, inhibit, configid])

                return configid

    def disable_inhibit(self, id_):
        """Disable the inhibit setting for a job.

        This is a convenience routine to simply disable the inhibit
        job configuration parameter without having to read and write
        the rest of the configuration.
        """

        with self.lock as c:
            c.execute('UPDATE jobconfig SET inhibit=0 WHERE jobid=?',
                      [id_])

    def get_orphan_configs(self):
        """Make a list of orphaned job configuration records."""

        with self.lock as c:
            return self._query_to_dict_list(
                c,
                'SELECT jobconfig.id AS configid, job.id AS id, '
                'host, user, job.crabid AS crabid, command '
                'FROM jobconfig JOIN job ON jobconfig.jobid = job.id '
                'WHERE job.deleted IS NOT NULL')

    def relink_job_config(self, configid, id_):
        with self.lock as c:
            c.execute('UPDATE jobconfig SET jobid = ? '
                      'WHERE id = ?', [id_, configid])

    def get_job_finishes(self, id_, limit=100,
                         finishid=None, before=None, after=None,
                         include_alreadyrunning=False):
        """Retrieves a list of recent job finish events for the given job,
        most recent first.

        Can optionally find a particular finish, or finishes before
        or after a certain finish.  In the case of finishes after
        a certain finish, the most recent event will be last.

        ALREADYRUNNING events are only reported if the include_alreadyrunning
        argument is set."""

        conditions = ['jobid = ?']
        params = [id_]
        order = 'DESC'

        if finishid is not None:
            conditions.append('id = ?')
            params.append(finishid)

        elif before is not None:
            conditions.append('id < ?')
            params.append(before)

        elif after is not None:
            conditions.append('id > ?')
            params.append(after)
            order = 'ASC'

        if not include_alreadyrunning:
            conditions.append('status <> ?')
            params.append(CrabStatus.ALREADYRUNNING)

        if limit is not None:
            limit_clause = 'LIMIT ?'
            params.append(limit)
        else:
            limit_clause = ''

        with self.lock as c:
            return self._query_to_dict_list(
                c,
                'SELECT id AS finishid, datetime AS "datetime [timestamp]", '
                'command, status '
                'FROM jobfinish '
                'WHERE ' + ' AND '.join(conditions) + ' '
                'ORDER BY datetime ' + order + ' ' + limit_clause,
                params)

    def get_job_events(self, id_, limit=100, start=None, end=None):
        """Fetches a combined list of events relating to the specified job.

        Return events, newest first (with finishes first for the same
        datetime).  This ordering allows us to apply the SQL limit on
        number of result rows to find the most recent events.  It gives
        the correct ordering for the job info page."""

        conditions = ['jobid=?']
        params = [id_]

        if start is not None:
            conditions.append('datetime>=?')
            params.append(start.astimezone(pytz.UTC))

        if end is not None:
            conditions.append('datetime<?')
            params.append(end.astimezone(pytz.UTC))

        where_clause = 'WHERE ' + ' AND '.join(conditions)
        params = params * 3

        if limit is None:
            limit_clause = ''
        else:
            limit_clause = 'LIMIT ?'
            params.append(limit)

        with self.lock as c:
            return self._query_to_dict_list(
                c,
                'SELECT ' +
                '    id AS eventid, 1 AS type, ' +
                '    datetime AS "datetime [timestamp]", ' +
                '    command, NULL AS status ' +
                '    FROM jobstart ' + where_clause + ' ' +
                'UNION SELECT ' +
                '    id AS eventid, 2 AS type, ' +
                '    datetime AS "datetime [timestamp]", ' +
                '    NULL AS command, status ' +
                '    FROM jobalarm ' + where_clause + ' ' +
                'UNION SELECT ' +
                '    id AS eventid, 3 AS type, ' +
                '    datetime AS "datetime [timestamp]", ' +
                '    command, status ' +
                '    FROM jobfinish ' + where_clause + ' ' +
                'ORDER BY datetime DESC, type DESC ' + limit_clause,
                params)

    def get_events_since(self, startid, alarmid, finishid):
        """Extract minimal summary information for events on all jobs
        since the given IDs, oldest first."""

        with self.lock as c:
            return self._query_to_dict_list(
                c,
                'SELECT ' +
                '    jobid, id AS eventid, 1 AS type, ' +
                '    datetime AS "datetime [timestamp]", ' +
                '    NULL AS status FROM jobstart ' +
                '    WHERE id > ? ' +
                'UNION SELECT ' +
                '    jobid, id AS eventid, 2 AS type, ' +
                '    datetime AS "datetime [timestamp]", ' +
                '    status FROM jobalarm ' +
                '    WHERE id > ? ' +
                'UNION SELECT ' +
                '    jobid, id AS eventid, 3 AS type, ' +
                '    datetime AS "datetime [timestamp]", ' +
                '    status FROM jobfinish ' +
                '    WHERE id > ? ' +
                'ORDER BY datetime ASC, type ASC',
                [startid, alarmid, finishid])

    def get_fail_events(self, limit=40):
        """Retrieves the most recent failures for all events,
        combining the finish and alarm tables.

        This method has to include a list of status codes to exclude
        since the filtering is done in the SQL.  The codes skipped
        are CLEARED, LATE, SUCCESS, ALREADYRUNNING and INHIBITED."""

        with self.lock as c:
            return self._query_to_dict_list(
                c,
                'SELECT ' +
                '    job.id AS id, status, ' +
                '    datetime AS "datetime [timestamp]", ' +
                '    host, user, ' +
                '    job.crabid AS crabid, jobfinish.command AS command, ' +
                '    jobfinish.id AS finishid ' +
                '    FROM jobfinish JOIN job ON jobfinish.jobid = job.id ' +
                '    WHERE status NOT IN (?, ?, ?) ' +
                'UNION SELECT ' +
                '    job.id AS id, status, ' +
                '    datetime AS "datetime [timestamp]", ' +
                '    host, user, ' +
                '    job.crabid AS crabid, job.command AS command, ' +
                '    NULL as finishid ' +
                '    FROM jobalarm JOIN job ON jobalarm.jobid = job.id ' +
                '    WHERE status NOT IN (?, ?) ' +
                'ORDER BY datetime DESC, status DESC LIMIT ?',
                [CrabStatus.SUCCESS, CrabStatus.ALREADYRUNNING,
                 CrabStatus.INHIBITED,
                 CrabStatus.CLEARED, CrabStatus.LATE,
                 limit])

    def delete_old_events(self, datetime_):
        """Delete events older than the given datetime."""

        with self.lock as c:
            c.execute('DELETE FROM jobalarm WHERE datetime<?', [datetime_])
            c.execute('DELETE FROM jobstart WHERE datetime<?', [datetime_])
            c.execute('DELETE FROM jobfinish WHERE datetime<?', [datetime_])

    def _write_job_output(self, c, finishid, host, user, id_, crabid,
                          stdout, stderr):
        """Writes the job output to the database.

        This method does not require the host, user, job ID number or Crab ID,
        but these arguments are accepted for compatability with stores which
        may require them."""

        c.execute('INSERT INTO joboutput (finishid, stdout, stderr) ' +
                  'VALUES (?, ?, ?)',
                  [finishid, stdout, stderr])

    def _get_job_output(self, c, finishid, host, user, id_, crabid):
        """Fetches the standard output and standard error for the
        given finish ID.

        This method does not require the host, user, job ID number or Crab ID,
        but these arguments are accepted for compatability with stores which
        may require them."""

        c.execute('SELECT stdout, stderr FROM joboutput ' +
                  'WHERE finishid=?', [finishid])

        row = c.fetchone()

        if row is None:
            return ('', '')

        return row

    def _write_raw_crontab(self, c, host, user, crontab):
        entry = self._query_to_dict(
            c,
            'SELECT id FROM rawcrontab WHERE host = ? AND user = ?',
            [host, user])

        if entry is None:
            c.execute(
                'INSERT INTO rawcrontab (host, user, crontab) '
                'VALUES (?, ?, ?)',
                [host, user, '\n'.join(crontab)])
        else:
            c.execute(
                'UPDATE rawcrontab SET crontab = ? WHERE id = ?',
                ['\n'.join(crontab), entry['id']])

    def _get_raw_crontab(self, c, host, user):
        entry = self._query_to_dict(
            c,
            'SELECT crontab FROM rawcrontab WHERE host = ? AND user = ?',
            [host, user])

        if entry is None:
            return None
        else:
            return entry['crontab'].split('\n')

    def get_notifications(self):
        """Fetches a list of notifications, combining those defined
        by a config ID with those defined by user and/or host."""

        with self.lock as c:
            return self._query_to_dict_list(
                c,
                'SELECT jobnotify.id AS notifyid, method, address, '
                '    skip_ok, skip_warning, skip_error, include_output, '
                '    jobconfig.jobid AS id, jobnotify.time AS time, '
                '    COALESCE(jobnotify.timezone, job.timezone) AS timezone '
                '    FROM jobnotify '
                '    JOIN jobconfig ON jobnotify.configid = jobconfig.id '
                '    JOIN job ON job.id = jobconfig.jobid '
                '    WHERE configid IS NOT NULL AND job.deleted IS NULL '
                'UNION SELECT jobnotify.id AS notifyid, method, address, '
                '    skip_ok, skip_warning, skip_error, include_output, '
                '    job.id AS id, jobnotify.time AS time, '
                '    COALESCE(jobnotify.timezone, job.timezone) AS timezone '
                '    FROM jobnotify JOIN job '
                '        ON COALESCE(job.user = jobnotify.user, 1) '
                '        AND COALESCE(job.host = jobnotify.host, 1) '
                '    WHERE configid IS NULL AND job.deleted IS NULL',
                [])

    def get_job_notifications(self, configid):
        """Fetches all of the notifications configured for the given
        configid."""

        with self.lock as c:
            return self._query_to_dict_list(
                c,
                'SELECT id AS notifyid, '
                'method, address, time, timezone, '
                'skip_ok, skip_warning, skip_error, include_output '
                'FROM jobnotify WHERE configid=?', [configid])

    def get_match_notifications(self, host=None, user=None):
        """Fetches matching notifications which are not tied to a
        configuration entry."""

        params = []
        conditions = ['configid IS NULL']

        if host is not None:
            params.append(host)
            conditions.append('host=?')
        if user is not None:
            params.append(user)
            conditions.append('user=?')

        where_clause = 'WHERE ' + ' AND '.join(conditions)

        with self.lock as c:
            return self._query_to_dict_list(
                c,
                'SELECT id AS notifyid, host, user, '
                'method, address, time, timezone, '
                'skip_ok, skip_warning, skip_error, include_output '
                'FROM jobnotify ' + where_clause, params)

    def write_notification(self, notifyid, configid, host, user,
                           method, address, time, timezone,
                           skip_ok, skip_warning, skip_error, include_output):
        """Adds or updates a notification record in the database."""

        if configid is not None and ((host is not None) or (user is not None)):
            raise CrabError('writing notification: job config and match '
                            'parameters both specified')

        with self.lock as c:
            if notifyid is None:
                c.execute('INSERT INTO jobnotify (configid, host, user, '
                          'method, address, time, timezone, skip_ok, '
                          'skip_warning, skip_error, include_output) '
                          'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                          [configid, host, user, method, address,
                           time, timezone, skip_ok,
                           skip_warning, skip_error, include_output])
            else:
                c.execute('UPDATE jobnotify SET configid=?, host=?, '
                          'user=?, method=?, address=?, time=?, '
                          'timezone=?, skip_ok=?, skip_warning=?, '
                          'skip_error=?, include_output=? '
                          'WHERE id=?',
                          [configid, host, user, method, address,
                           time, timezone, skip_ok,
                           skip_warning, skip_error, include_output,
                           notifyid])

    def delete_notification(self, notifyid):
        """Removes a notification from the database."""

        with self.lock as c:
            c.execute('DELETE FROM jobnotify WHERE id=?', [notifyid])

    def _query_to_dict(self, c, sql, param=[]):
        """Convenience method which returns a single row from
        _query_to_dict_list.

        Returns None if the result does not have exactly one row."""

        result = self._query_to_dict_list(c, sql, param)
        if len(result) == 1:
            return result[0]
        else:
            return None

    def _query_to_dict_list(self, c, sql, param=[]):
        """Execute an SQL query and return the result as a list of
        Python dict objects.

        The dict keys are retrieved from the SQL result using the
        description method of the DB cursor object.

        Any datetime values retieved have their timezone info set to UTC."""

        output = []

        c.execute(sql, param)

        while True:
            row = c.fetchone()
            if row is None:
                break

            dict = {}

            for (i, coldescription) in enumerate(c.description):
                value = row[i]
                if isinstance(value, datetime):
                    value = value.replace(tzinfo=pytz.UTC)
                dict[coldescription[0]] = value

            output.append(dict)

        return output
