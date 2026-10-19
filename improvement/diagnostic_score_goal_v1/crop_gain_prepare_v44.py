"""Pure44 plans/new-combination QA and callback reader for final500 readouts.

No CLI, artifact writer, image encoding/decoding, labels, model or GPU admission.
The caller binds old artifacts and writes an exclusive actual first-QA gate.
Old native quality STOP is retained; this is a new-purpose gain-critic arm.
"""
from __future__ import annotations

import copy
import datetime as dt
import hashlib
from numbers import Integral

import torch

SCHEMA = 'CROP_GAIN_FINAL500_CPU_INPUTS_V44'
GATE = 'PASS_ALL_GAIN44_2408_ADOPT2000_NEW408_COMBINATIONS_FIRST_CPU_QA'
FOUR_KEYS = {'input_ids', 'attention_mask', 'pixel_values', 'image_grid_thw'}


def _require(value, message):
    if not value:
        raise ValueError(message)


def _reference(value):
    _require(isinstance(value, dict) and set(value) == {'path', 'sha256'}
        and isinstance(value['path'], str) and value['path'] and isinstance(value['sha256'], str)
        and len(value['sha256']) == 64 and all(c in '0123456789abcdef' for c in value['sha256']),
        'Explicit immutable artifact reference required')
    return copy.deepcopy(value)


def _refkey(value):
    return tuple(sorted(_reference(value).items()))


def _key(*values):
    return hashlib.sha256('|'.join(map(str, values)).encode()).hexdigest()[:24]


def signature(values):
    result = {}
    for name, value in values.items():
        _require(isinstance(value, torch.Tensor) and value.device.type == 'cpu' and not value.requires_grad
            and value.layout == torch.strided and bool(torch.isfinite(value).all()), 'Finite detached CPU input tensors required')
        result[name] = dict(shape=list(value.shape), dtype=str(value.dtype),
            sha256=hashlib.sha256(value.contiguous().view(torch.uint8).numpy().tobytes()).hexdigest())
    return result


def _classes(value):
    _require(isinstance(value, list) and len(value) == 3 and len(set(value)) == 3
        and all(isinstance(v, Integral) and not isinstance(v, bool) and v >= 0 for v in value),
        'Distinct actual0/1/2 class identities required')
    return list(map(int, value))


def validate_cpu_registration(reg, *, training_completion, old_stop, old_gate):
    """Pure artifact-metadata checks; caller verifies every referenced byte."""
    _require(reg['schema'] == SCHEMA and reg['purpose'] == 'FIXED_FINAL500_GAIN_CRITIC_INPUT_READOUT_ONLY',
             'Explicit new-purpose44 registration required')
    for key in ('preparation_code', 'input_code', 'image_code', 'geometry_code', 'helper_code',
                'old_prepared', 'old_catalog', 'old_case_plan', 'old_input_gate', 'CPU_targets',
                'fixed_training_completion', 'adapter_weights', 'old_STOP', 'gain_protocol'):
        _reference(reg[key])
    _require(training_completion['status'] == 'COMPLETE_FIXED_FINAL500_CROP_COMPARISON_NOT_QUALITY'
        and training_completion['completed_updates'] == 500 and training_completion['successful_micro'] == 2000
        and training_completion['adapter_reload_all288_exact'] is True
        and training_completion['adapter_weights'] == reg['adapter_weights'], 'Exact saved final500 artifact required')
    _require(isinstance(old_stop['status'], str) and old_stop['status'].startswith('STOP')
        and old_stop['adapter_weights'] == reg['adapter_weights'], 'Old quality STOP must remain explicit and unchanged')
    _require(old_gate['status'] == 'PASS_ALL_CROP31_TRIPLET_FIRST_CPU_QA'
        and old_gate['prepared'] == reg['old_prepared'], 'Only actually accepted old31 inputs may be adopted')
    deadline = dt.datetime.fromisoformat(reg['deadline_utc'].replace('Z', '+00:00'))
    _require(deadline.tzinfo is not None and reg['new_image_processor_calls'] == 0
        and reg['new_original_decodes'] == 0, 'Explicit Goal deadline and no image/decode work required')
    return dict(status='METADATA_VALIDATED_NEW_CPU_PURPOSE_ONLY', old_native_quality='STOP',
                GPU_admitted=False, production_admitted=False)


