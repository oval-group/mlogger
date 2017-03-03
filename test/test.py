import unittest
import git
import time
import numpy as np

from logger.main import TimeMetric_, AvgMetric_, SumMetric_, ParentMetric_,\
	Experiment


class TestTimeMetric(unittest.TestCase):

	def setUp(self):

		self.name = "my_name"
		self.tag = "my_tag"
		self.metric = TimeMetric_(name=self.name,
		                          tag=self.tag)
		self.start_time = self.metric.start_time

	def test_init(self):

		assert self.metric.name == "my_name"
		assert self.metric.tag == "my_tag"
		assert self.metric.get() == 0.

	def test_update(self):

		value = time.time()
		self.metric.update(value)
		assert self.metric.get() == value - self.start_time

		self.metric.update()

		assert self.metric.get() > value - self.start_time


class TestAvgMetric(unittest.TestCase):

	def setUp(self):

		self.name = "my_name"
		self.tag = "my_tag"
		self.metric = AvgMetric_(name=self.name,
		                          tag=self.tag)

	def test_init(self):

		assert self.metric.name == "my_name"
		assert self.metric.tag == "my_tag"
		assert self.metric.acc == 0.
		assert self.metric.count == 0.

	def test_update(self):

		n_updates = 10
		values = np.random.random(size=n_updates)
		weights = np.random.randint(100, size=n_updates)
		
		for k in range(n_updates):
			value, weight = values[k], weights[k]
			self.metric.update(value, n=weight)
		
		assert np.isclose(self.metric.get(), 
		                  np.sum(values * weights) / np.sum(weights))


class TestSumMetric(unittest.TestCase):

	def setUp(self):

		self.name = "my_name"
		self.tag = "my_tag"
		self.metric = SumMetric_(name=self.name,
		                          tag=self.tag)

	def test_init(self):

		assert self.metric.name == "my_name"
		assert self.metric.tag == "my_tag"
		assert self.metric.acc == 0.
		assert self.metric.count == 0.

	def test_update(self):

		n_updates = 10
		values = np.random.random(size=n_updates)
		weights = np.random.randint(100, size=n_updates)
		
		for k in range(n_updates):
			value, weight = values[k], weights[k]
			self.metric.update(value, n=weight)
		
		assert np.isclose(self.metric.get(), np.sum(values * weights))

class TestParentMetric(unittest.TestCase):

	def setUp(self):

		self.tag = "my_tag"

		self.child_1 = TimeMetric_(name="time",
		                           tag=self.tag)
		self.child_2 = AvgMetric_(name="avg",
		                          tag=self.tag)
		self.child_3 = SumMetric_(name="sum",
		                          tag=self.tag)

		self.children = (self.child_1, self.child_2, self.child_3)

		self.metric = ParentMetric_(children=self.children)

	def test_init(self):

		assert set(self.metric.children.keys()) == \
			set([child.name for child in self.children])
		assert set(self.metric.children.values()) == \
			set(self.children)

	def test_update(self):

		value_time = time.time()
		value_avg = np.random.random()
		value_sum = np.random.random()
		n = np.random.randint(1, 100)

		self.metric.update(time=value_time,
		                   avg=value_avg,
		                   sum=value_sum,
		                   n=n)

		res_dict = self.metric.get()

		assert res_dict['time'] == value_time - self.child_1.start_time
		assert res_dict['avg'] == value_avg
		assert res_dict['sum'] == n * value_sum


class TestExperiment(unittest.TestCase):

	def setUp(self):

		self.name = "my_name"
		self.config = {"param1": 1, "param2": (1., 2., 3.)}

	def test_log_config(self):

		xp = Experiment("my_name", log_git_hash=False)
		xp.log_config(self.config)

		assert xp.config.items() == self.config.items()

	def test_log_git_hash(self):

		xp = Experiment("my_name")

		repo = git.Repo(search_parent_directories=True)
		commit = repo.head.object.hexsha

		assert xp.config['git_hash'] == commit

	def test_log_with_tag(self):

		return

	def test_log_metric(self):

		return

	def test_get_metric(self):

		return

	def to_pickle(self):

		return

	def to_json(self):

		return


