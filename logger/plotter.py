import numpy as np
import pprint

# optional visdom
try:
    import visdom
except ImportError:
    visdom = None


class Plotter(object):

    def __init__(self, visdom_opts):
        super(Plotter, self).__init__()

        if visdom_opts is None:
            visdom_opts = {}

        assert visdom is not None, "visdom could not be imported"
        # visdom env is given by Experiment name unless specified
        if 'env' not in list(visdom_opts.keys()):
            visdom_opts['env'] = self.name
        self.viz = visdom.Visdom(**visdom_opts)
        self.viz_dict = {}

    def register_metric(self, metric):
        xlabel = "Time (s)" if metric.indexing == 'time' else ""
        self.viz_dict[metric.name] = \
            self.viz.line(Y=[0], X=[0],
                          opts={'legend': [metric.tag],
                                'title': metric.name,
                                'xlabel': xlabel})

    def plot_xp(self, xp, visdom_opts):
        self.viz = visdom.Visdom(**visdom_opts)
        # format dictionary with pretty print
        pp = pprint.PrettyPrinter(indent=4)
        config = self.config.copy()
        if 'git_diff' in config.keys():
            config.pop('git_diff')
        msg = pp.pformat(config)
        # display dict on visdom
        self.viz.text(msg)
        for tag in sorted(self.logged.keys()):
            for name in sorted(self.logged[tag].keys()):
                xy = self.logged[tag][name]
                x = np.array(xy.keys()).astype(np.float)
                y = np.array(xy.values())
                if name not in list(self.viz_dict.keys()):
                    self.viz_dict[name] = \
                        self.viz.line(Y=y, X=x,
                                      opts={'legend': [tag],
                                            'title': name,
                                            'xlabel': 'Time (s)'})
                else:
                    self.viz.updateTrace(Y=y, X=x,
                                         name=tag,
                                         win=self.viz_dict[name],
                                         append=True)

    def plot_metric(self, metric):
        name, tag = metric.name, metric.tag
        x = np.array([metric.timer.get()])
        y = np.array([metric.get()])
        if name not in list(self.viz_dict.keys()):
            self.viz_dict[name] = \
                self.viz.line(Y=y, X=x,
                              opts={'legend': [tag],
                                    'title': name,
                                    'xlabel': 'Time (s)'})
        else:
            self.viz.updateTrace(Y=y, X=x,
                                 name=tag,
                                 win=self.viz_dict[name],
                                 append=True)

    def plot_config(self, config):
        # format dictionary with pretty print
        pp = pprint.PrettyPrinter(indent=4)
        msg = pp.pformat(config)
        # display dict on visdom
        self.viz.text(msg)
