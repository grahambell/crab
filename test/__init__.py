from unittest import TestCase
import sqlite3

from crab.store.db import CrabDB

class CrabDBTestCase(TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')

        with open('doc/schema.txt') as file:
            schema = file.read()

        self.conn.executescript(schema)

        c = self.conn.cursor()
        c.execute("PRAGMA foreign_keys = ON");
        c.close()

        self.store = CrabDB(self.conn)

    def tearDown(self):
        self.conn.close()
