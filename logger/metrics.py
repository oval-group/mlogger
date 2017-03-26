import time


class TimeMetric_(object):

    def __init__(self, name, tag):

        self.tag = tag
        self.name = name
        self.reset()
        self.timer = self

    def reset(self):

        self.start_time = time.time()
        self.end_time = self.start_time

    def update(self, value=None, n=None, timed=None):
        """ heavy interface so that interface is common with
        other metrics...
        """

        if value is not None:
            self.end_time = value
        elif timed is not None:
            self.end_time = timed
        else:
            self.end_time = time.time()

    def get(self):

        return self.end_time - self.start_time


class Accumulator_(object):
    """
    Accumulator.
    Credits to the authors of the ImageNet example of pytorch for this.
    """
    def __init__(self, name, tag):

        self.tag = tag
        self.name = name
        self.timer = TimeMetric_(name='timer', tag='{}_{}'.format(tag, name))
        self.reset()

    def reset(self):

        self.acc = 0
        self.count = 0
        self.const = 0

    def update(self, val, n=1, timed=None):

        self.acc += val * n
        self.count += n
        self.timer.update(timed)

    def set_constant(self, val, timed=None):

        self.const = val
        self.timer.update(timed)

    def get(self):

        raise NotImplementedError("Accumulator should be subclassed")


class AvgMetric_(Accumulator_):

    def __init__(self, name, tag):

        super(AvgMetric_, self).__init__(name, tag)

    def get(self):

        return self.const + self.acc * 1. / self.count


class SumMetric_(Accumulator_):

    def __init__(self, name, tag):

        super(SumMetric_, self).__init__(name, tag)

    def get(self):

        return self.const + self.acc


class ParentMetric_(object):

    def __init__(self, children):

        super(ParentMetric_, self).__init__()

        self.children = dict()
        for child in children:
            self.children[child.name] = child

    def update(self, n=1, timed=None, **kwargs):

        for (key, value) in kwargs.iteritems():
            self.children[key].update(value, n, timed)

    def set_constant(self, **kwargs):

        for (key, value) in kwargs.iteritems():
            self.children[key].set_constant(value)

    def reset(self):

        for child in self.children.itervalues():
            child.reset()

    def get(self):

        res = dict()
        for (name, child) in self.children.iteritems():
            res[name] = child.get()

        return res
