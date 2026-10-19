"""Conditional readonly final55 UTILITY inference; no actions on import.

CLI --root ROOT --scope resized20|resized19|production --registration ABS_JSON.
schema='UTILITY_FROZEN_PROFILE_INFERENCE_V59'; role='UTILITY_'+scope;
output_directory must be ROOT/utility_inference_59/scope. Explicit refs:
GPU_code, reader_code, image_code, CPU_registration, input_acceptance, prepared,
frozen_GPU55_code, frozen_GPU55_registration, training_completion, model_config,
adapter_weights, adapter_config, value_weights, old_TIME, old_PAIR, old_CROP,
training_quality_admission. Other fields: reader_class, expected_inputs,
expected_sources, GPU_job, deadline_utc, max_seconds, profile,
adopted_output_acceptances(list refs). resized19 additionally requires
profile_quality_admission; production also requires production_admission and
confirm_quality_admission, input_acceptance_status, official_source_count426,
affected_video_count<=303. Production expected_sources counts exact observed
frame owners, not the protected426 official video records. No target artifact
in any GPU input whitelist.

Reader constructor matches ProfileInputs58: prepared + gate/prepared_ref/
registration_ref/load_json/load_tensor/load_bytes/image keyword callbacks.
Future production reader must implement this same explicit contract. Already
first-QAd exact weights/source/class/F4 inputs adopt their persisted raw; no
old raw tensor is loaded or subjected to another first QA here.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import time
import traceback

_support = Path(__file__).resolve().parents[1]/'pair_code_17'
if _support.is_dir():
    sys.path.insert(0, str(_support))
from pair_common import WORK, read, save, sha, ref, bound, require, utc, signature, paths, append_event

SCHEMA = 'UTILITY_FROZEN_PROFILE_INFERENCE_V59'
SCOPES = ('resized20', 'resized19', 'production')
OUTPUT_QA_GATE = 'PASS_UTILITY59_FIRST_OUTPUT_QA'
CPU_GATE = 'PASS_UTILITY58_NEW_PROFILE_INPUTS_FIRST_CPU_QA'
GPU_REFS = ('GPU_code', 'reader_code', 'image_code', 'CPU_registration', 'input_acceptance', 'prepared',
    'frozen_GPU55_code', 'frozen_GPU55_registration', 'training_completion', 'model_config',
    'adapter_weights', 'adapter_config', 'value_weights', 'old_TIME', 'old_PAIR', 'old_CROP')
INPUT_KEYS = {'input_ids', 'attention_mask', 'pixel_values', 'image_grid_thw'}


def module(reference, name):
    path = bound(reference)
    require(name not in sys.modules, 'Bound runtime helper already imported under another identity')
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec); sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def _number(value):
    require(isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value), 'Known finite GPU value required')
    return float(value)


def exact_key(request, adapter, values):
    """Model-role intentionally excluded only for explicit external adoption."""
    require(set(request['input_signature']) == INPUT_KEYS, 'Exact four-tensor input signature required')
    return json.dumps(dict(source_id=request['source_id'], source_sha256=request['source_sha256'],
        class_token_ids=request['class_token_ids'], input_signature=request['input_signature'],
        adapter_weights=adapter, value_weights=values), sort_keys=True, separators=(',', ':'), allow_nan=False)


def validate_admission(reg, scope, training, native_quality, profile_quality=None, confirm_quality=None, production=None):
    require(reg['schema'] == SCHEMA and scope in SCOPES and reg['scope'] == scope
        and reg['model_role'] == 'UTILITY_'+scope and type(reg['expected_inputs']) is int and reg['expected_inputs'] > 0,
        'Explicit one-scope nonempty readonly utility registration required')
    require(training['status'] == 'COMPLETE_FIXED_FINAL500_UTILITY_VALUES_NOT_QUALITY'
        and training['completed_updates'] == 500 and training['successful_micro'] == 2000
        and training['actual_training_forwards'] == 4000
        and all(training[k] is True for k in ('adapter_reload_all288_exact', 'head_reload_exact', 'beta_reload_exact'))
        and training['adapter_weights'] == reg['adapter_weights'] and training['value_weights'] == reg['value_weights']
        and training['GPU_registration'] == reg['frozen_GPU55_registration'], 'Actual immutable complete final55 model required')
    require(native_quality['status'] == 'PASS_UTILITY_SCREEN20_ONLY'
        and native_quality['evaluation']['quality']['admitted'] is True
        and native_quality['confirm_admitted'] is True and native_quality['fixed_final_checkpoint'] is True
        and native_quality['adapter_weights'] == reg['adapter_weights'] and native_quality['value_weights'] == reg['value_weights']
        and native_quality['training_completion'] == reg['training_completion'], 'Actual new native utility screen qualification required')
    if scope in ('resized19', 'production'):
        require(profile_quality is not None and profile_quality['status'] == 'PASS_UTILITY_RESIZED20_PROFILE_ONLY'
            and profile_quality['quality']['admitted'] is True
            and profile_quality['adapter_weights'] == reg['adapter_weights'] and profile_quality['value_weights'] == reg['value_weights'],
            'Actual fixed-model resized20 qualification required')
    if scope == 'production':
        require(confirm_quality is not None and confirm_quality['status'] == 'PASS_UTILITY_RESIZED19_CONFIRM_ONLY'
            and confirm_quality['quality']['admitted'] is True
            and confirm_quality['adapter_weights'] == reg['adapter_weights'] and confirm_quality['value_weights'] == reg['value_weights'],
            'Actual resized19 qualification required')
        require(production is not None and production['status'] == 'ADMIT_UTILITY_EXACT_NATIVE_PTS_SPATIAL_ONLY'
            and production['production_admitted'] is True
            and production['confirm_quality_admission'] == reg['confirm_quality_admission']
            and production['adapter_weights'] == reg['adapter_weights'] and production['value_weights'] == reg['value_weights']
            and production['expected_sources'] == production['observations'] == reg['expected_sources']
            and production['official_source_count'] == reg['official_source_count'] == 426
            and production['affected_video_count'] == reg['affected_video_count']
            and production['whole426_preserved'] is True,
            'Explicit exact-native-PTS spatial-only production admission required')
    require(reg['profile'] == 'RESIZED_OBSERVATION_PLANE'
        and type(reg['expected_sources']) is int and reg['expected_sources'] > 0,
        'Explicit resized observation plane/source scope; never claim native RGB recovery')
    if scope == 'production':
        require(type(reg['affected_video_count']) is int and 0 < reg['affected_video_count'] <= min(303, reg['expected_sources']),
                'Production inference counts exact observation owners within declared native16 videos')
    else:
        require(reg['expected_sources'] == {'resized20':20, 'resized19':19}[scope], 'Fixed external profile source count required')


def validate_prepared(reg, gate, prepared):
    expected_gate = CPU_GATE if reg['scope'] != 'production' else reg['input_acceptance_status']
    require(isinstance(expected_gate, str) and expected_gate.startswith('PASS_')
        and gate['status'] == expected_gate and gate['registration'] == reg['CPU_registration']
        and gate['prepared'] == reg['prepared'] and prepared['scope'] == reg['scope']
        and prepared['profile'] == reg['profile'] and prepared['adapter_weights'] == reg['adapter_weights']
        and prepared['value_weights'] == reg['value_weights'] and prepared['sources'] == reg['expected_sources']
        and gate['scope'] == reg['scope'] and gate['sources'] == reg['expected_sources']
        and gate['first_independent_crop_processor_QA'] is True
        and gate['first_compressed_save_and_reader_roundtrip'] is True
        and prepared['native_RGB_recovered'] is False and gate['native_RGB_recovered'] is False,
        'Exact first-QAd new profile inputs and fixed weights required')
    entries = prepared['inference_inputs']; new = prepared['execution_entries']; adopted = prepared['adopted_success']
    ids = {e['id'] for e in entries}; new_ids = {e['id'] for e in new}
    require(len(ids) == len(entries) == reg['expected_inputs'] and len(new_ids) == len(new)
        and isinstance(adopted, dict) and not new_ids.intersection(adopted) and new_ids | set(adopted) == ids,
        'Execution/adopted plans must exactly partition unique complete inference inputs')
    require(gate['inference_inputs'] == len(entries) and gate['execution_inputs'] == len(new)
        and gate['adopted_successes'] == len(adopted), 'Accepted actual new/adopted input counts differ')
    by_id = {e['id']:e for e in entries}
    require(all(by_id[e['id']] == e for e in new), 'New execution entries must be unchanged accepted entries')
    if reg['scope'] == 'production':
        require(prepared['official_source_count'] == gate['official_source_count'] == reg['official_source_count'] == 426
            and prepared['affected_video_count'] == gate['affected_video_count'] == reg['affected_video_count']
            and len({e['source_id'] for e in entries}) == reg['expected_sources'],
            'Exact observed frame-owner count and protected whole426 inventory required')
    if reg['scope'] == 'resized19':
        require(prepared['original20_complete'] is False and all(e['source_id'] != 'gnmc:test:006575.jpeg' for e in entries),
                'Only original remaining19, permanently excluding lost first source')
    return entries


def adopted_index(acceptance_refs, adapter, values, training_ref):
    """Adopt old QA, bind artifact SHAs, never tensor-load/repeat old raw QA."""
    require(isinstance(acceptance_refs, list) and bool(acceptance_refs), 'Explicit prior successful output QA refs required')
    index, checked_raw = {}, set()
    for acceptance_ref in acceptance_refs:
        accepted = read(bound(acceptance_ref))
        require(accepted['status'] in ('PASS_UTILITY_FINAL500_SCREEN_FIRST_RAW_QA', OUTPUT_QA_GATE)
            and accepted['adapter_weights'] == adapter and accepted['value_weights'] == values
            and accepted['training_completion'] == training_ref, 'Adopt only already first-QAd exact final55 outputs')
        require(isinstance(accepted['predictions'], list), 'Explicit accepted prediction inventory required')
        for prediction in accepted['predictions']:
            request = read(bound(prediction['input'])); receipt = read(bound(prediction['receipt']))
            require(request['id'] == receipt['id'] == prediction['id']
                and request['source_id'] == receipt['source_id'] == prediction['source_id']
                and request['source_sha256'] == receipt['source_sha256'] == prediction['source_sha256']
                and receipt['input'] == prediction['input'] and receipt['input_signature'] == request['input_signature']
                and receipt['class_token_ids'] == request['class_token_ids']
                and receipt['adapter_weights'] == adapter and receipt['value_weights'] == values
                and prediction['raw_hidden'] == receipt['raw_hidden']
                and receipt['model_role'] in ('UTILITY_TRAINED_screen', *('UTILITY_'+s for s in SCOPES)),
                'Accepted old metadata/raw ownership differs')
            key = exact_key(request, adapter, values)
            raw_key = json.dumps(receipt['raw_hidden'], sort_keys=True)
            if raw_key not in checked_raw:
                bound(receipt['raw_hidden'])  # File integrity adoption, not another first raw QA.
                checked_raw.add(raw_key)
            candidate = dict(input=prediction['input'], receipt=prediction['receipt'], raw_hidden=receipt['raw_hidden'],
                acceptance=acceptance_ref, model_role=receipt['model_role'], adapter_weights=adapter, value_weights=values,
                GPU_value=_number(receipt['head_value']), source_id=request['source_id'], source_sha256=request['source_sha256'])
            if 'CPU_value' in prediction:
                candidate['CPU_value'] = _number(prediction['CPU_value'])
            if key in index:
                require(index[key]['raw_hidden'] == candidate['raw_hidden'] and index[key]['GPU_value'] == candidate['GPU_value'],
                        'Conflicting already accepted same-input raw/value cannot be silently selected')
            index.setdefault(key, candidate)  # Fixed explicit acceptance order; no quality choice.
    return index


def validate_adopted_plan(prepared, index, adapter, values):
    """Prove each compiler-declared reuse belongs to the registered old QA set."""
    entries = {e['id']:e for e in prepared['inference_inputs']}
    for identifier, planned in prepared['adopted_success'].items():
        request = read(bound(entries[identifier]['input'])); actual = index[exact_key(request, adapter, values)]
        require(all(planned[k] == actual[k] for k in ('input', 'receipt', 'raw_hidden', 'acceptance', 'model_role',
            'adapter_weights', 'value_weights', 'GPU_value')), 'Compiler declared adoption differs from exact old first QA')
        if 'CPU_value' in planned:
            require('CPU_value' in actual and planned['CPU_value'] == actual['CPU_value'], 'Adopted CPU replay evidence differs')


def ordered_stage(out, inputs, entries, reg, *, observe, write_tensor, external, successful_raw, check_deadline=None):
    """observe(values)->(CPU raw, deferred GPU-value callable).

    Deferring value evaluation guarantees returned hidden is fsynced BEFORE
    value-head execution or output checks can fail. Tests use synthetic callbacks.
    """
    import torch
    require(len(entries) == reg['expected_inputs'] and len({e['id'] for e in entries}) == len(entries),
            'Exact registered unique ordered input count required before any forward')
    out = Path(out); stage = out/'ordered'; stage.mkdir(exist_ok=False)
    journal = stage/'attempts.jsonl'; journal.touch(exist_ok=False)
    role = reg['model_role']; adapter = reg['adapter_weights']; values_ref = reg['value_weights']
    aliases, completed = {}, []
    new_count = external_count = internal_count = 0
    for i, entry in enumerate(entries):
        if check_deadline is not None:
            check_deadline()
        # ProfileInputs58 deliberately exposes only genuinely new execution
        # refs. Already-QAd external or same-scope aliases need metadata only.
        request = read(bound(entry['input']))
        require(request['id'] == entry['id'] and request['source_id'] == entry['source_id']
            and request['source_sha256'] == entry['source_sha256']
            and request['class_token_ids'] == inputs.prepared['class_token_ids']
            and request['adapter_weights'] == adapter and request['value_weights'] == values_ref
            and request['scope'] == reg['scope'] and request['profile'] == reg['profile']
            and request['native_RGB_recovered'] is False and request['reference_or_target_in_prompt'] is False,
            'Accepted scope/owner/class/four-input metadata differs')
        require(not any(k in request for k in ('target', 'labels', 'candidate_ious', 'original_reference_xywh')),
                'GPU input requests cannot carry human target fields')
        grid = torch.tensor(request['image_grid_thw'], dtype=torch.int64)
        require(tuple(grid.shape) == (3, 3)
            and bool((grid > 0).all()) and bool((grid[:, 0] == 1).all()) and bool((grid[:, 1:] % 2 == 0).all())
            and signature({'image_grid_thw':grid})['image_grid_thw'] == request['input_signature']['image_grid_thw'],
            'Accepted three static image grid metadata/signature differs')
        key = exact_key(request, adapter, values_ref); prior = aliases.get(key); adopted = external.get(key)
        started = time.monotonic()
        is_external = adopted is not None
        is_internal = adopted is None and prior is not None
        if is_external:
            raw_reference = adopted['raw_hidden']; value = adopted['GPU_value']; alias_of = adopted['receipt']
            external_count += 1
            append_event(journal, event='ADOPTED_PREVIOUSLY_QA_RAW', id=entry['id'], model_role=role,
                raw_hidden=raw_reference, adopted_from_acceptance=adopted['acceptance'], adopted_receipt=alias_of)
        elif is_internal:
            raw_reference, value, alias_of = prior['raw_hidden'], prior['head_value'], prior['receipt']
            internal_count += 1
        else:
            values, consumed = inputs.get(entry['input'])
            require(consumed == request and set(values) == INPUT_KEYS and signature(values) == request['input_signature']
                and all(isinstance(v, torch.Tensor) and v.device.type == 'cpu' for v in values.values())
                and values['image_grid_thw'].dtype == torch.int64,
                'Actual newly consumed first-QAd four-input signature differs')
            append_event(journal, event='BEGIN_NEW_ROLE_FORWARD', id=entry['id'], input=entry['input'], model_role=role)
            raw, finish_value = observe(values)
            raw_path = stage/('%06d.hidden.pt'%i); write_tensor(raw_path, raw)
            raw_reference = ref(raw_path)
            successful_raw.append(dict(id=entry['id'], source_id=request['source_id'], source_sha256=request['source_sha256'],
                model_role=role, raw_hidden=raw_reference))
            append_event(journal, event='FIRST_RAW_PERSISTED', id=entry['id'], raw_hidden=raw_reference, model_role=role)
            require(isinstance(raw, torch.Tensor) and raw.device.type == 'cpu' and raw.dtype == torch.float32
                and tuple(raw.shape) == (4096,) and bool(torch.isfinite(raw).all()), 'Persisted finite normalized hidden4096 required')
            value = _number(finish_value()); alias_of = None; new_count += 1
            del raw, finish_value
        receipt_path = stage/('%06d.receipt.json'%i)
        receipt = dict(id=entry['id'], source_id=request['source_id'], source_sha256=request['source_sha256'],
            input=entry['input'], model_role=role, scope=reg['scope'], profile=reg['profile'], native_RGB_recovered=False,
            raw_hidden=raw_reference, head_value=_number(value), raw_dtype='torch.float32', dimension=4096,
            adapter_weights=adapter, value_weights=values_ref, input_signature=request['input_signature'],
            image_grid_thw=request['image_grid_thw'], class_token_ids=request['class_token_ids'],
            actual_new_forward=not is_external and not is_internal, external_alias=is_external, internal_alias=is_internal,
            alias_of=alias_of, adopted_from_acceptance=adopted['acceptance'] if is_external else None,
            adopted_model_role=adopted['model_role'] if is_external else None,
            adopted_input=adopted['input'] if is_external else None,
            elapsed_seconds=time.monotonic()-started, screen_reference_read=False, no_full_vocabulary_logits=True,
            original_TIME_loaded=False, old_PAIR_loaded=False, old_CROP_loaded=False)
        save(receipt_path, receipt); receipt_reference = ref(receipt_path)
        aliases.setdefault(key, dict(raw_hidden=raw_reference, head_value=value, receipt=receipt_reference))
        completed.append(dict(id=entry['id'], source_id=request['source_id'], source_sha256=request['source_sha256'],
            input=entry['input'], receipt=receipt_reference))
        append_event(journal, event='ACCEPTED_NEW_ROLE_RESULT', id=entry['id'], receipt=receipt_reference,
            alias=is_external or is_internal, external_alias=is_external, internal_alias=is_internal, model_role=role)
    require(new_count+external_count+internal_count == len(entries) == reg['expected_inputs'], 'Actual new/external/internal counts differ')
    completion = stage/'completion.json'
    save(completion, dict(status='COMPLETE_UTILITY_ORDERED_HIDDEN_VALUES_NOT_QUALITY', model_role=role,
        scope=reg['scope'], profile=reg['profile'], entries=completed, actual_forward_calls=new_count,
        external_aliases=external_count, aliases=internal_count, expected_inputs=len(entries), attempts=ref(journal),
        GPU_registration=reg['_registration_ref'], adapter_weights=adapter, value_weights=values_ref,
        screen_reference_read=False, original_TIME_loaded=False, old_PAIR_loaded=False, old_CROP_loaded=False,
        no_training=True, no_old_first_QA_repeated=True))
    return ref(completion)


def run(root, scope, registration_path):
    require(bool(os.environ.get('CUDA_VISIBLE_DEVICES')), 'Shared-wrapper GPU assignment required')
    root = Path(root).resolve(); registration_path = Path(registration_path)
    require(root.is_relative_to(WORK) and registration_path.is_absolute()
        and registration_path.resolve().is_relative_to(root), 'Explicit registration and output root must stay inside their authorized work root')
    reg = read(registration_path)
    for key in GPU_REFS:
        bound(reg[key])  # Explicit whitelist; never bind/open target refs.
    require(bound(reg['GPU_code']) == Path(__file__).resolve(), 'Exact new readonly59 entry required')
    training = read(bound(reg['training_completion']))
    native_quality = read(bound(reg['training_quality_admission']))
    profile_quality = read(bound(reg['profile_quality_admission'])) if scope in ('resized19', 'production') else None
    confirm_quality = read(bound(reg['confirm_quality_admission'])) if scope == 'production' else None
    production = read(bound(reg['production_admission'])) if scope == 'production' else None
    validate_admission(reg, scope, training, native_quality, profile_quality, confirm_quality, production)
    output = root/'utility_inference_59'/scope
    require(Path(reg['output_directory']).resolve() == output.resolve(), 'Exact exclusive new scope output namespace required')
    original = read(bound(reg['frozen_GPU55_registration']))
    require(original['GPU_code'] == reg['frozen_GPU55_code'] and original['model_config'] == reg['model_config']
        and all(original[k] == reg[k] for k in ('old_TIME', 'old_PAIR', 'old_CROP')), 'Frozen55 physical/runtime identities differ')
    gate = read(bound(reg['input_acceptance'])); prepared = read(bound(reg['prepared']))
    cpu = read(bound(reg['CPU_registration']))
    require(cpu['preparation_code'] == reg['reader_code'] and cpu['input_code'] == reg['image_code']
        and cpu['scope'] == scope, 'Reader/image implementation must match actual first CPU QA registration')
    entries = validate_prepared(reg, gate, prepared)
    external = adopted_index(reg['adopted_output_acceptances'], reg['adapter_weights'], reg['value_weights'], reg['training_completion'])
    validate_adopted_plan(prepared, external, reg['adapter_weights'], reg['value_weights'])
    reader = module(reg['reader_code'], '_utility59_explicit_reader')
    image = module(reg['image_code'], '_utility59_explicit_image')
    paths()
    import torch
    from peft import PeftModel
    from safetensors.torch import load_file
    from transformers import Qwen3VLForConditionalGeneration
    from sft_contract import REVISION, verify_live_gpu_reservation
    from verify_saved_smoke import canonical_frozen_hash
    verify_live_gpu_reservation()
    require(read(WORK/'improvement_round1/active_gpu_job.json')['name'] == reg['GPU_job'], 'Wrong actual shared GPU reservation')
    old18 = read(bound(original['original_GPU18']))
    for reference in old18['runtime_dependencies']:
        bound(reference)
    helper = module(reg['frozen_GPU55_code'], '_utility59_frozen55')
    require(bound(original['math_code']) == Path(helper.utility.__file__).resolve(), 'Actual frozen55 math import differs')
    old17 = read(bound(old18['pair_registration']))
    for name, digest in old17['new_code'].items():
        require(sha(root/'pair_code_17'/name) == digest, 'Frozen17 runtime changed: '+name)
    old32 = read(bound(original['original_GPU32'])); frozen = module(old32['GPU_code'], '_utility59_frozen32')
    frozen._deadline(reg)
    inputs = getattr(reader, reg['reader_class'])(prepared, gate=gate, prepared_ref=reg['prepared'],
        registration_ref=reg['CPU_registration'], load_json=lambda r:read(bound(r)),
        load_tensor=lambda r:torch.load(bound(r), map_location='cpu', weights_only=True),
        load_bytes=lambda r:bound(r).read_bytes(), image=image)
    require(inputs.prepared == prepared, 'Exact accepted explicit input reader required')
    output.parent.mkdir(exist_ok=True); output.mkdir(exist_ok=False)
    registration_ref = ref(registration_path); reg = dict(reg, _registration_ref=registration_ref)
    save(output/'claim.json', dict(utc=utc(), GPU_registration=registration_ref, scope=scope,
        input_acceptance=reg['input_acceptance'], training_completion=reg['training_completion'],
        adapter_weights=reg['adapter_weights'], value_weights=reg['value_weights'], no_training=True,
        targets_read=False, no_automatic_followup=True, profile=reg['profile'], native_RGB_recovered=False))
    successful_raw = []
    try:
        cfg = read(bound(reg['model_config']))
        base = Qwen3VLForConditionalGeneration.from_pretrained(cfg['model_dir'], revision=REVISION,
            local_files_only=True, torch_dtype=torch.bfloat16, device_map={'':'cuda:0'},
            low_cpu_mem_usage=True, attn_implementation='sdpa')
        base.eval(); base.config.use_cache = False
        for p in base.parameters():
            p.requires_grad_(False)
        require(not any('lora_' in n for n, _ in base.named_parameters()), 'Readonly role must start from bare BASE')
        before = canonical_frozen_hash(base, torch)
        require(before['parameters'] == helper.BASE and before['sha256'] == cfg['expected_base_sha256'], 'Actual original BASE differs')
        weights = bound(reg['adapter_weights']); value_path = bound(reg['value_weights'])
        require(Path(reg['adapter_directory']).resolve() == weights.parent
            and bound(reg['adapter_config']).parent == weights.parent
            and Path(training['adapter_directory']).resolve() == weights.parent, 'Exact final500 adapter manifest required')
        expected_adapter = load_file(str(weights), device='cpu')
        value_state = torch.load(value_path, map_location='cpu', weights_only=True)
        require(set(value_state) == {'weight', 'geometry_beta'} and tuple(value_state['weight'].shape) == (1, 4096)
            and tuple(value_state['geometry_beta'].shape) == (11,)
            and all(v.device.type == 'cpu' and v.dtype == torch.float32 and bool(torch.isfinite(v).all()) for v in value_state.values()),
            'Complete finite frozen value4096/geometry11 artifacts required')
        model = PeftModel.from_pretrained(base, str(weights.parent), adapter_name='utility', is_trainable=False).eval()
        for p in model.parameters():
            p.requires_grad_(False)
        head = torch.nn.Linear(4096, 1, bias=False, device='cuda:0', dtype=torch.float32)
        head.load_state_dict(dict(weight=value_state['weight'])); head.requires_grad_(False); head.eval()
        beta = torch.nn.Parameter(value_state['geometry_beta'].to('cuda:0'), requires_grad=False)
        _, inventory = helper._inventory(model, head, beta, False, torch)
        expected = dict(adapter_state_dict=expected_adapter, head_state_dict=dict(weight=value_state['weight']),
            geometry_beta=value_state['geometry_beta'])
        require(helper._tree_equal(helper._trainables(model, head, beta, torch, frozen), expected, torch),
                'Actual final500 utility/value reload differs')
        save(output/'model_identity.json', dict(base_fingerprint=before, inventory=inventory,
            training_completion=reg['training_completion'], adapter_weights=reg['adapter_weights'], value_weights=reg['value_weights'],
            original_TIME_loaded=False, old_PAIR_loaded=False, old_CROP_loaded=False))

        def observe(values):
            frozen._deadline(reg)
            gpu = {k:v.to('cuda:0') for k, v in values.items()}
            with torch.inference_mode():
                # Same final language norm output as frozen55._hidden; defer
                # all returned-value checks until first raw persistence.
                result = model.get_base_model().model(**gpu, use_cache=False, return_dict=True)
                hidden = result.last_hidden_state[0, -1, :]
                raw = hidden.float().detach().cpu().contiguous()
            def finish():
                with torch.inference_mode():
                    value = float(head(hidden.float()).reshape(()).cpu())
                torch.cuda.synchronize()
                return value
            return raw, finish

        complete = ordered_stage(output, inputs, entries, reg, observe=observe,
            write_tensor=lambda path, tensor:frozen._tensor_file(path, tensor, torch), external=external, successful_raw=successful_raw,
            check_deadline=lambda:frozen._deadline(reg))
        helper._inventory(model, head, beta, False, torch)
        require(canonical_frozen_hash(model, torch) == before
            and helper._tree_equal(helper._trainables(model, head, beta, torch, frozen), expected, torch),
            'Readonly scope changed actual BASE/adapter/value/beta bytes')
        for key in ('old_TIME', 'old_PAIR', 'old_CROP', 'adapter_weights', 'value_weights'):
            bound(reg[key])
        frozen._deadline(reg)
        save(output/'completion.json', dict(status='COMPLETE_UTILITY_V59_READONLY_SCOPE_NOT_QUALITY', scope=scope,
            model_role=reg['model_role'], GPU_registration=registration_ref, completion=complete,
            input_acceptance=reg['input_acceptance'], prepared=reg['prepared'], training_completion=reg['training_completion'],
            adapter_weights=reg['adapter_weights'], value_weights=reg['value_weights'], base_fingerprint=before,
            inventory=inventory, profile=reg['profile'], native_RGB_recovered=False, new_optimizer_updates=0,
            labels_read=False, no_old_first_QA_repeated=True, automatic_confirm=False, automatic_production=False))
    except BaseException as error:
        save(output/'failure.json', dict(utc=utc(), error=repr(error), traceback=traceback.format_exc(),
            successful_raw=successful_raw, preserve_all_success=True, automatic_retry=False, failure_is_not_empty=True))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--scope', choices=SCOPES, required=True)
    parser.add_argument('--registration', type=Path, required=True)
    args = parser.parse_args(); run(args.root, args.scope, args.registration)
