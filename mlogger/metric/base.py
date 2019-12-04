import numpy as np
import time
import warnings

from collections import defaultdict, OrderedDict
from future.utils import viewitems

from .history import History
from .to_float import to_float


class Base(object):
    def __init__(self, time_indexing=None, plotter=None, plot_title=None, plot_legend=None,
                 visdom_plotter=None, summary_writer=None):
        """ Basic metric
        """

        self._time_indexing = time_indexing

        self.init_history(time_indexing)
        self.reset()
        self.reset_hooks_on_update()
        self.reset_hooks_on_log()

        if plotter is not None:
            assert visdom_plotter is None
            visdom_plotter = plotter
            del plotter
            warnings.warn("Argument `plotter` is deprecated. Please use `visdom_plotter` instead.", FutureWarning)

        self._summary_writer = summary_writer
        self._visdom_plotter = visdom_plotter
        self._plot_title = plot_title
        self._plot_legend = plot_legend

        if summary_writer is not None:
            assert plot_title is not None, "a plot title is required"
            self.plot_on_tensorboard(summary_writer, plot_title, plot_legend)

        if visdom_plotter is not None:
            assert plot_title is not None, "a plot title is required"
            self.plot_on_visdom(visdom_plotter, plot_title, plot_legend)

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

        # plot current value on visdom
        if self._visdom_plotter is not None:
            self._visdom_plotter._update_xy(title=self._plot_title, legend=self._plot_legend, x=event_time, y=value)

        # plot current value on tensorboard
        if self._summary_writer is not None:
            if self._plot_legend:
                tag = "{title}/{legend}".format(title=self._plot_title, legend=self._plot_legend)
            else:
                tag = self._plot_title

            if self._time_indexing:
                opts = dict(global_step=len(self._history._times), walltime=event_time)
            else:
                opts = dict(global_step=event_time)

            self._summary_writer.add_scalar(tag=tag, scalar_value=value, **opts)

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
        warnings.warn("Argument `plotter` is deprecated. Please use `visdom_plotter` instead.", FutureWarning)
        self.plot_on_visdom(plotter, plot_title, plot_legend)

    def plot_on_visdom(self, visdom_plotter, plot_title, plot_legend=None):
        # plot current state
        x, y = self._history._times, self._history._values
        assert len(x) == len(y)
        if len(x):
            visdom_plotter._update_xy(plot_title, plot_legend, x, y)

        # store for future logs
        self._visdom_plotter = visdom_plotter
        self._plot_title = plot_title
        self._plot_legend = plot_legend

        return self

    def plot_on_tensorboard(self, summary_writer, plot_title, plot_legend=None):
        # plot current state
        x, y = self._history._times, self._history._values
        assert len(x) == len(y)
        if plot_legend:
            tag = "{title}/{legend}".format(title=plot_title, legend=plot_legend)
        else:
            tag = plot_title
        for i, (x_scalar, y_scalar) in enumerate(zip(x, y)):
            if self._time_indexing:
                opts = dict(global_step=i, walltime=x_scalar)
            else:
                opts = dict(global_step=x_scalar)
            summary_writer.add_scalar(tag=tag, scalar_value=y_scalar, **opts)

        # store for future logs
        self._summary_writer = summary_writer
        self._plot_title = plot_title
        self._plot_legend = plot_legend

        return self
