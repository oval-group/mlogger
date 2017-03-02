# A minimalist logger for experiments

## Installation

To install the package, run:
* `pip install -r requirements.txt` (the only requirement is GitPython)
* `python setup.py install`.

## Example

You can subclass `Experiment` to fit your own needs. The subclass `NNExperiment` provides an example for that, by initializing a number of metrics useful to log the training of a neural net:

```
class NNExperiment(Experiment):

    def __init__(self, name):

        super(NNExperiment, self).__init__(name)

        self.add_data_fields(('train_objective',
                              'train_accuracy@1',
                              'train_accuracy@k',
                              'train_timer',
                              'test_objective',
                              'test_accuracy@1',
                              'test_accuracy@k'))
```

Then one can use `NNExperiment` as follows:
```
import logger

experiment = logger.NNExperiment("my_experiment")

train_obj = logger.AvgMetric('train_objective')
train_acc1 = logger.AvgMetric('train_accuracy@1')
train_acck = logger.AvgMetric('train_accuracy@k')
train_timer = logger.TimeMetric('train_timer')

test_obj = logger.AvgMetric('test_objective')
test_acc1 = logger.AvgMetric('test_accuracy@1')
test_acck = logger.AvgMetric('test_accuracy@k')

for epoch in my_number_of_epochs:

    train_obj.reset()
    train_acc1.reset()
    train_acck.reset()

    for mini_batch in my_training_data:

        new_obj, new_acc1, new_acck = my_oracle(mini_batch)
        train_obj.update(new_obj, mini_batch.n_samples())
        train_acc1.update(new_acc1, mini_batch.n_samples())
        train_acck.update(new_acck, mini_batch.n_samples())

    train_timer.update()
    experiment.append_metrics(train_obj, train_acc1, train_acck, train_timer)

for mini_batch in my_testing_data:

    new_obj, new_acc1, new_acck = my_oracle(mini_batch)
    test_obj.update(new_obj, mini_batch.n_samples())
    test_acc1.update(new_acc1, mini_batch.n_samples())
    test_acck.update(new_acck, mini_batch.n_samples())

experiment.append_metrics(test_obj, test_acc1, test_acck)
experiment.to_file("my_log.pkl")
```