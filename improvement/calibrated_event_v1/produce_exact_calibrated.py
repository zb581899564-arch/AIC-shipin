"""Conditional fixed lookup inference and one package; no models/data are fitted."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ.setdefault('OPENBLAS_NUM_THREADS', '2')
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile
import numpy as np

ROOT = Path('/home/inspur/aic_video_work/calibrated_event_20261018_v1')
EVENT = Path('/home/inspur/aic_video_work/meaningful_residual_20261018_v1')
sys.path.insert(0, str(ROOT/'code_v1'))
import calibrate as cal
sys.path.insert(0, str(EVENT/'code_v1'))
import event_runtime as rt
sys.path.insert(0, str(EVENT/'production_code_v1'))
from package_event import dump, histories
sys.path.insert(0,str(ROOT/'source_normalized_code_v2'))
from multiple_choice import multiple_choice_knapsack


def main():
    cal.deadline()
    admission = cal.read(ROOT/'production_exact_admission_03.json')
    cal.require(admission['allow_one_fixed_PAVA_package'] is True and admission['mechanism'] == 'RAW_PAVA_GLOBAL_OPTIONS' and admission['EM_allowed'] is False, 'Explicit reviewed admission, no prior adaptation')
    cal.bound(admission['confirmation_ref'])
    for method_ref in admission['method_refs']:
        cal.bound(method_ref)
    cal.require(Path(multiple_choice_knapsack.__code__.co_filename).resolve() == cal.bound(admission['solver_ref']).resolve(), 'Actual frozen prospective exact-budget solver')
    frozen = cal.read(ROOT/'frozen_selection.json')
    model = dict(np.load(cal.bound(frozen['weights_ref'])))
    accepted = cal.read(EVENT/'formal_inputs_01/completion.json')
    cal.require(accepted['status'] == 'PASS426_FIRST_NATIVE_EVENT_DESCRIPTOR_QA', 'Adopt prior complete native candidate QA')
    inherited = {r['id']:r for r in cal.read(rt.OLD/'feature_completion.json')['sources']}
    out = ROOT/'production_exact_03'
    out.mkdir()
    cal.save(out/'start.json', dict(admission_ref=cal.ref(ROOT/'production_exact_admission_03.json'), frozen_model_ref=frozen['weights_ref'], adopted_native_candidates_ref=cal.ref(EVENT/'formal_inputs_01/completion.json'), code_ref=cal.ref(Path(__file__)), utc=cal.utc()))
    items, qa = [], []
    for receipt_ref in accepted['sources']:
        row = cal.read(cal.bound(receipt_ref))
        sid = row['sid']
        baseline = np.load(cal.bound(row['input_ref']))['baseline']
        groups_ref = rt.OLD/'inputs'/sid/'native.npz'
        clock_ref = row['clock_ref']
        groups = np.load(cal.bound(dict(path=str(groups_ref), sha256=inherited[sid]['native_sha256'])))['groups']
        score = np.load(cal.bound(row['semantic_output_ref']))['residual']
        clock = cal.read(cal.bound(clock_ref))
        cal.require(baseline.dtype == np.bool_ and len(groups) == len(baseline) == len(clock['normalized_exact_pts']) and groups.min() == 0 and groups.max()+1 == len(score), 'Actual complete formal semantic/native mapping')
        probability = cal.probability(score, model)[groups]
        gain, stats = cal.gains(baseline, probability, row['candidates'])
        # Independent direct count audit of every candidate, separate from prefix implementation.
        direct = []
        base_tp = sum(map(float, probability[baseline]))
        total_p = sum(map(float, probability))
        base_den = int(baseline.sum())+total_p
        base_f = 0.0 if base_den == 0 else 2*base_tp/base_den
        for candidate in row['candidates']:
            added = ~baseline[candidate['left']:candidate['right']]
            values = probability[candidate['left']:candidate['right']][added]
            cal.require(int(added.sum()) == candidate['added_frames'], 'Independent unique addition count')
            direct.append(2*(base_tp+sum(map(float, values)))/(int(baseline.sum())+len(values)+total_p)-base_f)
        cal.require(np.allclose(gain, direct, atol=2e-12, rtol=1e-10), 'First full new lookup/utility output QA')
        index = None if not len(gain) or gain.max() <= 0 else int(gain.argmax())
        action = None if index is None else dict(sid=sid, candidate_index=index, added_frames=row['candidates'][index]['added_frames'], predicted_gain=float(gain[index]))
        path = out/(sid+'_output.npz')
        with path.open('xb') as f:
            np.savez(f, probability=probability, estimated_gain=gain)
        qa.append(dict(sid=sid, old_candidate_ref=receipt_ref, native_group_ref=cal.ref(groups_ref), clock_ref=clock_ref, old_semantic_ref=row['semantic_output_ref'], new_output_ref=cal.ref(path), candidates=len(gain), direct_all_candidate_equal=True, pava_ref=frozen['weights_ref']))
        items.append(dict(sid=sid, baseline=baseline, candidates=row['candidates'], action=action, options=[dict(candidate_index=i,added_frames=c['added_frames'],predicted_gain=float(gain[i]))for i,c in enumerate(row['candidates'])if gain[i]>0], stats=stats))
    cal.require(len(items) == 426 and {v['sid'] for v in items} == {str(i) for i in range(426)}, 'Complete426 new inference and output QA')
    cal.save(out/'input_output_acceptance.json', dict(status='PASS426_FIRST_FROZEN_LOOKUP_INPUT_OUTPUT_QA', sources=qa, new_8B_calls=0, old_processor_or_model_reexecution=0, official_labels_read=False, official_prior_fit=False))
    renderer, _ = rt.old_modules()
    base_ref = cal.read(EVENT/'registration.json')['baseline_ref']
    with zipfile.ZipFile(cal.bound(base_ref)) as z:
        base = [json.loads(line) for line in z.read('predictions.jsonl').splitlines()]
    baseline_frames = {(v['video_id'], p['frame']):p['bboxes'] for v in base for p in v['predictions']}
    selected = set(baseline_frames)
    exact = multiple_choice_knapsack({v['sid']:v['options'] for v in items},len(selected)//10)
    chosen_ids = set(exact['chosen'])
    cal.save(out/'exact_global_selection.json',exact)
    decisions = []
    for v in items:
        chosen = None
        if v['sid'] in chosen_ids:
            chosen = v['candidates'][exact['chosen'][v['sid']]]
            selected.update((v['sid'], i) for i in range(chosen['left'], chosen['right']))
        decisions.append(dict(sid=v['sid'], chosen=chosen, successful_null=v['action'] is None, omitted_by_budget=v['action'] is not None and chosen is None, estimated_gain=None if chosen is None else next(x['predicted_gain']for x in v['options']if x['candidate_index']==exact['chosen'][v['sid']])))
    cal.require(0 < len(selected)-len(baseline_frames) <= len(baseline_frames)//10, 'Meaningful distinct addition within original exposure budget')
    actual = 8782557449+sum(v.size for v in model.values())
    cal.require(actual <= 9_000_000_000, 'All actual base/TIME/semantic/lookup parameters<=9B')
    rows, provenance, chosen, inputs = renderer.render(selected)
    current = {(v['video_id'], p['frame']):p['bboxes'] for v in rows for p in v['predictions']}
    cal.require(len(rows) == 426 and all(v['predictions'] for v in rows) and set(current) == selected, '426 nonempty actual native render')
    cal.require(set(baseline_frames) <= set(current) and all(current[k] == value for k,value in baseline_frames.items()), 'Protected40.47 every original native frame/bbox unchanged')
    for row in rows:
        row['model_params_b'] = actual/1e9
    canonical = rt.canonical(rows)
    history = set(histories(cal.read(cal.bound(inputs['history']))))
    current_history = set(histories(cal.read(cal.bound(admission['current_delivered_history_ref']))))
    cal.require(len(current_history) == admission['current_delivered_history_canonical_count'] and current_history, 'Authoritative delivered-history inventory complete')
    history.update(current_history)
    history.update(cal.read(rt.OLD/'production_registration.json')['historical_prediction_sha256'])
    history.add(rt.canonical(base))
    history.add(cal.read(rt.SRC/'completion.json')['canonical_sha256'])
    for prior in (EVENT/'packages').glob('*/completion.json'):
        history.add(cal.read(prior)['canonical_sha256'])
    cal.require(canonical not in history, 'Not any previous delivered or renamed candidate')
    cal.bound(admission['official_rule_receipt_ref'])
    dump(out/'predictions.jsonl', rows)
    dump(out/'selected.jsonl', chosen)
    dump(out/'provenance.jsonl', provenance)
    cal.save(out/'metadata.json', cal.read(cal.bound(inputs['metadata'])))
    pending = out/'candidate_CALIBRATED_EVENT_EXACT.PENDING.zip'
    with zipfile.ZipFile(pending, 'x', zipfile.ZIP_DEFLATED) as z:
        z.write(out/'predictions.jsonl', 'predictions.jsonl')
    subprocess.run([str(rt.PY), '-B', str(rt.RUN/'baseline_a_pts_v1/vendor/independent_validate.py'), '--strict-loader-root', str(rt.RUN/'baseline_a_pts_v1/vendor/frozen_strict_loader'), '--metadata', str(out/'metadata.json'), '--selected', str(out/'selected.jsonl'), '--predictions', str(out/'predictions.jsonl'), '--provenance', str(out/'provenance.jsonl'), '--zip', str(pending), '--report', str(out/'independent_validation.json')], check=True)
    checks = cal.read(out/'independent_validation.json')['checks']
    cal.require(len(checks) == 11 and all(checks.values()), 'Actual independent11 strict acceptance')
    with zipfile.ZipFile(pending) as z:
        cal.require(z.namelist() == ['predictions.jsonl'] and z.testzip() is None and hashlib.sha256(z.read('predictions.jsonl')).hexdigest() == cal.sha(out/'predictions.jsonl'), 'Single member/CRC/memberSHA')
    final = out/'candidate_CALIBRATED_EVENT_EXACT.zip'
    pending.rename(final)
    cal.save(out/'completion.json', dict(status='NEW_ENGINEERING_ACCEPTED_FIXED_RAW_PAVA_EXACT_OPTIONS_EFFECT_UNKNOWN', zip=cal.ref(final), member_sha256=cal.sha(out/'predictions.jsonl'), canonical_sha256=canonical, records=426, frames=len(current), added_frames=len(current)-len(baseline_frames), removed_frames=0, changed_sources=len(chosen_ids), successful_source_nulls=sum(v['successful_null'] for v in decisions), actual_added_seconds=sum(float(rt.F(v['chosen']['added_duration_exact'])) for v in decisions if v['chosen']), actual_resident_parameters=actual, all_baseline_boxes_preserved=True, independent11strict=True, new_8B_calls=0, official_prior_fit=False, original_three_packages_unchanged=True, decisions=decisions, website_submitted=False, official_score='UNKNOWN', utc=cal.utc()))


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        import traceback
        cal.save(ROOT/('production_exact_failure_'+str(os.getpid())+'.json'), dict(error=repr(error), traceback=traceback.format_exc(), successes_preserved=True, utc=cal.utc()))
        raise
