import numpy as np

from future.utils import viewitems

from .index import TimeIndex_, ValueIndex_
from .utils import to_float


class BaseMetric_(object):
    def __init__(self, name, tag, time_idx, to_plot):
        """ Basic metric
        """
        self.tag = tag
        self.name = name
        if time_idx:
            self.index = TimeIndex_()
        else:
            self.index = ValueIndex_()
        self.time_idx = time_idx
        self.to_plot = to_plot
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

    def update(self, val, n=None):
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

    @property
    def value(self):
        return self.get()


class SimpleMetric_(BaseMetric_):
    def __init__(self, name, tag, time_idx, to_plot):
        """ Stores a value and elapsed time
        since last update and last reset
        """
        super(SimpleMetric_, self).__init__(name, tag, time_idx, to_plot)
        self.reset()

    def reset(self):
        self._val = 0.

    def update(self, val, n=None):
        self._val = to_float(val)
        self.hook()
        return self

    def get(self):
        return self._val


class TimeMetric_(BaseMetric_):
    def __init__(self, name, tag, to_plot, time_idx=False):
        """ Stores elapsed time since last update and last reset
        Note: ignores time_idx argument - always indexed by value
        """
        assert not time_idx, "a TimeMetric cannot be indexed by time"
        super(TimeMetric_, self).__init__(name, tag,
                                          time_idx=False,
                                          to_plot=to_plot)
        self._timer = TimeIndex_()

    def reset(self):
        self._timer.reset()

    def update(self, val=None, n=None):
        self._timer.update(val)
        self.hook()
        return self

    def get(self):
        return self._timer.get()


class BestMetric_(BaseMetric_):
    def __init__(self, name, tag, time_idx, to_plot, mode='max'):
        assert mode in ('min', 'max')
        super(BestMetric_, self).__init__(name, tag, time_idx, to_plot)
        self.mode = 1 if mode == 'max' else -1
        self.reset()

    def reset(self):
        self._val = -self.mode * np.inf

    def update(self, val, n=None):
        val = to_float(val)
        if self.mode * val > self.mode * self._val:
            self._val = val
            self.hook()
        return self

    def get(self):
        return self._val


class Accumulator_(BaseMetric_):
    """
    Accumulator.
    Credits to the authors of pytorch/tnt for this.
    """
    def __init__(self, name, tag, time_idx, to_plot):
        super(Accumulator_, self).__init__(name, tag, time_idx, to_plot)
        self.reset()

    def reset(self):
        self.acc = 0
        self.count = 0
        self.const = 0

    def set_const(self, const):
        self.const = to_float(const)

    def update(self, val, n=1):
        self.acc += to_float(val) * n
        self.count += n
        self.hook()
        return self

    def get(self):
        raise NotImplementedError("Accumulator should be subclassed")


class AvgMetric_(Accumulator_):
    def __init__(self, name, tag, time_idx, to_plot):
        super(AvgMetric_, self).__init__(name, tag, time_idx, to_plot)

    def get(self):
        return self.const + self.acc * 1. / self.count


class SumMetric_(Accumulator_):
    def __init__(self, name, tag, time_idx, to_plot):
        super(SumMetric_, self).__init__(name, tag, time_idx, to_plot)

    def get(self):
        return self.const + self.acc


class ParentWrapper_(BaseMetric_):
    def __init__(self, name, tag, children):
        super(ParentWrapper_, self).__init__(name, tag, False, False)
        self.children = dict()
        for child in children:
            self.children[child.name] = child

    def update(self, n=1, **kwargs):
        for (key, value) in kwargs.items():
            self.children[key].update(value, n)
        return self

    def reset(self):
        for child in self.children.values():
            child.reset()

    def get(self):
        res = dict()
        for (name, child) in viewitems(self.children):
            res[name] = child.get()
        return res


class DynamicMetric_(BaseMetric_):
    def __init__(self, name, tag, time_idx, to_plot, fun=None):
        """
        """
        super(DynamicMetric_, self).__init__(name, tag, time_idx, to_plot)
        self.reset()
        if fun is not None:
            self.set_fun(fun)

    def reset(self):
        self.fun = lambda: None
        self._val = None

    def update(self):
        self._val = self.fun()
        self.hook()
        return self

    def set_fun(self, fun):
        self.fun = fun

    def get(self):
        return self._val
