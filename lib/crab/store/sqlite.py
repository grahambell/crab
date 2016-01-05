# Copyright (C) 2012 Science and Technology Facilities Council.
# Copyright (C) 2015-2016 East Asian Observatory.
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

from contextlib import closing
import os
import pytz

import sqlite3

from crab.store.db import CrabStoreDB, CrabDBLock


class CrabStoreSQLite(CrabStoreDB):
    def __init__(self, filename, outputstore=None):
        if filename != ':memory:' and not os.path.exists(filename):
            raise Exception('SQLite file does not exist')

        conn = sqlite3.connect(
            filename, check_same_thread=False,
            detect_types=sqlite3.PARSE_COLNAMES)

        with closing(conn.cursor()) as c:
            c.execute("PRAGMA foreign_keys = ON")

        CrabStoreDB.__init__(
            self,
            lock=CrabDBLock(conn, error_class=sqlite3.DatabaseError),
            outputstore=outputstore)
