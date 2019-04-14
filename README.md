# MLogger: a Machine Learning logger

Currently in version alpha, the API might undergo some minor changes.

## Installation

To install the package, run:
* `pip install mlogger`

## Why Use MLogger?
These are the strengths of `mlogger` that make it a useful tool for logging machine learning experiments.

* Readable code that is easy to add to current projects:
```python
acc = mlogger.metric.Average()
acc.update(100)
acc.update(92)
print(acc.value)  # 96.0
acc.log()  # internally stores value of 96.0 with automatic time-stamp
acc.reset()  # reset average value
```
* Flexible use of metrics with containers, easy to save and re-load:
```python
xp = mlogger.Container()
xp.train = mlogger.Container()
xp.train.accuracy = mlogger.metric.Average()
xp.total_timer = mlogger.metric.Timer()

xp.total_timer.reset()  # start timer
xp.train.accuracy.update(97)
xp.total_timer.update()  # say 0.0001 second has elapsed since timer started, current_value is 0.0001
xp.save_to('saved_state.json')

new_xp = mlogger.load_container('saved_state.json')
print(new_xp.train.accuracy.value)  # 97.0
print(new_xp.total_timer.value)  # 0.0001
```

* Improve your user experience with `visdom`:
    * Ease of use:
    ```python
    plotter = mlogger.VisdomPlotter(({'env': 'my_experiment', 'server': 'http://localhost', 'port': 8097})
    acc = mlogger.metric.Average(plotter=plotter, plot_title="Accuracy")
    acc.update(100)
    acc.update(92)
    print(acc.value)  # 96.0
    acc.log()  # automatically sends 96.0 to visdom server on window with title 'Accuracy'
    ```
    * Robustness: if `visdom` fails to send data (due to a network instability for instance), `logger` automatically caches it and tries to send it together with the next request
    * Performance: you can manually choose when to update the `visdom` plots. This permits to batch the data being sent and yields considerable speedups when logging thousands or more points per second.

* Save all output printed in the console to a text file
```python
with mlogger.stdout_to('printed_stuff.txt'):
    # code printing stuff here...
```
* Automatically save information about the date, time, current directory, machine name, version control status of the code.
```python
cfg = mlogger.Config(get_general_info=True, get_git_info=True)
print(cfg.date_and_time, cfg.cwd, cfg.git_hash, cfg.git_diff)
```

## Example
The following example shows some functionalities of the package (full example code in `examples/example.py`):

```python
import mlogger
import numpy as np

#...
# code to generate fake data
#...


# some hyper-parameters of the experiment
use_visdom = True
lr = 0.01
n_epochs = 10

#----------------------------------------------------------
# Prepare logging
#----------------------------------------------------------

# log the hyperparameters of the experiment
if use_visdom:
    plotter = mlogger.VisdomPlotter({'env': 'my_experiment', 'server': 'http://localhost', 'port': 8097},
                                   manual_update=True)
else:
    plotter = None

xp = mlogger.Container()

xp.config = mlogger.Config(plotter=plotter)
xp.config.update(lr=lr, n_epochs=n_epochs)

xp.epoch = mlogger.metric.Simple()

xp.train = mlogger.Container()
xp.train.acc1 = mlogger.metric.Average(plotter=plotter, plot_title="Accuracy@1", plot_legend="training")
xp.train.acck = mlogger.metric.Average(plotter=plotter, plot_title="Accuracy@k", plot_legend="training")
xp.train.loss = mlogger.metric.Average(plotter=plotter, plot_title="Objective")
xp.train.timer = mlogger.metric.Timer(plotter=plotter, plot_title="Time", plot_legend="training")

xp.val = mlogger.Container()
xp.val.acc1 = mlogger.metric.Average(plotter=plotter, plot_title="Accuracy@1", plot_legend="validation")
xp.val.acck = mlogger.metric.Average(plotter=plotter, plot_title="Accuracy@k", plot_legend="validation")
xp.val.timer = mlogger.metric.Timer(plotter=plotter, plot_title="Time", plot_legend="validation")

xp.val_best = mlogger.Container()
xp.val_best.acc1 = mlogger.metric.Maximum(plotter=plotter, plot_title="Accuracy@1", plot_legend="validation-best")
xp.val_best.acck = mlogger.metric.Maximum(plotter=plotter, plot_title="Accuracy@k", plot_legend="validation-best")


#----------------------------------------------------------
# Training
#----------------------------------------------------------


for epoch in range(n_epochs):
    # train model
    for metric in xp.train.metrics():
        metric.reset()
    for (x, y) in training_data():
        loss, acc1, acck = oracle(x, y)
        # accumulate metrics (average over mini-batches)
        batch_size = len(x)
        xp.train.loss.update(loss, weighting=batch_size)
        xp.train.acc1.update(acc1, weighting=batch_size)
        xp.train.acck.update(acck, weighting=batch_size)
    xp.train.timer.update()
    for metric in xp.train.metrics():
        metric.log()

    # reset metrics in container xp.val
    # (does not include xp.val_best.acc1 and xp.val_best.acck, which we do not want to reset)
    for metric in xp.val.metrics():
        metric.reset()

    # update values on validation set
    for (x, y) in validation_data():
        _, acc1, acck = oracle(x, y)
        batch_size = len(x)
        xp.val.acc1.update(acc1, weighting=batch_size)
        xp.val.acck.update(acck, weighting=batch_size)
    xp.val.timer.update()
    # log values on validation set
    for metric in xp.val.metrics():
        metric.log()

    # update best values on validation set
    xp.val_best.acc1.update(xp.val.acc1.value)
    xp.val_best.acck.update(xp.val.acck.value)
    # log best values on validation set
    for metric in xp.val_best.metrics():
        metric.log()

print("=" * 50)
print("Best Performance On Validation Data:")
print("-" * 50)
print("Prec@1: \t {0:.2f}%".format(xp.val_best.acc1.value))
print("Prec@k: \t {0:.2f}%".format(xp.val_best.acck.value))

plotter.update_plots()

#----------------------------------------------------------
# Save & load experiment
#----------------------------------------------------------

xp.train.loss.reset()
xp.train.loss.update(1)
print('Train loss value before saving state: {}'.format(xp.train.loss.value))

xp.save_to('state.json')

new_plotter = mlogger.VisdomPlotter(visdom_opts={'env': 'my_experiment', 'server': 'http://localhost', 'port': 8097},
                                    manual_update=True)

new_xp = mlogger.load_container('state.json')
new_xp.plot_on(new_plotter)
new_plotter.update_plots()

print('Current train loss value: {}'.format(new_xp.train.loss.value))
new_xp.train.loss.update(2)
print('Updated train loss value: {}'.format(new_xp.train.loss.value))

# # remove the file
os.remove('state.json')
```

This generates (twice) the following plots on `visdom`:
![alt text](examples/example.jpg)


## Acknowledgements

Full credits to the authors of [tnt](https://github.com/pytorch/tnt) for the structure with metrics.