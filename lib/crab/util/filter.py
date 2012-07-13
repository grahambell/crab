import pytz

from crab import CrabEvent, CrabStatus

class CrabEventFilter:
    """Class implementing an event filtering action."""

    def __init__(self, store, timezone=None,
                 skip_trivial=True, skip_start=False,
                 skip_ok=False, skip_warning=False,
                 squash_start=False):
        """Construct filter object.

        Just stores the given information."""

        self.store = store
        self.set_timezone(timezone)

        self.skip_trivial = skip_trivial
        self.skip_start = skip_start
        self.skip_ok = skip_ok
        self.skip_warning = skip_warning

        self.squash_start = squash_start

    def set_timezone(self, timezone):
        """Sets the timezone used by the filter."""

        if timezone is None:
            self.zoneinfo = None
        else:
            try:
                self.zoneinfo = pytz.timezone(timezone)
            except pytz.UnknownTimeZoneError:
                self.zoneinfo = None

    def __call__(self, events):
        """Performs filtering, and returns the altered event list."""

        output = []
        squash = set()

        for (i, e) in enumerate(events):
            if i in squash:
                continue

            if e['type'] == CrabEvent.START:
                if self.skip_start:
                    continue
            else:
                if (self.skip_trivial and CrabStatus.is_trivial(e['status'])
                or self.skip_ok and CrabStatus.is_ok(e['status'])
                or self.skip_warning and CrabStatus.is_warning(e['status'])):
                    continue

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
