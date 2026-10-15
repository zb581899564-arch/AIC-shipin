"""Exact cache helpers only; importing this package never initializes torch/CUDA."""
from .codec import SCHEMA, LOCK_BACKEND, Store, exact_equal, signature
from .leases import LeaseStore

__all__ = ['SCHEMA', 'LOCK_BACKEND', 'Store', 'LeaseStore', 'signature', 'exact_equal']