def build_gain_plan(old_catalog, old_prepared, old_case_plan, old_requests):
    """Use original chosen2 unordered/source and2000 exact request metadata.

    old_requests=[{reference: original_request_ref, request: loaded_old_request}].
    Old schedule target fields are neither inspected nor copied.
    """
    _require(old_case_plan['GT_used_for_input_or_pair_choice'] is False, 'Only original label-free case plan')
    sources = [source for source in old_catalog['sources'] if source['role'] == 'train']
    _require(len(sources) == 602 and len({s['source_id'] for s in sources}) == 602
        and len({s['source_sha256'] for s in sources}) == 602, 'Exact distinct original602 train sources required')
    source_by_id = {source['source_id']: source for source in sources}
    chosen = old_case_plan['chosen_train_pairs']
    _require(set(chosen) == set(source_by_id), 'Original two-pair source scope differs')
    classes = _classes(old_prepared['class_token_ids'])
    schedule, original_schedule = old_prepared['train_schedule'], old_case_plan['train_schedule']
    _require(len(schedule) == len(original_schedule) == len(old_requests) == 2000,
             'Exact old2000 accepted ordered requests required')
    request_map = {}
    for record in old_requests:
        key = _refkey(record['reference'])
        _require(key not in request_map, 'Duplicate accepted old request ref')
        request_map[key] = record['request']
    old_cases = {case['id']: case for case in old_case_plan['cases']}
    adopted = {}
    for row, original in zip(schedule, original_schedule):
        key = _refkey(row['input'])
        _require(key in request_map and row['id'] == original['id'] and row['source_id'] == original['source_id'],
                 'Actual old schedule/ref/order differs')
        request = request_map[key]; case = old_cases[original['case_id']]; sid = row['source_id']
        source = source_by_id[sid]; a, b = case['a'], case['b']
        _require(request['id'] == case['id'] == _key(source['source_sha256'], a, b, 'CROP31_TRIPLET')
            and case['source_id'] == request['source_id'] == sid and request['source_sha256'] == source['source_sha256']
            and request['role'] == 'train' and request['reference_or_target_in_prompt'] is False
            and request['candidate_indices'] == [a, b] and request['boxes'] == [source['pool'][a], source['pool'][b]]
            and request['vision_inputs'][0] == source['source_vision'] and _classes(request['class_token_ids']) == classes,
            'Accepted original request/source/box/class identity differs')
        pair_key = (sid, int(a), int(b))
        _require(pair_key not in adopted, 'Old ordered requests are not unique')
        adopted[pair_key] = dict(input=_reference(row['input']), request=request)
    _require(len(request_map) == len(adopted) == 2000, 'Unused or duplicated old accepted request')
    ordered_sources = sorted(sources, key=lambda source: (source['source_sha256'], source['source_id']))
    cases, pair_index, catalog = [], [], []
    for source in ordered_sources:
        sid = source['source_id']; pairs = chosen[sid]
        _require(isinstance(pairs, (list, tuple)) and len(pairs) == 2 and len({tuple(p) for p in pairs}) == 2,
                 'Exactly original two distinct unordered pairs per source')
        catalog.append({key:copy.deepcopy(source[key]) for key in
            ('source_id', 'source_sha256', 'role', 'width', 'height', 'pool', 'source_vision', 'original_proof')})
        for pair in pairs:
            _require(len(pair) == 2 and all(isinstance(v, Integral) and not isinstance(v, bool) for v in pair)
                and 0 <= pair[0] < pair[1] < len(source['pool']), 'Original canonical unordered pair invalid')
            a, b = map(int, pair); ids = []
            for left, right in ((a, b), (b, a)):
                case_id = _key(source['source_sha256'], left, right, 'CROP31_TRIPLET'); ids.append(case_id)
                old = adopted.get((sid, left, right)); reverse = adopted.get((sid, right, left))
                _require(old is not None or reverse is not None, 'Missing both original orientations; cannot invent a template')
                cases.append(dict(id=case_id, source_id=sid, source_sha256=source['source_sha256'], role='train',
                    a=left, b=right, boxes=[copy.deepcopy(source['pool'][left]), copy.deepcopy(source['pool'][right])],
                    adopted_input=old is not None, input=copy.deepcopy(old['input']) if old else None,
                    template_input=copy.deepcopy((old or reverse)['input']),
                    template_case_id=(old or reverse)['request']['id']))
            pair_index.append(dict(source_id=sid, source_sha256=source['source_sha256'], a=a, b=b,
                                   first_id=ids[0], reverse_id=ids[1]))
    _require(len(cases) == len({case['id'] for case in cases}) == 2408
        and sum(case['adopted_input'] for case in cases) == 2000, 'Exact2408=adopt2000+new408 required')
    pilot_sources = [source['source_id'] for source in ordered_sources[:32]]
    pilot_ids = [case['id'] for case in cases if case['source_id'] in set(pilot_sources)]
    remaining_ids = [case['id'] for case in cases if case['source_id'] not in set(pilot_sources)]
    _require(len(pilot_ids) == 128 and len(remaining_ids) == 2280, 'Exact32x4/570x4 readout partition required')
    return dict(status='PURE_PLAN_NOT_INPUT_QA_OR_GPU_ADMISSION', cases=cases, pair_index=pair_index,
        source_catalog=dict(sources=catalog), class_token_ids=classes, pilot_source_ids=pilot_sources,
        pilot_case_ids=pilot_ids, remaining_case_ids=remaining_ids, adopted_inputs=2000, first_new_combinations=408,
        GT_used_for_input_or_pair_choice=False, new_image_processor_calls=0, new_original_decodes=0)


