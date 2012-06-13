import pytz

from crontab import CronItem

from crab import CrabError

def slice_to_set(slice):
    result = set()

    # Extract parts from the CronSlice object.
    for part in slice.parts:

        # In simple cases CronSlice just stores in int.
        if isinstance(part, int):
            result.add(part)

        else:
            # CronRange doesn't convert seq to an int.
            try:
                seq = int(part.seq)
            except ValueError:
                raise CrabError('Step ' + part.seq + ' not an integer')

            # Need to add 1 for a python-style ending because
            # CronRange includes value_to in the series.
            for value in range(part.value_from, part.value_to + 1, seq):
                result.add(value)

    return result

class CrabSchedule():
    def __init__(self, specifier, timezone):
        try:
            # Need to provide crontab.CronItem with a dummy command.
            item = CronItem(specifier + ' COMMAND')

            if not item.is_valid():
                raise CrabError('Time spcifier is not valid: ' + specifier)

        except (ValueError, TypeError, AttributeError, NoneError) as err:
            raise CrabError('Failed to parse cron time specifier ' +
                            specifier + ' reason: ' + str(err))

        self.minute = slice_to_set(item.minute())
        self.hour = slice_to_set(item.hour())
        self.dom = slice_to_set(item.dom())
        self.month = slice_to_set(item.month())
        self.dow = slice_to_set(item.dow())
        self.timezone = None

        # Sunday might have been specified as 0 or 7 - change it to 7 only
        # to match the result from datetime.isoweekday().
        if 0 in self.dow:
            self.dow.add(7)
            self.dow.discard(0)

        if timezone is not None:
            try:
                # pytz returns the same object if called twice
                # with the same timezone, so we don't need to cache
                # the timezone objects by zone name.
                self.timezone = pytz.timezone(timezone)
            except pytz.UnknownTimeZoneError:
                print 'Warning: unknown time zone', jobinfo['timezone']


    def match(self, datetime):
        if self.timezone is not None:
            localtime = datetime.astimezone(self.timezone)
        else:
            # Currently assume UTC.
            localtime = datetime

        return ((localtime.minute in self.minute) and
                (localtime.hour in self.hour) and
                (localtime.day in self.dom) and
                (localtime.month in self.month) and
                (localtime.isoweekday() in self.dow))
