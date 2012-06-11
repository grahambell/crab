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