def build_missing_input(case, template_request, template_values, processor, image):
    """Swap only accepted crop refs/flat patch blocks, never encode an image."""
    _require(case['adopted_input'] is False and case['input'] is None and case['a'] != case['b'], 'Only missing reverse combinations')
    _require(template_request['id'] == case['template_case_id']
        and template_request['source_id'] == case['source_id'] and template_request['source_sha256'] == case['source_sha256']
        and template_request['role'] == 'train' and template_request['reference_or_target_in_prompt'] is False
        and template_request['candidate_indices'] == [case['b'], case['a']]
        and template_request['boxes'] == list(reversed(case['boxes']))
        and set(template_values) == FOUR_KEYS and signature(template_values) == template_request['input_signature'],
        'Exact accepted opposite-order template required')
    grid = template_values['image_grid_thw']
    _require(grid.dtype == torch.int64 and grid.device.type == 'cpu' and tuple(grid.shape) == (3, 3)
        and grid.tolist() == template_request['image_grid_thw'] and bool((grid[:, 0] == 1).all()), 'Three actual accepted image grids required')
    lengths = [int(row.prod()) for row in grid]
    _require(sum(lengths) == len(template_values['pixel_values']), 'Accepted patch block/grid boundaries differ')
    blocks = list(torch.split(template_values['pixel_values'], lengths, dim=0))
    views, swapped_grid = [blocks[0], blocks[2], blocks[1]], grid[[0, 2, 1]].contiguous()
    packed = image.pack_image_pixels(views, swapped_grid)
    pixel_check = image.independent_pixel_check(views, swapped_grid, packed)
    reused = torch.equal(swapped_grid, grid)
    if reused:
        tokens = {key:template_values[key] for key in ('input_ids', 'attention_mask')}
        text = copy.deepcopy(template_request['text_evidence'])
    else:
        tokens, text = image.build_text_input(processor, swapped_grid)
    _require(_classes(text['class_token_ids']) == _classes(template_request['class_token_ids'])
        and text['question'] == template_request['text_evidence']['question'] == image.QUESTION,
        'Class/question must remain the fixed original31 contract')
    text_check = image.independent_text_check(processor, packed, tokens, text)
    request = copy.deepcopy(template_request)
    request.update(id=case['id'], candidate_indices=[case['a'], case['b']], boxes=copy.deepcopy(case['boxes']),
        vision_inputs=[template_request['vision_inputs'][i] for i in (0, 2, 1)],
        tokens=_reference(template_request['tokens']) if reused else None, image_grid_thw=swapped_grid.tolist(),
        class_token_ids=_classes(text['class_token_ids']), text_evidence=text, input_signature=signature(dict(**tokens, **packed)),
        gain44_new_combination=True, adopted_opposite_template=case['template_input'],
        adopted_native_tokens=reused, reference_or_target_in_prompt=False)
    values = dict(**tokens, **packed)
    return values, request, dict(pixel_check=pixel_check, text_check=text_check,
        adopted_tokens_ref=copy.deepcopy(request['tokens']), first_new_combination_QA=True,
        new_image_processor_calls=0, new_original_decodes=0, old_successful_input_QA_repeated=False)


def materialize_missing_input(request, new_tokens_ref=None):
    result = copy.deepcopy(request)
    _require(result['gain44_new_combination'] is True, 'Only new44 combination may be materialized')
    if result['tokens'] is None:
        result['tokens'] = _reference(new_tokens_ref)
    else:
        _require(new_tokens_ref is None or new_tokens_ref == result['tokens'], 'Unchanged-grid original tokens must be adopted')
    return result


