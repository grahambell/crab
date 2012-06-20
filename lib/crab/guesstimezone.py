import pytz

# There really ought to be a better way of doing this!  You could read
# /etc/sysconfig/clock but that would only work on certain systems.  The
# following might work anywhere the timezone database is installed in the
# correct place.  If the environment variable TZ is set, then it should
# be used instead of calling this.
#
# The Perl module DateTime::TimeZone::Local::Unix uses this method, among
# others.  TODO: implement some of the other methods.

def guess_timezone():
    """Function to try to determine the operating system's timezone setting.

    Currently this reads /etc/localtime and tries to find the file in
    /usr/share/zoneinfo which matches.  It uses pytz to get a list of
    common timezones to try."""

    try:
        f = open('/etc/localtime')
        localtime = f.read()
        f.close()
    except:
        return None

    for zone in pytz.common_timezones:
        try:
            f = open('/usr/share/zoneinfo/' + zone)
            timezone = f.read()
            f.close()

            if timezone == localtime:
                return zone

        except:
            pass

    return None
