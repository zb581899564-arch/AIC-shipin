"""Conditional first native-crop inputs for the exact historical remaining19.

This module never runs a model, trains, repeats an old source processor, or
admits a GPU. prepare() requires the actual native-screen PASS and final500
adapter. Confirm labels are written only to CPU_only_evaluation_targets.json.

crop_confirm_CPU_registration_36.json schema CROP_NATIVE_CONFIRM19_CPU_V36:
preparation_code, geometry_code, input_code, CPU_controller, model_config,
native_screen_result, native_remaining_registration, native_training_completion,
adapter_weights, adapter_directory, adapter_manifest={config:ref,weights:ref}, original_confirm_prepared,
original_confirm_input_acceptance, remaining19_output_acceptance,
remaining19_completion, original_confirm_labels: explicit {path,sha256} refs;
excluded_source={item_id,input}; deadline_utc; max_seconds; profile=NATIVE_RGB;
expected_sources=19; new_original_decode=0; old_source_processor_repeated=0.
The adapter_directory is an explicit string, not an artifact reference.
"""
from __future__ import annotations

import argparse
from collections import OrderedDict
import datetime as dt
import hashlib
import importlib.util
import os
from pathlib import Path
import sys
import time
import traceback

_support = Path(__file__).resolve().parents[1]/'pair_code_17'
if _support.is_dir():
    sys.path.insert(0, str(_support))
from pair_common import read, save, sha, ref, bound, require, utc, signature

SCHEMA = 'CROP_NATIVE_CONFIRM19_CPU_V36'
GATE = 'PASS_ALL_NATIVE_CONFIRM19_NEW_CROP_TRIPLETS_FIRST_CPU_QA_V36'
EXCLUDED_SOURCE = 'gnmc:test:006575.jpeg'
OUTPUT = 'crop_confirm_inputs_36'


def _reference(value):
    require(isinstance(value, dict) and set(value) == {'path', 'sha256'}
            and isinstance(value['path'], str) and bool(value['path'])
            and isinstance(value['sha256'], str) and len(value['sha256']) == 64
            and all(c in '0123456789abcdef' for c in value['sha256']), 'Explicit immutable file reference required')
    return value


def _key(*values):
    return hashlib.sha256('|'.join(map(str, values)).encode()).hexdigest()[:24]


def _module(reference, name):
    path = bound(reference)
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, 'Explicit helper cannot load')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def validate_native_admission(reg, screen, remaining, training, pilot, cpu):
    """Pure checks: actual native-screen PASS, exact registrations/final weights."""
    require(screen['status'] == 'PASS_NATIVE_CROP_SCREEN_ONLY'
            and screen['confirm_admitted'] is True and screen['primary'] == 'TRAINED'
            and screen['fixed_final_checkpoint'] is True
            and screen['registration'] == reg['native_remaining_registration']
            and screen['adapter_weights'] == reg['adapter_weights'], 'Actual native screen has not admitted confirm19')
    require(training['status'] == 'COMPLETE_FIXED_FINAL500_CROP_COMPARISON_NOT_QUALITY'
            and training['completed_updates'] == 500 and training['successful_micro'] == 2000
            and training['adapter_reload_all288_exact'] is True
            and training['adapter_weights'] == reg['adapter_weights']
            and training['adapter_directory'] == reg['adapter_directory']
            and training['remaining_admission'] == reg['native_remaining_registration'], 'Exact fixed-final500 adapter required')
    require(pilot['model_config'] == reg['model_config'] and pilot['CPU_registration'] == cpu['_reference']
            and cpu['geometry_code'] == reg['geometry_code'] and cpu['input_code'] == reg['input_code']
            and remaining['original_pilot_registration'] == pilot['_reference'], 'Native31/32/33 model/input/geometry identities differ')


