# coding: utf-8
# pylint: disable=invalid-name,
""" KVStore in mxnet """
from __future__ import absolute_import
import ctypes
from .narray import NArray
from .narray import zeros
from .base import _LIB
from .base import check_call, c_array, NArrayHandle

def _ctype_key_value(keys, vals):
    """ parse key-value args into ctype"""
    if isinstance(keys, int):
        if isinstance(vals, NArray):
            return (1,
                    c_array(ctypes.c_int, [keys]),
                    c_array(NArrayHandle, [vals.handle]))
        else:
            for v in vals:
                assert(isinstance(v, NArray))
            return (len(vals),
                    c_array(ctypes.c_int, [keys] * len(vals)),
                    c_array(NArrayHandle, [v.handle for v in vals]))
    else:
        for k in keys:
            assert(isinstance(k, int))
        if len(keys) == 1:
            return _ctype_key_value(keys[0], vals)
        assert(len(keys) == len(vals))
        for v in vals:
            assert(isinstance(v, NArray))
        return (len(keys),
                c_array(ctypes.c_int, keys),
                c_array(NArrayHandle, [v.handle for v in vals]))

def init_devices(contexts):
    """ Init key-value store with a list of device contexts

    Parameters
    ----------
    contexts : list of Context
       The list of local devices used by this process
    """
    masks = c_array(ctypes.c_int, [c.device_mask for c in contexts])
    ids = c_array(ctypes.c_int, [c.device_id for c in contexts])
    check_call(_LIB.MXKVStoreInitDevices(len(contexts), masks, ids))

def stop():
    """ stop kvstore """
    check_call(_LIB.MXKVStoreStop())


def init(keys, values):
    """ Initialize a list of key-value pairs

    Parameters
    ----------
    kv_list : tuple or list/generator of tuples
        a key-value tuple or a list of key-value tuples, where key is int and
        key is
    """
    num, ckeys, cvals = _ctype_key_value(keys, values)
    check_call(_LIB.MXKVStoreInit(num, ckeys, cvals))

def push(keys, values):
    """ Push a value into the store

    Parameters
    ----------
    """
    num, ckeys, cvals = _ctype_key_value(keys, values)
    check_call(_LIB.MXKVStorePush(num, ckeys, cvals))

def pull(keys, values):
    """ Pull the value from the store

    Parameters
    ----------
    key : int
        The key
    value : NArray
        The value
    """
    num, ckeys, cvals = _ctype_key_value(keys, values)
    check_call(_LIB.MXKVStorePull(num, ckeys, cvals))

def _updater_wrapper(updater):
    def updater_handle(lhs_handle, rhs_handle):
        lhs = NArray(NArrayHandle(lhs_handle))
        rhs = NArray(NArrayHandle(rhs_handle))
        updater(lhs, rhs)
    return updater_handle

def set_updater(updater):
    """ Register a updater into the store

    Example:
    def Update(grad, weight):
        weight[:] -= lr * grad  / batch_size

    Parameters
    ----------

    """
    _updater_proto = ctypes.CFUNCTYPE(None, NArrayHandle, NArrayHandle)
    global _updater_func
    _updater_func = _updater_proto(_updater_wrapper(updater))
    check_call(_LIB.MXKVStoreSetUpdater(_updater_func))
