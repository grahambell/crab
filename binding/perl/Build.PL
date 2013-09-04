#!/usr/bin/env perl

use strict;
use warnings;

use Module::Build;

our %require = ('Config::IniFiles' => 2.39,
                'File::HomeDir' => 0,
                'File::Spec' => 0,
                'HTTP::Request' => 0,
                'IO::Scalar' => 2.110,
                'JSON' => 0,
                'LWP::UserAgent' => 0,
                'Sys::Hostname' => 0,
                'perl' => '5.8.0',
               );


my $build = new Module::Build(
    module_name => 'WWW::Crab::Client',
    license       => 'gpl3',
    requires => \%require,
    build_requires => {
                       'Test::More' => 0,
                      },
);

$build->create_build_script();
