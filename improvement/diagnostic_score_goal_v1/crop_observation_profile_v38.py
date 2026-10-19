"""Conditional in-memory CPU components for the resized-observation profile.

No entrypoint, filesystem, real-data discovery, GT read, model or GPU admission.
The caller binds actual33+37 results, persists new artifacts exclusively, and
supplies bound IO callbacks to ProfileInputs. Native failures cannot be rescued.
"""
from __future__ import annotations

import copy
import hashlib
from numbers import Integral, Real

import numpy as np
from PIL import Image
import torch

PROFILE = 'RESIZED_OBSERVATION_PLANE'
FOUR_KEYS = {'input_ids', 'attention_mask', 'pixel_values', 'image_grid_thw'}
EXCLUDED_SOURCE = 'gnmc:test:006575.jpeg'


def _require(value, message):
    if not value:
        raise ValueError(message)


def _reference(value):
    _require(isinstance(value, dict) and set(value) == {'path', 'sha256'}
        and isinstance(value['path'], str) and value['path']
        and isinstance(value['sha256'], str) and len(value['sha256']) == 64
        and all(c in '0123456789abcdef' for c in value['sha256']), 'Explicit immutable artifact reference required')
    return copy.deepcopy(value)


def signature(values):
    result = {}
    for name, value in values.items():
        _require(isinstance(value, torch.Tensor) and value.device.type == 'cpu' and not value.requires_grad
            and value.layout == torch.strided and bool(torch.isfinite(value).all()), 'Finite detached CPU input tensors required')
        result[name] = dict(shape=list(value.shape), dtype=str(value.dtype),
            sha256=hashlib.sha256(value.contiguous().view(torch.uint8).numpy().tobytes()).hexdigest())
    return result


def _classes(values):
    _require(isinstance(values, list) and len(values) == 3
        and all(isinstance(v, Integral) and not isinstance(v, bool) and v >= 0 for v in values)
        and len(set(values)) == 3, 'Actual distinct0/1/2 next-token identities required')
    return list(map(int, values))


def _input_signature(value):
    _require(isinstance(value, dict) and set(value) == FOUR_KEYS, 'Full four-tensor signature required')
    for item in value.values():
        _require(isinstance(item, dict) and set(item) == {'shape', 'dtype', 'sha256'}
            and isinstance(item['shape'], list) and item['shape']
            and all(isinstance(v, Integral) and not isinstance(v, bool) and v > 0 for v in item['shape'])
            and isinstance(item['dtype'], str) and isinstance(item['sha256'], str)
            and len(item['sha256']) == 64 and all(c in '0123456789abcdef' for c in item['sha256']),
            'Malformed full tensor signature')
    return value


def validate_native_admission(screen_result, confirm_result, adapter_weights):
    _reference(adapter_weights)
    _require(screen_result['status'] == 'PASS_NATIVE_CROP_SCREEN_ONLY'
        and screen_result['confirm_admitted'] is True and screen_result['primary'] == 'TRAINED'
        and screen_result['fixed_final_checkpoint'] is True and screen_result['adapter_weights'] == adapter_weights,
        'Actual native33 PASS and exact final500 weights required; profile cannot rescue failure')
    _require(confirm_result['status'] == 'PASS_NATIVE_CROP_CONFIRM19_RESEARCH_ONLY'
        and confirm_result['native_research_qualified'] is True and confirm_result['primary'] == 'TRAINED'
        and confirm_result['adapter_weights'] == adapter_weights and confirm_result['original20_complete'] is False
        and confirm_result['excluded_missing_source_repeated'] is False,
        'Actual native37 PASS on unchanged remaining19 and same final500 weights required')
    return dict(status='CONDITIONAL_PROFILE_CPU_COMPONENTS_ONLY', adapter_weights=copy.deepcopy(adapter_weights),
                native_quality_failure_rescue=False, production_admitted=False)


