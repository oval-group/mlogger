import unittest
import time
import numpy as np

from logger.metrics import TimeMetric_, AvgMetric_, SumMetric_, SimpleMetric_, \
    ParentWrapper_, BestMetric_


class TestTimeMetric(unittest.TestCase):

    def setUp(self):

        self.name = "my_name"
        self.tag = "my_tag"
        self.to_plot = False
        self.metric = TimeMetric_(name=self.name,
                                  tag=self.tag,
                                  to_plot=self.to_plot)
        self.start = self.metric._timer.start

    def test_init(self):

        assert self.metric.name == "my_name"
        assert self.metric.tag == "my_tag"
        assert self.metric.get() == 0.

    def test_update(self):

        value = time.time()
        self.metric.update(value)
        assert self.metric.get() == value - self.start
        assert self.metric._timer.get() == value - self.start

        self.metric.update()

        assert self.metric.get() > value - self.start


class TestSimpleMetric(unittest.TestCase):

    def setUp(self):

        self.name = "my_name"
        self.tag = "my_tag"
        self.time_idx = True
        self.to_plot = False
        self.metric = SimpleMetric_(name=self.name,
                                    tag=self.tag,
                                    time_idx=self.time_idx,
                                    to_plot=self.to_plot)
        self.start = self.metric.index.start

    def test_init(self):

        assert self.metric.name == "my_name"
        assert self.metric.tag == "my_tag"
        assert self.metric._val == 0.

    def test_update(self):

        value = np.random.randn()
        timed = np.random.randn()
        self.metric.update(value)
        self.metric.index.update(self.start + timed)

        assert np.isclose(self.metric.get(), value)
        assert np.isclose(self.metric.index.get(), timed)


class TestBestMetric(unittest.TestCase):

    def setUp(self):

        self.name = "my_name"
        self.tag = "my_tag"
        self.time_idx = False
        self.to_plot = False
        self.metric_min = BestMetric_(name=self.name,
                                      tag=self.tag,
                                      time_idx=self.time_idx,
                                      to_plot=self.to_plot,
                                      mode="min")
        self.metric_max = BestMetric_(name=self.name,
                                      tag=self.tag,
                                      time_idx=self.time_idx,
                                      to_plot=self.to_plot,
                                      mode="max")
        self.start_min = self.metric_min.index.start
        self.start_max = self.metric_max.index.start

    def test_init(self):

        assert self.metric_min.name == "my_name"
        assert self.metric_min.tag == "my_tag"
        assert self.metric_min._val == np.inf

        assert self.metric_max.name == "my_name"
        assert self.metric_max.tag == "my_tag"
        assert self.metric_max._val == -np.inf

    def test_update(self):

        value = np.random.randn()
        value_greater = value + 1
        value_lower = value - 1

        self.metric_min.update(value)
        assert np.isclose(self.metric_min.get(), value)

        self.metric_min.update(value_greater)
        assert np.isclose(self.metric_min.get(), value)

        self.metric_min.update(value_lower)
        assert np.isclose(self.metric_min.get(), value_lower)

        self.metric_max.update(value)
        assert np.isclose(self.metric_max.get(), value)

        self.metric_max.update(value_lower)
        assert np.isclose(self.metric_max.get(), value)

        self.metric_max.update(value_greater)
        assert np.isclose(self.metric_max.get(), value_greater)


class TestAvgMetric(unittest.TestCase):

    def setUp(self):

        self.name = "my_name"
        self.tag = "my_tag"
        self.time_idx = False
        self.to_plot = False
        self.metric = AvgMetric_(name=self.name,
                                 tag=self.tag,
                                 time_idx=self.time_idx,
                                 to_plot=self.to_plot)

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
        self.time_idx = False
        self.to_plot = False
        self.metric = SumMetric_(name=self.name,
                                 tag=self.tag,
                                 time_idx=self.time_idx,
                                 to_plot=self.to_plot)

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
        self.time_idx = False
        self.to_plot = False

        self.child1 = TimeMetric_(name="time",
                                  tag=self.tag,
                                  time_idx=self.time_idx,
                                  to_plot=self.to_plot)
        self.child2 = AvgMetric_(name="avg",
                                 tag=self.tag,
                                 time_idx=self.time_idx,
                                 to_plot=self.to_plot)
        self.child3 = SumMetric_(name="sum",
                                 tag=self.tag,
                                 time_idx=self.time_idx,
                                 to_plot=self.to_plot)

        self.children = (self.child1, self.child2, self.child3)

        self.metric = ParentWrapper_(name="parent", tag=self.tag,
                                     children=self.children)

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
                                   value_time - self.child1._timer.start)
        np.testing.assert_allclose(res_dict['avg'], value_avg)
        np.testing.assert_allclose(res_dict['sum'], n * value_sum)