def registration(root):
    root = Path(root)
    reg = read(root/'crop_confirm_CPU_registration_36.json')
    require(reg['schema'] == SCHEMA and reg['profile'] == 'NATIVE_RGB' and reg['expected_sources'] == 19
            and reg['new_original_decode'] == 0 and reg['old_source_processor_repeated'] == 0,
            'Explicit native remaining19-only CPU registration required')
    for key in ('preparation_code', 'geometry_code', 'input_code', 'CPU_controller', 'model_config',
                'native_screen_result', 'native_remaining_registration', 'native_training_completion',
                'adapter_weights', 'original_confirm_prepared', 'original_confirm_input_acceptance',
                'remaining19_output_acceptance', 'remaining19_completion'):
        bound(_reference(reg[key]))
    # The inference reader may inspect this reference, never the label file bytes.
    # Only prepare()'s final CPU-target writer opens/binds original human labels.
    _reference(reg['original_confirm_labels'])
    require(bound(reg['preparation_code']) == Path(__file__).resolve(), 'Exact frozen36 preparation entry required')
    require(reg['excluded_source']['item_id'] == EXCLUDED_SOURCE, 'Original unrecorded source must remain unavailable')
    bound(_reference(reg['excluded_source']['input']))
    require(isinstance(reg['max_seconds'], (int, float)) and not isinstance(reg['max_seconds'], bool)
            and 0 < reg['max_seconds'] <= 1800, 'Explicit bounded first CPU preparation budget required')
    remaining = read(bound(reg['native_remaining_registration']))
    pilot_reference = remaining['original_pilot_registration']
    pilot = read(bound(pilot_reference)); pilot['_reference'] = pilot_reference
    cpu_reference = pilot['CPU_registration']
    cpu = read(bound(cpu_reference)); cpu['_reference'] = cpu_reference
    screen = read(bound(reg['native_screen_result']))
    training = read(bound(reg['native_training_completion']))
    validate_native_admission(reg, screen, remaining, training, pilot, cpu)
    accepted = read(bound(screen['TRAINED_acceptance']))
    require(accepted['status'] == 'PASS_CROP_TRAINED_SCREEN_FINAL500_FIRST_QA'
            and accepted['training_completion'] == reg['native_training_completion']
            and accepted['registration'] == reg['native_remaining_registration'], 'Actual final500 first output QA must bind the training completion')
    require(Path(reg['adapter_directory']).resolve() == bound(reg['adapter_weights']).parent,
            'Final500 adapter directory does not own the exact accepted weights')
    require(set(reg['adapter_manifest']) == {'config', 'weights'}
            and reg['adapter_manifest']['weights'] == reg['adapter_weights']
            and bound(_reference(reg['adapter_manifest']['config'])).parent == bound(reg['adapter_weights']).parent,
            'Explicit final adapter config and weights file references required; no directory digest')
    return reg


def build_confirm_catalog(original_entries, original_rows, baseline_records, original_proofs,
                          excluded_source, geometry):
    """Pure exact entries[1:] adoption. No tensors, human labels or source choice."""
    require(len(original_entries) == len(original_rows) == 20 and len(baseline_records) == 19,
            'Exactly original20 and already accepted remaining19 required')
    require(excluded_source['item_id'] == EXCLUDED_SOURCE and original_entries[0] == excluded_source['input']
            and original_rows[0]['item_id'] == EXCLUDED_SOURCE, 'The first unavailable source may not be replaced or called')
    ids = [r['item_id'] for r in original_rows]
    hashes = [r['source_sha256'] for r in original_rows]
    require(len(set(ids)) == len(set(hashes)) == 20
            and all(isinstance(sid, str) and sid.startswith('gnmc:test:') for sid in ids),
            'Original20 gnmc:test identities and source bytes must be unique')
    records = []
    for index, (entry, row, base_record) in enumerate(zip(original_entries[1:], original_rows[1:], baseline_records)):
        baseline = base_record['value']; sid = row['item_id']; proof = original_proofs[sid]
        require(sid != EXCLUDED_SOURCE and row['role'] == 'confirm' and row['reference_available_to_inference'] is False,
                'Only original remaining19 label-free source inputs may be adopted')
        require(baseline['item_id'] == sid and baseline['source_sha256'] == row['source_sha256']
                and baseline['source'] == entry and proof['source_sha256'] == row['source_sha256'],
                'Already accepted BASE/proof/source order differs from exact entries[1:]')
        width, height = geometry.dimensions(row['width'], row['height'])
        baseline_box = baseline['original_BASE_box']
        pool = geometry.candidate_pool(width, height, baseline_box=baseline_box)
        require(pool[0] == baseline_box and len(pool) <= 7, 'Observed BASE must remain unchanged first candidate')
        for key in ('RGB', 'new_vision', 'original_proof'):
            _reference(row[key])
        _reference(base_record['reference']); _reference(baseline['original_BASE_raw'])
        rgb_hash = proof['RGB_sha256']
        require(isinstance(rgb_hash, str) and len(rgb_hash) == 64, 'Accepted original RGB pixel identity required')
        records.append(dict(source_id=sid, source_sha256=row['source_sha256'], role='confirm',
            original_index=index+1, width=width, height=height, RGB=row['RGB'], RGB_pixel_sha256=rgb_hash,
            original_proof=row['original_proof'], original_entry=entry, source_vision=row['new_vision'],
            source_vision_signature=row['new_vision_signature'], original_BASE=base_record['reference'],
            original_BASE_raw=baseline['original_BASE_raw'], baseline_box=list(baseline_box), pool=pool,
            original_BASE_observed=True, profile='NATIVE_RGB'))
    return records


