"""First CPU acceptance for the new two-view human-summary training inputs.

One explicit new root/profile. Old pixels/clock are adopted, never regenerated.
This entry does not admit or launch GPU training.
"""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''  # CPU child only, never imported by GPU.
from pathlib import Path
from fractions import Fraction
from collections import Counter, defaultdict
import json
import hashlib
import time
import traceback
import torch
from summary_contract import (require, signature, build_pixels, independent_pixels,
    build_text, independent_text, training_suffix, parse_answer)

W = Path('/home/inspur/aic_video_work')
ROOT = W/'bottleneck_24h_20261019_v1'
OLD = W/'score_residual_execution_20261016_v2'


def read(p):
    return json.loads(Path(p).read_text())


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8<<20), b''):
            h.update(b)
    return h.hexdigest()


def ref(p):
    return dict(path=str(Path(p).resolve()), sha256=sha(p), bytes=Path(p).stat().st_size)


def bound(r):
    p = Path(r['path']).resolve()
    require(p.is_relative_to(W) and p.is_file() and sha(p) == r['sha256'], 'Actual adopted file binding differs')
    return p


def save(p, value):
    with Path(p).open('x') as f:
        json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.flush(); os.fsync(f.fileno())


def source_pixels(source):
    """Read/hash retained original image chunks; no old image encoder call."""
    frames, grids, ordinals = [], [], []
    for chunk in source['chunks']:
        p = bound(chunk); payload = torch.load(p, map_location='cpu', weights_only=True)
        pixels, grid = payload['pixel_values'], payload['image_grid_thw']
        require(list(pixels.shape) == chunk['pixel_shape'] and grid.tolist() == chunk['grid']
                and payload['sample_ordinals'] == chunk['samples'], 'Retained image chunk geometry/order changed')
        require(signature({'pixels':pixels})['pixels']['sha256'] == chunk['pixel_sha256'], 'Actual retained pixel SHA changed')
        offset = 0
        for t,h,w in grid.tolist():
            require(t == 1, 'Adopt only accepted individual-image patches')
            frames.append(pixels[offset:offset+h*w]); grids.append([h,w]); offset += h*w
        require(offset == len(pixels), 'Complete old image patch accounting')
        ordinals.extend(chunk['samples'])
    require(len(frames) == source['feature_cells'] == len(ordinals) and all(g == grids[0] for g in grids),
            'Complete consistent original source observation list')
    return frames, grids[0], ordinals


