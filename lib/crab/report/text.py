from crab import CrabEvent, CrabStatus
from crab.report import CrabReport

def report_to_text(report, output, event_list=True):
    lines = []
    sections = ['error', 'warning', 'ok']
    titles = ['Jobs with Errors', 'Jobs with Warnings', 'Successful Jobs']

    for (section, title) in zip(sections, titles):
        if output[section]:
            lines.append(title)
            lines.append('=' * len(title))
            lines.append('')
            for id_ in output[section]:
                lines.append('    ' + _summary_line(report, id_))
            lines.append('')

    if event_list:
        lines.append('Event Listing')
        lines.append('=============')
        lines.append('')

        for id_ in set.union(output['error'], output['warning'], output['ok']):
            subhead = _summary_line(report, id_)
            lines.append(subhead)
            lines.append('-' * len(subhead))
            lines.append('')

            job = report.get_job(id_)

            for e in job['events']:
                lines.append('    ' + _event_line(e))

            lines.append('')

    return "\n".join(lines)


def _summary_line(report, id_):
    job = report.get_job(id_)
    info = job['info']
    return '{0:10} {1:10} {2}'.format(info['host'], info['user'], info['title'])

def _event_line(event):
    return '{0:10} {1:10} {2}'.format(CrabEvent.get_name(event['type']),
                                CrabStatus.get_name(event['status']),
                                event['datetime'])
