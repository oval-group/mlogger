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
train_metrics = xp.ParentWrapper(tag='train', name='parent',
                                 children=(xp.AvgMetric(name='loss'),
                                           xp.AvgMetric(name='acc1'),
                                           xp.AvgMetric(name='acck')))
# same for validation metrics (note all children inherit tag from parent)
val_metrics = xp.ParentWrapper(tag='val', name='parent',
                               children=(xp.AvgMetric(name='loss'),
                                         xp.AvgMetric(name='acc1'),
                                         xp.AvgMetric(name='acck')))

for epoch in range(n_epochs):
    # reset metrics
    train_metrics.reset()
    # accumulate metrics over epoch
    for (x, y) in training_data():
        loss, acc1, acck = oracle(x, y)
        train_metrics.update(loss=loss, acc1=acc1,
                             acck=acck, n=len(x))

    train_metrics.log_and_reset()

    # Method 1 for logging: log all metrics tagged with 'train'
    # xp.log_with_tag('train')
    val_metrics.reset()
    for (x, y) in validation_data():
        loss, acc1, acck = oracle(x, y)
        val_metrics.update(loss=loss, acc1=acc1,
                           acck=acck, n=len(x))
    # Method 2 for logging: log Parent wrapper
    # (automatically logs all children)
    xp.log_metric(val_metrics)

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
