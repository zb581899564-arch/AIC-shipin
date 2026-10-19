"""One exclusive CPU gain-critic fit and historical screen20 evaluation.

CLI --root ROOT reads ROOT/crop_gain_fit_registration_47.json. Exact schema:
schema='CROP_GAIN_FINAL500_FIT_SCREEN_V47'; deadline_utc; all remaining fields
are absolute {path,sha256} refs: fit_code, math_code, policy_code,
gain_CPU_registration, gain_input_acceptance, gain_prepared, gain_plan,
gain_catalog, gain_GPU_registration, gain_remaining_admission,
pilot_output_acceptance, remaining_output_acceptance, original_screen_prepared,
original_screen_catalog, original_screen_case_plan, original_screen_input_acceptance,
screen_output_acceptance, CPU_targets, original_comparison,
fixed_training_completion, adapter_weights, gain_protocol.

Requires both already successful46 readout QAs. Reads accepted train class_logits3
and already-QAd33 receipt.class_logits, never raw tensors or old QA routines.
Uses bound45 math including its frozen train-only RMS. No model, processor,
IoU recomputation, checkpoint/threshold selection, confirm or production calls.
Exclusive ROOT/crop_gain_fit_47; failures preserve partial artifacts, no resume.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import math
from numbers import Integral, Real
import os
from pathlib import Path
import sys
import traceback

import numpy as np

SCHEMA = 'CROP_GAIN_FINAL500_FIT_SCREEN_V47'
OUTPUT = 'crop_gain_fit_47'
REF_FIELDS = ('fit_code', 'math_code', 'policy_code', 'gain_CPU_registration', 'gain_input_acceptance',
    'gain_prepared', 'gain_plan', 'gain_catalog', 'gain_GPU_registration', 'gain_remaining_admission',
    'pilot_output_acceptance', 'remaining_output_acceptance', 'original_screen_prepared',
    'original_screen_catalog', 'original_screen_case_plan', 'original_screen_input_acceptance',
    'screen_output_acceptance', 'CPU_targets', 'original_comparison', 'fixed_training_completion',
    'adapter_weights', 'gain_protocol')


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def reference(value):
    require(isinstance(value, dict) and set(value) == {'path', 'sha256'}
        and isinstance(value['path'], str) and Path(value['path']).is_absolute()
        and isinstance(value['sha256'], str) and len(value['sha256']) == 64
        and all(c in '0123456789abcdef' for c in value['sha256']), 'Explicit absolute artifact path/SHA required')
    return value


def bound(value):
    value = reference(value); path = Path(value['path'])
    require(path.is_file() and sha(path) == value['sha256'], 'Missing/changed bound artifact: '+str(path))
    return path


def ref(path):
    path = Path(path).resolve()
    return dict(path=str(path), sha256=sha(path))


def read(path):
    with Path(path).open(encoding='utf-8') as stream:
        return json.load(stream)


def save(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, allow_nan=False, indent=2)
        stream.write('\n')


def module(value, name):
    path = bound(value); spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec); sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def _finite(value):
    require(isinstance(value, Real) and not isinstance(value, (bool, np.bool_)) and math.isfinite(value),
            'Known finite numeric evidence required')
    return float(value)


def _ious(values, length):
    require(isinstance(values, list) and len(values) == length, 'Complete original candidate IoUs required')
    result = np.array([_finite(v) for v in values], dtype=np.float64)
    require(bool(((result >= 0) & (result <= 1)).all()), 'Original candidate IoU outside[0,1]')
    return result


def _logits(values):
    require(isinstance(values, list) and len(values) == 3, 'Exactly three accepted raw class logits required')
    return np.array([_finite(v) for v in values], dtype=np.float64)


def _unique(rows, label):
    result = {row['source_id']:row for row in rows}
    require(len(result) == len(rows), 'Duplicate '+label+' source identity')
    hashes = [row['source_sha256'] for row in rows]
    require(len(set(hashes)) == len(hashes) and all(isinstance(v, str) and len(v) == 64
        and all(c in '0123456789abcdef' for c in v) for v in hashes), 'Duplicate/invalid '+label+' source SHA')
    return result


def joined_targets(sources, targets):
    """Original stored candidate IoUs only; never derive or alter human boxes."""
    source_map = _unique(sources, 'catalog'); target_map = _unique(targets, 'target')
    require(set(source_map) == set(target_map), 'Exact original source/target scope required')
    result = {}
    for sid, source in source_map.items():
        target = target_map[sid]
        require(target['source_sha256'] == source['source_sha256'] and target['role'] == source['role']
            and target['reference_modified'] is False and target['baseline_index'] == 0, 'Original target/source/role binding differs')
        require(len(source['pool']) == len({tuple(b) for b in source['pool']}), 'Original candidate pool must be deduplicated')
        result[sid] = _ious(target['candidate_ious'], len(source['pool']))
    return result


def build_training_rows(sources, target_ious, pair_index, predictions, math45, policy33):
    """Exactly602 sources, two canonical unordered pairs/source, target B-A."""
    source_map = _unique(sources, 'train')
    require(len(source_map) == 602 and all(source['role'] == 'train' for source in sources), 'Exactly602 train sources only')
    grouped = {sid:[] for sid in source_map}; used = set(); rows, mapping = [], []
    for pair in pair_index:
        sid = pair['source_id']; require(sid in grouped, 'Unknown fit-pair source')
        grouped[sid].append(pair)
    for source in sources:
        sid = source['source_id']; pairs = grouped[sid]; seen = set(); training = []
        require(len(pairs) == 2, 'Exactly two fixed unordered pairs/source required')
        for pair in pairs:
            a, b = pair['a'], pair['b']
            require(isinstance(a, Integral) and isinstance(b, Integral) and not isinstance(a, bool) and not isinstance(b, bool)
                and 0 <= a < b < len(source['pool']) and (a, b) not in seen
                and pair['source_sha256'] == source['source_sha256'], 'Canonical pair/source/pool indexing differs')
            seen.add((a, b)); first, reverse = pair['first_id'], pair['reverse_id']
            require(first != reverse and first not in used and reverse not in used, 'Duplicate ordered training evidence')
            used.update((first, reverse)); f, r = predictions[first], predictions[reverse]
            require(all(p['source_id'] == sid and p['source_sha256'] == source['source_sha256'] for p in (f, r)),
                    'Accepted training readout owner differs')
            ga, gb = [policy33.geometry_features(source['pool'][i], source['width'], source['height']) for i in (a, b)]
            x = math45.pair_features(f['class_logits3'], r['class_logits3'], ga, gb)
            mirrored = math45.pair_features(r['class_logits3'], f['class_logits3'], gb, ga)
            require(np.array_equal(mirrored, -x), 'Fixed feature swap antisymmetry failed')
            ia, ib = map(float, target_ious[sid][[a, b]])
            training.append(dict(pair=[int(a), int(b)], x14=x, target=ib-ia, iou_A=ia, iou_B=ib))
            mapping.append(dict(source_id=sid, source_sha256=source['source_sha256'], a=int(a), b=int(b),
                first_id=first, reverse_id=reverse, target=ib-ia))
        rows.append(dict(source_id=sid, role='train', pairs=training))
    require(len(mapping) == 1204 and used == set(predictions) and len(used) == 2408, 'Full2408 evidence must supply exactly1204 pairs')
    return rows, mapping, np.stack([pair['x14'] for row in rows for pair in row['pairs']])


def build_scope_design(sources, pair_index, predictions, math45, policy33, *, phase):
    """GT-free full candidate/self feature construction; no screen fitting."""
    require(phase in ('screen20', 'confirm19'), 'Only fixed20screen/19confirm scopes')
    expected, role = (20, 'screen') if phase == 'screen20' else (19, 'confirm')
    source_map = _unique(sources, role)
    require(len(source_map) == expected and all(source['role'] == role for source in sources), 'Exact historical source scope required')
    groups = {sid:[] for sid in source_map}; used = set(); result = []
    for pair in pair_index:
        if pair['source_id'] in groups:
            groups[pair['source_id']].append(pair)
    for source in sources:
        sid = source['source_id']; features = {}; self_count = 0
        base = policy33.geometry_features(source['pool'][0], source['width'], source['height'])
        for pair in groups[sid]:
            index = pair['candidate_index']
            require(isinstance(index, Integral) and not isinstance(index, bool) and 0 <= index < len(source['pool'])
                and index not in features, 'Missing/duplicate/unknown candidate index')
            first, reverse = pair['first_id'], pair['reverse_id']
            f, r = predictions[first], predictions[reverse]; used.update((first, reverse))
            require(all(p['source_id'] == sid and p['source_sha256'] == source['source_sha256'] for p in (f, r)),
                    'Accepted screen readout owner differs')
            if pair['same_crop']:
                require(index == 0 and first == reverse, 'Self must adopt the same single successful raw')
                self_count += 1
            else:
                require(index > 0 and first != reverse, 'Every alternative needs both original orders')
            geometry = policy33.geometry_features(source['pool'][index], source['width'], source['height'])
            features[index] = math45.pair_features(f['class_logits3'], r['class_logits3'], base, geometry)
        require(self_count == 1 and set(features) == set(range(len(source['pool']))), 'Full pool and exactly one self/source required')
        matrix = np.stack([features[i] for i in range(len(source['pool']))])
        require(bool((matrix[0] == 0.).all()), 'Self feature must be exactly zero')
        result.append(dict(source=source, design=matrix))
    require(used == set(predictions), 'Missing or unused original screen readout evidence')
    return result


def save_reload_state(path, state, math45, designs):
    """One exclusive NPZ write; all scalars/arrays and predictions must match."""
    require(set(state) == math45.STATE_KEYS, 'Exact frozen45 state fields required')
    with Path(path).open('xb') as stream:
        np.savez(stream, **state)
    with np.load(path, allow_pickle=False) as saved:
        require(set(saved.files) == set(state), 'Saved state key mismatch')
        loaded = {name:saved[name].copy() for name in saved.files}
    require(all(np.asarray(value).shape == loaded[name].shape and np.asarray(value).dtype == loaded[name].dtype
        and np.asarray(value).tobytes(order='C') == loaded[name].tobytes(order='C') for name, value in state.items()),
        'State NPZ did not preserve every bit')
    for design in designs:
        first, second = math45.predict(state, design), math45.predict(loaded, design)
        require(all(first[arm].dtype == second[arm].dtype and first[arm].shape == second[arm].shape
            and first[arm].tobytes() == second[arm].tobytes() for arm in math45.ARMS), 'Prediction changed after exact reload')
    return loaded


def _evaluate_design(scope_design, target_ious, state, math45, policy33, original_geometry_mean, *, phase):
    rows = {arm:[] for arm in math45.ARMS}; predictions = []; zeros = {arm:0 for arm in math45.ARMS}
    for item in scope_design:
        source, matrix = item['source'], item['design']; sid = source['source_id']
        scores = math45.predict(state, matrix)
        decisions = {arm:math45.choose_pool(scores[arm], baseline_index=0) for arm in math45.ARMS}
        ious = target_ious[sid]; geometry = decisions['GEOM11']['selected_index']
        for arm in math45.ARMS:
            require(scores[arm][0] == 0., 'Self expected gain must be exactly zero')
            zeros[arm] += 1; selected = decisions[arm]['selected_index']
            rows[arm].append(dict(source_id=sid, source_sha256=source['source_sha256'], baseline_iou=float(ious[0]),
                selected_iou=float(ious[selected]), geometry_iou=float(ious[geometry]), oracle_iou=float(max(ious)),
                baseline_index=0, selected_index=selected, geometry_index=geometry, baseline_box=source['pool'][0],
                selected_box=source['pool'][selected], predicted_gain=decisions[arm]['predicted_gain']))
        predictions.append(dict(source_id=sid, source_sha256=source['source_sha256'],
            predicted_gains={arm:scores[arm].tolist() for arm in math45.ARMS}, decisions=decisions))
    summaries = {arm:policy33.summarize(rows[arm]) for arm in math45.ARMS}
    quality = math45.quality_checks(summaries['JOINT14'], phase, zeros['JOINT14'], 0,
        summaries['GEOM11']['mean_selected_iou'], original_geometry_mean)
    return dict(primary='JOINT14', phase=phase, summaries=summaries, selected=rows, predictions=predictions,
                self_gain_exact_zero=zeros, invalid_count=0, quality=quality)


def evaluate_scope(sources, pair_index, logits_lookup, target_ious, state, math45, policy33, *, phase, original_geometry_mean):
    """Pure frozen-policy source gains/choices/metrics for same-scope20 or19.

    Caller binds original targets and old13 coefficients for this exact scope;
    screen20's original mean must never be passed as a confirm19 constant.
    """
    design = build_scope_design(sources, pair_index, logits_lookup, math45, policy33, phase=phase)
    return _evaluate_design(design, target_ious, state, math45, policy33, original_geometry_mean, phase=phase)


def _accepted_train(accepted, expected, status, gpu_registration, original_registration, weights):
    require(accepted['status'] == status and accepted['GPU_registration'] == gpu_registration
        and accepted['original_GPU_registration'] == original_registration and accepted['adapter_weights'] == weights
        and accepted['no_utility_targets_read'] is True, 'Already successful exact46 raw QA required')
    entries = {row['id']:row for row in expected}; predictions = accepted['predictions']
    require(len(entries) == len(expected) == len(predictions) and {p['id'] for p in predictions} == set(entries), 'Complete exact46 phase predictions required')
    result = {}
    for prediction in predictions:
        entry = entries[prediction['id']]
        require(prediction['input'] == entry['input'] and prediction['source_id'] == entry['source_id']
            and prediction['source_sha256'] == entry['source_sha256'] and prediction['adapter_weights'] == weights,
            'Accepted46 input/source/final-weight binding differs')
        bound(entry['input'])
        bound(prediction['receipt'])  # Adopt existing first QA; do not read raw or repeat raw checks.
        _logits(prediction['class_logits3']); result[prediction['id']] = prediction
    return result


def run(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU-only fit child must mask CUDA')
    root = Path(root).resolve(); regpath = root/'crop_gain_fit_registration_47.json'
    out = root/OUTPUT; out.mkdir(exist_ok=False)
    try:
        reg = read(regpath)
        require(set(reg) == {'schema', 'deadline_utc', *REF_FIELDS} and reg['schema'] == SCHEMA, 'Exact registered47 fields required')
        for key in REF_FIELDS:
            bound(reg[key])
        require(bound(reg['fit_code']).resolve() == Path(__file__).resolve(), 'Exact frozen47 fit entry required')
        deadline = dt.datetime.fromisoformat(reg['deadline_utc'].replace('Z', '+00:00'))
        require(deadline.tzinfo is not None and dt.datetime.now(dt.timezone.utc) < deadline, 'Inside Goal deadline required')
        math45 = module(reg['math_code'], '_frozen_gain_math45_fit47')
        policy33 = module(reg['policy_code'], '_frozen_crop_policy33_fit47')
        save(out/'claim.json', dict(registration=ref(regpath), primary='JOINT14', new_model_calls=0,
            new_processor_calls=0, raw_QA_repeated=False, old_native_quality='STOP', automatic_confirm=False, automatic_production=False))
        cpu = read(bound(reg['gain_CPU_registration'])); gate = read(bound(reg['gain_input_acceptance']))
        prepared = read(bound(reg['gain_prepared'])); plan = read(bound(reg['gain_plan']))
        require(gate['status'] == 'PASS_ALL_GAIN44_2408_ADOPT2000_NEW408_COMBINATIONS_FIRST_CPU_QA'
            and gate['registration'] == reg['gain_CPU_registration'] and gate['prepared'] == reg['gain_prepared']
            and gate['adopted_inputs'] == 2000 and gate['first_new_combinations'] == 408
            and gate['new_image_processor_calls'] == gate['new_original_decodes'] == 0,
            'Actual44 completed first-combination gate required')
        require(prepared['source_catalog'] == reg['gain_catalog'] and prepared['CPU_targets'] == reg['CPU_targets']
            and prepared['adapter_weights'] == reg['adapter_weights'] and prepared['pair_index'] == plan['pair_index']
            and cpu['CPU_targets'] == reg['CPU_targets'] and cpu['gain_protocol'] == reg['gain_protocol']
            and cpu['fixed_training_completion'] == reg['fixed_training_completion']
            and cpu['adapter_weights'] == reg['adapter_weights'], 'Frozen44 plan/target/weight/protocol bindings differ')
        old_prepared = read(bound(reg['original_screen_prepared'])); old_gate = read(bound(reg['original_screen_input_acceptance']))
        require(old_gate['status'] == 'PASS_ALL_CROP31_TRIPLET_FIRST_CPU_QA'
            and old_gate['prepared'] == reg['original_screen_prepared']
            and old_prepared['source_catalog'] == reg['original_screen_catalog']
            and old_prepared['case_plan'] == reg['original_screen_case_plan']
            and prepared['original_bindings'] == {key:reg[value] for key, value in
                (('old_prepared', 'original_screen_prepared'), ('old_catalog', 'original_screen_catalog'),
                 ('old_case_plan', 'original_screen_case_plan'), ('old_input_gate', 'original_screen_input_acceptance'))},
            'Original accepted31 scope must be adopted unchanged')
        classes = prepared['class_token_ids']
        require(classes == old_prepared['class_token_ids'] and len(classes) == len(set(classes)) == 3, 'Exact native class identities required')
        catalog = read(bound(reg['original_screen_catalog']))['sources']; catalog_map = _unique(catalog, 'original')
        train = read(bound(reg['gain_catalog']))['sources']; train_map = _unique(train, 'gain')
        screen = [source for source in catalog if source['role'] == 'screen']
        require(len(catalog) == 622 and len(train) == 602 and len(screen) == 20
            and set(train_map) == {s['source_id'] for s in catalog if s['role'] == 'train'}, 'Exact original602+20 source scope')
        for sid, source in train_map.items():
            require(all(source[key] == catalog_map[sid][key] for key in source), 'Gain fit catalog differs from original31 source metadata')
        target_ious = joined_targets(catalog, read(bound(reg['CPU_targets']))['sources'])
        original = read(bound(reg['original_comparison'])); training = read(bound(reg['fixed_training_completion']))
        require(original['status'] == 'STOP_NATIVE_CROP_SCREEN' and original['primary'] == 'TRAINED'
            and original['fixed_final_checkpoint'] is True and original['adapter_weights'] == reg['adapter_weights']
            and original['TRAINED_acceptance'] == reg['screen_output_acceptance'] and original['CPU_targets'] == reg['CPU_targets']
            and original['policy_code'] == reg['policy_code'] and cpu['old_STOP'] == reg['original_comparison'], 'Original native CE STOP must stay bound')
        require(training['status'] == 'COMPLETE_FIXED_FINAL500_CROP_COMPARISON_NOT_QUALITY'
            and training['completed_updates'] == 500 and training['successful_micro'] == 2000
            and training['adapter_reload_all288_exact'] is True and training['adapter_weights'] == reg['adapter_weights'], 'Exact final500 artifact required')
        gpu = read(bound(reg['gain_GPU_registration'])); remaining = read(bound(reg['gain_remaining_admission']))
        require(gpu['CPU_registration'] == reg['gain_CPU_registration'] and gpu['input_acceptance'] == reg['gain_input_acceptance']
            and gpu['adapter_weights'] == reg['adapter_weights'] and gpu['fixed_training_completion'] == reg['fixed_training_completion']
            and remaining['original_GPU_registration'] == reg['gain_GPU_registration']
            and remaining['pilot_output_acceptance'] == reg['pilot_output_acceptance']
            and remaining['input_acceptance'] == reg['gain_input_acceptance'], 'Exact46 pilot and remaining admissions required')
        pilot = _accepted_train(read(bound(reg['pilot_output_acceptance'])), prepared['pilot_inputs'],
            'PASS_GAIN_PILOT128_FIRST_RAW_QA', reg['gain_GPU_registration'], reg['gain_GPU_registration'], reg['adapter_weights'])
        rest = _accepted_train(read(bound(reg['remaining_output_acceptance'])), prepared['remaining_inputs'],
            'PASS_GAIN_REMAINING2280_FIRST_RAW_QA', reg['gain_remaining_admission'], reg['gain_GPU_registration'], reg['adapter_weights'])
        require(len(pilot) == 128 and len(rest) == 2280 and not set(pilot) & set(rest)
            and len({p['source_id'] for p in pilot.values()}) == 32 and len({p['source_id'] for p in rest.values()}) == 570
            and not {p['source_id'] for p in pilot.values()} & {p['source_id'] for p in rest.values()}, 'Exact disjoint32/570 readout partition')
        first32 = {source['source_id'] for source in sorted(train, key=lambda source:(source['source_sha256'], source['source_id']))[:32]}
        require({p['source_id'] for p in pilot.values()} == first32, 'Pilot must remain the fixed source-SHA-first32')
        train_predictions = {**pilot, **rest}
        require({entry['id'] for entry in prepared['train_inputs']} == set(train_predictions)
            and len(prepared['train_inputs']) == 2408, 'Full original2408 readout inventory required')
        train_rows, train_mapping, train_design = build_training_rows(train, target_ious, plan['pair_index'], train_predictions, math45, policy33)
        # Screen receipts are already independently QAd. Extract small saved class logits only.
        accepted = read(bound(reg['screen_output_acceptance']))
        require(accepted['status'] == 'PASS_CROP_TRAINED_SCREEN_FINAL500_FIRST_QA'
            and accepted['training_completion'] == reg['fixed_training_completion']
            and accepted['registration'] == original['registration'], 'Adopt exact33 final500 screen first QA')
        expected = {entry['id']:entry for entry in old_prepared['screen_inputs']}
        require(len(expected) == len(accepted['predictions']) == 240
            and {p['id'] for p in accepted['predictions']} == set(expected), 'Adopt all original240 screen inputs')
        screen_predictions = {}
        for prediction in accepted['predictions']:
            entry = expected[prediction['id']]; receipt = read(bound(prediction['receipt']))
            bound(entry['input'])
            require(prediction['input'] == entry['input'] == receipt['input'] and receipt['id'] == prediction['id']
                and receipt['source_id'] == prediction['source_id'] == entry['source_id']
                and receipt['source_sha256'] == prediction['source_sha256']
                and receipt['model_role'] == 'TRAINED_screen' and receipt['class_token_ids'] == classes,
                'Adopted screen receipt/source/class identity differs')
            _logits(receipt['class_logits'])
            screen_predictions[prediction['id']] = dict(source_id=prediction['source_id'], source_sha256=prediction['source_sha256'],
                class_logits3=receipt['class_logits'])
        screen_plan = read(bound(reg['original_screen_case_plan']))
        require(screen_plan['GT_used_for_input_or_pair_choice'] is False, 'Original screen pairs must remain GT-free')
        screen_design = build_scope_design(screen, screen_plan['pair_index'], screen_predictions, math45, policy33, phase='screen20')
        original_mean = _finite(original['reports']['TRAINED']['summary']['mean_geometry_iou'])
        old_geometry_rows = original['selected']['TRAINED']
        require({row['source_id'] for row in old_geometry_rows} == {s['source_id'] for s in screen}
            and len(old_geometry_rows) == 20, 'Original GEOM13 must have this same20 scope')
        for row in old_geometry_rows:
            source = catalog_map[row['source_id']]; index = row['geometry_index']
            require(row['source_sha256'] == source['source_sha256'] and isinstance(index, int) and 0 <= index < len(source['pool'])
                and row['geometry_iou'] == float(target_ious[row['source_id']][index]), 'Original GEOM13 selection/IoU binding differs')
        require(abs(float(np.mean([row['geometry_iou'] for row in old_geometry_rows]))-original_mean) <= 1e-15,
                'Original GEOM13 reported mean inconsistent with same-scope stored selections')
        geometry_receipt = read(bound(original['geometry_control'])); bound(geometry_receipt['coefficients'])
        require(geometry_receipt['parameters'] == 13 and geometry_receipt['training_sources'] == 602
            and geometry_receipt['eval_target_fitted'] is False, 'Adopt original frozen GEOM13 control; never replace/refit it')
        require(dt.datetime.now(dt.timezone.utc) < deadline, 'No new fit after Goal deadline')
        state, fit_report = math45.fit(train_rows)  # Exactly one fit call, three fixed solves.
        require(fit_report['sources'] == 602 and fit_report['unordered_pairs'] == 1204 and fit_report['solves'] == 3,
                'Exact frozen source-equal fit scope')
        loaded = save_reload_state(out/'critic_state.npz', state, math45,
            [train_design]+[item['design'] for item in screen_design])
        save(out/'fit_report.json', fit_report); save(out/'train_pair_mapping.json', dict(rows=train_mapping, CPU_targets=reg['CPU_targets']))
        evaluation = _evaluate_design(screen_design, target_ious, loaded, math45, policy33, original_mean, phase='screen20')
        admitted = evaluation['quality']['admitted']
        reports = {arm:dict(summary=evaluation['summaries'][arm], self_gain_exact_zero=evaluation['self_gain_exact_zero'][arm])
                   for arm in math45.ARMS}
        reports['JOINT14']['quality'] = evaluation['quality']
        result = dict(status='PASS_GAIN_CRITIC_SCREEN20_ONLY' if admitted else 'STOP_GAIN_CRITIC_SCREEN20_REJECTED', primary='JOINT14',
            evaluation=evaluation, state=ref(out/'critic_state.npz'), fit_report=ref(out/'fit_report.json'),
            critic_weights=ref(out/'critic_state.npz'), reports=reports, fixed_final_checkpoint=True,
            screen_output_acceptance=reg['screen_output_acceptance'], source_catalog=reg['original_screen_catalog'],
            geometry_control=original['geometry_control'], production_admitted=False,
            training_pair_mapping=ref(out/'train_pair_mapping.json'), registration=ref(regpath), adapter_weights=reg['adapter_weights'],
            input_bindings={key:reg[key] for key in REF_FIELDS if key != 'fit_code'},
            original_geometry_control=dict(scope='SCREEN20_ONLY_NOT_A_CONFIRM19_CONSTANT', result=reg['original_comparison'],
                receipt=original['geometry_control'], coefficients=geometry_receipt['coefficients'], mean_iou=original_mean, adopted_sources=20),
            exact_state_reload=True, exact_train_and_screen_predictions_reload=True, new_fit_calls=1, fixed_ridge_solves=3,
            old_native_CE_quality='STOP', new_model_calls=0, new_processor_calls=0, raw_QA_repeated=False,
            IoU_targets_recomputed=False, screen_targets_fitted=False, threshold_search=False, checkpoint_selection=False,
            confirm_admitted=admitted, automatic_confirm=False, production_prepare_approved=False, automatic_production=False,
            historical_exposure=True, new_blind_sources=0, official_joint_metric=False,
            confirm_requires_separate_registered_scope_and_same_old_GEOM13_coefficients=True)
        save(out/'result.json', result)
        print('GAIN47_SCREEN', result['status'], evaluation['summaries']['JOINT14'], flush=True)
        return result
    except BaseException as error:
        save(out/'failure.json', dict(status='FAIL_PRESERVE_NO_AUTOMATIC_RETRY', error=repr(error), traceback=traceback.format_exc(),
            preserve_all_success=True, old_native_CE_quality='STOP', new_model_calls=0, automatic_confirm=False, automatic_production=False))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--root', type=Path, required=True)
    run(parser.parse_args().root)
