import pytz
import time
from threading import Event, Thread

from crab import CrabError, CrabEvent, CrabStatus

HISTORY_COUNT = 10

class CrabMonitor(Thread):
    def __init__(self, store):
        Thread.__init__(self)

        self.store = store
        self.sched = {}
        self.status = {}
        self.status_ready = Event()
        self.max_startid = 0
        self.max_warnid = 0
        self.max_finishid = 0

    def run(self):
        jobs = self.store.get_jobs()

        for job in jobs:
            jobid = job['id']
            self._initialize_job(jobid)

            # Allow a margin of events over HISTORY_COUNT to allow
            # for start events and warnings.
            events = self.store.get_job_events(jobid, 4 * HISTORY_COUNT)

            # Events are returned newest-first but we need to work
            # through them in order.
            for event in reversed(events):
                self._process_event(jobid, event)

            self._compute_reliability(jobid)

        self.status_ready.set()

        while True:
            time.sleep(10)

            # TODO: monitor needs to check for new jobs occasionally.
            # For now it can notice them if it sees an associated event.

            events = self.store.get_events_since(self.max_startid,
                                self.max_warnid, self.max_finishid)
            for event in events:
                jobid = event['jobid']

                if jobid not in self.status:
                    self._initialize_job(jobid)

                self._process_event(jobid, event)
                self._compute_reliability(jobid)

    def _initialize_job(self, jobid):
        jobinfo = self.store.get_job_info(jobid)

        # Write empty record in self.status

        self.status[jobid] = {'status': None, 'running': False, 'history': []}

        # Write record in self.sched

        if jobinfo is not None and jobinfo['time'] is not None:
            self.sched[jobid] = {'time': jobinfo['time'], 'timezone': None}
            if jobinfo['timezone'] is not None:
                try:
                    # pytz returns the same object if called twice
                    # with the same timezone, so we don't need to cache
                    # the timezone objects by zone name.
                    timezone = pytz.timezone(jobinfo['timezone'])
                    self.sched[jobid]['timezone'] = timezone
                except pytz.UnknownTimeZoneError:
                    print 'Warning: unknown time zone', jobinfo['timezone']

    def _process_event(self, jobid, event):
        if (event['type'] == CrabEvent.START and
                event['id'] > self.max_startid):
            self.max_startid = event['id']
        if (event['type'] == CrabEvent.WARN and
                event['id'] > self.max_warnid):
            self.max_warnid = event['id']
        if (event['type'] == CrabEvent.FINISH and
                event['id'] > self.max_finishid):
            self.max_finishid = event['id']

        # Needs to not apply less-important events.
        # Also needs to recompute reliability.
        if event['status'] is not None:
            status = event['status']
            prevstatus = self.status[jobid]['status']

            # If we need to decide the status precedence anywhere else,
            # then these rules should be made into functions in CrabStatus.
            # (Other than the Javascript which decides what color to use.)

            # LATE should only replace SUCCESS
            if status == CrabStatus.LATE:
                if prevstatus == CrabStatus.SUCCESS or prevstatus is None:
                    self.status[jobid]['status'] = status

            # MISSED should not replace TIMEOUT, FAIL or COULDNOTSTART
            elif status == CrabStatus.MISSED:
                if not (prevstatus == CrabStatus.FAIL or
                        prevstatus == CrabStatus.COULDNOTSTART or
                        prevstatus == CrabStatus.TIMEOUT):
                    self.status[jobid]['status'] = status

            # Other events can be set immediately
            else:
                self.status[jobid]['status'] = status

            # Don't include LATE in the history because it should happen
            # quite often and we don't want it to count as a failure.
            if status != CrabStatus.LATE:
                history = self.status[jobid]['history']
                if len(history) >= HISTORY_COUNT:
                    del history[0]
                history.append(status)

        if event['type'] == CrabEvent.START:
            self.status[jobid]['running'] = True

        if (event['type'] == CrabEvent.FINISH
                or event['status'] == CrabStatus.TIMEOUT):
            self.status[jobid]['running'] = False

    def _compute_reliability(self, jobid):
        history = self.status[jobid]['history']
        if len(history) == 0:
            self.status[jobid]['reliability'] = 0
        else:
            self.status[jobid]['reliability'] = int(100 *
                len(filter(lambda x: x == CrabStatus.SUCCESS, history)) /
                len(history))

    # For efficiency returns our job status dict.  Callers should not
    # modify it.
    def get_job_status(self):
        self.status_ready.wait()
        return self.status
