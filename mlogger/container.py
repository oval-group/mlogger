import copy
import mlogger
import json
import numpy as np
from builtins import dict
from collections import defaultdict, OrderedDict


class Container(object):

    def __init__(self, **kwargs):
        """
        """
        super(Container, self).__init__()

        object.__setattr__(self, '_children_dict', {})

        for (key, value) in kwargs.items():
            setattr(self, key, value)

    def __setattr__(self, key, value):
        if not isinstance(value, (mlogger.metric.Base, mlogger.Config, Container)):
            raise TypeError("Container object cannot store object with type '{}' (error for key {})"
                            .format(type(value), key))

        self._children_dict[key] = value
        object.__setattr__(self, key, value)

    def __delattr__(self, key):
        object.__delattr__(self, key)
        del self._children_dict[key]

    def state_dict(self):
        state = {}
        state['repr'] = repr(self)
        for key, value in self._children_dict.items():
            state[key] = value.state_dict()
        return state

    def load_state_dict(self, state_dict):
        for (key, new_state) in state_dict.items():
            if key == 'repr' or 'repr' not in new_state:
                continue

            new_object = eval('mlogger.' + new_state['repr'])
            new_object.load_state_dict(new_state)
            setattr(self, key, new_object)

    def children(self):
        return self._children_dict.values()

    def named_children(self):
        return self._children_dict.items()

    def metrics(self):
        metrics_list = []
        for child in self.children():
            if isinstance(child, mlogger.metric.Base):
                metrics_list.append(child)
            elif isinstance(child, Container):
                metrics_list += child.metrics()
        return metrics_list

    def named_metrics(self):
        named_metrics_list = []
        for name, child in self.named_children():
            if isinstance(child, mlogger.metric.Base):
                named_metrics_list.append((name, child))
            elif isinstance(child, Container):
                for child_metric_name, child_metric in child.named_metrics():
                    print(name, child_metric_name)
                    named_metrics_list.append(("{}.{}".format(name, child_metric_name), child_metric))
        return named_metrics_list

    def plot_on(self, plotter):
        for child in self.children():
            if isinstance(child, Container):
                child.plot_on(plotter)
            elif isinstance(child, mlogger.Config):
                plot_title = child._plot_title
                child.plot_on(plotter, plot_title)
            elif isinstance(child, mlogger.metric.Base):
                plot_title = child._plot_title
                plot_legend = child._plot_legend
                if plot_title is not None:
                    child.plot_on(plotter, plot_title, plot_legend)

    def __repr__(self):
        _repr = "Container()"
        return _repr

    def save_to(self, filename):
        with open(filename, "w") as f:
            json.dump(self.state_dict(), f)


def load_container(filename):
    with open(filename, "r") as f:
        state_dict = json.load(f)

    container = eval("mlogger." + state_dict['repr'])
    container.load_state_dict(state_dict)
    return container
