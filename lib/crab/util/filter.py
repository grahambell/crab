import pytz

from crab import CrabEvent, CrabStatus

class CrabEventFilter:
    """Class implementing an event filtering action."""

    def __init__(self, store, timezone=None,
                 squash_start=False):
        """Construct filter object.

        Just stores the given information."""

        self.store = store
        self.set_timezone(timezone)

        self.squash_start = squash_start

        self.errors = None
        self.warnings = None

    def set_timezone(self, timezone):
        """Sets the timezone used by the filter."""

        if timezone is None:
            self.zoneinfo = None
        else:
            try:
                self.zoneinfo = pytz.timezone(timezone)
            except pytz.UnknownTimeZoneError:
                self.zoneinfo = None

    def __call__(self, events, skip_ok=False, skip_warning=False,
                 skip_error=False, skip_trivial=True, skip_start=False):
        """Performs filtering, and returns the altered event list."""

        output = []
        squash = set()
        self.errors = 0
        self.warnings = 0

        for (i, e) in enumerate(events):
            if i in squash:
                continue

            e = e.copy()

            if e['type'] == CrabEvent.START:
                if skip_start:
                    continue
            else:
                if (skip_trivial and CrabStatus.is_trivial(e['status'])
                or skip_ok and CrabStatus.is_ok(e['status'])
                or skip_warning and CrabStatus.is_warning(e['status'])
                or skip_error and CrabStatus.is_error(e['status'])):
                    continue

                if CrabStatus.is_error(e['status']):
                    self.errors += 1
                if CrabStatus.is_warning(e['status']):
                    self.warnings += 1

            if self.squash_start and e['type'] == CrabEvent.FINISH:
                start = _find_previous_start(events, i)
                if start is not None:
                    squash.add(start)
                    delta = (self.store.parse_datetime(e['datetime'])
                        - self.store.parse_datetime(events[start]['datetime']))
                    e['duration'] = str(delta)

            if self.zoneinfo is not None:
                e['datetime'] = self.in_timezone(e['datetime'])

            output.append(e)

        return output

    def in_timezone(self, datetime_):
        """Convert the datetime string as output by the database
        to a string in the specified timezone.

        Includes the zone code to indicate that the conversion has been
        performed."""

        if datetime_ is None or self.zoneinfo is None:
            return datetime_
        else:
            return self.store.parse_datetime(datetime_).astimezone(
                        self.zoneinfo).strftime('%Y-%m-%d %H:%M:%S %Z')


def _find_previous_start(events, i):
    """Looks in the event list, past position i, for the previous start.

    Skips over warnings."""

    i += 1

    while (i < len(events)):
        e = events[i]

        if e['type'] == CrabEvent.START:
            return i

        elif e['type'] != CrabEvent.WARN:
            return None

        i += 1

    return None
