"""Conditional new-purpose native19 CPU inputs; never runs a model or admits GPU.

CLI --root ROOT. Registration ROOT/crop_gain_confirm_CPU_registration_49.json:
schema=GAIN_CRITIC_NATIVE19_CPU_V49; purpose=GAIN_CRITIC_NATIVE19_CONFIRM;
profile=NATIVE_RGB; expected_sources=19; max_seconds=1800;
deadline_utc=2026-10-18T03:22:24Z; new_original_decode=0;
old_source_processor_repeated=0. Explicit {path,sha256} file references:
preparation_code, legacy_confirm_pure_code (frozen36), geometry_code/input_code
(frozen31), math_code/policy_code (same47), model_config, original_GPU32,
original_CPU31, gain_screen_result, gain_fit_registration, gain_source_catalog,
screen_output_acceptance, critic_weights, fixed_training_completion,
adapter_weights, adapter_config, original_confirm_prepared,
original_confirm_input_acceptance, remaining19_output_acceptance,
remaining19_completion, original_confirm_labels. adapter_directory is a string;
excluded_source={item_id:'gnmc:test:006575.jpeg',input:exact old first ref}.
original_confirm_labels is opened ONLY by the final CPU-target writer.

Outputs ROOT/crop_gain_confirm_inputs_49/{source_catalog.json,case_plan.json,
CPU_only_evaluation_targets.json,prepared.json,input_acceptance.json}; source
subfolders hold first-new native crop tensors/proofs and prefix/request files.
NativeGainConfirmInputs(root).prepared.confirm_inputs; get(inputref)->4 CPU
tensors/request. It never calls36.registration/prepare or revives old33/37/38.
"""
from __future__ import annotations

import argparse
from collections import OrderedDict
import copy
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
from pair_common import read, save, ref, bound, require, signature, utc

SCHEMA = 'GAIN_CRITIC_NATIVE19_CPU_V49'
PURPOSE = 'GAIN_CRITIC_NATIVE19_CONFIRM'
GATE = 'PASS_GAIN_NATIVE19_NEW_CROP_TRIPLETS_FIRST_CPU_QA_V49'
OUTPUT = 'crop_gain_confirm_inputs_49'
REGISTRATION = 'crop_gain_confirm_CPU_registration_49.json'
EXCLUDED_SOURCE = 'gnmc:test:006575.jpeg'
DEADLINE = dt.datetime(2026, 10, 18, 3, 22, 24, tzinfo=dt.timezone.utc)
REF_KEYS = ('preparation_code', 'legacy_confirm_pure_code', 'geometry_code', 'input_code',
    'math_code', 'policy_code', 'model_config', 'original_GPU32', 'original_CPU31',
    'gain_screen_result', 'gain_fit_registration', 'gain_source_catalog', 'screen_output_acceptance',
    'critic_weights', 'fixed_training_completion', 'adapter_weights', 'adapter_config',
    'original_confirm_prepared', 'original_confirm_input_acceptance',
    'remaining19_output_acceptance', 'remaining19_completion')


def _reference(value):
    require(isinstance(value, dict) and set(value) == {'path', 'sha256'}
        and isinstance(value['path'], str) and value['path'] and isinstance(value['sha256'], str)
        and len(value['sha256']) == 64 and all(c in '0123456789abcdef' for c in value['sha256']),
        'Explicit immutable file reference required')
    return value


def _key(*values):
    return hashlib.sha256('|'.join(map(str, values)).encode()).hexdigest()[:24]


