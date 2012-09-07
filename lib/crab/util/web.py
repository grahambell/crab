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

import markupsafe

def abbr(text, limit=60, tolerance=10):
    """Returns an abbreviated and HTML-escaped version of the specified text.

    The text is trimmed to the given length limit, but if a space is found
    within the preceeding 'tolerance' number of characters, then it
    is trimmed there.  The result is an HTML span element with the
    full text as the title, unless it was not necessary to trim it."""

    if len(text) > limit:
        space = text.rfind(' ', limit - tolerance, limit)
        if space == -1:
            shorttext = text[:limit]
        else:
            shorttext = text[:space]

        return ('<span title="' + str(markupsafe.escape(text)) +
                '">' + str(markupsafe.escape(shorttext)) +
                '&hellip;</span>')

    else:
        return str(markupsafe.escape(text))
