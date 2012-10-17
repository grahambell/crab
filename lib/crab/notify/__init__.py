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

from collections import namedtuple

from crab.report import CrabReportGenerator, CrabReportJob
from crab.notify.email import CrabNotifyEmail

CrabNotifyJob = namedtuple('CrabNotifyJob', ['n', 'start', 'end'])

class CrabNotify:
    """Class for sending notification messages."""

    def __init__(self, config, store):
        self.store = store

        self.send_email = CrabNotifyEmail(config)

    def __call__(self, notifications):
        "Sends notification messages."""

        report = CrabReportGenerator(self.store)

        for (jobs, keys) in self._group_notifications(notifications):
            output = report(jobs)
            if output is not None:
                email = []

                for key in keys:
                    (method, address) = key[0:2]

                    if method == 'email':
                        # In the case of email, we can build a list of
                        # addresses and CC a single message to all of them.
                        email.append(address)
                    else:
                        print('Unknown notification method: ', method)

                if email:
                    self.send_email(output, email)

    def _group_notifications(self, notifications):
        """Constructs a list of notifications to be sent.

        Each item in the list consists of a tuple containing a tuple
        of CrabReportJob tuples and a set of (method, address) pairs.
        This allows each distinct report to be generated once, 
        and then sent to a number of recipients."""

        # First build a list of jobs to report on for each destination:
        notification = {}

        for entry in notifications:
            key = (entry.n['method'], entry.n['address'],
                   entry.n['skip_ok'], entry.n['skip_warning'],
                   entry.n['skip_error'], entry.n['include_output'])

            id_ = entry.n['id']
            report_job = CrabReportJob(id_, entry.start, entry.end,
                                       entry.n['skip_ok'],
                                       entry.n['skip_warning'],
                                       entry.n['skip_error'],
                                       entry.n['include_output'])

            if key in notification:
                if id_ not in notification[key]:
                    notification[key][id_] = report_job
                else:
                    notification[key][id_] = report_job._replace(
                        start=min(notification[key][id_].start, entry.start),
                        end=max(notification[key][id_].end, entry.end))

            else:
                notification[key] = {id_: report_job}

        # Then attempt to merge entries with the same job list:
        merged = {}

        for (key, jobs) in notification.items():
            jobs = tuple(jobs.values())

            if jobs not in merged:
                merged[jobs] = set([key])
            else:
                merged[jobs].add(key)

        return merged.items()