def _module(reference, name):
    path = bound(reference); sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, 'Explicit frozen helper cannot load')
    result = importlib.util.module_from_spec(spec); sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def validate_gain_admission(reg, result, fit_registration, training, screen_acceptance):
    """Pure49 gate: new47 PASS, not the old native-CE admission."""
    require(result['status'] == 'PASS_GAIN_CRITIC_SCREEN20_ONLY' and result['confirm_admitted'] is True
        and result['production_admitted'] is False and result['primary'] == 'JOINT14'
        and result['fixed_final_checkpoint'] is True and result['reports']['JOINT14']['quality']['admitted'] is True,
        'Only actual new47 JOINT14 screen PASS may admit native19')
    for result_key, reg_key in (('registration', 'gain_fit_registration'), ('critic_weights', 'critic_weights'),
            ('adapter_weights', 'adapter_weights'), ('source_catalog', 'gain_source_catalog'),
            ('screen_output_acceptance', 'screen_output_acceptance')):
        require(result[result_key] == reg[reg_key], 'New47 immutable admission reference differs: '+result_key)
    require(fit_registration['schema'] == 'CROP_GAIN_FINAL500_FIT_SCREEN_V47'
        and fit_registration['adapter_weights'] == reg['adapter_weights']
        and fit_registration['fixed_training_completion'] == reg['fixed_training_completion']
        and fit_registration['original_screen_catalog'] == reg['gain_source_catalog']
        and fit_registration['screen_output_acceptance'] == reg['screen_output_acceptance'], 'Exact successful47 fit/source scope required')
    for key in ('math_code', 'policy_code'):
        require(fit_registration[key] == result['input_bindings'][key] == reg[key], 'Frozen14-feature/policy implementation differs')
    require(training['status'] == 'COMPLETE_FIXED_FINAL500_CROP_COMPARISON_NOT_QUALITY'
        and training['completed_updates'] == 500 and training['successful_micro'] == 2000
        and training['adapter_reload_all288_exact'] is True and training['adapter_weights'] == reg['adapter_weights']
        and training['adapter_directory'] == reg['adapter_directory'], 'Same readonly final500 CROP adapter required')
    require(screen_acceptance['status'] == 'PASS_CROP_TRAINED_SCREEN_FINAL500_FIRST_QA'
        and screen_acceptance['training_completion'] == reg['fixed_training_completion'], 'Adopt original successful final500 screen QA')


def registration(root):
    root = Path(root); reg = read(root/REGISTRATION)
    require(reg['schema'] == SCHEMA and reg['purpose'] == PURPOSE and reg['profile'] == 'NATIVE_RGB'
        and reg['expected_sources'] == 19 and reg['max_seconds'] == 1800
        and reg['new_original_decode'] == reg['old_source_processor_repeated'] == 0,
        'Explicit new-purpose native19-only CPU registration required')
    require(dt.datetime.fromisoformat(reg['deadline_utc'].replace('Z', '+00:00')) == DEADLINE, 'Original Goal deadline must remain fixed')
    for key in REF_KEYS:
        bound(_reference(reg[key]))
    # An inference reader validates this reference's syntax only; no label bytes.
    _reference(reg['original_confirm_labels'])
    require(bound(reg['preparation_code']) == Path(__file__).resolve(), 'Exact49 preparation/reader entry required')
    require(reg['excluded_source']['item_id'] == EXCLUDED_SOURCE, 'Original unrecorded first source remains excluded')
    bound(_reference(reg['excluded_source']['input']))
    result = read(bound(reg['gain_screen_result'])); fit = read(bound(reg['gain_fit_registration']))
    training = read(bound(reg['fixed_training_completion']))
    validate_gain_admission(reg, result, fit, training, read(bound(reg['screen_output_acceptance'])))
    old32 = read(bound(reg['original_GPU32'])); old31 = read(bound(reg['original_CPU31']))
    old33 = read(bound(training['remaining_admission']))
    require(old33['original_pilot_registration'] == reg['original_GPU32']
        and old32['CPU_registration'] == reg['original_CPU31'] and old32['model_config'] == reg['model_config']
        and old31['geometry_code'] == reg['geometry_code'] and old31['input_code'] == reg['input_code'],
        'Original physical BASE/native geometry/input implementations differ')
    weights = bound(reg['adapter_weights']); config = bound(reg['adapter_config'])
    require(weights.parent == config.parent == Path(reg['adapter_directory']).resolve(), 'Explicit final adapter config/weights files must share the bound directory')
    return reg


def validate_confirm_scope(records, old_catalog):
    """Prove this exact19 is outside the fixed gain train602 and screen20."""
    require(len(records) == 19 and [r['original_index'] for r in records] == list(range(1, 20)), 'Only original entries[1:] in unchanged order')
    previous = old_catalog['sources']
    require(len(previous) == 622 and sum(r['role'] == 'train' for r in previous) == 602
        and sum(r['role'] == 'screen' for r in previous) == 20, 'Same original602train+20screen catalog required')
    ids = {r['source_id'] for r in previous}; hashes = {r['source_sha256'] for r in previous}
    require(len(ids) == len(hashes) == 622, 'Unique original gain train/screen identities required')
    require(len({r['source_id'] for r in records}) == len({r['source_sha256'] for r in records}) == 19
        and all(r['role'] == 'confirm' and r['source_id'] != EXCLUDED_SOURCE for r in records)
        and not ids & {r['source_id'] for r in records} and not hashes & {r['source_sha256'] for r in records},
        'Native19 cannot overlap any gain-fit or gain-screen source identity/bytes')


