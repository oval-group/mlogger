import os
import torch
import mlogger
import numpy as np

from builtins import range
from torch.utils.tensorboard import SummaryWriter

np.random.seed(1234)


def random_data_generator():
    """ fake data generator
    """
    n_batches = np.random.randint(1, 10)
    for _ in range(n_batches):
        batch_size = np.random.randint(1, 5)
        data = np.random.normal(size=(batch_size, 3))
        target = np.random.randint(10, size=batch_size)
        yield (data, target)


def training_data():
    return random_data_generator()


def validation_data():
    return random_data_generator()


def test_data():
    return random_data_generator()


def oracle(data, target):
    """ fake metric data generator
    """
    loss = np.random.rand()
    acc1 = np.random.rand() + 70
    acck = np.random.rand() + 90

    return loss, acc1, acck


# some hyper-parameters of the experiment
use_visdom = True
use_tensorboard = True
lr = 0.01
n_epochs = 10

#----------------------------------------------------------
# Prepare logging
#----------------------------------------------------------

# log the hyperparameters of the experiment
if use_visdom:
    visdom_plotter = mlogger.VisdomPlotter({'env': 'my_experiment', 'server': 'http://localhost', 'port': 8097},
                                   manual_update=True)
else:
    visdom_plotter = None

if use_tensorboard:
    summary_writer = SummaryWriter()
else:
    summary_writer = None

xp = mlogger.Container()

xp.config = mlogger.Config(visdom_plotter=visdom_plotter, summary_writer=summary_writer)
xp.config.update(lr=lr, n_epochs=n_epochs)

xp.epoch = mlogger.metric.Simple()

xp.train = mlogger.Container()
xp.train.acc1 = mlogger.metric.Average(visdom_plotter=visdom_plotter, summary_writer=summary_writer, plot_title="Accuracy@1", plot_legend="training")
xp.train.acck = mlogger.metric.Average(visdom_plotter=visdom_plotter, summary_writer=summary_writer, plot_title="Accuracy@k", plot_legend="training")
xp.train.loss = mlogger.metric.Average(visdom_plotter=visdom_plotter, summary_writer=summary_writer, plot_title="Objective")
xp.train.timer = mlogger.metric.Timer(visdom_plotter=visdom_plotter, summary_writer=summary_writer, plot_title="Time", plot_legend="training")

xp.val = mlogger.Container()
xp.val.acc1 = mlogger.metric.Average(visdom_plotter=visdom_plotter, summary_writer=summary_writer, plot_title="Accuracy@1", plot_legend="validation")
xp.val.acck = mlogger.metric.Average(visdom_plotter=visdom_plotter, summary_writer=summary_writer, plot_title="Accuracy@k", plot_legend="validation")
xp.val.timer = mlogger.metric.Timer(visdom_plotter=visdom_plotter, summary_writer=summary_writer, plot_title="Time", plot_legend="validation")

xp.val_best = mlogger.Container()
xp.val_best.acc1 = mlogger.metric.Maximum(visdom_plotter=visdom_plotter, summary_writer=summary_writer, plot_title="Accuracy@1", plot_legend="validation-best")
xp.val_best.acck = mlogger.metric.Maximum(visdom_plotter=visdom_plotter, summary_writer=summary_writer, plot_title="Accuracy@k", plot_legend="validation-best")


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

visdom_plotter.update_plots()

#----------------------------------------------------------
# Save & load experiment
#----------------------------------------------------------

xp.train.loss.reset()
xp.train.loss.update(1)
print('Train loss value before saving state: {}'.format(xp.train.loss.value))

xp.save_to('state.json')

new_visdom_plotter = mlogger.VisdomPlotter(visdom_opts={'env': 'my_experiment', 'server': 'http://localhost', 'port': 8097},
                                    manual_update=True)
new_summary_writer = SummaryWriter()

new_xp = mlogger.load_container('state.json')
new_xp.plot_on_visdom(new_visdom_plotter)
new_visdom_plotter.update_plots()

# new_xp.plot_on_tensorboard(new_summary_writer)

print('Current train loss value: {}'.format(new_xp.train.loss.value))
new_xp.train.loss.update(2)
print('Updated train loss value: {}'.format(new_xp.train.loss.value))

# # remove the file
os.remove('state.json')
