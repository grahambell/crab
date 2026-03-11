# Copyright (C) 2026 East Asian Observatory
# All Rights Reserved.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful,but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,51 Franklin
# Street, Fifth Floor, Boston, MA  02110-1301, USA

from locale import getpreferredencoding
from codecs import lookup


default_encoding = 'utf_8'


class CompatCodecInfo:
    """Compatibility class for Python (e.g. 2.4) without CodecInfo."""

    def __init__(self, encode, decode, name):
        self.encode = encode
        self.decode = decode
        self.name = name


def determine_codec(encoding=None, vars=None):
    """Function to try to determine which character encoding to use to read
    information from the system.  Returns either a CodecInfo object or an
    instance of the compatibility class above.

    Uses the first value found from:
        CRABENCODING (in given `vars` dictionary)
        `encoding` (given value, e.g. from a configuration file)
        getpreferredencoding (function from locale package)

    If the chosen encoding can not be looked up, uses:
        utf_8 (default value)

    Note: unless CRABENCODING is set, will call locale.getpreferredencoding
    which is not thread-safe.  Therefore this should be called at start up."""

    if (vars is not None) and ('CRABENCODING' in vars):
        encoding = vars['CRABENCODING']

    elif encoding:
        pass

    else:
        encoding = getpreferredencoding()

    try:
        codec = lookup(encoding)

    except LookupError:
        encoding = default_encoding
        codec = lookup(encoding)

    if hasattr(codec, 'name'):
        return codec

    return CompatCodecInfo(codec[0], codec[1], encoding)
