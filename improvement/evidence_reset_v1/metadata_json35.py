"""Serialization-only conversion, preserving scalar values and old evidence."""
import numpy as np


def native(value):
    if isinstance(value,np.generic):return value.item()
    if isinstance(value,dict):return {key:native(item)for key,item in value.items()}
    if isinstance(value,(list,tuple)):return [native(item)for item in value]
    return value
