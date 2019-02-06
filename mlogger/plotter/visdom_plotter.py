from collections import defaultdict

from .graph import GraphWindow
from .text import TextWindow

# optional visdom
try:
    import visdom
except ImportError:
    visdom = None


class VisdomPlotter(object):
    def __init__(self, visdom_opts, manual_update=False):
        """
        * visdom_opts:
            options for visdom instance
        * mode:
            - if 'automatic', sends data to visdom as soon as data arrives
            - if 'manual', sends data to visdom only when .update_plots() is called by user
        """
        super(VisdomPlotter, self).__init__()

        self.manual_update = manual_update
        self.visdom_opts = visdom_opts

        if self.visdom_opts is None:
            self.visdom_opts = {}

        assert visdom is not None, "visdom could not be imported"

        self.viz = visdom.Visdom(**self.visdom_opts)
        self.graph_wins = {}
        self.text_wins = {}
        self.win_opts = defaultdict(dict)

    def set_win_opts(self, title, opts):
        if 'title' in opts:
            del opts['title']
        self.win_opts[title] = opts

    def _update_xy(self, title, legend, x, y):
        if title not in self.graph_wins:
            self.graph_wins[title] = GraphWindow(
                plotter=self, title=title,
                opts=self.win_opts[title])
        self.graph_wins[title].update(legend, x, y)

    def _update_text(self, title, data_dict):
        if title not in self.text_wins:
            self.text_wins[title] = TextWindow(plotter=self, title=title)
        self.text_wins[title].update(data_dict)

    def update_plots(self):
        for graph_win in self.graph_wins.values():
            graph_win.update_plot()

        for text_win in self.text_wins.values():
            text_win.update_plot()

    def state_dict(self):
        state = {}
        state['repr'] = repr(self)

        state['graph_wins'] = {}
        for title, graph_win in self.graph_wins.items():
            state['graph_wins'][title] = graph_win.state_dict()

        state['text_wins'] = {}
        for title, text_win in self.text_wins.items():
            state['text_wins'][title] = text_win.state_dict()
        return state

    def load_state_dict(self, state):
        for title, graph_win_state in state['graph_wins'].items():
            self.graph_wins[title].load_state_dict(graph_win_state)

        state['text_wins'] = {}
        for title, text_win_state in state['text_wins'].items():
            self.text_wins[title].load_state_dict(text_win_state)

    def __repr__(self):
        repr_ = "VisdomPlotter({visdom_opts}, {manual_update})".format(visdom_opts=self.visdom_opts, manual_update=self.manual_update)
        return repr_
