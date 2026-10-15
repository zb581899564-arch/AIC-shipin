"""JSON-only exact-second helpers. No model, processor, decoder or network imports."""
from bisect import bisect_left
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

HOME = Path('/home/inspur/aic_video_work')
ARMS = ('ordinary', 'redundant')
GATES = dict(full_group_denominator=4,
    macro_paired_all_rater_duration_F1_delta_min='0',
    macro_all_rater_precision_delta_min='0', per_source_F1_delta_min='-1/100',
    minimum_sources_with_real_changed_native_frames=1, maximum_invalid_decisions=0)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def ref(path):
    path = Path(path).resolve()
    return dict(path=str(path), sha256=sha(path))


def checked(value):
    require(isinstance(value, dict) and set(value) == {'path', 'sha256'}, 'Explicit immutable path/SHA reference required')
    path = Path(value['path']).resolve()
    require(path.is_relative_to(HOME) and path.is_file() and sha(path) == value['sha256'],
            'Changed, missing or out-of-workspace metadata: '+str(path))
    return path


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def merged(spans):
    result = []
    for a, b in sorted((F(a), F(b)) for a, b in spans):
        require(0 <= a < b, 'Invalid exact-second interval')
        if result and a <= result[-1][1]:
            result[-1][1] = max(b, result[-1][1])
        else:
            result.append([a, b])
    return result


def serialized(spans):
    return [[str(a), str(b)] for a, b in merged(spans)]


def metrics(pred, reference):
    pred, reference = merged(pred), merged(reference)
    p = sum((b-a for a, b in pred), F(0))
    r = sum((b-a for a, b in reference), F(0))
    intersection = sum((max(F(0), min(b, d)-max(a, c))
        for a, b in pred for c, d in reference), F(0))
    return dict(f1=F(0) if not p+r else 2*intersection/(p+r),
        precision=F(0) if not p else intersection/p,
        recall=F(0) if not r else intersection/r)


def frames(spans, points):
    selected = set()
    for a, b in merged(spans):
        selected.update(range(bisect_left(points, a), bisect_left(points, b)))
    return selected


def exact_metrics(values):
    return {key: dict(exact=str(value), value=float(value)) for key, value in values.items()}


def validate_indices(parsed, count):
    require(isinstance(parsed, dict) and set(parsed) == set(ARMS), 'Exactly ordinary/redundant decision arrays required')
    for arm in ARMS:
        indices = parsed[arm]
        require(isinstance(indices, list) and all(type(i) is int and 0 <= i < count for i in indices)
            and len(indices) == len(set(indices)), 'Invalid or repeated '+arm+' candidate index')
    return parsed


def validate_gates(protocol):
    gates = protocol.get('deletion_quality_gates', protocol.get('quality_gates'))
    require(isinstance(gates, dict) and all(key in gates for key in GATES), 'All preregistered deletion gates required')
    for key, value in GATES.items():
        require(F(str(gates[key])) == F(str(value)), 'Deletion gate changed: '+key)
    return gates
