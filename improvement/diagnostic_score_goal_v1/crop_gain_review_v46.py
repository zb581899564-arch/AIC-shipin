"""First raw QA for the separately registered utility-training readouts."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'pair_code_17'))
from pair_common import read, save, ref, bound, require, signature, utc


def module(reference, name):
    path = bound(reference)
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def run(root, phase):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '' and phase in ('pilot128', 'remaining2280'),
            'Explicit first CPU raw review phase')
    import torch
    torch.set_num_threads(2)
    original_path = root/'crop_gain_GPU_registration_46.json'
    original = read(original_path)
    regpath = original_path if phase == 'pilot128' else root/'crop_gain_remaining_admission_46.json'
    reg = read(regpath)
    require(bound(original['review_code']) == Path(__file__).resolve(), 'Exact first new raw review')
    done_path = root/'crop_gain_model_46'/(phase+'_completion.json')
    done = read(done_path)
    require(done['status'] == 'COMPLETE_FIRST_FINAL500_GAIN_TRAIN_RAW_NOT_QUALITY'
            and done['phase'] == phase and done['GPU_registration'] == ref(regpath)
            and done['original_GPU_registration'] == ref(original_path)
            and done['new_optimizer_updates'] == 0 and done['training_targets_read'] is False,
            'Readonly exact final500 phase completion')
    resource = read(root/('crop_gain_'+phase+'_resource_46.json'))
    require(resource['unique_ledger_entries'] == 1 and resource['record']['status'] == 'completed'
            and resource['record']['exit_code'] == 0, 'Unique natural shared GPU terminal')
    gate = read(bound(original['input_acceptance']))
    prepared = read(bound(gate['prepared']))
    expected = prepared['pilot_inputs' if phase == 'pilot128' else 'remaining_inputs']
    by_id = {entry['id']: entry for entry in expected}
    require(len(by_id) == len(expected) == (128 if phase == 'pilot128' else 2280), 'Exact phase input IDs')
    catalog = read(bound(prepared['source_catalog']))
    sources = {s['source_id']: s for s in catalog['sources']}
    qa = module(original['raw_review_helper'], '_frozen_crop_raw_review33_gain46')
    qa._inventory(done, read(bound(original['model_config'])))
    training = read(bound(original['fixed_training_completion']))
    require(done['base_fingerprint'] == training['base_fingerprint']
            and done['adapter_weights'] == original['adapter_weights'] == training['adapter_weights'],
            'Actual BASE and immutable final500 identity')
    completion = read(bound(done['completion']))
    require(completion['status'] == 'COMPLETE_ALL_ROLE_INPUTS_RAW_LOGITS_NOT_QUALITY'
            and completion['expected_inputs'] == len(expected)
            and {entry['id'] for entry in completion['entries']} == set(by_id), 'Complete phase raw inventory')
    out = root/('crop_gain_first_QA_'+phase+'_46')
    out.mkdir(exist_ok=False)
    save(out/'claim.json', dict(utc=utc(), GPU_registration=ref(regpath), old_raw_QA_repeated=False,
        old_image_processor_repeated=False, training_targets_read=False))
    try:
        calls = aliases = 0
        seen = set()
        raw_paths = set()
        previous = {}
        receipts = []
        predictions = []
        for item in completion['entries']:
            entry = by_id[item['id']]
            request = read(bound(entry['input']))
            receipt = read(bound(item['receipt']))
            source = sources[request['source_id']]
            require(source['role'] == request['role'] == 'train'
                    and source['source_sha256'] == request['source_sha256'] == receipt['source_sha256']
                    and receipt['source_id'] == entry['source_id'] == request['source_id']
                    and request['id'] == receipt['id'] == entry['id']
                    and receipt['input'] == entry['input'] == item['input']
                    and receipt['input_signature'] == request['input_signature']
                    and receipt['model_role'] == 'GAIN_'+phase
                    and receipt['screen_reference_read'] is False
                    and request['reference_or_target_in_prompt'] is False,
                    'Exact source/role/request/signature bindings')
            require(set(request['input_signature']) == {'input_ids', 'attention_mask', 'pixel_values', 'image_grid_thw'},
                    'Only four consumed tensors, no target tensor')
            grid = torch.tensor(request['image_grid_thw'], dtype=torch.int64)
            require(grid.shape == (3, 3) and bool((grid[:, 0] == 1).all())
                    and signature({'image_grid_thw': grid})['image_grid_thw'] == request['input_signature']['image_grid_thw'],
                    'Actual accepted three-image grid')
            raw = torch.load(bound(receipt['raw_logits']), map_location='cpu', weights_only=True)
            probabilities = qa.validate_raw(raw, receipt, prepared['class_token_ids'], completion['full_vocabulary_size'])
            key = qa.validate_alias(receipt, item['receipt'], previous, seen)
            if receipt['actual_new_forward']:
                require(receipt['raw_logits']['path'] not in raw_paths, 'Distinct first raw for each real call')
                calls += 1
                raw_paths.add(receipt['raw_logits']['path'])
            else:
                aliases += 1
            seen.add(key)
            previous[item['receipt']['path']] = dict(reference=item['receipt'], receipt=receipt)
            receipts.append(receipt)
            predictions.append(dict(id=entry['id'], source_id=request['source_id'], source_sha256=request['source_sha256'],
                input=entry['input'], receipt=item['receipt'], class_logits3=receipt['class_logits'],
                probabilities3=probabilities, adapter_weights=original['adapter_weights']))
        require(calls == completion['actual_forward_calls'] and aliases == completion['aliases']
                and calls+aliases == len(expected), 'Actual call/alias totals')
        journal = bound(done['completion']).parent/'attempts.jsonl'
        events = [json.loads(line) for line in journal.read_text().splitlines() if line]
        begins = [e for e in events if e['event'] == 'BEGIN_NEW_ROLE_FORWARD']
        persisted = [e for e in events if e['event'] == 'FIRST_RAW_PERSISTED']
        accepted = [e for e in events if e['event'] == 'ACCEPTED_NEW_ROLE_RESULT']
        first = {item['id']: item for item in receipts if item['actual_new_forward']}
        require(len(events) == 2*calls+len(expected)
                and all(e['model_role'] == 'GAIN_'+phase for e in events)
                and len(begins) == len(persisted) == calls
                and {e['id'] for e in begins} == {e['id'] for e in persisted} == set(first)
                and all(e['raw_logits'] == first[e['id']]['raw_logits'] for e in persisted)
                and [e['id'] for e in accepted] == [e['id'] for e in completion['entries']]
                and all(e['receipt'] == item['receipt'] for e, item in zip(accepted, completion['entries'])),
                'Actual ordered begin/persist/accept journal')
        require(not torch.cuda.is_initialized(), 'CPU QA cannot initialize CUDA')
        save(root/('crop_gain_'+phase+'_output_acceptance_46.json'), dict(
            status='PASS_GAIN_PILOT128_FIRST_RAW_QA' if phase == 'pilot128' else 'PASS_GAIN_REMAINING2280_FIRST_RAW_QA',
            phase=phase, GPU_registration=ref(regpath), original_GPU_registration=ref(original_path),
            completion=ref(done_path), predictions=predictions, actual_new_forwards=calls, aliases=aliases,
            distinct_sources=len({e['source_id'] for e in expected}), inventory=done['inventory'],
            base_fingerprint=done['base_fingerprint'], adapter_weights=original['adapter_weights'],
            attempts=ref(journal), no_utility_targets_read=True, new_model_calls=0,
            fitting_admitted=False, quality_established=False, production_admitted=False))
    except BaseException as error:
        save(out/'failure.json', dict(utc=utc(), error=repr(error), traceback=traceback.format_exc(),
            preserve_all_success=True, automatic_retry=False))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--phase', choices=['pilot128', 'remaining2280'], required=True)
    args = parser.parse_args()
    run(args.root, args.phase)
