import numpy as np
import time

from collections import defaultdict, OrderedDict
from future.utils import viewitems

from .base import Base
from .to_float import to_float


__all__ = [
    "Simple", "TNT", "Timer", "Maximum", "Minimum", "Average", "Sum"
]


class Simple(Base):
    def __init__(self, time_indexing=None, plotter=None, plot_title=None, plot_legend=None):
        super(Simple, self).__init__(time_indexing, plotter, plot_title, plot_legend)

    def reset(self):
        self._val = 0.
        return self

    def _update(self, val, n=None):
        self._val = to_float(val)

    def state_dict_extra(self, state):
        state['val'] = self._val

    def load_state_dict_extra(self, state):
        self._val = to_float(state['val'])

    @property
    def value(self):
        return self._val

    def __repr__(self):
        repr_ = "Simple({time_indexing}, {plotter}, '{plot_title}', '{plot_legend}')"
        repr_ = repr_.format(time_indexing=self._time_indexing,
                             plotter=None,
                             plot_title=self._plot_title,
                             plot_legend=self._plot_legend)
        return repr_


class TNT(Base):
    def __init__(self, tnt_meter, time_indexing=None, plotter=None, plot_title=None, plot_legend=None):
        super(TNT, self).__init__(time_indexing, plotter, plot_title, plot_legend)
        self._tnt_meter = tnt_meter

    def reset(self):
        self._tnt_meter.reset()
        return self

    def _update(self, *args, **kwargs):
        self._tnt_meter.add(*args, **kwargs)

    @property
    def value(self):
        return self._tnt_meter.value()

    def __repr__(self):
        repr_ = "TNT({tnt_meter}, {time_indexing}, {plotter}, '{plot_title}', '{plot_legend}')"
        repr_ = repr_.format(tnt_meter=repr(self._tnt_meter),
                             time_indexing=self._time_indexing,
                             plotter=None,
                             plot_title=self._plot_title,
                             plot_legend=self._plot_legend)
        return repr_


class Timer(Base):
    def __init__(self, plotter=None, plot_title=None, plot_legend=None):
        super(Timer, self).__init__(False, plotter, plot_title, plot_legend)

    def reset(self):
        self.start = time.time()
        self.current = self.start
        return self

    def _update(self, current_time=None):
        if current_time is not None:
            self.current = to_float(current_time)
        else:
            self.current = time.time()

    @property
    def value(self):
        return self.current - self.start

    def state_dict_extra(self, state):
        state['start'] = self.start
        state['current'] = self.current

    def load_state_dict_extra(self, state):
        self.start = state['start']
        self.current = state['current']

    def __repr__(self):
        repr_ = "Timer({plotter}, '{plot_title}', '{plot_legend}')"
        repr_ = repr_.format(plotter=None,
                             plot_title=self._plot_title,
                             plot_legend=self._plot_legend)
        return repr_


class Maximum(Base):
    def __init__(self, time_indexing=None, plotter=None, plot_title=None, plot_legend=None):
        super(Maximum, self).__init__(time_indexing, plotter, plot_title, plot_legend)

    def reset(self):
        self._val = -np.inf
        self.hooks_on_new_max = ()
        return self

    def _update(self, val, n=None):
        val = to_float(val)
        if val > self._val:
            self._val = val
            for hook in self.hooks_on_new_max:
                hook()

    def hook_on_new_max(self, hook):
        self.hooks_on_new_max += (hook,)

    def state_dict_extra(self, state):
        state['val'] = self._val

    def load_state_dict_extra(self, state):
        self._val = to_float(state['val'])

    @property
    def value(self):
        return self._val

    def __repr__(self):
        repr_ = "Maximum({time_indexing}, {plotter}, '{plot_title}', '{plot_legend}')"
        repr_ = repr_.format(time_indexing=self._time_indexing,
                             plotter=None,
                             plot_title=self._plot_title,
                             plot_legend=self._plot_legend)
        return repr_


class Minimum(Base):
    def __init__(self, time_indexing=None, plotter=None, plot_title=None, plot_legend=None):
        super(Minimum, self).__init__(time_indexing, plotter, plot_title, plot_legend)

    def reset(self):
        self._val = np.inf
        self.hooks_on_new_min = ()
        return self

    def _update(self, val, n=None):
        val = to_float(val)
        if val < self._val:
            self._val = val
            for hook in self.hooks_on_new_min:
                hook()

    def hook_on_new_min(self, hook):
        self.hooks_on_new_min += (hook,)

    def state_dict_extra(self, state):
        state['val'] = self._val

    def load_state_dict_extra(self, state):
        self._val = to_float(state['val'])

    @property
    def value(self):
        return self._val

    def __repr__(self):
        repr_ = "Minimum({time_indexing}, {plotter}, '{plot_title}', '{plot_legend}')"
        repr_ = repr_.format(time_indexing=self._time_indexing,
                             plotter=None,
                             plot_title=self._plot_title,
                             plot_legend=self._plot_legend)
        return repr_


class Accumulator_(Base):
    """
    Credits to the authors of pytorch/tnt for this.
    """
    def __init__(self, time_indexing, plotter=None, plot_title=None, plot_legend=None):
        super(Accumulator_, self).__init__(time_indexing, plotter, plot_title, plot_legend)

    def reset(self):
        self._avg = 0
        self._total_weight = 0
        return self

    def _update(self, val, weighting=1):
        val, weighting = to_float(val), to_float(weighting)
        assert weighting > 0
        r = self._total_weight / (weighting + self._total_weight)
        self._avg = r * self._avg + (1 - r) * val
        self._total_weight += weighting

    def state_dict_extra(self, state):
        state['avg'] = self._avg
        state['total_weight'] = self._total_weight

    def load_state_dict_extra(self, state):
        self._avg = state['avg']
        self._total_weight = state['total_weight']

    @property
    def value(self):
        raise NotImplementedError("Accumulator should be subclassed")


class Average(Accumulator_):
    def __init__(self, time_indexing=None, plotter=None, plot_title=None, plot_legend=None):
        super(Average, self).__init__(time_indexing, plotter, plot_title, plot_legend)

    @property
    def value(self):
        return self._avg

    def __repr__(self):
        repr_ = "Average({time_indexing}, {plotter}, '{plot_title}', '{plot_legend}')"
        repr_ = repr_.format(time_indexing=self._time_indexing,
                             plotter=None,
                             plot_title=self._plot_title,
                             plot_legend=self._plot_legend)
        return repr_


class Sum(Accumulator_):
    def __init__(self, time_indexing=None, plotter=None, plot_title=None, plot_legend=None):
        super(Sum, self).__init__(time_indexing, plotter, plot_title, plot_legend)

    @property
    def value(self):
        return self._avg * self._total_weight

    def __repr__(self):
        repr_ = "Sum({time_indexing}, {plotter}, '{plot_title}', '{plot_legend}')"
        repr_ = repr_.format(time_indexing=self._time_indexing,
                             plotter=None,
                             plot_title=self._plot_title,
                             plot_legend=self._plot_legend)
        return repr_