def build_confirm_cases(records):
    """All alternatives versus BASE in both orders, plus one same-BASE control."""
    require(isinstance(records, list) and len(records) == 19, 'Exactly19 fixed confirmation sources required')
    require(len({r['source_id'] for r in records}) == len({r['source_sha256'] for r in records}) == 19,
            'Unique remaining19 source identities required')
    cases, pair_index = [], []
    for row in records:
        require(row['source_id'] != EXCLUDED_SOURCE and row['role'] == 'confirm'
                and row['pool'][0] == row['baseline_box'], 'Only remaining19 with unchanged BASE at index0')
        pool = row['pool']
        require(1 <= len(pool) <= 7 and len({tuple(box) for box in pool}) == len(pool), 'Fixed deduplicated crop pool required')
        def add(a, b):
            cid = _key(row['source_id'], row['source_sha256'], a, b, 'CROP36_NATIVE_CONFIRM_TRIPLET')
            cases.append(dict(id=cid, source_id=row['source_id'], a=a, b=b))
            return cid
        for candidate in range(1, len(pool)):
            forward, reverse = add(0, candidate), add(candidate, 0)
            pair_index.append(dict(source_id=row['source_id'], candidate_index=candidate,
                first_id=forward, reverse_id=reverse, same_crop=False))
        own = add(0, 0)
        pair_index.append(dict(source_id=row['source_id'], candidate_index=0,
            first_id=own, reverse_id=own, same_crop=True))
    require(len(cases) <= 247 and len({r['id'] for r in cases}) == len(cases), 'At most247 unique ordered confirmation inputs')
    return dict(cases=cases, confirm_ids=[r['id'] for r in cases], pair_index=pair_index,
                GT_used_for_input_or_pair_choice=False, exact_remaining_sources=19,
                historical_exposure=True, original20_complete=False, unavailable_source=EXCLUDED_SOURCE)


def build_cpu_targets(records, labels, geometry):
    """Human references are consumed only here, after the GT-free case plan."""
    require(isinstance(labels, list), 'Original CPU human label rows required')
    lookup = {row['item_id']: row for row in labels}
    require(len(lookup) == len(labels), 'Duplicate original human identity')
    result = []
    for source in records:
        human = lookup[source['source_id']]
        require(human['role'] == 'confirm' and human['source_sha256'] == source['source_sha256'],
                'Original confirm human/source identity differs')
        reference = list(geometry.validate_reference(human['reference_xywh'], source['width'], source['height']))
        result.append(dict(source_id=source['source_id'], source_sha256=source['source_sha256'], role='confirm',
            original_reference_xywh=reference, candidate_ious=[geometry.crop_iou(box, reference) for box in source['pool']],
            baseline_index=0, reference_modified=False))
    return result


