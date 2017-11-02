import numpy as np

from future.utils import viewitems

from .indexer import TimeIndexer_, ValueIndexer_
from .utils import to_float


class BaseMetric_(object):
    def __init__(self, name, tag, time_idx):
        """ Basic metric
        Includes a timer.
        """
        self.tag = tag
        self.name = name
        if time_idx:
            self.index = TimeIndexer_()
        else:
            self.index = ValueIndexer_()
        self.time_idx = time_idx
        self.reset_hooks()

    def reset_hooks(self):
        self.hooks = ()

    def add_hook(self, hook):
        self.hooks += (hook,)

    def hook(self):
        for hook in self.hooks:
            hook()

    def reset(self):
        raise NotImplementedError("reset should be re-implemented "
                                  "for each metric")

    def update(self, val, n=None, idx=None):
        raise NotImplementedError("update should be re-implemented "
                                  "for each metric")

    def get(self):
        raise NotImplementedError("get should be re-implemented "
                                  "for each metric")

    def name_id(self):
        if self.tag == "default":
            name_id = self.name
        else:
            name_id = "{}_{}".format(self.name, self.tag)
        name_id = name_id.lower()
        return name_id


class SimpleMetric_(BaseMetric_):
    def __init__(self, name, tag, time_idx=True):
        """ Stores a value and elapsed time
        since last update and last reset
        """
        super(SimpleMetric_, self).__init__(name, tag, time_idx)
        self.reset()

    def reset(self):
        self.val = 0.

    def update(self, val, n=None, idx=None):
        self.val = to_float(val)
        self.index.update(idx)
        self.hook()

    def get(self):
        return self.val


class TimeMetric_(BaseMetric_):
    def __init__(self, name, tag):
        """ Stores elapsed time since last update and last reset
        """
        super(TimeMetric_, self).__init__(name, tag, time_idx=True)
        self.timer = TimeIndexer_()

    def reset(self):
        self.timer.reset()

    def update(self, val=None, n=None, idx=None):
        self.timer.update(val)
        self.index.update(idx)
        self.hook()

    def get(self):
        return self.timer.get()


class BestMetric_(BaseMetric_):
    def __init__(self, name, tag, mode='max', time_idx=True):
        assert mode in ('min', 'max')
        super(BestMetric_, self).__init__(name, tag, time_idx)
        self.mode = 1 if mode == 'max' else -1
        self.reset()

    def reset(self):
        self.val = -self.mode * np.inf

    def update(self, val, n=None, idx=None):
        val = to_float(val)
        if self.mode * val > self.mode * self.val:
            self.val = val
            self.hook()
        self.index.update(idx)

    def get(self):
        return self.val


class Accumulator_(BaseMetric_):
    """
    Accumulator.
    Credits to the authors of pytorch/tnt for this.
    """
    def __init__(self, name, tag, time_idx=True):
        super(Accumulator_, self).__init__(name, tag, time_idx)
        self.reset()

    def reset(self):
        self.acc = 0
        self.count = 0
        self.const = 0

    def set_const(self, const):
        self.const = to_float(const)

    def update(self, val, n=1, idx=None):
        self.acc += to_float(val) * n
        self.count += n
        self.index.update(idx)
        self.hook()

    def get(self):
        raise NotImplementedError("Accumulator should be subclassed")


class AvgMetric_(Accumulator_):
    def __init__(self, name, tag, time_idx=True):
        super(AvgMetric_, self).__init__(name, tag, time_idx)

    def get(self):
        return self.const + self.acc * 1. / self.count


class SumMetric_(Accumulator_):
    def __init__(self, name, tag, time_idx=True):
        super(SumMetric_, self).__init__(name, tag, time_idx)

    def get(self):
        return self.const + self.acc


class ParentWrapper_(BaseMetric_):
    def __init__(self, name, tag, children, time_idx=True):
        super(ParentWrapper_, self).__init__(name, tag, time_idx)
        self.children = dict()
        for child in children:
            self.children[child.name] = child

    def update(self, n=1, idx=None, **kwargs):
        for (key, value) in kwargs.items():
            self.children[key].update(value, n, idx)

    def reset(self):
        for child in self.children.values():
            child.reset()

    def get(self):
        res = dict()
        for (name, child) in viewitems(self.children):
            res[name] = child.get()
        return res


class DynamicMetric_(BaseMetric_):
    def __init__(self, name, tag, fun=None, time_idx=True):
        """
        """
        super(DynamicMetric_, self).__init__(name, tag, time_idx)
        self.reset()
        if fun is not None:
            self.set_fun(fun)

    def reset(self):
        self.fun = lambda: None
        self.val = None

    def update(self, idx=None):
        self.val = self.fun()
        self.index.update(idx)
        self.hook()

    def set_fun(self, fun):
        self.fun = fun

    def get(self):
        return self.val
