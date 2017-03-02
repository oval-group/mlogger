# A minimalist logger for experiments

## Installation

To install the package, run `python setup.py install`.

## API:

### SumMetric, AvgMetric


### Experiment

## Example

You can subclass `Experiment` to fit your own needs. The subclass `NNExperiment` provides an example for that, by initializing a number of metrics useful to log the training of a neural net:

```
class NNExperiment(Experiment):

    def __init__(self, name):

        super(NNExperiment, self).__init__(name)

        self.add_data_fields(('train_objective',
                              'train_accuracy@1',
                              'train_accuracy@k',
                              'test_objective',
                              'test_accuracy@1',
                              'test_accuracy@k'))

        self.add_timers(('train',
                         'test'))
```