def build_gain_confirm_plan(records, pure36):
    """Adopt36's GT-free pool/pair algorithm; give every new purpose a new ID."""
    old = pure36.build_confirm_cases(records); result = copy.deepcopy(old)
    by_source = {r['source_id']: r for r in records}
    mapping = {case['id']: _key('GAIN49_NATIVE_CONFIRM', by_source[case['source_id']]['source_sha256'], case['id']) for case in old['cases']}
    require(len(mapping) == len(set(mapping.values())) == len(old['cases']), 'Unique purpose49 input identities required')
    for case in result['cases']:
        case['legacy_algorithm_case_id'] = case['id']; case['id'] = mapping[case['id']]
    result['confirm_ids'] = [mapping[cid] for cid in old['confirm_ids']]
    for pair in result['pair_index']:
        pair['first_id'], pair['reverse_id'] = mapping[pair['first_id']], mapping[pair['reverse_id']]
    result.update(purpose=PURPOSE, profile='NATIVE_RGB', old_CE_quality='STOP', old_CE_admission_used=False)
    return result


class NativeGainConfirmInputs:
    """Whitelisted four-tensor reader; never reads human targets or does a fit."""
    def __init__(self, root):
        self.root = Path(root); self.reg = registration(self.root); self.cache = OrderedDict()
        _module(self.reg['geometry_code'], 'crop_geometry_v31')
        self.image = _module(self.reg['input_code'], '_gain_native49_image31')
        gate = read(self.root/OUTPUT/'input_acceptance.json')
        require(gate['status'] == GATE and gate['registration'] == ref(self.root/REGISTRATION)
            and gate['sources'] == 19 and gate['original20_complete'] is False and gate['GPU_admitted'] is False
            and gate['critic_weights'] == self.reg['critic_weights'] and gate['adapter_weights'] == self.reg['adapter_weights'], 'Actual first49 complete input QA required')
        self.prepared = read(bound(gate['prepared']))
        entries = self.prepared['confirm_inputs']; self.allowed = {tuple(sorted(e['input'].items())): e for e in entries}
        require(len(entries) == len(self.allowed) == gate['inputs'] and 19 <= len(entries) <= 247
            and len({e['id'] for e in entries}) == len(entries) and len({e['source_id'] for e in entries}) == 19,
            'Complete distinct native19 input whitelist required')
        catalog = read(bound(self.prepared['source_catalog']))
        self.sources = {r['source_id']: r for r in catalog['sources']}
        require(len(self.sources) == 19 and set(self.sources) == {e['source_id'] for e in entries}, 'Exact accepted source catalog required')

    def _vision(self, reference):
        import torch
        key = tuple(sorted(_reference(reference).items()))
        if key not in self.cache:
            raw = torch.load(bound(reference), map_location='cpu', weights_only=True)
            self.cache[key] = {k: raw[k] for k in ('pixel_values', 'image_grid_thw')}
        self.cache.move_to_end(key)
        while len(self.cache) > 12:
            self.cache.popitem(last=False)
        return self.cache[key]

    def get(self, reference):
        import torch
        key = tuple(sorted(_reference(reference).items())); require(key in self.allowed, 'Only registered49 confirm inputs may be read')
        entry = self.allowed[key]; request = read(bound(reference)); source = self.sources[entry['source_id']]
        require(request['id'] == entry['id'] and request['source_id'] == entry['source_id'] != EXCLUDED_SOURCE
            and request['source_sha256'] == source['source_sha256'] and request['role'] == source['role'] == 'confirm'
            and request['reference_or_target_in_prompt'] is False
            and not any(k in request for k in ('target', 'labels', 'candidate_ious', 'original_reference_xywh')),
            'Only source-bound label-free remaining19 requests allowed')
        views = [self._vision(r) for r in request['vision_inputs']]
        grid = torch.cat([v['image_grid_thw'] for v in views])
        packed = self.image.pack_image_pixels([v['pixel_values'] for v in views], grid)
        tokens = torch.load(bound(request['tokens']), map_location='cpu', weights_only=True)
        values = dict(**tokens, **packed)
        require(set(values) == {'input_ids', 'attention_mask', 'pixel_values', 'image_grid_thw'}
            and signature(values) == request['input_signature'] and grid.tolist() == request['image_grid_thw']
            and request['class_token_ids'] == self.prepared['class_token_ids'], 'First-QAd49 tensors/grid/classes changed')
        return values, request


