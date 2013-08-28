# Copyright (C) 2013 Science and Technology Facilities Council.
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

import signal
import sys

def restore_signals():
    """Restore signals which Python otherwise ignores.

    For more information about this issue, please see:
    http://bugs.python.org/issue1652"""

    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    signal.signal(signal.SIGXFSZ, signal.SIG_DFL)

# Determine which options should be given to the subprocess module
# when starting new processes.  The "restore_signals" option was
# added in Python 3.2, so we need only ensure that it is turned on.
# Otherwise we need to provide a function to do this.
if sys.version_info >= (3, 2):
    subprocess_options = {'restore_signals': True}
else:
    subprocess_options = {'preexec_fn': restore_signals}
