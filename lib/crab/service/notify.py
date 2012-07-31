import datetime

from crab.notify import CrabNotify, CrabNotifyJob
from crab.service import CrabMinutely
from crab.util.schedule import CrabSchedule

class CrabNotifyService(CrabMinutely):
    """Service to send notifications as required.

    Currently only a single daily schedule is implemented."""

    def __init__(self, config, store, base_url):
        """Constructor method.

        Prepares CrabNotify object and daily CrabSchedule object."""

        CrabMinutely.__init__(self)

        self.store = store
        self.notify = CrabNotify(config, store, base_url)
        self.schedule = CrabSchedule(config['notify']['daily'],
                                     config['notify']['timezone'])
        self.config = {}
        self.sched = {}

    def run_minutely(self, datetime_):
        """Issues notifications if any are scheduled for the given minute."""

        current = []
        end = datetime_.replace(second=0, microsecond=0)
        match_daily = self.schedule.match(datetime_)

        if match_daily:
            daily_start = self.schedule.previous_datetime(end)
        else:
            daily_start = None

        for notification in self.store.get_notifications():
            n_id = notification['notifyid']

            if (n_id in self.config and n_id in self.sched
                and notification['time'] == self.config[n_id]['time']
                and notification['timezone'] == self.config[n_id]['timezone']):
                    schedule = self.sched[n_id]
            else:
                self.config[n_id] = notification
                if notification['time'] is not None:
                    schedule = CrabSchedule(notification['time'],
                                            notification['timezone'])
                else:
                    schedule = None

                self.sched[n_id] = schedule

            if schedule is None:
                if match_daily:
                    current.append(CrabNotifyJob(
                        notification, daily_start, end))
            else:
                if schedule.match(datetime_):
                    current.append(CrabNotifyJob(
                        notification, schedule.previous_datetime(end), end))

        if current:
            self.notify(current)
