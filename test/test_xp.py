import unittest
import git
import os
import json
import sys

from logger.xp import Experiment

if sys.version_info[0] == 2:
    import cPickle as pickle
else:
    import pickle


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
            [1. - timer._timer.start]

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
            [1. - timer._timer.start]

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
            [1. - timer._timer.start]

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
            [1. - timer._timer.start]

        os.remove('tmp.json')
