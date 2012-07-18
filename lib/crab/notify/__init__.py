from crab.report import CrabReport
from crab.notify.mail import CrabNotifyEmail

class CrabNotify:
    """Class for sending notification messages."""

    def __init__(self, config, store, base_url):
        self.store = store

        self.send_email = CrabNotifyEmail(config, base_url)

    def __call__(self, start, end):
        "Sends notification messages."""

        report = CrabReport(self.store, start, end)

        for (destinations, jobs) in self._get_notifications():
            output = report(jobs)
            email = []

            for (method, address) in destinations:
                if method == 'email':
                    # In the case of email, we can build a list of
                    # addresses and CC a single message to all of them.
                    email.append(address)
                else:
                    print('Unknown notification method: ' + method)

            if email:
                self.send_email(report, output, email)

    def _get_notifications(self):
        """Constructs a list of notifications to be sent.

        Each item in the list consists of a tuple containing a set
        of (method, address) pairs and a set of job ID numbers.  This
        allows each distinct report to be generated once, and then
        sent to a number of recipients."""

        # First build a list of jobs to report on for each destination:
        notification = {}

        for entry in self.store.get_notifications():
            key = (entry['method'], entry['address'])

            if key in notification:
                notification[key].add(entry['jobid'])

            else:
                notification[key] = set([entry['jobid']])

        # Then attempt to merge entries with the same job list:
        merged = []

        while notification:
            (key, jobs) = notification.popitem()
            keys = set([key])

            for key in list(notification.keys()):
                if notification[key] == jobs:
                    keys.add(key)
                    del notification[key]

            merged.append((keys, jobs))

        return merged
