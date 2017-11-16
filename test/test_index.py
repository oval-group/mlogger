import unittest
import time
import numpy as np

from logger.index import TimeIndex_, ValueIndex_


class TestTimeIndexer(unittest.TestCase):

    def setUp(self):

        self.indexer = TimeIndex_()
        self.start = self.indexer.start

    def test_init(self):

        assert self.indexer.get() == 0.

    def test_update(self):

        value = time.time()
        self.indexer.update(value)
        assert self.indexer.get() == value - self.start

        self.indexer.update()
        assert self.indexer.get() > value - self.start


class TestValueIndexer(unittest.TestCase):

    def setUp(self):

        self.indexer = ValueIndex_()

    def test_init(self):

        assert self.indexer.start == 0.
        assert self.indexer.current == 0.

    def test_update(self):

        value = np.random.randn()
        self.indexer.update(value)

        assert np.isclose(self.indexer.get(), value)

        self.indexer.update()
        assert np.isclose(self.indexer.get(), value + 1)
