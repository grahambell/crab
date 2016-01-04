# Copyright (C) 2016 East Asian Observatory.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json

JOB_FIELDS = [
    'host',
    'user',
    'crabid',
    'command',
    'time',
    'timezone',
]

CONFIG_FIELDS = [
    'graceperiod',
    'timeout',
    'success_pattern',
    'warning_pattern',
    'fail_pattern',
    'note',
    '*inhibit',
]

NOTIFICATION_FIELDS = [
    'method',
    'address',
    'time',
    'timezone',
    '*skip_ok',
    '*skip_warning',
    '*skip_error',
    '*include_output',
]


def import_config(store, file_):
    """Read job and configuration information from a JSON file."""

    # Read JSON from the given file handle.
    data = json.load(file_)

    # Ensure each job listed is present and update its configuration.
    for job in data['jobs']:
        id_ = store.check_job(**job['info'])

        configid = None
        if job['config'] is not None:
            configid = store.write_job_config(id_, **job['config'])

        # If there were notifications, try to fetch the existing notifications
        # so that those which match can be updated instead of being duplicated.
        # If we don't already have a configuration, create a blank one for
        # attaching notifications.
        if job['notifications']:
            # If we didn't set a config, check one didn't already exist.
            if configid is None:
                config = store.get_job_config(id_)
                if config is not None:
                    configid = config['configid']

            # If we still don't have a configid (didn't set and didn't already
            # exist) create one, otherwise fetch notifications.
            existing_notify = {}
            if configid is None:
                configid = store.write_job_config(id_)
            else:
                for notification in store.get_job_notifications(configid):
                    existing_notify[_notify_key(notification)] = \
                        notification['notifyid']

            for notification in job['notifications']:
                notifyid = existing_notify.get(_notify_key(notification))
                store.write_notification(notifyid=notifyid, configid=configid,
                                         host=None, user=None, **notification)

    # Store any crontabs which were given.
    for crontab in data['crontabs']:
        store.write_raw_crontab(**crontab)

    # Get a list of existing "match" notifications, then store/update
    # those given.
    existing_notify = {}
    for notification in store.get_match_notifications():
        existing_notify[_notify_key(notification, match=True)] = \
            notification['notifyid']

    for notification in data['notifications']:
        notifyid = existing_notify.get(_notify_key(notification, match=True))
        store.write_notification(notifyid=notifyid, configid=None,
                                 **notification)


def export_config(store, file_):
    """Write job and configuration information to a JSON file."""

    # Create list of jobs.
    jobs = []
    hostuser = set()
    for job in store.get_jobs():
        hostuser.add((job['host'], job['user']))

        config = store.get_job_config(job['id'])

        # If there was a configuration, also check for notifications.
        notifications = []
        if config is not None:
            for notification in store.get_job_notifications(
                    config['configid']):
                notifications.append(_filter_dict(
                    notification, NOTIFICATION_FIELDS))

        jobs.append({
            'info': _filter_dict(job, JOB_FIELDS),
            'config': _filter_dict(config, CONFIG_FIELDS),
            'notifications': notifications,
        })

    # Retrieve raw crontabs.
    crontabs = []
    for (host, user) in hostuser:
        crontab = store.get_raw_crontab(host, user)

        if crontab is not None:
            crontabs.append({
                'host': host,
                'user': user,
                'crontab': crontab,
            })

    # Retrieve "match" notifications.
    notifications = []
    for notification in store.get_match_notifications():
        notifications.append(_filter_dict(
            notification, ['host', 'user'] + NOTIFICATION_FIELDS))

    # Finally write the JSON to the given file handle.
    json.dump({
        'jobs': jobs,
        'notifications': notifications,
        'crontabs': crontabs,
    }, file_, indent=4, separators=(',', ': '), sort_keys=True)


def _filter_dict(d, keys):
    """Filters a dictionary to contain only the given keys.

    If the input dictionary is None, None is returned.

    If a key is prefixed with a *, it is forced to be a boolean.
    """

    if d is None:
        return d

    return dict(
        (key[1:], bool(d[key[1:]])) if key.startswith('*') else (key, d[key])
        for key in keys)


def _notify_key(notification, match=False):
    """Return notification information tuple for use in identifying a
    notification.

    If "match" is selected, then includes host and user for a match-type
    notification."""

    if match:
        return (notification['host'], notification['user']) + \
            _notify_key(notification)

    return (notification['method'], notification['address'],
            notification['time'], notification['timezone'])