def build_profile_plan(screen_catalog, screen_prepared, screen_plan, confirm_catalog, confirm_prepared,
                       confirm_plan, *, screen_targets_ref, confirm_targets_ref, adapter_weights,
                       screen_result, confirm_result):
    """Pure same39/pools/order/cases projection. CPU targets remain refs only."""
    validate_native_admission(screen_result, confirm_result, adapter_weights)
    targets = dict(screen=_reference(screen_targets_ref), confirm=_reference(confirm_targets_ref))
    _require(confirm_prepared['CPU_targets'] == targets['confirm'], 'Original36 CPU targets ref must remain unchanged')
    if 'CPU_targets' in screen_prepared:
        _require(screen_prepared['CPU_targets'] == targets['screen'], 'Original31 CPU targets ref must remain unchanged')
    classes = _classes(screen_prepared['class_token_ids'])
    _require(classes == _classes(confirm_prepared['class_token_ids']), 'Native screen/confirm class identities differ')
    sources, cases, pair_index, groups, all_ids, all_hashes = [], [], [], {}, set(), set()
    for role, catalog, prepared, plan, expected in (
        ('screen', screen_catalog, screen_prepared, screen_plan, 20),
        ('confirm', confirm_catalog, confirm_prepared, confirm_plan, 19)):
        _require(plan['GT_used_for_input_or_pair_choice'] is False, 'Only original GT-free plans')
        rows = [row for row in catalog['sources'] if row['role'] == role]
        _require(len(rows) == expected, 'Exact historical20screen/19confirm required')
        lookup = {}
        for row in rows:
            sid, digest = row['source_id'], row['source_sha256']
            _require(sid not in all_ids and sid != EXCLUDED_SOURCE and digest not in all_hashes,
                     'Duplicate or unavailable source in fixed39 profile')
            all_ids.add(sid); all_hashes.add(digest); lookup[sid] = row
            _require(row['pool'] and row['pool'][0] == row['baseline_box'], 'Observed native BASE must stay pool index0')
            sources.append(dict(source_id=sid, source_sha256=digest, role=role, width=row['width'], height=row['height'],
                pool=copy.deepcopy(row['pool']), baseline_box=copy.deepcopy(row['baseline_box']),
                source_vision=_reference(row['source_vision']), original_proof=_reference(row['original_proof']),
                profile=PROFILE, native_RGB_recovered=False))
        native_entries = prepared['screen_inputs' if role == 'screen' else 'confirm_inputs']
        entries = {entry['id']: entry for entry in native_entries}
        _require(len(entries) == len(native_entries), 'Duplicate native request identity')
        selected_cases = [case for case in plan['cases'] if case['source_id'] in lookup]
        _require([case['id'] for case in selected_cases] == [entry['id'] for entry in native_entries],
                 'Native source/case order must remain exact')
        mapping, role_ids = {}, []
        for case in selected_cases:
            source = lookup[case['source_id']]
            _require(entries[case['id']]['source_id'] == case['source_id']
                and all(isinstance(case[k], Integral) and not isinstance(case[k], bool)
                    and 0 <= case[k] < len(source['pool']) for k in ('a', 'b')), 'Native case/pool mapping differs')
            cid = hashlib.sha256(('CROP_PROFILE38|'+role+'|'+source['source_sha256']+'|'+case['id']).encode()).hexdigest()[:24]
            mapping[case['id']] = cid; role_ids.append(cid)
            cases.append(dict(id=cid, native_case_id=case['id'], native_input=_reference(entries[case['id']]['input']),
                source_id=case['source_id'], role=role, a=int(case['a']), b=int(case['b'])))
        for pair in plan['pair_index']:
            if pair['source_id'] in lookup:
                row = copy.deepcopy(pair)
                row['first_id'], row['reverse_id'] = mapping[pair['first_id']], mapping[pair['reverse_id']]
                pair_index.append(row)
        groups[role+'_ids'] = role_ids
    _require(len({case['id'] for case in cases}) == len(cases), 'Profile case identity collision')
    return dict(profile=PROFILE, sources=sources, cases=cases, pair_index=pair_index, **groups,
        class_token_ids=classes, CPU_targets=targets, adapter_weights=_reference(adapter_weights),
        GT_used_for_input_or_pair_choice=False, native_RGB_recovered=False,
        historical_exposure=True, new_blind_sources=0, production_admitted=False)


