# Copyright (C) 2012 Science and Technology Facilities Council.
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

import re

from crab.util.string import \
    quote_multiword, remove_quotes, split_crab_vars, true_string

# These patterns do not deal with quoting or trailing spaces,
# so these must be dealt with in the parse_crontab function.
blankline = re.compile('^\s*$')
comment = re.compile('^\s*#')
variable = re.compile('^\s*(\w+)\s*=\s*(.*)$')
cronrule = re.compile('^\s*(@\w+|\S+\s+\S+\s+\S+\s+\S+\s+\S+)\s+(.*)$')
plain_percent = re.compile('(?<!\\\\)%')


def parse_crontab(crontab, timezone=None):
    """
    Parses a list of crontab lines.

    Returns a pair comprising a list of cron jobs (as dictionaries)
    and a list of warning strings.
    """

    env = {}
    jobs = []
    warnings = []

    for job in crontab:
        if (blankline.search(job) is not None or
                comment.search(job) is not None):
            continue

        m = variable.search(job)
        if m is not None:
            (var, value) = m.groups()
            if var == 'CRON_TZ':
                timezone = remove_quotes(value.rstrip())
            elif var.startswith('CRAB'):
                env[var] = remove_quotes(value.rstrip())
            continue

        m = cronrule.search(job)
        if m is not None:
            (time, full_command) = m.groups()

            # Process percent signs in command (indicating command input
            # and line breaks).
            input_lines = plain_percent.split(full_command)
            command = input_lines.pop(0).rstrip().replace('\%', '%')

            if input_lines:
                input_ = '\n'.join(x.replace('\%', '%') for x in input_lines)
            else:
                input_ = None

            # Process embedded environment variables.
            (command, jobvars) = split_crab_vars(command)
            vars_ = env.copy()
            vars_.update(jobvars)

            # Skip this job if CRABIGNORE is set, otherwise add it
            # to the jobs list.
            if 'CRABIGNORE' in vars_:
                if true_string(vars_['CRABIGNORE']):
                    continue

            crabid = vars_.pop('CRABID', None)

            jobs.append({
                'crabid': crabid,
                'command': command,
                'time': time,
                'timezone': timezone,
                'input': input_,
                'vars': vars_,
                'rule': job,
            })

            continue

        warnings.append('Did not recognise line: ' + job)

    return (jobs, warnings)


def write_crontab(jobs):
    """
    Converts a series of cron jobs into a crontab style representation.

    The output consists of job lines, which are commented out if
    their schedule is not known.  Timezone lines are inserted
    where the timezone changes between jobs.  If job identifiers
    are present, CRABID will be set on the corresponding job lines.
    """

    crontab = []
    timezone = None
    firstrow = True

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

        elif (job['timezone'] is None and
                (timezone is not None or firstrow)):
            crontab.append('### CRAB: UNKNOWN TIMEZONE ###')
            timezone = None

        # Build the command string via a list of parts.
        command = []

        # Include the crabid in if present.
        if job['crabid'] is not None:
            command.append('CRABID=' + quote_multiword(job['crabid']))

        # Include additional variables, if "vars" is present in the job.
        vars_ = job.get('vars')
        if vars_ is not None:
            for var in sorted(vars_.keys()):
                command.append(var + '=' + quote_multiword(vars_[var]))

        command.append(job['command'])

        # Process percent signs in the command, and add input if present.
        command = ' '.join(command).replace('%', '\%')

        input_ = job.get('input')
        if input_ is not None:
            command += '%' + '%'.join(
                x.replace('%', '\%') for x in input_.splitlines())

        crontab.append(time + ' ' + command)

        firstrow = False

    return crontab
