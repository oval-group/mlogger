import copy
import git
import time
import cPickle as pickle
import json

try:
    import pycrayon
except:
    pycrayon = None

from collections import defaultdict

from .metrics import TimeMetric_, AvgMetric_, SumMetric_, ParentMetric_

__version__ = 0.1

class Experiment(object):

    def __init__(self, name, log_git_hash=True):

        super(Experiment, self).__init__()

        self.name = name
        self.date_and_time = time.strftime('%d-%m-%Y--%H-%M-%S')

        self.config = dict()
        self.crayons = dict()
        self.logged = defaultdict(list)
        self.metrics = defaultdict(dict)

        if log_git_hash:
            self.log_git_hash()

    def AvgMetric(self, name, tag="default"):

    	assert name not in self.metrics[tag].keys(), \
    		"metric with tag {} and name {} already exists".format(tag, name)

    	metric = AvgMetric_(name, tag)
    	self.metrics[tag][name] = metric

    	return metric

    def TimeMetric(self, name, tag="default"):

    	assert name not in self.metrics[tag].keys(), \
    		"metric with tag {} and name {} already exists".format(tag, name)

    	metric = TimeMetric_(name, tag)
    	self.metrics[tag][name] = metric

    	return metric

    def SumMetric(self, name, tag="default"):

    	assert name not in self.metrics[tag].keys(), \
    		"metric with tag {} and name {} already exists".format(tag, name)

    	metric = SumMetric_(name, tag)
    	self.metrics[tag][name] = metric

    	return metric

    def ParentMetric(self, name, tag="default", children=()):

        for child in children:

            # continue if child tag is same as parent's
            if child.tag == tag:
                continue

            # else remove child from previous tagging
            self.metrics[child.tag].pop(child.name)

            # update child's tag
            child.tag = tag

            # update tagging
            self.metrics[child.tag][child.name] = child

    	metric = ParentMetric_(children)
        self.metrics[tag][name] = metric

        return metric

    def log_git_hash(self):

        try:
            repo = git.Repo(search_parent_directories=True)
            self.log_config({'git_hash': repo.head.object.hexsha})
        except:
            print("I tried to find a git repository in current "
                  "and parent directories but did not find any.")

    def log_config(self, config_dict):

        self.config.update(config_dict)

    def log_with_tag(self, tag):

        # gather all metrics with given tag except Parents
        # (to avoid logging twice the information)
    	metrics = (m for m in self.metrics[tag].itervalues() \
            if not isinstance(m, ParentMetric_))

    	for metric in metrics:
            self.log_metric(metric)

    def log_metric(self, metric):

    	if isinstance(metric, ParentMetric_):
    		for child in metric.children:
    			self.update_metric(metric)
			return

        key = "{}_{}".format(metric.name, metric.tag)
        self.logged[key].append(metric.get())

        if metric.tag in self.crayons:
            self.crayons[metric.tag].add_scalar_value(metric.name, metric.get())

    def get_metric(self, name, tag="default"):

        assert tag in self.metrics.keys() and name in self.metrics[tag].keys()

        return self.metrics[tag][name]

    def Crayon(self, crayon_xp, tag):

        assert pycrayon is not None, 'pycrayon is not installed'
        self.crayons[tag] = crayon_xp

    def to_pickle(self, filename):

        var_dict = copy.copy(vars(self))
        var_dict.pop('metrics')
        var_dict.pop('crayons')
        with open(filename, 'wb') as f:
        	pickle.dump(var_dict, f)

    def to_json(self, filename):

        var_dict = copy.copy(vars(self))
        var_dict.pop('metrics')
        var_dict.pop('crayons')
        with open(filename, 'wb') as f:
        	json.dump(var_dict, f)
