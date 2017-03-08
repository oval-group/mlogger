import copy
import git
import time
import cPickle as pickle
import json

from collections import defaultdict

from .metrics import TimeMetric_, AvgMetric_, SumMetric_, ParentMetric_

__version__ = 0.1

class Experiment(object):

    def __init__(self, name, log_git_hash=True):

        super(Experiment, self).__init__()

        self.name = name
        self.date_and_time = time.strftime('%d-%m-%Y--%H-%M-%S')

        self.config = dict()
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
    	names = (k for k in self.metrics[tag].keys() \
            if not isinstance(self.metrics[tag][k], ParentMetric_))

    	for name in names:
    		key = "{}_{}".format(name, tag)
    		self.logged[key].append(self.metrics[tag][name].get())

    def log_metric(self, metric):

    	if isinstance(metric, ParentMetric_):
    		for child in metric.children:
    			self.update_metric(metric)
			return

		tag = metric.tag
		name = metric.name
		key = "{}_{}".format(name, tag)
		self.logged[key].append(self.metrics[tag][name].get())

    def get_metric(self, name, tag="default"):

        assert tag in self.metrics.keys() and name in self.metrics[tag].keys()

        return self.metrics[tag][name]

    def to_pickle(self, filename):

        var_dict = copy.copy(vars(self))
        var_dict.pop('metrics')
        with open(filename, 'wb') as f:
        	pickle.dump(var_dict, f)

    def to_json(self, filename):

        var_dict = copy.copy(vars(self))
        var_dict.pop('metrics')
        with open(filename, 'wb') as f:
        	json.dump(var_dict, f)
