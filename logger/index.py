import time

from .utils import to_float


class Index_(object):
    def __init__(self):
        super(Index_, self).__init__()
        self.reset()

    def reset(self):
        raise NotImplementedError

    def update(self):
        raise NotImplementedError

    def get(self):
        return self.current - self.start


class TimeIndex_(Index_):
    def __init__(self):
        super(TimeIndex_, self).__init__()
        self.reset()

    def reset(self):
        self.start = time.time()
        self.current = self.start

    def update(self, timed=None):
        if timed is not None:
            self.current = to_float(timed)
        else:
            self.current = time.time()


class ValueIndex_(Index_):
    def __init__(self):
        super(ValueIndex_, self).__init__()
        self.reset()

    def reset(self, start=0):
        start = to_float(start)
        self.start = start
        self.current = self.start

    def update(self, val=None):
        if val is not None:
            self.current = to_float(val)
        else:
            self.current += 1
