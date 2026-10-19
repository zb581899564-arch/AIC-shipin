"""Separately admitted, label-free production input preparation and CPU reuse.

The protected40.47 ZIP is the only baseline authority.  The inherited native
NPZ is used for observation ownership and sample ordinals, never its baseline.
This module cannot admit GPU inference, training or packaging.
"""
from __future__ import annotations

import argparse
import datetime as dt
from fractions import Fraction
import hashlib
import importlib
import json
from numbers import Integral
from pathlib import Path
import sys
import traceback
import zipfile

_support = Path(__file__).resolve().parents[1]/'pair_code_17'
if _support.is_dir():
    sys.path.insert(0, str(_support))
import pair_common
import pair_preference_math
import pair_video_input
from pair_common import WORK, bound, read, ref, require, save, sha, signature, utc
from pair_preference_math import prepare_policy
from pair_video_input import (pair_video_pixels, build_text_input,
                              independent_pixel_check, independent_text_check)


PROTECTED_SHA = 'b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'
SCHEMA = 'EXPLICIT_PAIR_PRODUCTION_INPUTS_V21'
GATE_STATUS = 'PASS_ALL426_NEW_TWO_VIDEO_PRODUCTION_INPUTS'
PRODUCTION_IDS = {str(i) for i in range(426)}


def _deadline(reg):
    limit = dt.datetime.fromisoformat(reg['deadline_utc'].replace('Z', '+00:00'))
    require(limit.tzinfo is not None and dt.datetime.now(dt.timezone.utc) < limit,
            'No new production preparation after registered goal deadline')


def registration21(root):
    """Check the independent21 registration; never call registration17."""
    root = Path(root).resolve()
    require(root.is_relative_to(WORK.resolve()), 'Production main root outside Linux work root')
    reg = read(root/'pair_production_registration_21.json')
    require(reg['schema'] == SCHEMA, 'Explicit independent production21 registration required')
    require(bound(reg['code']) == Path(__file__).resolve(), 'Actual production21 preparation code differs')
    for name, module in [('pair_common', pair_common), ('pair_video_input', pair_video_input),
                         ('pair_preference_math', pair_preference_math)]:
        require(bound(reg['helper_code'][name]) == Path(module.__file__).resolve(),
                'Actual frozen production helper differs: '+name)
    for original in reg['old_helpers']:
        bound(original)
    require(reg['protected_baseline']['sha256'] == PROTECTED_SHA,
            'Only protected40.47 may define the production baseline')
    bound(reg['protected_baseline']); bound(reg['accepted_production'])
    quality = read(bound(reg['approved_quality']))
    require(quality.get('production_prepare_approved') is True,
            'Explicit successful-quality approval before production CPU preparation')
    bound(reg['model_config']); bound(reg['original_pairing_proof'])
    return reg


def protected_masks(rows, native_lengths):
    """Read exact zero-based native frame membership, including40.47 additions.

    Neither old native.baseline nor a time-to-frame rounding path is accepted.
    Complete source identity, duplicate frames and physical endpoints are strict.
    """
    import numpy as np
    require(isinstance(rows, list) and isinstance(native_lengths, dict), 'Complete baseline rows/native lengths required')
    require(all(isinstance(sid, str) and type(n) is int and n > 0 for sid, n in native_lengths.items()),
            'Original positive integer native lengths required')
    masks = {}
    for row in rows:
        sid = row['video_id']
        require(isinstance(sid, str) and sid in native_lengths and sid not in masks,
                'Duplicate, missing or unknown protected baseline source')
        require(isinstance(row['predictions'], list), 'Original prediction frame list required')
        mask = np.zeros(native_lengths[sid], dtype=np.bool_)
        previous = -1
        for prediction in row['predictions']:
            frame = prediction['frame']
            require(type(frame) is int and previous < frame < len(mask),
                    'Protected frames must be unique ordered zero-based native ordinals')
            mask[frame] = True; previous = frame
        masks[sid] = mask
    require(set(masks) == set(native_lengths), 'Every original source needs its protected baseline record')
    return masks


