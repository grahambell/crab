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

import datetime
import os
import pytz

import sqlite3

from crab.store.db import CrabStoreDB

class CrabStoreSQLite(CrabStoreDB):
    def __init__(self, filename, outputstore=None):
        if filename != ':memory:' and not os.path.exists(filename):
            raise Exception('SQLite file does not exist')

        conn = sqlite3.connect(filename, check_same_thread=False)

        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON");
        c.close()

        CrabStoreDB.__init__(self, conn, outputstore)

    def parse_datetime(self, timestamp):
        """Parses the timestamp strings used by the database.

        The returned datetime object will include the correct timezone:
        for SQLite this is always UTC.

        An alternative thing to do would be to have _query_to_dict_list
        guess which fields are timestamps and automatically run this
        method on them."""

        return datetime.datetime.strptime(timestamp,
                        '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.UTC)

    def format_datetime(self, datetime_):
        """Converts a datetime into a timestamp string for the database.

        Includes conversion to UTC as used by SQLite."""

        return datetime_.astimezone(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S')
