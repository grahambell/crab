# Copyright (C) 2012-2013 Science and Technology Facilities Council.
# Copyright (C) 2015 East Asian Observatory.
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

from logging import getLogger

from crab import CrabError
from crab.notify import CrabNotify, CrabNotifyJob
from crab.service import CrabMinutely
from crab.util.schedule import CrabSchedule

logger = getLogger(__name__)


class CrabNotifyService(CrabMinutely):
    """Service to send notifications as required.

    Currently only a single daily schedule is implemented."""

    def __init__(self, config, store, notify):
        """Constructor method.

        Stores CrabNotify object and daily CrabSchedule object."""

        CrabMinutely.__init__(self)

        self.store = store
        self.notify = notify
        self.schedule = CrabSchedule(config['daily'],
                                     config['timezone'])
        self.config = {}
        self.sched = {}

    def run_minutely(self, datetime_):
        """Issues notifications if any are scheduled for the given minute."""

        current = []
        match_daily = self.schedule.match(datetime_)

        if match_daily:
            daily_start = self.schedule.previous_datetime(datetime_)
        else:
            daily_start = None

        try:
            notifications = self.store.get_notifications()

        except CrabError as err:
            logger.exception('Error fetching notifications')
            return

        for notification in notifications:
            n_id = notification['notifyid']

            if (n_id in self.config and n_id in self.sched and
                    notification['time'] == self.config[n_id]['time'] and
                    notification['timezone'] == self.config[n_id]['timezone']):
                schedule = self.sched[n_id]
            else:
                self.config[n_id] = notification
                if notification['time'] is not None:
                    try:
                        schedule = CrabSchedule(notification['time'],
                                                notification['timezone'])
                    except CrabError as err:
                        schedule = None
                        logger.exception(
                            'Warning: could not read notification schedule')
                else:
                    schedule = None

                self.sched[n_id] = schedule

            if schedule is None:
                if match_daily:
                    current.append(CrabNotifyJob(
                        notification, daily_start, datetime_))
            else:
                if schedule.match(datetime_):
                    current.append(CrabNotifyJob(
                        notification, schedule.previous_datetime(datetime_),
                        datetime_))

        if current:
            self.notify(current)
