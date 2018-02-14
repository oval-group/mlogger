import git
import time
import json
import sys
import fnmatch

from builtins import dict
from collections import defaultdict, OrderedDict

from .plotter import Plotter
from .metrics import TimeMetric_, AvgMetric_, SumMetric_, ParentWrapper_,\
    SimpleMetric_, BestMetric_, DynamicMetric_

# pickle for python 2 / 3
if sys.version_info[0] == 2:
    import cPickle as pickle
else:
    import pickle


class Experiment(object):

    def __init__(self, name, log_git_hash=True,
                 use_visdom=False, visdom_opts=None,
                 time_indexing=True, xlabel=None):
        """ Create an experiment with the following parameters:
        - log_git_hash (bool): retrieve current commit hash to log code status
        - use_visdom (bool): monitor metrics logged on visdom
        - visdom_opts (dict): options for visdom
        - time_indexing (bool): use time to index values (otherwise counter)
        """

        super(Experiment, self).__init__()

        self.name = name.split('/')[-1]
        self.name_and_dir = name
        self.date_and_time = time.strftime('%d-%m-%Y--%H-%M-%S')

        self.logged = defaultdict(OrderedDict)
        self.metrics = defaultdict(dict)
        self.registered = []

        self.config = dict()
        self.use_visdom = use_visdom
        self.time_indexing = time_indexing

        if self.use_visdom:
            self.plotter = Plotter(self, visdom_opts, xlabel)

        if log_git_hash:
            self.log_git_hash()

    def NewMetric_(self, name, tag, Metric_, time_idx, to_plot, **kwargs):
        if time_idx is None:
            time_idx = self.time_indexing
        metric = Metric_(name, tag,
                         time_idx=time_idx, to_plot=to_plot, **kwargs)
        self.register_metric(metric)
        return metric

    def AvgMetric(self, name, tag="default", time_idx=None, to_plot=True):
        return self.NewMetric_(name, tag, AvgMetric_, time_idx, to_plot)

    def SimpleMetric(self, name, tag="default", time_idx=None, to_plot=True):
        return self.NewMetric_(name, tag, SimpleMetric_, time_idx, to_plot)

    def TimeMetric(self, name, tag="default", to_plot=True):
        return self.NewMetric_(name, tag, TimeMetric_, False, to_plot)

    def SumMetric(self, name, tag="default", time_idx=None, to_plot=True):
        return self.NewMetric_(name, tag, SumMetric_, time_idx, to_plot)

    def BestMetric(self, name, tag="default", mode="max", time_idx=None, to_plot=True):
        return self.NewMetric_(name, tag, BestMetric_, time_idx, to_plot, mode=mode)

    def DynamicMetric(self, name, tag="default", fun=None, time_idx=None, to_plot=True):
        return self.NewMetric_(name, tag, DynamicMetric_, time_idx, to_plot, fun=fun)

    def ParentWrapper(self, name, tag="default", children=()):

        for child in children:
            # continue if child tag is same as parent's
            if child.tag == tag:
                continue
            # else remove child from previous tagging and attribute
            self.remove_metric(child)
            # update child's tag
            child.tag = tag
            # register child again
            self.register_metric(child)

        wrapper = ParentWrapper_(name, tag, children=children)
        self.register_metric(wrapper)
        return wrapper

    def register_metric(self, metric):

        name_id = metric.name_id()
        Name_Id = name_id.title()
        assert name_id not in self.registered, \
            "metric with id {} already exists".format(name_id)

        self.registered.append(name_id)
        self.metrics[metric.tag][metric.name] = metric

        assert not hasattr(self, Name_Id) or metric is getattr(self, Name_Id)
        assert not hasattr(self, name_id), name_id

        # set attribute in title format for metric
        setattr(self, Name_Id, metric)
        # set attribute in lower format to store logged value of metric
        # initial value of None
        setattr(self, name_id, None)

        setattr(metric, 'log',
                lambda idx=None: self.log_metric(metric, idx))
        setattr(metric, 'log_and_reset',
                lambda idx=None: self.log_and_reset_metric(metric, idx))

    def remove_metric(self, metric):
        name_id = metric.name_id()
        Name_Id = name_id.title()

        self.metrics[metric.tag].pop(metric.name)
        self.registered.remove(name_id)
        delattr(self, Name_Id)
        delattr(self, name_id)

    def log_git_hash(self):

        try:
            repo = git.Repo(search_parent_directories=True)
            git_hash = repo.head.object.hexsha
            head = repo.head.commit.tree
            git_diff = repo.git.diff(head)
            self.log_config(dict(git_hash=git_hash,
                                 git_diff=git_diff),
                            to_visdom=False)
        except:
            print("I tried to find a git repository in current "
                  "and parent directories but did not find any.")

    def log_config(self, config_dict, to_visdom=True):
        self.config.update(config_dict)
        if to_visdom and self.use_visdom:
            self.plotter.plot_config(config_dict)

    def log_with_tag(self, tag, idx=None, reset=False):
        """ Log metrics from each tag matching the given pattern.
        tag parameter must be in Unix shell-style wildcards format.
        """
        matched_tags = fnmatch.filter(self.metrics, tag)
        assert matched_tags, "Could not find any tag matching with {}".format(tag)

        for match in matched_tags:
            # log all metrics with given tag except Parents
            # (to avoid logging twice the information)
            for metric in self.metrics[match].values():
                if isinstance(metric, ParentWrapper_):
                    continue
                self.log_metric(metric, idx, reset)

    def log_metric(self, metric, idx=None, reset=False):

        # log only child metrics
        if isinstance(metric, ParentWrapper_):
            for child in metric.children.values():
                self.log_metric(child, idx)
            return

        metric.index.update(idx)
        # update logged value of metric
        setattr(self, metric.name_id(), metric.get())
        self.logged[metric.name_id()][metric.index.get()] = metric.get()

        if self.use_visdom and metric.to_plot:
            self.plotter.plot_metric(metric)

        if reset:
            metric.reset()

    def log_and_reset_metric(self, metric, idx=None):
        self.log_metric(metric, idx)
        metric.reset()

    def get_metric(self, name, tag="default"):

        assert tag in list(self.metrics.keys()) \
            and name in list(self.metrics[tag].keys()), \
            "could not find metric with tag {} and name {}".format(tag, name)

        return self.metrics[tag][name]

    def get_var_dict(self):
        var_dict = {}
        var_dict['config'] = self.config
        var_dict['logged'] = self.logged
        var_dict['name'] = self.name
        var_dict['name_and_dir'] = self.name_and_dir
        var_dict['date_and_time'] = self.date_and_time
        if self.use_visdom:
            var_dict['visdom_win_opts'] = self.plotter.windows_opts
        return var_dict

    def to_pickle(self, filename):
        var_dict = self.get_var_dict()
        with open(filename, 'wb') as f:
            pickle.dump(var_dict, f)

    def to_json(self, filename):
        var_dict = self.get_var_dict()
        with open(filename, 'w') as f:
            json.dump(var_dict, f)

    def from_pickle(self, filename):
        with open(filename, 'r') as f:
            my_dict = pickle.load(f)
            my_dict = _dict_process(my_dict)
        self.__dict__.update(my_dict)

    def from_json(self, filename):
        with open(filename, 'r') as f:
            my_dict = json.load(f, object_pairs_hook=OrderedDict)
            my_dict = _dict_process(my_dict)
        self.__dict__.update(my_dict)

    def to_visdom(self, visdom_opts=None, xlabel=None):
        self.plotter = Plotter(self, visdom_opts, xlabel)
        # restore visdom options that have been saved (if experiment loaded from file)
        if hasattr(self, 'visdom_win_opts'):
            windows_opts = self.__dict__.pop('visdom_win_opts')
            for (name, opts) in windows_opts.items():
                self.plotter.set_win_opts(name, opts)
        self.plotter.plot_xp(self)


def _dict_process(my_dict):
    logged = defaultdict(OrderedDict)
    for key in list(my_dict['logged'].keys()):
        splitted = key.split('_')
        if not len(splitted):
            splitted.append("default")
        name, tag = '_'.join(splitted[:-1]), splitted[-1]
        values = my_dict['logged'].pop(key)
        # sort values based on x-value
        values = sorted(values.items(), key=lambda x: float(x[0]))
        logged[tag][name] = OrderedDict(values)
    my_dict['logged'] = logged
    # no need for an ordered dictionary for config
    my_dict['config'] = dict(my_dict['config'])
    return my_dict
