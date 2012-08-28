# Copyright (C) 2012 Science and Technology Facilities Council.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re

def remove_quotes(value):
  """If the given string starts and ends with matching quote marks,
  remove them from the returned value."""

  if (value.startswith("'") and value.endswith("'")) \
  or (value.startswith('"') and value.endswith('"')):
      return value[1:-1]
  else:
      return value

def quote_multiword(value):
    """If the given string contains space characters, return it
    surrounded by double quotes, otherwise return the original string."""

    if value.find(' ') != -1:
        return '"' + value + '"'
    else:
        return value

def split_quoted_word(value):
    """Splits the given string on the first word boundary, unless it starts
    with a quote.

    If quotes are present it splits at the first matching quote. Eg.:

    >>> split_quoted_word('alpha bravo charlie delta echo')
    ['alpha', 'bravo charlie delta echo']
    >>> split_quoted_word('"alpha bravo" charlie delta echo')
    ('alpha bravo', 'charlie delta echo')

    Does not handle escaped quotes within the string."""

    if value.startswith("'"):
        (a, b) = value[1:].split("'", 1)
    elif value.startswith('"'):
        (a, b) = value[1:].split('"', 1)
    else:
        return value.split(None, 1)

    return (a, b.lstrip())

def alphanum(value):
    """Removes all non-alphanumeric characters from the string,
    replacing them with underscores."""

    return re.sub('[^a-zA-Z0-9]', '_', value)

def mergelines(text):
    """Merges the lines of a string by removing newline characters."""

    output = ''
    for line in text.split('\n'):
        output = output + line.strip()
    return output
