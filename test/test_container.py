import unittest
import os
import mlogger


class TestContainer(unittest.TestCase):

    def setUp(self):

        self.C = mlogger.Container()
        self.metric_a = mlogger.metric.Simple()
        self.config = mlogger.Config(entry="running_a_test")
        self.CC = mlogger.Container(b=mlogger.metric.Average())
        self.CCC = mlogger.Container(c=mlogger.metric.Timer(),
                                     d=mlogger.metric.Maximum())

    def test_setter(self):
        # set metric
        self.C.a = self.metric_a
        # second time
        self.C.a = self.metric_a

        assert self.C.a is self.metric_a

        # set config
        self.C.config = self.config

        # set container
        self.C.CC = self.CC

        # set nested container
        self.C.CC.CCC = self.CCC

        with self.assertRaises(TypeError):
            self.C.e = 0

    def test_deletion(self):
        # set attribute and check
        self.C.a = self.metric_a
        assert self.C.a is self.metric_a

        # delete attribute
        del self.C.a

        # check attribute has been deleted
        with self.assertRaises(AttributeError):
            metric_a = self.C.a

        # check error when deleting non-existing attribute
        with self.assertRaises(AttributeError):
            del self.C.b

        # check attribute can be set again
        self.C.a = self.metric_a
        assert self.C.a is self.metric_a

    def test_state_dict(self):
        self.C.a = self.metric_a
        self.C.conf = self.config
        self.C.CC = self.CC
        self.C.CC.CCC = self.CCC

        self.metric_a.update(10)
        self.CC.b.update(12)
        self.CC.b.update(15)
        self.CCC.c.update()
        self.CCC.d.update(12)
        self.CCC.d.update(15)

        state = self.C.state_dict()

        self.assertDictEqual(state['a'], self.metric_a.state_dict())
        self.assertDictEqual(state['conf'], self.config.state_dict())
        self.assertDictEqual(state['CC'], self.CC.state_dict())
        self.assertDictEqual(state['CC']['b'], self.CC.b.state_dict())
        self.assertDictEqual(state['CC']['CCC'], self.CC.CCC.state_dict())
        self.assertDictEqual(state['CC']['CCC']['c'], self.CC.CCC.c.state_dict())
        self.assertDictEqual(state['CC']['CCC']['d'], self.CC.CCC.d.state_dict())

    def test_load_state_dict(self):
        self.C.a = self.metric_a
        self.C.conf = self.config
        self.C.CC = self.CC
        self.C.CC.CCC = self.CCC

        self.metric_a.update(10)
        self.CC.b.update(12)
        self.CC.b.update(15)
        self.CCC.c.update()
        self.CCC.d.update(12)
        self.CCC.d.update(15)

        state = self.C.state_dict()
        new_C = mlogger.Container()
        new_C.load_state_dict(state)

        self.assertDictEqual(self.C.state_dict(), new_C.state_dict())

        for old, new in zip(self.C.children(), new_C.children()):
            assert old is not new
            assert isinstance(new, type(old))
            self.assertDictEqual(old.state_dict(), new.state_dict())

    def test_save_and_load(self):
        self.C.a = self.metric_a
        self.C.conf = self.config
        self.C.CC = self.CC
        self.C.CC.CCC = self.CCC

        self.metric_a.update(10)
        self.CC.b.update(12)
        self.CC.b.update(15)
        self.CCC.c.update()
        self.CCC.d.update(12)
        self.CCC.d.update(15)

        tmp = 'tmp.json'
        self.C.save_to(tmp)
        new_C = mlogger.load_container(tmp)

        self.assertDictEqual(self.C.state_dict(), new_C.state_dict())

        for old, new in zip(self.C.children(), new_C.children()):
            assert old is not new
            assert isinstance(new, type(old))
            self.assertDictEqual(old.state_dict(), new.state_dict())

        os.remove(tmp)
