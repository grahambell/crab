import datetime
import pytz

from sqlite3 import DatabaseError

from crab import CrabError, CrabStatus
from crab.store import CrabStore

class CrabDB(CrabStore):
    """Crab storage backend using a database.

    Currently written for SQLite but since it uses the Python DB API
    it should be possible to generalize it by altering the queries
    based on the database type where necessary."""

    def __init__(self, conn, outputstore=None):
        """Constructor for CrabDB.

        Records the reference to the database connection for future reference.

        A separate storage backend can be provided for the storage of
        job output.  An outputstore should implement write_job_output
        and get_job_output, and if provided will be used instead of
        writing the stdout and stderr from the cron jobs to the database.
        The outputstore should only raise instances of CrabError."""

        self.conn = conn
        self.outputstore = outputstore

    # TODO: Because Python DB API transactions work at the connection
    # level rather than the cursor, we need to implement locking
    # so that we don't have two "transactions" open, and thus commit
    # them both when one completes.  One way would be to have the database
    # opened with check_same_thread turned off and route all updates
    # through a Queue.  These methods should be used internally by this
    # class, but for now they are just used by CrabStore.
    # Would be nice to allow for the 'with' command to be used.

    def _begin_transaction(self):
        pass

    def _commit_transaction(self):
        self.conn.commit()

    def _rollback_transaction(self):
        self.conn.rollback()

    def get_jobs(self, host=None, user=None, include_deleted=False):
        """Fetches a list of all of the cron jobs stored in the database,
        excluding deleted jobs by default.

        Optionally filters by host or username if these parameters are
        supplied."""

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

        if conditions:
            where_clause = 'WHERE ' + ' AND '.join(conditions)
        else:
            where_clause = ''

        return self._query_to_dict_list(
                'SELECT id, host, user, jobid, command, time, ' +
                    'installed, deleted ' +
                'FROM job ' + where_clause + ' ' +
                'ORDER BY host ASC, user ASC, installed ASC', params)

    # TODO merge this with the above function now that it
    # supports parameters.
    def get_user_jobs(self, host, user):
        """Reads cron job information corresponding to a particular
        host and user.

        Does not include deleted jobs."""

        return self._query_to_dict_list(
                'SELECT time, command, jobid, timezone ' +
                'FROM job WHERE host=? AND user=? AND deleted IS NULL ' +
                'ORDER BY installed ASC',
                [host, user])

    # TODO: decide if this function is in its most sensible form.
    # This version added while extracting the crontab importing code
    # from the database module.
    def get_user_job_set(self, host, user):
        """Prepares a set of job ID numbers for the given host and user
        including deleted jobs."""

        c = self.conn.cursor()
        id_ = set()

        try:
            c.execute('SELECT id FROM job WHERE host=? AND user=?',
                      [host, user])
            while True:
                row = c.fetchone()
                if row is None:
                    break
                id_.add(row[0])
        except DatabaseError as err:
            raise CrabError('database error : ' + str(err))

        finally:
            c.close()

        return id_

    # TODO: get rid of this method after updating the one below.

    def _check_job_with_cursor(self, host, user, jobid, command,
                               time, timezone):
        """Calls the private _check_job method with a new cursor."""

        c = self.conn.cursor()

        try:
            id_ = self._check_job(c, host, user, jobid, command,
                                  time, timezone)

        except DatabaseError as err:
            raise CrabError('database error : ' + str(err))

        finally:
            c.close()

        return id_

    # TODO: remove requirement to pass a cursor, since transactions
    # aren't based on cursors anyway.

    def _check_job(self, c, host, user, jobid, command,
                  time=None, timezone=None):
        """Ensure that a job exists in the database.

        Tries to find (and update if necessary) the corresponding job in
        the database.  If it is not found, the job is stored as a new
        entry.

        In either case, the job's ID number is returned.

        This is a private method because it must be run within
        a database transaction."""

        # We know the jobid, so use it to search

        if jobid is not None:
            c.execute('SELECT id, command, time, timezone, deleted ' +
                      'FROM job WHERE host=? AND user=? AND jobid=?',
                      [host, user, jobid])
            row = c.fetchone()

            if row is not None:
                (id_, dbcommand, dbtime, dbtz, deleted) = row

                if (deleted is None and
                        command == dbcommand and
                        (time is None or time == dbtime) and
                        (timezone is None or timezone == dbtz)):
                    pass

                else:
                    if time is None:
                        time = dbtime
                    if timezone is None:
                        timezone = dbtz

                    c.execute('UPDATE job SET command=?, time=?, ' +
                              'timezone=?, installed=CURRENT_TIMESTAMP, ' +
                              'deleted=NULL WHERE id=?',
                              [command, time, timezone, id_])

                return id_

            else:
                # Need to check if the job already existed without
                # a job ID, in which case we update it to add the job ID.

                c.execute('SELECT id, time, timezone, deleted ' +
                          'FROM job WHERE host=? AND user=? AND command=? ' +
                          'AND jobid IS NULL',
                          [host, user, command])

                row = c.fetchone()

                if row is not None:
                    (id_, dbtime, dbtz, deleted) = row

                    if time is None:
                        time = dbtime
                    if timezone is None:
                        timezone = dbtz

                    c.execute('UPDATE job SET time=?, timezone=?, ' +
                                  'jobid=?, '
                                  'installed=CURRENT_TIMESTAMP, deleted=NULL '
                              'WHERE id=?',
                              [time, timezone, jobid, id_])

                    return id_

                else:
                  self._insert_job(c, host, user, jobid, time,
                                   command, timezone)

                  return c.lastrowid

        # We don't know the jobid, so we must search by command.
        # In general we can't distinguish multiple copies of the same
        # command running at different times.
        # Such jobs should be given job IDs, or combined using
        # time ranges / steps.

        else:
            c.execute('SELECT id, time, timezone, deleted ' +
                      'FROM job WHERE host=? AND user=? AND command=?',
                      [host, user, command])

            row = c.fetchone()

            if row is not None:
                (id_, dbtime, dbtz, deleted) = row

                if (deleted is None and
                        (time is None or time == dbtime) and
                        (timezone is None or timezone == dbtz)):
                    pass

                else:
                    if time is None:
                        time = dbtime
                    if timezone is None:
                        timezone = dbtz

                    c.execute('UPDATE job SET time=?, timezone=?, ' +
                              'installed=CURRENT_TIMESTAMP, deleted=NULL ' +
                              'WHERE id=?',
                              [time, timezone, id_])

                return id_

            else:
                self._insert_job(c, host, user, jobid, time, command, timezone)

                return c.lastrowid

    def _insert_job(self, c, host, user, jobid, time, command, timezone):
        """Inserts a job record into the database."""

        c.execute('INSERT INTO job (host, user, jobid, ' +
                      'time, command, timezone)' +
                      'VALUES (?, ?, ?, ?, ?, ?)',
                  [host, user, jobid, time, command, timezone])

    def _delete_job(self, id_):
        """Marks a job as deleted in the database."""

        c = self.conn.cursor()

        try:
            c.execute('UPDATE job SET deleted=CURRENT_TIMESTAMP ' +
                      'WHERE id=?',
                      [id_])

        except DatabaseError as err:
            raise CrabError('database error : ' + str(err))

        finally:
            c.close()

    def log_start(self, host, user, jobid, command):
        """Inserts a job start record into the database."""

        c = self.conn.cursor()

        try:
            id_ = self._check_job(c, host, user, jobid, command)

            c.execute('INSERT INTO jobstart (jobid, command) VALUES (?, ?)',
                      [id_, command])

            self.conn.commit()

        except DatabaseError as err:
            raise CrabError('database error : ' + str(err))

        finally:
            c.close()

    def log_finish(self, host, user, jobid, command, status,
                   stdout=None, stderr=None):
        """Inserts a job finish record into the database.

        The output will be passed to the write_job_output method."""

        c = self.conn.cursor()

        try:
            id_ = self._check_job(c, host, user, jobid, command)

            c.execute('INSERT INTO jobfinish (jobid, command, status) ' +
                      'VALUES (?, ?, ?)',
                      [id_, command, status])

            finishid = c.lastrowid

            self.conn.commit()

            self.write_job_output(finishid, host, user, id_,
                                  stdout, stderr)

        except DatabaseError as err:
            raise CrabError('database error : ' + str(err))

        finally:
            c.close()

    def log_warning(self, id_, status):
        """Inserts a warning regarding a job into the database.

        This is for warnings generated interally by crab, for example
        from the monitor thread.  Such warnings are currently stored
        in an separate table and do not have any associated output
        records."""

        c = self.conn.cursor()

        try:
            c.execute('INSERT INTO jobwarn (jobid, status) VALUES (?, ?)',
                      [id_, status])

            self.conn.commit()

        except DatabaseError as err:
            raise CrabError('database error : ' + str(err))

        finally:
            c.close()

    def get_job_info(self, id_):
        """Retrieve information about a job by ID number."""

        return self._query_to_dict(
                'SELECT host, user, command, jobid, time, timezone, ' +
                    'installed, deleted ' +
                    'FROM job WHERE id = ?', [id_])

    def get_job_config(self, id_):
        """Retrieve configuration data for a job by ID number."""

        return self._query_to_dict(
                'SELECT graceperiod, timeout ' +
                'FROM jobconfig WHERE jobid = ?', [id_])

    def get_job_starts(self, id_, limit=100):
        """Retrieves a list of recent job starts for the given job,
        most recent first."""

        return self._query_to_dict_list(
                'SELECT id, datetime, command ' +
                    'FROM jobstart WHERE jobid = ? ' +
                    'ORDER BY datetime DESC LIMIT ?',
                [id_, limit])

    def get_job_finishes(self, id_, limit=100):
        """Retrieves a list of recent job finish events for the given job,
        most recent first."""

        return self._query_to_dict_list(
                'SELECT id, datetime, command, status ' +
                    'FROM jobfinish WHERE jobid = ? ' +
                    'ORDER BY datetime DESC LIMIT ?',
                [id_, limit])

    def get_job_events(self, id_, limit=100, start=None, end=None):
        """Fetches a combined list of events relating to the specified job.

        Return events, newest first (with finishes first for the same
        datetime).  This ordering allows us to apply the SQL limit on
        number of result rows to find the most recent events.  It gives
        the correct ordering for the job info page."""

        # TODO: implement start and end as WHERE clause.

        return self._query_to_dict_list(
                'SELECT ' +
                    'id, 1 AS type, ' +
                    'datetime, command, NULL AS status FROM jobstart ' +
                        'WHERE jobid = ? ' +
                'UNION SELECT ' +
                    'id, 2 AS type, ' +
                        'datetime, NULL AS command, status FROM jobwarn ' +
                        'WHERE jobid = ? ' +
                'UNION SELECT ' +
                    'id, 3 AS type, ' +
                        'datetime, command, status FROM jobfinish ' +
                        'WHERE jobid = ? ' +
                'ORDER BY datetime DESC, type DESC LIMIT ?',
                [id_, id_, id_, limit])

    def get_events_since(self, startid, warnid, finishid):
        """Extract minimal summary information for events on all jobs
        since the given IDs, oldest first."""

        return self._query_to_dict_list(
                'SELECT ' +
                    'jobid, id, 1 AS type, ' +
                    'datetime, NULL AS status FROM jobstart ' +
                    'WHERE id > ? ' +
                'UNION SELECT ' +
                    'jobid, id, 2 AS type, ' +
                    'datetime, status FROM jobwarn ' +
                    'WHERE id > ? ' +
                'UNION SELECT ' +
                    'jobid, id, 3 AS type, ' +
                    'datetime, status FROM jobfinish ' +
                    'WHERE id > ? ' +
                'ORDER BY datetime ASC, type ASC',
                [startid, warnid, finishid])

    def get_fail_events(self, limit=40):
        """Retrieves the most recent failures for all events,
        combining the finish and warning tables.

        This method has to include a list of status codes to exclude
        since the filtering is done in the SQL.  The codes skipped
        are LATE and SUCCESS."""

        return self._query_to_dict_list(
                'SELECT ' +
                    'job.id AS id, status, datetime, host, user, ' +
                    'job.jobid AS jobid, jobfinish.command AS command, ' +
                    'jobfinish.id AS finishid ' +
                    'FROM jobfinish JOIN job ON jobfinish.jobid = job.id ' +
                    'WHERE status NOT IN (?, ?) ' +
                'UNION SELECT ' +
                    'job.id AS id, status, datetime, host, user, ' +
                    'job.jobid AS jobid, job.command AS command, ' +
                    'NULL as finishid ' +
                    'FROM jobwarn JOIN job ON jobwarn.jobid = job.id ' +
                    'WHERE status NOT IN (?, ?) ' +
                'ORDER BY datetime DESC, status DESC LIMIT ?',
                [CrabStatus.SUCCESS, CrabStatus.LATE,
                 CrabStatus.SUCCESS, CrabStatus.LATE, limit])

    def _query_to_dict(self, sql, param=[]):
        """Convenience method which returns a single row from
        _query_to_dict_list.

        Returns None if the result does not have exactly one row."""

        result = self._query_to_dict_list(sql, param)
        if len(result) == 1:
            return result[0]
        else:
            return None

    def _query_to_dict_list(self, sql, param=[]):
        """Execute an SQL query and return the result as a list of
        Python dict objects.

        The dict keys are retrieved from the SQL result using the
        description method of the DB cursor object."""

        c = self.conn.cursor()
        output = []

        try:
            c.execute(sql, param)

            while True:
                row = c.fetchone()
                if row is None:
                    break

                dict = {}

                for (i, coldescription) in enumerate(c.description):
                    dict[coldescription[0]] = row[i]

                output.append(dict)

        except DatabaseError as err:
            raise CrabError('database error : ' + str(err))

        finally:
            c.close()

        return output

    def write_job_output(self, finishid, host, user, id_,
                         stdout, stderr):
        """Writes the job output to the database using the given cursor.

        However this method also allows calling without a cursor
        reference, in which case it will create one, and
        commit the transaction, closing the cursor before returning.

        This method does not require the host, user, or job ID
        number, but will pass them to the outputstore's corresponding
        method if it is defined rather than performing this action
        with the database."""

        if self.outputstore is not None:
            return self.outputstore.write_job_output(finishid, host, user, id_,
                                                     stdout, stderr)

        c = self.conn.cursor()

        try:
            c.execute('INSERT INTO joboutput (finishid, stdout, stderr) ' +
                      'VALUES (?, ?, ?)',
                      [finishid, stdout, stderr])

            self.conn.commit()

        except DatabaseError as err:
            raise CrabError('database error : ' + str(err))

        finally:
            c.close()

    def get_job_output(self, finishid, host, user, id_):
        """Fetches the standard output and standard error for the
        given finish ID.

        The result is returned as a two element list.  The parameters
        host, user and id number are passed on to the outputstore's
        get_job_output method if an outputstore was provided to the
        contructor, allowing the outputstore to organise its
        information hierarchically if desired.  Otherwise this method
        does not make use of those parameters."""

        if self.outputstore is not None:
            return self.outputstore.get_job_output(finishid, host, user, id_)

        c = self.conn.cursor()

        try:
            c.execute('SELECT stdout, stderr FROM joboutput ' +
                      'WHERE finishid=?', [finishid])

            row = c.fetchone()

            if row is None:
                raise CrabError('no output found')

            return row

        except DatabaseError as err:
            raise CrabError('database error : ' + str(err))

        finally:
            c.close()

    def parse_datetime(self, timestamp):
        """Parses the timestamp strings used by the database.

        This is a method in this class so that it could potentially
        adapt to different databases.

        The returned datetime object will include the correct timezone:
        for SQLite this is always UTC.

        An alternative thing to do would be to have _query_to_dict_list
        guess which fields are timestamps and automatically run this
        method on them."""

        return datetime.datetime.strptime(timestamp,
                        '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.UTC)

    def write_raw_crontab(self, host, user, crontab):
        if self.outputstore is not None and hasattr(self.outputstore,
                                                    'write_raw_crontab'):
            return self.outputstore.write_raw_crontab(host, user, crontab)

        entry = self._query_to_dict('SELECT id FROM rawcrontab ' +
                                    'WHERE host = ? AND user = ?',
                                    [host, user])

        c = self.conn.cursor()

        try:
            if entry is None:
                c.execute('INSERT INTO rawcrontab (host, user, crontab) ' +
                          'VALUES (?, ?, ?)', [host, user, '\n'.join(crontab)])
            else:
                c.execute('UPDATE rawcrontab SET crontab = ? WHERE id = ?',
                          ['\n'.join(crontab), entry['id']])

            self.conn.commit()

        except DatabaseError as err:
            self.conn.rollback()
            raise CrabError('database error : ' + str(err))

        finally:
            c.close()

    def get_raw_crontab(self, host, user):
        if self.outputstore is not None and hasattr(self.outputstore,
                                                    'get_raw_crontab'):
            return self.outputstore.get_raw_crontab(host, user)

        entry = self._query_to_dict('SELECT crontab FROM rawcrontab ' +
                                    'WHERE host = ? AND user = ?',
                                    [host, user])

        if entry is None:
            return None
        else:
            return entry['crontab'].split('\n')
