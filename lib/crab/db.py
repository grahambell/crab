import re

from sqlite3 import DatabaseError

from crab import CrabError
from crab.util import remove_quotes, quote_multiword, split_quoted_word

class CrabDB:
    def __init__(self, conn, outputstore = None):
        self.conn = conn

        # An outputstore should implement write_output and read_output,
        # and if provided will be used instead of writing the stdout
        # and stderr from the cron jobs to the database.
        self.outputstore = outputstore


    def get_crontab(self, host, user):
        c = self.conn.cursor()
        crontab = []
        timezone = None

        try:
            c.execute("SELECT time, command, jobid, timezone "
                    + "FROM job WHERE host=? AND user=? AND deleted IS NULL "
                    + "ORDER BY installed ASC",
                    [host, user]);
            while True:
                row = c.fetchone()
                if row == None:
                    break
                (time, command, id, dbtz) = row

                if time == None:
                    time = "### CRAB: UNKNOWN SCHEDULE ###"

                if dbtz != None and dbtz != timezone:
                    timezone = dbtz
                    crontab.append("CRON_TZ=" + quote_multiword(timezone))

                elif dbtz == None and timezone != None:
                    crontab.append("### CRAB: UNKNOWN TIMEZONE ###")
                    timezone = None

                if id != None:
                    command = "CRABID=" + quote_multiword(id) + " " + command

                crontab.append(time + " " + command)

        finally:
            c.close()

        return crontab

    def save_crontab(self, host, user, crontab, timezone = None):
        c = self.conn.cursor()
        jobid = None
        rowid = set()

        # These patterns do not deal with quoting or trailing spaces,
        # so these must be dealt with in the code below.
        blankline = re.compile("^\s*$")
        comment   = re.compile("^\s*#")
        variable  = re.compile("^\s*(\w+)\s*=\s*(.*)$")
        cronrule  = re.compile("^\s*(@\w+|\S+\s+\S+\s+\S+\s+\S+\s+\S+)\s+(.*)$")

        try:
            # Fetch the current list of jobs on this crontab.

            c.execute("SELECT id FROM job WHERE host=? AND user=?",
                      [host, user])
            while True:
                row = c.fetchone()
                if row == None:
                    break
                rowid.add(row[0])


            # Iterate over the supplied cron jobs, removing each
            # job from the rowid set as we encounter it.

            for job in crontab:
                if blankline.search(job) != None or comment.search(job) != None:
                    continue

                m = variable.search(job)
                if m != None:
                    (var, value) = m.groups()
                    if var == "CRABID":
                        jobid = remove_quotes(value.rstrip())
                    if var == "CRON_TZ":
                        timezone = remove_quotes(value.rstrip())
                    continue

                m = cronrule.search(job)
                if m != None:
                    (time, command) = m.groups()

                    if command.startswith("CRABID="):
                        (jobid, command) = split_quoted_word(
                                               command[7:].rstrip())

                    command = command.rstrip()

                    id = self.check_job(c, host, user, jobid,
                                        command, time, timezone)

                    rowid.discard(id)
                    jobid = None
                    continue

                print "*** Did not recognise line:", job


            # Set any jobs remaining in the rowid set to deleted
            # because we did not see them in the current crontab

            for id in rowid:
                c.execute("UPDATE job SET deleted=CURRENT_TIMESTAMP WHERE id=?",
                          [id]);

            self.conn.commit()

        except DatabaseError as err:
            raise CrabError("database error : " + str(err))

        finally:
            c.close()

    # Find and update, or store the specified cron job and return the row id.
    def check_job(self, c, host, user, jobid, command,
                  time = None, timezone = None):

        # We know the jobid, so use it to search

        if jobid != None:
            c.execute("SELECT id, command, time, timezone, deleted "
                    + "FROM job WHERE host=? AND user=? AND jobid=?",
                    [host, user, jobid])
            row = c.fetchone()

            if row != None:
                (id, dbcommand, dbtime, dbtz, deleted) = row

                if (deleted == None
                        and command == dbcommand
                        and (time == None or time == dbtime)
                        and (timezone == None or timezone == dbtz)):
                    pass

                else:
                    if time == None:
                        time = dbtime
                    if timezone == None:
                        timezone = dbtz

                    c.execute("UPDATE job SET command=?, time=?, timezone=?, "
                            + "installed=CURRENT_TIMESTAMP, deleted=NULL "
                            + "WHERE id=?",
                            [command, time, timezone, id])

                return id

            else:
                # Need to check if the job already existed without
                # a job ID, in which case we update it to add the job ID.

                c.execute("SELECT id, time, timezone, deleted "
                    + "FROM job WHERE host=? AND user=? AND command=? "
                    + "AND jobid IS NULL",
                    [host, user, command])

                row = c.fetchone()

                if row != None:
                    (id, dbtime, dbtz, deleted) = row

                    if time == None:
                        time = dbtime
                    if timezone == None:
                        timezone = dbtz

                    c.execute("UPDATE job SET time=?, timezone=?, "
                            + "jobid=?, "
                            + "installed=CURRENT_TIMESTAMP, deleted=NULL "
                            + "WHERE id=?",
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
            c.execute("SELECT id, time, timezone, deleted "
                 + "FROM job WHERE host=? AND user=? AND command=?",
                 [host, user, command])

            row = c.fetchone()

            if row != None:
                (id, dbtime, dbtz, deleted) = row

                if (deleted == None
                        and (time == None or time == dbtime)
                        and (timezone == None or timezone == dbtz)):
                    pass

                else:
                    if time == None:
                        time = dbtime
                    if timezone == None:
                        timezone = dbtz

                    c.execute("UPDATE job SET time=?, timezone=?, "
                            + "installed=CURRENT_TIMESTAMP, deleted=NULL "
                            + "WHERE id=?",
                            [time, timezone, id])

                return id

            else:
                self._insert_job(c, host, user, jobid, time, command, timezone)

                return c.lastrowid

    def _insert_job(self, c, host, user, jobid, time, command, timezone):
        c.execute("INSERT INTO job (host, user, jobid, "
                        + "time, command, timezone)"
                        + "VALUES (?, ?, ?, ?, ?, ?)",
                        [host, user, jobid, time, command, timezone])


#    def _last_id(self, c):
#        c.execute("SELECT LAST_INSERT_ROWID()")
#        row = c.fetchone()
#
#        if row == None:
#            raise CrabError("could not fetch row id")
#
#        return row[0]

    def log_start(self, host, user, jobid, command):
        c = self.conn.cursor()

        try:
            id = self.check_job(c, host, user, jobid, command)

            c.execute("INSERT INTO jobstart (jobid, command) VALUES (?, ?)",
                      [id, command])
            self.conn.commit()

        except DatabaseError as err:
            raise CrabError("database error : " + str(err))

        finally:
            c.close()

    def log_finish(self, host, user, jobid, command, status,
                   stdout = None, stderr = None):

        c = self.conn.cursor()

        try:
            id = self.check_job(c, host, user, jobid, command)

            c.execute("INSERT INTO jobfinish (jobid, command, status) "
                    + "VALUES (?, ?, ?)",
                    [id, command, status])

            finishid = c.lastrowid

            if self.outputstore != None:
                self.outputstore.write_output(host, user, jobid, command,
                                              finishid, stdout, stderr)
            else:
                c.execute("INSERT INTO joboutput (finishid, stdout, stderr) "
                        + "VALUES (?, ?, ?)",
                        [finishid, stdout, stderr])

            self.conn.commit()

        except DatabaseError as err:
            raise CrabError("database error : " + str(err))

        finally:
            c.close()