def finalize_prepared(plan, new_input_refs, *, CPU_targets_ref, adapter_weights, bindings):
    """Attach exclusive writer refs; does not generate a successful QA gate."""
    missing = {case['id'] for case in plan['cases'] if not case['adopted_input']}
    _require(set(new_input_refs) == missing and len(missing) == 408, 'Exactly408 first-new request refs required')
    required = {'old_prepared', 'old_catalog', 'old_case_plan', 'old_input_gate', 'source_catalog'}
    _require(set(bindings) == required, 'Exact original/new catalog bindings required')
    bound_refs = {key:_reference(value) for key, value in bindings.items()}
    entries = [dict(id=case['id'], source_id=case['source_id'], source_sha256=case['source_sha256'], input=_reference(case['input'] if case['adopted_input']
        else new_input_refs[case['id']])) for case in plan['cases']]
    _require(len({_refkey(entry['input']) for entry in entries}) == 2408, 'Every ordered input needs a distinct immutable request ref')
    lookup = {entry['id']:entry for entry in entries}
    return dict(status='PREPARED_NOT_GPU_ADMISSION', train_inputs=entries,
        pilot_inputs=[lookup[cid] for cid in plan['pilot_case_ids']],
        remaining_inputs=[lookup[cid] for cid in plan['remaining_case_ids']],
        pair_index=copy.deepcopy(plan['pair_index']), class_token_ids=_classes(plan['class_token_ids']),
        pilot_source_ids=copy.deepcopy(plan['pilot_source_ids']),
        source_catalog=bound_refs.pop('source_catalog'), original_bindings=bound_refs,
        CPU_targets=_reference(CPU_targets_ref), adapter_weights=_reference(adapter_weights),
        sources=602, adopted_inputs=2000, first_new_combinations=408, new_image_processor_calls=0,
        new_original_decodes=0, labels_in_inputs=False, GPU_admitted=False, old_native_quality='STOP')


class GainInputs:
    """Bound-callback2408 whitelist. Never opens CPUtargets or schedule labels."""
    def __init__(self, prepared, *, gate, prepared_ref, registration_ref, load_json, load_tensor, image):
        _require(gate['status'] == GATE and gate['prepared'] == _reference(prepared_ref)
            and gate['registration'] == _reference(registration_ref)
            and gate['adopted_inputs'] == 2000 and gate['first_new_combinations'] == 408
            and gate['new_image_processor_calls'] == gate['new_original_decodes'] == 0,
            'Actual new-purpose44 first combination QA gate required')
        entries = prepared['train_inputs']
        _require(len(entries) == 2408 and len(prepared['pilot_inputs']) == 128 and len(prepared['remaining_inputs']) == 2280,
                 'Exact complete2408/pilot128/remaining2280 manifest required')
        self.allowed = {_refkey(entry['input']):entry for entry in entries}
        _require(len(self.allowed) == 2408, 'Duplicate request refs in gain reader whitelist')
        by_id = {entry['id']:entry for entry in entries}
        pilot = prepared['pilot_inputs']; remaining = prepared['remaining_inputs']
        pilot_ids, remaining_ids = {entry['id'] for entry in pilot}, {entry['id'] for entry in remaining}
        _require(len(by_id) == 2408 and len(pilot_ids) == 128 and len(remaining_ids) == 2280
            and not pilot_ids & remaining_ids and pilot_ids | remaining_ids == set(by_id)
            and all(by_id.get(entry['id']) == entry for entry in pilot+remaining),
            'Pilot128 and remaining2280 must partition the same exact2408 inputs')
        self.prepared, self.load_json, self.load_tensor, self.image = prepared, load_json, load_tensor, image
        _classes(prepared['class_token_ids'])
        self.current_source, self.cache = None, {}

    def get(self, reference):
        key = _refkey(reference)
        _require(key in self.allowed, 'Only the2408 registered final500 train readout inputs are allowed')
        entry, request = self.allowed[key], self.load_json(reference)
        _require(request['id'] == entry['id'] and request['source_id'] == entry['source_id']
            and request['source_sha256'] == entry['source_sha256']
            and request['role'] == 'train' and request['reference_or_target_in_prompt'] is False
            and not any(name in request for name in ('target', 'labels', 'candidate_ious', 'original_reference_xywh')),
            'Only label-free original train-source requests may be read')
        if self.current_source != request['source_id']:
            self.cache.clear(); self.current_source = request['source_id']
        _require(len(request['vision_inputs']) == 3, 'Three accepted Source/A/B inputs required')
        views = []
        for item in request['vision_inputs']:
            cache_key = _refkey(item)
            if cache_key not in self.cache:
                raw = self.load_tensor(item)
                self.cache[cache_key] = {key:raw[key] for key in ('pixel_values', 'image_grid_thw')}
            views.append(self.cache[cache_key])
        grid = torch.cat([view['image_grid_thw'] for view in views])
        packed = self.image.pack_image_pixels([view['pixel_values'] for view in views], grid)
        tokens = self.load_tensor(request['tokens'])
        _require(set(tokens) == {'input_ids', 'attention_mask'}, 'Prefix-only actual accepted tokens required')
        values = dict(**tokens, **packed)
        _require(set(values) == FOUR_KEYS and signature(values) == request['input_signature']
            and grid.tolist() == request['image_grid_thw']
            and _classes(request['class_token_ids']) == _classes(self.prepared['class_token_ids']),
            'Actual gain readout four-tensor/class/grid signature differs')
        return values, request
