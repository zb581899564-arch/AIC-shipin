"""First independent CPU context-output QA and one frozen pilot comparison.

Old successful local-input output QA is adopted, never rerun. The primary role
is always PAIR_TRUE. Passing the focused context checks permits only a separately
registered remaining-TRUE readout; it never qualifies production or official F1.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import traceback

_support = Path(__file__).resolve().parents[1]/'pair_code_17'
if _support.is_dir():
    sys.path.insert(0, str(_support))
from pair_common import WORK, read, save, sha, ref, bound, require, utc, signature
from pair_preference_math import source_metrics


ROLES = ('BASE_TRUE', 'PAIR_TRUE', 'PAIR_FOREIGN')
COUNTS = {'BASE_TRUE': 45, 'PAIR_TRUE': 45, 'PAIR_FOREIGN': 40}
OWNER_KEYS = ('source_id', 'source_sha256', 'overview_source_id', 'overview_source_sha256', 'overview_is_foreign')
BASE_PARAMETERS, PAIR_PARAMETERS, PIPELINE_PARAMETERS = 8767123696, 7667712, 8790225161


def _owners(row):
    return {key: row[key] for key in OWNER_KEYS}


def _alias_key(receipt):
    return json.dumps(dict(role=receipt['model_role'], owners=_owners(receipt),
        signature=receipt['input_signature'], classes=receipt['class_token_ids']), sort_keys=True, separators=(',', ':'))


def validate_alias(receipt, current_reference, prior_receipts, seen_inputs):
    """Pure alias validation; a foreign/different-owner raw is never reusable."""
    require(type(receipt['actual_new_forward']) is bool, 'Actual-new-forward must be an explicit bool')
    key = _alias_key(receipt)
    if receipt['actual_new_forward']:
        require(receipt['alias_of'] is None and key not in seen_inputs,
                'A new forward cannot repeat a successful exact same-role/owner input')
        return key
    require(isinstance(receipt['alias_of'], dict), 'Alias requires its original receipt reference')
    previous = prior_receipts.get(receipt['alias_of']['path'])
    require(previous is not None and current_reference != receipt['alias_of']
            and previous['reference'] == receipt['alias_of']
            and previous['receipt']['actual_new_forward'] is True
            and _alias_key(previous['receipt']) == key
            and previous['receipt']['raw_logits'] == receipt['raw_logits'] and key in seen_inputs,
            'Only the earlier successful same-role exact-input/class/owner raw may be aliased')
    return key


def validate_raw(raw, receipt, class_ids, vocabulary_size):
    """Independent CPU raw extraction and torch float64 three-class softmax."""
    import numpy as np
    import torch
    require(isinstance(raw, torch.Tensor) and raw.device.type == 'cpu' and raw.ndim == 1
            and raw.dtype == torch.float32 and len(raw) == vocabulary_size == receipt['full_vocabulary_size']
            and bool(torch.isfinite(raw).all()), 'Actual finite CPU full-vocabulary float32 logits required')
    require(len(class_ids) == len(set(class_ids)) == 3
            and all(type(k) is int and 0 <= k < len(raw) for k in class_ids)
            and receipt['class_token_ids'] == class_ids and receipt['raw_dtype'] == 'torch.float32',
            'Actual original0/1/2 token IDs and raw dtype required')
    three = raw[class_ids].double()
    require(np.array_equal(three.numpy(), np.asarray(receipt['class_logits'], dtype=np.float64)),
            'Independent full-vocabulary class-index extraction differs')
    probabilities = torch.softmax(three, dim=0).numpy()
    declared = np.asarray(receipt['probabilities'], dtype=np.float64)
    require(declared.shape == (3,) and np.isfinite(declared).all()
            and np.allclose(probabilities, declared, rtol=0, atol=5e-15)
            and int(np.argmax(probabilities)) == receipt['predicted_index'],
            'Independent float64 three-class softmax/argmax differs')
    return probabilities.tolist()


def _bundle(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'Independent context review must be CPU-only')
    reg_path = root/'context_GPU_registration_29.json'; reg = read(reg_path)
    require(reg['schema'] == 'FROZEN_PAIR200_SOURCE_OVERVIEW_PILOT_V29'
            and bound(reg['review_code']) == Path(__file__).resolve(), 'Exact frozen CPU29 review code required')
    bound(reg['GPU_code']); bound(reg['preparation_code'])
    cpu = read(bound(reg['CPU_registration'])); gate = read(bound(reg['input_acceptance']))
    require(gate['status'] == 'PASS_ALL_NEW_SOURCE_OVERVIEW_CONTEXT_INPUTS'
            and gate['registration'] == reg['CPU_registration'] and gate['TRUE_inputs'] == 295
            and gate['FOREIGN_inputs'] == 40 and gate['inputs'] == 335
            and gate['first_independent_pixels_text_native_owner_QA'] is True
            and gate['actual3video_grids'] is True and gate['old_two_video_QA_substituted'] is False,
            'All335 independent new input QA required')
    require(cpu['schema'] == 'THREE_VIDEO_SOURCE_OVERVIEW_CPU_INPUTS_V28'
            and cpu['preparation_code'] == reg['preparation_code']
            and cpu['training_completion'] == reg['training_completion'], 'Frozen28/29 preparation/final200 binding differs')
    prepared = read(bound(gate['prepared'])); inventory = read(bound(cpu['case_inventory']))
    require(prepared['case_inventory'] == cpu['case_inventory'] and inventory['selected_by_GT_or_scores'] is False
            and prepared['source_catalog'] == cpu['source_catalog']
            and prepared['frozen_primary_role'] == 'PAIR_TRUE' and prepared['remaining_or_production_admitted'] is False,
            'Frozen source-hash-only pilot and primary PAIR role required')
    require(set(prepared['pilot_roles']) == set(ROLES)
            and prepared['pilot_roles']['BASE_TRUE'] == prepared['pilot_roles']['PAIR_TRUE'], 'Identical true-input role manifests required')
    for role in ROLES:
        entries = prepared['pilot_roles'][role]
        require(len(entries) == COUNTS[role] and len({e['id'] for e in entries}) == len(entries)
                and [e['id'] for e in entries] == inventory['pilot_role_ids'][role], 'Exact frozen pilot role IDs/counts required')
    old18 = read(bound(reg['original_GPU18'])); old17 = read(bound(old18['pair_registration']))
    require(cpu['pair_registration'] == old18['pair_registration'] and reg['evaluation_targets'] == old18['evaluation_targets']
            and reg['model_config'] == old17['model_config'] and reg['old_TIME'] == old17['old_TIME_weights'],
            'Original model/TIME/source/CPU-only target chain differs')
    for name in ('pair_common.py', 'pair_preference_math.py'):
        require(sha(root/'pair_code_17'/name) == old17['new_code'][name], 'Frozen original CPU math helper changed')
    old_gate = read(bound(old18['input_acceptance'])); old_prepared = read(bound(old_gate['prepared']))
    catalog = read(bound(prepared['source_catalog']))
    source_hashes = {s['id']: s['source_sha256'] for s in catalog['sources']}
    old_inputs = {e['id']: e for e in old_prepared['dev_inputs']}
    require(len(old_inputs) == 295 and len(old_prepared['dev_source_ids']) == 5, 'Original successful295 inputs required')
    return reg, cpu, prepared, inventory, old_prepared, old_inputs, source_hashes


def _identity(root, reg):
    completion_path = root/'context_model_29/completion.json'; done = read(completion_path)
    require(done['status'] == 'COMPLETE_130_SOURCE_OVERVIEW_PILOT_NOT_QUALITY'
            and done['role_order'] == list(ROLES) and done['completed_receipts'] == done['expected_pilot_forwards'] == 130
            and done['expected_role_counts'] == COUNTS and set(done['stages']) == set(ROLES)
            and done['actual_forward_calls']+done['aliases'] == 130, 'Complete130 context pilot terminal required')
    for key in ('CPU_registration', 'input_acceptance', 'preparation_code', 'original_GPU18', 'training_completion',
                'model_config', 'old_TIME', 'adapter_weights'):
        require(done[key] == reg[key], 'GPU terminal reference differs: '+key)
    require(done['GPU_registration'] == ref(root/'context_GPU_registration_29.json')
            and done['labels_read'] is False and done['new_optimizer_updates'] == 0
            and done['original_TIME_loaded'] is False and done['original_TIME_unchanged'] is True
            and done['adapter_all288_unchanged'] is True and done['independent_adapter_reload_all288_exact'] is True
            and done['automatic_remaining_or_production'] is False, 'Frozen pilot-only identity required')
    training = read(bound(reg['training_completion']))
    require(training['status'] == 'COMPLETE_FIXED_FINAL200_PAIR_COMPARISON_NOT_QUALITY'
            and training['completed_updates'] == 200 and training['successful_micro'] == 800
            and training['adapter_reload_all288_exact'] is True and training['adapter_weights'] == reg['adapter_weights'],
            'Exact complete final200 adapter required')
    bound(reg['adapter_weights']); bound(reg['old_TIME'])
    base = read(bound(done['BASE_identity'])); pair = read(bound(done['PAIR_identity']))
    cfg = read(bound(reg['model_config'])); fingerprint = done['base_fingerprint']
    require(base['base_fingerprint'] == pair['base_fingerprint'] == fingerprint
            and fingerprint['parameters'] == BASE_PARAMETERS and fingerprint['sha256'] == cfg['expected_base_sha256']
            and cfg['base_parameters'] == BASE_PARAMETERS and cfg['b_adapter_sha256'] == reg['old_TIME']['sha256']
            and base['inventory']['base'] == BASE_PARAMETERS and base['inventory']['pair'] == 0
            and base['inventory']['resident'] == BASE_PARAMETERS
            and base['inventory']['conservative_pipeline'] == PIPELINE_PARAMETERS
            and base['original_TIME_loaded'] is False and base['original_TIME'] == reg['old_TIME']
            and base['no_training'] is True, 'Actual original frozen BASE identity differs')
    inv = pair['inventory']
    require(inv == done['inventory'] and inv['base'] == BASE_PARAMETERS and inv['pair'] == PAIR_PARAMETERS
            and inv['resident'] == BASE_PARAMETERS+PAIR_PARAMETERS and inv['conservative_pipeline'] == PIPELINE_PARAMETERS
            and inv['original_TIME_counted'] == 15335424 and inv['semantic_counted'] == 98329
            and inv['actual_lora_matrices'] == 288 and inv['actual_language_targets'] == 144 and inv['adapter'] == 'pair'
            and inv['original_TIME_loaded'] is False and pair['original_TIME_loaded'] is False
            and pair['adapter_weights'] == reg['adapter_weights'] and pair['training_completion'] == reg['training_completion']
            and pair['independent_adapter_reload_all288_exact'] is True and pair['no_training'] is True,
            'Actual readonly PAIR288/whole-pipeline identity differs')
    # Independent header inventory, without loading a model or touching old QA.
    from safetensors import safe_open
    parameters = 0; keys = []
    with safe_open(str(bound(reg['adapter_weights'])), framework='pt', device='cpu') as tensors:
        keys = list(tensors.keys())
        for key in keys:
            shape = tensors.get_slice(key).get_shape()
            require('lora_' in key and len(shape) == 2 and (shape[0] == 8 if '.lora_A.' in key else '.lora_B.' in key and shape[1] == 8),
                    'Independent saved PAIR matrix rank/name differs')
            parameters += shape[0]*shape[1]
    require(len(keys) == 288 and parameters == PAIR_PARAMETERS, 'Independent saved adapter header288/count differs')
    require(not (root/'context_model_29/failure.json').exists(), 'A failed context job cannot become a complete pilot')
    return done, completion_path


def _journal(path, entries, receipts, role, calls):
    rows = [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line]
    allowed = {'BEGIN_FIRST_CONTEXT_FORWARD', 'FIRST_CONTEXT_RAW_PERSISTED', 'ACCEPTED_FIRST_CONTEXT_RESULT'}
    require(all(row['event'] in allowed and row['model_role'] == role for row in rows), 'Unknown/mismatched-role context journal event')
    begins = [r for r in rows if r['event'] == 'BEGIN_FIRST_CONTEXT_FORWARD']
    persisted = [r for r in rows if r['event'] == 'FIRST_CONTEXT_RAW_PERSISTED']
    accepted = [r for r in rows if r['event'] == 'ACCEPTED_FIRST_CONTEXT_RESULT']
    first = {row['id']: row for row in receipts if row['actual_new_forward']}
    require(len(begins) == len(persisted) == calls == len(first)
            and {r['id'] for r in begins} == {r['id'] for r in persisted} == set(first)
            and [r['id'] for r in accepted] == [e['id'] for e in entries]
            and all(r['receipt'] == entry['receipt'] for r, entry in zip(accepted, entries))
            and all(r['raw_logits'] == first[r['id']]['raw_logits'] for r in persisted),
            'Actual first-call/persist/accept journal does not match complete raw receipts')


def qa(root):
    import numpy as np
    import torch
    torch.set_num_threads(2)
    reg, cpu, prepared, inventory, old_prepared, old_inputs, hashes = _bundle(root)
    done, completion_path = _identity(root, reg)
    out = root/'context_output_QA_29'; out.mkdir(exist_ok=False)
    save(out/'claim.json', dict(utc=utc(), GPU_completion=ref(completion_path), review_code=reg['review_code'],
                               old_successful_output_QA_repeated=False, labels_read=False))
    exports = {}; stage_refs = {}; actual = aliases = 0
    specifications = {row['id']: row for row in inventory['inputs']}
    try:
        for role in ROLES:
            stage = read(bound(done['stages'][role])); expected = prepared['pilot_roles'][role]
            require(bound(done['stages'][role]) == (root/'context_model_29'/role/'completion.json').resolve()
                    and stage['status'] == 'COMPLETE_ALL_ROLE_INPUTS_RAW_LOGITS_NOT_QUALITY'
                    and stage['model_role'] == role and stage['weights_role'] == ('BASE' if role == 'BASE_TRUE' else 'PAIR200')
                    and len(stage['entries']) == stage['expected_inputs'] == len(expected)
                    and stage['full_vocabulary_size'] == done['full_vocabulary_size'], 'Exact completed pilot stage required')
            require(stage['inventory'] == (read(bound(done['BASE_identity']))['inventory'] if role == 'BASE_TRUE' else done['inventory'])
                    and stage['input_acceptance'] == reg['input_acceptance'] and stage['CPU_registration'] == reg['CPU_registration']
                    and stage['GPU_registration'] == done['GPU_registration'] and stage['training_completion'] == reg['training_completion']
                    and stage['labels_read'] is False and stage['original_TIME_loaded'] is False
                    and stage['new_optimizer_updates'] == 0, 'Stage inventory/frozen evidence differs')
            seen, priors, seen_inputs, raw_paths, predictions, receipts = set(), {}, set(), set(), [], []
            calls = alias_count = 0
            for row, entry in zip(stage['entries'], expected):
                require(row['id'] == entry['id'] and row['id'] not in seen and row['input'] == entry['inputref'],
                        'Exact frozen input order/owner and one result per input required')
                request = read(bound(row['input'])); receipt = read(bound(row['receipt']))
                spec = specifications[row['id']]; oid = request['original_case_id']; old = old_inputs[oid]
                require(spec['original_case_id'] == oid and spec['source_id'] == request['source_id'] == entry['source_id']
                        and spec['overview_source_id'] == request['overview_source_id']
                        and spec['overview_is_foreign'] is request['overview_is_foreign']
                        and request['old_input'] == old['input'], 'Case-inventory/original-input join differs')
                require(receipt['id'] == request['id'] == row['id'] and receipt['original_case_id'] == oid
                        and receipt['input'] == row['input'] and _owners(receipt) == _owners(request)
                        and receipt['source_sha256'] == hashes[request['source_id']]
                        and receipt['overview_source_sha256'] == hashes[request['overview_source_id']]
                        and receipt['model_role'] == role and receipt['weights_role'] == stage['weights_role']
                        and receipt['input_signature'] == request['input_signature']
                        and receipt['class_token_ids'] == request['class_token_ids'] == old_prepared['class_token_ids']
                        and receipt['labels_read'] is False and receipt['new_optimizer_updates'] == 0
                        and receipt['original_TIME_loaded'] is False, 'Actual output/source/overview/class/weight identity differs')
                foreign = role == 'PAIR_FOREIGN'
                require(request['overview_is_foreign'] is foreign
                        and ((request['overview_source_id'] != request['source_id'] and request['overview_source_sha256'] != request['source_sha256'])
                             if foreign else (request['overview_source_id'] == request['source_id'] and request['overview_source_sha256'] == request['source_sha256'])),
                        'Foreign source identity cannot be disguised as native context')
                old_request = read(bound(old['input']))
                require(request['clip_ranges'] == old_request['clip_ranges']
                        and request['no_GT_or_label_in_prompt'] is True, 'A/B cases must stay original and label-free')
                tokens = torch.load(bound(request['tokens']), map_location='cpu', weights_only=True)
                require(set(tokens) == {'input_ids', 'attention_mask'}
                        and signature(tokens) == {k: request['input_signature'][k] for k in tokens}
                        and tokens['input_ids'].dtype == tokens['attention_mask'].dtype == torch.int64
                        and tokens['input_ids'].shape == tokens['attention_mask'].shape
                        and tokens['input_ids'].ndim == 2 and tokens['input_ids'].shape[0] == 1
                        and bool((tokens['attention_mask'] == 1).all()), 'Actual unpadded prefix token binding differs')
                grid = torch.tensor(request['video_grid_thw'], dtype=torch.int64)
                require(tuple(grid.shape) == (3, 3) and bool((grid > 0).all()) and bool((grid[:, 1:] % 2 == 0).all())
                        and 1 <= int(grid[0, 0]) <= 32 and int(grid[1, 0]) == int(grid[2, 0]) == 4
                        and signature({'video_grid_thw': grid})['video_grid_thw'] == request['input_signature']['video_grid_thw'],
                        'Actual accepted Overview/A/B grid tensor signature differs')
                prefix_length = int(tokens['input_ids'].shape[1])
                require(prefix_length == request['text_evidence']['sequence_tokens'] and 0 < prefix_length <= 4096
                        and request['text_evidence']['video_grids'] == grid.tolist(), 'Actual prefix length/grid text evidence differs')
                raw = torch.load(bound(receipt['raw_logits']), map_location='cpu', weights_only=True)
                probabilities = validate_raw(raw, receipt, request['class_token_ids'], done['full_vocabulary_size'])
                key = validate_alias(receipt, row['receipt'], priors, seen_inputs)
                if receipt['actual_new_forward']:
                    require(receipt['raw_logits']['path'] not in raw_paths, 'Independent new calls need independent first raw files')
                    calls += 1; raw_paths.add(receipt['raw_logits']['path'])
                else:
                    alias_count += 1
                seen_inputs.add(key); priors[row['receipt']['path']] = dict(reference=row['receipt'], receipt=receipt)
                seen.add(row['id']); receipts.append(receipt)
                predictions.append(dict(id=row['id'], original_case_id=oid, input=row['input'], receipt=row['receipt'],
                    probabilities=probabilities, model_role=role, prefix_tokens=prefix_length,
                    video_grid_thw=grid.tolist(), overview_timestamps=request['video_metadata'][0]['timestamps_exact'], **_owners(request)))
            require(calls == stage['actual_forward_calls'] and alias_count == stage['aliases'] and calls+alias_count == len(expected),
                    'First actual-call/alias counts differ')
            journal = root/'context_model_29'/role/'attempts.jsonl'
            _journal(journal, stage['entries'], receipts, role, calls)
            path = out/(role+'.json')
            save(path, dict(status='PASS_FIRST_ALL_RAW_LOGIT_INPUT_ROLE_QA', role=role, completion=done['stages'][role],
                predictions=predictions, inputs=len(predictions), actual_new_forwards=calls, exact_input_aliases=alias_count,
                attempts=ref(journal), new_model_calls=0, dev_GT_read=False))
            exports[role] = predictions; stage_refs[role] = ref(path); actual += calls; aliases += alias_count
        require(actual == done['actual_forward_calls'] and aliases == done['aliases'] and actual+aliases == 130
                and not torch.cuda.is_initialized(), 'Independent all130 role/raw/count QA must be CPU-only')
        save(root/'context_output_acceptance_29.json', dict(status='PASS_FIRST_ALL130_CONTEXT_RAW_ROLE_OWNER_QA',
            GPU_completion=ref(completion_path), GPU_registration=done['GPU_registration'], input_acceptance=reg['input_acceptance'],
            stages=stage_refs, predictions=exports, inputs=130, actual_new_forwards=actual, exact_input_aliases=aliases,
            base_fingerprint=done['base_fingerprint'], inventory=done['inventory'], adapter_weights=reg['adapter_weights'],
            independent_adapter_header_matrices=288, independent_adapter_header_parameters=PAIR_PARAMETERS,
            old_successful_output_QA_repeated=False, dev_GT_read=False, new_model_calls=0, remaining_TRUE_pair_admitted=False,
            production_prepare_approved=False))
    except BaseException as error:
        save(out/'failure.json', dict(error=repr(error), traceback=traceback.format_exc(), stages_completed=stage_refs,
                                    preserve_all_success=True, no_automatic_retry=True, new_model_calls=0))
        raise


def select_pilot_targets(evaluation_targets, true_original_ids, foreign_original_ids, source_ids):
    """Join by original IDs, never labels or scores; reject half-present pairs."""
    true_ids, foreign_ids = set(true_original_ids), set(foreign_original_ids)
    generic, controls, used = [], [], set()
    for row in evaluation_targets['pairs']:
        if row['purpose'] not in ('FIXED_GENERIC_PAIR', 'IDENTICAL_CLIP_TIE_CONTROL'):
            continue
        first, reverse = row['first_id'], row['reverse_id']
        present = (first in true_ids, reverse in true_ids)
        require(present[0] == present[1], 'Both original orders must belong to the frozen pilot')
        if not present[0]:
            continue
        require(row['source_id'] in source_ids, 'Unexpected source in pilot target join')
        if row['purpose'] == 'FIXED_GENERIC_PAIR':
            require(row['same_clip'] is False and first != reverse, 'Original generic unordered pair required')
            generic.append(row)
        else:
            require(row['same_clip'] is True and first == reverse and row['target'] == [0., 0., 1.], 'Original self TIE identity required')
            controls.append(row)
        used.update((first, reverse))
    require(len(generic) == 20 and len(controls) == 5 and used == true_ids
            and {r['first_id'] for r in generic} | {r['reverse_id'] for r in generic} == foreign_ids,
            'Exactly frozen20 generic pairs/5self and40 foreign orders required')
    for sid in source_ids:
        require(sum(row['source_id'] == sid for row in generic) == 4
                and sum(row['source_id'] == sid for row in controls) == 1, 'Four generic pairs and one self control per source required')
    return generic, controls


def compare_predictions(generic, controls, predictions, source_ids):
    """Pure fixed source-equal metrics and prespecified primary admission bits."""
    import numpy as np
    names = ('OLD_BASE_LOCAL', 'OLD_PAIR_LOCAL', 'BASE_TRUE', 'TRAIN_SOURCE_EQUAL_PRIOR', 'PAIR_TRUE', 'PAIR_FOREIGN')
    require(set(predictions) == set(names) and len(source_ids) == len(set(source_ids)) == 5, 'Exact six comparisons/five sources required')
    metrics = {}
    for name in names:
        scores = predictions[name]
        categories = {}
        for label, rows in (('generic', generic), ('self', [] if name == 'PAIR_FOREIGN' else controls)):
            records = {sid: [] for sid in source_ids}
            for row in rows:
                records[row['source_id']].append(dict(target=row['target'], first_order=scores[row['first_id']],
                    reverse_order=scores[row['reverse_id']], same_clip=row['same_clip']))
            categories[label] = source_metrics(records)
        variation = {}
        for sid in source_ids:
            values = np.asarray([(np.asarray(scores[row['first_id']], dtype=np.float64)+
                                  np.asarray(scores[row['reverse_id']], dtype=np.float64)[[1, 0, 2]])/2
                                 for row in generic if row['source_id'] == sid], dtype=np.float64)
            variation[sid] = dict(mapped_pair_mean_class_probability_ranges=np.ptp(values, axis=0).tolist(),
                exact_unique_probability_vectors=len({tuple(v) for v in values.tolist()}),
                constant_within_source=bool(np.all(values == values[0])))
        categories['nonconstant_behavior'] = variation
        metrics[name] = categories
    primary = metrics['PAIR_TRUE']['generic']; old = metrics['OLD_PAIR_LOCAL']['generic']
    constant = metrics['TRAIN_SOURCE_EQUAL_PRIOR']['generic']; foreign = metrics['PAIR_FOREIGN']['generic']
    primary_mean = primary['macro']['distribution_brier']
    vs_old, vs_foreign = {}, {}
    for sid in source_ids:
        value = primary['per_source'][sid]['distribution_brier']
        vs_old[sid] = value-old['per_source'][sid]['distribution_brier']
        vs_foreign[sid] = value-foreign['per_source'][sid]['distribution_brier']
    self_rows = metrics['PAIR_TRUE']['self']['per_source']
    checks = dict(primary_beats_old_PAIR_macro=primary_mean < old['macro']['distribution_brier'],
        primary_beats_train_constant_macro=primary_mean < constant['macro']['distribution_brier'],
        at_least3_sources_beat_old_PAIR=sum(v < 0 for v in vs_old.values()) >= 3,
        primary_beats_foreign_macro=primary_mean < foreign['macro']['distribution_brier'],
        at_least3_sources_favor_true_context=sum(v < 0 for v in vs_foreign.values()) >= 3,
        all5_self_controls_strict_TIE=all(row['same_clip_controls'] == 1
            and row['same_clip_tie_strict_argmax_both_fraction'] == 1. for row in self_rows.values()))
    return dict(metrics=metrics, primary_role='PAIR_TRUE', checks=checks,
        per_source_primary_minus_old_PAIR=vs_old, per_source_primary_minus_foreign=vs_foreign,
        primary_macro_minus_old_PAIR=primary_mean-old['macro']['distribution_brier'],
        primary_macro_minus_constant=primary_mean-constant['macro']['distribution_brier'],
        primary_macro_minus_foreign=primary_mean-foreign['macro']['distribution_brier'],
        remaining_TRUE_pair_admitted=all(checks.values()), production_prepare_approved=False,
        status='PASS_FOCUSED_CONTEXT_PILOT_ONLY' if all(checks.values()) else 'STOP_CONTEXT_PILOT_NO_REMAINING')


def prefix_differences(true_rows, foreign_rows):
    """Report text-length/timestamp confounding rather than assume pixel-only."""
    rows = []
    for oid, foreign in foreign_rows.items():
        require(oid in true_rows, 'Foreign original case absent from true context')
        true = true_rows[oid]
        require(true['source_id'] == foreign['source_id'] and true['video_grid_thw'] == foreign['video_grid_thw'],
                'Foreign control must retain same actual local owner and full visual-grid lengths')
        rows.append(dict(original_case_id=oid, source_id=true['source_id'], true_prefix_tokens=true['prefix_tokens'],
            foreign_prefix_tokens=foreign['prefix_tokens'], true_minus_foreign_prefix_tokens=true['prefix_tokens']-foreign['prefix_tokens'],
            overview_timestamps_equal=true['overview_timestamps'] == foreign['overview_timestamps'], grids_equal=True,
            true_input=true['input'], foreign_input=foreign['input']))
    return rows


def evaluate(root):
    import numpy as np
    import torch
    torch.set_num_threads(2)
    reg, cpu, prepared, inventory, old_prepared, old_inputs, hashes = _bundle(root)
    acceptance_path = root/'context_output_acceptance_29.json'; accepted = read(acceptance_path)
    require(accepted['status'] == 'PASS_FIRST_ALL130_CONTEXT_RAW_ROLE_OWNER_QA'
            and accepted['GPU_registration'] == ref(root/'context_GPU_registration_29.json') and accepted['inputs'] == 130,
            'Successful first independent new output QA must precede reference comparison')
    old_acceptances = {}
    training = read(bound(reg['training_completion']))
    for role, key in (('BASE', 'old_BASE_acceptance'), ('TRAINED', 'old_PAIR_acceptance')):
        adopted = read(bound(reg[key]))
        require(adopted['status'] == 'PASS_FIRST_ALL_RAW_LOGIT_INPUT_ROLE_QA' and adopted['role'] == role
                and adopted['inputs'] == 295 and len(adopted['predictions']) == 295
                and adopted['completion'] == training['BASE_completion' if role == 'BASE' else 'TRAINED_completion']
                and {row['id'] for row in adopted['predictions']} == set(old_inputs)
                and all(row['input'] == old_inputs[row['id']]['input'] for row in adopted['predictions']),
                'Exact original successful local-output QA must be adopted without rerunning it')
        old_acceptances[role] = adopted
    labels = read(bound(reg['evaluation_targets']))
    maps, rows_by_original = {}, {}
    for role in ROLES:
        rows = accepted['predictions'][role]
        require(len(rows) == COUNTS[role] and len({r['original_case_id'] for r in rows}) == len(rows), 'Unique original-case output mapping required')
        rows_by_original[role] = {r['original_case_id']: r for r in rows}
        maps[role] = {r['original_case_id']: r['probabilities'] for r in rows}
    require(set(maps['BASE_TRUE']) == set(maps['PAIR_TRUE']), 'Same local A/B pilot in both true model roles required')
    source_ids = old_prepared['dev_source_ids']
    generic, controls = select_pilot_targets(labels, maps['PAIR_TRUE'], maps['PAIR_FOREIGN'], source_ids)
    train = read(bound(old_prepared['train_targets'])); by_source = {sid: [] for sid in old_prepared['train_source_ids']}
    for row in train:
        require(row['source_id'] in by_source, 'Train-only constant prior cannot receive dev targets')
        by_source[row['source_id']].append(row['target'])
    require(len(by_source) == 20 and all(by_source.values()), 'Every original training source contributes equally to prior')
    prior = np.mean([np.mean(values, axis=0) for values in by_source.values()], axis=0)
    for role, name in (('BASE', 'OLD_BASE_LOCAL'), ('TRAINED', 'OLD_PAIR_LOCAL')):
        maps[name] = {r['id']: r['probabilities'] for r in old_acceptances[role]['predictions']}
    maps['TRAIN_SOURCE_EQUAL_PRIOR'] = {oid: prior.tolist() for oid in maps['PAIR_TRUE']}
    result = compare_predictions(generic, controls, maps, source_ids)
    prefix = prefix_differences(rows_by_original['PAIR_TRUE'], rows_by_original['PAIR_FOREIGN'])
    out = root/'context_comparison_29'; out.mkdir(exist_ok=False)
    result.update(output_acceptance=ref(acceptance_path), GPU_registration=ref(root/'context_GPU_registration_29.json'),
        review_code=reg['review_code'], evaluation_targets=reg['evaluation_targets'], case_inventory=cpu['case_inventory'],
        adopted_old_BASE_acceptance=reg['old_BASE_acceptance'], adopted_old_PAIR_acceptance=reg['old_PAIR_acceptance'],
        train_prior=prior.tolist(), generic_unordered_pairs=20, generic_ordered_inputs=40, same_clip_controls=5,
        actual_prefix_length_differences=prefix, pure_pixel_only_foreign_control=False,
        foreign_control_limitation='Overview donor uses its own real timestamps; text/token lengths may differ. No pure visual causality claim.',
        historical_exposure=True, independent_blind_confirmation=False, official_joint_metric=False,
        fixed_PRIMARY_not_switched_to_BASE=True, old_successful_QA_repeated=False, new_model_calls=0,
        new_training_updates=0, automatic_remaining_execution=False, production_prepare_approved=False)
    save(out/'result.json', result)
    require(not torch.cuda.is_initialized(), 'CPU comparison must never initialize CUDA')
    return result


def run(root):
    qa(root)
    return evaluate(root)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', nargs='?', choices=('run', 'qa', 'evaluate'), default='run')
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    {'run': run, 'qa': qa, 'evaluate': evaluate}[args.mode](args.root)
