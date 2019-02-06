from collections import defaultdict

import numpy as np


class GraphWindow(object):
    def __init__(self, plotter, title, opts=None):
        self.plotter = plotter
        self.opts = opts if opts is not None else {}
        self.opts['title'] = title
        self._visdom_window = None
        self.create_on_visdom()
        self.caches = defaultdict(XYCache)

    def create_on_visdom(self):
        window = self.plotter.viz.line(Y=np.array([np.nan]), opts=self.opts)
        # check creation sucess
        if window is False:
            self._visdom_window = None
        else:
            self._visdom_window = window

    def update(self, legend, x, y):
        cache = self.caches[legend]
        cache.update(x, y)
        if not self.plotter.manual_update:
            self.update_plot()

    def update_plot(self):
        # window not yet created on visdom
        if self._visdom_window is None:
            self.create_on_visdom()

        # window creation failed, abort
        if self._visdom_window is None:
            return

        # else plot cached data
        for legend, cache in self.caches.items():
            if cache.is_empty:
                continue

            # plot data
            plotted = self.plotter.viz.line(
                Y=cache.y_array, X=cache.x_array,
                name=legend, win=self._visdom_window,
                update='append')

            # clear cache if plotting did not fail
            if plotted is not False:
                cache.clear()

    def state_dict(self):
        return {'opts': self.opts.copy()}

    def load_state_dict(self, state):
        if 'title' in state['opts']:
            del state['opts']['title']
        self.opts = state['opts']


class XYCache(object):
    def __init__(self):
        self.clear()

    def clear(self):
        self._x = []
        self._y = []

    def update(self, x, y):
        self._x.append(x)
        self._y.append(y)

    def array(self, u):
        u = np.asarray(u)
        u = np.squeeze(u)
        if u.ndim == 0:
            u = u[None]
        return u

    @property
    def x_array(self):
        return self.array(self._x)

    @property
    def y_array(self):
        return self.array(self._y)

    @property
    def is_empty(self):
        return len(self._x) == 0
