# A simple logger for experiments

Full credits to the authors of [tnt](https://github.com/pytorch/tnt) for the structure with metrics.

## Installation

To install the package, run:
* `pip install -r requirements.txt` (the only requirement are `GitPython` and `numpy`, `visdom` is optional but recommended for real-time visualization)
* `python setup.py install`.

## Examples
An toy example can be found at `examples/example.py`:

```python
import logger
import numpy as np

# code to generate fake data
# ...

n_epochs = 10
use_visdom = True
# some hyperparameters we wish to save for this experiment
hyperparameters = dict(regularization=1,
                       n_epochs=n_epochs)
# options for the remote visualization backend                       
visdom_opts = dict(server='http://localhost',
                   port=8097)
xp = logger.Experiment("xp_name", use_visdom=use_visdom,
                       visdom_opts=visdom_opts)
# log the hyperparameters of the experiment
xp.log_config(hyperparameters)
# create parent metric for training metrics (easier interface)
train_metrics = xp.ParentMetric(tag='train', name='parent',
                                children=(xp.AvgMetric(name='loss'),
                                          xp.AvgMetric(name='acc1'),
                                          xp.AvgMetric(name='acck')))
# same for validation metrics (note all children inherit tag from parent)
val_metrics = xp.ParentMetric(tag='val', name='parent',
                              children=(xp.AvgMetric(name='loss'),
                                        xp.AvgMetric(name='acc1'),
                                        xp.AvgMetric(name='acck')))

for epoch in range(n_epochs):
    # reset training metrics
    train_metrics.reset()
    # accumulate metrics over epoch
    for (x, y) in training_data():
        loss, acc1, acck = oracle(x, y)
        train_metrics.update(loss=loss, acc1=acc1,
                             acck=acck, n=len(x))
    # Method 1 for logging: log all metrics tagged with 'train'
    xp.log_with_tag('train')

    for (x, y) in validation_data():
        loss, acc1, acck = oracle(x, y)
        val_metrics.update(loss=loss, acc1=acc1,
                           acck=acck, n=len(x))
    # Method 2 for logging: log Parent metric
    # (automatically logs all children)
    xp.log_metric(val_metrics)

# save to pickle file
xp.to_pickle("my_pickle_log.pkl")
# save to json file
xp.to_json("my_json_log.json")
```

This generates the following plot on `visdom`:
![alt text](examples/example.jpg)