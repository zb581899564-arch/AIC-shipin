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
    if isinstance(n, (bool, np.bool_)) or not isinstance(n, (int, np.integer)) or n <= 0:
        raise ValueError('A positive integer native frame count is required')
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
    """Select an exact native-frame budget; invalid group indices never wrap."""
    import numpy as np
    scores, groups = np.asarray(scores), np.asarray(groups)
    if (scores.ndim != 1 or not scores.size or scores.dtype.kind not in 'fiu'
            or not np.isfinite(scores).all()):
        raise ValueError('A finite one-dimensional cell score vector is required')
    if (groups.ndim != 1 or not groups.size or groups.dtype.kind not in 'iu'
            or groups.min() < 0 or groups.max() >= len(scores)):
        raise ValueError('Native groups must be nonnegative integer cell indices')
    if (isinstance(count, (bool, np.bool_)) or not isinstance(count, (int, np.integer))
            or not 0 <= count <= len(groups)):
        raise ValueError('Invalid score/coverage')
    values = scores[groups]
    out = np.zeros(len(groups), dtype=bool)
    # Avoid negating uint / the minimum signed integer. Reversing both the
    # input order and sorted order keeps native-order ties in descending rank.
    descending = len(values) - 1 - np.argsort(values[::-1], kind='stable')[::-1]
    out[descending[:count]] = True
    return out


def binary_membership(values, *, ndim, name):
    """Validate before casting: NaN, -1 and soft votes are not membership."""
    import numpy as np
    values = np.asarray(values)
    if (values.ndim != ndim or not values.size or values.dtype.kind not in 'bifu'
            or not np.isfinite(values).all()
            or not np.logical_or(values == 0, values == 1).all()):
        raise ValueError(f'{name} must contain finite binary membership with {ndim} dimensions')
    return values.astype(np.bool_, copy=False)


def comparison_targets(data):
    """Load this complete-source NPZ contract, not an arbitrary metadata file.

    Only the registered ``known`` label-mask column is accepted; another known-
    related column needs explicit adoption rather than being silently ignored.
    """
    mask = binary_membership(data['baseline'], ndim=1, name='baseline')
    labels = binary_membership(data['labels'], ndim=2, name='labels')
    if len(labels) != len(mask):
        raise ValueError('Baseline and reviewer labels have different native domains')
    known_keys = {key for key in data.keys() if 'known' in key.lower()}
    if not known_keys <= {'known'}:
        raise ValueError('Unregistered known-label mask requires explicit adoption')
    if 'known' in known_keys:
        import numpy as np
        known = np.asarray(data['known'])
        if known.dtype != np.bool_ or known.shape != labels.shape or not known.all():
            raise ValueError('Complete-source F1 requires all reviewer memberships to be known')
    return mask, labels


def mean_pair_f1(mask, labels):
    """External summary proxy; preserve this pilot's both-empty=0 convention.

    This historical convention differs from the official joint metric and the
    native-preference helper. Changing it would be a new metric, not a repair.
    """
    import numpy as np
    mask = binary_membership(mask, ndim=1, name='selection')
    labels = binary_membership(labels, ndim=2, name='labels')
    if len(labels) != len(mask):
        raise ValueError('Selection and reviewer labels have different native domains')
    tp = labels[mask].sum(axis=0)
    denom = int(mask.sum()) + labels.sum(axis=0)
    return float(np.divide(2*tp, denom, out=np.zeros_like(tp, dtype=float), where=denom > 0).mean())
