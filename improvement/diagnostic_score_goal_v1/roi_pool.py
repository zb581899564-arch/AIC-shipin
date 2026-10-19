"""CPU candidate ROI descriptors over an ACTUAL row-major merged patch grid.

No GT, model, image decoder, candidate construction or calibration lives here.
The caller must establish the actual merged grid and its original-image map.
Tokens may contain full-image attention: ROI pooling does not make them
independent local pixels or an isolated crop observation.
"""
from __future__ import annotations

import numpy as np
from crop_geometry import dimensions, legal, require

PATCH_DIM = 4096
VISUAL_DIM = PATCH_DIM*3
GEOMETRY_DIM = 8
FEATURE_DIM = VISUAL_DIM+GEOMETRY_DIM


def _checked_grid(grid):
    require(isinstance(grid, np.ndarray) and grid.ndim == 3 and grid.shape[2] == PATCH_DIM
            and min(grid.shape[:2]) > 0 and np.issubdtype(grid.dtype, np.floating)
            and bool(np.isfinite(grid).all()), 'Actual finite nonempty[row,col,4096] merged grid required')
    return grid.astype(np.float64, copy=False)


def _area_weights(rows, cols, rectangle):
    """Integrate cell/ROI rectangle overlap, rather than test cell centers."""
    x, y, w, h = rectangle
    require(all(np.isfinite(v) for v in rectangle) and 0 <= x < x+w <= 1+1e-12
            and 0 <= y < y+h <= 1+1e-12 and w > 0 and h > 0,
            'Positive normalized ROI wholly within original image required')
    xs = np.arange(cols+1, dtype=np.float64)/cols
    ys = np.arange(rows+1, dtype=np.float64)/rows
    dx = np.maximum(0., np.minimum(xs[1:], x+w)-np.maximum(xs[:-1], x))
    dy = np.maximum(0., np.minimum(ys[1:], y+h)-np.maximum(ys[:-1], y))
    overlap = dy[:, None]*dx[None, :]
    mass = float(overlap.sum(dtype=np.float64))
    require(np.isfinite(mass) and mass > 0 and abs(mass-w*h) <= 64*np.finfo(np.float64).eps,
            'Empty/incomplete/nonfinite ROI intersection; no zero fill')
    return overlap/mass


def candidate_features(grid, boxes, width, height):
    """Return float32[K,12296] using original integer[x,y,w] candidates.

Height is w*9/16. Visual blocks are ROI-global, left-right and top-bottom
area-weighted patch means. Geometry is normalized x,y,w,h,area,cx,cy,16/9.
"""
    dimensions(width, height)
    value = _checked_grid(grid)
    require(isinstance(boxes, (list, tuple)) and len(boxes) > 0,
            'Nonempty fixed candidate list required')
    rows, cols, _ = value.shape
    weights, geometry = [], []
    for box in boxes:
        require(legal(box, width, height), 'Candidate escaped original implicit-height crop contract')
        px, py, pw = box; ph = pw*9/16
        x, y, w, h = px/width, py/height, pw/width, ph/height
        roi = _area_weights(rows, cols, (x, y, w, h))
        left = _area_weights(rows, cols, (x, y, w/2, h))
        right = _area_weights(rows, cols, (x+w/2, y, w/2, h))
        top = _area_weights(rows, cols, (x, y, w, h/2))
        bottom = _area_weights(rows, cols, (x, y+h/2, w, h/2))
        weights.extend((roi.reshape(-1), (left-right).reshape(-1), (top-bottom).reshape(-1)))
        geometry.append((x, y, w, h, w*h, x+w/2, y+h/2, 16/9))
    # One small matrix product, not repeated full grid copies per candidate.
    pooled = np.stack(weights) @ value.reshape(-1, PATCH_DIM)
    pooled = pooled.reshape(len(boxes), 3, PATCH_DIM)
    pooled[:, 0] -= value.mean(axis=(0, 1), dtype=np.float64)
    result = np.concatenate((pooled.reshape(len(boxes), VISUAL_DIM), np.asarray(geometry, np.float64)), axis=1).astype(np.float32)
    require(result.shape == (len(boxes), FEATURE_DIM) and bool(np.isfinite(result).all()),
            'Finite fixed12296-dimensional ROI descriptor required')
    return result
