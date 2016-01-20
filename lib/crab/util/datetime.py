# Copyright (C) 2012 Science and Technology Facilities Council.
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

from __future__ import absolute_import

from datetime import datetime

import pytz


def parse_datetime(datetime_):
    """Parse a datetime string.

    The returned datetime object will include the UTC timezone."""

    return datetime.strptime(
        datetime_, '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.UTC)


def format_datetime(datetime_):
    """Converts a datetime into a string.

    Includes conversion to UTC."""

    return datetime_.astimezone(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S')
