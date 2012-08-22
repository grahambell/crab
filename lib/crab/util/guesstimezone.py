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

import os
import pytz

# There really ought to be a better way of doing this!  You could read
# /etc/sysconfig/clock but that would only work on certain systems.  The
# following might work anywhere the timezone database is installed in the
# correct place.
#
# The Perl module DateTime::TimeZone::Local::Unix uses this method, among
# others.  TODO: implement some of the other methods.

def guess_timezone():
    """Function to try to determine the operating system's timezone setting.

    Currently this checks for a TZ environment variable.  Otherwise
    it reads /etc/localtime and tries to find the file in
    /usr/share/zoneinfo which matches.  It uses pytz to get a list of
    common timezones to try."""

    if 'TZ' in os.environ:
        return os.environ['TZ']

    try:
        f = open('/etc/localtime', 'rb')
        localtime = f.read()
        f.close()
    except:
        return None

    for zone in pytz.common_timezones:
        try:
            f = open('/usr/share/zoneinfo/' + zone, 'rb')
            timezone = f.read()
            f.close()

            if timezone == localtime:
                return zone

        except:
            pass

    return None
