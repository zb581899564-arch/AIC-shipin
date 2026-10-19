"""Single CPU-only cached-output representation experiment; no model calls.

--root reads crop_full_readout_registration_52.json with exact refs:
run_code,extract_code,math_code,policy_code,protocol,model_config,adapter_weights,
fixed_training_completion,source_catalog,case_plan,CPU_targets,gain_prepared,
pilot_output_acceptance,remaining_output_acceptance,screen_output_acceptance,
old_gain_result47. Other fields: schema,deadline_utc,max_seconds(900).
Output crop_full_readout_52 is exclusive. New feature cache precedes any fit;
failure preserves it for explicit remaining-stage recovery, never automatic retry.
"""
import argparse
import datetime as dt
import importlib.util
import os
from pathlib import Path
import sys
import time
import traceback

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'pair_code_17'))
from pair_common import read, save, ref, bound, require, utc

REFS = ('run_code', 'extract_code', 'math_code', 'policy_code', 'protocol', 'model_config',
    'adapter_weights', 'fixed_training_completion', 'source_catalog', 'case_plan', 'CPU_targets',
    'gain_prepared', 'pilot_output_acceptance', 'remaining_output_acceptance',
    'screen_output_acceptance', 'old_gain_result47')


def module(reference, name):
    path = bound(reference)
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    sys.modules[name] = obj
    spec.loader.exec_module(obj)
    return obj


def cache_features(path, lookup):
    ids = sorted(lookup)
    data = dict(ids=np.array(ids, dtype='U24'),
        readouts=np.stack([lookup[k]['readout4096'] for k in ids]),
        digits=np.stack([lookup[k]['class_logits3'] for k in ids]))
    require(data['readouts'].shape == (2648, 4096) and data['digits'].shape == (2648, 3), 'Complete fixed compact readout cache')
    with path.open('xb') as f:
        np.savez(f, **data)
    with np.load(path, allow_pickle=False) as saved:
        require(set(saved.files) == set(data) and all(saved[k].dtype == value.dtype
                and saved[k].shape == value.shape and saved[k].tobytes() == value.tobytes()
                for k, value in data.items()), 'First feature cache exact save/reload')
    return {k:{field:value for field, value in lookup[k].items()
               if field not in ('readout4096', 'class_logits3')} for k in ids}


def training_rows(sources, pairs, lookup, target_ious, policy):
    grouped = {s['source_id']: [] for s in sources}
    for pair in pairs:
        require(pair['source_id'] in grouped, 'Registered train pair scope differs')
        grouped[pair['source_id']].append(pair)
    result, used = [], set()
    for source in sources:
        sid = source['source_id']
        require(source['role'] == 'train' and len(grouped[sid]) == 2, 'Exact original602 two-pair train scope')
        records = []
        for pair in grouped[sid]:
            a, b = pair['a'], pair['b']
            require(0 <= a < b < len(source['pool']) and pair['source_sha256'] == source['source_sha256'], 'Canonical original pair owner')
            f, r = lookup[pair['first_id']], lookup[pair['reverse_id']]
            require(all(v['source_id'] == sid and v['source_sha256'] == source['source_sha256'] for v in (f, r)), 'Readout owner differs')
            used.update((pair['first_id'], pair['reverse_id']))
            ga, gb = [policy.geometry_features(source['pool'][i], source['width'], source['height']) for i in (a, b)]
            ia, ib = target_ious[sid][a], target_ious[sid][b]
            records.append(dict(pair=[a, b], x4096=np.asarray(f['readout4096'])-np.asarray(r['readout4096']),
                digit_delta3=np.asarray(f['class_logits3'])-np.asarray(r['class_logits3']),
                geometry_delta11=(gb-ga)[1:12], target=ib-ia, iou_A=ia, iou_B=ib))
        result.append(dict(source_id=sid, role='train', pairs=records))
    require(len(result) == 602 and len(used) == 2408, 'Exact602/1204 unordered/2408 ordered scope')
    return result