def main():
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU child must mask its own CUDA only')
    torch.set_num_threads(2)
    registration = read(ROOT/'summary_CPU_registration_05.json')
    for r in registration['code'].values():
        bound(r)
    result = read(bound(registration['target_acceptance']))
    require(result['sources'] == 25 and result['windows'] == 144 and result['reviewer_window_targets'] == 2236
            and result['max_native_runs'] == 6, 'Adopt complete first target audit, no dropped references')
    targets = [json.loads(s) for s in bound(result['candidate_targets_ref']).read_text().splitlines()]
    old = read(bound(registration['source_registration']))
    original_sources = {s['sid']:s for s in old['sources'] if s['group'] == 'train'}
    windows = {w['uid']:w for w in old['windows'] if w['sid'] in original_sources}
    accepted = read(bound(registration['retained_image_acceptance']))
    catalog = []
    for s in accepted['sources']:
        p = OLD/'inputs'/s['id']
        clock = p/'clock.json'; native = p/'native.npz'
        require(sha(clock) == s['clock_sha256'] and sha(native) == s['native_sha256'], 'Retained original native mapping binding')
        c = read(clock); original = original_sources[s['id']]
        require(c['source_sha256'] == original['media']['sha256'] and s['name'] == original['name'],
                'Original author source identity must match accepted image source')
        require(c['normalized_exact_pts'] == read(bound(original['clock_ref']))['normalized_exact_pts'],
                'Original human native ordinal clock must equal retained image source clock')
        catalog.append(dict(id=s['id'], name=s['name'], source_sha256=c['source_sha256'],
            clock=ref(clock), native=ref(native), chunks=s['chunks'], feature_cells=s['feature_cells']))
    require(len(catalog) == 25 and len(windows) == 144, 'Exact original train source/window denominator')
    from transformers import AutoProcessor
    cfg = read(bound(registration['model_config']))
    processor = AutoProcessor.from_pretrained(cfg['model_dir'], local_files_only=True)
    out = ROOT/'summary_inputs_05'; out.mkdir(exist_ok=False)
    save(out/'source_catalog.json', dict(sources=catalog))
    by_window = defaultdict(list)
    for row in targets:
        by_window[row['uid']].append(row)
    prepared, supervised = [], []
    window_counts = Counter(w['sid'] for w in windows.values())
    all_weight = Counter(); answer_lengths = []; started = time.monotonic()
    for source in sorted(catalog, key=lambda s:hashlib.sha256(s['source_sha256'].encode()).hexdigest()):
        frames, grid, ordinals = source_pixels(source); clock = read(bound(source['clock']))
        owner = dict(source_id=source['id'], source_sha256=source['source_sha256'])
        for uid,w in windows.items():
            if w['sid'] != source['id']:
                continue
            start, end = w['meta']['window_start'], w['meta']['window_end']
            pixels, plan = build_pixels(frames, grid, ordinals, clock['normalized_exact_pts'], start, end, owner)
            independent_pixels(frames, grid, pixels, plan, ordinals, clock['normalized_exact_pts'])
            encoded, text = build_text(processor, plan, pixels['video_grid_thw'], clock['physical_end_exact'])
            values = dict(**pixels, **encoded)
            independent_text(processor, plan, values, text)
            prefix = out/(uid+'.prefix.pt')
            with prefix.open('xb') as f:
                torch.save(encoded, f); f.flush(); os.fsync(f.fileno())
            request = dict(uid=uid, sid=source['id'], source_sha256=source['source_sha256'],
                plan=plan, grid_hw=grid, prefix_ref=ref(prefix), input_signature=signature(values),
                text=text, source_clock_ref=source['clock'], original_window_ref=w['old_done'],
                first_new_pixel_text_native_QA=True, training_admitted=False)
            request_file = out/(uid+'.json'); save(request_file, request); prepared.append(ref(request_file))
            rows = by_window[uid]
            require({r['reviewer'] for r in rows} == set(range(len(rows))), 'All original reviewer columns, none picked')
            for row in rows:
                parse_answer(row['target_json'], Fraction(end)-Fraction(start))
                suffix = training_suffix(processor.tokenizer, text, encoded['input_ids'], row['target_json'])
                weight = len(targets)/(25*window_counts[source['id']]*len(rows))
                supervised.append(dict(uid=uid, sid=source['id'], reviewer=row['reviewer'],
                    target_json=row['target_json'], suffix_ids=suffix, weight=weight, input_ref=ref(request_file),
                    empty_means_unselected_source_summary_only=True))
                all_weight[source['id']] += weight; answer_lengths.append(len(suffix))
            save(out/(uid+'.first_acceptance.json'), dict(status='PASS_FIRST_TWO_VIEW_INPUT_AND_ALL_REVIEWER_TOKEN_TARGETS',
                 uid=uid, input_ref=ref(request_file), reviewers=len(rows), new_decoder=0, new_image_processor=0,
                 pixel_QA=True, text_stub_QA=True, native_QA=True, all_suffix_EOS_QA=True))
            print(json.dumps(dict(event='FIRST_SUMMARY_INPUT_ACCEPTED', uid=uid, input_tokens=text['prefix_tokens'],
                                  reviewer_targets=len(rows))), flush=True)
            del pixels, values, encoded
        del frames
    require(len(prepared) == 144 and len(supervised) == 2236 and len(all_weight) == 25
            and all(abs(v-len(targets)/25)<1e-9 for v in all_weight.values()), 'Exact full target/source weight accounting')
    with (out/'training_targets.jsonl').open('x') as f:
        for row in supervised:
            f.write(json.dumps(row, ensure_ascii=False, separators=(',',':'))+'\n')
    save(out/'prepared.json', dict(inputs=prepared, training_targets=ref(out/'training_targets.jsonl'),
        source_catalog=ref(out/'source_catalog.json'), all_original_reviewers_equal=True,
        source_weights=dict(all_weight), inference_reference_labels_in_prompt=False))
    save(out/'input_acceptance.json', dict(status='PASS_ALL144_FIRST_NEW_TWO_VIEW_CPU_INPUTS_2236_TOKEN_TARGETS',
        sources=25, windows=144, original_reviewer_targets=2236, empty_targets=780,
        max_native_runs=6, maximum_answer_tokens=max(answer_lengths), new_decoder_calls=0,
        new_image_or_video_encoder_calls=0, new_model_calls=0, new_optimizer_updates=0,
        first_independent_actual_pixel_text_native_label_mask_EOS_QA=True,
        prepared=ref(out/'prepared.json'), registration=ref(ROOT/'summary_CPU_registration_05.json'),
        elapsed_seconds=time.monotonic()-started, training_or_GPU_admitted=False))


if __name__ == '__main__':
    try:
        main()
    except BaseException as e:
        path = ROOT/'summary_CPU_failure_05.json'
        if not path.exists():
            save(path, dict(error=repr(e), traceback=traceback.format_exc(), automatic_retry=False,
                successful_items_preserved=True, first_admission_not_granted=True))
        raise