def prepare_source_profile(source, source_vision, cases, native_inputs, processor, *, recovery, image,
                           screen_result, confirm_result, adapter_weights):
    """One-source memory-only first CPU construction; caller persists artifacts.

    native_inputs[native_case_id]={request: old_request, tokens: adopted_tokens}.
    No old crop tensor or native RGB is accepted by this interface.
    """
    validate_native_admission(screen_result, confirm_result, adapter_weights)
    _require(source['role'] in ('screen', 'confirm') and source['source_id'] != EXCLUDED_SOURCE
        and cases and all(case['source_id'] == source['source_id'] and case['role'] == source['role'] for case in cases),
        'Only one registered historical profile source at a time')
    old_vision = {key: source_vision[key] for key in ('pixel_values', 'image_grid_thw')}
    rgb, recovery_proof = recovery.recover_observation_rgb(old_vision['pixel_values'], old_vision['image_grid_thw'])
    recovery_check = recovery.independent_recovery_check(old_vision['pixel_values'], old_vision['image_grid_thw'], rgb, recovery_proof)
    _require(recovery_proof['native_RGB_recovered'] is False and recovery_proof['profile'] == PROFILE,
             'Recovered pixels are only the processor-resized observation')
    needed = sorted({case[key] for case in cases for key in ('a', 'b')})
    _require(needed == list(range(len(source['pool']))), 'Original complete candidate/control inventory required')
    crops, outputs = {}, []
    for index in needed:
        box = source['pool'][index]
        rendered, render_proof = recovery.render_observation_crop(rgb, box, [source['width'], source['height']])
        render_check = recovery.independent_observation_crop_check(rgb, box, [source['width'], source['height']], rendered, render_proof)
        values = dict(processor.image_processor(images=[Image.fromarray(rendered)], return_tensors='pt'))
        check = dict(processor.image_processor(images=[Image.fromarray(rendered.copy())], return_tensors='pt'))
        _require(set(values) == set(check) == {'pixel_values', 'image_grid_thw'} and signature(values) == signature(check),
                 'First new observation-crop independent processor bits differ')
        crops[index] = dict(vision=values, rendered_rgb=rendered, render=render_proof,
            independent_render=render_check, first_new_processor_calls=1, first_independent_processor_calls=1)
    for case in cases:
        native = native_inputs[case['native_case_id']]
        request, old_tokens = native['request'], native['tokens']
        a, b = case['a'], case['b']
        _require(request['source_id'] == source['source_id'] and request['source_sha256'] == source['source_sha256']
            and request['role'] == source['role'] and request['reference_or_target_in_prompt'] is False
            and request['candidate_indices'] == [a, b] and request['boxes'] == [source['pool'][a], source['pool'][b]]
            and request['vision_inputs'][0] == source['source_vision'], 'Original native request/source/pool/order differs')
        _require(set(old_tokens) == {'input_ids', 'attention_mask'}
            and signature(old_tokens) == {key: request['input_signature'][key] for key in old_tokens},
            'Original native token reference/signature differs')
        views = [old_vision, crops[a]['vision'], crops[b]['vision']]
        grid = torch.cat([view['image_grid_thw'] for view in views])
        packed = image.pack_image_pixels([view['pixel_values'] for view in views], grid)
        image.independent_pixel_check([view['pixel_values'] for view in views], grid, packed)
        adopted_tokens = grid.tolist() == request['image_grid_thw']
        if adopted_tokens:
            tokens, text = old_tokens, copy.deepcopy(request['text_evidence'])
        else:
            tokens, text = image.build_text_input(processor, grid)
        _require(text['question'] == request['text_evidence']['question'] == image.QUESTION
            and _classes(text['class_token_ids']) == _classes(request['class_token_ids']), 'Native question/class identity changed')
        text_check = image.independent_text_check(processor, packed, tokens, text)
        values = dict(**tokens, **packed)
        _require(set(values) == FOUR_KEYS, 'Exactly four profile input tensors required')
        new_request = dict(id=case['id'], native_case_id=case['native_case_id'], native_request=case['native_input'],
            source_id=source['source_id'], source_sha256=source['source_sha256'], role=source['role'], profile=PROFILE,
            native_RGB_recovered=False, boxes=copy.deepcopy(request['boxes']), candidate_indices=[a, b],
            source_vision=_reference(source['source_vision']), input_signature=signature(values), image_grid_thw=grid.tolist(),
            class_token_ids=_classes(text['class_token_ids']), text_evidence=text, adopted_native_tokens=adopted_tokens,
            reference_or_target_in_prompt=False, adapter_weights=_reference(adapter_weights))
        outputs.append(dict(request=new_request, values=values, tokens=tokens,
            adopted_tokens_ref=_reference(request['tokens']) if adopted_tokens else None,
            native_crop_refs=copy.deepcopy(request['vision_inputs'][1:]), independent_text=text_check))
    return dict(source_id=source['source_id'], observation_rgb=rgb, recovery=recovery_proof,
        independent_recovery=recovery_check, crops=crops, cases=outputs, native_RGB_recovered=False,
        old_source_processor_repeated=0, new_original_decodes=0, production_admitted=False)


