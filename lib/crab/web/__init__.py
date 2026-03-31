# Copyright (C) 2012-2014 Science and Technology Facilities Council.
# Copyright (C) 2015-2018 East Asian Observatory.
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

from crab.util.bus import CrabStoreListener


class CrabWebBase(CrabStoreListener):
    def __init__(self, bus):
        super(CrabWebBase, self).__init__(bus)

        self.bus = bus
        self.service = {}
        self.monitor = None

    def subscribe(self):
        super(CrabWebBase, self).subscribe()

        self.bus.subscribe('crab-service', self.__service)

    def __service(self, name, service):
        self.service[name] = service

        if name == 'Monitor':
            self.monitor = service