def prepare(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'Only CPU child masks its own CUDA')
    root = Path(root); reg = registration(root)
    require(dt.datetime.now(dt.timezone.utc) < DEADLINE, 'Inside the fixed Goal window only')
    geometry = _module(reg['geometry_code'], 'crop_geometry_v31')
    image = _module(reg['input_code'], '_gain_native49_prepare_image31')
    pure36 = _module(reg['legacy_confirm_pure_code'], '_frozen36_pure_native_gain49')
    # adopted_catalog calls only old identity/BASE metadata and the pure builder;
    # it never calls36.registration,36.prepare, a processor or a model.
    records = pure36.adopted_catalog(reg, geometry)
    validate_confirm_scope(records, read(bound(reg['gain_source_catalog'])))
    plan = build_gain_confirm_plan(records, pure36)
    import numpy as np
    import torch
    from PIL import Image
    from transformers import AutoProcessor
    torch.set_num_threads(2); cfg = read(bound(reg['model_config']))
    processor = AutoProcessor.from_pretrained(cfg['model_dir'], local_files_only=True, min_pixels=65536, max_pixels=65536)
    out = root/OUTPUT; out.mkdir(exist_ok=False); started = time.monotonic()
    save(out/'claim.json', dict(utc=utc(), registration=ref(root/REGISTRATION), purpose=PURPOSE,
        screen_result=reg['gain_screen_result'], critic_weights=reg['critic_weights'], adapter_weights=reg['adapter_weights'],
        old_CE_quality='STOP', old_CE_admission_used=False, old_source_processor_repeated=0, new_decode=0, GPU_admitted=False))
    completed, proofs = [], []
    try:
        save(out/'source_catalog.json', dict(sources=records, exact_remaining_sources=19, original20_complete=False,
            excluded_source=reg['excluded_source'], original_prepared=reg['original_confirm_prepared'],
            adopted_remaining19_QA=reg['remaining19_output_acceptance'], profile='NATIVE_RGB', purpose=PURPOSE,
            gain_fit_sources_overlap=False, historical_exposure=True))
        save(out/'case_plan.json', plan)
        by_source = {r['source_id']: [] for r in records}
        for case in plan['cases']:
            by_source[case['source_id']].append(case)
        entries, profiles, classes, crop_count = {}, [], None, 0
        for source in records:
            require(time.monotonic()-started < 1800 and dt.datetime.now(dt.timezone.utc) < DEADLINE, 'Registered49 CPU budget/window exceeded')
            sid = source['source_id']; directory = out/_key(sid); directory.mkdir()
            rgb = np.load(bound(source['RGB']), allow_pickle=False)
            require(rgb.dtype == np.uint8 and rgb.shape == (source['height'], source['width'], 3)
                and hashlib.sha256(rgb.tobytes()).hexdigest() == source['RGB_pixel_sha256'], 'Accepted original native RGB differs')
            raw = torch.load(bound(source['source_vision']), map_location='cpu', weights_only=True)
            source_vision = {k: raw[k] for k in ('pixel_values', 'image_grid_thw')}
            require(signature(source_vision) == source['source_vision_signature'], 'Adopted source pixels/grid changed')
            crops, crop_refs = {}, {}
            for index, box in enumerate(source['pool']):
                rendered, meta = image.render_crop(rgb, box); image.independent_render_check(rgb, box, rendered, meta)
                vision = dict(processor.image_processor(images=[Image.fromarray(rendered)], return_tensors='pt'))
                check = dict(processor.image_processor(images=[Image.fromarray(rendered.copy())], return_tensors='pt'))
                require(set(vision) == set(check) == {'pixel_values', 'image_grid_thw'}
                    and all(torch.equal(vision[k], check[k]) for k in vision), 'First-new native crop independent encoding differs')
                path = directory/('crop_%02d.pt'%index)
                with path.open('xb') as stream:
                    torch.save(vision, stream); stream.flush(); os.fsync(stream.fileno())
                require(signature(vision) == signature(torch.load(path, map_location='cpu', weights_only=True)), 'First crop exact save/reload differs')
                proof = directory/('crop_%02d.proof.json'%index)
                save(proof, dict(source_id=sid, source_sha256=source['source_sha256'], RGB=source['RGB'], original_proof=source['original_proof'],
                    box=box, render=meta, tensor=ref(path), signature=signature(vision), first_independent_QA=True, old_source_processor_repeated=False))
                proofs.append(ref(proof)); crops[index] = vision; crop_refs[index] = ref(path); crop_count += 1
            for case in by_source[sid]:
                a, b = case['a'], case['b']; views = [source_vision, crops[a], crops[b]]
                pixels = [v['pixel_values'] for v in views]; grid = torch.cat([v['image_grid_thw'] for v in views])
                packed = image.pack_image_pixels(pixels, grid); image.independent_pixel_check(pixels, grid, packed)
                tokens, text = image.build_text_input(processor, grid); image.independent_text_check(processor, packed, tokens, text)
                if classes is None:
                    classes = text['class_token_ids']
                require(classes == text['class_token_ids'], 'One actual class0/1/2 identity')
                token_path = directory/(case['id']+'.tokens.pt')
                with token_path.open('xb') as stream:
                    torch.save(tokens, stream); stream.flush(); os.fsync(stream.fileno())
                require(signature(tokens) == signature(torch.load(token_path, map_location='cpu', weights_only=True)), 'New prefix exact save/reload differs')
                request = dict(id=case['id'], source_id=sid, source_sha256=source['source_sha256'], role='confirm',
                    purpose=PURPOSE, profile='NATIVE_RGB', boxes=[source['pool'][a], source['pool'][b]], candidate_indices=[a, b],
                    vision_inputs=[source['source_vision'], crop_refs[a], crop_refs[b]], tokens=ref(token_path),
                    input_signature=signature(dict(**tokens, **packed)), image_grid_thw=grid.tolist(), class_token_ids=classes,
                    text_evidence=text, original_RGB=source['RGB'], original_proof=source['original_proof'], reference_or_target_in_prompt=False)
                path = directory/(case['id']+'.json'); save(path, request)
                entry = dict(id=case['id'], source_id=sid, input=ref(path)); entries[case['id']] = entry; completed.append(entry)
                profiles.append(dict(id=case['id'], source_id=sid, grid=grid.tolist(), sequence_tokens=int(tokens['input_ids'].shape[1])))
            del rgb, raw, source_vision, crops
        # Only this CPU-only final writer opens the original human label file.
        targets = pure36.build_cpu_targets(records, read(bound(reg['original_confirm_labels'])), geometry)
        targets_path = out/'CPU_only_evaluation_targets.json'
        save(targets_path, dict(status='GAIN_NATIVE19_ORIGINAL_HUMAN_TARGETS_CPU_ONLY', sources=targets,
            pair_index=plan['pair_index'], original20_complete=False, excluded_source=reg['excluded_source'],
            historical_exposure=True, old_ROI_exposure=True, no_new_blind_sources=True, purpose=PURPOSE))
        actual = [entries[cid] for cid in plan['confirm_ids']]; prepared_path = out/'prepared.json'
        save(prepared_path, dict(source_catalog=ref(out/'source_catalog.json'), case_plan=ref(out/'case_plan.json'),
            CPU_targets=ref(targets_path), confirm_inputs=actual, pair_index=plan['pair_index'], class_token_ids=classes,
            profiles=profiles, sources=19, confirm_sources=19, new_crop_count=crop_count, profile='NATIVE_RGB', purpose=PURPOSE,
            critic_weights=reg['critic_weights'], adapter_weights=reg['adapter_weights'], math_code=reg['math_code'], policy_code=reg['policy_code'],
            screen_result=reg['gain_screen_result'], original20_complete=False, unavailable_source=EXCLUDED_SOURCE,
            train_schedule=[], old_CE_quality='STOP', historical_exposure=True, new_decode=0, old_source_processor_repeated=0, GPU_admitted=False))
        require(not torch.cuda.is_initialized(), 'CPU preparation cannot initialize CUDA')
        save(out/'input_acceptance.json', dict(status=GATE, registration=ref(root/REGISTRATION), prepared=ref(prepared_path),
            purpose=PURPOSE, sources=19, inputs=len(actual), confirm_inputs=len(actual), original20_complete=False,
            first_independent_pixels_text_native_QA=True, new_crop_count=crop_count,
            first_new_crop_prepare_calls=crop_count, first_independent_crop_QA_calls=crop_count,
            adapter_weights=reg['adapter_weights'], critic_weights=reg['critic_weights'], screen_result=reg['gain_screen_result'],
            old_CE_quality='STOP', old_CE_admission_used=False, new_original_decode=0, old_source_processor_repeated=0,
            GPU_admitted=False, elapsed_seconds=time.monotonic()-started))
        print('GAIN49_NATIVE19_FIRST_CPU_QA', len(actual), crop_count, flush=True)
    except BaseException as error:
        save(out/'failure.json', dict(error=repr(error), traceback=traceback.format_exc(), completed_inputs=completed,
            completed_crop_proofs=proofs, preserve_all_success=True, automatic_retry=False, GPU_admitted=False))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--root', type=Path, required=True)
    prepare(parser.parse_args().root)