def adopted_catalog(reg, geometry):
    old_gate = read(bound(reg['original_confirm_input_acceptance']))
    require(old_gate['status'] == 'PASS_FIRST_ALL20_CONFIRM_BASE_AND_NEW_VISION_INPUTS'
            and old_gate['prepared'] == reg['original_confirm_prepared'] and old_gate['actual_sources'] == 20,
            'Adopt actual original20 first input QA without repeating it')
    old = read(bound(reg['original_confirm_prepared'])); refs = old['entries']
    rows = [read(bound(r)) for r in refs]
    qa = read(bound(reg['remaining19_output_acceptance']))
    require(qa['status'] == 'PASS_FIRST_REMAINING19_BASE_AND_ROI_QA_ORIGINAL20_INCOMPLETE'
            and qa['completion'] == reg['remaining19_completion'] and qa['actual_sources'] == 19,
            'Only actually accepted remaining19 BASE outputs may be adopted')
    done = read(bound(reg['remaining19_completion']))
    require(done['status'] == 'COMPLETE_REMAINING19_BASE_AND_VISION_ORIGINAL20_INCOMPLETE'
            and done['first_new_BASE_generations'] == done['first_new_vision_readouts'] == 19
            and len(done['entries']) == len(done['base_calls']) == 19, 'Complete old remaining19 execution required')
    baseline_records = []
    for source_ref, result_ref, raw_ref in zip(refs[1:], done['entries'], done['base_calls']):
        result = read(bound(result_ref)); base_ref = result['original_BASE']; baseline = read(bound(base_ref))
        require(result['source'] == source_ref and result['source_sha256'] == baseline['source_sha256']
                and result['item_id'] == baseline['item_id'] and baseline['original_BASE_raw'] == raw_ref,
                'Accepted old output/source/raw references do not match exact remaining order')
        bound(raw_ref)
        baseline_records.append(dict(reference=base_ref, value=baseline))
    proofs = {r['item_id']: read(bound(r['original_proof'])) for r in rows[1:]}
    records = build_confirm_catalog(refs, rows, baseline_records, proofs, reg['excluded_source'], geometry)
    for source in records:
        bound(source['RGB']); bound(source['source_vision'])
    return records


class ConfirmInputs:
    """Independent confirm19 reader: only four input tensors, never CPU targets."""
    def __init__(self, root):
        self.root = Path(root); self.reg = registration(self.root); self.cache = OrderedDict()
        _module(self.reg['geometry_code'], 'crop_geometry_v31')
        self.image = _module(self.reg['input_code'], '_frozen_crop31_image_input_confirm36')
        gate = read(self.root/OUTPUT/'input_acceptance.json')
        require(gate['status'] == GATE and gate['registration'] == ref(self.root/'crop_confirm_CPU_registration_36.json')
                and gate['sources'] == 19 and gate['original20_complete'] is False,
                'Complete first new native confirm19 crop QA required')
        self.prepared = read(bound(gate['prepared']))

    def _vision(self, reference):
        import torch
        key = (reference['path'], reference['sha256'])
        if key not in self.cache:
            raw = torch.load(bound(reference), map_location='cpu', weights_only=True)
            self.cache[key] = {k: raw[k] for k in ('pixel_values', 'image_grid_thw')}
        self.cache.move_to_end(key)
        while len(self.cache) > 12:
            self.cache.popitem(last=False)
        return self.cache[key]

    def get(self, reference):
        import torch
        request = read(bound(reference)); views = [self._vision(r) for r in request['vision_inputs']]
        require(request['source_id'] != EXCLUDED_SOURCE and request['role'] == 'confirm'
                and request['reference_or_target_in_prompt'] is False, 'Only GT-free accepted remaining19 request')
        grid = torch.cat([v['image_grid_thw'] for v in views])
        packed = self.image.pack_image_pixels([v['pixel_values'] for v in views], grid)
        tokens = torch.load(bound(request['tokens']), map_location='cpu', weights_only=True)
        values = dict(**tokens, **packed)
        require(set(values) == {'input_ids', 'attention_mask', 'pixel_values', 'image_grid_thw'}
                and signature(values) == request['input_signature'] and grid.tolist() == request['image_grid_thw']
                and request['class_token_ids'] == self.prepared['class_token_ids'], 'Actual first-QAd confirm triplet changed')
        return values, request


