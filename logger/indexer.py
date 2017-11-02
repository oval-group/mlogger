import time

from .utils import to_float


class Indexer_(object):
    def __init__(self):
        super(Indexer_, self).__init__()
        self.reset()

    def reset(self):
        raise NotImplementedError

    def update(self, val=None, n=None, timed=None):
        """ 'val' and 'timed' are redundant here in order to have
        a common interface for all metrics.
        """
        raise NotImplementedError

    def get(self):
        return self.current - self.start


class TimeIndexer_(Indexer_):
    def __init__(self):
        super(TimeIndexer_, self).__init__()
        self.reset()

    def reset(self):
        self.start = time.time()
        self.current = self.start

    def update(self, timed=None):
        """ 'val' and 'timed' are redundant here in order to have
        a common interface for all metrics.
        """
        if timed is not None:
            self.current = to_float(timed)
        else:
            self.current = time.time()


class ValueIndexer_(Indexer_):
    def __init__(self):
        super(ValueIndexer_, self).__init__()
        self.reset()

    def reset(self, start=0):
        start = to_float(start)
        self.start = start
        self.current = self.start

    def update(self, val=None):
        """ 'val' and 'timed' are redundant here in order to have
        a common interface for all metrics.
        """
        if val is not None:
            self.current = to_float(val)
        else:
            self.current += 1
