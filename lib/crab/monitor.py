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
            jobinfo = self.store.get_job_info(jobid)

            info = {"status": None, "running": False}

            if jobinfo is not None and jobinfo["time"] is not None:
                self.sched[jobid] = {"time": jobinfo["time"], "timezone": None}
                if jobinfo["timezone"] is not None:
                    try:
                        # pytz returns the same object if called twice
                        # with the same timezone, so we don't need to cache
                        # the timezone objects by zone name.
                        timezone = pytz.timezone(jobinfo["timezone"])
                        self.sched[jobid]["timezone"] = timezone
                    except pytz.UnknownTimeZoneError:
                        print "Warning: unknown time zone", jobinfo["timezone"]

            # Allow a margin of events over HISTORY_COUNT to allow
            # for start events and warnings.
            events = self.store.get_job_events(jobid, 4 * HISTORY_COUNT)
            history = []

            for event in events:
                if (event["type"] == CrabEvent.START
                        and event["id"] > self.max_startid):
                    self.max_startid = event["id"]
                if (event["type"] == CrabEvent.WARN
                        and event["id"] > self.max_warnid):
                    self.max_warnid = event["id"]
                if (event["type"] == CrabEvent.FINISH
                        and event["id"] > self.max_finishid):
                    self.max_finishid = event["id"]

                # Don't insert things like LATE into history.
                if event["status"] is not None:
                    if info["status"] is None:
                        info["status"] = event['status']
                    if (len(history) < HISTORY_COUNT
                            and event['status'] != CrabStatus.LATE):
                        history.append(event['status'])

            info["reliability"] = self._reliability(history)
            info["history"] = history

            self.status[jobid] = info

        self.status_ready.set()

        while True:
            time.sleep(10)
            print "*** hello from CrabMonitor ***"
            events = self.store.get_events_since(self.max_startid,
                                                 self.max_warnid,
                                                 self.max_finishid)
            print repr(events)

            for event in events:
                jobid = event["jobid"]

                if (event["type"] == CrabEvent.START
                        and event["id"] > self.max_startid):
                    self.max_startid = event["id"]
                if (event["type"] == CrabEvent.WARN
                        and event["id"] > self.max_warnid):
                    self.max_warnid = event["id"]
                if (event["type"] == CrabEvent.FINISH
                        and event["id"] > self.max_finishid):
                    self.max_finishid = event["id"]

                # Needs to not apply less-important events.
                # Also needs to recompute reliability.
                if event["status"] is not None:
                    self.status[jobid]["status"] = event["status"]

                if event["type"] == CrabEvent.START:
                    self.status[jobid]["running"] = True

                if (event["type"] == CrabEvent.FINISH
                        or event["status"] == CrabStatus.TIMEOUT):
                    self.status[jobid]["running"] = False


    def _reliability(self, history):
        if len(history) == 0:
            return 0
        else:
            return int(100 *
                len(filter(lambda x: x == CrabStatus.SUCCESS, history)) /
                len(history))

    # For efficiency returns our job status dict.  Callers should not
    # modify it.
    def get_job_status(self):
        self.status_ready.wait()
        return self.status
