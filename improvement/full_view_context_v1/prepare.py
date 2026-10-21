"""Adopt seven successful inverses; first recover only the remaining 49."""
from fractions import Fraction
import sys
import numpy as np
import torch
from common import ROOT, WORK, PREVIOUS, CLIP, checked, read, ref, write, save_array
from render import center_view, full_view, contracts


def inverse_frame(source, case):
    sys.path.insert(0, str(PREVIOUS / 'code'))
    from patch_inverse import recover_uint8
    path = checked(dict(path=case['context_path'], sha256=case['context_sha256']))
    content = torch.load(path, map_location='cpu', weights_only=True)
    grids = content['image_grid_thw'].tolist()
    index = case['context_query_index']
    assert grids[index] == case['grid']
    lengths = [int(np.prod(g)) for g in grids]
    start = sum(lengths[:index])
    profile = read(checked(case['profile']))
    rgb, integer_error, normalized_error = recover_uint8(
        content['pixel_values'][start:start + lengths[index]], grids[index], profile['processor_dict'])
    target = ROOT / 'inverse' / f'{source["sid"]}_{case["native_ordinal"]}.npy'
    save_array(target, rgb)
    record = dict(sid=source['sid'], ordinal=case['native_ordinal'], cached_view=ref(target),
                  original_context_sha256=case['context_sha256'], integer_error=integer_error,
                  normalized_error=normalized_error, adopted=False)
    with (ROOT / 'inverse_journal.jsonl').open('a') as stream:
        import json
        stream.write(json.dumps(record) + '\n')
    return rgb, record


def reference_rows(inventory, old_inputs):
    annotations = {r['video_id']: r for r in read(checked(old_inputs['author_annotation']))}
    result = []
    for source in inventory['sources']:
        if not source['chosen']:
            continue
        old = next(s for s in old_inputs['sources'] if s['sid'] == source['sid'])
        clock = read(checked(old['clock']))
        assert clock['source_sha256'] == source['media_sha256']
        pts = [Fraction(clock['original_exact_pts'][c['native_ordinal']]) for c in source['chosen']]
        annotation = annotations[source['name']]
        queries = []
        for qid in old['query_ids']:
            query = old_inputs['queries'][qid]
            assert query['query_id'] == qid and query['sid'] == source['sid']
            assert query['text'] == annotation['tsum'][query['event']]
            start, end = map(lambda v: Fraction(str(v)), annotation['timestamps'][query['event']])
            labels = [int(start <= time < end) for time in pts]
            valid = 0 < sum(labels) < len(labels)
            queries.append(dict(query_id=qid, event=query['event'], positive=labels, scorable=valid,
                                reason=None if valid else 'SINGLE_CLASS_AT_FIXED_HASH_POINTS'))
        result.append(dict(sid=source['sid'], name=source['name'], queries=queries,
                           ordinals=[c['native_ordinal'] for c in source['chosen']],
                           exact_pts=[str(p) for p in pts], clock=old['clock']))
    return result


def main():
    protocol = read(ROOT / 'protocol.json')
    inventory_path = PREVIOUS / 'full_view_cache_inventory10.json'
    old_inverse_path = PREVIOUS / 'input_inverse11_acceptance.json'
    assert ref(inventory_path)['sha256'] == protocol['inventory_sha256']
    assert ref(old_inverse_path)['sha256'] == protocol['inverse7_sha256']
    inventory, old_inverse = read(inventory_path), read(old_inverse_path)
    old_inputs = read(CLIP / 'input_acceptance.json')
    references = reference_rows(inventory, old_inputs)
    valid_queries = sum(q['scorable'] for r in references for q in r['queries'])
    valid_sources = sum(any(q['scorable'] for q in r['queries']) for r in references)
    support = dict(valid_sources=valid_sources, valid_queries=valid_queries,
                   supported=valid_sources >= protocol['minimum_support']['sources'] and
                             valid_queries >= protocol['minimum_support']['queries'])
    write(ROOT / 'point_reference.json', dict(sources=references, support=support,
          annotation=old_inputs['author_annotation'], metric='Sparse same-native-point AP; never dense frame AP',
          timestamps_in_encoder=False, historical_exposure=True))
    if not support['supported']:
        write(ROOT / 'input_acceptance.json', dict(status='STOP_INSUFFICIENT_FIXED_POINT_SUPPORT', support=support))
        return
    contract = contracts()
    (ROOT / 'inverse').mkdir()
    adopted = {(r['sid'], r['ordinal']): r for r in old_inverse['sources']}
    frames, rows = [], []
    for source in inventory['sources']:
        for case in source['chosen']:
            key = source['sid'], case['native_ordinal']
            if key in adopted:
                row = adopted[key]
                assert row['cached_context_sha256'] == case['context_sha256']
                rgb = np.load(checked(row['cached_view']), allow_pickle=False)
                inverse = dict(sid=key[0], ordinal=key[1], cached_view=row['cached_view'], adopted=True)
            else:
                rgb, inverse = inverse_frame(source, case)
            assert rgb.dtype == np.uint8 and list(rgb.shape) == [case['grid'][1] * 16, case['grid'][2] * 16, 3]
            center, (full, info) = center_view(rgb), full_view(rgb)
            assert center.shape == full.shape == (224, 224, 3) and not np.array_equal(center, full)
            index = len(frames)
            frames.extend([center, full])
            rows.append(dict(sid=key[0], ordinal=key[1], center_index=index, full_index=index + 1,
                             cached_inverse=inverse, full_renderer=info, recovered_shape=list(rgb.shape)))
    assert len(rows) == 56 and sum(r['cached_inverse']['adopted'] for r in rows) == 7
    pixels = np.stack(frames)
    save_array(ROOT / 'pixels.npy', pixels)
    old_text = read(CLIP / 'inference_completion.json')['text']
    text = np.load(checked(old_text), allow_pickle=False)
    assert text.shape == (26, 512) and np.isfinite(text).all()
    weight = ref(CLIP / 'model/ViT-B-32.pt')
    assert weight['sha256'] == protocol['weight_sha256'] and weight['bytes'] == 353976522
    write(ROOT / 'input_acceptance.json', dict(status='PASS56_SAME_NATIVE_RGB_TWO_VIEWS', pixels=ref(ROOT / 'pixels.npy'),
          rows=rows, point_reference=ref(ROOT / 'point_reference.json'), text=old_text, weight=weight,
          adopted_inverse7=ref(old_inverse_path), adopted_packing_contract=old_inverse['contract'],
          inverse_helper=ref(PREVIOUS / 'code/patch_inverse.py'), new_inverses=49, adopted_inverses=7,
          new_original_decode=0, new_original_processor=0, text_reencoding=0, render_contract=contract,
          support=support, original_full_resolution_recovered=False, production_allowed=False))


if __name__ == '__main__':
    main()
