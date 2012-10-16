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

from __future__ import print_function

import re

from crab.util.string import remove_quotes, quote_multiword, split_quoted_word

class CrabStore:
    def get_jobs(self, host=None, user=None, include_deleted=False):
        """Fetches a list of all of the cron jobs,
        excluding deleted jobs by default.

        Optionally filters by host or username if these parameters are
        supplied."""

        with self.lock:
            return self._get_jobs(host, user, include_deleted)


    def get_crontab(self, host, user):
        """Fetches the job entries for a particular host and user and builds
        a crontab style representation.

        The output consists of job lines, which are commented out if
        their schedule is not in the database.  Timezone lines are inserted
        where the timezone changes between jobs.  If job identifiers
        are present, CRABID will be set on the corresponding job lines."""

        crontab = []
        timezone = None
        firstrow = True

        jobs = self.get_jobs(host, user)

        for job in jobs:
            # Check if job has a schedule attached.
            time = job['time']
            if time is None:
                time = '### CRAB: UNKNOWN SCHEDULE ###'

            # Track the timezone, so that we do not repeat CRON_TZ
            # assignments unnecessarily.
            if job['timezone'] is not None and job['timezone'] != timezone:
                timezone = job['timezone']
                crontab.append('CRON_TZ=' + quote_multiword(timezone))

            elif job['timezone'] is None and (timezone is not None or firstrow):
                crontab.append('### CRAB: UNKNOWN TIMEZONE ###')
                timezone = None

            # Include the crabid in the command if present.
            command = job['command']
            if job['crabid'] is not None:
                command = 'CRABID=' + quote_multiword(job['crabid']) + ' ' + command

            crontab.append(time + ' ' + command)

            firstrow = False

        return crontab

    def save_crontab(self, host, user, crontab, timezone=None):
        """Takes a list of crontab lines and uses them to update the job records.

        It looks for the CRABID and CRON_TZ variables, but otherwise
        ignores everything except command lines.  It also checks for commands
        starting with a CRABID= definition, but otherwise inserts them
        into the database as is.

        Returns a list of warning strings."""

        # Save the raw crontab.
        self.write_raw_crontab(host, user, crontab)

        # These patterns do not deal with quoting or trailing spaces,
        # so these must be dealt with in the code below.
        blankline = re.compile('^\s*$')
        comment = re.compile('^\s*#')
        variable = re.compile('^\s*(\w+)\s*=\s*(.*)$')
        cronrule = re.compile('^\s*(@\w+|\S+\s+\S+\s+\S+\s+\S+\s+\S+)\s+(.*)$')

        crabid = None
        idset = set()
        idsaved = set()
        warning = []
        for job in self.get_jobs(host, user):
            idset.add(job['id'])

        with self.lock:
            # Iterate over the supplied cron jobs, removing each
            # job from the idset set as we encounter it.

            for job in crontab:
                if (blankline.search(job) is not None or
                        comment.search(job) is not None):
                    continue

                m = variable.search(job)
                if m is not None:
                    (var, value) = m.groups()
                    if var == 'CRABID':
                        crabid = remove_quotes(value.rstrip())
                    if var == 'CRON_TZ':
                        timezone = remove_quotes(value.rstrip())
                    continue

                m = cronrule.search(job)
                if m is not None:
                    (time, command) = m.groups()

                    if command.startswith('CRABIGNORE='):
                        (ignore, command) = split_quoted_word(command[11:])
                        if ignore.lower() not in ['0', 'no', 'false', 'off']:
                            continue

                    if command.startswith('CRABID='):
                        (crabid, command) = split_quoted_word(command[7:])

                    command = command.rstrip()

                    id_ = self._check_job(host, user, crabid,
                                          command, time, timezone)

                    if id_ in idsaved:
                        warning.append('Indistinguishable duplicated job: ' +
                                       job)
                    else:
                        idsaved.add(id_)

                    idset.discard(id_)
                    crabid = None
                    continue

                warning.append('Did not recognise line: ' + job)


            # Set any jobs remaining in the id set to deleted
            # because we did not see them in the current crontab

            for id_ in idset:
                self._delete_job(id_);

            return warning

    def _check_job(self, host, user, crabid, command, time=None, timezone=None):
        """Ensure that a job exists in the store.

        Tries to find (and update if necessary) the corresponding job.
        If it is not found, the job is stored as a new entry.

        In either case, the job's ID number is returned.

        This is a private method because the lock must be acquired
        prior to calling it."""

        id_ = None

        # We know the crabid, so use it to search

        if crabid is not None:
            jobs = self._get_jobs(host, user, include_deleted=True,
                                  crabid=crabid)

            if jobs:
                job = jobs[0]
                id_ = job['id']

                if (job['deleted'] is None and
                        command == job['command'] and
                        (time is None or time == job['time']) and
                        (timezone is None or timezone == job['timezone'])):
                    pass

                else:
                    self._update_job(id_, None, command, time, timezone)

            else:
                # Need to check if the job already existed without
                # a job ID, in which case we update it to add the job ID.

                jobs = self._get_jobs(host, user, include_deleted=True,
                                      command=command, without_crabid=True)
                if jobs:
                    job = jobs[0]
                    id_ = job['id']

                    self._update_job(id_, crabid, None, time, timezone)

                else:
                    id_ = self._insert_job(host, user, crabid, time,
                                           command, timezone)

        # We don't know the crabid, so we must search by command.
        # In general we can't distinguish multiple copies of the same
        # command running at different times.
        # Such jobs should be given job IDs, or combined using
        # time ranges / steps.

        else:
            jobs = self._get_jobs(host, user, include_deleted=True,
                                  command=command)

            if jobs:
                job = jobs[0]
                id_ = job['id']

                if (job['deleted'] is None and
                        (time is None or time == job['time']) and
                        (timezone is None or timezone == job['timezone'])):
                    pass

                else:
                    self._update_job(id_, None, None, time, timezone)

            else:
                id_ = self._insert_job(host, user, crabid,
                                       time, command, timezone)

        if id_ is None:
            raise CrabError('store error: failed to identify job')

        return id_
