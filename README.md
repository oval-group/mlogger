# A simple logger for experiments [![Build Status](https://travis-ci.org/oval-group/logger.svg?branch=master)](https://travis-ci.org/oval-group/logger)

Full credits to the authors of [tnt](https://github.com/pytorch/tnt) for the structure with metrics.

## Installation

To install the package, run:
* `pip install -r requirements.txt` (the only requirement are `GitPython` and `numpy`, `visdom` is optional but recommended for real-time visualization)
* `python setup.py install`.

## Usage

There are two types of objects in this package: `Experiment` and `Metric`. An `Experiment` instance serves as an interface, and all `Metric` objects are reattached to it (details below).


### Logging Hyper-Parameters

Hyper-parameters can easily be stored in the configuration of an experiment, by passing a dictionary to `log_config`:
```python
xp = logger.Experiment("my_xp_name")  # creating an experiment
n_epochs = 100
lr = 0.01
hp_dict = dict(n_epochs=n_epochs, lr=lr)  # create dictionary of hyper-parameters
xp.log_config(hp_dict)  # store hyper-parameters in experiment
```

The main use case of this package is to use metrics to monitor various values during an experiment. We detail this below.

### Initializing a Metric

Metrics are instantiated through the experiment object:
```python
xp = logger.Experiment("my_xp_name")  # creating an experiment
xp.SimpleMetric(name="score")  # creating a simple metric
```

A metric is identified by a combination of name (required when creating the metric) and tag (optional, set to "default" by default). A suggestion for machine learning is to use tags like "train", "val" and "test" to identify metrics on training, validation and testing data sets. We recommend to use strings in lower case without special characters for the names and tags.

### Types of Metrics
* `SimpleMetric`: yields the value of the last update
* `TimeMetric`: yields the time difference between the last update and the last reset
* `AvgMetric`: yields the (possibly weighted) average of all updates since last reset
* `SumMetric`: yields the (possibly weighted) sum of all updates since last reset
* `BestMetric`: yields the best value given in update since last reset (maximal in "max" mode, minimal in "min" mode)
* `DynamicMetric`: requires a function to obtain its value, yields value obtained by a function call at last update
* `ParentWrapper`: wraps around children Metrics, whcih all inherit its tag, yields a dictionary with values of its children

### Indexing a Metric

Every metric is indexed by either a `ValueIndex` or a `TimeIndex` (except `TimeMetric`, which is always indexed by a `ValueIndex`). This allows to have values for an x-axis when logging the information. The index is modified when the metric is logged (more on that below). By default, `TimeIndex` updates its value at the time of the log, and `ValueIndex` increments a counter by one.

The default behavior is that all metrics are indexed by a `TimeIndex`. This can be changed to a default behavior of value indexing by setting `time_indexing=False` when creating the `Experiment`.

### Accessing a Metric Object

A metric can be accessed by any of the following:
* The object returned at instantiation:
```python
xp = logger.Experiment("my_xp_name")
my_metric = xp.SimpleMetric(name="score", tag="cool")
```
* A call to `get_metric` on the `Experiment` object:
```python
xp = logger.Experiment("my_xp_name")
xp.SimpleMetric(name="score", tag="cool")
my_metric = xp.get_metric(name="score", tag="cool")
```

* An attribute request to the `Experiment` object based with the formatting `{}_{}`.format(name, tag).title() of the metric:
```python
xp = logger.Experiment("my_xp_name")
xp.SimpleMetric(name="score", tag="cool")
my_metric = xp.Score_Cool
```

NB: if the metric has the "default" tag, it can be accessed without the tag:
```python
xp = logger.Experiment("my_xp_name")
xp.SimpleMetric(name="score")
my_metric = xp.Score
```

### Updating & Getting the Value of a Metric

The value of a metric is updated through the `update` method, and obtained by a call to the `get` method:
```python
xp = logger.Experiment("my_xp_name")
xp.SimpleMetric(name="score")
xp.Score.update(10) # set the value of the metric to 10.
xp.Score.get() # returns 10.
```

The value given in the `update` method of a metric must be one of the following:
* pytorch autograd Variable with one element
* pytorch tensor with one element
* numpy array with one element
* any type supported by the python `float()` function

It is then converted to a python `float` number.

For a `ParentWrapper`, the arguments of `update` must be named with child names, and the `get` method returns a dictionary:
```python
xp = logger.Experiment("my_xp_name")
xp.ParentWrapper(name="parent",
                 children=(xp.SimpleMetric("child1"),
                           xp.SimpleMetric("child2"),
                           xp.SimpleMetric("child3"))
xp.Parent.update(child1=3, child2=5) # set the value of the metric xp.Child1 to 3. and xp.Child2 to 5.
xp.Parent.update(child3=9) # set the value of the metric xp.Child3 to 9.
xp.Parent.get() # returns {'child1': 3., 'child2': 5., 'child3': 9.}
```

### Logging a Metric

When a metric is storing a value worth keeping or displaying, it should be logged through:
```python
xp = logger.Experiment("my_xp_name")
xp.SimpleMetric(name="score")
xp.Score.update(10) # set the value of the metric to 10
xp.Score.log() # log value of metric (preferred syntax)
xp.log_metric(name="score") # equivalent syntax
```

This logs the value of the metric in the attribute `logged` of `xp`. It also updates the `ValueIndexer` or the `TimeIndex` of the metric. If `xp` is connected to a plotting backend (e.g. `visdom`), this also sends the value of the metric to be displayed.


### Resetting a Metric

Some metrics need to be reset manually, e.g. `AvgMetric` or `TimeMetric`. This can be done through the `reset` method:
```python
xp = logger.Experiment("my_xp_name")
xp.SumMetric(name="score")
xp.Score.update(3)
xp.Score.get()  # return 3.
xp.Score.update(2)
xp.Score.get()  # return 5.
xp.Score.reset()
xp.Score.get()  # return 0.
```

Note that instead of calling `log()` followed by `reset()`, a metric can be logged and reset through a single call to `log_and_reset()`.

### Saving an Experiment

Experiments can be easily saved to `json` or `pickle` formats (and can then be loaded). Saving an `Experiment` stores the hyper-parameters logged, and all values of metrics logged throughout the experiment. All metrics and their unlogged values are discarded. The syntax is as follows:

```python
xp = logger.Experiment("my_xp_name", time_indexing=False)
xp.log_config({'n_epochs': 100, 'lr': 0.01})
xp.SimpleMetric(name="score", tag="cool")
xp.SimpleMetric(name="score", tag="cooler")
xp.Score_Cool.update(2.5)
xp.Score_Cool.log()
xp.Score_Cool.update(3.6)
xp.Score_Cool.log()
xp.Score_Cooler.update(5.7)
xp.Score_Cooler.log()
xp.Score_Cooler.update(6.8)
xp.Score_Cooler.log()
xp.to_json("my_xp.json")  # or xp.to_pickle("my_xp.pkl")

del xp

xp = logger.Experiment("dummy_name")
xp.from_json("my_xp.json")  # or xp.from_pickle("my_xp.pkl")
xp.name  # "my_xp_name"
xp.config  # {'n_epochs': 100, 'lr': 0.01}
xp.logged  # {'cool': {'score': {[0, 2.5], [1, 3.6]}}, 'cooler': {'score': {[0, 5.7], [1, 6.8]}}}
xp.to_visdom()  # send the logged data to visdom
```

## Example
In `examples/example.py`, we provide a toy example that puts together these functionalities:

```python
import logger
import numpy as np

from builtins import range


#...
# code to generate fake data
#...


n_epochs = 10
use_visdom = True
time_indexing = True
# some hyperparameters we wish to save for this experiment
hyperparameters = dict(regularization=1,
                       n_epochs=n_epochs)
# options for the remote visualization backend
visdom_opts = dict(server='http://localhost',
                   port=8097)
xp = logger.Experiment("xp_name", use_visdom=use_visdom,
                       visdom_opts=visdom_opts,
                       time_indexing=time_indexing)
# log the hyperparameters of the experiment
xp.log_config(hyperparameters)
# create parent metric for training metrics (easier interface)
xp.ParentWrapper(tag='train', name='parent',
                 children=(xp.AvgMetric(name='loss'),
                           xp.AvgMetric(name='acc1'),
                           xp.AvgMetric(name='acck')))
# same for validation metrics (note all children inherit tag from parent)
xp.ParentWrapper(tag='val', name='parent',
                 children=(xp.AvgMetric(name='loss'),
                           xp.AvgMetric(name='acc1'),
                           xp.AvgMetric(name='acck')))
xp.AvgMetric(tag="test", name="acc1")
xp.AvgMetric(tag="test", name="acck")

for epoch in range(n_epochs):
    # accumulate metrics over epoch
    for (x, y) in training_data():
        loss, acc1, acck = oracle(x, y)
        xp.Parent_Train.update(loss=loss, acc1=acc1,
                               acck=acck, n=len(x))
    xp.Parent_Train.log_and_reset()

    for (x, y) in validation_data():
        loss, acc1, acck = oracle(x, y)
        xp.Parent_Val.update(loss=loss, acc1=acc1,
                             acck=acck, n=len(x))
    xp.Parent_Val.log()
    xp.Parent_Val.reset()

for (x, y) in test_data():
    _, acc1, acck = oracle(x, y)
    # update metrics individually
    xp.Acc1_Test.update(acc1, n=len(x))
    xp.Acck_Test.update(acck, n=len(x))

# access to current values of metric with property of xp in lower case:
# xp.acc1_test is equivalent to xp.Acc1_Test.get()
acc1_test = xp.acc1_test
acck_test = xp.acck_test
print("Performance On Test Data:")
print("-" * 50)
print("Prec@1: \t {0:.2f}%".format(acc1_test))
print("Prec@k: \t {0:.2f}%".format(acck_test))

# save to pickle file
xp.to_pickle("my_pickle_log.pkl")
# save to json file
xp.to_json("my_json_log.json")

xp2 = logger.Experiment("")
xp2.from_json("my_json_log.json")
xp2.to_visdom()

xp3 = logger.Experiment("")
xp3.from_pickle("my_pickle_log.pkl")
xp3.to_visdom()

```

This generates the following plot on `visdom`:
![alt text](examples/example.jpg)
