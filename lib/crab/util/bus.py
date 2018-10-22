# Copyright (C) 2018 East Asian Observatory.
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


def priority(level):
    """Decorator to set the priority attribute of a function."""

    def decorator(f):
        f.priority = level
        return f
    return decorator


class CrabStoreListener:
    """Base class for plugins which require a store.

    Listens on the "crab-store" channel, setting the instance value "store"
    to the store object received."""

    def __init__(self, bus):
        self.bus = bus
        self.store = None

    def subscribe(self):
        self.bus.subscribe('crab-store', self.__store)

    def __store(self, store):
        self.store = store


class CrabPlugin(CrabStoreListener):
    """Class to launch Crab services as CherryPy plugins.

    This class subscribes to the "start" channel.  When it recieves a message,
    it constructs an instance of the service class and publishes it on the
    "crab-service" channel."""

    def __init__(self, bus, name, class_, **kwargs):
        super(CrabPlugin, self).__init__(bus)

        self.name = name
        self.class_ = class_
        self.kwargs = kwargs

    def subscribe(self):
        super(CrabPlugin, self).subscribe()

        self.bus.subscribe('start', self.start)

        # If the service takes a "notify" argument (specified as notify=None)
        # then also subscribe to the "crab-notify" channel.
        if self.kwargs.get('notify', ()) is None:
            self.bus.subscribe('crab-notify', self.notify)

    @priority(71)
    def start(self):
        self.bus.log('Starting Crab service "{}"'.format(self.name))
        service = self.class_(store=self.store, **self.kwargs)
        service.daemon = True
        service.start()

        self.bus.publish('crab-service', self.name, service)

    def notify(self, notify):
        self.kwargs['notify'] = notify
