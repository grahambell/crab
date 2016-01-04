from unittest import main, TestCase

from crab.server.io import _filter_dict, _notify_key


class ServerIOTestCase(TestCase):
    def test_filter_dict(self):
        d = {'a': 100, 'b': 200, 'c': 0, 'd': 1}
        keys = ['a', '*c', '*d']

        result = _filter_dict(None, keys)
        self.assertIsNone(result)

        result = _filter_dict(d, keys)
        self.assertIsInstance(result, dict)
        self.assertEqual(set(result.keys()), set(('a', 'c', 'd')))
        self.assertEqual(result['a'], 100)
        self.assertIs(result['c'], False)
        self.assertIs(result['d'], True)

    def test_notify_key(self):
        notification = {
            'host': 'localhost',
            'user': 'user',
            'method': 'email',
            'address': 'user@localhost',
            'time': '* * * * *',
            'timezone': 'Pacific/Honolulu',
        }

        result = _notify_key(notification)
        self.assertIsInstance(result, tuple)
        self.assertEqual(result, ('email', 'user@localhost',
                                  '* * * * *', 'Pacific/Honolulu'))

        result = _notify_key(notification, match=True)
        self.assertIsInstance(result, tuple)
        self.assertEqual(result, ('localhost', 'user',
                                  'email', 'user@localhost',
                                  '* * * * *', 'Pacific/Honolulu'))
