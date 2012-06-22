import re

from crab.util.string import remove_quotes, quote_multiword, split_quoted_word

def get_crontab(store, host, user):
    """Fetches the job entries for a particular host and user and builds
    a crontab style representation.

    The output consists of job lines, which are commented out if
    their schedule is not in the database.  Timezone lines are inserted
    where the timezone changes between jobs.  If job identifiers
    are present, CRABID will be set on the corresponding job lines."""

    crontab = []
    timezone = None

    for job in store.get_user_jobs(host, user):
        # Check if job has a schedule attached.
        time = job['time']
        if time is None:
            time = '### CRAB: UNKNOWN SCHEDULE ###'

        # Track the timezone, so that we do not repeat CRON_TZ
        # assignments unnecessarily.
        if job['timezone'] is not None and job['timezone'] != timezone:
            timezone = job['timezone']
            crontab.append('CRON_TZ=' + quote_multiword(timezone))

        elif job['timezone'] is None and timezone is not None:
            crontab.append('### CRAB: UNKNOWN TIMEZONE ###')
            timezone = None

        # Include the jobid in the command if present.
        command = job['command']
        if job['jobid'] is not None:
            command = 'CRABID=' + quote_multiword(job['jobid']) + ' ' + command

        crontab.append(time + ' ' + command)

    return crontab

# TODO: update the store's interface so that we don't need to call
# private methods.

def save_crontab(store, host, user, crontab, timezone=None):
    """Takes a list of crontab lines and uses them to update the job records.

    It looks for the CRABID and CRON_TZ variables, but otherwise
    ignores everything except command lines.  It also checks for commands
    starting with a CRABID= definition, but otherwise inserts them
    into the database as is."""

    # These patterns do not deal with quoting or trailing spaces,
    # so these must be dealt with in the code below.
    blankline = re.compile('^\s*$')
    comment = re.compile('^\s*#')
    variable = re.compile('^\s*(\w+)\s*=\s*(.*)$')
    cronrule = re.compile('^\s*(@\w+|\S+\s+\S+\s+\S+\s+\S+\s+\S+)\s+(.*)$')

    idset = store.get_user_job_set(host, user)
    jobid = None

    store._begin_transaction()

    try:

        # Iterate over the supplied cron jobs, removing each
        # job from the idset set as we encounter it.

        for job in crontab:
            if (blankline.search(job) is not None or
                    comment.search(job) is not None):
                continue

            m = variable.search(job)
            if m is not None:
                (var, value) = m.groups()
                if var == 'CRABID':
                    jobid = remove_quotes(value.rstrip())
                if var == 'CRON_TZ':
                    timezone = remove_quotes(value.rstrip())
                continue

            m = cronrule.search(job)
            if m is not None:
                (time, command) = m.groups()

                if command.startswith('CRABID='):
                    (jobid, command) = split_quoted_word(command[7:].rstrip())

                command = command.rstrip()

                id_ = store._check_job_with_cursor(host, user, jobid,
                                                   command, time, timezone)

                idset.discard(id_)
                jobid = None
                continue

            print '*** Did not recognise line:', job


        # Set any jobs remaining in the id set to deleted
        # because we did not see them in the current crontab

        for id_ in idset:
            store._delete_job(id_);

    except:
        store._rollback_transaction()
        raise

    else:
        store._commit_transaction()
