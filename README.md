# A minimalist logger for experiments

## Installation

To install the package, run:
* `pip install -r requirements.txt` (the only requirement is GitPython)
* `python setup.py install`.

## Example

```
import logger

xp = logger.Experiment("xp_name")

xp.log_config(my_hyperparameters_dict)

train_metrics = xp.ParentMetric(xp.AvgMetric(tag='train', name='loss'),
                                xp.AvgMetric(tag='train', name='acc1'),
                                xp.AvgMetric(tag='train', name='acck'))
train_timer = xp.TimeMetric(tag='train', name='timer')

test_metrics = xp.ParentMetric(xp.AvgMetric(tag='test', name='loss'),
                               xp.AvgMetric(tag='test', name='acc1'),
                               xp.AvgMetric(tag='test', name='acck'))

for epoch in my_number_of_epochs:

    train_metrics.reset()

    for mini_batch in my_training_data:

        loss, acc1, acck = my_oracle(mini_batch)
        train_metrics.update(train_loss=loss, train_acc1=acc1,
                             train_acck=acck, n=minibatch.n_samples())

    train_timer.update()
    xp.log_with_tag('train')

for mini_batch in my_testing_data:

    loss, acc1, acck = my_oracle(mini_batch)
    test_metrics.update(test_loss=loss, test_acc1=acc1,
                        test_acck=acck, n=minibatch.n_samples())

xp.log_metric(test_metrics)
xp.to_pickle("my_pickle_log.pkl")
xp.to_json("my_json_log.json")
```