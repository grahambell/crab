#!/usr/bin/env python

# Copyright (C) 2012 Science and Technology Facilities Council.
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

from __future__ import print_function

from crab.server.config import read_crabd_config, construct_store

def main():
    config = read_crabd_config()

    store = construct_store(config['store'])
    outputstore = construct_store(config['outputstore'])

    copy_data(store, store, outputstore)

def copy_data(indexstore, instore, outstore):
    """Copies data from the instore to the outstore, using the
    indexstore as the one from which to get the list of
    events and crontabs to copy."""

    hostuser = set()

    for job in indexstore.get_jobs(include_deleted=True):
        hostuser.add((job['host'], job['user']))

        print('Processing job:', job['id'])

        for finish in indexstore.get_job_finishes(job['id'], limit=None):
            pair = instore.get_job_output(finish['finishid'],
                        job['host'], job['user'], job['id'], job['crabid'])

            if pair is not None:
                (stdout, stderr) = pair

                outstore.write_job_output(finish['finishid'],
                        job['host'], job['user'], job['id'], job['crabid'],
                        stdout, stderr)

    for (host, user) in hostuser:
        print('Processing crontab:', user, '@', host)

        crontab = instore.get_raw_crontab(host, user)

        if crontab is not None:
            outstore.write_raw_crontab(host, user, crontab)

if __name__ == "__main__":
    main()
