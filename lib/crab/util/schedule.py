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

import datetime
import pytz

from crontab import CronTab

from crab import CrabError

class CrabSchedule(CronTab):
    """Class handling the schedule of a cron job."""

    def __init__(self, specifier, timezone):
        """Construct a CrabSchedule object from a cron time specifier
        and the associated timezone name.

        The timezone string, if provided, is converted into an object
        using the pytz module."""

        try:
            item = CronTab.__init__(self, specifier)

        except ValueError as err:
            raise CrabError('Failed to parse cron time specifier ' +
                            specifier + ' reason: ' + str(err))

        self.timezone = None

        if timezone is not None:
            try:
                # pytz returns the same object if called twice
                # with the same timezone, so we don't need to cache
                # the timezone objects by zone name.
                self.timezone = pytz.timezone(timezone)
            except pytz.UnknownTimeZoneError:
                print('Warning: unknown time zone', timezone)


    def match(self, datetime):
        """Determines whether the given datetime matches the scheduling
        rules stored in the class instance.

        The datetime is converted to the stored timezone, and then the
        components of the time are checked against the matchers
        in the CronTab superclass."""

        localtime = self._localtime(datetime)

        return (self.matchers.minute(localtime.minute, localtime) and
                self.matchers.hour(localtime.hour, localtime) and
                self.matchers.day(localtime.day, localtime) and
                self.matchers.month(localtime.month, localtime) and
                self.matchers.weekday(localtime.isoweekday() % 7, localtime))

    def next_datetime(self, datetime_):
        """return a datetime rather than number of
        seconds."""

        localtime = self._localtime(datetime_)
        return datetime_ + datetime.timedelta(
                               seconds=int(self.next(localtime)))

    def previous_datetime(self, datetime_):
        """return a datetime rather than number of
        seconds."""

        localtime = self._localtime(datetime_)
        return datetime_ + datetime.timedelta(
                               seconds=int(self.previous(localtime)))

    def _localtime(self, datetime):
        if self.timezone is not None:
            return datetime.astimezone(self.timezone)
        else:
            # Currently assume UTC.
            return datetime

