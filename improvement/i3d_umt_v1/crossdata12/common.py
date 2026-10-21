"""Fixed cross-dataset pilot paths and native-cell contracts."""
import json
from fractions import Fraction
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
ENGINEERING = ROOT.parent
WORK = ENGINEERING.parent
sys.path.insert(0, str(ENGINEERING))
from provenance import digest, reference, write_new


def read(path):
    return json.loads(Path(path).read_text())


def checked(ref):
    path = Path(ref['path'])
    if ref.get('bytes') is not None and path.stat().st_size != ref['bytes']:
        raise ValueError(f'Byte count mismatch: {path}')
    if digest(path) != ref['sha256']:
        raise ValueError(f'Identity mismatch: {path}')
    return path


def native_cells(n):
    """Disjoint original ordinal cells; short final RGB clips repeat pixels only."""
    import numpy as np
    if n <= 0:
        raise ValueError('No native frames')
    bounds = [(s, min(s + 64, n)) for s in range(0, n, 64)]
    samples = np.array([[min(s + 8*k, e - 1) for k in range(8)] for s, e in bounds])
    groups = np.repeat(np.arange(len(bounds)), [e-s for s, e in bounds])
    assert len(groups) == n and samples.min() == 0 and samples.max() < n
    return bounds, samples, groups


def clock(row):
    c = read(checked(row['clock_ref']))
    pts = [Fraction(p) for p in c['original_exact_pts']]
    n = c.get('n_frames', c.get('native_frames'))
    assert n == len(pts) and all(b > a for a, b in zip(pts, pts[1:]))
    origin = Fraction(c['first_original_pts_exact'])
    end = Fraction(c['physical_end_exact']) + origin
    assert end > pts[-1] and c['source_sha256'] == row['media']['sha256']
    return c, pts, end


def rank_mask(scores, groups, count):
    import numpy as np
    values = np.asarray(scores)[groups]
    if not np.isfinite(values).all() or not 0 <= count <= len(groups):
        raise ValueError('Invalid score/coverage')
    out = np.zeros(len(groups), dtype=bool)
    out[np.argsort(-values, kind='stable')[:count]] = True
    return out


def mean_pair_f1(mask, labels):
    import numpy as np
    labels = np.asarray(labels, dtype=bool)
    assert labels.ndim == 2 and len(labels) == len(mask)
    tp = labels[mask].sum(axis=0)
    denom = int(mask.sum()) + labels.sum(axis=0)
    return float(np.divide(2*tp, denom, out=np.zeros_like(tp, dtype=float), where=denom > 0).mean())
