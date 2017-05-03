import time
import numpy as np

try:
    import torch
    import torch.autograd as torch_autograd
except ImportError:
    torch = None
    torch_autograd = None


def to_float(val):
    """ Check that val is one of the following:
    - pytorch autograd Variable with one element
    - pytorch tensor with one element
    - numpy array with one element
    - any type supporting float() operation
    And convert val to float
    """

    if isinstance(val, np.ndarray):
        assert val.size == 1, \
            "val should have one element (got {})".format(val.size)
        return float(val.squeeze()[0])

    if torch is not None:
        if isinstance(val, torch_autograd.Variable):
            val = val.data
        if torch.is_tensor(val):
            assert torch.numel(val) == 1, \
                "val should have one element (got {})".format(torch.numel(val))
            return float(val.squeeze()[0])

    try:
        return float(val)
    except:
        raise TypeError("Unsupported type for val ({})".format(type(val)))

from future.utils import viewitems


class BaseTimer_(object):
    def __init__(self):
        super(BaseTimer_, self).__init__()
        self.reset()

    def reset(self):
        self.start_time = time.time()
        self.end_time = self.start_time

    def update(self, val=None, n=None, timed=None):
        """ 'val' and 'timed' are redundant here in order to have
        a common interface for all metrics.
        """
        if val is not None:
            self.end_time = to_float(val)
        elif timed is not None:
            self.end_time = to_float(timed)
        else:
            self.end_time = time.time()

    def get(self):
        return self.end_time - self.start_time


class BaseMetric_(object):
    def __init__(self, name, tag):
        """ Basic metric
        Includes a timer.
        """
        self.tag = tag
        self.name = name
        self.timer = BaseTimer_()

    def reset(self):
        raise NotImplementedError("reset should be re-implemented "
                                  "for each metric")

    def update(self, val, n=None, timed=None):
        raise NotImplementedError("update should be re-implemented "
                                  "for each metric")

    def get(self):
        raise NotImplementedError("get should be re-implemented "
                                  "for each metric")


class SimpleMetric_(BaseMetric_):
    def __init__(self, name, tag):
        """ Stores a value and elapsed time
        since last update and last reset
        """
        super(SimpleMetric_, self).__init__(name, tag)
        self.reset()

    def reset(self):
        self.val = 0.

    def update(self, val, n=None, timed=None):
        self.val = to_float(val)
        self.timer.update(timed)

    def get(self):
        return self.val


class TimeMetric_(BaseMetric_):
    def __init__(self, name, tag):
        """ Stores elapsed time since last update and last reset
        """
        super(TimeMetric_, self).__init__(name, tag)

    def reset(self):
        self.timer.reset()

    def update(self, val=None, n=None, timed=None):
        self.timer.update(val, n, timed)

    def get(self):
        return self.timer.get()


class Accumulator_(BaseMetric_):
    """
    Accumulator.
    Credits to the authors of pytorch/tnt for this.
    """
    def __init__(self, name, tag):
        super(Accumulator_, self).__init__(name, tag)
        self.reset()

    def reset(self):
        self.acc = 0
        self.count = 0
        self.const = 0

    def set_const(self, const):
        self.const = to_float(const)

    def update(self, val, n=1, timed=None):
        self.acc += to_float(val) * n
        self.count += n
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


class ParentWrapper_(object):
    def __init__(self, children):
        super(ParentWrapper_, self).__init__()
        self.children = dict()
        for child in children:
            self.children[child.name] = child

    def update(self, n=1, timed=None, **kwargs):
        for (key, value) in kwargs.items():
            self.children[key].update(value, n, timed)

    def reset(self):
        for child in self.children.values():
            child.reset()

    def get(self):
        res = dict()
        for (name, child) in viewitems(self.children):
            res[name] = child.get()
        return res
