import numpy as np
import pprint

from collections import defaultdict

# optional visdom
try:
    import visdom
except ImportError:
    visdom = None


class Cache(object):
    def __init__(self):
        self.clear()

    def clear(self):
        self._x = []
        self._y = []

    def update(self, metric):
        self._x.append(metric.index.get())
        self._y.append(metric.get())

    @property
    def x(self):
        return np.array(self._x)

    @property
    def y(self):
        return np.array(self._y)


class Plotter(object):

    def __init__(self, xp, visdom_opts):
        super(Plotter, self).__init__()

        if visdom_opts is None:
            visdom_opts = {}

        assert visdom is not None, "visdom could not be imported"

        # visdom env is given by Experiment name unless specified
        if 'env' not in list(visdom_opts.keys()):
            visdom_opts['env'] = xp.name

        self.viz = visdom.Visdom(**visdom_opts)
        self.windows = {}
        self.append = {}
        self.cache = defaultdict(Cache)

    def _plot_xy(self, name, tag, x, y, time_idx=True):
        """
        Creates a window if it does not exist yet.
        Returns True / non-empty string if data has been sent successfully,
        False otherwise.
        """
        xlabel = 'Time (s)' if time_idx else 'Index'
        if name not in list(self.windows.keys()):
            opts = {'legend': [tag], 'title': name, 'xlabel': xlabel}
            self.windows[name] = self.viz.line(Y=y, X=x, opts=opts)
            return True
        else:
            return self.viz.updateTrace(Y=y, X=x, name=tag,
                                        win=self.windows[name],
                                        append=True)

    def plot_xp(self, xp):

        if 'git_diff' in xp.config.keys():
            config = xp.config.copy()
            config.pop('git_diff')
        self.plot_config(config)

        for tag in sorted(xp.logged.keys()):
            for name in sorted(xp.logged[tag].keys()):
                self.plot_logged(xp.logged, tag, name)

    def plot_logged(self, logged, tag, name):
        xy = logged[tag][name]
        x = np.array(xy.keys()).astype(np.float)
        y = np.array(xy.values())
        time_idx = not np.isclose(x, x.astype(np.int)).all()
        self._plot_xy(name, tag, x, y, time_idx)

    def plot_metric(self, metric):
        name, tag = metric.name, metric.tag
        cache = self.cache[metric.name_id()]
        cache.update(metric)
        sent = self._plot_xy(name, tag, cache.x, cache.y,
                             metric.time_idx)
        # clear cache if data has been sent successfully
        if sent:
            cache.clear()

    def plot_config(self, config):
        # format dictionary with pretty print
        pp = pprint.PrettyPrinter(indent=4)
        msg = pp.pformat(config)
        # display dict on visdom
        self.viz.text(msg)
