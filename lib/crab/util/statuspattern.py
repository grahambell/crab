# Copyright (C) 2014 Science and Technology Facilities Council.
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

import re

from crab import CrabStatus


def check_status_patterns(status, config, output):
    """Function to update a job status based on the patterns.

    Compares the given output with the patterns in the
    job configuration, and returns the updated status."""

    # Is this a special status which doesn't indicate job completion?
    # If so we should not attempt to look at the patterns.
    if status == CrabStatus.ALREADYRUNNING:
        return status

    # Check for error status.
    if CrabStatus.is_error(status):
        return status

    fail_pattern = config['fail_pattern']
    if fail_pattern is not None and re.search(fail_pattern, output):
        return CrabStatus.FAIL

    # Check for warning status.
    if CrabStatus.is_warning(status):
        return status

    warning_pattern = config['warning_pattern']
    if warning_pattern is not None and re.search(warning_pattern, output):
        return CrabStatus.WARNING

    # Check for good status.
    success_pattern = config['success_pattern']
    if success_pattern is not None and re.search(success_pattern, output):
        return CrabStatus.SUCCESS

    # No match -- decide what to do based on which patterns were defined.
    if success_pattern is not None:
        if fail_pattern is not None:
            # There were success and fail patterns but we matched neither
            # of them, so the status is UNKNOWN.
            return CrabStatus.UNKNOWN
        else:
            # There was a success pattern which we did not match, so
            # assume this was a failure as there was no explicit success
            # match.
            return CrabStatus.FAIL

    # Otherwise return the original status.  If there was a failure
    # pattern, then we already know we didn't match it.
    return status
