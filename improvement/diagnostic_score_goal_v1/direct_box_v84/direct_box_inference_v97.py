"""Conditionally registered readonly single-source direct-box inference.

No training, target reads, old-stage execution or automatic next phase. Only
the exact final798NEW adapter/head is loaded. Each first hidden/head raw is
persisted before postchecks; prior successful exact inputs adopt their QA.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import traceback

_here = Path(__file__).resolve()
for _support in (_here.parents[1]/'pair_code_17', _here.parents[1], _here.parents[2]/'pair_code_17'):
    if (_support/'pair_common.py').is_file():
        sys.path.insert(0, str(_support)); break
from pair_common import WORK, read, save, ref, bound, require, utc, paths, append_event

SCHEMA = 'FROZEN_DIRECT_BOX97_L2_SINGLE_IMAGE_INFERENCE'
PHASES = ('confirm19', 'formal')
ARMS = {'DIRECT', 'ANCHORED_HALF'}
STATUSES = dict(confirm19='COMPLETE_DIRECT_BOX97_CONFIRM19_RAW_NOT_QUALITY', formal='COMPLETE_DIRECT_BOX97_FORMAL_RAW_NOT_QUALITY')
ADOPTABLE = {'PASS_DIRECT_BOX93_SCREEN_FIRST_RAW_HEAD_NATIVE_CPU_QA',
    'PASS_DIRECT_BOX96_CONFIRM19_FIRST_RAW_HEAD_CPU_QA', 'PASS_DIRECT_BOX96_FORMAL_FIRST_RAW_HEAD_PTS_CPU_QA'}
GPU_REFS = ('GPU_code', 'frozen_GPU93_code', 'frozen_GPU93_registration', 'frozen_math84_code', 'training_completion', 'adapter_weights', 'head_weights',
    'adapter_config', 'model_config', 'math_code', 'preparation_code', 'CPU_registration', 'prepared', 'input_acceptance',
    'old_TIME', 'old_PAIR', 'old_CROP', 'native20_quality_result')


def module(reference, name):
    path = bound(reference); require(name not in sys.modules, 'One pinned97 helper identity')
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec); sys.modules[name] = result; spec.loader.exec_module(result)
    return result


def identity(row):
    return json.dumps({k:row[k] for k in ('source_id', 'source_sha256', 'width', 'height', 'input_signature',
        'adapter_weights', 'head_weights')}, sort_keys=True, separators=(',', ':'), allow_nan=False)


def quality_arms(summary, status, reg, result_key):
    names = summary['admitted_arm_names']
    require(summary['status'] == status and isinstance(names, list) and names and len(names) == len(set(names))
        and set(names) <= ARMS and all(summary[k] == reg[k] for k in ('training_completion', 'adapter_weights', 'head_weights'))
        and summary['result'] == reg[result_key],
        'Frozen actual quality summary and final798NEW identities required')
    return set(names)


def validate_admission(root, phase, registration_path, reg):
    root = Path(root).resolve()
    require(phase in PHASES and Path(registration_path).resolve() == root/('direct_box_inference_registration_97_'+phase+'.json')
        and reg['schema'] == SCHEMA and reg['phase'] == phase and reg['inference_admitted'] is True, 'Explicit admitted97 phase')
    require(bound(reg['GPU_code']) == Path(__file__).resolve(), 'Exact registered97 code')
    for key in GPU_REFS:
        bound(reg[key])  # Rich quality result is SHA-bound only, never parsed by GPU.
    require(all(bound(reg[k]).is_relative_to(root) for k in ('CPU_registration', 'prepared', 'input_acceptance')),
        'New registered CPU inputs stay inside this root')
    require(Path(reg['output_directory']).resolve() == root/'direct_box_inference_97'/phase, 'Exact fresh output namespace; no path escape')
    require(type(reg['expected_inputs']) is int and reg['expected_inputs'] > 0
        and type(reg['expected_sources']) is int and reg['expected_sources'] == reg['expected_inputs'], 'One actual input per observation owner')
    native = quality_arms(reg['native20_quality_summary'], 'PASS_DIRECT_BOX93_NATIVE20_QUALIFIED_ARMS', reg, 'native20_quality_result')
    if phase == 'confirm19':
        require(reg['expected_inputs'] == 19, 'Only fixed successful19, missing original first source excluded')
        allowed = native
    else:
        bound(reg['confirm19_quality_result'])
        confirm = quality_arms(reg['confirm19_quality_summary'], 'PASS_DIRECT_BOX95_CONFIRM19_QUALIFIED_ARMS', reg, 'confirm19_quality_result')
        allowed = native & confirm
        require(allowed and reg['production_admitted'] is True and reg['official_source_count'] == 426
            and type(reg['affected_video_count']) is int and 0 < reg['affected_video_count'] <= 426
            and type(reg['expected_affected_videos']) is int
            and reg['expected_affected_videos'] == reg['affected_video_count'] == len(set(reg['affected_video_ids']))
            and reg['whole426_preserved'] is True and reg['time_selection_unchanged'] is True
            and reg['selection'] == 'OBS_INDEX_EVEN', 'Exact native-observation spatial-only formal admission')
    require(isinstance(reg['admitted_arm_names'], list) and len(set(reg['admitted_arm_names'])) == len(reg['admitted_arm_names'])
        and set(reg['admitted_arm_names']) == allowed, 'Same qualified arm intersection; no posthoc arm switch')


def validate_inputs(reg, prepared, gate):
    require(prepared['schema'] == reg['prepared_schema'] and prepared['phase'] == gate['phase'] == reg['phase']
        and gate['status'] == reg['input_acceptance_status'] and gate['prepared'] == reg['prepared']
        and gate['registration'] == reg['CPU_registration'], 'Actual complete registered CPU gate/schema')
    entries = prepared['inference_inputs']; expected = reg['expected_inputs']
    require(len(entries) == len({e['id'] for e in entries}) == len({e['source_id'] for e in entries}) == expected
        and prepared['sources'] == gate['sources'] == gate['inputs'] == reg['expected_sources'], 'Exact complete source-owner/input inventory')
    require(prepared['execution_entries'] == entries and prepared['adopted_success'] == {}, '95 inputs are all compiled;97 derives only proven prior raw aliases')
    require(all(prepared[k] == reg[k] for k in ('training_completion', 'adapter_weights', 'head_weights', 'admitted_arm_names')), 'Prepared model and qualified arms bound to this97 registration')
    role = 'confirm' if reg['phase'] == 'confirm19' else 'formal'
    require(all(e['role'] == role for e in entries), 'No train/screen input in conditional phase')
    if reg['phase'] == 'confirm19':
        require(len({e['source_sha256'] for e in entries}) == 19
            and all(e['source_id'] != 'gnmc:test:006575.jpeg' for e in entries)
            and set(e['source_id'] for e in entries) == set(reg['expected_source_ids']), 'Exact19 successful owner whitelist; missing source never reattempted')
    else:
        require(prepared['official_source_count'] == gate['official_source_count'] == reg['official_source_count'] == 426
            and prepared['affected_video_count'] == gate['affected_video_count'] == reg['affected_video_count']
            and prepared['selection'] == reg['selection']
            and prepared['CPU_targets'] is None, 'Formal source count is D observations; no GT artifact')
    return entries


def adopted_index(reg):
    """Adopt successful metadata; never torch-load or re-QA an old raw."""
    result = {}
    for acceptance_ref in reg['adopted_output_acceptances']:
        accepted = read(bound(acceptance_ref))
        require(accepted['status'] in ADOPTABLE and all(accepted[k] == reg[k] for k in ('training_completion', 'adapter_weights', 'head_weights')),
            'Only a real existing first raw QA for this exact final798NEW model')
        for prediction in accepted['predictions']:
            receipt_ref, input_ref = prediction['receipt'], prediction['input']
            receipt, request = read(bound(receipt_ref)), read(bound(input_ref))
            require(all(prediction[k] == receipt[k] == request[k] for k in ('id', 'source_id', 'source_sha256'))
                and receipt['input'] == input_ref and all(receipt[k] == reg[k] for k in ('adapter_weights', 'head_weights'))
                and receipt['input_signature'] == request['input_signature'] and receipt['image_grid_thw'] == request['image_grid_thw']
                and receipt['width'] == request['width'] and receipt['height'] == request['height']
                and receipt['hidden_transform'] == 'F32_L2_UNIT_VECTOR_NO_EPS', 'Prior accepted source/weights/full-input/L2 identity')
            for name in ('raw_hidden', 'raw_head'):
                require(prediction[name] == receipt[name], 'Prior acceptance raw binding changed'); bound(receipt[name])
            key = identity(receipt)
            record = dict(acceptance=acceptance_ref, receipt=receipt_ref, input=input_ref, model_role=receipt['model_role'],
                raw_hidden=receipt['raw_hidden'], raw_head=receipt['raw_head'], decoded_xyw=receipt['decoded_xyw'])
            require(key not in result or all(result[key][k] == record[k] for k in ('raw_hidden', 'raw_head')),
                'Conflicting previously accepted raw for one exact model input')
            result.setdefault(key, record)
    return result


def validate_training(reg, original, trained):
    require(original['GPU_code'] == reg['frozen_GPU93_code']
        and all(original[k] == reg[k] for k in ('model_config', 'math_code', 'old_TIME', 'old_PAIR', 'old_CROP'))
        and trained['status'] == 'COMPLETE_DIRECT_BOX93_NEW798_NOT_QUALITY'
        and trained['GPU_registration'] == reg['frozen_GPU93_registration']
        and trained['completed_updates'] == 798 and trained['successful_micro'] == trained['actual_training_forwards'] == 3192
        and trained['original_successful_updates'] == 1 and trained['original_successful_forwards'] == 8
        and trained['original84_progress'] == original['original84_progress'] and trained['optimizer_reset'] is True
        and trained['hidden_transform'] == 'F32_L2_UNIT_VECTOR_NO_EPS'
        and all(trained[k] is True for k in ('adapter_reload_all288_exact', 'head_reload_all2_exact'))
        and all(trained[k] == reg[k] for k in ('adapter_weights', 'head_weights')),
        'Only actual complete final798NEW plus adopted84 step1 model is qualified')


def inference_stage(out, reg, registration_ref, prepared, reader, model, head, helper84, math84, frozen, torch, trace):
    phase = reg['phase']; role = 'DIRECT_BOX93_'+phase; entries = prepared['inference_inputs']
    journal = out/'attempts.jsonl'; journal.touch(exist_ok=False)
    external = adopted_index(reg); previous = {}; completed = []; new = internal = adopted = 0; videos = set()
    model.eval(); head.eval()
    require(not any(p.requires_grad for p in model.parameters()) and not any(p.requires_grad for p in head.parameters()), 'Readonly BASE+new direct-box model')
    for i, entry in enumerate(entries):
        frozen._deadline(reg); values, request = helper84._input(reader, entry, torch)
        receipt_metadata = dict(source_id=request['source_id'], source_sha256=request['source_sha256'], width=request['width'], height=request['height'],
            input_signature=request['input_signature'], adapter_weights=reg['adapter_weights'], head_weights=reg['head_weights'])
        key = identity(receipt_metadata); first = previous.get(key); prior = external.get(key) if first is None else None
        started = time.monotonic(); native_binding = {}
        if phase == 'formal':
            require(type(request['observation_index']) is int and request['observation_index'] >= 0 and request['observation_index'] % 2 == 0
                and type(request['native_ordinal']) is int and request['native_ordinal'] >= 0 and request['video_id'], 'Only registered even exact-native formal observations')
            native_binding = {k:request[k] for k in ('video_id', 'native_ordinal', 'native_pts_exact', 'observation_index')}
            videos.add(request['video_id'])
        if first is not None:
            raw_hidden_ref, raw_head_ref, decoded = first['raw_hidden'], first['raw_head'], first['decoded_xyw']; internal += 1
        elif prior is not None:
            raw_hidden_ref, raw_head_ref, decoded = prior['raw_hidden'], prior['raw_head'], prior['decoded_xyw']; adopted += 1
            append_event(journal, event='ADOPTED_PREVIOUSLY_QA_RAW', id=entry['id'], model_role=role,
                adopted_from_acceptance=prior['acceptance'], adopted_receipt=prior['receipt'], adopted_input=prior['input'],
                raw_hidden=raw_hidden_ref, raw_head=raw_head_ref)
        else:
            gpu = {k:v.to('cuda:0') for k, v in values.items()}
            append_event(journal, event='BEGIN_NEW_ROLE_FORWARD', id=entry['id'], input=entry['input'], model_role=role)
            trace['attempted'].append(entry['id']); frozen._deadline(reg)
            with torch.inference_mode(): hidden = helper84._hidden(model, gpu, torch, False); hidden_cpu = hidden.float().cpu().contiguous()
            hidden_path = out/('%06d.hidden.pt'%i); frozen._tensor_file(hidden_path, hidden_cpu, torch)
            item = dict(id=entry['id'], raw_hidden=ref(hidden_path), model_forward_returned=True); trace['raw'].append(item)
            with torch.inference_mode(): raw_gpu = head(math84.normalize_hidden(hidden)); raw_cpu = raw_gpu.float().cpu().contiguous()
            head_path = out/('%06d.head.pt'%i); frozen._tensor_file(head_path, raw_cpu, torch); item['raw_head'] = ref(head_path)
            raw_hidden_ref, raw_head_ref = item['raw_hidden'], item['raw_head']
            append_event(journal, event='FIRST_RAW_PERSISTED', id=entry['id'], raw_hidden=raw_hidden_ref, raw_head=raw_head_ref, model_role=role)
            require(hidden_cpu.dtype == raw_cpu.dtype == torch.float32 and tuple(hidden_cpu.shape) == (4096,)
                and tuple(raw_cpu.shape) == (3,) and bool(torch.isfinite(hidden_cpu).all()) and bool(torch.isfinite(raw_cpu).all()), 'Persisted finite hidden4096/head3')
            with torch.inference_mode(): decoded = math84.decode_torch(raw_gpu, request['width'], request['height']).float().cpu().tolist()
            torch.cuda.synchronize(); del gpu, hidden, hidden_cpu, raw_gpu, raw_cpu; new += 1
        is_new, is_internal, is_external = first is None and prior is None, first is not None, first is None and prior is not None
        receipt_path = out/('%06d.receipt.json'%i)
        save(receipt_path, dict(id=entry['id'], input=entry['input'], role=request['role'], phase=phase, model_role=role,
            **receipt_metadata, image_grid_thw=request['image_grid_thw'], raw_hidden=raw_hidden_ref, raw_head=raw_head_ref, decoded_xyw=decoded,
            raw_dtype='torch.float32', hidden_dimension=4096, head_dimension=3, actual_new_forward=is_new, internal_alias=is_internal, external_alias=is_external,
            hidden_transform=math84.RECIPE['hidden_transform'],
            alias_of=first['receipt'] if first else None, adopted_from_acceptance=prior['acceptance'] if prior else None,
            adopted_receipt=prior['receipt'] if prior else None, adopted_input=prior['input'] if prior else None,
            adopted_model_role=prior['model_role'] if prior else None, native_binding=native_binding,
            elapsed_seconds=time.monotonic()-started, screen_reference_read=False, no_LM_generation=True,
            original_TIME_loaded=False, old_PAIR_loaded=False, old_CROP_loaded=False, old_UTILITY_loaded=False))
        receipt_ref = ref(receipt_path)
        previous.setdefault(key, dict(receipt=receipt_ref, raw_hidden=raw_hidden_ref, raw_head=raw_head_ref, decoded_xyw=decoded))
        completed.append(dict(id=entry['id'], source_id=request['source_id'], source_sha256=request['source_sha256'], input=entry['input'], receipt=receipt_ref))
        append_event(journal, event='ACCEPTED_NEW_ROLE_RESULT', id=entry['id'], receipt=receipt_ref, model_role=role,
            alias=not is_new, internal_alias=is_internal, external_alias=is_external)
        del values
    require(new+internal+adopted == reg['expected_inputs'] == len(completed), 'Exact new/internal/external execution inventory')
    extra = {}
    if phase == 'formal':
        require(len(videos) == reg['affected_video_count'] and videos == set(reg['affected_video_ids']), 'Actual affected426 subset matches registered source manifest')
        extra = dict(official_source_count=426, affected_video_count=len(videos), affected_video_ids=sorted(videos),
            expected_affected_videos=reg['expected_affected_videos'],
            whole426_preserved=True, time_selection_unchanged=True, selection=reg['selection'])
    frozen._deadline(reg)
    save(out/'completion.json', dict(status=STATUSES[phase], phase=phase, model_role=role, entries=completed,
        expected_inputs=reg['expected_inputs'], sources=reg['expected_sources'], actual_forward_calls=new, internal_aliases=internal,
        aliases=internal, external_adopted=adopted, attempts=ref(journal), GPU_registration=registration_ref,
        input_prepared=reg['prepared'], CPU_registration=reg['CPU_registration'], input_acceptance=reg['input_acceptance'],
        training_completion=reg['training_completion'], adapter_weights=reg['adapter_weights'], head_weights=reg['head_weights'],
        admitted_arm_names=reg['admitted_arm_names'], hidden_transform=math84.RECIPE['hidden_transform'],
        screen_reference_read=False, targets_read=False, no_training=True, automatic_next_phase=False,
        no_LM_generation=True, **extra))
    return ref(out/'completion.json')


def run(root, phase, registration_path):
    root = Path(root).resolve(); registration_path = Path(registration_path).resolve(); reg = read(registration_path)
    require(root.is_relative_to(WORK) and bool(os.environ.get('CUDA_VISIBLE_DEVICES')), 'Authorized Linux root and actual physical GPU assignment')
    validate_admission(root, phase, registration_path, reg)
    prepared, gate = read(bound(reg['prepared'])), read(bound(reg['input_acceptance'])); validate_inputs(reg, prepared, gate)
    original = read(bound(reg['frozen_GPU93_registration'])); trained = read(bound(reg['training_completion']))
    validate_training(reg, original, trained)
    adapter_path = bound(reg['adapter_weights']); directory = Path(reg['adapter_directory']).resolve()
    require(adapter_path.parent == directory == Path(trained['adapter_directory']).resolve()
        and bound(reg['adapter_config']) == directory/'adapter_config.json', 'Exact saved final adapter configuration and weight directory')
    old32 = read(bound(original['original_GPU32'])); old18 = read(bound(original['original_GPU18']))
    for item in old18['runtime_dependencies']: bound(item)
    old17 = read(bound(old18['pair_registration']))
    for name, expected in old17['new_code'].items():
        require(ref(root/'pair_code_17'/name)['sha256'] == expected, 'Frozen runtime helper changed: '+name)
    helper84 = module(reg['frozen_GPU93_code'], '_readonly_direct93_for97')
    frozen = module(old32['GPU_code'], '_readonly_direct97_io32'); frozen._deadline(reg); paths()
    import torch
    import transformers
    import peft
    from transformers import Qwen3VLForConditionalGeneration
    from peft import PeftModel
    from safetensors.torch import load_file
    from sft_contract import REVISION, verify_live_gpu_reservation
    from verify_saved_smoke import canonical_frozen_hash
    require(transformers.__version__ == '4.57.1' and peft.__version__ == '0.17.1', 'Pinned readonly direct-box runtime')
    verify_live_gpu_reservation(); require(read(WORK/'improvement_round1/active_gpu_job.json')['name'] == reg['GPU_job'], 'Exact shared GPU reservation')
    torch.set_num_threads(2)
    math84 = module(reg['math_code'], '_readonly_direct97_math')
    require(trained['recipe'] == original['recipe'] == math84.RECIPE
        and original['frozen_math84_code'] == reg['frozen_math84_code']
        and Path(math84.frozen84.__file__).resolve() == bound(reg['frozen_math84_code']),
        'Frozen L2 trained decoder and complete recipe identity')
    component = module(reg['preparation_code'], '_readonly_direct97_input_reader')
    reader = component.load_inputs(root, phase=phase, registration_ref=ref(registration_path))
    require(reader.prepared == prepared, 'Reader adopts exact registered external inputs')
    out = Path(reg['output_directory']).resolve(); out.parent.mkdir(exist_ok=True); out.mkdir(exist_ok=False)
    save(out/'claim.json', dict(utc=utc(), pid=os.getpid(), phase=phase, GPU_registration=ref(registration_path), no_training=True, targets_read=False))
    started = time.monotonic(); torch.cuda.reset_peak_memory_stats(); trace = dict(attempted=[], raw=[])
    try:
        cfg = read(bound(reg['model_config']))
        base = Qwen3VLForConditionalGeneration.from_pretrained(cfg['model_dir'], revision=REVISION, local_files_only=True,
            torch_dtype=torch.bfloat16, device_map={'':'cuda:0'}, low_cpu_mem_usage=True, attn_implementation='sdpa')
        for p in base.parameters(): p.requires_grad_(False)
        base.eval(); base.config.use_cache = False
        require(not any('lora_' in name for name, _ in base.named_parameters()), 'Physical BASE has no failed adapter')
        before = canonical_frozen_hash(base, torch)
        require(before['parameters'] == helper84.BASE and before['sha256'] == cfg['expected_base_sha256']
            and before == trained['base_fingerprint'], 'Exact frozen physical BASE hash and qualified training identity')
        model = PeftModel.from_pretrained(base, str(directory), adapter_name='direct_box', is_trainable=False, local_files_only=True).eval()
        for p in model.parameters(): p.requires_grad_(False)
        head = torch.nn.Linear(4096, 3, bias=True, device='cuda:0', dtype=torch.float32)
        saved_head = torch.load(bound(reg['head_weights']), map_location='cpu', weights_only=True)
        require(set(saved_head) == {'weight', 'bias'} and tuple(saved_head['weight'].shape) == (3, 4096) and tuple(saved_head['bias'].shape) == (3,)
            and all(v.dtype == torch.float32 and bool(torch.isfinite(v).all()) for v in saved_head.values()), 'Complete persisted F32 final head2')
        head.load_state_dict(saved_head); head.requires_grad_(False); head.eval()
        _, inventory = helper84._inventory(model, head, False, torch)
        require(inventory == trained['inventory'], 'Actual readonly parameter inventory equals qualified final798 identity')
        initial = helper84._trainables(model, head, torch, frozen)
        require(frozen._same_state(initial['adapter_state_dict'], load_file(str(adapter_path), device='cpu'), torch)
            and frozen._same_state(initial['head_state_dict'], saved_head, torch), 'All288+2 actual loaded tensors match final798NEW bytes')
        completion = inference_stage(out, reg, ref(registration_path), prepared, reader, model, head, helper84, math84, frozen, torch, trace)
        require(helper84._tree_equal(helper84._trainables(model, head, torch, frozen), initial, torch)
            and canonical_frozen_hash(model, torch) == before, 'Readonly conditional source inference changed weights')
        helper84._inventory(model, head, False, torch)
        for key in ('adapter_weights', 'head_weights', 'old_TIME', 'old_PAIR', 'old_CROP'): bound(reg[key])
        frozen._deadline(reg)
        save(out/'model_integrity.json', dict(status='PASS_DIRECT_BOX97_READONLY_MODEL_BYTE_IDENTITY', completion=completion,
            registration=ref(registration_path), training_completion=reg['training_completion'], inventory=inventory, base_fingerprint=before,
            adapter_all288_exact=True, head_all2_exact=True, all_weights_frozen=True, no_training=True, targets_read=False,
            seconds=time.monotonic()-started, peak_allocated_mib=torch.cuda.max_memory_allocated()/2**20,
            peak_reserved_mib=torch.cuda.max_memory_reserved()/2**20))
    except BaseException as error:
        save(out/'failure.json', dict(utc=utc(), error=repr(error), traceback=traceback.format_exc(), attempted_model_calls=trace['attempted'],
            successful_raw=trace['raw'], preserve_all_success=True, automatic_retry=False, failure_is_not_empty=True,
            no_training=True, automatic_next_phase=False))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--phase', choices=PHASES, required=True)
    parser.add_argument('--registration', type=Path, required=True)
    args = parser.parse_args(); run(args.root, args.phase, args.registration)
