"""First formal original-TIME and disabled-adapter BASE summaries, zero training.

One shared wrapper invocation loads one BASE and the original TIME adapter once.
The two roles run serially, each with its own natural completion artifact. No
launcher, selection, implicit registration discovery, automatic retry or labels.
"""
import argparse
from collections import defaultdict
from contextlib import contextmanager, nullcontext
from datetime import datetime, timezone
from fractions import Fraction as F
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
import traceback

import torch
from summary_contract import build_pixels, signature, require
from summary_grammar6 import PrefixConstraint, ascii_token_candidates
from summary_output import parse_summary

W = Path('/home/inspur/aic_video_work')
RUN = W / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
SCHEMA = 'FIVE_SUMMARY_SPRINT_V41'
SOURCE_KIND = 'ADOPTED_FORMAL_2HZ_ORIGINAL_IMAGE_PATCHES'
ROLES = ('TIME', 'BASE')
LORA_NAME = re.compile(r'language_model\.layers\.\d+\.self_attn\.(q_proj|k_proj|v_proj|o_proj)\.lora_(A|B)\.TIME\.weight$')


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def ref(path):
    path = Path(path).resolve(strict=True)
    return dict(path=str(path), bytes=path.stat().st_size, sha256=sha(path))


def bound(reference):
    path = Path(reference['path']).resolve(strict=True)
    require(path.is_relative_to(W) and path.is_file(), 'Artifact outside explicit Linux work root')
    require(sha(path) == reference['sha256'], 'Explicit registered artifact changed: ' + str(path))
    if 'bytes' in reference:
        require(path.stat().st_size == reference['bytes'], 'Explicit registered byte size changed')
    return path


def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())


def event(path, name, **values):
    with Path(path).open('a') as stream:
        stream.write(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),
                                     event=name, **values), ensure_ascii=False, allow_nan=False) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def same_ref(first, second):
    return bound(first) == bound(second) and first['sha256'] == second['sha256']


