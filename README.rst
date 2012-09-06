Crab
====

Requirements
------------

* crontab (0.15 or newer): http://pypi.python.org/pypi/crontab/#downloads
* CherryPy: http://download.cherrypy.org/cherrypy/
* Mako templates: http://pypi.python.org/pypi/Mako/#downloads
* PyRSS2Gen: http://dalkescientific.com/Python/PyRSS2Gen.html
* jQuery: http://code.jquery.com/

Installation
------------

The Crab libraries and scripts can be installed as follows::

    python setup.py install

If any of the Python dependancies listed above can not be installed,
they can be symlinked into the ``lib`` directory in the following locations::

    lib/PyRSS2Gen.py
    lib/cherrypy
    lib/crontab
    lib/mako

The jQuery JavaScript library should be copied or symlinked into
Crab's ``res`` directory as::

    res/jquery.js

The Crab Server
---------------

Database Creation
~~~~~~~~~~~~~~~~~

A SQLite database file can be prepared for Crab using the
schema provided::

    % sqlite3 crab.db < doc/schema.txt

Configuration
~~~~~~~~~~~~~

The Crab server is configured by a ``crabd.ini`` file which can
be placed either in ``/etc/crab/`` or ``~/.crab/``.  Note that this
is a CherryPy configuration file, which is read slightly differently to
typical ``.ini`` files which use Python's ConfigParser.

    % cp doc/crabd.ini ~/.crab/

The example ``crabd.ini`` file should be edited to uncomment the
[crab] and [store] sections.  The 'home' and 'file' entries must point
to the location of Crab's data files and the database file just created.

Running
~~~~~~~

The Crab server is run as ``crabd``.  When the server
is executed directly, it will stay in the foreground::

    % crabd

It can also be run in the background with the ``crabd-check`` script,
which checks that it is not still running from a previous invocation of
``crabd-check``.  Therefore this is suitable for running from cron
to keep the server running::

    PYTHONPATH=/path/to/crab/lib
    PATH=/path/to/crab/scripts:/bin:/usr/bin
    7-57/10 * * * * CRABIGNORE=yes crabd-check

With the server running, the Crab dashboard should be visible from
a web browser, by default on port 8000.  The Crab clients will use this
same web service to communicate with the server.

Monitoring Cron Jobs
--------------------

There are two Crab client commands: the ``crab`` utility, and
the ``crabsh`` wrapper shell.  Cron jobs can either be run under
``crabsh``, or they can be updated to report their own status
to the Crab server.

Configuration
~~~~~~~~~~~~~

The Crab clients are configured by a ``crab.ini`` file which can
be placed either in ``/etc/crab/`` or ``~/.crab/``.  The file
specifies how to contact the Crab server, and the username and
hostname which the client will use to report cron jobs.

    % cp doc/crab.ini ~/.crab/

The configuration can be checked with the ``crab info`` command.
This reports the settings, and indicates which configuration
files were read.  It is a useful way to check that everything
is in order before importing a crontab.

The ``crabsh`` Wrapper
~~~~~~~~~~~~~~~~~~~~~~

``crabsh`` is a wrapper script designed to act like a shell.  It can
therefore be invoked by cron via the ``SHELL`` variable, for example::

    PYTHONPATH=/path/to/crab/lib
    SHELL=/path/to/crab/scripts/crabsh
    0 10 * * 1-5 CRABID=test echo "Test cron job"

Where the rules following the ``SHELL`` assignment will be run with the 
wrapper.  The ``PYTHONPATH`` will need to be set if Crab is not installed
where the system can find it.  Cron requires the full path when
specifying the ``SHELL``. The ``CRABID`` parameter is used to
give the cron job a convenient and unique name.  This is optional,
unless there are multiple jobs with the same command, 
in which case they would otherwise be indistinguishable.
However if it specified, then it must be unique for a given
host and user, as the Crab server will use it in preference
to the command string to identify cron job reports.

``crabsh`` will notify the server when the job starts, and when it finishes, 
assuming it succeeded if the exit status was zero.

