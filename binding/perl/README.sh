#!/bin/bash

cat <<END
WWW::Crab::Client
=================

END

perl -MPod::Usage -e 'pod2usage(-input=>"lib/WWW/Crab/Client.pm",-verbose=>99,-sections=>["DESCRIPTION"])' | sed -e '1d'

cat <<END
    The Crab server and utilities are available from:

    http://github.com/grahambell/crab

Requirements
------------

END

perl -e 'local $\ = "\n"; $INC{"Module/Build.pm"} = 1; do "Build.PL"; print "    ", $_ foreach keys %require;'

cat <<END

Building
--------

    perl Build.PL
    ./Build
    ./Build test
    ./Build install

Authors
-------

END

perl -MPod::Usage -e 'pod2usage(-input=>"lib/WWW/Crab/Client.pm",-verbose=>99,-sections=>["AUTHOR"])' | sed -e '1d'

cat <<END

Copyright
---------

END

perl -MPod::Usage -e 'pod2usage(-input=>"lib/WWW/Crab/Client.pm",-verbose=>99,-sections=>["COPYRIGHT"])' | sed -e '1d'
