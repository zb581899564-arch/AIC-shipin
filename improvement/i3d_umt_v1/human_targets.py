"""Original MTurk ordinal targets; edited-video matches are never a substitute."""
from fractions import Fraction
import math


def validate_mturk(annotation, native_pts, physical_end, *, index_convention):
    if index_convention != 'ZERO_BASED_HALF_OPEN':
        raise ValueError('Frame index convention must be evidenced before conversion')
    if not isinstance(annotation, list) or len(annotation) != 2:
        raise ValueError("Expected original [clip_bounds, soft_votes]")
    bounds, votes = annotation
    if len(bounds) != len(votes) or not bounds:
        raise ValueError("Missing or unequal annotation rows")
    pts = [Fraction(t) for t in native_pts]
    if not pts or any(a >= b for a, b in zip(pts, pts[1:])):
        raise ValueError("Native PTS must be strictly increasing")
    result = []
    for interval, vote in zip(bounds, votes):
        start, end = interval
        # Author endpoint convention must be proven in the source manifest first.
        if not float(start).is_integer() or not float(end).is_integer():
            raise ValueError("Nonintegral native frame boundary")
        a, b = int(start), int(end)
        if not 0 <= a < b <= len(pts):
            raise ValueError("Annotation outside verified original native sequence")
        if not math.isfinite(vote) or vote < 0:
            raise ValueError("Unknown vote cannot become a zero/negative label")
        result.append(dict(start_index=a, end_index=b, start=pts[a],
                           end=pts[b] if b < len(pts) else Fraction(physical_end),
                           soft_vote=float(vote)))
    return result


def ordinal_pair_indices(votes):
    """Preserve the human vote ordering without inventing an annotator count."""
    return [(i, j) for i, x in enumerate(votes) for j, y in enumerate(votes) if x > y]


def source_ordinal_loss(logits, votes):
    """One full source, equally weighted pairs; no summary/unselected-as-ordinary rule."""
    import torch.nn.functional as F
    if logits.ndim != 1 or len(logits) != len(votes):
        raise ValueError("Logit/annotation mismatch")
    pairs = ordinal_pair_indices(votes)
    if not pairs:
        raise ValueError("Source supplies no relative human supervision")
    better, worse = zip(*pairs)
    return F.softplus(-(logits[list(better)] - logits[list(worse)])).mean()


def require_media_admission(manifest):
    required = ['original_source_id', 'media_sha256', 'clock_sha256', 'mturk_sha256',
                'author_frame_end_convention', 'original_frame_count_evidence',
                'usage_basis', 'identity_isolation_acceptance']
    missing = [key for key in required if not manifest.get(key)]
    if missing:
        raise ValueError('Not admitted: ' + ', '.join(missing))
    if manifest.get('target_kind') != 'ORIGINAL_MTURK_SOFT_VOTES':
        raise ValueError('Automatic edit matches or summary targets are prohibited here')
    if manifest['author_frame_end_convention'] != 'ZERO_BASED_HALF_OPEN':
        raise ValueError('This converter does not implement an unverified indexing convention')
