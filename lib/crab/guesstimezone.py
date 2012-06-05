import pytz

# There really ought to be a better way of doing this!  You could read
# /etc/sysconfig/clock but that would only work on certain systems.  The
# following might work anywhere the timezone database is installed in the
# correct place.  If the environment variable TZ is set, then it should
# be used instead of calling this.

def guess_timezone():
    try:
        f = open('/etc/localtime')
        localtime = f.read()
        f.close()

        for zone in pytz.common_timezones:
            f = open('/usr/share/zoneinfo/' + zone)
            timezone = f.read()
            f.close()

            if timezone == localtime:
                return zone

    except:
        pass

    return None
