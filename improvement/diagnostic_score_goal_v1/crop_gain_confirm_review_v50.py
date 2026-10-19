"""First CPU raw review of new gain native19, without labels or policy scoring."""
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
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def run(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'Independent first raw QA is CPU only')
    import torch
    torch.set_num_threads(2)
    regpath = root/'crop_gain_confirm_GPU_registration_50.json'
    reg = read(regpath)
    require(bound(reg['review_code']) == Path(__file__).resolve(), 'Exact first native gain review entry')
    reader = module(reg['reader_code'], '_gain_native19_reader49_QA')
    gate = read(bound(reg['input_acceptance']))
    require(gate['status'] == reader.GATE and gate['registration'] == reg['CPU_registration']
            and gate['sources'] == 19 and gate['original20_complete'] is False, 'Actual full first CPU gate required')
    prepared = read(bound(gate['prepared']))
    expected = prepared['confirm_inputs']
    by_id = {item['id']: item for item in expected}
    sources = {s['source_id']: s for s in read(bound(prepared['source_catalog']))['sources']}
    require(len(expected) == len(by_id) == gate['inputs'] and len(sources) == 19
            and 'gnmc:test:006575.jpeg' not in sources, 'Exact remaining19 inventory')
    donepath = root/'crop_gain_confirm_model_50/completion.json'
    done = read(donepath)
    require(done['status'] == 'COMPLETE_GAIN_NATIVE19_FIRST_RAW_NOT_QUALITY'
            and done['GPU_registration'] == ref(regpath) and done['input_acceptance'] == reg['input_acceptance']
            and done['critic_weights'] == reg['critic_weights'] and done['adapter_weights'] == reg['adapter_weights']
            and done['new_optimizer_updates'] == 0 and done['training_targets_read'] is False,
            'Actual immutable native19 readout completion required')
    resource = read(root/'crop_gain_confirm_resource_50.json')
    require(resource['unique_ledger_entries'] == 1 and resource['record']['status'] == 'completed'
            and resource['record']['exit_code'] == 0, 'Natural unique shared GPU completion required')
    qa = module(reg['raw_review_helper'], '_crop_raw33_gain_confirm50')
    qa._inventory(done, read(bound(reg['model_config'])))
    training = read(bound(reg['fixed_training_completion']))
    require(done['base_fingerprint'] == training['base_fingerprint'], 'Same complete frozen BASE bytes')
    output = read(bound(done['completion']))
    require(output['status'] == 'COMPLETE_ALL_ROLE_INPUTS_RAW_LOGITS_NOT_QUALITY'
            and output['expected_inputs'] == len(expected)
            and {row['id'] for row in output['entries']} == set(by_id), 'All required native outputs present')
    out = root/'crop_gain_confirm_first_QA_50'
    out.mkdir(exist_ok=False)
    save(out/'claim.json', dict(utc=utc(), registration=ref(regpath), first_new_raw_QA=True,
        old_raw_QA_repeated=False, CPU_targets_read=False))
    try:
        calls = aliases = 0
        seen, raw_paths, previous, receipts, predictions = set(), set(), {}, [], []
        for item in output['entries']:
            entry = by_id[item['id']]
            request = read(bound(entry['input']))
            receipt = read(bound(item['receipt']))
            source = sources[entry['source_id']]
            require(source['role'] == request['role'] == 'confirm'
                    and request['source_id'] == receipt['source_id'] == source['source_id']
                    and source['source_sha256'] == request['source_sha256'] == receipt['source_sha256']
                    and request['id'] == receipt['id'] == entry['id']
                    and receipt['input'] == entry['input'] == item['input']
                    and request['input_signature'] == receipt['input_signature']
                    and receipt['model_role'] == 'GAIN_NATIVE19' and receipt['screen_reference_read'] is False
                    and request['reference_or_target_in_prompt'] is False, 'Native source/request/model binding differs')
            require(set(request['input_signature']) == {'input_ids', 'attention_mask', 'pixel_values', 'image_grid_thw'},
                    'Exactly four consumed input tensors')
            grid = torch.tensor(request['image_grid_thw'], dtype=torch.int64)
            require(tuple(grid.shape) == (3, 3) and bool((grid[:, 0] == 1).all())
                    and signature({'image_grid_thw': grid})['image_grid_thw'] == request['input_signature']['image_grid_thw'],
                    'Actual accepted native triplet grid differs')
            raw = torch.load(bound(receipt['raw_logits']), map_location='cpu', weights_only=True)
            probs = qa.validate_raw(raw, receipt, prepared['class_token_ids'], output['full_vocabulary_size'])
            key = qa.validate_alias(receipt, item['receipt'], previous, seen)
            if receipt['actual_new_forward']:
                require(receipt['raw_logits']['path'] not in raw_paths, 'Real calls require distinct first raw files')
                calls += 1
                raw_paths.add(receipt['raw_logits']['path'])
            else:
                aliases += 1
            seen.add(key)
            previous[item['receipt']['path']] = dict(reference=item['receipt'], receipt=receipt)
            receipts.append(receipt)
            predictions.append(dict(id=entry['id'], source_id=source['source_id'], source_sha256=source['source_sha256'],
                input=entry['input'], receipt=item['receipt'], class_logits3=receipt['class_logits'],
                probabilities3=probs, adapter_weights=reg['adapter_weights']))
        require(calls == output['actual_forward_calls'] and aliases == output['aliases']
                and calls+aliases == len(expected), 'Exact native actual-call and alias totals')
        journal = bound(done['completion']).parent/'attempts.jsonl'
        events = [json.loads(line) for line in journal.read_text().splitlines() if line]
        begins = [e for e in events if e['event'] == 'BEGIN_NEW_ROLE_FORWARD']
        persisted = [e for e in events if e['event'] == 'FIRST_RAW_PERSISTED']
        accepted = [e for e in events if e['event'] == 'ACCEPTED_NEW_ROLE_RESULT']
        first = {item['id']: item for item in receipts if item['actual_new_forward']}
        require(len(events) == 2*calls+len(expected)
                and all(e['model_role'] == 'GAIN_NATIVE19' for e in events)
                and len(begins) == len(persisted) == calls
                and {e['id'] for e in begins} == {e['id'] for e in persisted} == set(first)
                and all(e['raw_logits'] == first[e['id']]['raw_logits'] for e in persisted)
                and [e['id'] for e in accepted] == [item['id'] for item in output['entries']]
                and all(e['receipt'] == item['receipt'] for e, item in zip(accepted, output['entries'])),
                'Native actual begin/persist/accept journal differs')
        require(not torch.cuda.is_initialized(), 'First raw QA must not initialize CUDA')
        save(root/'crop_gain_confirm_output_acceptance_50.json', dict(status='PASS_GAIN_NATIVE19_FIRST_RAW_QA',
            GPU_registration=ref(regpath), completion=ref(donepath), input_acceptance=reg['input_acceptance'],
            predictions=predictions, actual_new_forwards=calls, aliases=aliases, distinct_sources=19,
            adapter_weights=reg['adapter_weights'], critic_weights=reg['critic_weights'], inventory=done['inventory'],
            base_fingerprint=done['base_fingerprint'], attempts=ref(journal), CPU_targets_read=False,
            new_model_calls=0, quality_established=False, automatic_production=False))
    except BaseException as error:
        save(out/'failure.json', dict(utc=utc(), error=repr(error), traceback=traceback.format_exc(),
            preserve_all_success=True, automatic_retry=False))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    run(parser.parse_args().root)
