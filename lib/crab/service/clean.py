# Copyright (C) 2016 East Asian Observatory.
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

from datetime import timedelta

from crab import CrabError
from crab.service import CrabMinutely
from crab.util.schedule import CrabSchedule


class CrabCleanService(CrabMinutely):
    """Service to clean the store by removing old events."""

    def __init__(self, config, store):
        """Constructor method.

        Stores the store object and a CrabSchedule object."""

        CrabMinutely.__init__(self)

        self.store = store
        self.schedule = CrabSchedule(config['schedule'], config['timezone'])
        self.keep_days = config['keep_days']

    def run_minutely(self, datetime_):
        """Performs cleaning if scheduled for the given minute."""

        if self.schedule.match(datetime_):
            self.store.delete_old_events(
                datetime_=(datetime_ - timedelta(days=self.keep_days)))
