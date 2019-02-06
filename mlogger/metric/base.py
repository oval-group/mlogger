import numpy as np
import time

from collections import defaultdict, OrderedDict
from future.utils import viewitems

from .history import History
from .to_float import to_float


class Base(object):
    def __init__(self, time_indexing=None, plotter=None, plot_title=None, plot_legend=None):
        """ Basic metric
        """

        self._time_indexing = time_indexing

        self.init_history(time_indexing)
        self.reset()
        self.reset_hooks_on_update()
        self.reset_hooks_on_log()

        if plotter is not None:
            assert plot_title is not None, "a plot title is required"
            self.plot_on(plotter, plot_title, plot_legend)
        else:
            self._plotter = plotter
            self._plot_title = plot_title
            self._plot_legend = plot_legend

    def init_history(self, time_indexing):
        self._history = History(time_indexing)

    def reset_hooks_on_update(self):
        self.hooks_on_update = ()

    def reset_hooks_on_log(self):
        self.hooks_on_log = ()

    def hook_on_update(self, hook):
        self.hooks_on_update += (hook,)

    def hook_on_log(self, hook):
        self.hooks_on_log += (hook,)

    def reset(self):
        raise NotImplementedError("reset should be re-implemented for each metric")

    def _update(self, *args, **kwargs):
        raise NotImplementedError("_update should be re-implemented for each metric")

    def __repr__(self):
        raise NotImplementedError("__repr__ should be re-implemented for each metric")

    def state_dict_extra(self, state):
        raise NotImplementedError("state_dict_extra should be re-implemented for each metric")

    def load_state_dict_extra(self, state):
        raise NotImplementedError("load_state_dict_extra should be re-implemented for each metric")

    @property
    def value(self):
        raise NotImplementedError("value should be re-implemented for each metric")

    def update(self, *args, **kwargs):
        self._update(*args, **kwargs)
        for hook in self.hooks_on_update:
            hook()
        return self

    def log(self, time=None):
        # get current value
        value = self.value

        event_time = time if time is not None else self._history.time()

        self._history.log(event_time, value)

        # plot current value
        if self._plotter is not None:
            self._plotter._update_xy(title=self._plot_title, legend=self._plot_legend, x=event_time, y=value)

        for hook in self.hooks_on_log:
            hook()

        return self

    def state_dict(self):
        state = {}
        state['repr'] = repr(self)
        state['history'] = self._history.state_dict()
        state['plot_title'] = self._plot_title
        state['plot_legend'] = self._plot_legend
        self.state_dict_extra(state)
        return state

    def load_state_dict(self, state):
        self._history.load_state_dict(state['history'])
        self._plot_title = state['plot_title']
        self._plot_legend = state['plot_legend']
        self.load_state_dict_extra(state)

    def last_logged(self):
        return self._history._last_value

    def plot_on(self, plotter, plot_title, plot_legend=None):
        # plot current state
        x, y = self._history._times, self._history._values
        assert len(x) == len(y)
        if len(x):
            plotter._update_xy(plot_title, plot_legend, x, y)

        # store for future logs
        self._plotter = plotter
        self._plot_title = plot_title
        self._plot_legend = plot_legend

        return self
