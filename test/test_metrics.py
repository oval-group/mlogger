import unittest
import time
import numpy as np

import mlogger


class TestTimer(unittest.TestCase):

    def setUp(self):

        self.metric = mlogger.metric.Timer()
        self.start = self.metric.start

    def test_init(self):

        assert self.metric.value == 0.

    def test_update(self):

        value = time.time()
        self.metric.update(value)
        assert self.metric.value == value - self.start

        self.metric.update()
        new_time = time.time()

        assert self.metric.value > value - self.start
        assert self.metric.value <= new_time - self.start


class TestSimple(unittest.TestCase):

    def setUp(self):

        self.metric = mlogger.metric.Simple()

    def test_init(self):

        assert self.metric.value == 0

    def test_update(self):

        value = np.random.randn()
        self.metric.update(value)

        assert self.metric.value == value


class TestMaximum(unittest.TestCase):

    def setUp(self):

        self.metric = mlogger.metric.Maximum()

    def test_init(self):

        assert self.metric.value == float('-inf')

    def test_update(self):

        value = np.random.randn()
        value_greater = value + 1
        value_lower = value - 1

        self.metric.update(value)
        assert self.metric.value == value

        self.metric.update(value_lower)
        assert self.metric.value == value

        self.metric.update(value_greater)
        assert self.metric.value == value_greater

        self.metric.update(value)
        assert self.metric.value == value_greater


class TestAverage(unittest.TestCase):

    def setUp(self):

        self.metric = mlogger.metric.Average()

    def test_init(self):

        assert self.metric.value == 0.

    def test_update(self):

        n_updates = 10
        values = np.random.random(size=n_updates)
        weights = 100 * np.random.rand(n_updates) + 1e-10

        for k in range(n_updates):
            value, weight = values[k], weights[k]
            self.metric.update(value, weighting=weight)

        np.testing.assert_allclose(self.metric.value,
                                   np.sum(values * weights) / np.sum(weights))


class TestSum(unittest.TestCase):

    def setUp(self):

        self.metric = mlogger.metric.Sum()

    def test_init(self):

        assert self.metric.value == 0

    def test_update(self):

        n_updates = 10
        values = np.random.random(size=n_updates)
        weights = np.random.randint(1, 100, size=n_updates)

        for k in range(n_updates):
            value, weight = values[k], weights[k]
            self.metric.update(value, weighting=weight)

        np.testing.assert_allclose(self.metric.value,
                                   np.sum(values * weights))
