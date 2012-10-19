=head1 NAME

WWW::Crab::Client - Crab client library

=head1 SYNOPSIS

  use WWW::Crab::Client;

  my $crab = new WWW::Crab::Client();

  eval {
      $crab->start();
  };

  # Perform the cron job actions ...

  my $finished_ok = eval {
      $crab->finish(status => WWW::Crab::Client::SUCCESS, stdout => $message);
  };
  unless ($finished_ok) {
      print "Failed to report job completion.\n" . $@ . "\n" . $message;
  }

=head1 DESCRIPTION

This module implements a subset of the Crab protocol sufficient
for reporting the status of a cron job to the Crab server.
It is intended to work similarly to the Python Crab client module,
but be more convient for cron jobs written in Perl.

=cut

package WWW::Crab::Client;

use strict;

use Config::IniFiles;
use File::HomeDir;
use File::Spec;
use HTTP::Request;
use JSON;
use LWP::UserAgent;
use Sys::Hostname;

our $VERSION = 0.02;

use constant {
    SUCCESS       => 0,
    FAIL          => 1,
    UNKNOWN       => 2,
    COULDNOTSTART => 3,
};

=head1 CONSTRUCTOR

=over 4

=item new()

Constructs a new client object.  All parameters are optional.
If no job identifier is given, then a null value is sent to
the server.  If the command is unspecified, C<$0> will be used.
No communication is performed until the L<start> or L<finish>
methods are called.

  my $crab = new WWW::Crab::Client(id       => 'job identifier',
                                   command  => 'command name',
                                   server   => 'localhost',
                                   port     => 8000,
                                   hostname => 'localhost',
                                   username => 'username');

If the other settings are not specified, the crab settings files
will be read, the CRABHOST and CRABPORT environment variables will
be checked, or defaults will be used.

=cut

sub new {
    my $class = shift;
    my %opt = @_;

    my ($username, undef, undef, undef, undef, undef, undef,
        undef, undef, undef) = getpwuid($<);

    my $conf = new Config::IniFiles(-file => \'', -allowempty => 1);
    my $conf_system = File::Spec->catfile($ENV{'CRABSYSCONFIG'} || '/etc/crab',
                                          'crab.ini');
    my $conf_user = File::Spec->catfile(File::HomeDir->my_home(),
                                        '.crab', 'crab.ini');
    $conf = new Config::IniFiles(-file => $conf_system, '-import' => $conf,
                                 -allowempty => 1)
        if (-e $conf_system);

    $conf = new Config::IniFiles(-file => $conf_user, '-import' => $conf,
                                 -allowempty => 1)
        if (-e $conf_user);

    my $self = {
        id       => $opt{'id'}       || undef,
        command  => $opt{'command'}  || $0,
        server   => $opt{'server'}   || $ENV{'CRABHOST'} ||
                                     $conf->val('server', 'host', 'localhost'),
        port     => $opt{'port'}     || $ENV{'CRABPORT'} ||
                                     $conf->val('server', 'port', 8000),
        hostname => $opt{'hostname'} || $conf->val('client', 'hostname',
                                            hostname()),
        username => $opt{'username'} || $conf->val('client', 'username',
                                            $username),
    };

    return bless $self, $class;
}

=back

=head1 METHODS

=over 4

=item start()

Reports that the job has started.

  $crab->start();

This method uses "die" to raise an exception if it is unsuccessful
in reporting to the Crab server.

Returns a true value on success.

=cut

sub start {
    my $self = shift;

    return $self->_write_json($self->_get_url('start'), {
        command => $self->{'command'}});
}

=item finish()

Reports that the job has finished.  If the status is not specified,
UNKNOWN will be sent.

  $crab->finish(status => WWW::Crab::Client::SUCCESS,
                stdout => $command_output,
                stderr => $error_message);

The following constants are defined in this module, and should be used
to obtain the appropriate Crab status codes:

  SUCCESS
  FAIL
  UNKNOWN
  COULDNOTSTART

This method uses "die" to raise an exception if it is unsuccessful
in reporting to the Crab server.

Returns a true value on success.

=cut

sub finish {
    my $self = shift;
    my %opt = @_;

    return $self->_write_json($self->_get_url('finish'), {
        command => $self->{'command'},
        status  => defined $opt{'status'} ? $opt{'status'} : UNKNOWN,
        stdout  => $opt{'stdout'} || '',
        stderr  => $opt{'stderr'} || ''});
}

# _write_json()
#
# Sends the given object to the Crab server as a JSON message.
#
#   $self->_write_json($self->_get_url($ACTION), $HASHREF);
#
# Dies on failure, and returns 1 on success.  Could be improved
# to return a useful value on success, so long as it is 'true'.

sub _write_json {
    my $self = shift;
    my $url = shift;
    my $obj = shift;

    my $ua = new LWP::UserAgent();
    my $req = new HTTP::Request(PUT => $url);
    $req->content(encode_json($obj));
    my $res = $ua->request($req);
    die $res->status_line() unless $res->is_success();
    return 1;
}

# _get_url()
#
# Returns the URL to be used for a given Crab aaction.
#
#     my $url = $self->_get_url($ACTION);
#
# Where the action is typically 'start' or 'finish'.

sub _get_url {
    my $self = shift;
    my $action = shift;

    my @path = ($self->{'hostname'}, $self->{'username'});
    push @path, $self->{'id'} if defined $self->{'id'};

    return 'http://' . $self->{'server'} . ':' . $self->{'port'} . '/' .
           join('/', 'api', '0', $action, @path);
}

1;

__END__

=back

=head1 AUTHOR

Graham Bell <g.bell@jach.hawaii.edu>

=head1 COPYRIGHT

Copyright (C) 2012 Science and Technology Facilities Council.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
