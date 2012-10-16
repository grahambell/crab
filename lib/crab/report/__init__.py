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

from collections import namedtuple

from crab import CrabError, CrabStatus, CrabEvent
from crab.util.filter import CrabEventFilter

CrabReportJob = namedtuple('CrabReportJob', ['id_', 'start', 'end',
                           'skip_ok', 'skip_warning', 'skip_error',
                           'include_output'])

CrabReport = namedtuple('CrabReport', ['num', 'error', 'warning', 'ok',
                                       'info', 'events', 'stdout', 'stderr'])

class CrabReportGenerator:
    """Class for generating reports on the operation of cron jobs.

    This class maintains a cache of job information and events
    to allow it to handle multiple report requests in an efficient
    manner.  This depends on a single configuration, so methods
    for adjusting the filtering are not provided."""

    def __init__(self, store, **kwargs):
        """Constructor for report object."""

        self.store = store

        self.filter = CrabEventFilter(store, **kwargs)
        self.cache_info = {}
        self.cache_event = {}
        self.cache_error = {}
        self.cache_warning = {}
        self.cache_stdout = {}
        self.cache_stderr = {}

    def __call__(self, jobs):
        """Function call method, to process a list of jobs.

        Takes a list of jobs, which is a list of CrabReportJob
        tuples.

        Returns a CrabReport object including the number of jobs to be
        included in the report and sets of jobs in each state,
        or None if there are no entries to show."""

        checked = set()
        error = set()
        warning = set()
        ok = set()
        num = 0
        report_info = {}
        report_events = {}
        report_stdout = {}
        report_stderr = {}

        for job in jobs:
            if job in checked:
                continue
            else:
                checked.add(job)

            (id_, start, end, skip_ok, skip_warning, skip_error,
                include_output) = job

            if id_ in self.cache_info:
                info = self.cache_info[id_]
            else:
                info = self.store.get_job_info(id_)
                if info is None:
                    continue

                if info['crabid'] is None:
                    info['title'] = info['command']
                else:
                    info['title'] = info['crabid']

                self.cache_info[id_] = info

            if job in self.cache_event:
                events = self.cache_event[job]
                num_errors = self.cache_error[job]
                num_warnings = self.cache_warning[job]
            else:
                self.filter.set_timezone(info['timezone'])
                events = self.cache_event[job] = self.filter(
                             self.store.get_job_events(id_, limit=None,
                                                       start=start, end=end),
                             skip_ok=skip_ok, skip_warning=skip_warning,
                             skip_error=skip_error, skip_start=True)
                num_errors = self.cache_error[job] = self.filter.errors
                num_warnings = self.cache_warning[job] = self.filter.warnings

            if events:
                num += 1

                if num_errors:
                    error.add(id_)
                elif num_warnings:
                    warning.add(id_)
                else:
                    ok.add(id_)

                report_info[id_] = info
                report_events[id_] = events

                if include_output:
                    for event in events:
                        if event['type'] == CrabEvent.FINISH:
                            finishid = event['eventid']
                            if finishid in self.cache_stdout:
                                report_stdout[finishid] = \
                                    self.cache_stdout[finishid]
                                report_stderr[finishid] = \
                                    self.cache_stderr[finishid]
                            else:
                                output = self.store.get_job_output(finishid,
                                         info['host'], info['user'], id_,
                                         info['crabid'])

                                if output is None:
                                    stdout = stderr = None
                                else:
                                    (stdout, stderr) = output

                                report_stdout[finishid] = \
                                    self.cache_stdout[finishid] = stdout
                                report_stderr[finishid] = \
                                    self.cache_stderr[finishid] = stderr

        if num:
            return CrabReport(num, error, warning, ok,
                              report_info, report_events,
                              report_stdout, report_stderr)
        else:
            return None