def scope_design(sources, pairs, lookup, policy):
    result, used = [], set()
    require(len(sources) == 20 and len({s['source_id'] for s in sources}) == 20, 'Fixed screen20 scope')
    for source in sources:
        sid = source['source_id']; pool = source['pool']
        require(source['role'] == 'screen', 'Only historical20 development sources')
        base = policy.geometry_features(pool[0], source['width'], source['height'])
        vectors = {}
        for pair in pairs:
            if pair['source_id'] != sid:
                continue
            i = pair['candidate_index']
            require(i not in vectors and 0 <= i < len(pool), 'Unique complete candidate scope')
            f, r = lookup[pair['first_id']], lookup[pair['reverse_id']]
            require(all(v['source_id'] == sid and v['source_sha256'] == source['source_sha256'] for v in (f, r)), 'Screen readout owner differs')
            require((i == 0 and pair['same_crop'] and pair['first_id'] == pair['reverse_id'])
                    or (i > 0 and not pair['same_crop'] and pair['first_id'] != pair['reverse_id']), 'Exact self/two-order alternative')
            used.update((pair['first_id'], pair['reverse_id']))
            vectors[i] = (np.asarray(f['readout4096'])-np.asarray(r['readout4096']),
                (policy.geometry_features(pool[i], source['width'], source['height'])-base)[1:12])
        require(set(vectors) == set(range(len(pool))), 'Every original candidate and self required')
        result.append(dict(source=source, X=np.stack([vectors[i][0] for i in range(len(pool))]),
            G=np.stack([vectors[i][1] for i in range(len(pool))])))
    require(used == {k for k, v in lookup.items() if v['source_id'] in {s['source_id'] for s in sources}}, 'All exact screen outputs consumed')
    return result


def evaluate(design, targets, state, math51, policy33, old47):
    arms = ('FULL43', 'GEOM11')
    rows = {a: [] for a in arms}; zero = {a: 0 for a in arms}; predictions = []
    old_choices = {v['source_id']: v['decisions'] for v in old47['evaluation']['predictions']}
    differs47 = differs_margin = False
    for item in design:
        source = item['source']; sid = source['source_id']; scores = math51.predict(state, item['X'], item['G'])
        negative = math51.predict(state, -item['X'], -item['G'])
        require(all(np.array_equal(negative[a], -scores[a]) for a in arms), 'Swap must strictly negate actual predictions')
        decisions = {a: math51.choose_pool(scores[a], baseline_index=0) for a in arms}
        ious = targets[sid]; gi = decisions['GEOM11']['selected_index']
        for arm in arms:
            require(scores[arm][0] == 0., 'Actual self must be zero')
            zero[arm] += 1; i = decisions[arm]['selected_index']
            rows[arm].append(dict(source_id=sid, source_sha256=source['source_sha256'], baseline_iou=ious[0],
                selected_iou=ious[i], geometry_iou=ious[gi], oracle_iou=max(ious), baseline_index=0,
                selected_index=i, geometry_index=gi, baseline_box=source['pool'][0], selected_box=source['pool'][i]))
        selected = decisions['FULL43']['selected_index']
        differs47 |= selected != old_choices[sid]['JOINT14']['selected_index']
        differs_margin |= selected != old_choices[sid]['MARGIN1']['selected_index']
        predictions.append(dict(source_id=sid, source_sha256=source['source_sha256'], decisions=decisions,
            predicted_gains={a: scores[a].tolist() for a in arms}))
    summaries = {a: policy33.summarize(rows[a]) for a in arms}
    quality = math51.quality_checks(summaries['FULL43'], 'screen20', zero['FULL43'], 0,
        summaries['GEOM11']['mean_selected_iou'], old47['original_geometry_control']['mean_iou'],
        action_differs_old47_margin=bool(differs47 and differs_margin))
    return dict(summaries=summaries, selected=rows, predictions=predictions, quality=quality,
        self_gain_exact_zero=zero, differs_old47=bool(differs47), differs_old_margin=bool(differs_margin))


