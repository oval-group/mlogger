import unittest
import mlogger


class TestConfig(unittest.TestCase):

    def setUp(self):
        self.some_things = dict(param1=1, param2=(1., 2., 3.))
        self.other_things = dict(param2="my_text_here", param4={'a': 0})
        self.all_things = self.some_things.copy()
        self.all_things.update(self.other_things)
        self.config = mlogger.Config(get_general_info=False,
                                     get_git_info=False)

    def test_init(self):
        config = mlogger.Config(get_general_info=False,
                                get_git_info=False,
                                **self.some_things)
        self.assertDictEqual(config._state, self.some_things)

    def test_setter(self):
        self.config.update(**self.some_things)
        for key, item in self.other_things.items():
            setattr(self.config, key, item)

        self.assertDictEqual(self.all_things, self.config._state)

        # fail when trying to write _state attribute
        with self.assertRaises(TypeError):
            self.config._state = None

    def test_getter(self):
        self.config.update(**self.some_things)
        assert self.config.param1 == self.some_things['param1']
        assert self.config.param2 == self.some_things['param2']

    def test_state_dict(self):
        self.config.update(**self.all_things)
        state = self.config.state_dict()

        self.assertDictEqual(state['_state'], self.all_things)

        new_config = mlogger.Config()
        new_config.load_state_dict(state)

        self.assertDictEqual(new_config.state_dict(), self.config.state_dict())
