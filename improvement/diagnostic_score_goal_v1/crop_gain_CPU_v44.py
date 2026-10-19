"""Exclusive first missing408 combination preparation; adopt original2000."""
import argparse
import datetime as dt
import importlib.util
import os
from pathlib import Path
import sys
import time
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
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'First combinations only on CPU')
    import torch
    torch.set_num_threads(2)
    from transformers import AutoProcessor
    regpath = root/'crop_gain_CPU_registration_44.json'
    reg = read(regpath)
    require(bound(reg['preparation_code']) == Path(__file__).resolve(), 'Exact new-purpose CPU entry')
    component = module(reg['input_code'], '_frozen_gain_prepare44')
    old_prepared = read(bound(reg['old_prepared']))
    old_catalog = read(bound(reg['old_catalog']))
    old_plan = read(bound(reg['old_case_plan']))
    old_gate = read(bound(reg['old_input_gate']))
    component.validate_cpu_registration(reg, training_completion=read(bound(reg['fixed_training_completion'])),
                                       old_stop=read(bound(reg['old_STOP'])), old_gate=old_gate)
    require(reg['max_seconds'] == 900 and reg['new_original_decodes'] == reg['new_image_processor_calls'] == 0,
            'Fixed first-only preparation budget and input purpose')
    for reference in (reg['geometry_code'], reg['helper_code'], reg['adapter_weights'], reg['gain_protocol']):
        bound(reference)
    old_requests = [dict(reference=row['input'], request=read(bound(row['input'])))
                    for row in old_prepared['train_schedule']]
    plan = component.build_gain_plan(old_catalog, old_prepared, old_plan, old_requests)
    out = root/'crop_gain_inputs_44'
    out.mkdir(exist_ok=False)
    save(out/'claim.json', dict(utc=utc(), registration=ref(regpath), original_CE_quality='STOP',
        old_2000_input_QA_adopted=True, image_processor_calls=0, original_decodes=0,
        new_model_calls=0, production_admitted=False))
    completed = []
    started = time.monotonic()
    try:
        save(out/'label_free_plan.json', plan)
        save(out/'source_catalog.json', plan['source_catalog'])
        image = module(reg['image_code'], '_frozen_crop_image31_gain44')
        legacy = module(reg['original_input_reader'], '_frozen_crop31_template_reader44')
        original_inputs = legacy.CropInputs(root)
        cfg = read(bound(reg['model_config']))
        processor = AutoProcessor.from_pretrained(cfg['model_dir'], local_files_only=True,
                                                  min_pixels=65536, max_pixels=65536)
        references = {}
        for case in plan['cases']:
            if case['adopted_input']:
                continue
            deadline = dt.datetime.fromisoformat(reg['deadline_utc'].replace('Z', '+00:00'))
            require(time.monotonic()-started < 900 and dt.datetime.now(dt.timezone.utc) < deadline,
                    'Inside registered CPU budget and Goal deadline')
            values, template = original_inputs.get(case['template_input'])
            new_values, request, evidence = component.build_missing_input(case, template, values, processor, image)
            if request['tokens'] is None:
                token_path = out/(case['id']+'.tokens.pt')
                with token_path.open('xb') as f:
                    torch.save({k: new_values[k] for k in ('input_ids', 'attention_mask')}, f)
                loaded = torch.load(token_path, map_location='cpu', weights_only=True)
                require(signature(loaded) == {k: request['input_signature'][k] for k in loaded},
                        'First new prefix exact save/reload')
                request = component.materialize_missing_input(request, ref(token_path))
            else:
                request = component.materialize_missing_input(request)
            request_path = out/(case['id']+'.json')
            save(request_path, request)
            evidence_path = out/(case['id']+'.first_QA.json')
            save(evidence_path, dict(request=ref(request_path), source_id=case['source_id'],
                source_sha256=case['source_sha256'], original_template=case['template_input'],
                evidence=evidence, first_combination_QA=True, new_image_processor_calls=0, new_original_decodes=0))
            references[case['id']] = ref(request_path)
            completed.append(ref(evidence_path))
            del values, new_values
        require(len(references) == len(completed) == 408 and not torch.cuda.is_initialized(),
                'All408 first-new combinations complete, no CUDA')
        prepared = component.finalize_prepared(plan, references, CPU_targets_ref=reg['CPU_targets'],
            adapter_weights=reg['adapter_weights'], bindings={key: reg[key] for key in
            ('old_prepared', 'old_catalog', 'old_case_plan', 'old_input_gate')} | {'source_catalog': ref(out/'source_catalog.json')})
        save(out/'prepared.json', prepared)
        save(out/'input_acceptance.json', dict(status=component.GATE, registration=ref(regpath),
            prepared=ref(out/'prepared.json'), adopted_inputs=2000, first_new_combinations=408,
            new_image_processor_calls=0, new_original_decodes=0, first_QA_receipts=completed,
            pilot_inputs=128, remaining_inputs=2280, original_CE_quality='STOP',
            GPU_admitted=False, elapsed_seconds=time.monotonic()-started))
        print('GAIN44_FIRST_INPUTS_COMPLETE', len(completed), 'ADOPTED2000', flush=True)
    except BaseException as error:
        save(out/'failure.json', dict(utc=utc(), error=repr(error), traceback=traceback.format_exc(),
            completed_first_QA=completed, preserve_all_success=True, automatic_retry=False))
        raise


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    run(p.parse_args().root)
