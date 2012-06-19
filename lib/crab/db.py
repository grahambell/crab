import re

from sqlite3 import DatabaseError

from crab import CrabError, CrabStatus
from crab.util import remove_quotes, quote_multiword, split_quoted_word

class CrabDB:
    def __init__(self, conn, outputstore=None):
        self.conn = conn

        # An outputstore should implement write_job_output and get_job_output,
        # and if provided will be used instead of writing the stdout
        # and stderr from the cron jobs to the database.  The outputstore
        # should only raise instances of CrabError.
        self.outputstore = outputstore

    def get_jobs(self):
        return self._query_to_dict_list(
                'SELECT id, host, user, jobid, command, installed ' +
                'FROM job WHERE deleted IS NULL ' +
                'ORDER BY host ASC, user ASC, installed ASC', [])

    def get_crontab(self, host, user):
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
                (time, command, id, dbtz) = row

                if time is None:
                    time = '### CRAB: UNKNOWN SCHEDULE ###'

                if dbtz is not None and dbtz != timezone:
                    timezone = dbtz
                    crontab.append('CRON_TZ=' + quote_multiword(timezone))

                elif dbtz is None and timezone is not None:
                    crontab.append('### CRAB: UNKNOWN TIMEZONE ###')
                    timezone = None

                if id is not None:
                    command = 'CRABID=' + quote_multiword(id) + ' ' + command

                crontab.append(time + ' ' + command)

        except DatabaseError as err:
            raise CrabError('database error : ' + str(err))

        finally:
            c.close()

        return crontab

    def save_crontab(self, host, user, crontab, timezone=None):
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

                    id = self.check_job(c, host, user, jobid,
                                        command, time, timezone)

                    rowid.discard(id)
                    jobid = None
                    continue

                print '*** Did not recognise line:', job


            # Set any jobs remaining in the rowid set to deleted
            # because we did not see them in the current crontab

            for id in rowid:
                c.execute('UPDATE job SET deleted=CURRENT_TIMESTAMP ' +
                          'WHERE id=?',
                          [id]);

            self.conn.commit()

        except DatabaseError as err:
            raise CrabError('database error : ' + str(err))

        finally:
            c.close()

    # Find and update, or store the specified cron job and return the row id.
    def check_job(self, c, host, user, jobid, command,
                  time=None, timezone=None):

        # We know the jobid, so use it to search

        if jobid is not None:
            c.execute('SELECT id, command, time, timezone, deleted ' +
                      'FROM job WHERE host=? AND user=? AND jobid=?',
                      [host, user, jobid])
            row = c.fetchone()

            if row is not None:
                (id, dbcommand, dbtime, dbtz, deleted) = row

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
                              [command, time, timezone, id])

                return id

            else:
                # Need to check if the job already existed without
                # a job ID, in which case we update it to add the job ID.

                c.execute('SELECT id, time, timezone, deleted ' +
                          'FROM job WHERE host=? AND user=? AND command=? ' +
                          'AND jobid IS NULL',
                          [host, user, command])

                row = c.fetchone()

                if row is not None:
                    (id, dbtime, dbtz, deleted) = row

                    if time is None:
                        time = dbtime
                    if timezone is None:
                        timezone = dbtz

                    c.execute('UPDATE job SET time=?, timezone=?, ' +
                                  'jobid=?, '
                                  'installed=CURRENT_TIMESTAMP, deleted=NULL '
                              'WHERE id=?',
                              [time, timezone, jobid, id])

                    return id

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
                (id, dbtime, dbtz, deleted) = row

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
                              [time, timezone, id])

                return id

            else:
                self._insert_job(c, host, user, jobid, time, command, timezone)

                return c.lastrowid

    def _insert_job(self, c, host, user, jobid, time, command, timezone):
        c.execute('INSERT INTO job (host, user, jobid, ' +
                      'time, command, timezone)' +
                      'VALUES (?, ?, ?, ?, ?, ?)',
                  [host, user, jobid, time, command, timezone])

    def log_start(self, host, user, jobid, command):
        c = self.conn.cursor()

        try:
            id = self.check_job(c, host, user, jobid, command)

            c.execute('INSERT INTO jobstart (jobid, command) VALUES (?, ?)',
                      [id, command])
            self.conn.commit()

        except DatabaseError as err:
            raise CrabError('database error : ' + str(err))

        finally:
            c.close()

    def log_finish(self, host, user, jobid, command, status,
                   stdout=None, stderr=None):

        c = self.conn.cursor()

        try:
            id = self.check_job(c, host, user, jobid, command)

            c.execute('INSERT INTO jobfinish (jobid, command, status) ' +
                      'VALUES (?, ?, ?)',
                      [id, command, status])

            finishid = c.lastrowid

            if self.outputstore is not None:
                self.outputstore.write_job_output(finishid, host, user, id,
                                                  stdout, stderr)
            else:
                c.execute('INSERT INTO joboutput (finishid, stdout, stderr) ' +
                          'VALUES (?, ?, ?)',
                          [finishid, stdout, stderr])

            self.conn.commit()

        except DatabaseError as err:
            raise CrabError('database error : ' + str(err))

        finally:
            c.close()

    def log_warning(self, id, status):

        c = self.conn.cursor()

        try:
            c.execute('INSERT INTO jobwarn (jobid, status) VALUES (?, ?)',
                      [id, status])

            self.conn.commit()

        except DatabaseError as err:
            raise CrabError('database error : ' + str(err))

        finally:
            c.close()

    def get_job_info(self, id_):
        return self._query_to_dict(
                'SELECT host, user, command, jobid, time, timezone, ' +
                    'installed, deleted ' +
                    'FROM job WHERE id = ?', [id_])

    def get_job_starts(self, id_, limit):
        return self._query_to_dict_list(
                'SELECT id, datetime, command ' +
                    'FROM jobstart WHERE jobid = ? ' +
                    'ORDER BY datetime DESC LIMIT ?',
                [id_, limit])

    def get_job_finishes(self, id_, limit=100):
        return self._query_to_dict_list(
                'SELECT id, datetime, command, status ' +
                    'FROM jobfinish WHERE jobid = ? ' +
                    'ORDER BY datetime DESC LIMIT ?',
                [id_, limit])

    # Return events, newest first (with finishes first for the same datetime).
    # This ordering allows us to apply the limit and also gives the correct
    # order for the job info page.
    def get_job_events(self, id_, limit=100):
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

    # Extract minimal summary information for events on all jobs
    # since the given IDs, oldest first.
    def get_events_since(self, startid, warnid, finishid):
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
        result = self._query_to_dict_list(sql, param)
        if len(result) == 1:
            return result[0]
        else:
            return None

    def _query_to_dict_list(self, sql, param=[]):
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

    def get_job_output(self, finishid, host, user, id_):
        if self.outputstore is not None:
            return self.outputstore.get_job_output(finishid, host, user, id_)
        else:
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

