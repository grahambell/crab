# Copyright (C) 2013 Science and Technology Facilities Council.
# Copyright (C) 2021 East Asian Observatory.
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
# Otherwise if the backported subprocess32 module is not available,
# we need to provide a function to do this and a dummy timeout implementation.
have_new_subprocess = True
if sys.version_info >= (3, 2):
    import subprocess
    from subprocess import TimeoutExpired

else:
    try:
        import subprocess32 as subprocess
        from subprocess32 import TimeoutExpired

    except ImportError:
        have_new_subprocess = False
        import subprocess


if have_new_subprocess:
    subprocess_options = {'restore_signals': True}

    def subprocess_communicate(p, input=None, timeout=None):
        return p.communicate(input=input, timeout=timeout)

    def subprocess_call(args, timeout=None, **kwargs):
        return subprocess.call(args, timeout=timeout, **kwargs)

else:
    subprocess_options = {'preexec_fn': restore_signals}

    def subprocess_communicate(p, input=None, timeout=None):
        return p.communicate(input=input)

    def subprocess_call(args, timeout=None, **kwargs):
        return subprocess.call(args, **kwargs)

    class TimeoutExpired(Exception):
        pass