def aware_time(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(result.tzinfo is not None, 'Explicit timezone-aware deadline required')
    return result


def checked_registration(path):
    path = Path(path).resolve(strict=True)
    require(path.is_relative_to(W), 'Explicit registration must remain in Linux work root')
    reg = read(path)
    require(reg['schema'] == SCHEMA and reg['expected_sources'] == 426
            and reg['expected_windows'] == 522, 'Exact frozen426/522 schema required')
    require(reg.get('roles', list(ROLES)) == list(ROLES), 'Only original TIME then BASE, once each')
    here = Path(__file__).resolve().parent
    required = {'generate_formal41.py', 'summary_contract.py', 'summary_grammar6.py', 'summary_output.py'}
    require(required <= set(reg['code']), 'Every executed generation code component must be bound')
    # Do not depend on unrelated QA/package files that may be registered later.
    for name in sorted(required):
        require(bound(reg['code'][name]) == here / name, 'Actual executed generation code differs: ' + name)
    cfg = read(bound(reg['model_config_ref']))
    original = bound(reg['original_TIME_ref'])
    require(original == Path(cfg['b_adapter']) / 'adapter_model.safetensors'
            and sha(original) == cfg['b_adapter_sha256'], 'Frozen original TIME path/bytes required')
    require(reg['actual_resident_parameters'] == cfg['complete_parameters'] == 8782459120
            and type(reg['actual_pipeline_parameters']) is int
            and reg['actual_resident_parameters'] <= reg['actual_pipeline_parameters'] <= 9_000_000_000,
            'Exact shared BASE/TIME resident count and complete registered pipeline inventory')
    admission = read(bound(reg['production_admission_ref']))
    require(admission['status'] == 'ADMIT_FROZEN_ORIGINAL_TIME_BASE_426_TWO_VIEW_41'
            and admission['production_allowed'] is True
            and admission['allow_first_formal_inputs'] is True
            and admission['main_review_completed'] is True
            and same_ref(admission['original_TIME_ref'], reg['original_TIME_ref'])
            and admission['actual_pipeline_parameters'] == reg['actual_pipeline_parameters'],
            'Actual original-TIME/BASE pilot review must explicitly admit this formal task')
    root = Path(reg['root']).resolve(strict=True)
    out = Path(reg['output_directory']).resolve()
    require(root.is_relative_to(W) and out == root / 'formal_outputs_41', 'Explicit new formal output directory')
    require(isinstance(reg['job_name'], str) and re.fullmatch(r'[A-Za-z0-9_-]+', reg['job_name'])
            and reg['max_gpu_seconds'] > 0
            and set(reg['max_gpu_seconds_by_role']) == set(ROLES)
            and all(reg['max_gpu_seconds_by_role'][role] > 0 for role in ROLES), 'Explicit job and finite budgets')
    require(aware_time(reg['model_start_cutoff_utc']) == aware_time('2026-10-19T11:52:37Z')
            and aware_time(reg['deadline_utc']) == aware_time('2026-10-19T15:52:37Z'),
            'Original experiment cutoff and final deadline must not be extended')
    return path, reg, cfg, out


def accepted_inputs(reg):
    gate = read(bound(reg['first_input_acceptance_ref']))
    require(gate['status'] == 'PASS_ALL426_FIRST_SUMMARY_FORMAL_TWO_VIEW_INPUTS_41'
            and gate['sources'] == 426 and gate['windows'] == 522,
            'Complete actual first426/522 two-view input acceptance required')
    require(same_ref(gate['registration_ref'], reg['input_phase_registration_ref']),
            'CPU gate must bind the immutable input-phase registration')
    input_reg = read(bound(reg['input_phase_registration_ref']))
    require(input_reg['schema'] == SCHEMA and input_reg['root'] == reg['root']
            and same_ref(input_reg['original_TIME_ref'], reg['original_TIME_ref'])
            and same_ref(input_reg['production_admission_ref'], reg['production_admission_ref']),
            'GPU and accepted CPU phases must bind the same original model/admission/root')
    prepared = read(bound(gate['prepared_ref']))
    sources = read(bound(prepared.get('source_catalog_ref', prepared.get('source_catalog'))))['sources']
    catalog = {source['id']: source for source in sources}
    require(len(sources) == len(catalog) == 426 and set(catalog) == {str(i) for i in range(426)}
            and len(prepared['inputs']) == 522 and all(source['kind'] == SOURCE_KIND for source in sources),
            'Exact426 IDs, original patch kind and522 windows')
    by_source, requests = defaultdict(list), {}
    for request_ref in prepared['inputs']:
        request = read(bound(request_ref))
        uid, sid = request['uid'], request['sid']
        require(isinstance(uid, str) and re.fullmatch(r'[A-Za-z0-9_.:-]+', uid)
                and uid not in requests and sid in catalog
                and request['source_sha256'] == catalog[sid]['source_sha256']
                and request['source_clock_ref'] == catalog[sid]['clock']
                and request['first_new_pixel_text_native_QA'] is True and request['labels_read'] is False,
                'Unique accepted window/source/native-clock identity')
        requests[uid] = (request_ref, request)
        by_source[sid].append(uid)
    require(set(by_source) == set(catalog), 'All426 sources must have accepted windows')
    return gate, prepared, catalog, requests, by_source


def load_formal_source(source):
    """Read original uncompressed image patch PTs; no media decode or encoder."""
    require(source['kind'] == SOURCE_KIND, 'Accepted original formal2Hz patches only')
    frames, grids, ordinals = [], [], []
    for case in source['context_cases']:
        path = bound(case)
        with path.open('rb') as stream:
            require(stream.read(2) != b'\x1f\x8b', 'Formal patches must be original uncompressed PTs')
        payload = torch.load(path, map_location='cpu', weights_only=True)
        require(set(payload) == {'pixel_values', 'image_grid_thw', 'sample_ordinals'}, 'Original ordinary PT keys')
        pixels, grid = payload['pixel_values'], payload['image_grid_thw']
        require(grid.dtype == torch.int64 and grid.tolist() == case['grids']
                and payload['sample_ordinals'] == case['samples'] and len(grid) == len(case['samples'])
                and pixels.device.type == grid.device.type == 'cpu'
                and pixels.dtype == torch.float32 and pixels.ndim == 2,
                'Actual retained grid/sample/pixel mapping')
        offset = 0
        for t, h, w in grid.tolist():
            require(t == 1 and h > 0 and w > 0, 'Individual source observations only')
            frames.append(pixels[offset:offset + h*w])
            grids.append([h, w])
            offset += h*w
        require(offset == len(pixels), 'All retained patch slices accounted for')
        ordinals.extend(case['samples'])
    require(frames and len(frames) == source['cells'] == len(ordinals)
            and ordinals == sorted(set(ordinals)) and all(grid == grids[0] for grid in grids),
            'Complete source-local native observations')
    return frames, grids[0], ordinals


def reconstruct(request, source, source_values, clock):
    frames, grid, ordinals = source_values
    plan = request['plan']
    values, actual = build_pixels(frames, grid, ordinals, clock['normalized_exact_pts'],
        plan['window_start_exact'], plan['window_end_exact'],
        dict(source_id=request['sid'], source_sha256=source['source_sha256']))
    require(actual == plan, 'Accepted whole-source Overview/Excerpt plan changed')
    prefix = torch.load(bound(request['prefix_ref']), map_location='cpu', weights_only=True)
    require(set(prefix) == {'input_ids', 'attention_mask'}
            and prefix['input_ids'].dtype == prefix['attention_mask'].dtype == torch.int64
            and prefix['input_ids'].shape == prefix['attention_mask'].shape
            and prefix['input_ids'].shape[0] == 1, 'Accepted exact prefix batch1')
    values.update(prefix)
    require(signature(values) == request['input_signature'], 'Runtime input differs from first accepted actual tensors')
    return values


def role_flags(model, layers, role):
    require(len(layers) == 144 and model.active_adapter == 'TIME'
            and all(set(layer.lora_A) == {'TIME'} and list(layer.active_adapters) == ['TIME']
                    and bool(layer.disable_adapters) == (role == 'BASE') for layer in layers),
            'Actual144 adapter flags differ from current role ' + role)


def inventory(model, pipeline):
    counts, matrices = dict(base=0, TIME=0), 0
    for name, parameter in model.named_parameters():
        require(not parameter.requires_grad, 'Every inference parameter must be frozen')
        if 'lora_' in name:
            match = LORA_NAME.search(name)
            require(match is not None and parameter.ndim == 2
                    and (parameter.shape[0] if match[2] == 'A' else parameter.shape[1]) == 16,
                    'Only original144 language rank16 TIME pairs may reside')
            counts['TIME'] += parameter.numel()
            matrices += 1
        else:
            counts['base'] += parameter.numel()
    layers = [module for module in model.modules() if hasattr(module, 'lora_A')]
    require(counts == dict(base=8767123696, TIME=15335424) and matrices == 288,
            'Actual one-BASE/original-TIME resident parameter inventory')
    role_flags(model, layers, 'TIME')
    return dict(**counts, resident_parameters=sum(counts.values()), actual_pipeline_parameters=pipeline,
                all_frozen=True, active_adapter='TIME', matrices=288, language_targets=144)


@contextmanager
def frozen_role_scope(model, layers, role, parameter_flags, proof_path):
    """Restore PEFT's enable-adapter trainability side effect, including on error."""
    role_flags(model, layers, 'TIME')
    require(all(not flag and not parameter.requires_grad for parameter, flag in parameter_flags),
            'Only the exact original frozen inference flags may enter a role')
    try:
        with model.disable_adapter() if role == 'BASE' else nullcontext():
            role_flags(model, layers, role)
            yield
            role_flags(model, layers, role)
    finally:
        # PEFT0.17.1 enables the resident adapter at context exit and may also
        # set its requires_grad flags. Restore the original per-parameter flags
        # explicitly; this changes no tensors and invokes no model forward.
        trainable_before_restore = sum(parameter.numel() for parameter, _ in parameter_flags
                                       if parameter.requires_grad)
        disabled_before_restore = sum(bool(layer.disable_adapters) for layer in layers)
        for parameter, flag in parameter_flags:
            parameter.requires_grad_(flag)
        role_flags(model, layers, 'TIME')
        require(all(parameter.requires_grad == flag for parameter, flag in parameter_flags),
                'Original per-parameter inference flags failed to restore')
        save(proof_path, dict(status='PASS_ORIGINAL_TIME_ROLE_AND_FROZEN_FLAGS_RESTORED_41',
             model_role=role, post_context_trainable_parameters_before_restore=trainable_before_restore,
             post_context_disabled_layers_before_restore=disabled_before_restore,
             restored_trainable_parameters=0, restored_disabled_layers=0,
             all144_TIME_layers_enabled=True, optimizer_updates=0, model_forwards_in_restoration=0))


def exact_time_weights(model, weights, diagnostic_path=None):
    from peft import get_peft_model_state_dict
    from peft.utils.save_and_load import set_peft_model_state_dict
    from safetensors.torch import load_file
    actual = get_peft_model_state_dict(model, adapter_name='TIME')
    saved = load_file(str(weights), device='cpu')
    require(set(actual) == set(saved) and len(saved) == 288
            and all(value.dtype == torch.float32 for value in actual.values())
            and all(value.dtype == torch.float32 for value in saved.values()),
            'Original288 saved and resident TIME matrices must be FP32')
    mismatches = [key for key in saved if not torch.equal(actual[key].detach().cpu(), saved[key])]
    rounded = [key for key in mismatches if torch.equal(actual[key].detach().cpu(),
                                                       saved[key].to(torch.bfloat16).float())]
    if diagnostic_path is not None:
        save(diagnostic_path, dict(status='ORIGINAL_TIME_PRE_FORWARD_LOAD_DIAGNOSTIC_41',
             matrices=288, pre_restore_mismatches=len(mismatches),
             mismatches_equal_saved_bfloat16_roundtrip=len(rounded), source_weights_modified=False))
        require(len(rounded) == len(mismatches), 'Unexplained adapter loading difference; no forward permitted')
        # Restore only the same immutable saved FP32 tensors after PEFT's dtype
        # conversion. No training, rounding tolerance or checkpoint substitution.
        set_peft_model_state_dict(model, saved, adapter_name='TIME')
        actual = get_peft_model_state_dict(model, adapter_name='TIME')
    require(all(actual[key].dtype == saved[key].dtype and
                torch.equal(actual[key].detach().cpu().contiguous().view(torch.uint8),
                            saved[key].contiguous().view(torch.uint8)) for key in saved),
            'All288 original saved TIME matrices must match resident FP32 bits')
    return dict(matrices=288, all288_bit_equal_saved=True, saved_and_actual_dtype='torch.float32')


def run(registration_path):
    require(os.uname().nodename == 'inspur-NP5570M5'
            and os.environ.get('CUDA_VISIBLE_DEVICES') not in (None, ''),
            'Only registered shared GPU runner on actual training host')
    path, reg, cfg, out = checked_registration(registration_path)
    gate, prepared, catalog, requests, by_source = accepted_inputs(reg)
    require(datetime.now(timezone.utc) < aware_time(reg['model_start_cutoff_utc']),
            'No new model launch after original main cutoff')
    out.mkdir(parents=True, exist_ok=False)
    save(out / 'claim.json', dict(schema=SCHEMA, registration_ref=ref(path), pid=os.getpid(),
         job_name=reg['job_name'], roles=list(ROLES), original_TIME_ref=reg['original_TIME_ref'],
         expected_sources=426, expected_windows=522, automatic_retry=False))
    started = time.monotonic()
    completed_roles, role, role_out = [], None, None
    outputs, raw_saved, source_completions = [], [], []
    forward_checks = {name: 0 for name in ROLES}
    role_started = None

    def deadline():
        require(datetime.now(timezone.utc) < aware_time(reg['deadline_utc'])
                and time.monotonic() - started < reg['max_gpu_seconds'], 'Actual final deadline or total GPU budget reached')
        if role_started is not None:
            require(time.monotonic() - role_started < reg['max_gpu_seconds_by_role'][role],
                    'Actual role GPU budget reached')

    try:
        sys.path.insert(0, str(RUN / 'temporal_sft8b_v1'))
        from sft_contract import verify_live_gpu_reservation
        from verify_saved_smoke import canonical_frozen_hash
        verify_live_gpu_reservation()
        deadline()
        import transformers
        import peft
        from transformers import Qwen3VLForConditionalGeneration, AutoTokenizer
        from peft import PeftModel
        require(transformers.__version__ == '4.57.1' and peft.__version__ == '0.17.1'
                and torch.cuda.is_available(), 'Pinned actual Qwen CUDA runtime')
        require(datetime.now(timezone.utc) < aware_time(reg['model_start_cutoff_utc']),
                'Actual model load cannot begin past original main cutoff')
        base = Qwen3VLForConditionalGeneration.from_pretrained(cfg['model_dir'], revision=cfg['model_revision'],
            local_files_only=True, torch_dtype=torch.bfloat16, device_map={'': 'cuda:0'},
            low_cpu_mem_usage=True, attn_implementation='sdpa')
        for parameter in base.parameters():
            parameter.requires_grad_(False)
        before = canonical_frozen_hash(base, torch)
        require(before['parameters'] == 8767123696 and before['sha256'] == cfg['expected_base_sha256'],
                'Actual original BASE bytes')
        weights = bound(reg['original_TIME_ref'])
        model = PeftModel.from_pretrained(base, str(weights.parent), adapter_name='TIME', is_trainable=False).eval()
        for parameter in model.parameters():
            parameter.requires_grad_(False)
        flags = [(parameter, parameter.requires_grad) for parameter in model.parameters()]
        inv = inventory(model, reg['actual_pipeline_parameters'])
        layers = [module for module in model.modules() if hasattr(module, 'lora_A')]
        exact = exact_time_weights(model, weights, out / 'TIME_load_diagnostic41.json')
        save(out / 'exact_TIME_load_acceptance41.json', dict(
            status='PASS_ORIGINAL_TIME_EXACT_SAVED_FP32_BEFORE_ANY_FORWARD_41',
            original_TIME_ref=reg['original_TIME_ref'], **exact, model_forwards=0))
        tokenizer = AutoTokenizer.from_pretrained(cfg['model_dir'], local_files_only=True)
        eos = tokenizer.convert_tokens_to_ids('<|im_end|>')
        require(eos == 151645, 'Original trained EOS')
        candidates = ascii_token_candidates(tokenizer)

        def actual_forward_guard(module, args):
            require(role in ROLES, 'No unregistered actual forward')
            deadline()
            role_flags(model, layers, role)
            require(all(not parameter.requires_grad for parameter, _ in flags), 'Actual forward must be entirely frozen')
            forward_checks[role] += 1

        # Hook the actual Qwen module invoked inside PEFT.generate, including
        # every cached decoding forward, rather than only the PEFT wrapper.
        forward_guard = base.register_forward_pre_hook(actual_forward_guard)
        for role in ROLES:
            deadline()
            role_started = time.monotonic()
            role_out = out / role
            role_out.mkdir(exist_ok=False)
            outputs, raw_saved, source_completions = [], [], []
            save(role_out / 'claim.json', dict(schema=SCHEMA, model_role=role, registration_ref=ref(path),
                 original_TIME_ref=reg['original_TIME_ref'], pid=os.getpid(), automatic_retry=False))
            role_flags(model, layers, 'TIME')
            restore_proof = role_out / 'post_context_flag_restore41.json'
            with frozen_role_scope(model, layers, role, flags, restore_proof):
                role_flags(model, layers, role)
                for sid in sorted(catalog, key=int):
                    source = catalog[sid]
                    clock = read(bound(source['clock']))
                    require(clock['source_sha256'] == source['source_sha256'], 'Original source-clock identity')
                    source_values = load_formal_source(source)
                    local_outputs = []
                    for uid in by_source[sid]:
                        deadline()
                        request_ref, request = requests[uid]
                        values = reconstruct(request, source, source_values, clock)
                        duration = F(request['plan']['window_end_exact']) - F(request['plan']['window_start_exact'])
                        prefix = int(values['input_ids'].shape[1])
                        constraint = PrefixConstraint(tokenizer, prefix, duration, max_segments=6,
                            candidate_token_ids=candidates, eos_token_ids=[eos], allow_empty=True)
                        gpu = {key: value.to('cuda:0') for key, value in values.items()}
                        event(role_out / 'journal.jsonl', 'BEGIN_GENERATION', uid=uid, sid=sid,
                              model_role=role, request_ref=request_ref)
                        before_checks = forward_checks[role]
                        role_flags(model, layers, role)
                        with torch.inference_mode():
                            generated = model.generate(**gpu, max_new_tokens=512, do_sample=False, num_beams=1,
                                num_return_sequences=1, use_cache=True, eos_token_id=eos, pad_token_id=eos,
                                prefix_allowed_tokens_fn=constraint)
                        torch.cuda.synchronize()
                        ids = generated[0, prefix:].detach().cpu().tolist()
                        raw_path = role_out / (uid + '.tokens.json')
                        # Persist first raw tokens before syntax, role or semantic
                        # acceptance. A later failure cannot become an empty answer.
                        save(raw_path, dict(uid=uid, sid=sid, request_ref=request_ref, generated_ids=ids,
                            model_role=role, model_weights_ref=reg['original_TIME_ref'],
                            actual_prefix_signature=signature({'input_ids': generated[:, :prefix].detach().cpu()}),
                            expected_prefix_signature=signature({'input_ids': values['input_ids']})))
                        raw_saved.append(ref(raw_path))
                        calls = forward_checks[role] - before_checks
                        require(calls > 0, 'Every output must have actual-forward role flag evidence')
                        role_flags(model, layers, role)
                        require(generated.shape[0] == 1 and
                                torch.equal(generated[0, :prefix].detach().cpu(), values['input_ids'][0]),
                                'Actual generated prefix identity')
                        constraint.assert_complete(ids)
                        require(ids and ids[-1] == eos and eos not in ids[:-1] and len(ids) <= 512,
                                'Natural complete single EOS/length')
                        text = tokenizer.decode(ids[:-1], skip_special_tokens=False, clean_up_tokenization_spaces=False)
                        segments = parse_summary(text, duration)
                        destination = role_out / (uid + '.output.json')
                        save(destination, dict(uid=uid, sid=sid, request_ref=request_ref, raw_token_ref=ref(raw_path),
                            raw_text=text, generated_ids=ids, model_role=role, model_weights_ref=reg['original_TIME_ref'],
                            parsed_exact_segments=[[str(a), str(b)] for a, b in segments], grammar_stats=constraint.stats,
                            adapter_disabled_actual_forward=(role == 'BASE'), forward_role_flag_checks=calls))
                        output_ref = ref(destination)
                        outputs.append(output_ref)
                        local_outputs.append(output_ref)
                        event(role_out / 'journal.jsonl', 'RAW_ACCEPTED', uid=uid, sid=sid, output_ref=output_ref)
                        del gpu, generated, values
                    source_path = role_out / ('source_' + sid + '.completion.json')
                    save(source_path, dict(status='PASS_FORMAL_SOURCE_SUMMARY_GENERATIONS_41', sid=sid,
                        source_sha256=source['source_sha256'], source_clock_ref=source['clock'], outputs=local_outputs,
                        windows=len(by_source[sid]), model_role=role, model_weights_ref=reg['original_TIME_ref']))
                    source_completions.append(ref(source_path))
                    del source_values, clock
            # disable_adapter() must restore all144 TIME flags at role end.
            role_flags(model, layers, 'TIME')
            require(len(outputs) == 522 and len(source_completions) == 426 and forward_checks[role] > 0,
                    'Every registered source/window exactly once for the role')
            require(canonical_frozen_hash(model, torch) == before and sha(weights) == cfg['b_adapter_sha256']
                    and all(parameter.requires_grad == flag for parameter, flag in flags),
                    'Frozen BASE/original TIME/parameter flags changed')
            exact_time_weights(model, weights)
            inventory(model, reg['actual_pipeline_parameters'])
            completion = role_out / 'completion.json'
            save(completion, dict(status='PASS_ALL426_FORMAL_SUMMARY_GENERATIONS_41', schema=SCHEMA,
                model_role=role, registration_ref=ref(path), outputs=outputs, source_completion_refs=source_completions,
                sources=426, windows=522, model_weights_ref=reg['original_TIME_ref'],
                input_acceptance_ref=reg['first_input_acceptance_ref'], production_admission_ref=reg['production_admission_ref'],
                base_fingerprint=before, inventory=inv, old_TIME_unchanged=True,
                all_parameter_flags_unchanged=True, original_TIME_exact_FP32_bits_unchanged=True,
                adapter_disabled_actual_forward=(role == 'BASE'), TIME_flags_restored=True,
                TIME_frozen_flag_restoration_ref=ref(restore_proof),
                forward_role_flag_checks=forward_checks[role], optimizer_updates=0, role_terminal='completed', role_exit_code=0,
                elapsed_seconds=time.monotonic() - role_started, labels_read=False, automatic_retry=False))
            completed_roles.append(ref(completion))
            event(out / 'journal.jsonl', 'ROLE_NATURALLY_COMPLETED', model_role=role, completion_ref=ref(completion))
            role_started = None
        forward_guard.remove()
        save(out / 'completion.json', dict(status='PASS_BOTH_ORIGINAL_TIME_BASE_FORMAL_GENERATIONS_41', schema=SCHEMA,
            registration_ref=ref(path), role_completion_refs=completed_roles, roles=list(ROLES), sources=426, windows_per_role=522,
            original_TIME_ref=reg['original_TIME_ref'], actual_resident_parameters=8782459120,
            actual_pipeline_parameters=reg['actual_pipeline_parameters'], optimizer_updates=0, new_model_loads=1,
            elapsed_seconds=time.monotonic() - started, automatic_retry=False, labels_read=False))
    except BaseException as exc:
        failure = dict(error=repr(exc), traceback=traceback.format_exc(), model_role=role,
            outputs=outputs, first_raw_token_generations=raw_saved, source_completion_refs=source_completions,
            completed_sources=len(source_completions), completed_windows=len(outputs), completed_role_refs=completed_roles,
            forward_role_flag_checks=forward_checks, automatic_retry=False, failure_to_empty=False,
            preserve_all_successful_items=True, utc=datetime.now(timezone.utc).isoformat())
        if role_out is not None and not (role_out / 'completion.json').exists():
            save(role_out / 'failure.json', failure)
        save(out / 'failure.json', failure)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--registration', required=True)
    run(parser.parse_args().registration)
