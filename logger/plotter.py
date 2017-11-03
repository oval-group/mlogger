import numpy as np
import pprint

# optional visdom
try:
    import visdom
except ImportError:
    visdom = None


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

    def _plot_xy(self, name, tag, x, y, time_idx=True):
        xlabel = 'Time (s)' if time_idx else 'Index'
        if name not in list(self.windows.keys()):
            self.windows[name] = \
                self.viz.line(Y=y, X=x,
                              opts={'legend': [tag],
                                    'title': name,
                                    'xlabel': xlabel})
        else:
            self.viz.updateTrace(Y=y, X=x,
                                 name=tag,
                                 win=self.windows[name],
                                 append=True)

    def plot_xp(self, xp, visdom_opts):
        self.viz = visdom.Visdom(**visdom_opts)

        if 'git_diff' in xp.config.keys():
            config = xp.config.copy().pop('git_diff')
        self.plot_config(config)

        for tag in sorted(xp.logged.keys()):
            for name in sorted(xp.logged[tag].keys()):
                self.plot_logged(xp.logged, tag, name)

    def plot_logged(self, logged, tag, name):
        xy = self.logged[tag][name]
        x = np.array(xy.keys()).astype(np.float)
        y = np.array(xy.values())
        time_idx = not np.isclose(x, x.astype(np.int))
        self._plot_xy(name, tag, x, y, time_idx)

    def plot_metric(self, metric):
        name, tag = metric.name, metric.tag
        x = np.array([metric.index.get()])
        y = np.array([metric.get()])
        self._plot_xy(name, tag, x, y, metric.time_idx)

    def plot_config(self, config):
        # format dictionary with pretty print
        pp = pprint.PrettyPrinter(indent=4)
        msg = pp.pformat(config)
        # display dict on visdom
        self.viz.text(msg)
