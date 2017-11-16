import logger
import numpy as np

from builtins import range


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


n_epochs = 10
use_visdom = True
time_indexing = False
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
acc1_test = xp.acc1_test()
acck_test = xp.acck_test()
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
