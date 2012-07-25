import datetime

from crab.notify import CrabNotify
from crab.service import CrabMinutely
from crab.util.schedule import CrabSchedule

class CrabNotifyService(CrabMinutely):
    """Service to send notifications as required.

    Currently only a single daily schedule is implemented."""

    def __init__(self, config, store, base_url):
        """Constructor method.

        Prepares CrabNotify object and daily CrabSchedule object."""

        CrabMinutely.__init__(self)

        self.notify = CrabNotify(config, store, base_url)
        self.schedule = CrabSchedule(config['notify']['daily'],
                                     config['notify']['timezone'])

    def run_minutely(self, datetime_):
        """Issues notifications if any are scheduled for the given minute."""

        end = datetime_.replace(second=0, microsecond=0)

        if self.schedule.match(datetime_):
            self.notify(end - datetime.timedelta(days=1), end)
