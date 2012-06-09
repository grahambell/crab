class CrabError(Exception):
    pass

class CrabStatus:
    SUCCESS = 0
    FAIL = 1
    UNKNOWN = 2
    COULDNOTSTART = 3

    VALUES = set([SUCCESS, FAIL, UNKNOWN, COULDNOTSTART])
