from datetime import datetime, timedelta
from pytz import timezone, UTC
from unittest import main, TestCase

from crab.util.schedule import CrabSchedule

class ScheduleTestCase(TestCase):
    def test_events(self):
        lon = timezone('Europe/London')
        van = timezone('America/Vancouver') # GMT-8
        syd = timezone('Australia/Sydney') # GMT+10

        qs = CrabSchedule('0 15 25 12 *', 'Europe/London')
        ar = CrabSchedule('0 11 11 11 *', 'America/Vancouver')
        gf = CrabSchedule('30 19 5 11 *', 'Europe/London')

        # Check scheduling correct for different timezones.

        self.assertTrue(qs.match(datetime(2012, 12, 25, 15, 0, tzinfo=lon)),
                        'Queen on time in London')
        self.assertTrue(qs.match(datetime(2011, 12, 25, 7, 0, tzinfo=van)),
                        'Queen on time in Vancouver last year')
        self.assertTrue(qs.match(datetime(2013, 12, 26, 1, 0, tzinfo=syd)),
                        'Queen on time in Sydney next year')
        self.assertTrue(qs.match(datetime(2020, 12, 25, 15, 0, tzinfo=UTC)),
                        'Queen on time in UTC')

        self.assertTrue(ar.match(datetime(2012, 11, 11, 11, 0, tzinfo=van)),
                        'Armistice correct time in Vancouver')
        self.assertTrue(ar.match(datetime(2012, 11, 11, 19, 0, tzinfo=lon)),
                        'Vancouver Armistice correct time in London')
        self.assertTrue(ar.match(datetime(2012, 11, 12, 5, 0, tzinfo=syd)),
                        'Vancouver Armistice correct time in Sydney')

        # Check scheduling tests all date parts.

        self.assertFalse(qs.match(datetime(2012, 12, 25, 14, 0, tzinfo=lon)),
                         'Queen not one hour early')
        self.assertFalse(qs.match(datetime(2012, 12, 25, 15, 5, tzinfo=lon)),
                         'Queen not five minutes late')
        self.assertFalse(qs.match(datetime(2012, 12, 26, 15, 0, tzinfo=lon)),
                         'Queen not on boxing day')
        self.assertFalse(qs.match(datetime(2012, 11, 25, 15, 0, tzinfo=lon)),
                         'Queen not on in November')

        # And an event which doesn't happen at minute zero.

        self.assertTrue(gf.match(datetime(2012, 11, 5, 19, 30, 0, tzinfo=lon)),
                        'Fireworks on time')
        self.assertTrue(gf.match(datetime(2012, 11, 5, 19, 30, 1, tzinfo=lon)),
                        'Fireworks might be one second late')
        self.assertFalse(gf.match(datetime(2012, 11, 5, 19, 35, tzinfo=lon)),
                         'Fireworks not 5 minutes late')

    def test_weekdays(self):
        sun = CrabSchedule('* * * * 0', 'UTC')
        mon = CrabSchedule('* * * * 1', 'UTC')
        tue = CrabSchedule('* * * * 2', 'UTC')
        wed = CrabSchedule('* * * * wed', 'UTC')
        thu = CrabSchedule('* * * * 4', 'UTC')
        fri = CrabSchedule('* * * * fri', 'UTC')
        sat = CrabSchedule('* * * * 6', 'UTC')
        sun7= CrabSchedule('* * * * 7', 'UTC')

        d = datetime(2012, 8, 10, 12, 0, tzinfo=UTC)
        day = timedelta(days=1)
        self.assertTrue(fri.match(d), 'Date is Friday')
        self.assertFalse(sat.match(d), 'Date is not Satuday')
        d += day
        self.assertTrue(sat.match(d), 'Date + 1 is Saturday')
        d += day
        self.assertTrue(sun.match(d), 'Date + 2 is Sunday')
        self.assertTrue(sun7.match(d), 'Date + 2 is Sunday (day 7)')
        d += day
        self.assertTrue(mon.match(d), 'Date + 3 is Monday')
        d += day
        self.assertTrue(tue.match(d), 'Date + 4 is Tuesday')
        d += day
        self.assertTrue(wed.match(d), 'Date + 5 is Wednesday')
        d += day
        self.assertTrue(thu.match(d), 'Date + 6 is Thursday')

    def test_range(self):
        fm = CrabSchedule('0-55/5 * * * *', 'UTC')

        self.assertTrue(fm.match(datetime(2012, 7, 4, 10, 0, tzinfo=UTC)),
                        'Minute 0 % 5')
        self.assertFalse(fm.match(datetime(2013, 8, 5, 14, 1, tzinfo=UTC)),
                         'Minute 1 not % 5')
        self.assertFalse(fm.match(datetime(2014, 9, 7, 18, 4, tzinfo=UTC)),
                         'Minute 4 not % 5')
        self.assertTrue(fm.match(datetime(2015, 1, 9, 20, 10, tzinfo=UTC)),
                        'Minute 10 % 5')
        self.assertFalse(fm.match(datetime(2010, 2, 1, 11, 42, tzinfo=UTC)),
                         'Minute 42 not % 5')
        self.assertTrue(fm.match(datetime(2011, 3, 2, 13, 45, tzinfo=UTC)),
                        'Minute 45 % 5')
        self.assertTrue(fm.match(datetime(2012, 4, 3, 16, 55, tzinfo=UTC)),
                        'Minute 55 % 5')
        self.assertFalse(fm.match(datetime(2012, 5, 4, 19, 59, tzinfo=UTC)),
                         'Minute 59 not % 5')

        wd = CrabSchedule('0 0 * * 1-5', 'UTC')
        self.assertTrue(wd.match(datetime(2012, 5, 7, 0, 0, tzinfo=UTC)),
                        'May 7th 2012 a weekday')
        self.assertTrue(wd.match(datetime(2012, 5, 8, 0, 0, tzinfo=UTC)),
                        'May 8th 2012 a weekday')
        self.assertTrue(wd.match(datetime(2012, 5, 9, 0, 0, tzinfo=UTC)),
                        'May 9th 2012 a weekday')
        self.assertTrue(wd.match(datetime(2012, 5, 10, 0, 0, tzinfo=UTC)),
                        'May 10th 2012 a weekday')
        self.assertTrue(wd.match(datetime(2012, 5, 11, 0, 0, tzinfo=UTC)),
                        'May 11th 2012 a weekday')
        self.assertFalse(wd.match(datetime(2012, 5, 12, 0, 0, tzinfo=UTC)),
                         'May 12th 2012 not a weekday')
        self.assertFalse(wd.match(datetime(2012, 5, 13, 0, 0, tzinfo=UTC)),
                         'May 13th 2012 not a weekday')

    def test_list(self):
        hon = timezone('Pacific/Honolulu')
        br = CrabSchedule('0 10,15 * * *', 'Pacific/Honolulu')
        self.assertTrue(br.match(datetime(2012, 10, 15, 10, 0, tzinfo=hon)),
                        'Coffee break on time')
        self.assertTrue(br.match(datetime(2012, 10, 15, 15, 0, tzinfo=hon)),
                        'Tea break on time')
        self.assertFalse(br.match(datetime(2012, 10, 15, 11, 0, tzinfo=hon)),
                         'Coffee break not 1 hour late')
        self.assertFalse(br.match(datetime(2012, 10, 15, 16, 0, tzinfo=hon)),
                         'Tea break not 1 hour late')

    def test_aliases(self):
        ho = CrabSchedule('@hourly', 'UTC')
        da = CrabSchedule('@daily', 'UTC')
        wk = CrabSchedule('@weekly', 'UTC')

        self.assertTrue(ho.match(datetime(1998, 10, 30, 1, 0, tzinfo=UTC)),
                        'Hourly alias match')
        self.assertFalse(ho.match(datetime(1998, 10, 30, 1, 1, tzinfo=UTC)),
                         'Hourly alias non-match')
        self.assertTrue(da.match(datetime(1998, 10, 30, 0, 0, tzinfo=UTC)),
                        'Daily alias match')
        self.assertFalse(da.match(datetime(1998, 10, 30, 1, 0, tzinfo=UTC)),
                         'Daily alias non-match')
        self.assertTrue(wk.match(datetime(1998, 10, 25, 0, 0, tzinfo=UTC)),
                        'Weekly alias match')
        self.assertFalse(wk.match(datetime(1998, 10, 30, 0, 0, tzinfo=UTC)),
                         'Weekly alias non-match')

    def test_nextprev(self):
        hon = timezone('Pacific/Honolulu')
        ho = CrabSchedule('0 * * * *', 'UTC')
        fm = CrabSchedule('0-55/5 * * * *', 'UTC')
        lt = CrabSchedule('0 12 * * * *', 'Pacific/Honolulu')
        d = datetime(2020, 2, 1, 12, 30, tzinfo=UTC)
        dl = datetime(2020, 2, 1, 12, 30, tzinfo=hon)

        self.assertEqual(ho.next_datetime(d),
                         datetime(2020, 2, 1, 13, 0, tzinfo=UTC),
                         'Next hourly datetime correct')
        self.assertEqual(ho.previous_datetime(d),
                         datetime(2020, 2, 1, 12, 0, tzinfo=UTC),
                         'Previous hourly datetime correct')

        self.assertEqual(fm.next_datetime(d),
                         datetime(2020, 2, 1, 12, 35, tzinfo=UTC),
                         'Next five minute datetime correct')
        self.assertEqual(fm.previous_datetime(d),
                         datetime(2020, 2, 1, 12, 25, tzinfo=UTC),
                         'Previous five minute datetime correct')

        self.assertEqual(lt.next_datetime(d),
                         datetime(2020, 2, 1, 22, 0, tzinfo=UTC),
                         'Next lunchtime correct as UTC')
        self.assertEqual(lt.previous_datetime(d),
                         datetime(2020, 1, 31, 22, 0, tzinfo=UTC),
                         'Previous lunchtime correct as UTC')

        self.assertEqual(lt.next_datetime(dl),
                         datetime(2020, 2, 2, 12, 0, tzinfo=hon),
                         'Next lunchtime correct')
        self.assertEqual(lt.previous_datetime(dl),
                         datetime(2020, 2, 1, 12, 0, tzinfo=hon),
                         'Previous lunchtime correct')

if __name__ == '__main__':
    main()
