import copy
import git
import time
import json
import numpy as np
import sys
import pprint
import warnings

from builtins import dict
from collections import defaultdict, OrderedDict

from .metrics import TimeMetric_, AvgMetric_, SumMetric_, ParentWrapper_,\
    SimpleMetric_, BestMetric_, DynamicMetric_

# pickle for python 2 / 3
if sys.version_info[0] == 2:
    import cPickle as pickle
else:
    import pickle

# optional visdom
try:
    import visdom
except ImportError:
    visdom = None


class Experiment(object):

    def __init__(self, name, log_git_hash=True,
                 use_visdom=False, visdom_opts={}):
        """ Create an experiment with the following parameters:
        - log_git_hash (bool): retrieve current commit hash to log code status
        - use_visdom (bool): monitor metrics logged on visdom
        - visdom_opts (dict): options for visdom
        """

        super(Experiment, self).__init__()

        self.name = name.split('/')[-1]
        self.name_and_dir = name
        self.date_and_time = time.strftime('%d-%m-%Y--%H-%M-%S')

        self.logged = defaultdict(OrderedDict)
        self.metrics = defaultdict(dict)

        self.config = dict()
        self.use_visdom = use_visdom

        if self.use_visdom:
            self._visdom(visdom_opts)

        if log_git_hash:
            self.log_git_hash()

    def _visdom(self, visdom_opts):
        assert visdom is not None, "visdom could not be imported"
        # visdom env is given by Experiment name unless specified
        if 'env' not in list(visdom_opts.keys()):
            visdom_opts['env'] = self.name
        self.viz = visdom.Visdom(**visdom_opts)
        self.viz_dict = dict()

    def NewMetric_(self, name, tag, Metric_, **kwargs):
        metric = Metric_(name, tag, **kwargs)
        setattr(metric, 'log', lambda: self.log_metric(metric))
        self.register_metric(metric)
        return metric

    def AvgMetric(self, name, tag="default"):
        return self.NewMetric_(name, tag, AvgMetric_)

    def SimpleMetric(self, name, tag="default"):
        return self.NewMetric_(name, tag, SimpleMetric_)

    def TimeMetric(self, name, tag="default"):
        return self.NewMetric_(name, tag, TimeMetric_)

    def SumMetric(self, name, tag="default"):
        return self.NewMetric_(name, tag, SumMetric_)

    def BestMetric(self, name, tag="default", mode="max"):
        return self.NewMetric_(name, tag, BestMetric_, mode=mode)

    def DynamicMetric(self, name, tag="default", fun=None):
        return self.NewMetric_(name, tag, DynamicMetric_, fun=fun)

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

        return self.NewMetric_(name, tag, ParentWrapper_, children=children)

    def register_metric(self, metric):

        assert metric.name not in list(self.metrics[metric.tag].keys()), \
            "metric with tag {} and name {} already exists" \
            .format(metric.tag, metric.name)

        self.metrics[metric.tag][metric.name] = metric

        if metric.tag == "default":
            attr_name = metric.name
        else:
            attr_name = "{}_{}".format(metric.name, metric.tag)
        if attr_name.title() in list(self.__dict__.keys()) or \
                attr_name.lower() in list(self.__dict__.keys()):
            warnings.warn("Combination of tag '{}' and name '{}' will"
                          "override an existing attribute"
                          .format(metric.tag, metric.name))

        # set attribute in title format for metric
        setattr(self, attr_name.title(), metric)
        # set property in lower format for dynamic value of metric
        setattr(Experiment, attr_name.lower(),
                property(lambda x: metric.get()))

    def remove_metric(self, metric):
        self.metrics[metric.tag].pop(metric.name)

        if metric.tag == "default":
            attr_name = metric.name
        else:
            attr_name = "{}_{}".format(metric.name, metric.tag)
        delattr(self, attr_name.title())
        delattr(Experiment, attr_name.lower())

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
            # format dictionary with pretty print
            pp = pprint.PrettyPrinter(indent=4)
            msg = pp.pformat(config_dict)
            # display dict on visdom
            self.viz.text(msg)

    def log_with_tag(self, tag):

        # gather all metrics with given tag except Parents
        # (to avoid logging twice the information)
        metrics = (m for m in self.metrics[tag].values()
                   if not isinstance(m, ParentWrapper_))

        # log all metrics
        for metric in metrics:
            self.log_metric(metric)

    def log_metric(self, metric):

        # log only child metrics
        if isinstance(metric, ParentWrapper_):
            for child in metric.children.values():
                self.log_metric(child)
            return

        tag, name = metric.tag, metric.name
        key = "{}_{}".format(name, tag)
        self.logged[key][metric.timer.get()] = metric.get()

        if self.use_visdom and not isinstance(metric, TimeMetric_):
            try:
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
            except:
                # if an error occurs, warn user and give up monitoring
                # (useful if connection is lost for instance)
                print('I could not send my data to Visdom :(\n'
                      'Giving up monitoring.')
                self.use_visdom = False

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
        assert filename.endswith(".pickle")

        with open(filename, 'r') as f:
            my_dict = pickle.load(f)
            my_dict = dict_process(my_dict)
        self.__dict__.update(my_dict)

    def from_json(self, filename):
        assert filename.endswith(".json")
        with open(filename, 'r') as f:
            my_dict = json.load(f, object_pairs_hook=OrderedDict)
            my_dict = dict_process(my_dict)
        self.__dict__.update(my_dict)

    def to_visdom(self, visdom_opts={}):
        self._visdom(visdom_opts)
        # format dictionary with pretty print
        pp = pprint.PrettyPrinter(indent=4)
        msg = pp.pformat(self.config)
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


def dict_process(my_dict):
    logged = defaultdict(OrderedDict)
    for key in my_dict['logged'].keys():
        splitted = key.split('_')
        name, tag = '_'.join(splitted[:-1]), splitted[-1]
        values = my_dict['logged'].pop(key)
        # sort values based on x-value
        values = sorted(values.items(), key=lambda x: float(x[0]))
        logged[tag][name] = OrderedDict(values)
    my_dict['logged'] = logged
    # no need for an ordered dictionary for config
    my_dict['config'] = dict(my_dict['config'])
    return my_dict
