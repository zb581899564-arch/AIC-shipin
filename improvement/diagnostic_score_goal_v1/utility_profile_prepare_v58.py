"""Conditional CPU58 inputs; never a quality or GPU admission.

--root ROOT --scope resized20|resized19|native19 reads the explicit
utility_profile_CPU_registration_58_<scope>.json, schema
UTILITY_CONDITIONAL_PROFILE_CPU_V58. Required path/SHA refs: preparation_code,
input_code(31), geometry_code(31), recovery_code(34), model_config,
quality_result56, adapter_weights, value_weights, source_catalog, case_plan,
CPU_targets. Also scope,expected_source_ids,deadline_utc,max_seconds;
native_prepared/native_input_acceptance/native_output_acceptance are nullable;
profile_acceptanceRef is mandatory for resized19; recovery_receipts is a list.
Main supplies fixed GT-free19 metadata, since old36 was never executed.

Output utility_profile_inputs_58/<scope> is exclusive. All pools/BASE/indices
remain in original native coordinates. Resized renders use exact diagonal
affine extents; the GT transform is written only to a separate CPU target file.
New crop encodings are losslessly gzip(torch.saveBytes), never old source
patches. Reader callbacks never open CPU targets. No model/decoder is used.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
from fractions import Fraction
import gzip
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import time
import traceback

import numpy as np
from PIL import Image
import torch

_support = Path(__file__).resolve().parents[1]/'pair_code_17'
if _support.is_dir(): sys.path.insert(0, str(_support))
from pair_common import read, save, ref, bound, require, signature, utc

SCHEMA = 'UTILITY_CONDITIONAL_PROFILE_CPU_V58'
GATE = 'PASS_UTILITY58_NEW_PROFILE_INPUTS_FIRST_CPU_QA'
PROFILE = 'RESIZED_OBSERVATION_PLANE'
EXCLUDED = 'gnmc:test:006575.jpeg'
FOUR = {'input_ids', 'attention_mask', 'pixel_values', 'image_grid_thw'}
CODEC = 'TORCH_SAVE_GZIP_V1'


def reference(value):
    require(isinstance(value, dict) and set(value) == {'path', 'sha256'} and isinstance(value['path'], str)
        and len(value['sha256']) == 64 and all(c in '0123456789abcdef' for c in value['sha256']), 'Explicit immutable file ref')
    return copy.deepcopy(value)


def key(*values):
    return hashlib.sha256('|'.join(map(str, values)).encode()).hexdigest()[:24]


def validate_quality(reg, result56, profile_result=None):
    require(reg['schema'] == SCHEMA and reg['scope'] in ('resized20', 'resized19', 'native19'), 'Explicit scope58')
    require(result56['status'] == 'PASS_UTILITY_SCREEN20_ONLY' and result56['primary'] == 'UTILITY'
        and result56['confirm_admitted'] is True and result56['fixed_final_checkpoint'] is True
        and result56['evaluation']['quality']['admitted'] is True
        and result56['adapter_weights'] == reg['adapter_weights'] and result56['value_weights'] == reg['value_weights']
        and result56['original_CROP_CE_and_old47_52_remain_STOP'] is True, 'Actual56 PASS on fixed fresh utility weights required')
    if reg['scope'] == 'resized19':
        reference(reg['profile_acceptanceRef'])
        require(profile_result is not None and profile_result['status'] == 'PASS_UTILITY_RESIZED20_PROFILE_ONLY'
            and profile_result['primary'] == 'UTILITY' and profile_result['confirm_admitted'] is True
            and profile_result['fixed_final_checkpoint'] is True and profile_result['quality']['admitted'] is True
            and profile_result['adapter_weights'] == reg['adapter_weights']
            and profile_result['value_weights'] == reg['value_weights'], 'Actual new resized20 quality PASS before remaining19')


def build_plan(reg, catalog, case_plan, native_prepared, result56, profile_result=None):
    """GT-free exact inventory projection, with no label-dependent choices."""
    validate_quality(reg, result56, profile_result)
    scope = reg['scope']; role, expected = ('screen', 20) if scope == 'resized20' else ('confirm', 19)
    rows = [s for s in catalog['sources'] if s['role'] == role]
    require(len(rows) == expected and [s['source_id'] for s in rows] == reg['expected_source_ids']
        and len({s['source_id'] for s in rows}) == len({s['source_sha256'] for s in rows}) == expected
        and all(s['source_id'] != EXCLUDED for s in rows), 'Exact fixed historical source order; no substitution')
    require(case_plan['GT_used_for_input_or_pair_choice'] is False, 'Original label-free case pool required')
    entries = {} if native_prepared is None else {e['id']:e for e in native_prepared['screen_inputs' if role == 'screen' else 'confirm_inputs']}
    sources, cases, pairs, mapping = [], [], [], {}
    selected = {s['source_id'] for s in rows}
    original_cases = [c for c in case_plan['cases'] if c['source_id'] in selected]
    require(len({c['id'] for c in original_cases}) == len(original_cases), 'Unique original ordered case identity')
    for s in rows:
        require(s['original_BASE_observed'] is True and s['pool'][0] == s['baseline_box']
            and 1 <= len(s['pool']) <= 7 and len({tuple(b) for b in s['pool']}) == len(s['pool'])
            and not any(k in s for k in ('candidate_ious', 'original_reference_xywh', 'reference_xywh')), 'Unchanged observed BASE and GT-free fixed pool')
        fields = ('source_id', 'source_sha256', 'role', 'width', 'height', 'pool', 'baseline_box', 'source_vision', 'original_proof')
        source = {k:copy.deepcopy(s[k]) for k in fields}
        if scope == 'native19':
            source.update(RGB=reference(s['RGB']), RGB_pixel_sha256=s['RGB_pixel_sha256'])
        source.update(profile='NATIVE_RGB' if scope == 'native19' else PROFILE, native_RGB_recovered=False,
            original_BASE_observed=True, scope=scope)
        sources.append(source)
        own = [c for c in original_cases if c['source_id'] == s['source_id']]
        required = {(0, 0)} | {(0, i) for i in range(1, len(s['pool']))} | {(i, 0) for i in range(1, len(s['pool']))}
        require(len(own) == len(required) and {(c['a'], c['b']) for c in own} == required, 'Complete both-order baseline comparisons and self')
    for c in original_cases:
        source = next(s for s in sources if s['source_id'] == c['source_id'])
        cid = key('UTILITY58', scope, source['source_sha256'], c['id']); mapping[c['id']] = cid
        old = entries.get(c['id'])
        if old is not None: require(old['source_id'] == c['source_id'], 'Native request source changed')
        cases.append(dict(id=cid, native_case_id=c['id'], native_input=reference(old['input']) if old else None,
            source_id=c['source_id'], source_sha256=source['source_sha256'], role=role, a=c['a'], b=c['b']))
    for p in case_plan['pair_index']:
        if p['source_id'] not in selected: continue
        q = copy.deepcopy(p); q['first_id'], q['reverse_id'] = mapping[p['first_id']], mapping[p['reverse_id']]
        first, reverse = [next(c for c in cases if c['id'] == q[k]) for k in ('first_id', 'reverse_id')]
        i = q['candidate_index']
        require((first['a'], first['b']) == (0, i) and (reverse['a'], reverse['b']) == (i, 0)
            and q['same_crop'] is (i == 0), 'Original pair-index order/self mapping differs')
        pairs.append(q)
    require(len(pairs) == sum(len(s['pool']) for s in sources) and len(cases) == 2*len(pairs)-expected,
            'Exact full-pool source coverage')
    if scope == 'resized20': require(len(cases) == 240, 'Original20 exact240 requests')
    return dict(scope=scope, profile=sources[0]['profile'], sources=sources, cases=cases, pair_index=pairs,
        GT_used_for_input_or_pair_choice=False, native_RGB_recovered=False, historical_exposure=True,
        original20_complete=False if expected == 19 else True, unavailable_source=EXCLUDED,
        adapter_weights=reference(reg['adapter_weights']), value_weights=reference(reg['value_weights']),
        CPU_targets=reference(reg['CPU_targets']), production_admitted=False)


def affine_xywh(box, native_dimensions, observation_dimensions):
    require(len(box) == 4 and len(native_dimensions) == len(observation_dimensions) == 2, 'Explicit XYWH and two dimension pairs')
    W, H = native_dimensions; ow, oh = observation_dimensions
    require(all(type(v) is int and v > 0 for v in (W, H, ow, oh)), 'Positive exact dimensions')
    x, y, w, h = map(lambda v:Fraction(str(v)), box)
    require(0 <= x < x+w <= W and 0 <= y < y+h <= H, 'Unmodified original legal reference')
    return list(map(str, (x*ow/W, y*oh/H, w*ow/W, h*oh/H)))


def cpu_targets(plan, original, observation_dimensions):
    """After input fixation only; never supplied to a request or reader."""
    by_id = {s['source_id']:s for s in original['sources']}; rows = []
    for s in plan['sources']:
        t = by_id[s['source_id']]
        require(t['source_sha256'] == s['source_sha256'] and t['role'] == s['role'] and t['baseline_index'] == 0
            and t['reference_modified'] is False and len(t['candidate_ious']) == len(s['pool']), 'Original frozen CPU-only human mapping')
        dims = observation_dimensions[s['source_id']]
        row = copy.deepcopy(t); row.update(native_dimensions=[s['width'], s['height']], observation_dimensions=dims,
            observation_reference_xywh_exact=affine_xywh(t['original_reference_xywh'], [s['width'], s['height']], dims),
            original_reference_unchanged=True, candidate_ious_adopted_without_recompute=True,
            geometry_policy='ORIGINAL_NATIVE_NORMALIZED_GEOMETRY_DELTA11')
        rows.append(row)
    return dict(status='UTILITY58_ORIGINAL_REFERENCES_AND_AFFINE_CPU_ONLY', sources=rows, native_RGB_recovered=False,
        original_targets=plan['CPU_targets'], scope=plan['scope'], historical_exposure=True, new_blind_sources=0)


def encode_crop(vision):
    """Lossless first-new serialization; byte counts are measured, not assumed."""
    require(set(vision) == {'pixel_values', 'image_grid_thw'}, 'Two-key new crop only')
    started = time.monotonic(); handle = io.BytesIO(); torch.save(vision, handle); raw = handle.getvalue()
    compressed = gzip.compress(raw, compresslevel=6, mtime=0)
    restored = torch.load(io.BytesIO(gzip.decompress(compressed)), map_location='cpu', weights_only=True)
    require(signature(restored) == signature(vision), 'First compressed patch save/decode is not bit exact')
    return compressed, dict(codec=CODEC, decoded_signature=signature(vision),
        uncompressed_bytes=len(raw), compressed_bytes=len(compressed), compression_seconds=time.monotonic()-started,
        first_lossless_roundtrip_bitidentical=True)


def cached_recovery(source, vision, receipts, load_array, recovery_code):
    matches = [r for r in receipts if r['entry']['source_id'] == source['source_id']
               and r['entry']['source_sha256'] == source['source_sha256']]
    if not matches: return None
    require(len(matches) == 1, 'Ambiguous cached source recovery')
    r = matches[0]; layout = r['entry']['layout']; grid = vision['image_grid_thw'][0].tolist()
    require(r['status'] == 'PASS_RESIZED_OBSERVATION_LAYOUT_ONLY' and r['formula_code'] == recovery_code
        and layout['tensor_ref'] == source['source_vision'] and layout['row_start'] == 0
        and layout['row_end_exclusive'] == grid[1]*grid[2] and layout['grid_thw'] == grid
        and layout['normalization'] == r['recovery']['normalization'] == 'FLOAT32(u-127.5)/127.5'
        and r['native_dimensions'] == [source['width'], source['height']] and r['native_RGB_recovered'] is False
        and r['recovery']['input_pixel_tensor_sha256'] == signature(vision)['pixel_values']['sha256']
        and r['independent_recovery']['status'] == 'PASS_EXACT_RESIZED_OBSERVATION_LAYOUT_AND_UINT8', 'Cached recovery is not exact same source/input/formula')
    rgb = load_array(r['resized_RGB'])
    require(rgb.dtype == np.uint8 and list(rgb.shape) == [grid[1]*16, grid[2]*16, 3]
        and hashlib.sha256(rgb.tobytes()).hexdigest() == r['recovery']['observation_RGB_pixel_sha256'], 'Adopted resized plane changed')
    return dict(rgb=rgb, recovery=r['recovery'], independent_recovery=r['independent_recovery'], adopted=r['resized_RGB'])


def prepare_source(source, cases, vision, processor, image, recovery, *, native_inputs=None, native_rgb=None, adopted_recovery=None):
    """One-source first construction; all supplied pixels are accepted CPU data."""
    old = {k:vision[k] for k in ('pixel_values', 'image_grid_thw')}; native_inputs = native_inputs or {}
    require(all(c['source_id'] == source['source_id'] for c in cases), 'One source per bounded construction')
    if source['profile'] == PROFILE:
        if adopted_recovery is None:
            rgb, proof = recovery.recover_observation_rgb(old['pixel_values'], old['image_grid_thw'])
            check = recovery.independent_recovery_check(old['pixel_values'], old['image_grid_thw'], rgb, proof)
            plane = dict(rgb=rgb, recovery=proof, independent_recovery=check, adopted=None)
        else: plane = adopted_recovery; rgb = plane['rgb']
    else:
        rgb = native_rgb
        require(isinstance(rgb, np.ndarray) and rgb.dtype == np.uint8 and rgb.shape == (source['height'], source['width'], 3)
            and hashlib.sha256(rgb.tobytes()).hexdigest() == source['RGB_pixel_sha256'], 'Accepted original RGB changed; no decoder fallback')
        plane = dict(rgb=rgb, recovery=None, independent_recovery=None, adopted=source['RGB'])
    crops = {}
    for i, box in enumerate(source['pool']):
        if source['profile'] == PROFILE:
            rendered, proof = recovery.render_observation_crop(rgb, box, [source['width'], source['height']])
            check = recovery.independent_observation_crop_check(rgb, box, [source['width'], source['height']], rendered, proof)
        else:
            rendered, proof = image.render_crop(rgb, box); check = image.independent_render_check(rgb, box, rendered, proof)
        crop = dict(processor.image_processor(images=[Image.fromarray(rendered)], return_tensors='pt'))
        independent = dict(processor.image_processor(images=[Image.fromarray(rendered.copy())], return_tensors='pt'))
        require(set(crop) == set(independent) == {'pixel_values', 'image_grid_thw'}
            and signature(crop) == signature(independent), 'First new crop independent processor bit QA')
        compressed, codec = encode_crop(crop)
        crops[i] = dict(vision=crop, compressed=compressed, codec=codec, render=proof, independent_render=check)
    outputs, text_cache = [], {}
    for case in cases:
        a, b = case['a'], case['b']; views = [old, crops[a]['vision'], crops[b]['vision']]
        grid = torch.cat([v['image_grid_thw'] for v in views]); pixels = [v['pixel_values'] for v in views]
        packed = image.pack_image_pixels(pixels, grid); image.independent_pixel_check(pixels, grid, packed)
        prior = native_inputs.get(case['native_case_id']); tokens_ref = None; native_crops = []
        if prior is not None:
            q, tokens = prior['request'], prior['tokens']
            require(q['source_id'] == source['source_id'] and q['source_sha256'] == source['source_sha256']
                and q['candidate_indices'] == [a, b] and q['boxes'] == [source['pool'][a], source['pool'][b]]
                and q['vision_inputs'][0] == source['source_vision'] and q['reference_or_target_in_prompt'] is False,
                'Original native request owner/order/source differs')
            require(signature(tokens) == {k:q['input_signature'][k] for k in ('input_ids', 'attention_mask')}, 'Adopted native tokens changed')
            native_crops = q['vision_inputs'][1:]
            if grid.tolist() == q['image_grid_thw']: tokens_ref = q['tokens']; text = q['text_evidence']
        if tokens_ref is None:
            token_key = json.dumps(grid.tolist())
            if token_key not in text_cache: text_cache[token_key] = image.build_text_input(processor, grid)
            tokens, text = text_cache[token_key]
        text_check = image.independent_text_check(processor, packed, tokens, text)
        require(text['question'] == image.QUESTION, 'Exact original question/prefix required')
        request = dict(id=case['id'], native_case_id=case['native_case_id'], source_id=source['source_id'],
            source_sha256=source['source_sha256'], role=source['role'], scope=source['scope'], profile=source['profile'],
            native_RGB_recovered=False, candidate_indices=[a, b], boxes=[source['pool'][a], source['pool'][b]],
            input_signature=signature(dict(**tokens, **packed)), image_grid_thw=grid.tolist(),
            class_token_ids=text['class_token_ids'], text_evidence=text, reference_or_target_in_prompt=False,
            geometry_policy='ORIGINAL_NATIVE_NORMALIZED_GEOMETRY_DELTA11', native_crop_refs_for_no_reuse_check=native_crops)
        outputs.append(dict(request=request, tokens=tokens, adopted_tokens_ref=tokens_ref, independent_text=text_check))
    return dict(plane=plane, crops=crops, cases=outputs, observation_dimensions=[rgb.shape[1], rgb.shape[0]])


def partition(requests, successes, weights, value_weights):
    executions, adopted, entries = [], {}, []
    for q in requests:
        entry = {k:q[k] for k in ('id', 'source_id', 'source_sha256', 'role', 'input')}; entries.append(entry)
        matches = [s for s in successes if s['source_id'] == q['source_id'] and s['source_sha256'] == q['source_sha256']
            and s['class_token_ids'] == q['class_token_ids'] and s['input_signature'] == q['input_signature']]
        if not matches: executions.append(entry); continue
        require(all(s['adapter_weights'] == weights and s['value_weights'] == value_weights and s['first_output_QA_passed'] is True
            for s in matches), 'Exact successful old weight/input identity required for external alias')
        require(all(s['raw_hidden'] == matches[0]['raw_hidden'] and s['CPU_value'] == matches[0]['CPU_value'] for s in matches), 'Conflicting accepted same-input values')
        s = matches[0]
        adopted[q['id']] = {k:copy.deepcopy(s[k]) for k in ('input', 'receipt', 'raw_hidden', 'acceptance', 'model_role',
            'adapter_weights', 'value_weights', 'CPU_value', 'GPU_value')}
    require(len({e['id'] for e in entries}) == len(entries), 'Unique new profile request IDs')
    return dict(inference_inputs=entries, execution_entries=executions, adopted_success=adopted)


class ProfileInputs:
    """Explicit callback whitelist; no target/ref discovery or processor calls."""
    def __init__(self, prepared, *, gate, prepared_ref, registration_ref, load_json, load_tensor, image, load_bytes=None):
        require(gate['status'] == GATE and gate['prepared'] == reference(prepared_ref)
            and gate['registration'] == reference(registration_ref) and prepared['schema'] == 'UTILITY_PROFILE_PREPARED_V58', 'Actual new58 first CPU input gate')
        ids = {e['id'] for e in prepared['inference_inputs']}; execution = prepared['execution_entries']; aliases = prepared['adopted_success']
        by_id = {e['id']:e for e in prepared['inference_inputs']}
        require(len(ids) == len(prepared['inference_inputs']) and not {e['id'] for e in execution}&set(aliases)
            and {e['id'] for e in execution}|set(aliases) == ids and all(e == by_id[e['id']] for e in execution), 'Exact execution/adopted partition')
        self.prepared = prepared; self.allowed = {tuple(sorted(reference(e['input']).items())):e for e in execution}
        require(len(self.allowed) == len(execution), 'Unique execution refs')
        self.load_json, self.load_tensor, self.load_bytes, self.image = load_json, load_tensor, load_bytes, image
        self.current_source, self.cache = None, {}
    def get(self, input_ref):
        k = tuple(sorted(reference(input_ref).items())); require(k in self.allowed, 'Only first-new58 execution refs')
        e = self.allowed[k]; q = self.load_json(input_ref)
        require(all(q[x] == e[x] for x in ('id', 'source_id', 'source_sha256', 'role')) and q['source_id'] != EXCLUDED
            and q['scope'] == self.prepared['scope'] and q['profile'] == self.prepared['profile']
            and q['role'] in ('screen', 'confirm')
            and q['reference_or_target_in_prompt'] is False and q['native_RGB_recovered'] is False
            and q['adapter_weights'] == self.prepared['adapter_weights'] and q['value_weights'] == self.prepared['value_weights']
            and not any(n in q for n in ('target', 'labels', 'candidate_ious', 'original_reference_xywh')), 'Label-free source/role/weight request identity')
        if self.current_source != q['source_id']: self.cache.clear(); self.current_source = q['source_id']
        require(len(q['vision_inputs']) == len(q['vision_codecs']) == 3, 'Exactly3 source/A/B views and codecs')
        views = []
        for i, (vref, codec) in enumerate(zip(q['vision_inputs'], q['vision_codecs'])):
            cache_key = tuple(sorted(reference(vref).items()))
            if cache_key not in self.cache:
                if i == 0:
                    require(codec['codec'] == 'TORCH_RAW', 'Old source patch stays original uncompressed reference')
                    raw = self.load_tensor(vref)
                else:
                    require(codec['codec'] == CODEC and callable(self.load_bytes)
                        and vref not in q['native_crop_refs_for_no_reuse_check'], 'First-new compressed crop; no old native crop reuse')
                    raw = torch.load(io.BytesIO(gzip.decompress(self.load_bytes(vref))), map_location='cpu', weights_only=True)
                self.cache[cache_key] = {n:raw[n] for n in ('pixel_values', 'image_grid_thw')}
            view = self.cache[cache_key]; require(signature(view) == codec['decoded_signature'], 'Decompressed first-QA patch bytes differ')
            views.append(view)
        grid = torch.cat([v['image_grid_thw'] for v in views]); packed = self.image.pack_image_pixels([v['pixel_values'] for v in views], grid)
        tokens = self.load_tensor(q['tokens']); require(set(tokens) == {'input_ids', 'attention_mask'}, 'Prefix-only tokens')
        values = dict(**tokens, **packed)
        require(set(values) == FOUR and signature(values) == q['input_signature'] and grid.tolist() == q['image_grid_thw']
            and q['class_token_ids'] == self.prepared['class_token_ids'], 'Exact first-QA58 fourtensor/class/grid mapping')
        return values, q


def _module(r, name):
    p = bound(r); spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m); return m


def run(root, scope):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '' and not torch.cuda.is_initialized(), 'CPU-only58 child')
    rp = root/('utility_profile_CPU_registration_58_'+scope+'.json'); reg = read(rp)
    require(reg['scope'] == scope and bound(reg['preparation_code']) == Path(__file__).resolve(), 'Exact new58 scope/source')
    screen = read(bound(reg['quality_result56'])); profile = read(bound(reg['profile_acceptanceRef'])) if reg.get('profile_acceptanceRef') else None
    validate_quality(reg, screen, profile)
    def budget():
        require(time.monotonic()-started < reg['max_seconds'] and dt.datetime.now(dt.timezone.utc) <
            dt.datetime.fromisoformat(reg['deadline_utc'].replace('Z', '+00:00')), 'Registered CPU/Goal budget')
    started = time.monotonic(); budget()
    geometry = _module(reg['geometry_code'], '_utility58_geometry'); image = _module(reg['input_code'], '_utility58_image')
    recovery = _module(reg['recovery_code'], '_utility58_recovery')
    old = read(bound(reg['native_prepared'])) if reg.get('native_prepared') else None
    if old is not None:
        gate = read(bound(reg['native_input_acceptance']))
        require(gate['status'] == 'PASS_ALL_CROP31_TRIPLET_FIRST_CPU_QA' and gate['prepared'] == reg['native_prepared'], 'Adopt real old31 input QA')
    plan = build_plan(reg, read(bound(reg['source_catalog'])), read(bound(reg['case_plan'])), old, screen, profile)
    for s in plan['sources']:
        require(all(geometry.legal(b, s['width'], s['height']) for b in s['pool']), 'Native pool legality unchanged')
    from transformers import AutoProcessor
    cfg = read(bound(reg['model_config'])); processor = AutoProcessor.from_pretrained(cfg['model_dir'], local_files_only=True, min_pixels=65536, max_pixels=65536)
    out = root/'utility_profile_inputs_58'/scope; out.mkdir(parents=True, exist_ok=False)
    save(out/'claim.json', dict(registration=ref(rp), utc=utc(), old_STOPs_unchanged=True, production_admitted=False))
    completed, recoveries, dims, requests, compressed_bytes, raw_bytes, compression_seconds = [], [], {}, [], 0, 0, 0.
    try:
        caches = [read(bound(r)) for r in reg.get('recovery_receipts', [])]
        for s in plan['sources']:
            budget(); directory = out/key(s['source_id']); directory.mkdir()
            bound(s['original_proof']); raw = torch.load(bound(s['source_vision']), map_location='cpu', weights_only=True)
            vision = {k:raw[k] for k in ('pixel_values', 'image_grid_thw')}
            own = [c for c in plan['cases'] if c['source_id'] == s['source_id']]; native = {}
            for c in own:
                if c['native_input'] is not None:
                    q = read(bound(c['native_input'])); native[c['native_case_id']] = dict(request=q,
                        tokens=torch.load(bound(q['tokens']), map_location='cpu', weights_only=True))
            adopted = cached_recovery(s, vision, caches, lambda r:np.load(bound(r), allow_pickle=False), reg['recovery_code']) if scope != 'native19' else None
            rgb = np.load(bound(s['RGB']), allow_pickle=False) if scope == 'native19' else None
            actual = prepare_source(s, own, vision, processor, image, recovery, native_inputs=native, native_rgb=rgb, adopted_recovery=adopted)
            dims[s['source_id']] = actual['observation_dimensions']; plane = actual['plane']
            if plane['adopted'] is None:
                p = directory/'resized_RGB.npy'
                with p.open('xb') as f: np.save(f, plane['rgb'], allow_pickle=False)
                plane_ref = ref(p)
            else: plane_ref = plane['adopted']
            save(directory/'recovery.json', dict(source_id=s['source_id'], source_sha256=s['source_sha256'],
                source_vision=s['source_vision'], resized_RGB=plane_ref, adopted=plane['adopted'] is not None,
                recovery=plane['recovery'], independent_recovery=plane['independent_recovery'], native_RGB_recovered=False))
            recoveries.append(ref(directory/'recovery.json')); crop_refs = {}
            for i, crop in actual['crops'].items():
                p = directory/('crop_%02d.pt.gz'%i)
                with p.open('xb') as f: f.write(crop['compressed']); f.flush(); os.fsync(f.fileno())
                require(signature(torch.load(io.BytesIO(gzip.decompress(p.read_bytes())), map_location='cpu', weights_only=True)) == crop['codec']['decoded_signature'], 'Persisted compressed patch first byte QA')
                crop_refs[i] = ref(p); compressed_bytes += crop['codec']['compressed_bytes']; raw_bytes += crop['codec']['uncompressed_bytes']; compression_seconds += crop['codec']['compression_seconds']
                save(directory/('crop_%02d.proof.json'%i), dict(candidate_index=i, native_box=s['pool'][i], input=crop_refs[i],
                    codec=crop['codec'], render=crop['render'], independent_render=crop['independent_render']))
            for case in actual['cases']:
                q = case['request']; a, b = q['candidate_indices']; tokens_ref = case['adopted_tokens_ref']
                if tokens_ref is None:
                    p = directory/(q['id']+'.tokens.pt')
                    with p.open('xb') as f: torch.save(case['tokens'], f)
                    require(signature(torch.load(p, map_location='cpu', weights_only=True)) == signature(case['tokens']), 'New prefix save/reload bits')
                    tokens_ref = ref(p)
                q.update(tokens=tokens_ref, vision_inputs=[s['source_vision'], crop_refs[a], crop_refs[b]],
                    vision_codecs=[dict(codec='TORCH_RAW', decoded_signature=signature(vision)), actual['crops'][a]['codec'], actual['crops'][b]['codec']],
                    adapter_weights=reg['adapter_weights'], value_weights=reg['value_weights'])
                p = directory/(q['id']+'.json'); save(p, q); q['input'] = ref(p); requests.append(q); completed.append(q['id'])
            del actual, raw, vision
        budget(); successes = []
        if reg.get('native_output_acceptance'):
            require(reg['native_output_acceptance'] == screen['screen_output_acceptance'], 'Only accepted native55 screen output aliases')
            accepted = read(bound(reg['native_output_acceptance']))
            require(accepted['status'] == 'PASS_UTILITY_FINAL500_SCREEN_FIRST_RAW_QA', 'Adopt successful first raw QA, never replay')
            for p in accepted['predictions']:
                q, receipt = read(bound(p['input'])), read(bound(p['receipt']))
                require(p['adapter_weights'] == reg['adapter_weights'] and p['value_weights'] == reg['value_weights'], 'Alias accepted weights')
                successes.append(dict(source_id=p['source_id'], source_sha256=p['source_sha256'], input=p['input'], receipt=p['receipt'],
                    raw_hidden=p['raw_hidden'], acceptance=reg['native_output_acceptance'], model_role=receipt['model_role'],
                    adapter_weights=reg['adapter_weights'], value_weights=reg['value_weights'], class_token_ids=q['class_token_ids'],
                    input_signature=q['input_signature'], first_output_QA_passed=True, CPU_value=p['CPU_value'], GPU_value=p['GPU_value']))
        partitioned = partition(requests, successes, reg['adapter_weights'], reg['value_weights'])
        require(all(q['class_token_ids'] == requests[0]['class_token_ids'] for q in requests), 'One actual0/1/2 class identity throughout fixed scope')
        source_set_sha = hashlib.sha256(json.dumps([(s['source_id'], s['source_sha256']) for s in plan['sources']],
            separators=(',', ':')).encode()).hexdigest()
        save(out/'source_catalog.json', dict(sources=plan['sources'], GT_included=False))
        save(out/'case_plan.json', {k:plan[k] for k in ('cases', 'pair_index', 'GT_used_for_input_or_pair_choice')})
        # Only after every input/request has been fixed, open the separate CPU labels.
        targets = cpu_targets(plan, read(bound(reg['CPU_targets'])), dims); save(out/'CPU_targets.json', targets)
        prepared = dict(schema='UTILITY_PROFILE_PREPARED_V58', scope=scope, profile=plan['profile'], **partitioned,
            pair_index=plan['pair_index'], source_catalog=ref(out/'source_catalog.json'), case_plan=ref(out/'case_plan.json'),
            label_free_case_plan=ref(out/'case_plan.json'), source_set_sha256=source_set_sha,
            CPU_targets=ref(out/'CPU_targets.json'), class_token_ids=requests[0]['class_token_ids'],
            adapter_weights=reg['adapter_weights'], value_weights=reg['value_weights'], quality_result56=reg['quality_result56'],
            profile_acceptanceRef=reg.get('profile_acceptanceRef'), sources=len(plan['sources']),
            historical_exposure=True, original20_complete=plan['original20_complete'], native_RGB_recovered=False,
            codec=CODEC, new_crop_compressed_bytes=compressed_bytes, new_crop_uncompressed_bytes=raw_bytes,
            compression_seconds=compression_seconds, production_admitted=False)
        save(out/'prepared.json', prepared)
        reader = ProfileInputs(prepared, gate=dict(status=GATE, prepared=ref(out/'prepared.json'), registration=ref(rp)),
            prepared_ref=ref(out/'prepared.json'), registration_ref=ref(rp), load_json=lambda r:read(bound(r)),
            load_tensor=lambda r:torch.load(bound(r), map_location='cpu', weights_only=True), image=image, load_bytes=lambda r:bound(r).read_bytes())
        for entry in prepared['execution_entries']: reader.get(entry['input'])
        budget(); require(not torch.cuda.is_initialized(), 'CPU58 initialized CUDA')
        save(out/'input_acceptance.json', dict(status=GATE, registration=ref(rp), prepared=ref(out/'prepared.json'), scope=scope,
            schema='UTILITY_PROFILE_INPUT_ACCEPTANCE_V58', source_set_sha256=source_set_sha,
            sources=len(plan['sources']), inference_inputs=len(requests), execution_inputs=len(partitioned['execution_entries']),
            adopted_successes=len(partitioned['adopted_success']), source_processor_repeated=0, new_original_decode=0,
            new_crop_count=sum(len(s['pool']) for s in plan['sources']), first_independent_crop_processor_QA=True,
            first_compressed_save_and_reader_roundtrip=True, native_RGB_recovered=False, recoveries=recoveries,
            compressed_bytes=compressed_bytes, uncompressed_bytes=raw_bytes, compression_seconds=compression_seconds,
            elapsed_seconds=time.monotonic()-started, production_admitted=False, GPU_admitted=False))
    except BaseException as error:
        save(out/'failure.json', dict(error=repr(error), traceback=traceback.format_exc(), completed_requests=completed,
            completed_recoveries=recoveries, preserve_all_success=True, automatic_retry=False, GPU_admitted=False))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--scope', choices=['resized20', 'resized19', 'native19'], required=True)
    a = parser.parse_args(); run(a.root, a.scope)
