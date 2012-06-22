import datetime
import pytz
import re

from sqlite3 import DatabaseError

from crab import CrabError, CrabStatus
from crab.util.string import remove_quotes, quote_multiword, split_quoted_word

class CrabDB:
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

    def get_jobs(self):
        """Fetches a list of all of the cron jobs stored in the database."""

        return self._query_to_dict_list(
                'SELECT id, host, user, jobid, command, installed ' +
                'FROM job WHERE deleted IS NULL ' +
                'ORDER BY host ASC, user ASC, installed ASC', [])

    def get_crontab(self, host, user):
        """Reads the job entries for a particular host and user and builds
        a crontab style representation.

        The output consists of job lines, which are commented out if
        their schedule is not in the database.  Timezone lines are inserted
        where the timezone changes between jobs.  If job identifiers
        are present, CRABID will be set on the corresponding job lines."""

        # TODO: split the non-database specific part into another module.

        c = self.conn.cursor()
        crontab = []
        timezone = None

        try:
            c.execute('SELECT time, command, jobid, timezone ' +
                      'FROM job WHERE host=? AND user=? AND deleted IS NULL ' +
                      'ORDER BY installed ASC',
                      [host, user]);
            while True:
                row = c.fetchone()
                if row is None:
                    break
                (time, command, jobid, dbtz) = row

                if time is None:
                    time = '### CRAB: UNKNOWN SCHEDULE ###'

                if dbtz is not None and dbtz != timezone:
                    timezone = dbtz
                    crontab.append('CRON_TZ=' + quote_multiword(timezone))

                elif dbtz is None and timezone is not None:
                    crontab.append('### CRAB: UNKNOWN TIMEZONE ###')
                    timezone = None

                if jobid is not None:
                    command = 'CRABID=' + quote_multiword(jobid) + ' ' + command

                crontab.append(time + ' ' + command)

        except DatabaseError as err:
            raise CrabError('database error : ' + str(err))

        finally:
            c.close()

        return crontab

    def save_crontab(self, host, user, crontab, timezone=None):
        """Reads a set of crontab lines and uses them to update the job
        database.

        It looks for the CRABID and CRON_TZ variables, but otherwise
        ignores everything except command lines.  It also checks for commands
        starting with a CRABID= definition, but otherwise inserts them
        into the database as is."""

        # TODO: split the non-database specific part into another module.

        c = self.conn.cursor()
        jobid = None
        rowid = set()

        # These patterns do not deal with quoting or trailing spaces,
        # so these must be dealt with in the code below.
        blankline = re.compile('^\s*$')
        comment = re.compile('^\s*#')
        variable = re.compile('^\s*(\w+)\s*=\s*(.*)$')
        cronrule = re.compile('^\s*(@\w+|\S+\s+\S+\s+\S+\s+\S+\s+\S+)\s+(.*)$')

        try:
            # Fetch the current list of jobs on this crontab.

            c.execute('SELECT id FROM job WHERE host=? AND user=?',
                      [host, user])
            while True:
                row = c.fetchone()
                if row is None:
                    break
                rowid.add(row[0])


            # Iterate over the supplied cron jobs, removing each
            # job from the rowid set as we encounter it.

            for job in crontab:
                if (blankline.search(job) is not None or
                        comment.search(job) is not None):
                    continue

                m = variable.search(job)
                if m is not None:
                    (var, value) = m.groups()
                    if var == 'CRABID':
                        jobid = remove_quotes(value.rstrip())
                    if var == 'CRON_TZ':
                        timezone = remove_quotes(value.rstrip())
                    continue

                m = cronrule.search(job)
                if m is not None:
                    (time, command) = m.groups()

                    if command.startswith('CRABID='):
                        (jobid, command) = split_quoted_word(
                                               command[7:].rstrip())

                    command = command.rstrip()

                    id_ = self.check_job(c, host, user, jobid,
                                         command, time, timezone)

                    rowid.discard(id_)
                    jobid = None
                    continue

                print '*** Did not recognise line:', job


            # Set any jobs remaining in the rowid set to deleted
            # because we did not see them in the current crontab

            for id_ in rowid:
                c.execute('UPDATE job SET deleted=CURRENT_TIMESTAMP ' +
                          'WHERE id=?',
                          [id_]);

            self.conn.commit()

        except DatabaseError as err:
            raise CrabError('database error : ' + str(err))

        finally:
            c.close()

    def check_job(self, c, host, user, jobid, command,
                  time=None, timezone=None):
        """Ensure that a job exists in the database.

        Tries to find (and update if necessary) the corresponding job in
        the database.  If it is not found, the job is stored as a new
        entry.

        In either case, the job's ID number is returned.
        """

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

    def log_start(self, host, user, jobid, command):
        """Inserts a job start record into the database."""

        c = self.conn.cursor()

        try:
            id_ = self.check_job(c, host, user, jobid, command)

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

        The output will be passed to the write_job_output method,
        providing the DB cursor so that the output can be inserted
        in the same SQL commit."""

        c = self.conn.cursor()

        try:
            id_ = self.check_job(c, host, user, jobid, command)

            c.execute('INSERT INTO jobfinish (jobid, command, status) ' +
                      'VALUES (?, ?, ?)',
                      [id_, command, status])

            finishid = c.lastrowid

            self.write_job_output(finishid, host, user, id_,
                                  stdout, stderr, c)

            self.conn.commit()

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

    def get_job_events(self, id_, limit=100):
        """Fetches a combined list of events relating to the specified job.

        Return events, newest first (with finishes first for the same
        datetime).  This ordering allows us to apply the SQL limit on
        number of result rows to find the most recent events.  It gives
        the correct ordering for the job info page."""

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
                         stdout, stderr, cursor=None):
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

        if cursor is None:
            c = self.conn.cursor()
        else:
            c = cursor

        try:
            c.execute('INSERT INTO joboutput (finishid, stdout, stderr) ' +
                      'VALUES (?, ?, ?)',
                      [finishid, stdout, stderr])

            if cursor is None:
                self.conn.commit

        except DatabaseError as err:
            raise CrabError('database error : ' + str(err))

        finally:
            if cursor is None:
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
