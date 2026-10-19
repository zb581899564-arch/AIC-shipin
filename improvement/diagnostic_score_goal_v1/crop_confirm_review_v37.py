"""First confirm19 raw QA and fixed native-IoU comparison; CPU only."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'pair_code_17'))
from pair_common import read, save, ref, bound, require, utc


def module(reference, name):
    path = bound(reference)
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def run(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'Independent CPU review only')
    import numpy as np
    import torch
    regpath = root/'crop_confirm_GPU_registration_37.json'
    reg = read(regpath)
    require(bound(reg['review_code']) == Path(__file__).resolve(), 'Exact independent review entry')
    gpu_done = read(root/'crop_confirm_model_37/completion.json')
    require(gpu_done['status'] == 'COMPLETE_FIXED_FINAL500_NATIVE_CONFIRM19_RAW_NOT_QUALITY'
            and gpu_done['registration'] == ref(regpath), 'Natural complete fixed-weight confirm required')
    resource = read(root/'crop_confirm_resource_37.json')
    require(resource['unique_ledger_entries'] == 1 and resource['record']['status'] == 'completed'
            and resource['record']['exit_code'] == 0, 'Unique natural shared GPU terminal before first review')
    gate = read(bound(reg['input_acceptance']))
    prepared = read(bound(gate['prepared']))
    entries = {e['id']: e for e in prepared['confirm_inputs']}
    catalog = read(bound(prepared['source_catalog']))
    targets = read(bound(prepared['CPU_targets']))
    plan = read(bound(prepared['case_plan']))
    sources = {s['source_id']: s for s in catalog['sources']}
    target = {s['source_id']: s for s in targets['sources']}
    require(len(sources) == 19 and set(sources) == set(target), 'Exactly19 source-bound original references')
    qa = module(reg['raw_review_helper'], '_frozen_crop_raw_qa33_confirm37')
    qa._inventory(gpu_done, read(bound(reg['model_config'])))
    training = read(bound(reg['native_training_completion']))
    require(gpu_done['base_fingerprint'] == training['base_fingerprint']
            and gpu_done['adapter_weights'] == reg['adapter_weights'] == training['adapter_weights']
            and gpu_done['original_TIME_loaded'] is False and gpu_done['old_PAIR_loaded'] is False,
            'Actual confirm BASE/final-adapter and whole-pipeline inventory differ')
    policy = module(reg['policy_code'], '_frozen_crop_policy33_confirm37')
    geometry = module(reg['geometry_code'], '_frozen_crop_geometry31_confirm37')
    original = read(bound(reg['native_screen_result']))
    require(original['status'] == 'PASS_NATIVE_CROP_SCREEN_ONLY' and original['confirm_admitted'] is True,
            'Native screen qualification must precede this confirmation')
    control_receipt = read(bound(original['geometry_control']))
    with np.load(bound(control_receipt['coefficients']), allow_pickle=False) as z:
        coefficients = z['beta'].copy()
    require(coefficients.shape == (13,) and control_receipt['new_fits'] == 1,
            'Adopt only original train602 geometry control; no refit on confirm')
    out = root/'crop_confirm_comparison_37'
    out.mkdir(exist_ok=False)
    save(out/'claim.json', dict(utc=utc(), registration=ref(regpath), first_confirm_QA=True,
        old_input_QA_repeated=False, old_screen_raw_QA_repeated=False, new_fits=0))
    try:
        for sid, source in sources.items():
            t = target[sid]
            require(t['source_sha256'] == source['source_sha256'] and t['reference_modified'] is False,
                    'Confirm source/reference identity differs')
            expected = [geometry.crop_iou(b, t['original_reference_xywh']) for b in source['pool']]
            require(np.array_equal(expected, t['candidate_ious']), 'Native original-reference IoU differs')
        exports = {}
        reports = {}
        actual = 0
        for role in ('BASE', 'TRAINED'):
            completion_ref = gpu_done[role+'_completion']
            completion = read(bound(completion_ref))
            require(completion['status'] == 'COMPLETE_ALL_ROLE_INPUTS_RAW_LOGITS_NOT_QUALITY'
                    and {e['id'] for e in completion['entries']} == set(entries)
                    and len(completion['entries']) == len(entries), 'Complete unique confirm raw inventory')
            probabilities = {}
            receipts = []
            raw_receipts = []
            seen = set()
            previous = {}
            calls = aliases = 0
            raw_paths = set()
            for item in completion['entries']:
                entry = entries[item['id']]
                receipt = read(bound(item['receipt']))
                request = read(bound(entry['input']))
                require(receipt['input'] == entry['input'] and receipt['id'] == entry['id']
                        and receipt['source_id'] == request['source_id'] == entry['source_id']
                        and receipt['source_sha256'] == request['source_sha256']
                        and receipt['input_signature'] == request['input_signature']
                        and receipt['model_role'] == role+'_confirm', 'Actual raw/input/source/role binding differs')
                raw = torch.load(bound(receipt['raw_logits']), map_location='cpu', weights_only=True)
                probability = qa.validate_raw(raw, receipt, prepared['class_token_ids'], completion['full_vocabulary_size'])
                key = qa.validate_alias(receipt, item['receipt'], previous, seen)
                if receipt['actual_new_forward']:
                    require(receipt['raw_logits']['path'] not in raw_paths, 'New calls need distinct persisted raw files')
                    calls += 1
                    raw_paths.add(receipt['raw_logits']['path'])
                else:
                    aliases += 1
                seen.add(key)
                previous[item['receipt']['path']] = dict(reference=item['receipt'], receipt=receipt)
                probabilities[item['id']] = probability
                receipts.append(dict(id=item['id'], receipt=item['receipt'], probabilities3=probability))
                raw_receipts.append(receipt)
            require(calls == completion['actual_forward_calls'] and aliases == completion['aliases']
                    and calls+aliases == len(entries), 'Actual raw call and alias counts differ')
            journal = bound(completion_ref).parent/'attempts.jsonl'
            events = [json.loads(line) for line in journal.read_text().splitlines() if line]
            begins = [e for e in events if e['event'] == 'BEGIN_NEW_ROLE_FORWARD']
            persisted = [e for e in events if e['event'] == 'FIRST_RAW_PERSISTED']
            accepted = [e for e in events if e['event'] == 'ACCEPTED_NEW_ROLE_RESULT']
            first = {row['id']: row for row in raw_receipts if row['actual_new_forward']}
            require(len(events) == 2*calls+len(entries)
                    and all(e['model_role'] == role+'_confirm' for e in events)
                    and len(begins) == len(persisted) == calls
                    and {e['id'] for e in begins} == {e['id'] for e in persisted} == set(first)
                    and all(e['raw_logits'] == first[e['id']]['raw_logits'] for e in persisted)
                    and [e['id'] for e in accepted] == [e['id'] for e in completion['entries']]
                    and all(e['receipt'] == item['receipt'] for e, item in zip(accepted, completion['entries'])),
                    'Actual begin/persist/accept journal differs from complete raw results')
            actual += calls
            rows = []
            self_tie = 0
            for sid, source in sources.items():
                pairs = []
                own = []
                for pair in plan['pair_index']:
                    if pair['source_id'] != sid:
                        continue
                    if pair['same_crop']:
                        own.append(probabilities[pair['first_id']])
                    else:
                        pairs.append(dict(candidate_index=pair['candidate_index'],
                            forward_probs=probabilities[pair['first_id']], reverse_probs=probabilities[pair['reverse_id']]))
                require(len(own) == 1, 'One explicit samecrop control per source')
                self_tie += int(policy.strict_tie(own[0]))
                chosen = policy.select_pool(source['pool'], 0, pairs)
                control = policy.geometry_select(source['pool'], source['width'], source['height'], coefficients, 0)
                ious = target[sid]['candidate_ious']
                rows.append(dict(source_id=sid, baseline_iou=ious[0], selected_iou=ious[chosen],
                    geometry_iou=ious[control], oracle_iou=max(ious), baseline_index=0,
                    selected_index=chosen, baseline_box=source['pool'][0], selected_box=source['pool'][chosen]))
            summary = policy.summarize(rows)
            reports[role] = dict(summary=summary, quality=policy.quality_checks(summary, 'confirm19', self_tie, 0),
                self_tie_count=self_tie, accepted_predictions=receipts)
            exports[role] = rows
        admitted = reports['TRAINED']['quality']['admitted']
        save(out/'result.json', dict(status='PASS_NATIVE_CROP_CONFIRM19_RESEARCH_ONLY' if admitted else 'STOP_NATIVE_CROP_CONFIRM19',
            primary='TRAINED', reports=reports, selected=exports, native_research_qualified=admitted,
            production_prepare_approved=False, requires_production_observation_profile_qualification=True,
            actual_new_model_calls=actual, new_fits=0, new_training_updates=0,
            GPU_completion=ref(root/'crop_confirm_model_37/completion.json'), resource=ref(root/'crop_confirm_resource_37.json'),
            registration=ref(regpath), adapter_weights=reg['adapter_weights'], original20_complete=False,
            excluded_missing_source_repeated=False, historical_exposure=True, new_blind_sources=0,
            scope='STATIC_NATIVE16_SINGLE_EDITOR_REFERENCE_NOT_OFFICIAL_JOINT_OR_VIDEO_QUALITY'))
        print('NATIVE_CONFIRM19', admitted, reports['TRAINED']['summary'], flush=True)
    except BaseException as error:
        save(out/'failure.json', dict(error=repr(error), traceback=traceback.format_exc(),
            preserve_all_success=True, automatic_retry=False))
        raise


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    run(p.parse_args().root)
