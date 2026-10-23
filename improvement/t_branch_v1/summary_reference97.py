"""First remaining fit-source summary masks; adopt existing original native maps."""
from fractions import Fraction
import math

import numpy as np

from t_io import ROOT, check, identity, read, save


def original_spans(source, rows, timeline):
    if len(rows) != source['independent_reviewers']:
        raise ValueError('Complete original reviewer denominator differs')
    names, result = [], []
    for row in rows:
        name = row['annotator_id']
        if not isinstance(name, str) or name in names:
            raise ValueError('Original reviewer identity is missing or duplicated')
        names.append(name); spans = []
        for interval in row['summary_timestamps']:
            score = interval['score']
            if not isinstance(score, (float, int)) or not math.isfinite(score) or score <= 0:
                raise ValueError('Original selected-summary score schema differs')
            lo, hi = (Fraction(str(interval[k])) / 1000 for k in ['start_time', 'end_time'])
            if not 0 <= lo < hi <= timeline.end:
                raise ValueError('Human interval outside native source; no clipping, padding or repair')
            spans.append((lo, hi))
        if not spans:
            raise ValueError('Missing original reference cannot become an empty human target')
        result.append(spans)
    return names, result


def independent_integer_mapping(timeline, all_spans):
    # Exact integer predicates are independent of NativeTimeline's bisect maps.
    values = list(timeline.points) + [x for spans in all_spans for pair in spans for x in pair]
    scale = math.lcm(*{value.denominator for value in values})
    ticks = [value.numerator * (scale // value.denominator) for value in timeline.points]
    if max(value.numerator * (scale // value.denominator) for value in values) > np.iinfo(np.int64).max:
        raise ValueError('Exact integer reference exceeds this implementation; never use float stretching')
    ticks = np.array(ticks, dtype=np.int64); masks = []
    for spans in all_spans:
        mask = np.zeros(len(ticks), dtype=bool)
        for lo, hi in spans:
            first, last = lo.numerator * (scale // lo.denominator), hi.numerator * (scale // hi.denominator)
            mask |= (ticks >= first) & (ticks < last)
        masks.append(mask)
    return masks


def reference(source, timeline, folder):
    sid = source['sid']; previous = ROOT / 'summary_targets28' / (sid + '.json')
    if previous.exists():
        old = read(previous)
        if (old['original_annotations']['sha256'] != source['annotations']['sha256']
                or old['original_clock']['sha256'] != source['clock']['sha256']):
            raise ValueError('Old accepted native reference belongs to different original annotations/clock')
        with np.load(check(old['tensor']), allow_pickle=False) as data:
            masks, domain = data['summary_selected'].copy(), data['summary_task_domain'].copy()
        if masks.shape != (source['independent_reviewers'], len(timeline.points)) or domain.shape != (len(timeline.points),):
            raise ValueError('Accepted original reference dimensions differ')
        return old['all_original_reviewers'], masks, domain, identity(previous), False
    rows = read(check(source['annotations']))
    names, spans = original_spans(source, rows, timeline)
    masks = [timeline.intervals(pairs) for pairs in spans]
    independent = independent_integer_mapping(timeline, spans)
    if any(not np.array_equal(a, b) for a, b in zip(masks, independent)):
        raise ValueError('First independent exact native summary-to-frame predicates differ')
    masks = np.stack(masks); domain = np.ones(len(timeline.points), dtype=bool)
    path = folder / (sid + '_reference.npz')
    with path.open('xb') as stream:
        np.savez_compressed(stream, summary_selected=masks, summary_task_domain=domain)
    meta = folder / (sid + '_reference.json')
    save(meta, dict(state='FIRST_REMAINING_FIT_ORIGINAL_SUMMARY_NATIVE_REFERENCE_PASS',
        source=sid, original_annotations=source['annotations'], original_clock=source['clock'],
        all_original_reviewers=names, tensor=identity(path), frames=len(timeline.points),
        independent_integer_predicate_equals_native_bisect=True,
        unselected_semantics='UNKNOWN_NOT_GENERIC_ORDINARY', score_not_used_as_strength=True,
        whole_source_summary_task_domain=True, no_model_or_inference_input=True))
    return names, masks, domain, identity(meta), True
