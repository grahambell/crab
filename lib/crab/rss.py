import calendar
import datetime
import socket

import cherrypy
from PyRSS2Gen import RSS2, RSSItem, Guid

from crab import CrabError, CrabStatus


class CrabRSS:
    def __init__(self, store):
        self.store = store
        self.fqdn = socket.getfqdn()
        # TODO: make this configurable
        self.base = 'http://' + self.fqdn + ':8000';

    @cherrypy.expose
    def failures(self):
        # TODO: make limit configurable (in CherryPy App .ini file)
        events = self.store.get_fail_events(limit=20)

        # Attach output
        for fail in events:
            fail['stdout'] = None
            fail['stderr'] = None

            if fail['finishid'] is not None:
                try:
                    (stdout, stderr) = self.store.get_job_output(
                            fail['finishid'], fail['host'], fail['user'],
                            fail['id'])
                    fail['stdout'] = stdout
                    fail['stderr'] = stderr
                except CrabError:
                    pass

        rssitems = map(lambda e: self.event_to_rssitem(e), events)

        rss = RSS2('Crab failures', self.base + '/',
                   'List of recent cron job failures.',
                   lastBuildDate=datetime.datetime.now(),
                   ttl = 30,
                   items = rssitems)
        return rss.to_xml()

    def event_to_rssitem(self, event):
        title = (CrabStatus.get_name(event['status']) + ' : ' +
                    event['user'] + ' @ ' + event['host'])
        if event['command'] is not None:
            title += ' : '+ event['command']
        link = self.base + '/job/' + str(event['id'])
        if event['finishid'] is not None:
            link += '/output/' + str(event['finishid'])
        output = ''
        if event['stdout'] is not None and event['stdout'] != '':
            output += event['stdout']
        if event['stderr'] is not None and event['stderr'] != '':
            if event['stdout'] is not None and event['stdout'] != '':
                output += '\n\nStandard Error:\n\n'
            output += event['stderr']

        date = datetime.datetime.strptime(event['datetime'],
                                          '%Y-%m-%d %H:%M:%S')

        guid = ':'.join(['crab', self.fqdn, str(event['id']),
               str(calendar.timegm(date.timetuple())), str(event['status'])])

        info = {}

        if output != '':
            info['description'] = '<pre>' + output + '</pre>'

        return RSSItem(title=title,
                       link=link,
                       pubDate=date,
                       guid=Guid(guid, isPermaLink = False),
                       **info)

