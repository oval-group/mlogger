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

    n_elements = 1
    if isinstance(val, np.ndarray):
        n_elements = val.size
    elif torch is not None and (isinstance(val, torch_autograd.Variable) or torch.is_tensor(val)):
        n_elements = torch.numel(val)

    assert n_elements == 1, \
        "val should have one element (got {})".format(n_elements)
    try:
        return float(val)
    except:
        raise TypeError("Unsupported type for val ({})".format(type(val)))
