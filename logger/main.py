import copy
import git
import time
import cPickle as pickle
import json

from collections import defaultdict

__version__ = 0.1


class TimeMetric_(object):

    def __init__(self, name, tag):

        self.tag = tag
        self.name = name
        self.reset()

    def reset(self):

        self.start_time = time.time()
        self.end_time = self.start_time

    def update(self, value=None):

        if value is None:
            value = time.time()

        self.end_time = value

    def get(self):

        return self.end_time - self.start_time


class Accumulator_(object):
    """
    Accumulator.
    Credits to the authors of the ImageNet example of pytorch for this.
    """
    def __init__(self, name, tag):

        self.tag = tag
        self.name = name
        self.reset()

    def reset(self):

        self.acc = 0
        self.count = 0

    def update(self, val, n=1):

        self.acc += val * n
        self.count += n

    def get(self):

        raise NotImplementedError("Accumulator should be subclassed")


class AvgMetric_(Accumulator_):

    def __init__(self, name, tag):

        super(AvgMetric_, self).__init__(name, tag)

    def get(self):

        return self.acc * 1. / self.count


class SumMetric_(Accumulator_):

    def __init__(self, name, tag):

        super(SumMetric_, self).__init__(name, tag)

    def get(self):

        return self.acc

class ParentMetric_(object):

    def __init__(self, children):

        super(ParentMetric_, self).__init__()

    	self.children = dict()
    	for child in children:
    		self.children[child.name] = child

    def update(self, n=1, **kwargs):

    	for (key, value) in kwargs.iteritems():
            self.children[key].update(value, n)

    def reset(self):

        for child in self.children.itervalues():
    		child.reset()

    def get(self):

        res = dict()
        for (name, child) in self.children.iteritems():
            res[name] = child.get()

        return res


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
