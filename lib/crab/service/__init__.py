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
import time
from threading import Thread

class CrabMinutely(Thread):
    """A thread which will call its run_minutely method for each minute
    which passes.

    The problem which this class seeks to address is that other methods of
    pausing a program (eg. threading.Timer, time.sleep) can't guarantee not
    to pause for longer than expected.  Therefore in the context of
    cron jobs, it might be possible to miss a cron scheduling point."""

    def __init__(self):
        """Constructor for minutely scheduled sevices.

        In order to allow subclasses to override the run method,
        we record the start time here."""

        Thread.__init__(self)
        self._previous = datetime.datetime.now(pytz.UTC)

    def run(self):
        """Thread run function.

        This calls _check_minute on regular intervals."""

        while True:
            time.sleep(5)
            self._check_minute()

    def _check_minute(self):
        """Check whether one or more minutes has passed, and if so,
        run the run_minutely method for each of them.

        If a subclass needs to implements its own run method, it should
        call this method regularly."""

        delta = datetime.timedelta(seconds=55)
        current = datetime.datetime.now(pytz.UTC)
        previous = self._previous

        while minute_before(previous, current):
            previous = self._previous + delta

            if not minute_equal(previous, self._previous):
                try:
                    self.run_minutely(previous)
                except Exception as e:
                    print("Error: run_minutely raised exception:", str(e))

            self._previous = previous

    def run_minutely(self, datetime_):
        """This is the method which will be called each minute.  It should
        be overridden by subclasses."""

        pass

def minute_equal(a, b):
    """Determine whether one time is in the same minute as another."""
    return a.timetuple()[0:5] == b.timetuple()[0:5]

def minute_before(a, b):
    """Determine whether one time is in a minute before another."""
    return a.timetuple()[0:5] < b.timetuple()[0:5]
