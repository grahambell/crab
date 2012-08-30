from random import sample
from threading import Thread
import sys

from . import CrabDBTestCase

DUPLICATES=200
ITERATIONS=10

class StoreThreadsTestCase(CrabDBTestCase):
    def test_thread(self):
        """Test for threading problems.

        Spawn a lot of threads each performing actions on the database.
        The intention is to cover all public methods of the store
        object.  If any of the methods are not thread-safe then
        this kind of test ought to stand a chance of detecting
        the issue."""

        threads = []

        for i in range(DUPLICATES):
            threads.append(CronTabTester(self.store))
            threads.append(CronJobTester(self.store))
            threads.append(CronLogTester(self.store))

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        for t in threads:
            self.assertEqual(t.exceptions, 0)


class RandomTester(Thread):
    def __init__(self, store):
        Thread.__init__(self)
        self.exceptions = 0
        self.store = store
        self.user = sample(['usera', 'userb', 'userc', 'userd',
                              'usere', 'userf', 'userg', 'userh'], 1)[0]
        self.host = sample(['hosta', 'hostb', 'hostc', 'hostd',
                              'hoste', 'hostf', 'hostg', 'hosth'], 1)[0]

    def run(self):
        for i in range(ITERATIONS):
            try:
                self.run_iteration()
            except:
                self.exceptions += 1;
                raise
            print('.', end='')
            sys.stdout.flush()

class CronTabTester(RandomTester):
    def run_iteration(self):
        self.store.save_crontab(self.host, self.user, self.randomtab())
        self.store.get_crontab(self.host, self.user)
        self.store.get_raw_crontab(self.host, self.user)

    def randomtab(self):
        return list(sample(['CRON_TZ=Europe/Paris',
                            'CRABSHELL=/bin/tcsh',
                            '#comment',
                            '* * * * * cal',
                            '0 * * * * date',
                            '0 0 * * * uname',
                            '0 0 * * 1-5 gnubeep',
                            '* * * * * CRABID=minutely /bin/minutely.sh'], 3))

class CronJobTester(RandomTester):
    def run_iteration(self):
        self.store.get_jobs()
        self.store.get_jobs(self.host, self.user)
        self.store.get_jobs(self.host, self.user, include_deleted=True)
        with self.store.lock:
            self.store._check_job(self.host, self.user, None, sample([
                              'command1', 'command2', 'command3'],1)[0])
        self.store.get_notifications()

class CronLogTester(RandomTester):
    def __init__(self, store):
        RandomTester.__init__(self, store)
        self.s = 0
        self.w = 0
        self.f = 0

    def run_iteration(self):
        c = [ 'command1', 'command2', 'command3', 'command4']
        self.store.log_start(self.host, self.user, None, sample(c, 1)[0])
        self.store.log_finish(self.host, self.user, None, sample(c, 1)[0],
                              1, 'stdout', 'stderr')
        with self.store.lock:
            id_ = self.store._check_job(self.host, self.user,
                                    None, sample(c, 1)[0])
        self.store.log_warning(id_, -1)
        self.store.get_job_info(id_)
        # Need to add the write_config method when implemented
        self.store.get_job_config(id_)
        self.store.get_job_finishes(id_, 10)
        self.store.get_job_events(id_, 10)

        es = self.store.get_events_since(self.s, self.w, self.f)
        for e in es:
            eid = e['id']
            if e['type'] == 1 and eid > self.s:
                self.s = eid
            elif e['type'] == 2 and eid > self.w:
                self.w = eid
            elif e['type'] == 3 and eid > self.f:
                self.f = eid

        self.store.get_fail_events(10)
        self.store.get_job_output(0, self.host, self.user, id_)
