from collections import defaultdict


class TextWindow(object):
    def __init__(self, plotter, title, opts=None):
        self.plotter = plotter
        self.opts = opts if opts is not None else {}
        self.opts['title'] = title
        self._visdom_window = None
        self.create_on_visdom()
        self.cache = DataDictCache()

    def create_on_visdom(self):
        window = self.plotter.viz.text("")
        if window is False:
            self._visdom_window = None
        else:
            self._visdom_window = window

    def update(self, data_dict):
        self.cache.update(data_dict)
        if not self.plotter.manual_update:
            self.update_plot()

    def update_plot(self):
        # window not yet created on visdom
        if self._visdom_window is None:
            self.create_on_visdom()

        # window creation failed, abort
        if self._visdom_window is None:
            return

        if self.cache.is_empty:
            return

        # plot data
        plotted = self.plotter.viz.text(
            text=self.cache.text, win=self._visdom_window,
            append=True)

        # clear cache if plotting did not fail
        if plotted is not False:
            self.cache.clear()

    def state_dict(self):
        return {}

    def load_state_dict(self, state):
        pass


class DataDictCache(object):
    def __init__(self):
        self.clear()

    def clear(self):
        self._data = {}

    def update(self, data_dict):
        self._data.update(data_dict)

    @property
    def text(self):
        return "<br />".join(
            ["{key}: {value}".format(key=str(k), value=v)
             for (k, v) in sorted(self._data.items(), key=lambda x: x[0])])

    @property
    def is_empty(self):
        return len(self._data) == 0
