import pkg_resources
import os
import socket
import git
import time
import sys
import mlogger


class Config(object):
    def __init__(self, plotter=None, plot_title=None,
                 get_general_info=True, get_git_info=False, **kwargs):

        object.__setattr__(self, '_state', {})

        if plotter is not None:
            self.plot_on(plotter, plot_title)
        else:
            object.__setattr__(self, '_plotter', plotter)
            object.__setattr__(self, '_plot_title', plot_title)

        if get_general_info:
            self.update_general_info()

        if get_git_info:
            self.update_git_info()

        self.update(**kwargs)

    def update_general_info(self):
        self.update(
            date_and_time=time.strftime('%d-%m-%Y--%H-%M-%S'),
            mlogger_version=pkg_resources.get_distribution("mlogger").version,
            command_line=' '.join(sys.argv),
            pid=os.getpid(),
            cwd=os.getcwd(),
            hostname=socket.gethostname())

    def update_git_info(self):
        try:
            repo = git.Repo(search_parent_directories=True)
            head = repo.head.commit.tree
            self.update(git_hash=repo.head.object.hexsha,
                        git_diff=repo.git.diff(head))
        except:
            print("I tried to find a git repository in current "
                  "and parent directories but did not find any.")

    def state_dict(self):
        state = {}
        state['repr'] = repr(self)
        state['_state'] = self._state
        state['plot_title'] = self._plot_title
        return state

    def update(self, **kwargs):
        self._state.update(kwargs)
        if self._plotter is not None:
            self._plotter._update_text(self._plot_title, kwargs)
        return self

    def load_state_dict(self, state):
        _state = state['_state']
        object.__setattr__(self, '_state', _state)
        object.__setattr__(self, '_plot_title', state['plot_title'])

    def __repr__(self):
        repr_ = "Config()"
        return repr_

    def plot_on(self, plotter, plot_title):
        # plot current state
        if len(self._state):
            plotter._update_text(plot_title, self._state)

        # store for future logs
        object.__setattr__(self, '_plotter', plotter)
        object.__setattr__(self, '_plot_title', plot_title)

        return self

    def __getattr__(self, key):
        if key == '_state':
            return object.__getattr__(self, _state)
        else:
            return self._state[key]

    def __setattr__(self, key, value):
        if key == '_state':
            raise TypeError("attribute '_state' of Config() does not support assignment")
        self._state[key] = value
