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

class CrabStoreFile:
    """Store class for cron job output.
    
    This is currently a dummy implementation of just the
    write_job_output and get_job_output methods, to allow
    the "outputstore" hooks in CrabStoreDB to be tested.
    
    It needs a constructor method including parameters to
    determine where the files are to be stored."""

    def write_job_output(self, finishid, host, user, id_, stdout, stderr):
        """Write the cron job output to a file.

        DUMMY IMPLEMENTATION

        The only parameter required to uniquely identify the event
        associated with this output is the "finishid", but the
        host, user and job ID number are also provided to allow
        hierarchical storage."""

        print('Write output for finishid:', finishid, 'host:', host,
              'user:', user, 'id:', id_)
        print('Stdout:', stdout)
        print('Stderr:', stderr)

    def get_job_output(self, finishid, host, user, id_):
        """Find the file containing the cron job output and read it.

        DUMMY IMPLEMENTATION

        As for write_job_output, only the "finishid" is really required,
        but this method can make use of the host, user and job ID number
        to read from a directory hierarchy."""

        print('Read output for finishid:', finishid, 'host:', host,
              'user:', user, 'id:', id_)
        return ('Dummy stdout', 'Dummy stderr')