def load_protected_masks(path, native_lengths):
    # Reading the member verifies its own ZIP CRC; do not repeat old strict QA.
    with zipfile.ZipFile(path) as archive:
        require(archive.namelist() == ['predictions.jsonl'], 'Protected baseline has one original JSONL member')
        rows = [json.loads(line) for line in archive.read('predictions.jsonl').splitlines() if line.strip()]
    return protected_masks(rows, native_lengths)


def source_geometry(source, baseline):
    """Adopt original ownership/clock; never read native.npz['baseline']."""
    import numpy as np
    with np.load(bound(source['native']), allow_pickle=False) as native:
        cells = native['groups'].copy()
        ordinals = native['sample_ordinals'].copy()
    groups = np.load(bound(source['native_groups']), allow_pickle=False)
    require(isinstance(groups, np.ndarray), 'Original paired native_groups.npy required')
    groups = groups.copy()
    n = source['native_frames']
    require(type(n) is int and n > 0 and len(groups) == len(cells) == n,
            'Unchanged complete original native domain required')
    require(isinstance(baseline, np.ndarray) and baseline.dtype == np.bool_ and baseline.shape == (n,),
            'Protected ZIP bool native baseline required')
    require(ordinals.ndim == 1 and ordinals.dtype.kind in 'iu' and len(ordinals) == source['feature_cells']
            and len(ordinals) > 0 and (ordinals < n).all()
            and (ordinals >= 0).all() and (np.diff(ordinals.astype(np.int64)) > 0).all(),
            'Exact unique ordered original observation ordinals required')
    clock = read(bound(source['clock']))
    raw_points = clock['normalized_exact_pts']
    require(clock['source_sha256'] == source['source_sha256'] and len(raw_points) == n
            and all(isinstance(x, (str, Integral, Fraction)) and not isinstance(x, bool) for x in raw_points),
            'Original exact native clock/source identity required')
    points = [Fraction(int(x)) if isinstance(x, Integral) else Fraction(x) for x in raw_points]
    require(points[0] == 0 and all(a < b for a, b in zip(points, points[1:])),
            'Original native PTS must remain strictly increasing with zero origin')
    inventory = prepare_policy(groups, cells, baseline)
    require(int(cells[-1])+1 == len(ordinals), 'Original observation/native ownership domain differs')
    return dict(groups=groups, cells=cells, sample_ordinals=ordinals.tolist(), clock=clock, inventory=inventory)


def candidate_requests(inventory, make_input):
    """No anchor/no candidate is an explicit abstention, with zero input calls."""
    if inventory['anchor'] is None:
        return []
    return [dict(clip=clip, first_id=make_input(clip, inventory['anchor']),
                 reverse_id=make_input(inventory['anchor'], clip)) for clip in inventory['candidates']]


def source_status(inventory):
    if inventory['anchor'] is None:
        return 'ABSTAIN_NO_COMPLETE_BASELINE_ANCHOR'
    if not inventory['candidates']:
        return 'ABSTAIN_NO_DISJOINT_COMPLETE_CANDIDATE'
    return 'PASS_NEW_PRODUCTION_SOURCE_INPUTS'


def _source_pixels(reg):
    """Use the registered old loader and reject accidental module shadowing."""
    old_code = Path(reg['accepted_production']['path']).parent/'code'
    expected = {Path(r['path']).name: bound(r) for r in reg['old_helpers']}
    require(all(name in expected for name in ('data.py', 'common.py', 'mapping.py')),
            'Exact old image loader and native helpers must be independently bound')
    require(expected['data.py'] == (old_code/'data.py').resolve(), 'Image loader must belong to accepted production input root')
    sys.path.insert(0, str(old_code))
    module = importlib.import_module('data')
    for name, filename in [('data', 'data.py'), ('common', 'common.py'), ('mapping', 'mapping.py')]:
        actual = sys.modules[name]
        require(Path(actual.__file__).resolve() == expected[filename], 'Old loader module shadowed: '+name)
    return module.source_pixels


