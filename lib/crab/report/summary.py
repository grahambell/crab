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


def report_to_summary(report, max_jobs=3, max_len=10):
    """
    Generate a brief summary string for the given report.
    """

    # Determine the jobs of most interest: if none, return "no jobs".
    if report.error:
        jobs = report.error

    elif report.warning:
        jobs = report.warning

    elif report.ok:
        jobs = report.ok

    else:
        return 'no jobs'

    # Are there too many jobs to list?
    if len(jobs) > max_jobs:
        return 'multiple jobs'

    # Truncate the job titles, allowing three characters for "..." when
    # indicating truncation.
    titles = []
    crop_len = max(1, max_len - 3)

    for id_ in jobs:
        title = report.info[id_]['title']

        if len(title) <= max_len:
            titles.append(title)

        else:
            titles.append(title[:crop_len] + '...')

    # Join the titles to create the summary.
    return ', '.join(sorted(titles))