def materialize_request(case_output, crop_refs, tokens_ref=None):
    """Attach caller's newly persisted crop/token refs; never use old native crops."""
    request = copy.deepcopy(case_output['request'])
    a, b = request['candidate_indices']
    new_crops = [_reference(crop_refs[a]), _reference(crop_refs[b])]
    _require(all(value not in case_output['native_crop_refs'] for value in new_crops),
             'Old native crop artifacts cannot stand in for first-new profile encodings')
    request['vision_inputs'] = [request.pop('source_vision')]+new_crops
    request['native_crop_refs_for_no_reuse_check'] = copy.deepcopy(case_output['native_crop_refs'])
    adopted = case_output['adopted_tokens_ref']
    if adopted is not None:
        _require(tokens_ref is None or tokens_ref == adopted, 'Same-grid native token reference must be adopted unchanged')
        request['tokens'] = _reference(adopted)
    else:
        request['tokens'] = _reference(tokens_ref)
    return request


def _probabilities(values):
    _require(isinstance(values, (list, tuple)) and len(values) == 3
        and all(isinstance(v, Real) and not isinstance(v, bool) and np.isfinite(v) and 0 <= v <= 1 for v in values)
        and abs(sum(values)-1.) <= 1e-6, 'Actual finite three-class accepted probabilities required')
    return list(map(float, values))


def find_native_alias(request, accepted_successes, adapter_weights):
    """No raw QA here: compare already accepted final500 full-input evidence."""
    _reference(adapter_weights)
    _require(request['role'] in ('screen', 'confirm') and request['profile'] == PROFILE
        and request['native_RGB_recovered'] is False, 'Explicit profile role required')
    classes, fingerprint = _classes(request['class_token_ids']), _input_signature(request['input_signature'])
    _require(request['adapter_weights'] == adapter_weights, 'Profile must keep final500 weights')
    expected_role = 'TRAINED_'+request['role']
    matches = []
    for old in accepted_successes:
        if (old['source_id'], old['source_sha256']) != (request['source_id'], request['source_sha256']):
            continue
        _require(old['first_output_QA_passed'] is True and old['model_role'] == expected_role
            and old['adapter_weights'] == adapter_weights, 'Alias source evidence is not accepted same-role final500 inference')
        if _classes(old['class_token_ids']) == classes and _input_signature(old['input_signature']) == fingerprint:
            matches.append(dict(native_request=_reference(old['native_request']), receipt=_reference(old['receipt']),
                probabilities3=_probabilities(old['probabilities3']), adapter_weights=_reference(adapter_weights)))
    if not matches:
        return None
    _require(all(match['probabilities3'] == matches[0]['probabilities3'] for match in matches),
             'Conflicting already accepted probabilities for one exact input')
    return min(matches, key=lambda value: (value['native_request']['path'], value['receipt']['path']))