def _save_baseline(path, mask, source_sha256):
    import numpy as np
    import os
    with Path(path).open('xb') as stream:
        np.savez(stream, baseline=mask, source_sha256=np.asarray(source_sha256),
                 protected_baseline_sha256=np.asarray(PROTECTED_SHA))
        stream.flush(); os.fsync(stream.fileno())


def prep(root):
    import os
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'Only this production CPU child masks CUDA')
    import numpy as np
    import torch
    from transformers import AutoProcessor
    torch.set_num_threads(2)
    root = Path(root).resolve(); reg = registration21(root); _deadline(reg)
    out = root/'pair_production_21'; out.mkdir(exist_ok=False)
    save(out/'claim.json', dict(utc=utc(), registration=ref(root/'pair_production_registration_21.json'), pid=os.getpid()))
    inputs = []; completed_sources = []
    try:
        accepted = read(bound(reg['accepted_production']))
        sources = accepted['sources']
        require(accepted['status'] == 'PASS_ALL_NEW_VIDEO_INPUTS_AND_FIRST_INDEPENDENT_QA'
                and accepted['scope'] == 'production' and len(sources) == 426
                and {s['id'] for s in sources} == PRODUCTION_IDS,
                'Adopt only the exact originally accepted426 production sources')
        proof = read(bound(reg['original_pairing_proof']))
        require(proof['status'] == 'PASS_DIRECT_VIDEO_PROCESSOR_BIT_EQUAL_EVEN_AND_ODD',
                'Adopt original successful pairing proof without repeating processor')
        masks = load_protected_masks(bound(reg['protected_baseline']), {s['id']: s['native_frames'] for s in sources})
        source_catalog = out/'source_catalog.json'
        save(source_catalog, dict(sources=sources, original_acceptance=reg['accepted_production'],
                                 inherited_success_only=True, new_independent_sources=False))
        destination = out/'inputs'; destination.mkdir()
        loader = _source_pixels(reg); processor = None; class_ids = None; requests = {}
        for source in sources:
            _deadline(reg)
            sid = source['id']; src_dir = destination/sid; src_dir.mkdir()
            geometry = source_geometry(source, masks[sid]); inventory = geometry['inventory']
            baseline_path = src_dir/'protected_baseline.npz'
            _save_baseline(baseline_path, masks[sid], source['source_sha256'])
            frames = None; grid = None; ordinals = None
            source_start = len(inputs)

            def make_input(a, b):
                nonlocal frames, grid, ordinals, processor, class_ids
                _deadline(reg)
                ranges = [[a['cell_start'], a['cell_end_exclusive']], [b['cell_start'], b['cell_end_exclusive']]]
                key = hashlib.sha256(json.dumps([source['source_sha256'], ranges], separators=(',', ':')).encode()).hexdigest()[:24]
                cid = sid+'_'+key
                if cid in requests:
                    return cid
                if frames is None:
                    frames, grid, ordinals = loader(source)
                    require(ordinals == geometry['sample_ordinals'], 'Actual inherited image/native observation order differs')
                if processor is None:
                    cfg = read(bound(reg['model_config']))
                    processor = AutoProcessor.from_pretrained(cfg['model_dir'], local_files_only=True,
                        max_pixels=65536, min_pixels=65536)
                pair = pair_video_pixels(frames, grid, ranges, ordinals, geometry['clock']['normalized_exact_pts'],
                                         pairing_proof_ref=reg['original_pairing_proof'])
                encoded, text = build_text_input(processor, pair)
                independent_pixel_check(frames, grid, ranges, ordinals, geometry['clock']['normalized_exact_pts'], pair)
                independent_text_check(processor, pair, encoded, text)
                if class_ids is None:
                    class_ids = text['class_token_ids']
                require(text['class_token_ids'] == class_ids, 'Unchanged actual production digit-token mapping required')
                token_path = src_dir/(cid+'.tokens.pt')
                with token_path.open('xb') as stream:
                    torch.save(encoded, stream); stream.flush(); os.fsync(stream.fileno())
                restored = torch.load(token_path, map_location='cpu', weights_only=True)
                require(signature(restored) == signature(encoded), 'New production token save/reload differs')
                values = dict(**encoded, pixel_values_videos=pair['pixel_values_videos'], video_grid_thw=pair['video_grid_thw'])
                path = src_dir/(cid+'.json')
                save(path, dict(id=cid, source_id=sid, source_sha256=source['source_sha256'], clip_ranges=ranges,
                    clip_A=a, clip_B=b, tokens=ref(token_path), class_token_ids=class_ids,
                    input_signature=signature(values), video_grid_thw=pair['video_grid_thw'].tolist(),
                    text_evidence=text, clip_metadata=pair['clip_metadata'], sample_bindings=pair['sample_bindings'],
                    clock=source['clock'], native=source['native'], native_groups=source['native_groups'],
                    protected_baseline=reg['protected_baseline'], baseline_mask=ref(baseline_path),
                    old_pairing_proof=reg['original_pairing_proof'], role='PRODUCTION_NO_LABELS',
                    original_decode=0, original_processor_calls=0, target_or_GT_in_prompt=False))
                requests[cid] = ref(path)
                inputs.append(dict(id=cid, source_id=sid, input=requests[cid], role='PRODUCTION_NO_LABELS'))
                return cid

            candidates = candidate_requests(inventory, make_input)
            record = dict(id=sid, source_sha256=source['source_sha256'], clock=source['clock'], native=source['native'],
                native_groups=source['native_groups'], baseline_mask=ref(baseline_path), inventory=inventory,
                candidates=candidates, status=source_status(inventory), native_frames=source['native_frames'],
                baseline_native_frames=int(masks[sid].sum()), new_unique_inputs=len(inputs)-source_start)
            save(src_dir/'source_acceptance.json', dict(**record, actual_image_grid=grid,
                original_decode=0, original_processor_calls=0, reference_labels_read=False,
                inherited_source_isolation=True, independent_new_source=False))
            record['source_acceptance'] = ref(src_dir/'source_acceptance.json')
            completed_sources.append(record)
            print('FIRST_PRODUCTION_CPU_INPUTS', sid, record['status'], record['new_unique_inputs'], flush=True)
            del frames
        require(len(completed_sources) == 426 and {s['id'] for s in completed_sources} == PRODUCTION_IDS
                and len({r['id'] for r in inputs}) == len(inputs), 'All426 explicit source outcomes and unique new requests required')
        prepared = out/'prepared.json'
        save(prepared, dict(source_catalog=ref(source_catalog), dev_inputs=inputs, sources=completed_sources,
            class_token_ids=class_ids, protected_baseline=reg['protected_baseline'],
            original_processor_calls=0, original_decode=0, reference_labels_read=False,
            role='PRODUCTION_NO_LABELS', no_train_targets=True))
        require(not torch.cuda.is_initialized(), 'Production preparation cannot initialize CUDA')
        save(out/'input_acceptance.json', dict(status=GATE_STATUS, prepared=ref(prepared),
            registration=ref(root/'pair_production_registration_21.json'), sources=426, inputs=len(inputs),
            class_token_ids=class_ids, protected_baseline=reg['protected_baseline'],
            source_status_counts={s: sum(r['status'] == s for r in completed_sources)
                                  for s in sorted({r['status'] for r in completed_sources})},
            independent_pixels_and_text=True, old_pairing_QA_adopted=reg['original_pairing_proof'],
            original_processor_calls=0, original_decode=0, new_real_vision_processor_calls=0,
            reference_labels_read=False, new_independent_sources=False, production_GPU_admitted=False))
    except BaseException as error:
        save(out/'failure.json', dict(error=repr(error), traceback=traceback.format_exc(),
            completed_new_inputs=inputs, completed_sources=completed_sources,
            preserve_all_success=True, no_automatic_retry=True, failure_is_not_empty=True))
        raise


