import os
import logger
import numpy as np

from builtins import range

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
lr = 0.01
n_epochs = 10

#----------------------------------------------------------
# Prepare logging
#----------------------------------------------------------

# create Experiment
xp = logger.Experiment("xp_name", use_visdom=True,
                       visdom_opts={'server': 'http://localhost', 'port': 8097},
                       time_indexing=False, xlabel='Epoch')
# log the hyperparameters of the experiment
xp.log_config({'lr': lr, 'n_epochs': n_epochs})
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
best1 = xp.BestMetric(tag="val-best", name="acc1")
bestk = xp.BestMetric(tag="val-best", name="acck")
xp.AvgMetric(tag="test", name="acc1")
xp.AvgMetric(tag="test", name="acck")

xp.plotter.set_win_opts(name="acc1", opts={'title': 'Accuracy@1'})
xp.plotter.set_win_opts(name="acck", opts={'title': 'Accuracy@k'})
xp.plotter.set_win_opts(name="loss", opts={'title': 'Loss'})

#----------------------------------------------------------
# Training
#----------------------------------------------------------

for epoch in range(n_epochs):
    # train model
    for (x, y) in training_data():
        loss, acc1, acck = oracle(x, y)
        # accumulate metrics (average over mini-batches)
        xp.Parent_Train.update(loss=loss, acc1=acc1,
                               acck=acck, n=len(x))
    # log metrics (i.e. store in xp and send to visdom) and reset
    xp.Parent_Train.log_and_reset()

    for (x, y) in validation_data():
        loss, acc1, acck = oracle(x, y)
        xp.Parent_Val.update(loss=loss, acc1=acc1,
                             acck=acck, n=len(x))
    xp.Parent_Val.log_and_reset()
    best1.update(xp.acc1_val).log()  # will update only if better than previous values
    bestk.update(xp.acck_val).log()  # will update only if better than previous values

for (x, y) in test_data():
    _, acc1, acck = oracle(x, y)
    # update metrics individually
    xp.Acc1_Test.update(acc1, n=len(x))
    xp.Acck_Test.update(acck, n=len(x))
xp.log_with_tag('test')

print("=" * 50)
print("Best Performance On Validation Data:")
print("-" * 50)
print("Prec@1: \t {0:.2f}%".format(best1.value))
print("Prec@k: \t {0:.2f}%".format(bestk.value))
print("=" * 50)
print("Performance On Test Data:")
print("-" * 50)
print("Prec@1: \t {0:.2f}%".format(xp.acc1_test))
print("Prec@k: \t {0:.2f}%".format(xp.acck_test))

#----------------------------------------------------------
# Save & load experiment
#----------------------------------------------------------

# save file
xp.to_json("my_json_log.json")  # or xp.to_pickle("my_pickle_log.pkl")

xp2 = logger.Experiment("")  # new Experiment instance
xp2.from_json("my_json_log.json")  # or xp.from_pickle("my_pickle_log.pkl")
xp2.to_visdom(visdom_opts={'server': 'http://localhost', 'port': 8097})  # plot again data on visdom

# remove the file
os.remove("my_json_log.json")
