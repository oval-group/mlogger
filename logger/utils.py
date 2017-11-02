import numpy as np

try:
    import torch
    import torch.autograd as torch_autograd
except ImportError:
    torch = None
    torch_autograd = None


def to_float(val):
    """ Check that val is one of the following:
    - pytorch autograd Variable with one element
    - pytorch tensor with one element
    - numpy array with one element
    - any type supporting float() operation
    And convert val to float
    """

    if isinstance(val, np.ndarray):
        assert val.size == 1, \
            "val should have one element (got {})".format(val.size)
        return float(val.squeeze()[0])

    if torch is not None:
        if isinstance(val, torch_autograd.Variable):
            val = val.data
        if torch.is_tensor(val):
            assert torch.numel(val) == 1, \
                "val should have one element (got {})".format(torch.numel(val))
            return float(val.squeeze()[0])

    try:
        return float(val)
    except:
        raise TypeError("Unsupported type for val ({})".format(type(val)))
