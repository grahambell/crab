from unittest import TestCase

from crab import CrabStatus, CrabEvent


class CrabTypeTestCase(TestCase):
    def test_status(self):
        self.assertEqual(CrabStatus.get_name(1), 'Failed')
        self.assertEqual(CrabStatus.get_name(-1), 'Late')
        self.assertEqual(CrabStatus.get_name(42), 'Status 42')
        self.assertEqual(CrabStatus.get_name(None), 'Undefined')

        self.assertTrue(CrabStatus.is_ok(CrabStatus.SUCCESS))
        self.assertTrue(CrabStatus.is_ok(CrabStatus.LATE))
        self.assertFalse(CrabStatus.is_ok(CrabStatus.WARNING))
        self.assertFalse(CrabStatus.is_ok(CrabStatus.FAIL))

        self.assertFalse(CrabStatus.is_error(CrabStatus.SUCCESS))
        self.assertFalse(CrabStatus.is_error(CrabStatus.LATE))
        self.assertFalse(CrabStatus.is_error(CrabStatus.WARNING))
        self.assertTrue(CrabStatus.is_error(CrabStatus.FAIL))

    def test_event(self):
        self.assertEqual(CrabEvent.get_name(1), 'Started')
        self.assertEqual(CrabEvent.get_name(42), 'Event 42')