def prepare(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU child must mask its own CUDA')
    root = Path(root); reg = registration(root)
    deadline = dt.datetime.fromisoformat(reg['deadline_utc'].replace('Z', '+00:00'))
    require(dt.datetime.now(dt.timezone.utc) < deadline, 'No CPU prepare outside the registered window')
    geometry = _module(reg['geometry_code'], 'crop_geometry_v31')
    image = _module(reg['input_code'], '_frozen_crop31_image_input_prepare36')
    records = adopted_catalog(reg, geometry); plan = build_confirm_cases(records)
    import numpy as np
    import torch
    from PIL import Image
    from transformers import AutoProcessor
    torch.set_num_threads(2)
    cfg = read(bound(reg['model_config']))
    processor = AutoProcessor.from_pretrained(cfg['model_dir'], local_files_only=True, min_pixels=65536, max_pixels=65536)
    out = root/OUTPUT; out.mkdir(exist_ok=False); started = time.monotonic()
    save(out/'claim.json', dict(registration=ref(root/'crop_confirm_CPU_registration_36.json'), utc=utc(),
        native_screen_result=reg['native_screen_result'], adapter_weights=reg['adapter_weights'],
        historical_exposure=True, original20_complete=False, new_decode=0, old_source_processor_repeated=0, GPU_admitted=False))
    completed, crop_proofs = [], []
    try:
        save(out/'source_catalog.json', dict(sources=records, exact_remaining_sources=19, original20_complete=False,
            excluded_source=reg['excluded_source'], profile='NATIVE_RGB', original_prepared=reg['original_confirm_prepared'],
            adopted_remaining19_QA=reg['remaining19_output_acceptance'], historical_exposure=True))
        save(out/'case_plan.json', plan)
        bysource = {r['source_id']: [] for r in records}
        for case in plan['cases']:
            bysource[case['source_id']].append(case)
        entries, profiles, classes, crop_count = {}, [], None, 0
        for source in records:
            require(time.monotonic()-started < reg['max_seconds'] and dt.datetime.now(dt.timezone.utc) < deadline,
                    'Registered first CPU budget/window exceeded')
            sid = source['source_id']; directory = out/_key(sid); directory.mkdir()
            rgb = np.load(bound(source['RGB']), allow_pickle=False)
            require(rgb.dtype == np.uint8 and rgb.shape == (source['height'], source['width'], 3)
                    and hashlib.sha256(rgb.tobytes()).hexdigest() == source['RGB_pixel_sha256'], 'Accepted original native RGB differs')
            raw = torch.load(bound(source['source_vision']), map_location='cpu', weights_only=True)
            old_vision = {k: raw[k] for k in ('pixel_values', 'image_grid_thw')}
            require(signature(old_vision) == source['source_vision_signature'], 'Adopted accepted source pixels changed')
            crop_inputs, crop_refs = {}, {}
            for index, box in enumerate(source['pool']):
                rendered, meta = image.render_crop(rgb, box)
                image.independent_render_check(rgb, box, rendered, meta)
                vision = dict(processor.image_processor(images=[Image.fromarray(rendered)], return_tensors='pt'))
                check = dict(processor.image_processor(images=[Image.fromarray(rendered.copy())], return_tensors='pt'))
                require(set(vision) == set(check) == {'pixel_values', 'image_grid_thw'}
                        and all(torch.equal(vision[k], check[k]) for k in vision), 'First new native crop independent processor QA differs')
                path = directory/('crop_%02d.pt'%index)
                with path.open('xb') as stream:
                    torch.save(vision, stream); stream.flush(); os.fsync(stream.fileno())
                require(signature(vision) == signature(torch.load(path, map_location='cpu', weights_only=True)), 'New crop exact save/reload differs')
                proof = directory/('crop_%02d.proof.json'%index)
                save(proof, dict(source_id=sid, source_sha256=source['source_sha256'], RGB=source['RGB'], original_proof=source['original_proof'],
                    box=box, render=meta, tensor=ref(path), signature=signature(vision), first_independent_QA=True, old_source_processor_repeated=False))
                crop_proofs.append(ref(proof)); crop_count += 1; crop_inputs[index] = vision; crop_refs[index] = ref(path)
            for case in bysource[sid]:
                a, b = case['a'], case['b']; views = [old_vision, crop_inputs[a], crop_inputs[b]]
                pixels = [v['pixel_values'] for v in views]; grid = torch.cat([v['image_grid_thw'] for v in views])
                packed = image.pack_image_pixels(pixels, grid); image.independent_pixel_check(pixels, grid, packed)
                tokens, text = image.build_text_input(processor, grid); image.independent_text_check(processor, packed, tokens, text)
                if classes is None:
                    classes = text['class_token_ids']
                require(classes == text['class_token_ids'], 'One actual next-token class identity required')
                token_path = directory/(case['id']+'.tokens.pt')
                with token_path.open('xb') as stream:
                    torch.save(tokens, stream); stream.flush(); os.fsync(stream.fileno())
                require(signature(tokens) == signature(torch.load(token_path, map_location='cpu', weights_only=True)), 'Triplet prefix save/reload differs')
                request = dict(id=case['id'], source_id=sid, source_sha256=source['source_sha256'], role='confirm', profile='NATIVE_RGB',
                    boxes=[source['pool'][a], source['pool'][b]], candidate_indices=[a, b],
                    vision_inputs=[source['source_vision'], crop_refs[a], crop_refs[b]], tokens=ref(token_path),
                    input_signature=signature(dict(**tokens, **packed)), image_grid_thw=grid.tolist(), class_token_ids=classes,
                    text_evidence=text, original_RGB=source['RGB'], original_proof=source['original_proof'], reference_or_target_in_prompt=False)
                path = directory/(case['id']+'.json'); save(path, request)
                entry = dict(id=case['id'], source_id=sid, input=ref(path)); entries[case['id']] = entry; completed.append(entry)
                profiles.append(dict(id=case['id'], source_id=sid, sequence_tokens=int(tokens['input_ids'].shape[1]), grid=grid.tolist()))
            del rgb, raw, old_vision, crop_inputs
        # Evaluation human references are read only after every GT-free input is fixed.
        targets = build_cpu_targets(records, read(bound(reg['original_confirm_labels'])), geometry)
        save(out/'CPU_only_evaluation_targets.json', dict(status='ORIGINAL_CONFIRM19_HUMAN_TARGETS_CPU_ONLY', sources=targets,
            pair_index=plan['pair_index'], original20_complete=False, excluded_source=reg['excluded_source'],
            single_editor=True, historical_exposure=True, no_new_blind_sources=True))
        actual = [entries[cid] for cid in plan['confirm_ids']]
        prepared_path = out/'prepared.json'
        save(prepared_path, dict(source_catalog=ref(out/'source_catalog.json'), case_plan=ref(out/'case_plan.json'),
            CPU_targets=ref(out/'CPU_only_evaluation_targets.json'),
            confirm_inputs=actual, screen_inputs=actual, train_schedule=[], class_token_ids=classes, profiles=profiles,
            sources=19, confirm_sources=19, new_crop_count=crop_count, profile='NATIVE_RGB', original20_complete=False,
            unavailable_source=EXCLUDED_SOURCE, historical_exposure=True, new_decode=0, old_source_processor_repeated=0,
            adapter_weights=reg['adapter_weights'], native_screen_result=reg['native_screen_result'], GPU_admitted=False))
        require(not torch.cuda.is_initialized(), 'First CPU crop preparation must not initialize CUDA')
        save(out/'input_acceptance.json', dict(status=GATE, registration=ref(root/'crop_confirm_CPU_registration_36.json'),
            prepared=ref(prepared_path), sources=19, inputs=len(actual), confirm_inputs=len(actual), new_crop_count=crop_count, profile='NATIVE_RGB',
            original20_complete=False, historical_exposure=True, first_independent_pixels_text_native_QA=True,
            first_new_crop_prepare_calls=crop_count, first_independent_crop_QA_calls=crop_count,
            original_source_processor_repeated=0, old_source_processor_repeated=0, new_original_decode=0, GPU_admitted=False,
            native_screen_result=reg['native_screen_result'], adapter_weights=reg['adapter_weights'], elapsed_seconds=time.monotonic()-started))
        print('CROP36_NATIVE_CONFIRM19_FIRST_CPU_QA', len(actual), crop_count, flush=True)
    except BaseException as error:
        save(out/'failure.json', dict(error=repr(error), traceback=traceback.format_exc(), completed_inputs=completed,
            completed_crop_proofs=crop_proofs, preserve_all_success=True, automatic_retry=False, GPU_admitted=False))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--root', type=Path, required=True)
    prepare(parser.parse_args().root)
