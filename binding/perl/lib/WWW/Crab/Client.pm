=head1 NAME

WWW::Crab::Client - Crab client library

=head1 SYNOPSIS

  use WWW::Crab::Client;

  my $crab = new WWW::Crab::Client();

  $crab->start();

  # Perform the cron job actions ...

  $crab->finish(status => WWW::Crab::Client::SUCCESS);

=head1 DESCRIPTION

This module implements a subset of the Crab protocol sufficient
for reporting the status of a cron job to the Crab server.
It is intended to work similarly to the Python Crab client module,
but be more convient for cron jobs written in Perl.

=cut

package WWW::Crab::Client;

use strict;

use Config::IniFiles;
use HTTP::Request;
use JSON;
use LWP::UserAgent;
use Sys::Hostname;

our $VERSION = 0.01;

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
        $homedir, undef, undef) = getpwuid($<);

    my $conf = new Config::IniFiles(-file => \'', -allowempty => 1);
    my $conf_system = '/etc/crab/crab.ini';
    my $conf_user = $homedir . '/.crab/crab.ini';

    $conf = new Config::IniFiles(-file => $conf_system, '-import' => $conf)
        if (-e $conf_system);

    $conf = new Config::IniFiles(-file => $conf_user, '-import' => $conf)
        if (-e $conf_user);

    my $self = {
        id       => $opt{'id'}       || undef,
        command  => $opt{'command'}  || $0,
        server   => $opt{'server'}   || $conf->val('server', 'host',
                                            $ENV{'CRABHOST'} || 'localhost'),
        port     => $opt{'port'}     || $conf->val('server', 'port',
                                            $ENV{'CRABPORT'} || 8000),
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

=cut

sub start {
    my $self = shift;

    $self->_write_json($self->_get_url('start'), {
        command => $self->{'command'}});
}

=item finish()

Reports that the job has finished.  If the status is not specified,
UNKNOWN will be sent.

  $crab->finish(status => WWW::Crab::Client::SUCCESS,
                stdout => $command_output,
                stderr => $error_message);

=cut

sub finish {
    my $self = shift;
    my %opt = @_;

    $self->_write_json($self->_get_url('finish'), {
        command => $self->{'command'},
        status  => defined $opt{'status'} ? $opt{'status'} : UNKNOWN,
        stdout  => $opt{'stdout'} || '',
        stderr  => $opt{'stderr'} || ''});
}

sub _write_json {
    my $self = shift;
    my $url = shift;
    my $obj = shift;

    my $ua = new LWP::UserAgent();
    my $req = new HTTP::Request(PUT => $url);
    $req->content(encode_json($obj));
    my $res = $ua->request($req);
    die $res->status_line() unless $res->is_success();
}

sub _get_url {
    my $self = shift;
    my $action = shift;

    my @path = ($self->{'hostname'}, $self->{'username'});
    push @path, $self->{'id'} if defined $self->{'id'};

    return 'http://' . $self->{'server'} . ':' . $self->{'port'} . '/' .
           join('/', 'api', '0', $action, @path);
}

1;

=back
