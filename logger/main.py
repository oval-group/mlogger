import git
import time
import cPickle as pickle
import json

from collections import defautdict

__version__ = 0.1


class TimeMetric_(object):

    def __init__(self, name, tag):

        self.tag = tag
        self.name = name
        self.reset()

    def reset(self):

        self.start_time = time.time()
        self.end_time = self.start_time

    def update(self):

        self.end_time = time.time()

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

        super(AvgMetric, self).__init__(tag, name)

    def get(self):

        return self.acc * 1. / self.count


class SumMetric_(Accumulator_):

    def __init__(self, name, tag):

        super(SumMetric, self).__init__(tag, name)

    def get(self):

        return self.acc

class ParentMetric_(object):

	def _init__(self, *metrics):

		self.children = dict()
		for metric in self.metrics:
			key = "{}_{}".format(metric.name, metric.tag)
			self.children[key] = metric

	def update(self, n=1, **kwargs):

		for (key, value) in kwargs.iteritems():
			self.children[key].update(value, n)

	def reset(self):

		for child in self.children:
			child.reset()


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

    def AvgMetric(self, name, tag):

    	assert name not self.metrics[tag].keys(), \
    		"metric with tag {} and name {} already exists".format(tag, name)

    	metric = AvgMetric_(name, tag)
    	self.metrics[tag][name] = metric

    	return metric

    def TimeMetric(self, name, tag):

    	assert name not self.metrics[tag].keys(), \
    		"metric with tag {} and name {} already exists".format(tag, name)

    	metric = TimeMetric_(name, tag)
    	self.metrics[tag][name] = metric

    	return metric

    def SumMetric(self, name, tag):

    	assert name not self.metrics[tag].keys(), \
    		"metric with tag {} and name {} already exists".format(tag, name)

    	metric = SumMetric_(name, tag)
    	self.metrics[tag][name] = metric

    	return metric

    def ParentMetric(self, *metrics):

    	return ParentMetric_(metrics)

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

    	names = self.metrics[tag].keys()

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

    def to_pickle(self, filename):

        var_dict = vars(self)
        var_dict.pop('metrics')
        with open(filename, 'wb') as f:
        	pickle.dump(var_dict, f)

    def to_json(self, filename):

        var_dict = vars(self)
        var_dict.pop('metrics')
        with open(filename, 'wb') as f:
        	json.dump(var_dict, f)
