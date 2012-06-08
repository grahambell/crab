import re

from crab import CrabError

class CrabDB:
    def __init__(self, conn):
        self.conn = conn

    def get_crontab(self, host, user):
        c = self.conn.cursor()
        crontab = []

        try:
            c.execute("SELECT time, command FROM job WHERE host=? AND user=? "
                    + "AND deleted IS NULL",
                    [host, user]);
            while True:
                row = c.fetchone()
                if row == None:
                    break
                crontab.append(row[0] + " " + row[1])

        finally:
            c.close()

        return crontab

    def save_crontab(self, host, user, crontab, timezone = None):
        c = self.conn.cursor()
        jobid = None
        rowid = set()

        blankline = re.compile("^\s*$")
        comment   = re.compile("^\s*#")
        variable  = re.compile("^\s*(\w+)\s*=\s*(.*)$")
        cronrule  = re.compile("^\s*(\S+\s+\S+\s+\S+\s+\S+\s+\S+|@\w+)\s+(.*)$")

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
                        jobid = value
                    if var == "CRON_TZ":
                        timezone = value
                    continue

                m = cronrule.search(job)
                if m != None:
                    (time, command) = m.groups()

                    if command.startswith("CRABID="):
                        (stmt, command) = command.split(None, 1)
                        jobid = stmt[7:]

                    id = self.store_job(c, host, user, jobid,
                                        time, command, timezone)
                    print "Row id: ", id
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

    # Store the specified cron job and return the row id.
    def store_job(self, c, host, user, jobid, time, command, timezone):

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
                # a job ID.

                #c.execute("SELECT id, time, timezone, deleted "
                #    + "FROM job WHERE host=? AND user=? AND command=? "
                #    + "AND jobid IS NULL",
                #    [host, user, command])


                self._insert_job(c, host, user, jobid, time, command, timezone)

                return c.lastrowid

        # We don't know the jobid, so we must search by command.
        # In general we can't distinguish multiple copies of the same
        # command running at different times.
        # Such jobs should be given job IDs, or combined using
        # time ranges / steps if possible.

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

