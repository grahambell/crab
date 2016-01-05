from unittest import TestCase

from crab.store.sqlite import CrabStoreSQLite


class CrabDBTestCase(TestCase):
    def setUp(self):
        with open('doc/schema.sql') as file:
            schema = file.read()

        self.store = CrabStoreSQLite(':memory:')
        self.store.lock.conn.executescript(schema)

    def tearDown(self):
        self.store.lock.conn.close()
