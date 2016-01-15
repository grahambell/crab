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

from __future__ import absolute_import

import re
import pytz

import mysql.connector
from mysql.connector.errors import Error as _MySQLError
from mysql.connector.cursor import MySQLCursor

from crab.store.db import CrabStoreDB, CrabDBLock


class CrabStoreMySQLCursor(MySQLCursor):
    """MySQL compatability cursor class."""

    def execute(self, query, params):
        """Execute an SQL query.

        This method prepares the query for use with MySQL and then
        calls the (superclass) MySQLCursor.execute method.

        This is for compatability with SQL statements which were
        written for SQLite."""

        # Replace placeholders.
        query = re.sub('\?', '%s', query)

        # Remove column type instructions.
        query = re.sub('AS "([a-z]+) \[timestamp\]"', '', query)

        return MySQLCursor.execute(self, query, params)


class CrabStoreMySQL(CrabStoreDB):
    """MySQL-based storage class."""

    def __init__(self, host, database, user, password, outputstore=None):
        """Connects to MySQL and initializes the storage object."""

        conn = mysql.connector.connect(
            host=host, database=database, user=user, password=password,
            time_zone='+00:00')

        CrabStoreDB.__init__(
            self,
            lock=CrabDBLock(
                conn, error_class=_MySQLError,
                cursor_args={'cursor_class': CrabStoreMySQLCursor},
                ping=True),
            outputstore=outputstore)
