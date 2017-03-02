# A minimalist logger for experiments

## Installation

To install the package, run:
* `pip install -r requirements.txt` (the only requirement is GitPython)
* `python setup.py install`.

## Example

```
import logger

experiment = logger.Experiment("my_experiment")

experiment.log_config(my_hyperparameters_dict)

train_loss = experiment.AvgMetric(tag='train', name='loss')
train_acc1 = experiment.AvgMetric(tag='train', name='acc@1')
train_acck = experiment.AvgMetric(tag='train' name='acc@k')
train_metrics = experiment.ParentMetric(train_loss, train_acc1, train_acck)

train_timer = experiment.TimeMetric(tag='train', name='timer')

test_loss = experiment.AvgMetric(tag='test', name='loss')
test_acc1 = experiment.AvgMetric(tag='test', name='acc@1')
test_acck = experiment.AvgMetric(tag='test', name='acc@k')
test_metrics = experiment.ParentMetric(test_loss, test_acc1, test_acck)

for epoch in my_number_of_epochs:

    train_metrics.reset()

    for mini_batch in my_training_data:

        loss, acc1, acck = my_oracle(mini_batch)
        train_metrics.update(train_loss=loss, train_acc@1=acc1,
                             train_acc@k=acck, n=minibatch.n_samples())

    train_timer.update()
    experiment.log_with_tag('train')

for mini_batch in my_testing_data:

    loss, acc1, acck = my_oracle(mini_batch)
    test_metrics.update(test_loss=loss, test_acc@1=acc1,
                        test_acc@k=acck, n=minibatch.n_samples())

experiment.log_metric(test_metrics)
experiment.to_pickle("my_pickle_log.pkl")
experiment.to_json("my_json_log.json")
```