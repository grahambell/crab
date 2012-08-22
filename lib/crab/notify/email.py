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

from __future__ import absolute_import

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from smtplib import SMTP

from crab.report.text import report_to_text
from crab.report.html import report_to_html

class CrabNotifyEmail:
    """Class to send notification messages by email."""

    def __init__(self, config, base_url):
        """Construct a nofication object.

        Stores relevant configuration information in the object."""

        self.home = config['crab']['home']
        self.server = config['email']['server']
        self.from_ = config['email']['from']
        self.subject_ok = config['email']['subject_ok']
        self.subject_warning = config['email']['subject_warning']
        self.subject_error = config['email']['subject_error']
        self.base_url = base_url

    def __call__(self, report, to):
        """Sends a report by email to the given addresses."""

        if report.error:
            subject = self.subject_error
        elif report.warning:
            subject = self.subject_warning
        else:
            subject = self.subject_ok

        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['Date'] = formatdate(localtime=True)
        message['From'] = self.from_
        message['To'] = ', '.join(to)

        message.attach(MIMEText(report_to_text(report), 'plain'))
        message.attach(MIMEText(report_to_html(report,
                                self.home, self.base_url), 'html'))

        smtp = SMTP(self.server)
        smtp.sendmail(self.from_, to, message.as_string())
        smtp.quit()
