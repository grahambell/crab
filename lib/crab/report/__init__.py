from crab import CrabError, CrabStatus, CrabEvent
from crab.util.filter import CrabEventFilter

class CrabReport:
    """Class for generating reports on the operation of cron jobs.

    This class maintains a cache of job information and events
    to allow it to handle multiple report requests in an efficient
    manner.  This depends on a single configuration, so methods
    for adjusting the filtering are not provided."""

    def __init__(self, store, start, end,
                 skip_start=True, skip_ok=False, **kwargs):
        """Constructor for report object."""

        self.store = store
        self.start = start
        self.end = end

        self.filter = CrabEventFilter(store, skip_start=skip_start,
                                      skip_ok=skip_ok, **kwargs)
        self.cache = {}

    def __call__(self, jobs):
        """Function call method, to process a list of jobs.

        Takes a list of jobs, which can either be a list of job ID numbers,
        or a list of job information dicts as returned by get_jobs.

        Returns a dict including the number of jobs to be included in the
        report and sets of jobs in each state, or None if there are no
        entries to show."""

        checked = set()
        error = set()
        warning = set()
        ok = set()
        num = 0

        for job in jobs:
            if isinstance(job, dict):
                id_ = job['id']
                if id_ in self.cache:
                    info = self.cache[id_]['info']
                else:
                    info = job.copy()
                    self._add_job(id_, info)
            else:
                id_ = job
                if id_ in self.cache:
                    info = self.cache[id_]['info']
                else:
                    info = self.store.get_job_info(id_)
                    if info is None:
                        continue
                    self._add_job(id_, info)

            if id_ in checked:
                continue
            else:
                checked.add(id_)

            if 'events' in self.cache[id_]:
                events = self.cache[id_]['events']
            else:
                self.filter.set_timezone(info['timezone'])
                events = self.filter(self.store.get_job_events(id_, limit=None,
                                          start=self.start, end=self.end))
                self.cache[id_]['events'] = events

                info['errors'] = self.filter.errors
                info['warnings'] = self.filter.warnings

            if events:
                num += 1

                if info['errors']:
                    error.add(id_)
                elif info['warnings']:
                    warning.add(id_)
                else:
                    ok.add(id_)

        if num:
            return {'num': num, 'error': error, 'warning': warning, 'ok': ok}
        else:
            return None

    def get_job(self, id_):
        """Returns our cache entry for the specified job."""

        return self.cache.get(id_)

    def _add_job(self, id_, info):
        """Adds a job info record to our cache.

        Also performs any general operations we want to perform
        in preparation for generating reports."""

        if info['jobid'] is None:
            info['title'] = info['command']
        else:
            info['title'] = info['jobid']

        self.cache[id_] = {'info': info}

