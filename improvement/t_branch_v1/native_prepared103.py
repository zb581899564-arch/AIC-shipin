"""One bounded CPU load and GPU transfer per micro; identical tensors serve both calls."""
from concurrent.futures import ThreadPoolExecutor
import json

import torch

from native_input99 import values
from t_io import check, read


class Prefetch:
    """One next CPU input, deterministic order, no CUDA in the producer."""
    def __init__(self, items, loader):
        self.items = iter(items)
        self.loader = loader
        self.worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix='native-input')
        self.pending = None

    def __enter__(self):
        self.advance()
        return self

    def advance(self):
        item = next(self.items, None)
        self.pending = None if item is None else (item, self.worker.submit(self.loader, item))

    def __iter__(self):
        while self.pending is not None:
            item, future = self.pending
            prepared = future.result()
            self.advance()
            yield item, prepared

    def __exit__(self, *unused):
        self.worker.shutdown(wait=True, cancel_futures=True)


def prepare(case, proof, tokenizer, rt):
    actual = values(case, proof, tokenizer, rt)
    if any(v.is_cuda for v in actual.values() if torch.is_tensor(v)):
        raise ValueError('CPU producer unexpectedly created a CUDA tensor')
    return actual


def versions(values):
    tensors = {key: (v.data_ptr(), v._version, tuple(v.shape), tuple(v.stride()), str(v.dtype), str(v.device))
               for key, v in values.items() if torch.is_tensor(v)}
    tensors['non_tensor_values'] = json.dumps({k: v for k, v in values.items() if not torch.is_tensor(v)},
                                             sort_keys=True)
    return tensors


def transfer(actual, proof, rt):
    row = read(check(proof))
    gpu = {key: value.cuda() if torch.is_tensor(value) else value for key, value in actual.items()}
    signature = rt.tensor_signature({key: value.cpu() if torch.is_tensor(value) else value
                                     for key, value in gpu.items()})
    if signature != row['actual_signature']:
        raise ValueError('Single actual GPU transfer differs from first native CPU input')
    return gpu, signature, versions(gpu)


def unchanged(actual, expected):
    if versions(actual) != expected:
        raise ValueError('Greedy generation mutated the accepted shared input tensors')


def causal_values(gpu, history):
    result = dict(gpu)
    result.update({key: history[key].cuda() for key in ['input_ids', 'attention_mask']})
    return result
