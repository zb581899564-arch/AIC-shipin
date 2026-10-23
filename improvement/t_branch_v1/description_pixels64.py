"""New annotation-bound views, adopting matching already materialized native RGB."""
from collections import defaultdict
from fractions import Fraction

from native_sets import NativeTimeline
from t_io import ROOT, check, identity, read, save


def prior_pixels():
    result = {}
    for ref in read(ROOT / 'pilot_input_qa29/completion.json')['accepted']:
        proof = read(check(ref)); meta = read(check(proof['input']))
        result[meta['case_id']] = dict(input=meta)
    return result


def prepare_views(examples, view_root, rt, processor):
    from pilot_inputs27 import source_pixels, window_meta
    from time_control50_prepare import encode_case
    old = prior_pixels(); by_source = defaultdict(list)
    for example in examples:
        by_source[example['source']['sid']].append(example)
    result = {}
    for sid, rows in by_source.items():
        source = rows[0]['source']; clock = read(check(source['clock']))
        check(source['media'])
        points = NativeTimeline.from_clock(clock).points
        windows = [row[key] for row in rows for key in ('correct_view', 'wrong_native_view')]
        pictures = source_pixels(source, clock, points, windows, old)
        for example in rows:
            physical = {}
            for kind, key in [('correct', 'correct_view'), ('wrong', 'wrong_native_view')]:
                name = example['example_id'] + '_' + kind
                folder = view_root / name; folder.mkdir()
                meta = window_meta(source, clock, points, example[key], pictures, folder)
                physical[kind] = encode_case(rt, processor, meta, folder)
                print('DESCRIPTION64_FIRST_REAL_VIEW', sid, name, flush=True)
            result[example['example_id']] = physical
        save(view_root / (sid + '_completion.json'), dict(source=source, first_encoded_view_pairs={
            row['example_id']: result[row['example_id']] for row in rows},
            exact_original_annotation_intervals=True, old_RGB_adopted_where_same_native_ordinal=True,
            no_new_human_or_semantic_ordinary_labels=True))
        del pictures
    return result
