import numpy as np
import time
import mlogger

from collections import defaultdict, OrderedDict
from future.utils import viewitems


class History(object):
    def __init__(self, time_indexing):

        self._times = []
        self._values = []

        if time_indexing is None:
            time_indexing = mlogger._time_indexing

        self.time_indexing = time_indexing

        if self.time_indexing:
            self.start_time = time.time()
        else:
            self.start_time = 0

    def time(self):
        # elapsed time since start for time indexing
        if self.time_indexing:
            event_time = time.time() - self.start_time
        # increment by one since last event for increment
        elif len(self._times):
            event_time = self._times[-1] + 1
        # start at 0 for increment
        else:
            event_time = 0

        return event_time

    def log(self, event_time, value):
        self._times.append(event_time)
        self._values.append(value)

        return self

    def state_dict(self):
        state = {}
        state['start_time'] = self.start_time
        state['time_indexing'] = self.time_indexing
        state['times'] = list(self._times)
        state['values'] = list(self._values)

        return state

    def load_state_dict(self, state):

        self.time_indexing = state['time_indexing']
        self.start_time = state['start_time']

        self._times = list(state['times'])
        self._values = list(state['values'])

    @property
    def last_value(self):
        if len(self._values):
            return self._values[-1]
        else:
            return None
