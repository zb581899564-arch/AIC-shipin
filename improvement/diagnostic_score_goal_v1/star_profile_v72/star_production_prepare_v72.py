"""Conditional exact-observation production CPU inputs, no model or decoder.

CLI --root ROOT --phase pilot32|remaining. Original registration is
star_production_CPU_registration_72.json, schema
STAR_PRODUCTION_OBSERVATION_CPU_V72. Required refs: preparation_code,
profile_code(58),geometry_code(31),image_code(31),recovery_code(34),model_config,
accepted_production,production_metadata,protected_baseline,resized20_quality,
resized19_quality,adapter_weights,value_weights,production_admission. Also
accepted_root,selection='OBS_INDEX_EVEN',class_token_ids,deadline_utc,
max_seconds,recovery_receipts(list of35 receipt refs).

Original production_admission is CPU-only ADMIT_STAR_PRODUCTION_CPU_PILOT32_ONLY
with production_prepare_approved=True,production_admitted=False,selection,
resized20_quality/resized19_quality refs,adapter/value refs,whole426_preserved.
The separate star_production_remaining_admission_72.json binds schema
STAR_PRODUCTION_REMAINING_CPU_V72,original_registration,pilot_acceptance,
domain,source_catalog,case_plan,remaining_source_ids (exact frozen selectedD
minus32),production_admission (explicit spatial-only production approval),
max_additional_bytes,deadline_utc,max_seconds. No automatic continuation/retry.

Output star_production_inputs_72: domain/source_catalog/case_plan are frozen
before the32-observation capacity pilot. Final prepared/input_acceptance appear
only after explicit remaining completion, adopting all original32 proofs.
All426 protected records/other frames/9:16 are references to unchanged40.47.
Each virtual owner is one EXACT accepted native frame; no nearest/interpolation.
No ground truth, source processor, native-RGB recovery or model is used.
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
import shutil
import sys
import time
import traceback
import zipfile

import numpy as np
import torch

_support = Path(__file__).resolve().parents[2]/'pair_code_17'
if _support.is_dir(): sys.path.insert(0, str(_support))
from pair_common import read, ref, bound, require, signature, utc
sys.path.insert(0, str(Path(__file__).resolve().parent))
import star_identity_v72 as identity

SCHEMA = 'STAR_PRODUCTION_OBSERVATION_CPU_V72'
GATE = 'PASS_STAR72_ALL_SELECTED_OBSERVATIONS_FIRST_CPU_QA'
PILOT_GATE = 'PASS_STAR72_CPU_CAPACITY_PILOT32_ONLY'
OBS_GATE = 'PASS_STAR72_OBSERVATION_FIRST_CPU_INPUT_QA'
SELECTION = 'OBS_INDEX_EVEN'
SOURCE_CODEC = 'ACCEPTED_CHUNK_ROW_V61'
CROP_CODEC = 'TORCH_SAVE_GZIP_V1'
PROFILE = 'RESIZED_OBSERVATION_PLANE'
PROTECTED_SHA = 'b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'
OFFICIAL_IDS = {str(i) for i in range(426)}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def file_ref(value):
    require(isinstance(value, dict) and set(value) == {'path', 'sha256'} and isinstance(value['path'], str)
        and len(value['sha256']) == 64 and all(c in '0123456789abcdef' for c in value['sha256']), 'Explicit immutable artifact reference')
    return copy.deepcopy(value)


def validate_quality(reg, q20, q19, admission, *, pilot):
    require(reg['schema'] == SCHEMA and reg['selection'] == SELECTION
        and reg['protected_baseline']['sha256'] == PROTECTED_SHA, 'Fixed even-observation budget scope/protected40.47')
    for result, status in ((q20, 'PASS_STAR_RESIZED20_PROFILE_ONLY'), (q19, 'PASS_STAR_RESIZED19_CONFIRM_ONLY')):
        require(result['status'] == status and result['primary'] == 'UTILITY' and result['quality']['admitted'] is True
            and result['adapter_weights'] == reg['adapter_weights'] and result['value_weights'] == reg['value_weights'], 'Both actual resized quality PASSes and exact fresh utility weights')
    expected = 'ADMIT_STAR_PRODUCTION_CPU_PILOT32_ONLY' if pilot else 'ADMIT_STAR_EXACT_NATIVE_PTS_SPATIAL_ONLY'
    require(admission['status'] == expected and admission['production_prepare_approved'] is True
        and admission['production_admitted'] is (not pilot) and admission['whole426_preserved'] is True
        and admission['selection'] == SELECTION and admission['resized20_quality'] == reg['resized20_quality']
        and admission['resized19_quality'] == reg['resized19_quality'] and admission['adapter_weights'] == reg['adapter_weights']
        and admission['value_weights'] == reg['value_weights'], 'Explicit phase-specific admission; no old STOP bypass')


def compile_domain(accepted, metadata, baseline_rows, clocks, source_refs, geometry):
    """Metadata only. Even index is applied before the baseline intersection."""
    sources = {s['id']:s for s in accepted['sources']}; meta = {s['video_id']:s for s in metadata['records']}
    baseline = {s['video_id']:s for s in baseline_rows}
    require(len(sources) == len(meta) == len(baseline) == 426 and set(sources) == set(meta) == set(baseline) == OFFICIAL_IDS,
        'Whole426 accepted/source/protected-row identities required')
    all_d, selected, official = [], [], []
    for sid in sorted(sources, key=int):
        old, m, b = sources[sid], meta[sid], baseline[sid]
        require(old['name'] == sid and old['native_frames'] == m['n_frames']
            and b['targetRatioWH'] == m['targetRatioWH'], 'Original video/native length/target ratio differs')
        pred = {}; previous = -1
        for p in b['predictions']:
            n = p['frame']; require(type(n) is int and previous < n < old['native_frames'], 'Exact ordered protected zero-based native ordinals')
            previous = n; pred[n] = p['bboxes']
        official.append(dict(video_id=sid, source_sha256=m['source_sha256'], targetRatioWH=m['targetRatioWH'],
            native_frames=old['native_frames'], protected_selected_frames=len(pred), baseline_authority='PROTECTED40.47_ZIP',
            all_unregistered_frames_unchanged=True))
        if m['targetRatioWH'] != [16, 9]: continue
        c = clocks[sid]; refs = source_refs[sid]; points = c['normalized_exact_pts']
        require(c['video_id'] == sid and c['source_sha256'] == m['source_sha256'] and len(points) == old['native_frames']
            and c['n_frames'] == old['native_frames'] and file_ref(refs['clock'])['sha256'] == old['clock_sha256'], 'Accepted exact native clock/source ownership')
        pts = [Fraction(p) for p in points]
        require(pts[0] == 0 and all(a < z for a, z in zip(pts, pts[1:])), 'Strict exact native PTS; no nominal FPS mapping')
        observation_index = 0; previous_sample = -1
        for chunk_index, chunk in enumerate(old['chunks']):
            require(len(chunk['samples']) == len(chunk['grid']) and len(chunk['pixel_shape']) == 2
                and chunk['pixel_shape'][1] == 1536, 'Accepted actual chunk/sample/grid schema')
            offset = 0
            for row_index, (ordinal, grid) in enumerate(zip(chunk['samples'], chunk['grid'])):
                require(type(ordinal) is int and previous_sample < ordinal < len(points) and len(grid) == 3
                    and all(type(v) is int and v > 0 for v in grid) and grid[0] == 1
                    and grid[1]%2 == grid[2]%2 == 0, 'Exact unique ordered actual2Hz observations and static grids')
                previous_sample = ordinal; end = offset+grid[1]*grid[2]
                if ordinal in pred:
                    identity = dict(video_id=sid, source_sha256=m['source_sha256'], native_ordinal=ordinal,
                        observation_index=observation_index, native_pts_exact=points[ordinal])
                    all_d.append(identity)
                    if observation_index%2 == 0:
                        box = pred[ordinal]; require(geometry.legal(box, m['width'], m['height']), 'Unchanged legal protected16:9 frame box')
                        owner = 'official:%s:native:%d'%(sid, ordinal)
                        layout = dict(tensor_ref=dict(path=chunk['path'], sha256=chunk['sha256']), pixel_key='pixel_values',
                            row_start=offset, row_end_exclusive=end, grid_thw=list(grid),
                            grid_locator=dict(kind='TENSOR_ROW', key='image_grid_thw', row_index=row_index),
                            normalization='FLOAT32(u-127.5)/127.5')
                        selected.append(dict(**identity, source_id=owner, role='production', scope='production',
                            profile=PROFILE, native_RGB_recovered=False, width=m['width'], height=m['height'],
                            targetRatioWH=[16, 9], baseline_box=list(box), pool=geometry.candidate_pool(m['width'], m['height'], box),
                            original_BASE_observed=True, source_layout=layout, source_vision=layout['tensor_ref'],
                            clock=refs['clock'], accepted_input_ref=refs['acceptance'], original_proof=refs['acceptance'],
                            chunk_index=chunk_index, chunk_sample_index=row_index, sample_ordinal=ordinal))
                offset = end; observation_index += 1
            require(offset == chunk['pixel_shape'][0], 'Actual cumulative grid row boundaries differ from chunk shape')
        require(observation_index == old['feature_cells'], 'Complete inherited observation list required')
    require(len({s['source_id'] for s in selected}) == len(selected) and len(selected) >= 32, 'At least32 unique fixed selected observations')
    selected.sort(key=lambda s:(s['source_sha256'], s['video_id'], s['native_ordinal']))
    pilot_ids = [s['source_id'] for s in selected[:32]]
    return dict(selection=SELECTION, all_D=all_d, selected_D=selected, all_D_count=len(all_d), selected_D_count=len(selected),
        all_D_sha256=digest(all_d), selected_D_sha256=digest(selected), pilot_source_ids=pilot_ids,
        remaining_source_ids=[s['source_id'] for s in selected[32:]], official_sources=official,
        official_source_count=426, affected_video_count=len({s['video_id'] for s in selected}),
        no_nearest_or_interpolation=True, protected_baseline_sha256=PROTECTED_SHA)


def case_plan(sources):
    cases, pairs = [], []
    for s in sources:
        def add(a, b):
            cid = digest(['STAR72_OBS_EVEN', s['source_id'], a, b])[:24]
            cases.append(dict(id=cid, native_case_id=cid, source_id=s['source_id'], source_sha256=s['source_sha256'],
                role='production', a=a, b=b, native_input=None)); return cid
        for i in range(1, len(s['pool'])):
            f, r = add(0, i), add(i, 0)
            pairs.append(dict(source_id=s['source_id'], candidate_index=i, first_id=f, reverse_id=r, same_crop=False))
        own = add(0, 0); pairs.append(dict(source_id=s['source_id'], candidate_index=0, first_id=own, reverse_id=own, same_crop=True))
    require(len({c['id'] for c in cases}) == len(cases), 'Exact unique per-observation cases')
    return dict(cases=cases, pair_index=pairs, GT_used_for_input_or_pair_choice=False)


def validate_continuation(reg, continuation, pilot, domain, original_ref):
    require(digest(domain['selected_D']) == domain['selected_D_sha256'] and digest(domain['all_D']) == domain['all_D_sha256']
        and domain['pilot_source_ids'] == [s['source_id'] for s in domain['selected_D'][:32]]
        and domain['remaining_source_ids'] == [s['source_id'] for s in domain['selected_D'][32:]], 'Immutable complete domain content/order')
    require(continuation['schema'] == 'STAR_PRODUCTION_REMAINING_CPU_V72' and continuation['original_registration'] == original_ref
        and pilot['status'] == PILOT_GATE and pilot['registration'] == original_ref
        and pilot['selected_D_sha256'] == domain['selected_D_sha256'] and pilot['pilot_source_ids'] == domain['pilot_source_ids']
        and continuation['remaining_source_ids'] == domain['remaining_source_ids']
        and continuation['expected_sources'] == continuation['observations'] == domain['selected_D_count']
        and continuation['official_source_count'] == 426 and continuation['affected_video_count'] == domain['affected_video_count']
        and type(continuation['max_additional_bytes']) is int and continuation['max_additional_bytes'] > 0
        and continuation['selection'] == reg['selection'] == SELECTION, 'Same immutable selectedD; no repeat pilot or scope switch')


def extract_chunk_row(payload, layout):
    """Independently validate actual cumulative grid offsets, not fixed240 rows."""
    require(layout['pixel_key'] == 'pixel_values' and layout['normalization'] == 'FLOAT32(u-127.5)/127.5'
        and layout['grid_locator']['kind'] == 'TENSOR_ROW' and layout['grid_locator']['key'] == 'image_grid_thw', 'Only actual accepted static chunk layout')
    p, g = payload['pixel_values'], payload['image_grid_thw']; row = layout['grid_locator']['row_index']
    require(p.device.type == g.device.type == 'cpu' and p.dtype == torch.float32 and g.dtype == torch.int64
        and not p.requires_grad
        and p.ndim == 2 and p.shape[1] == 1536 and g.ndim == 2 and g.shape[1] == 3 and type(row) is int and 0 <= row < len(g)
        and bool((g > 0).all()) and bool((g[:,0] == 1).all()) and bool((g[:,1:]%2 == 0).all()), 'Accepted CPU chunk static tensor/grid shapes')
    sizes = g[:,1]*g[:,2]; start = int(sizes[:row].sum()); end = start+int(sizes[row])
    require(int(sizes.sum()) == len(p) and layout['row_start'] == start and layout['row_end_exclusive'] == end
        and layout['grid_thw'] == g[row].tolist(), 'Explicit row interval must match actual grid prefix sum')
    pixels = p[start:end].contiguous(); require(bool(torch.isfinite(pixels).all()), 'Finite adopted observation patch')
    return dict(pixel_values=pixels, image_grid_thw=g[row:row+1].contiguous())


def adopt_plane35(source, vision, receipts, load_array, recovery_code):
    """Virtual owner changes do not change the exact old physical input identity."""
    layout = source['source_layout']; candidates = []
    for r in receipts:
        e = r['entry']
        if e['source_id'] != 'official:'+source['video_id'] or e['source_sha256'] != source['source_sha256']: continue
        if e['layout'] != layout: continue  # Another row of that source is genuinely a new observation.
        require(e['accepted_input_ref'] == source['accepted_input_ref'] and source['sample_ordinal'] == source['native_ordinal']
            and source['chunk_sample_index'] == layout['grid_locator']['row_index'], 'Exact original video/sample/row owner mapping')
        require(r['status'] == 'PASS_RESIZED_OBSERVATION_LAYOUT_ONLY' and r['formula_code']['sha256'] == recovery_code['sha256']
            and r['native_dimensions'] == [source['width'], source['height']] and r['native_RGB_recovered'] is False
            and r['recovery']['normalization'] == layout['normalization']
            and r['recovery']['input_pixel_tensor_sha256'] == signature(vision)['pixel_values']['sha256']
            and r['independent_recovery']['status'] == 'PASS_EXACT_RESIZED_OBSERVATION_LAYOUT_AND_UINT8', 'Adopt only exact successful35 recovery/proof')
        rgb = load_array(r['resized_RGB'])
        require(rgb.dtype == np.uint8 and list(rgb.shape) == [layout['grid_thw'][1]*16, layout['grid_thw'][2]*16, 3]
            and hashlib.sha256(rgb.tobytes()).hexdigest() == r['recovery']['observation_RGB_pixel_sha256'], 'Adopted plane bytes changed')
        candidates.append(dict(rgb=rgb, recovery=r['recovery'], independent_recovery=r['independent_recovery'], adopted=r['resized_RGB']))
    require(len(candidates) <= 1, 'Ambiguous successful old observation recovery')
    return candidates[0] if candidates else None


def read_request(q, *, load_tensor, load_bytes, image, cache=None):
    cache = {} if cache is None else cache; views = []
    require(len(q['vision_inputs']) == len(q['vision_codecs']) == 3, 'Exactly3 production views')
    for i, (r, codec) in enumerate(zip(q['vision_inputs'], q['vision_codecs'])):
        k = json.dumps([r, codec], sort_keys=True)
        if k not in cache:
            if i == 0:
                require(codec['codec'] == SOURCE_CODEC and r == q['source_layout']['tensor_ref'], 'Original accepted source row, no new source tensor')
                cache[k] = extract_chunk_row(load_tensor(r), q['source_layout'])
            else:
                require(codec['codec'] == CROP_CODEC, 'First new lossless crop codec')
                cache[k] = torch.load(io.BytesIO(gzip.decompress(load_bytes(r))), map_location='cpu', weights_only=True)
        v = {n:cache[k][n] for n in ('pixel_values', 'image_grid_thw')}
        require(signature(v) == codec['decoded_signature'], 'Actual decoded new crop/source bytes differ')
        views.append(v)
    grid = torch.cat([v['image_grid_thw'] for v in views]); packed = image.pack_image_pixels([v['pixel_values'] for v in views], grid)
    tokens = load_tensor(q['tokens']); require(set(tokens) == {'input_ids','attention_mask'}, 'Prefix-only production tokens')
    values = dict(**tokens, **packed)
    require(signature(values) == q['input_signature'] and grid.tolist() == q['image_grid_thw'], 'First-QA production fourtensor mapping')
    return values


class ProductionInputs:
    """Same constructor as58; only complete61 gate can admit the fixedD reader."""
    def __init__(self, prepared, *, gate, prepared_ref, registration_ref, load_json, load_tensor, image, load_bytes=None):
        require(gate['status'] == GATE and gate['prepared'] == file_ref(prepared_ref) and gate['registration'] == file_ref(registration_ref)
            and prepared['schema'] == 'STAR_PRODUCTION_PREPARED_V72' and prepared['scope'] == gate['scope'] == 'production'
            and prepared['profile'] == PROFILE and prepared['native_RGB_recovered'] is gate['native_RGB_recovered'] is False
            and gate['first_independent_crop_processor_QA'] is True and gate['first_compressed_save_and_reader_roundtrip'] is True
            and prepared['selection'] == SELECTION and prepared['official_source_count'] == gate['official_source_count'] == 426,
            'Actual full selectedD CPU61 gate, not capacity pilot')
        entries = prepared['inference_inputs']; require(entries == prepared['execution_entries'] and prepared['adopted_success'] == {}, 'Formal outputs not yet run; exact all-new request inventory')
        self.allowed = {tuple(sorted(file_ref(e['input']).items())):e for e in entries}
        require(len(self.allowed) == len(entries) and len({e['source_id'] for e in entries}) == prepared['sources'] == gate['sources'], 'Complete registered virtual observation owner count')
        self.prepared, self.load_json, self.load_tensor, self.load_bytes, self.image = prepared, load_json, load_tensor, load_bytes, image
        self.source_id, self.cache = None, {}
    def get(self, input_ref):
        k = tuple(sorted(file_ref(input_ref).items())); require(k in self.allowed, 'Only fixed selectedD request refs')
        e = self.allowed[k]; q = self.load_json(input_ref)
        require(all(q[n] == e[n] for n in ('id','source_id','source_sha256','role')) and q['role'] == 'production'
            and q['scope'] == 'production' and q['profile'] == PROFILE and q['native_RGB_recovered'] is False
            and q['reference_or_target_in_prompt'] is False and q['selection'] == SELECTION
            and q['source_id'] == 'official:%s:native:%d'%(q['video_id'], q['native_ordinal'])
            and q['observation_index']%2 == 0 and q['adapter_weights'] == self.prepared['adapter_weights']
            and q['value_weights'] == self.prepared['value_weights'] and q['class_token_ids'] == self.prepared['class_token_ids']
            and q['protected_baseline'] == self.prepared['protected_baseline']
            and not any(n in q for n in ('target','labels','candidate_ious','original_reference_xywh')), 'Label-free exact native observation/weight request')
        if q['source_id'] != self.source_id: self.cache.clear(); self.source_id = q['source_id']
        return read_request(q, load_tensor=self.load_tensor, load_bytes=self.load_bytes, image=self.image, cache=self.cache), q


class Writer:
    def __init__(self, root, limit=None): self.root, self.limit, self.bytes = root, limit, 0
    def write(self, path, data):
        require(self.limit is None or self.bytes+len(data) <= self.limit, 'Explicit measured-capacity additional-byte budget exceeded')
        require(shutil.disk_usage(self.root).free >= len(data), 'Insufficient live disk for actual new bytes; no fallback')
        with path.open('xb') as f: f.write(data); f.flush(); os.fsync(f.fileno())
        self.bytes += len(data)
    def json(self, path, value): self.write(path, (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode())
    def tensor(self, path, value):
        h = io.BytesIO(); torch.save(value, h); self.write(path, h.getvalue())


def _module(r, name):
    p = bound(r); spec = importlib.util.spec_from_file_location(name, p); m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m; spec.loader.exec_module(m); return m


def _source_observation(source, own_cases, writer, out, profile58, image, recovery, processor, reg, receipts):
    bytes_before_observation = writer.bytes
    directory = out/'observations'/digest(source['source_id'])[:24]; directory.mkdir(parents=True, exist_ok=False)
    raw = torch.load(bound(source['source_layout']['tensor_ref']), map_location='cpu', weights_only=True)
    vision = extract_chunk_row(raw, source['source_layout'])
    adopted = adopt_plane35(source, vision, receipts, lambda r:np.load(bound(r), allow_pickle=False), reg['recovery_code'])
    actual = profile58.prepare_source(source, own_cases, vision, processor, image, recovery, adopted_recovery=adopted)
    plane = actual['plane']; plane_ref = plane['adopted']
    if plane_ref is None:
        h = io.BytesIO(); np.save(h, plane['rgb'], allow_pickle=False); p = directory/'resized_RGB.npy'; writer.write(p, h.getvalue()); plane_ref = ref(p)
    crop_refs = {}; codecs = {}; compressed = uncompressed = 0; seconds = 0.
    for i, crop in actual['crops'].items():
        p = directory/('crop_%02d.pt.gz'%i); writer.write(p, crop['compressed'])
        require(signature(torch.load(io.BytesIO(gzip.decompress(p.read_bytes())), map_location='cpu', weights_only=True)) == crop['codec']['decoded_signature'], 'First saved crop exact lossless QA')
        crop_refs[i], codecs[i] = ref(p), crop['codec']; compressed += crop['codec']['compressed_bytes']; uncompressed += crop['codec']['uncompressed_bytes']; seconds += crop['codec']['compression_seconds']
        writer.json(directory/('crop_%02d.proof.json'%i), dict(native_box=source['pool'][i], tensor=crop_refs[i], codec=crop['codec'], render=crop['render'], independent_render=crop['independent_render']))
    entries, snapshot_cache = [], {}
    for case in actual['cases']:
        q = case['request']; a,b = q['candidate_indices']; p = directory/(q['id']+'.tokens.pt'); writer.tensor(p, case['tokens'])
        require(signature(torch.load(p, map_location='cpu', weights_only=True)) == signature(case['tokens']), 'New production prefix save/reload')
        q.update(tokens=ref(p), vision_inputs=[source['source_vision'], crop_refs[a], crop_refs[b]],
            vision_codecs=[dict(codec=SOURCE_CODEC, decoded_signature=signature(vision)), codecs[a], codecs[b]],
            source_layout=source['source_layout'], video_id=source['video_id'], native_ordinal=source['native_ordinal'],
            native_pts_exact=source['native_pts_exact'], observation_index=source['observation_index'], selection=SELECTION,
            protected_baseline=reg['protected_baseline'], adapter_weights=reg['adapter_weights'], value_weights=reg['value_weights'])
        require(q['class_token_ids'] == reg['class_token_ids'], 'Same actual digit classes and original question')
        p = directory/(q['id']+'.json'); writer.json(p, q); r = ref(p)
        read_request(q, load_tensor=lambda r:torch.load(bound(r), map_location='cpu', weights_only=True),
            load_bytes=lambda r:bound(r).read_bytes(), image=image, cache=snapshot_cache)
        entries.append(dict(id=q['id'], source_id=source['source_id'], source_sha256=source['source_sha256'], role='production', input=r))
    proof = dict(status=OBS_GATE, source_id=source['source_id'], source_metadata_sha256=digest(source),
        source_sha256=source['source_sha256'], video_id=source['video_id'], native_ordinal=source['native_ordinal'],
        native_pts_exact=source['native_pts_exact'], observation_index=source['observation_index'], entries=entries,
        resized_RGB=plane_ref, recovery=plane['recovery'], independent_recovery=plane['independent_recovery'],
        old35_recovery_adopted=plane['adopted'] is not None, new_crop_count=len(crop_refs), compressed_bytes=compressed,
        uncompressed_bytes=uncompressed, compression_seconds=seconds, first_independent_crop_processor_QA=True,
        new_bytes_before_observation_receipt=writer.bytes-bytes_before_observation,
        first_compressed_save_and_reader_roundtrip=True, native_RGB_recovered=False,
        new_source_processor_calls=0, new_original_decodes=0, model_calls=0)
    writer.json(directory/'acceptance.json', proof); return ref(directory/'acceptance.json'), proof


def run(root, phase):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '' and not torch.cuda.is_initialized(), 'Only CPU61 child')
    rp = root/'star_production_CPU_registration_72.json'; reg = read(rp)
    require(bound(reg['preparation_code']) == Path(__file__).resolve() and reg['selection'] == SELECTION, 'Exact new61 source/fixed selection')
    identity.check(reg)
    q20, q19 = read(bound(reg['resized20_quality'])), read(bound(reg['resized19_quality']))
    original_admission = read(bound(reg['production_admission'])); validate_quality(reg, q20, q19, original_admission, pilot=True)
    original_ref = ref(rp); continuation = None
    if phase == 'remaining':
        cp = root/'star_production_remaining_admission_72.json'; continuation = read(cp)
        production_admission = read(bound(continuation['production_admission']))
        validate_quality(reg, q20, q19, production_admission, pilot=False)
    budget_reg = reg if continuation is None else continuation; started = time.monotonic()
    def budget():
        require(time.monotonic()-started < budget_reg['max_seconds'] and dt.datetime.now(dt.timezone.utc) <
            dt.datetime.fromisoformat(budget_reg['deadline_utc'].replace('Z','+00:00')), 'Registered CPU61/Goal budget')
    budget(); out = root/'star_production_inputs_72'
    if phase == 'pilot32': out.mkdir(exist_ok=False)
    else: require(out.is_dir(), 'Remaining must adopt original capacity pilot')
    writer = Writer(out, continuation['max_additional_bytes'] if continuation else None)
    writer.json(out/(phase+'_claim.json'), dict(utc=utc(), registration=original_ref, continuation=ref(cp) if continuation else None, production_GPU_admitted=False))
    completed, current = [], None
    try:
        geometry = _module(reg['geometry_code'], '_star72_61_geometry'); image = _module(reg['image_code'], '_star72_61_image')
        recovery = _module(reg['recovery_code'], '_star72_61_recovery'); profile58 = _module(reg['profile_code'], '_star72_61_profile58')
        if phase == 'pilot32':
            accepted = read(bound(reg['accepted_production'])); metadata = read(bound(reg['production_metadata']))
            accepted_root = Path(reg['accepted_root']); require(accepted_root == bound(reg['accepted_production']).parent, 'Exact original accepted production root')
            clocks, source_refs = {}, {}; meta = {m['video_id']:m for m in metadata['records']}
            for s in accepted['sources']:
                if meta[s['id']]['targetRatioWH'] != [16,9]: continue
                directory = accepted_root/'inputs'/s['id']; clock_ref = dict(path=str(directory/'clock.json'), sha256=s['clock_sha256'])
                clocks[s['id']] = read(bound(clock_ref)); ap = directory/'acceptance.json'
                require(read(ap) == s, 'Original whole-source accepted input record changed')
                source_refs[s['id']] = dict(clock=clock_ref, acceptance=ref(ap))
            with zipfile.ZipFile(bound(reg['protected_baseline'])) as z:
                require(z.namelist() == ['predictions.jsonl'], 'Original protected40.47 member')
                baseline = [json.loads(line) for line in z.read('predictions.jsonl').splitlines() if line.strip()]
            domain = compile_domain(accepted, metadata, baseline, clocks, source_refs, geometry)
            plan = case_plan(domain['selected_D'])
            writer.json(out/'domain.json', domain); writer.json(out/'case_plan.json', plan)
            writer.json(out/'source_catalog.json', dict(sources=domain['selected_D'], official_sources=domain['official_sources'],
                official_source_count=426, affected_video_count=domain['affected_video_count'], GT_included=False,
                protected_baseline=reg['protected_baseline'], all_other_baseline_frames_and_boxes_unchanged=True))
            ids = domain['pilot_source_ids']; proof_refs = []
        else:
            pilot = read(bound(continuation['pilot_acceptance'])); domain = read(bound(continuation['domain']))
            require(bound(continuation['domain']) == (out/'domain.json').resolve()
                and continuation['domain'] == pilot['domain']
                and continuation['source_catalog'] == pilot['source_catalog'] and continuation['case_plan'] == pilot['case_plan'], 'Exact frozen domain/catalog/case-plan refs')
            validate_continuation(reg, continuation, pilot, domain, original_ref)
            require(production_admission['expected_sources'] == production_admission['observations'] == domain['selected_D_count']
                and production_admission['official_source_count'] == 426
                and production_admission['affected_video_count'] == domain['affected_video_count'], 'Admitted complete fixed observation/official-video counts')
            plan = read(bound(continuation['case_plan'])); ids = domain['remaining_source_ids']; proof_refs = list(pilot['observation_acceptances'])
            require(len(proof_refs) == 32, 'Adopt complete original32 successful observation proofs')
        from transformers import AutoProcessor
        cfg = read(bound(reg['model_config'])); processor = AutoProcessor.from_pretrained(cfg['model_dir'], local_files_only=True, min_pixels=65536, max_pixels=65536)
        receipts = [read(bound(r)) for r in reg.get('recovery_receipts', [])]
        source_map = {s['source_id']:s for s in domain['selected_D']}; all_proofs = []
        for r in proof_refs:
            p = read(bound(r)); require(p['status'] == OBS_GATE and p['source_metadata_sha256'] == digest(source_map[p['source_id']]), 'Exact adopted pilot source proof')
            all_proofs.append(p)
        require([p['source_id'] for p in all_proofs] == ([] if phase == 'pilot32' else domain['pilot_source_ids']), 'Pilot success order not repeated')
        for sid in ids:
            budget(); current = sid; source = source_map[sid]; cases = [c for c in plan['cases'] if c['source_id'] == sid]
            r,p = _source_observation(source, cases, writer, out, profile58, image, recovery, processor, reg, receipts)
            proof_refs.append(r); all_proofs.append(p); completed.append(r)
            writer.json(out/(phase+'_completed_%06d.json'%len(completed)), dict(source_id=sid, acceptance=r))
        budget(); require(not torch.cuda.is_initialized(), 'CPU production preparation initialized CUDA')
        stats = dict(new_bytes_before_receipt=writer.bytes, elapsed_seconds=time.monotonic()-started,
            compressed_bytes=sum(p['compressed_bytes'] for p in all_proofs), uncompressed_bytes=sum(p['uncompressed_bytes'] for p in all_proofs),
            compression_seconds=sum(p['compression_seconds'] for p in all_proofs), new_crop_count=sum(p['new_crop_count'] for p in all_proofs),
            new_observations_this_phase=len(ids), adopted_pilot_observations=0 if phase == 'pilot32' else 32,
            new_observation_payload_bytes_this_phase=sum(p['new_bytes_before_observation_receipt'] for p in all_proofs[-len(ids):]) if ids else 0,
            byte_scope='CURRENT_CPU_PHASE_WRITES_BEFORE_RECEIPT', compression_scope='ALL_ADOPTED_AND_NEW_OBSERVATION_CROPS')
        common = dict(registration=original_ref, domain=ref(out/'domain.json'), source_catalog=ref(out/'source_catalog.json'),
            case_plan=ref(out/'case_plan.json'), observation_acceptances=proof_refs, pilot_source_ids=domain['pilot_source_ids'],
            all_D_count=domain['all_D_count'], all_D_sha256=domain['all_D_sha256'], selected_D_count=domain['selected_D_count'],
            selected_D_sha256=domain['selected_D_sha256'], selection=SELECTION, **stats)
        if phase == 'pilot32':
            writer.json(out/'pilot_acceptance.json', dict(status=PILOT_GATE, capacity_only=True, observations=32,
                model_calls=0, production_admitted=False, automatic_remaining=False, **common)); return
        entries = [e for p in all_proofs for e in p['entries']]
        require(len(all_proofs) == domain['selected_D_count'] and [p['source_id'] for p in all_proofs] == [s['source_id'] for s in domain['selected_D']]
            and [e['id'] for e in entries] == [c['id'] for c in plan['cases']], 'Complete fixed selectedD; exact source/case order')
        prepared = dict(schema='STAR_PRODUCTION_PREPARED_V72', scope='production', profile=PROFILE, selection=SELECTION,
            inference_inputs=entries, execution_entries=entries, adopted_success={}, sources=len(all_proofs),
            official_source_count=426, affected_video_count=domain['affected_video_count'],
            source_catalog=ref(out/'source_catalog.json'), case_plan=ref(out/'case_plan.json'), label_free_case_plan=ref(out/'case_plan.json'),
            pair_index=plan['pair_index'], CPU_targets=None, class_token_ids=reg['class_token_ids'],
            adapter_weights=reg['adapter_weights'], value_weights=reg['value_weights'], protected_baseline=reg['protected_baseline'],
            training_completion=reg['training_completion'], star_GPU69_registration=reg['star_GPU69_registration'],
            native_RGB_recovered=False, codec=CROP_CODEC, source_codec=SOURCE_CODEC, all_D_sha256=domain['all_D_sha256'],
            selected_D_sha256=domain['selected_D_sha256'], interpolation_or_propagation=False, production_admitted=False)
        writer.json(out/'prepared.json', prepared)
        writer.json(out/'input_acceptance.json', dict(status=GATE, prepared=ref(out/'prepared.json'), scope='production',
            sources=len(all_proofs), official_source_count=426, affected_video_count=domain['affected_video_count'],
            inference_inputs=len(entries), execution_inputs=len(entries), adopted_successes=0,
            first_independent_crop_processor_QA=True, first_compressed_save_and_reader_roundtrip=True,
            native_RGB_recovered=False, source_processor_repeated=0, new_original_decode=0, model_calls=0,
            production_admitted=False, **common))
    except BaseException as error:
        Writer(out).json(out/(phase+'_failure.json'), dict(error=repr(error), traceback=traceback.format_exc(), active_source=current,
            completed_observation_proofs=completed, preserve_all_success=True, automatic_retry=False, production_admitted=False))
        raise


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--root', type=Path, required=True)
    p.add_argument('--phase', choices=['pilot32','remaining'], required=True); a=p.parse_args(); run(a.root, a.phase)
