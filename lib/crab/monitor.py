from time import sleep
from threading import Thread

from crab import CrabError, CrabStatus

class CrabMonitor(Thread):
    def __init__(self, store):
        Thread.__init__(self)

        self.store = store

    def run(self):
        while True:
            print "*** hello from CrabMonitor ***"
            sleep(10)