def run(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU-only first cached-output task')
    import torch
    torch.set_num_threads(2)
    regpath = root/'crop_full_readout_registration_52.json'; reg = read(regpath)
    require(set(reg) == {'schema', 'deadline_utc', 'max_seconds', *REFS}
            and reg['schema'] == 'FULL_LAST_LANGUAGE_READOUT_V52' and reg['max_seconds'] == 900,
            'Exact registered single CPU experiment')
    for name in REFS:
        bound(reg[name])
    require(bound(reg['run_code']) == Path(__file__).resolve(), 'Exact new52 entry')
    deadline = dt.datetime.fromisoformat(reg['deadline_utc'].replace('Z', '+00:00'))
    require(dt.datetime.now(dt.timezone.utc) < deadline, 'Inside original Goal window')
    started = time.monotonic(); out = root/'crop_full_readout_52'; out.mkdir(exist_ok=False)
    save(out/'claim.json', dict(utc=utc(), registration=ref(regpath), new_model_calls=0,
        new_decode_or_processor=0, old_QA_adopted=True, old44_47_remain_STOP=True))
    try:
        extract = module(reg['extract_code'], '_full_readout_extract51')
        math51 = module(reg['math_code'], '_full_readout_math51')
        policy = module(reg['policy_code'], '_frozen_crop_policy33_full52')
        cfg = read(bound(reg['model_config'])); training = read(bound(reg['fixed_training_completion']))
        old = read(bound(reg['old_gain_result47']))
        require(training['completed_updates'] == 500 and training['successful_micro'] == 2000
                and training['adapter_reload_all288_exact'] is True and training['adapter_weights'] == reg['adapter_weights']
                and training['base_fingerprint']['sha256'] == cfg['expected_base_sha256']
                and old['status'] == 'STOP_GAIN_CRITIC_SCREEN20_REJECTED'
                and old['adapter_weights'] == reg['adapter_weights'] and old['source_catalog'] == reg['source_catalog']
                and old['screen_output_acceptance'] == reg['screen_output_acceptance'], 'Immutable final500 / prior STOP scope')
        prepared = read(bound(reg['gain_prepared'])); plan = read(bound(reg['case_plan']))
        all_sources = read(bound(reg['source_catalog']))['sources']
        train = [s for s in all_sources if s['role'] == 'train']; screen = [s for s in all_sources if s['role'] == 'screen']
        require(len(train) == 602 and len(screen) == 20 and len({s['source_sha256'] for s in all_sources}) == 622,
                'Exact original disjoint602train/20screen')
        classes = prepared['class_token_ids']
        indices = extract.select_indices(cfg['expected_base_sha256'], reg['adapter_weights']['sha256'], classes)
        save(out/'column_registration.json', dict(indices=indices.tolist(), model_base_sha=cfg['expected_base_sha256'],
            crop_sha=reg['adapter_weights']['sha256'], actual_class_ids=classes, recipe='FULL_VOCAB_SWAP32_V51',
            common_all_sources=True, semantic_token_selection=False))
        lookup, reports = {}, []
        scopes = [('pilot_output_acceptance', 'PASS_GAIN_PILOT128_FIRST_RAW_QA', 'GAIN_pilot128', 128),
            ('remaining_output_acceptance', 'PASS_GAIN_REMAINING2280_FIRST_RAW_QA', 'GAIN_remaining2280', 2280),
            ('screen_output_acceptance', 'PASS_CROP_TRAINED_SCREEN_FINAL500_FIRST_QA', 'TRAINED_screen', 240)]
        for key, status, role, count in scopes:
            require(time.monotonic()-started < 900 and dt.datetime.now(dt.timezone.utc) < deadline, 'Inside CPU/Goal budgets')
            accepted = read(bound(reg[key]))
            require(accepted['status'] == status and len(accepted['predictions']) == count, 'Exact adopted first-QA export')
            if key == 'screen_output_acceptance':
                require(accepted['training_completion'] == reg['fixed_training_completion'], 'Actual final500 screen identity')
            else:
                require(accepted['adapter_weights'] == reg['adapter_weights'], 'Actual final500 train identity')
            part, report = extract.collect(accepted['predictions'], indices, reg['adapter_weights'],
                expected_role=role, class_token_ids=classes, load_json=lambda p: read(p),
                load_tensor=lambda p: torch.load(p, map_location='cpu', weights_only=True), bound=bound)
            require(len(part) == count and not set(part) & set(lookup), 'All adopted roles disjoint')
            lookup.update(part); reports.append(dict(accepted=reg[key], evidence=report))
        require(set(lookup) == {e['id'] for e in prepared['train_inputs']} | {p['id'] for p in read(bound(reg['screen_output_acceptance']))['predictions']},
                'Exact registered2648 first cached readouts, no additions')
        bindings = cache_features(out/'features.npz', lookup)
        save(out/'feature_bindings.json', bindings)
        save(out/'feature_completion.json', dict(status='FIRST_FULL4096_READOUT_CACHE_COMPLETE_NOT_QUALITY',
            registration=ref(regpath), features=ref(out/'features.npz'), bindings=ref(out/'feature_bindings.json'),
            columns=ref(out/'column_registration.json'), rows=2648, reports=reports,
            elapsed_seconds=time.monotonic()-started, new_model_calls=0, old_QA_repeated=False))
        targets = read(bound(reg['CPU_targets']))['sources']
        target_map = {t['source_id']: t for t in targets}; source_map = {s['source_id']: s for s in all_sources}
        require(len(target_map) == len(source_map) == 622 and set(target_map) == set(source_map), 'Exact original human reference scope')
        target_ious = {}
        for sid, source in source_map.items():
            target = target_map[sid]
            require(target['source_sha256'] == source['source_sha256'] and target['role'] == source['role']
                    and target['reference_modified'] is False and target['baseline_index'] == 0
                    and len(target['candidate_ious']) == len(source['pool']), 'Original unmodified target identity')
            target_ious[sid] = target['candidate_ious']
        rows = training_rows(train, prepared['pair_index'], lookup, target_ious, policy)
        require(time.monotonic()-started < 900 and dt.datetime.now(dt.timezone.utc) < deadline, 'Fit inside original CPU/Goal budgets')
        state, fit_report = math51.fit(rows)
        with (out/'state.npz').open('xb') as f:
            np.savez(f, **state)
        with np.load(out/'state.npz', allow_pickle=False) as saved:
            loaded = {k: saved[k].copy() for k in saved.files}
        require(set(loaded) == set(state) and all(loaded[k].shape == np.asarray(v).shape
                and loaded[k].dtype == np.asarray(v).dtype and loaded[k].tobytes() == np.asarray(v).tobytes()
                for k, v in state.items()), 'Exact complete wide state save/reload')
        save(out/'fit_report.json', fit_report)
        train_X = np.stack([p['x4096'] for row in rows for p in row['pairs']])
        train_G = np.stack([p['geometry_delta11'] for row in rows for p in row['pairs']])
        original_train, loaded_train = math51.predict(state, train_X, train_G), math51.predict(loaded, train_X, train_G)
        require(all(original_train[k].tobytes() == loaded_train[k].tobytes() for k in original_train),
                'Exact train predictions after state reload')
        require(time.monotonic()-started < 900 and dt.datetime.now(dt.timezone.utc) < deadline,
                'Completed fit and state saved inside CPU/Goal budgets')
        design = scope_design(screen, plan['pair_index'], lookup, policy)
        for item in design:
            a, b = math51.predict(state, item['X'], item['G']), math51.predict(loaded, item['X'], item['G'])
            require(all(a[k].tobytes() == b[k].tobytes() for k in a), 'Exact screen prediction save/reload')
        evaluation = evaluate(design, target_ious, loaded, math51, policy, old)
        require(time.monotonic()-started < 900 and dt.datetime.now(dt.timezone.utc) < deadline,
                'No quality terminal after registered CPU/Goal budgets')
        admitted = evaluation['quality']['admitted']
        result = dict(status='PASS_WIDE_READOUT_SCREEN20_ONLY' if admitted else 'STOP_WIDE_READOUT_SCREEN20_REJECTED',
            registration=ref(regpath), primary='FULL43', evaluation=evaluation, state=ref(out/'state.npz'),
            columns=ref(out/'column_registration.json'), features=ref(out/'feature_completion.json'),
            fit_report=ref(out/'fit_report.json'), adapter_weights=reg['adapter_weights'],
            original_geometry_control=old['original_geometry_control'], confirm_admitted=admitted,
            production_admitted=False, automatic_confirm=False, automatic_production=False,
            old44_47_quality='STOP', historical_sources_not_blind=True, new_model_calls=0,
            elapsed_seconds=time.monotonic()-started, no_new_visual_observation=True)
        save(out/'result.json', result)
        print('WIDE52', result['status'], {k:v for k,v in evaluation['summaries']['FULL43'].items() if k != 'per_source'}, flush=True)
    except BaseException as error:
        if 'math51' in locals() and isinstance(error, math51.ReadoutStop):
            save(out/'result.json', dict(status='STOP_WIDE_READOUT_STRUCTURAL_INFORMATION_GATE',
                error=str(error), diagnostics=error.diagnostics, registration=ref(regpath),
                feature_completion=ref(out/'feature_completion.json'), confirm_admitted=False, production_admitted=False,
                new_model_calls=0, automatic_retry=False))
            print('WIDE52_STRUCTURAL_STOP', str(error), flush=True)
            return
        save(out/'failure.json', dict(utc=utc(), error=repr(error), traceback=traceback.format_exc(),
            feature_cache_preserved=(out/'feature_completion.json').exists(), preserve_all_success=True,
            automatic_retry=False, new_model_calls=0, automatic_production=False))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    run(parser.parse_args().root)