def partition_inputs(requests, accepted_successes, adapter_weights):
    """Requests carry an input artifact ref supplied by the exclusive writer."""
    executions, adopted, all_entries, seen = [], {}, [], set()
    for request in requests:
        _require(request['id'] not in seen, 'Duplicate profile input identity')
        seen.add(request['id'])
        entry = dict(id=request['id'], source_id=request['source_id'], role=request['role'], input=_reference(request['input']))
        all_entries.append(entry)
        alias = find_native_alias(request, accepted_successes, adapter_weights)
        if alias is None:
            executions.append(entry)
        else:
            adopted[request['id']] = alias
    return dict(all_entries=all_entries, execution_entries=executions, adopted_success=adopted,
        actual_new_inputs=len(executions), adopted_native_successes=len(adopted), raw_QA_repeated=0)


class ProfileInputs:
    """Callback-based bound reader, execution-only; never opens CPU targets."""
    def __init__(self, prepared, *, load_json, load_tensor, image):
        _require(prepared['profile'] == PROFILE, 'Explicit profile prepared manifest required')
        self.prepared, self.load_json, self.load_tensor, self.image = prepared, load_json, load_tensor, image
        self.allowed = {tuple(sorted(entry['input'].items())): entry for entry in prepared['execution_entries']}
        _require(len(self.allowed) == len(prepared['execution_entries']), 'Duplicate execution input refs')
        self.cache, self.current_source = {}, None

    def get(self, reference):
        key = tuple(sorted(_reference(reference).items()))
        _require(key in self.allowed, 'Only truly new admitted execution refs may be read')
        entry = self.allowed[key]; request = self.load_json(reference)
        _require(request['id'] == entry['id'] and request['source_id'] == entry['source_id']
            and request['role'] == entry['role'] and request['role'] in ('screen', 'confirm')
            and request['source_id'] != EXCLUDED_SOURCE and request['profile'] == PROFILE
            and request['native_RGB_recovered'] is False and request['reference_or_target_in_prompt'] is False,
            'Profile input source/role/identity changed')
        _require(request['adapter_weights'] == self.prepared['adapter_weights'], 'Reader must keep the registered final500 weights')
        if request['source_id'] != self.current_source:
            self.cache.clear(); self.current_source = request['source_id']
        views = []
        _require(len(request['vision_inputs']) == 3, 'Source/A/B exactly three views required')
        _require(all(value not in request['native_crop_refs_for_no_reuse_check'] for value in request['vision_inputs'][1:]),
                 'Reader rejects old native crop artifacts reused as profile input')
        for item in request['vision_inputs']:
            cache_key = tuple(sorted(_reference(item).items()))
            if cache_key not in self.cache:
                raw = self.load_tensor(item)
                self.cache[cache_key] = {name: raw[name] for name in ('pixel_values', 'image_grid_thw')}
            views.append(self.cache[cache_key])
        grid = torch.cat([view['image_grid_thw'] for view in views])
        packed = self.image.pack_image_pixels([view['pixel_values'] for view in views], grid)
        tokens = self.load_tensor(request['tokens'])
        _require(set(tokens) == {'input_ids', 'attention_mask'}, 'Prefix-only accepted tokens required')
        values = dict(**tokens, **packed)
        _require(set(values) == FOUR_KEYS and signature(values) == request['input_signature']
            and grid.tolist() == request['image_grid_thw']
            and _classes(request['class_token_ids']) == _classes(self.prepared['class_token_ids']),
            'Actual profile four-tensor signature/class/grid differs')
        return values, request
