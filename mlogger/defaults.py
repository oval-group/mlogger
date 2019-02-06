import mlogger

mlogger._time_indexing = False


def use_time_indexing(use=True):
    assert use is True or use is False
    mlogger._time_indexing = use
