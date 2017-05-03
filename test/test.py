import unittest
import git
import time
import numpy as np
import os
import json
import sys

from logger.xp import Experiment
from logger.metrics import TimeMetric_, AvgMetric_, SumMetric_, SimpleMetric_, \
    ParentWrapper_

if sys.version_info[0] == 2:
    import cPickle as pickle
else:
    import pickle


class TestTimeMetric(unittest.TestCase):

    def setUp(self):

        self.name = "my_name"
        self.tag = "my_tag"
        self.metric = TimeMetric_(name=self.name,
                                  tag=self.tag)
        self.start_time = self.metric.timer.start_time

    def test_init(self):

        assert self.metric.name == "my_name"
        assert self.metric.tag == "my_tag"
        assert self.metric.get() == 0.

    def test_update(self):

        value = time.time()
        self.metric.update(value)
        assert self.metric.get() == value - self.start_time
        assert self.metric.timer.get() == value - self.start_time

        self.metric.update()

        assert self.metric.get() > value - self.start_time


class TestSimpleMetric(unittest.TestCase):

    def setUp(self):

        self.name = "my_name"
        self.tag = "my_tag"
        self.metric = SimpleMetric_(name=self.name,
                                    tag=self.tag)
        self.start_time = self.metric.timer.start_time

    def test_init(self):

        assert self.metric.name == "my_name"
        assert self.metric.tag == "my_tag"
        assert self.metric.val == 0.

    def test_update(self):

        value = np.random.randn()
        timed = np.random.randn()
        self.metric.update(value, timed=(self.start_time + timed))

        assert np.isclose(self.metric.get(), value)
        assert np.isclose(self.metric.timer.get(), timed)


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

        np.testing.assert_allclose(self.metric.get(),
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

        np.testing.assert_allclose(self.metric.get(), np.sum(values * weights))


class TestParentWrapper(unittest.TestCase):

    def setUp(self):

        self.tag = "my_tag"

        self.child1 = TimeMetric_(name="time",
                                  tag=self.tag)
        self.child2 = AvgMetric_(name="avg",
                                 tag=self.tag)
        self.child3 = SumMetric_(name="sum",
                                 tag=self.tag)

        self.children = (self.child1, self.child2, self.child3)

        self.metric = ParentWrapper_(children=self.children)

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

        np.testing.assert_allclose(res_dict['time'],
                                   value_time - self.child1.timer.start_time)
        np.testing.assert_allclose(res_dict['avg'], value_avg)
        np.testing.assert_allclose(res_dict['sum'], n * value_sum)


class TestExperiment(unittest.TestCase):

    def setUp(self):

        self.name = "my_name"
        self.config = {"param1": 1, "param2": (1., 2., 3.)}

    def test_log_config(self):

        xp = Experiment("my_name", log_git_hash=False)
        xp.log_config(self.config)

        assert list(xp.config.items()) == list(self.config.items())

    def test_log_git_hash(self):

        xp = Experiment("my_name")

        repo = git.Repo(search_parent_directories=True)
        commit = repo.head.object.hexsha

        assert xp.config['git_hash'] == commit

    def test_log_with_tag(self):

        xp = Experiment("my_name")
        metrics = xp.ParentWrapper(tag='my_tag', name='parent',
                                   children=(xp.AvgMetric(name='child1'),
                                             xp.SumMetric(name='child2')))
        timer = xp.TimeMetric(tag='my_tag', name='timer')
        metrics.update(child1=0.1, child2=0.5)
        timer.update(1.)

        xp.log_with_tag('my_tag')

        assert list(xp.logged['child1_my_tag'].values()) == [0.1]
        assert list(xp.logged['child2_my_tag'].values()) == [0.5]
        assert list(xp.logged['timer_my_tag'].values()) == \
            [1. - timer.timer.start_time]

    def test_log_metric(self):

        xp = Experiment("my_name")
        metrics = xp.ParentWrapper(tag='my_tag', name='parent',
                                   children=(xp.AvgMetric(name='child1'),
                                             xp.SumMetric(name='child2')))
        timer = xp.TimeMetric(tag='my_tag', name='timer')
        metrics.update(child1=0.1, child2=0.5)
        timer.update(1.)

        xp.log_metric(metrics)
        xp.log_metric(timer)

        assert list(xp.logged['child1_my_tag'].values()) == [0.1]
        assert list(xp.logged['child2_my_tag'].values()) == [0.5]
        assert list(xp.logged['timer_my_tag'].values()) == \
            [1. - timer.timer.start_time]

    def test_get_metric(self):

        xp = Experiment("my_name")
        metric_not_tagged = xp.SumMetric(name='my_metric')
        metric_not_tagged_1 = xp.get_metric(name='my_metric')
        metric_not_tagged_2 = xp.get_metric(name='my_metric', tag='default')
        metric_tagged = xp.SumMetric(tag='my_tag', name='my_metric')
        metric_tagged_1 = xp.get_metric(tag='my_tag', name='my_metric')

        assert metric_not_tagged_1 is metric_not_tagged
        assert metric_not_tagged_2 is metric_not_tagged

        assert metric_tagged_1 is metric_tagged

    def test_to_pickle(self):

        xp = Experiment("my_name")
        metrics = xp.ParentWrapper(tag='my_tag', name='parent',
                                   children=(xp.AvgMetric(name='child1'),
                                             xp.SumMetric(name='child2')))
        timer = xp.TimeMetric(tag='my_tag', name='timer')
        metrics.update(child1=0.1, child2=0.5)
        timer.update(1.)

        xp.log_with_tag('my_tag')
        xp.to_pickle('tmp.pkl')

        with open('tmp.pkl', 'rb') as tmp:
            my_dict = pickle.load(tmp)

        # check basic attributes
        assert my_dict['name'] == getattr(xp, 'name')
        assert my_dict['date_and_time'] == getattr(xp, 'date_and_time')
        assert list(my_dict['config'].values()) == \
            list(getattr(xp, 'config').values())

        # check log
        assert list(my_dict['logged']['child1_my_tag'].values()) == [0.1]
        assert list(my_dict['logged']['child2_my_tag'].values()) == [0.5]
        assert list(my_dict['logged']['timer_my_tag'].values()) == \
            [1. - timer.timer.start_time]

        os.remove('tmp.pkl')

    def test_to_json(self):

        xp = Experiment("my_name")
        metrics = xp.ParentWrapper(tag='my_tag', name='parent',
                                   children=(xp.AvgMetric(name='child1'),
                                             xp.SumMetric(name='child2')))
        timer = xp.TimeMetric(tag='my_tag', name='timer')
        metrics.update(child1=0.1, child2=0.5)
        timer.update(1.)

        xp.log_with_tag('my_tag')
        xp.to_json('tmp.json')

        with open('tmp.json', 'r') as tmp:
            my_dict = json.load(tmp)

        # check basic attributes
        assert my_dict['name'] == getattr(xp, 'name')
        assert my_dict['date_and_time'] == getattr(xp, 'date_and_time')
        assert list(my_dict['config'].values()) == \
            list(getattr(xp, 'config').values())

        # check log
        assert list(my_dict['logged']['child1_my_tag'].values()) == [0.1]
        assert list(my_dict['logged']['child2_my_tag'].values()) == [0.5]
        assert list(my_dict['logged']['timer_my_tag'].values()) == \
            [1. - timer.timer.start_time]

        os.remove('tmp.json')