Crab-aware Cron Jobs
~~~~~~~~~~~~~~~~~~~~

Alternatively a cron job can report its own status to the Crab server.
The most straightforward way to do this is to execute the ``crab``
utility.  So a cron job written as a shell script could include
commands such as::

   % crab start -c "$0"
   % crab finish -c "$0"
   % crab fail -c "$0"

In this way you can also report an unknown status with ``crab unknown``.

Python
    If the cron job is written in Python, it could import ``crab.client``
    directly and make use of the ``CrabClient`` class.

Perl
    A Perl module ``WWW::Crab::Client`` is also available.

Other languages
    Other language libraries could be written.  They would need to make
    HTTP PUT requests with an appropriate JSON message.

Managing the Cron Job List
~~~~~~~~~~~~~~~~~~~~~~~~~~

The Crab server needs to be given the schedule for each job so that it
can detect when a job is late or missed.  This is done by "importing"
a user's crontab file::

    % crab import

The database entries can then be checked by "exporting" them,
again using the ``crab`` utility::

    % crab export
    > CRON_TZ=Pacific/Honolulu
    > 0 10 * * 1-5 CRABID=test echo "Test cron job"

The output is a set of crontab-style lines representing the entries 
from the database.  The crontab can be retrieved exactly as last imported
(from a separate database table containing the raw crontab) by giving
the ``--raw`` option as follows::

    % crab export --raw

This is useful as a backup in case a crontab is accidentally lost.
However it will not contain any new jobs which have been added automatically
by the Crab server since the last import.

Cron Job Parameters
~~~~~~~~~~~~~~~~~~~

In order to specify the Crab specific parameters of a cron job,
Bourne-style shell variables at the start of a command are used.
The syntax for each cron job is as follows::

    <schedule> [CRABIGNORE=yes] [CRABID=<identifier>] <command string>

A command starting with CRABIGNORE set to a value other than
0/no/off/false will be ignored when importing a crontab.

A CRABID specification will override any CRABID environment variable
in effect, and is a better way of specifying the identifier as it
can not apply to more than one cron job.  There should not be multiple
jobs with the same identifier for any user and host.

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

CRABECHO
    If present and not set to 0/no/off/false then ``crabsh`` will print out
    the standard output and standard error it receives from the cron job.
    This allows the output to be sent by email via cron's default
    behavior as well as being captured by the Crab system.

CRABHOST
    Specifies the Crab server to which clients should connect, overriding
    the setting in the configuration file.

CRABID
    Specifies the job identifier which ``crabsh`` will use to file reports
    if there is no ``CRABID=`` variable at the start of the cron command.
    This should be used with caution to avoid specifying the same
    identifier for multiple cron jobs.

CRABPORT
    Specifies the port on the Crab server, overriding the setting in the
    configuration file.

CRABSHELL
    The shell which ``crabsh`` will use to invoke the cron job command.
    Defaults to ``/bin/sh`` regardless of the user's shell to replicate
    cron's behavior.

CRABSYSCONFIG
    The directory to be searched for system-level configuration files.
    If not set, then /etc/crab will be used.

CRON_TZ
    Cron reads this variable to know in which timezone to interpret
    the crontab schedule.  When the server receives a crontab,
    it will check for this timezone and use it to override the
    general timezone which the ``crab`` utility will send with
    the crontab (if it is able to determine it).

MAILTO
    Configures the email address to which cron sends email.  This is
    useful when ``CRABECHO`` is on, or if ``crabsh`` needs to report
    a failure to contact the Crab server.

SHELL
    Cron uses this variable to select the shell which will be used
    to execute the cron jobs.  The full path must be specified.
    Crab does not use this variable itself.

TZ
    This can be set to the system timezone, in which case ``crab import``
    will use it as the default timezone for the crontab.

Copyright
---------

Copyright (C) 2012 Science and Technology Facilities Council.

Crab is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Crab.  If not, see <http://www.gnu.org/licenses/>.