class ProductionInputs:
    """Actual21 first-QA input replay, with at most one source pixel cache."""
    def __init__(self, root):
        self.root = Path(root).resolve(); self.reg = registration21(self.root)
        gate = read(self.root/'pair_production_21/input_acceptance.json')
        require(gate['status'] == GATE_STATUS and gate['registration'] == ref(self.root/'pair_production_registration_21.json'),
                'Exact independent21 registration and actual full production first QA required')
        self.prepared = read(bound(gate['prepared']))
        catalog = read(bound(self.prepared['source_catalog']))
        self.sources = {s['id']: s for s in catalog['sources']}
        require(set(self.sources) == PRODUCTION_IDS and len(self.prepared['sources']) == 426
                and {s['id'] for s in self.prepared['sources']} == PRODUCTION_IDS
                and self.prepared['protected_baseline'] == self.reg['protected_baseline'],
                'Exact426 production source and protected baseline binding required')
        entries = self.prepared['dev_inputs']
        require(all(e['role'] == 'PRODUCTION_NO_LABELS' for e in entries)
                and len({e['id'] for e in entries}) == len(entries), 'Only unique label-free production requests allowed')
        self.expected = {e['id']: e for e in entries}
        self.cache = {}; self.source_pixels = _source_pixels(self.reg)

    def get(self, reference):
        import torch
        request = read(bound(reference)); sid = request['source_id']; cid = request['id']
        expected = self.expected[cid]; source = self.sources[sid]
        require(expected['input'] == reference and expected['source_id'] == sid
                and request['source_sha256'] == source['source_sha256']
                and request['class_token_ids'] == self.prepared['class_token_ids']
                and request['role'] == 'PRODUCTION_NO_LABELS', 'Actual accepted21 production request/source/classes differ')
        if sid not in self.cache:
            self.cache.clear()  # Drop the previous source before loading the next.
            frames, grid, ordinals = self.source_pixels(source)
            clock = read(bound(source['clock']))
            require(clock['source_sha256'] == source['source_sha256']
                    and len(clock['normalized_exact_pts']) == source['native_frames'], 'Original production native clock/source identity')
            self.cache[sid] = frames, grid, ordinals, clock['normalized_exact_pts']
        frames, grid, ordinals, points = self.cache[sid]
        pair = pair_video_pixels(frames, grid, request['clip_ranges'], ordinals, points,
                                 pairing_proof_ref=self.reg['original_pairing_proof'])
        tokens = torch.load(bound(request['tokens']), map_location='cpu', weights_only=True)
        values = dict(**tokens, pixel_values_videos=pair['pixel_values_videos'], video_grid_thw=pair['video_grid_thw'])
        require(signature(values) == request['input_signature'] and pair['video_grid_thw'].tolist() == request['video_grid_thw']
                and pair['clip_metadata'] == request['clip_metadata'] and pair['sample_bindings'] == request['sample_bindings'],
                'Actual production pixels/tokens/native mapping differ from first independent21 QA')
        ids = request['class_token_ids']
        require(values['input_ids'].shape[0] == 1 and 0 < values['input_ids'].shape[1] < 4096
                and len(ids) == len(set(ids)) == 3 and all(type(i) is int and i >= 0 for i in ids),
                'Actual production token-plus-digit budget and distinct classes')
        return values, request


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--root', type=Path, required=True)
    prep(parser.parse_args().root)
