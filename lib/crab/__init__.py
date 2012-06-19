class CrabError(Exception):
    pass

class CrabStatus:
    SUCCESS = 0
    FAIL = 1
    UNKNOWN = 2
    COULDNOTSTART = 3

    VALUES = set([SUCCESS, FAIL, UNKNOWN, COULDNOTSTART])

    # Additional internal status values (it is not valid for
    # a client to send these).  Also some of these are less bad
    # than the client statuses.  For example, if something has a 
    # status of FAIL, you don't want to change it to just LATE.
    LATE = -1
    MISSED = -2
    TIMEOUT = -3

    _error_names = ['OK', 'Failed', 'Unknown', 'Could not start']
    _warning_names = ['Late', 'Missed', 'Timed out']

    @staticmethod
    def get_name(status):
        try:
            if status >= 0:
                # TODO: find out if this can be referred to without class name?
                return CrabStatus._error_names[status]
            else:
                return CrabStatus._warning_names[(-1) - status]
        except IndexError:
            return 'Status ' + int(status)

    @staticmethod
    def is_trivial(status):
        return status == CrabStatus.LATE

    @staticmethod
    def is_ok(status):
        return status == CrabStatus.SUCCESS or status == CrabStatus.LATE

    @staticmethod
    def is_warning(status):
        return status == CrabStatus.UNKNOWN or status == CrabStatus.MISSED

    @staticmethod
    def is_error(status):
        return not (CrabStatus.is_ok(status) or CrabStatus.is_warning(status))

class CrabEvent:
    START = 1
    WARN = 2
    FINISH = 3
