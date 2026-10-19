"""Bounded CPU layout feasibility from explicitly registered accepted tensors.

This recovers PROCESSOR-RESIZED observations, never original/native RGB.
No processor, media decoder, model, GT, quality metric or production admission.
Each invocation owns a new exclusive output directory; there is no resume.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import traceback
from numbers import Integral

import numpy as np
import torch

SCHEMA = 'RESIZED_OBSERVATION_LAYOUT_FEASIBILITY_V35'
NORMALIZATION = 'FLOAT32(u-127.5)/127.5'
OUTPUT_DIRECTORY = 'observation_feasibility_35'


def _require(value, message):
    if not value:
        raise ValueError(message)


def _integer(value):
    _require(isinstance(value, Integral) and not isinstance(value, (bool, np.bool_)), 'Explicit integer required')
    return int(value)


def _sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def _sha_string(value):
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def _reference(value):
    _require(isinstance(value, dict) and set(value) == {'path', 'sha256'}
        and isinstance(value['path'], str) and Path(value['path']).is_absolute()
        and _sha_string(value['sha256']), 'Explicit absolute path/SHA256 reference required')
    return value


def _bound(value):
    value = _reference(value)
    path = Path(value['path'])
    _require(path.is_file() and _sha(path) == value['sha256'], 'Registered artifact missing or changed: '+str(path))
    return path


def _ref(path):
    path = Path(path).resolve()
    return dict(path=str(path), sha256=_sha(path))


def _read(path):
    with Path(path).open(encoding='utf-8') as stream:
        return json.load(stream)


def _save(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, allow_nan=False, indent=2)
        stream.write('\n')


def _module(reference, name):
    path = _bound(reference)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _identity(source):
    _require(isinstance(source, dict) and set(source) == {'source_id', 'source_sha256'}
        and isinstance(source['source_id'], str) and source['source_id']
        and _sha_string(source['source_sha256']), 'Explicit source identity required')
    return source['source_id'], source['source_sha256']


def _layout(layout):
    _require(isinstance(layout, dict) and set(layout) == {'tensor_ref', 'pixel_key', 'row_start',
        'row_end_exclusive', 'grid_thw', 'grid_locator', 'normalization'}, 'Explicit supported layout fields required')
    _reference(layout['tensor_ref'])
    _require(isinstance(layout['pixel_key'], str) and layout['pixel_key'], 'Explicit flat dictionary pixel key required')
    start, end = _integer(layout['row_start']), _integer(layout['row_end_exclusive'])
    grid = layout['grid_thw']
    _require(isinstance(grid, (list, tuple)) and len(grid) == 3, 'One explicit static THW grid required')
    t, h, w = map(_integer, grid)
    _require(t == 1 and h > 0 and w > 0 and h % 2 == w % 2 == 0
        and 0 <= start < end and end-start == h*w, 'Static merge2 grid/half-open patch-row range mismatch')
    _require(layout['normalization'] == NORMALIZATION, 'Unsupported normalization; no approximate inverse')
    locator = layout['grid_locator']
    _require(isinstance(locator, dict), 'Explicit grid evidence locator required')
    if locator.get('kind') == 'TENSOR_ROW':
        _require(set(locator) == {'kind', 'key', 'row_index'} and isinstance(locator['key'], str) and locator['key'],
                 'Explicit saved grid key and row index required')
        _require(_integer(locator['row_index']) >= 0, 'Negative saved grid row')
    else:
        _require(set(locator) == {'kind', 'evidence_ref'} and locator['kind'] == 'REGISTERED_CONSTANT',
                 'Unsupported grid locator; never infer chunk layout')
        _reference(locator['evidence_ref'])
    return start, end, [t, h, w]


def extract_pixels(payload, layout):
    """Pure explicit2D dict-key/row slicing; returns pixels and grid[1,3].

    REGISTERED_CONSTANT evidence bytes are bound by run(); this pure function
    only validates its schema. Other chunk/container layouts are unsupported.
    """
    start, end, grid = _layout(layout)
    _require(isinstance(payload, dict) and layout['pixel_key'] in payload, 'Registered flat pixel key missing')
    value = payload[layout['pixel_key']]
    _require(isinstance(value, torch.Tensor) and value.device.type == 'cpu' and value.dtype == torch.float32
        and value.layout == torch.strided and value.ndim == 2 and value.shape[1] == 1536
        and not value.requires_grad and end <= value.shape[0], 'Unsupported tensor rank/dtype/row range')
    locator = layout['grid_locator']
    if locator['kind'] == 'TENSOR_ROW':
        saved = payload.get(locator['key'])
        _require(isinstance(saved, torch.Tensor) and saved.device.type == 'cpu' and saved.dtype == torch.int64
            and saved.ndim == 2 and saved.shape[1] == 3 and locator['row_index'] < saved.shape[0],
            'Registered actual saved grid row missing or invalid')
        _require(saved[locator['row_index']].tolist() == grid, 'Registered grid differs from the actual saved row')
    selected = value[start:end].contiguous()
    _require(bool(torch.isfinite(selected).all()), 'Nonfinite selected observation pixels')
    return selected, torch.tensor([grid], dtype=torch.int64)


def validate_registration(registration):
    """Structural/selection check only. No GT or source-file inspection."""
    fields = {'schema', 'self_code', 'recovery_code', 'geometry_code', 'deadline_utc', 'selection', 'external', 'production'}
    _require(isinstance(registration, dict) and set(registration) in (fields, fields|{'identity_evidence_refs'}),
             'Exact v35 registration fields required')
    _require(registration['schema'] == SCHEMA, 'Explicit observation-layout registration required')
    for key in ('self_code', 'recovery_code', 'geometry_code'):
        _reference(registration[key])
    evidence = registration.get('identity_evidence_refs', [])
    _require(isinstance(evidence, list), 'Identity evidence must be an explicit reference list')
    for reference in evidence:
        _reference(reference)
    deadline = dt.datetime.fromisoformat(registration['deadline_utc'].replace('Z', '+00:00'))
    _require(deadline.tzinfo is not None, 'Timezone-aware Goal deadline required')
    selection = registration['selection']
    _require(isinstance(selection, dict) and set(selection) == {'method', 'candidate_sources'}
        and selection['method'] == 'LEXICOGRAPHIC_SOURCE_SHA256_FIRST4', 'Frozen GT-free SHA source selection required')
    candidates = selection['candidate_sources']
    _require(isinstance(candidates, list) and len(candidates) >= 4, 'At least4 registered external candidate identities required')
    identities = [_identity(source) for source in candidates]
    _require(len({x[0] for x in identities}) == len(identities) and len({x[1] for x in identities}) == len(identities),
             'Distinct registered external candidate identities/SHA required')
    selected = sorted(identities, key=lambda value: (value[1], value[0]))[:4]
    external, production = registration['external'], registration['production']
    _require(isinstance(external, list) and len(external) == 4
        and isinstance(production, list) and len(production) <= 2, 'Exactly4 external and at most2 production observations')
    entries, seen = [], set()
    for scope, rows in (('external', external), ('production', production)):
        for entry in rows:
            _require(isinstance(entry, dict) and set(entry) == {'entry_id', 'source_id', 'source_sha256',
                'native_dimensions', 'accepted_input_ref', 'layout'}, 'Exact label-free observation entry schema required')
            name = entry['entry_id']
            _require(isinstance(name, str) and name and len(name) <= 80
                and all(c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in name)
                and name not in seen, 'Unique safe entry_id required')
            seen.add(name)
            _identity({key: entry[key] for key in ('source_id', 'source_sha256')})
            dims = entry['native_dimensions']
            _require(isinstance(dims, list) and len(dims) == 2 and all(_integer(v) > 0 for v in dims),
                     'Original native dimensions[W,H] required; never infer from resized image')
            _reference(entry['accepted_input_ref'])
            _layout(entry['layout'])
            entries.append((scope, entry))
    _require([(row['source_id'], row['source_sha256']) for row in external] == selected,
             'External4 are not the frozen SHA-first4 order; no quality selection')
    return entries


def run(root, registration_path=None):
    """One first CPU feasibility pass; exclusive output, fail/preserve, no resume."""
    _require(os.environ.get('CUDA_VISIBLE_DEVICES') == '' and not torch.cuda.is_initialized(), 'CPU-only child required')
    root = Path(root).resolve()
    registration_path = Path(registration_path) if registration_path else root/'observation_feasibility_registration_35.json'
    out = root/OUTPUT_DIRECTORY
    out.mkdir(exist_ok=False)
    completed, active = [], None
    try:
        registration_ref = _ref(registration_path)
        reg = _read(registration_path)
        entries = validate_registration(reg)
        _require(_bound(reg['self_code']).resolve() == Path(__file__).resolve(), 'Exact frozen feasibility code required')
        identities = reg.get('identity_evidence_refs', [])
        for reference in identities:
            _bound(reference)
        recovery = _module(reg['recovery_code'], '_frozen_observation_recovery35')
        geometry = _module(reg['geometry_code'], '_frozen_observation_geometry35')
        _save(out/'claim.json', dict(registration=registration_ref, identity_evidence_refs=identities,
            identity_mapping_basis='FROZEN_REGISTRATION_WITH_BOUND_EVIDENCE_NOT_REDERIVED', native_RGB_recovered=False,
            new_processor_calls=0, new_original_decodes=0, new_model_calls=0, production_admitted=False))
        for scope, entry in entries:
            active = entry['entry_id']
            deadline = dt.datetime.fromisoformat(reg['deadline_utc'].replace('Z', '+00:00'))
            _require(dt.datetime.now(dt.timezone.utc) < deadline, 'Outside registered Goal deadline')
            directory = out/active
            directory.mkdir(exist_ok=False)
            _bound(entry['accepted_input_ref'])
            layout = entry['layout']
            locator = layout['grid_locator']
            if locator['kind'] == 'REGISTERED_CONSTANT':
                _bound(locator['evidence_ref'])
            payload = torch.load(_bound(layout['tensor_ref']), map_location='cpu', weights_only=True)
            pixels, grid = extract_pixels(payload, layout)
            rgb, recovery_proof = recovery.recover_observation_rgb(pixels, grid)
            recovery_check = recovery.independent_recovery_check(pixels, grid, rgb, recovery_proof)
            _require(recovery_proof['native_RGB_recovered'] is False and recovery_proof['profile'] == 'RESIZED_OBSERVATION_PLANE'
                and recovery_proof['normalization'] == NORMALIZATION,
                     'Recovery must remain explicitly non-native')
            image_path = directory/'resized_RGB.npy'
            with image_path.open('xb') as stream:
                np.save(stream, rgb, allow_pickle=False)
            width, height = entry['native_dimensions']
            pool = geometry.candidate_pool(width, height)
            _require(len(pool) >= 2, 'Fewer than2 unique fixed geometries; not a padded success')
            crops = []
            for index, box in enumerate(pool[:2]):
                crop, proof = recovery.render_observation_crop(rgb, box, [width, height])
                check = recovery.independent_observation_crop_check(rgb, box, [width, height], crop, proof)
                path = directory/('crop_%02d.npy'%index)
                with path.open('xb') as stream:
                    np.save(stream, crop, allow_pickle=False)
                crops.append(dict(candidate_index=index, native_box=box, resized_crop=_ref(path), render=proof, check=check))
            receipt = directory/'receipt.json'
            _save(receipt, dict(status='PASS_RESIZED_OBSERVATION_LAYOUT_ONLY', scope=scope, entry=entry,
                native_RGB_recovered=False, native_dimensions=[width, height], resized_RGB=_ref(image_path),
                recovery=recovery_proof, independent_recovery=recovery_check, fixed_pool_size=len(pool), crops=crops,
                formula_code=reg['recovery_code'], geometry_code=reg['geometry_code'], self_code=reg['self_code'],
                registration=registration_ref, adopted_old_success_ref=entry['accepted_input_ref'],
                identity_evidence_refs=identities,
                identity_mapping_basis='FROZEN_REGISTRATION_WITH_BOUND_EVIDENCE_NOT_REDERIVED',
                new_processor_calls=0, new_original_decodes=0, new_model_calls=0, GT_read=False,
                quality_evaluated=False, production_admitted=False))
            completed.append(_ref(receipt))
            del payload, pixels, rgb
        _require(not torch.cuda.is_initialized(), 'Feasibility initialized CUDA')
        result = dict(status='PASS_RESIZED_OBSERVATION_LAYOUT_FEASIBILITY_ONLY', registration=registration_ref,
            identity_evidence_refs=identities,
            external_sources=4, production_observations=len(reg['production']), receipts=completed,
            native_RGB_recovered=False, new_processor_calls=0, new_original_decodes=0, new_model_calls=0,
            GT_read=False, quality_evaluated=False, production_admitted=False,
            limitation='Recovered processor-resized observations cannot restore native pixels or rescue native-quality failure.')
        _save(out/'result.json', result)
        return result
    except BaseException as error:
        _save(out/'failure.json', dict(status='FAIL_PRESERVE_NO_FALLBACK_NO_AUTOMATIC_RETRY', active_entry=active,
            error=str(error), traceback=traceback.format_exc(), completed_receipts=completed,
            native_RGB_recovered=False, production_admitted=False))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--registration', type=Path)
    args = parser.parse_args()
    run(args.root, args.registration)
