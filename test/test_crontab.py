from unittest import TestCase

from crab.util.crontab import parse_crontab, write_crontab


class CrontabTestCase(TestCase):
    def test_read_write(self):
        """Test crontab read and write functions."""

        crontab_orig = [
            'CRON_TZ=Europe/Berlin',
            '* * * * * CRABID=job_one command_one',
            '0 15 * * * command_two',
        ]

        (jobs, warnings) = parse_crontab(crontab_orig)

        self.assertEqual(jobs, [
            {'crabid': 'job_one', 'command': 'command_one',
             'time': '* * * * *', 'timezone': 'Europe/Berlin'},
            {'crabid': None, 'command': 'command_two',
             'time': '0 15 * * *', 'timezone': 'Europe/Berlin'},
        ])

        self.assertEqual(warnings, [])

        crontab_written = write_crontab(jobs)

        self.assertEqual(crontab_written, crontab_orig)
