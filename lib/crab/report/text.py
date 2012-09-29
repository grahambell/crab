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

from crab import CrabEvent, CrabStatus

def report_to_text(report, event_list=True):
    lines = []
    sections = ['error', 'warning', 'ok']
    titles = ['Jobs with Errors', 'Jobs with Warnings', 'Successful Jobs']

    for (section, title) in zip(sections, titles):
        jobs = getattr(report, section)
        if jobs:
            lines.append(title)
            lines.append('=' * len(title))
            lines.append('')
            for id_ in jobs:
                lines.append('    ' + _summary_line(report, id_))
            lines.append('')

    if event_list:
        lines.append('Event Listing')
        lines.append('=============')
        lines.append('')

        for id_ in set.union(report.error, report.warning, report.ok):
            subhead = _summary_line(report, id_)
            lines.append(subhead)
            lines.append('-' * len(subhead))
            lines.append('')

            for e in report.events[id_]:
                lines.append('    ' + _event_line(e))

                if e['type'] == CrabEvent.FINISH:
                    finishid = e['eventid']
                    if finishid in report.stdout and report.stdout[finishid]:
                        lines.extend(_output_lines(8, 'Std. Out.',
                                                   report.stdout[finishid]))
                    if finishid in report.stderr and report.stderr[finishid]:
                        lines.extend(_output_lines(8, 'Std. Error',
                                                   report.stderr[finishid]))

            lines.append('')

    return "\n".join(lines)


def _summary_line(report, id_):
    info = report.info[id_]
    return '{0:10} {1:10} {2}'.format(info['host'], info['user'], info['title'])

def _event_line(event):
    return '{0:10} {1:10} {2}'.format(CrabEvent.get_name(event['type']),
                                CrabStatus.get_name(event['status']),
                                event['datetime'])

def _output_lines(indent, title, text):
    lines = []
    for line in text.strip().split('\n'):
        if lines:
            head = ''
        else:
            head = title
        lines.append('{0}{1:10} {2}'.format(' ' * indent, head, line))

    return lines
