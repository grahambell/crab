from __future__ import print_function

from collections import namedtuple

from crab.report import CrabReportGenerator, CrabReportJob
from crab.notify.email import CrabNotifyEmail

CrabNotifyJob = namedtuple('CrabNotifyJob', ['n', 'start', 'end'])

class CrabNotify:
    """Class for sending notification messages."""

    def __init__(self, config, store, base_url):
        self.store = store

        self.send_email = CrabNotifyEmail(config, base_url)

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
                   entry.n['skip_error'])

            id_ = entry.n['id']
            report_job = CrabReportJob(id_, entry.start, entry.end,
                                       entry.n['skip_ok'],
                                       entry.n['skip_warning'],
                                       entry.n['skip_error'])

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
