import datetime
import socket

import cherrypy
from PyRSS2Gen import RSS2, RSSItem, Guid

from crab import CrabStatus


class CrabRSS:
    def __init__(self, store):
        self.store = store
        # TODO: make this configurable
        self.base = 'http://' + socket.getfqdn() + ':8000';

    @cherrypy.expose
    def failures(self):
        events = self.store.get_fail_events()

        # Attach output
        for fail in events:
            if fail['finishid'] is not None:
                (stdout, stderr) = self.store.get_job_output(fail['finishid'])
                fail['stdout'] = stdout
                fail['stderr'] = stderr
            else:
                fail['stdout'] = None
                fail['stderr'] = None

        rssitems = map(lambda e: self.event_to_rssitem(e), events)

        rss = RSS2('crab failures', self.base + '/',
                   'List of recent cron job failures.',
                   lastBuildDate=datetime.datetime.now(),
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
        if event['stdout'] is not None:
            output += 'STDOUT:\n' + event['stdout'] + '\n\n'
        if event['stderr'] is not None:
            output += 'STDERR:\n' + event['stderr'] + '\n\n'

        guid = ':'.join(['crab', socket.getfqdn(), str(event['id']),
                        event['datetime'], str(event['status'])])

        return RSSItem(title=title,
                       link=link,
                       description='<pre>' + output + '</pre>',
                       pubDate=datetime.datetime.strptime(event['datetime'],
                                                          '%Y-%m-%d %H:%M:%S'),
                       guid=Guid(guid, isPermaLink = False))

