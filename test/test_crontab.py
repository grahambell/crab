from unittest import TestCase

from crab.util.crontab import parse_crontab, write_crontab


class CrontabTestCase(TestCase):
    def test_read_write(self):
        """Test crontab read and write functions."""

        crontab_orig = [
            'CRON_TZ=Europe/Berlin',
            '* * * * * CRABID=job_one command_one',
            '0 15 * * * command_two',
            '0 0 1 4 * date +\%Y\%m\%d',
            '59 23 12 31 * echo%a\%b%c\%d',
            '1 2 3 4 * CRABID=cal CRABCLIENTHOSTNAME=b CRABUSERNAME=a cal',
        ]

        (jobs, warnings) = parse_crontab(crontab_orig)

        self.assertEqual(jobs, [
            {'crabid': 'job_one', 'command': 'command_one',
             'time': '* * * * *', 'timezone': 'Europe/Berlin',
             'rule': '* * * * * CRABID=job_one command_one',
             'input': None, 'vars': {}},
            {'crabid': None, 'command': 'command_two',
             'time': '0 15 * * *', 'timezone': 'Europe/Berlin',
             'rule': '0 15 * * * command_two',
             'input': None, 'vars': {}},
            {'crabid': None, 'command': 'date +%Y%m%d',
             'time': '0 0 1 4 *', 'timezone': 'Europe/Berlin',
             'rule': '0 0 1 4 * date +\%Y\%m\%d',
             'input': None, 'vars': {}},
            {'crabid': None, 'command': 'echo',
             'time': '59 23 12 31 *', 'timezone': 'Europe/Berlin',
             'rule': '59 23 12 31 * echo%a\%b%c\%d',
             'input': 'a%b\nc%d', 'vars': {}},
            {'crabid': 'cal', 'command': 'cal',
             'time': '1 2 3 4 *', 'timezone': 'Europe/Berlin',
             'rule': '1 2 3 4 * CRABID=cal CRABCLIENTHOSTNAME=b CRABUSERNAME=a cal',
             'input': None,
             'vars': {'CRABCLIENTHOSTNAME': 'b', 'CRABUSERNAME': 'a'}},
        ])

        self.assertEqual(warnings, [])

        crontab_written = write_crontab(jobs)

        self.assertEqual(crontab_written, crontab_orig)
