"""Pure retained-context image reader; no environment mutation or encoding."""
from pathlib import Path
import gzip
import hashlib
import importlib.util
import torch


def load_context_frames(source, dictionary_module):
    """Read existing lossless dictionary/gzip image caches in original order."""
    frames, grids, ordinals = [], [], []
    for case in source['context_cases']:
        path = Path(case['path'])
        if hashlib.sha256(path.read_bytes()).hexdigest() != case['sha256']:
            raise ValueError('Adopted original context file SHA differs')
        with path.open('rb') as f:
            magic = f.read(2)
        if magic == b'\x1f\x8b':
            with gzip.open(path, 'rb') as f:
                payload = dictionary_module.unpack(torch.load(f, map_location='cpu', weights_only=True))
        else:
            payload = torch.load(path, map_location='cpu', weights_only=True)
        pixels, grid = payload['pixel_values'], payload['image_grid_thw']
        if grid.tolist() != case['grids'] or len(grid) != len(case['samples']):
            raise ValueError('Original native image order/grid count changed')
        offset = 0
        for t,h,w in grid.tolist():
            if t != 1:
                raise ValueError('Only retained individual image patches may be adopted')
            frames.append(pixels[offset:offset+h*w]); grids.append([h,w]); offset += h*w
        if offset != len(pixels):
            raise ValueError('Incomplete retained context patch accounting')
        ordinals.extend(case['samples'])
    if not frames or any(g != grids[0] for g in grids) or len(frames) != source['cells']:
        raise ValueError('Complete original single-grid source observations required')
    return frames, grids[0], ordinals
