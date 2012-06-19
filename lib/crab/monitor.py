import datetime
import pytz
import time
from random import Random
from threading import Condition, Event, Thread

from crab import CrabError, CrabEvent, CrabStatus
from crab.schedule import CrabSchedule

HISTORY_COUNT = 10

class JobDeleted(Exception):
    pass

class CrabMonitor(Thread):
    def __init__(self, store):
        Thread.__init__(self)

        self.store = store
        self.sched = {}
        self.status = {}
        self.status_ready = Event()
        self.config = {}
        self.last_start = {}
        self.timeout = {}
        self.miss_timeout = {}
        self.max_startid = 0
        self.max_warnid = 0
        self.max_finishid = 0
        self.last_time = None
        self.new_event = Condition()
        self.num_warning = 0
        self.num_error = 0
        self.random = Random()

    def run(self):
        jobs = self.store.get_jobs()

        for job in jobs:
            jobid = job['id']
            try:
                self._initialize_job(jobid)

                # Allow a margin of events over HISTORY_COUNT to allow
                # for start events and warnings.
                events = self.store.get_job_events(jobid, 4 * HISTORY_COUNT)

                # Events are returned newest-first but we need to work
                # through them in order.
                for event in reversed(events):
                    self._update_max_id_values(event)
                    self._process_event(jobid, event)

                self._compute_reliability(jobid)

            except JobDeleted:
                print 'Warning: job', jobid, 'has vanished'

        self.status_ready.set()

        while True:
            time.sleep(5)
            datetime_ = datetime.datetime.now(pytz.UTC)

            # TODO: monitor needs to check for new jobs occasionally.
            # For now it can notice them if it sees an associated event.

            events = self.store.get_events_since(self.max_startid,
                                self.max_warnid, self.max_finishid)
            for event in events:
                jobid = event['jobid']
                self._update_max_id_values(event)

                try:
                    if jobid not in self.status:
                        self._initialize_job(jobid)

                    self._process_event(jobid, event)
                    self._compute_reliability(jobid)

                # If the monitor is loaded when a job has just been
                # deleted, then it may have events more recent
                # than those of the events that still exist.
                except JobDeleted:
                    pass

            self.num_error = 0;
            self.num_warning = 0;
            for id in self.status:
                jobstatus = self.status[id]['status']
                if (jobstatus is None or CrabStatus.is_ok(jobstatus)):
                    pass
                elif (CrabStatus.is_warning(jobstatus)):
                    self.num_warning += 1;
                else:
                    self.num_error += 1;

            if events:
                with self.new_event:
                    self.new_event.notify_all()

            # Hour and minute should be sufficient to check
            # that the minute has changed.
            # TODO: check we didn't somehow miss a minute?
            time_stamp = datetime_.strftime('%H%M')

            if self.last_time is None or time_stamp != self.last_time:
                for id in self.sched:
                    if self.sched[id].match(datetime_):
                        if ((not self.last_start.has_key(id)) or
                                (self.last_start[id] + self.config[id]['graceperiod'] < datetime_)):
                            self._write_warning(id, CrabStatus.LATE)
                            self.miss_timeout[id] = (datetime_ +
                                    self.config[id]['graceperiod'])

                # Look for new or deleted jobs.
                currentjobs = set(self.status.keys())
                jobs = self.store.get_jobs()
                for job in jobs:
                    jobid = job['id']
                    if jobid in currentjobs:
                        currentjobs.discard(jobid)

                        # Compare installed timestamp is case we need to
                        # reload the schedule.  NOTE: assumes database
                        # datetimes compare in the correct order.
                        if job['installed'] > self.status[jobid]['installed']:
                            self._schedule_job(jobid)
                            self.status[jobid]['installed'] = job['installed']
                    else:
                        # No need to check event history: if there were any
                        # events, we would have added the job when they
                        # occurred (unless a job was just un-deleted or the
                        # an event happend during the schedule check.
                        try:
                            self._initialize_job(jobid)
                        except JobDeleted:
                            print 'Warning: job', jobid, 'has vanished'

                # Remove (presumably deleted) jobs.
                for jobid in currentjobs:
                    self._remove_job(jobid)

            self.last_time = time_stamp

            # Check status of timeouts - need to get a list of keys
            # so that we can delete from the dict while iterating.

            for id in self.miss_timeout.keys():
                if self.miss_timeout[id] < datetime_:
                    self._write_warning(id, CrabStatus.MISSED)
                    del self.miss_timeout[id]

            for id in self.timeout.keys():
                if self.timeout[id] < datetime_:
                    self._write_warning(id, CrabStatus.TIMEOUT)
                    del self.timeout[id]

    def _initialize_job(self, jobid):
        jobinfo = self.store.get_job_info(jobid)
        if jobinfo is None or jobinfo['deleted'] is not None:
            raise JobDeleted

        self.status[jobid] = {'status': None, 'running': False, 'history': [],
                              'installed': jobinfo['installed']}

        self._schedule_job(jobid, jobinfo)

        # TODO: read these from the jobsettings table
        self.config[jobid] = {'graceperiod': datetime.timedelta(minutes=2),
                              'timeout': datetime.timedelta(minutes=5)}

    def _schedule_job(self, jobid, jobinfo=None):
        if jobinfo is None:
            jobinfo = self.store.get_job_info(jobid)

        if jobinfo is not None and jobinfo['time'] is not None:
            try:
                self.sched[jobid] = CrabSchedule(jobinfo['time'],
                                                 jobinfo['timezone'])
            except CrabError as err:
                print 'Warning: could not add schedule: ' + str(err)

    def _remove_job(self, jobid):
        try:
            del self.status[jobid]
            if self.config.has_key(jobid):
                del self.config[jobid]
            if self.sched.has_key(jobid):
                del self.sched[jobid]
            if self.last_start.has_key(jobid):
                del self.last_start[jobid]
            if self.timeout.has_key(jobid):
                del self.timeout[jobid]
            if self.miss_timeout.has_key(jobid):
                del self.miss_timeout[jobid]
        except KeyError:
            print 'Warning: stopping monitoring job but it is not in monitor.'

    def _update_max_id_values(self, event):
        if (event['type'] == CrabEvent.START and
                event['id'] > self.max_startid):
            self.max_startid = event['id']
        if (event['type'] == CrabEvent.WARN and
                event['id'] > self.max_warnid):
            self.max_warnid = event['id']
        if (event['type'] == CrabEvent.FINISH and
                event['id'] > self.max_finishid):
            self.max_finishid = event['id']

    def _process_event(self, jobid, event):
        # Parse date from SQLite format, which is always UTC.
        datetime_ = datetime.datetime.strptime(event['datetime'],
                        '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.UTC);

        if event['status'] is not None:
            status = event['status']
            prevstatus = self.status[jobid]['status']

            # Avoid overwriting a status with a less important one.

            if CrabStatus.is_trivial(status):
                if prevstatus is None or CrabStatus.is_ok(prevstatus):
                    self.status[jobid]['status'] = status

            elif CrabStatus.is_warning(status):
                if prevstatus is None or not CrabStatus.is_error(prevstatus):
                    self.status[jobid]['status'] = status

            # Always set success / failure status (the remaining options).

            else:
                self.status[jobid]['status'] = status

            if not CrabStatus.is_trivial(status):
                history = self.status[jobid]['history']
                if len(history) >= HISTORY_COUNT:
                    del history[0]
                history.append(status)

        if event['type'] == CrabEvent.START:
            self.status[jobid]['running'] = True
            self.last_start[jobid] = datetime_
            self.timeout[jobid] = datetime_ + self.config[jobid]['timeout']
            if self.miss_timeout.has_key(jobid):
                del self.miss_timeout[jobid]

        if (event['type'] == CrabEvent.FINISH
                or event['status'] == CrabStatus.TIMEOUT):
            self.status[jobid]['running'] = False
            if self.timeout.has_key(jobid):
                del self.timeout[jobid]

    def _compute_reliability(self, jobid):
        history = self.status[jobid]['history']
        if len(history) == 0:
            self.status[jobid]['reliability'] = 0
        else:
            self.status[jobid]['reliability'] = int(100 *
                len(filter(lambda x: x == CrabStatus.SUCCESS, history)) /
                len(history))

    def _write_warning(self, id, status):
        try:
            self.store.log_warning(id, status)
        except CrabError as err:
            print 'Could not record warning : ' + str(err)

    # For efficiency returns our job status dict.  Callers should not
    # modify it.
    def get_job_status(self):
        self.status_ready.wait()
        return self.status

    # Function which waits for new result.  A random time up to 20s is added
    # to the timeout to stagger requests.
    def wait_for_event_since(self, startid, warnid, finishid, timeout=120):
        if (self.max_startid > startid or self.max_warnid > warnid or
                                          self.max_finishid > finishid):
            pass
        else:
            with self.new_event:
                self.new_event.wait(timeout + self.random.randint(0,20))

        return {'startid': self.max_startid, 'warnid': self.max_warnid,
                'finishid': self.max_finishid, 'status': self.status,
                'numwarning': self.num_warning, 'numerror': self.num_error}
