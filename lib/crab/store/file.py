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

import os

from crab import CrabError
from crab.util.string import alphanum

class CrabStoreFile:
    """Store class for cron job output.
    
    This backend currently implements only the write_job_output and
    get_job_output methods, to allow it to be used as an
    "outputstore" along with CrabStoreDB."""

    def __init__(self, dir):
        """Constructor for file-based storage backend.

        Takes a path to the base directory in which the files are to be
        stored."""

        self.dir = dir
        self.breakdigits = 3
        self.outext = 'txt'
        self.errext = 'err'
        self.tabext = 'txt'

        if not os.path.isdir(self.dir):
            raise CrabError('file store error: invalid base directory')

        if not os.access(self.dir, os.W_OK):
            raise CrabError('file store error: unwritable base directory')

        self.outputdir = os.path.join(dir, 'output')
        self.tabdir = os.path.join(dir, 'crontab')

        for directory in [self.outputdir, self.tabdir]:
            if not os.path.exists(directory):
                try:
                    os.mkdir(directory)
                except OSError as err:
                    raise CrabError('file store error: '
                                    'could not make directory ' + directory +
                                    ': ' + str(err))


    def write_job_output(self, finishid, host, user, id_, crabid,
                         stdout, stderr):
        """Write the cron job output to a file.

        The only parameter required to uniquely identify the event
        associated with this output is the "finishid", but the
        host, user and job identifiers are also provided to allow
        hierarchical storage.

        Always writes a stdout file (extension set by self.outext, by default
        txt), but only writes a stderr file (extension self.errext, default
        err) if the standard error is not empty."""

        path = self._make_output_path(finishid, host, user, id_, crabid)

        (dir, file) = os.path.split(path)

        if not os.path.exists(dir):
            try:
                os.makedirs(dir)
            except OSError as err:
                raise CrabError('file store error: could not make directory: ' +
                                str(err))

        outfile = path + '.' + self.outext
        errfile = path + '.' + self.errext

        if os.path.exists(outfile) or os.path.exists(errfile):
            raise CrabError('file store error: file already exists: ' + path)

        try:
            with open(outfile, 'w') as file:
                file.write(stdout)

            if stderr != '':
                with open(errfile, 'w') as file:
                    file.write(stderr)

        except IOError as err:
            raise CrabError('file store error: could not write files: ' +
                            str(err))

    def get_job_output(self, finishid, host, user, id_, crabid):
        """Find the file containing the cron job output and read it.

        As for write_job_output, only the "finishid" is logically required,
        but this method makes use of the host, user and job identifiers
        to read from a directory hierarchy.

        Requires there to be an stdout file but allows the
        stderr file to be absent."""

        path = self._make_output_path(finishid, host, user, id_, crabid)
        outfile = path + '.' + self.outext

        if not os.path.exists(outfile):
            if crabid is not None:
                # Try again with no crabid.  This is to handle the case where
                # a job is imported with no name, but is subsequently named.
                path = self._make_output_path(finishid, host, user, id_, None)
                outfile = path + '.' + self.outext

                if not os.path.exists(outfile):
                    return None
            else:
                return None

        try:
            with open(outfile) as file:
                stdout = file.read()

            errfile = path + '.' + self.errext

            if os.path.exists(errfile):
                with open(errfile) as file:
                    stderr = file.read()
            else:
                stderr = ''

        except IOError as err:
            raise CrabError('file store error: could not read files: ' +
                            str(err))

        return (stdout, stderr)

    def write_raw_crontab(self, host, user, crontab):
        """Writes the given crontab to a file."""

        pathname = self._make_crontab_path(host, user)

        (dir, file) = os.path.split(pathname)

        if not os.path.exists(dir):
            try:
                os.makedirs(dir)
            except OSError as err:
                raise CrabError('file store error: could not make directory: ' +
                                str(err))

        try:
            with open(pathname, 'w') as file:
                file.write('\n'.join(crontab))

        except IOError as err:
            raise CrabError('file store error: could not write crontab: ' +
                            str(err))


    def get_raw_crontab(self, host, user):
        """Reads the given user's crontab from a file."""

        pathname = self._make_crontab_path(host, user)

        if not os.path.exists(pathname):
            return None

        try:
            with open(pathname) as file:
                crontab = file.read()

        except IOError as err:
            raise CrabError('file store error: could not read crontab: ' +
                            str(err))

        return crontab.split('\n')


    def _make_output_path(self, finishid, host, user, id_, crabid):
        """Determine the full path to use to store output
        (excluding file extensions).

        This uses a directory heirarchy:

            * host
            * user
            * crabid (name) or ID (number)
            * finish ID

        Where the finish ID is broken into blocks of a few characters,
        the first of which is zero-padded to ensure all blocks are the
        same length.  This prevents an excessive number of entries
        being placed in a single directory, while the path is easily
        determined without needing to read the directory structure.
        So breaking on the default number of digits (3) finish ID 1 would
        yield 001 whereas 2005 would yield 002/005."""

        if crabid is None or crabid == '':
            job = str(id_)
        else:
            job = alphanum(crabid)

        finish = str(finishid)
        finishpath = []

        lead = len(finish) % self.breakdigits
        if lead:
            finishpath.append('0' * (self.breakdigits - lead) + finish[:lead])
            finish = finish[lead:]

        finishpath.extend([finish[x:x + self.breakdigits]
                           for x in range(0, len(finish), self.breakdigits)])

        return os.path.join(self.outputdir, alphanum(host), alphanum(user),
                            job, *finishpath)

    def _make_crontab_path(self, host, user):
        """Determine the full path to be used to store a crontab."""

        return (os.path.join(self.tabdir, alphanum(host), alphanum(user)) +
                '.' + self.tabext)
