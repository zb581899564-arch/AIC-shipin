"""One frozen new-source comparison; reference values enter after inference."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import sys
from pathlib import Path
import numpy as np
from fractions import Fraction as F
from bisect import bisect_left

ROOT = Path('/home/inspur/aic_video_work/calibrated_event_20261018_v1')
sys.path.insert(0, str(ROOT/'code_v1'))
from calibrate import read, ref, bound, require, save, utc, probability, gains, metric, knapsack
from event_features import proposals


def main():
    pipeline_root = Path(sys.argv[1])
    require(pipeline_root == ROOT/'confirm4_02', 'Explicit registered confirmation pipeline root')
    prepared = read(pipeline_root/'stages/finalize/completion.json')
    require(prepared['status'] == 'PASS' and prepared['labels_read'] is False and len(prepared['sources']) == 4, 'Complete first model/output QA before confirmation inference')
    require(read(ROOT/'confirm4_reference_01/native_admission_for_model.json')['status'] == 'PASS', 'Unmodified human endpoint admission')
    frozen = read(ROOT/'frozen_selection.json')
    model = dict(np.load(bound(frozen['weights_ref'])))
    out = ROOT/'new4_comparison_01'
    out.mkdir()
    items = []
    for s in prepared['sources']:
        value = np.load(bound(s['data_ref']))
        clock = read(bound(s['clock_ref']))
        baseline, groups, score = value['baseline'], value['groups'], value['semantic_score']
        require(baseline.dtype == np.bool_ and len(baseline) == len(groups) == len(clock['normalized_exact_pts']) and groups.min() == 0 and groups.max()+1 == len(score) and np.isfinite(score).all(), 'Complete new source native semantic field')
        candidates = proposals(clock, baseline)
        p = probability(score, model)[groups]
        gain, stats = gains(baseline, p, candidates)
        field = score[groups]
        mean_score = np.asarray([field[c['left']:c['right']][~baseline[c['left']:c['right']]].mean() for c in candidates])
        def action(values):
            if not len(values) or values.max() <= 0:
                return None
            index = int(values.argmax())
            return dict(sid=s['sid'], candidate_index=index, added_frames=candidates[index]['added_frames'], predicted_gain=float(values[index]))
        semantic_gain = 1/(1+np.exp(-np.clip(mean_score,-30,30)))
        # Original D ranks the untouched means; clipping is only its budget value.
        semantic_action = None
        if len(mean_score):
            index = int(mean_score.argmax())
            semantic_action = dict(sid=s['sid'], candidate_index=index, added_frames=candidates[index]['added_frames'], predicted_gain=float(semantic_gain[index]))
        constant_gain, _ = gains(baseline, np.full(len(baseline),float(model['rho_train'])), candidates)
        items.append(dict(source=s, clock=clock, baseline=baseline, groups=groups, score=score, p=p, candidates=candidates, gain=gain, stats=stats, pava_action=action(gain), semantic_action=semantic_action, constant_action=action(constant_gain)))
    budget = sum(int(v['baseline'].sum()) for v in items)//10
    selected = {name:knapsack([v[name+'_action'] for v in items if v[name+'_action']],budget) for name in ('pava','semantic','constant')}
    predictions = []
    for v in items:
        masks, choices = {}, {}
        for name in selected:
            mask = v['baseline'].copy()
            choice = None
            if v['source']['sid'] in selected[name]:
                choice = v['candidates'][v[name+'_action']['candidate_index']]
                mask[choice['left']:choice['right']] = True
            require(np.all(v['baseline'] <= mask), 'Original40.47 policy source frames protected')
            masks[name] = mask
            choices[name] = choice
        p = out/(v['source']['sid']+'_outputs.npz')
        with p.open('xb') as f:
            np.savez(f,baseline=v['baseline'],probability=v['p'],estimated_gain=v['gain'],**masks)
        predictions.append(dict(sid=v['source']['sid'],name=v['source']['name'],data_ref=v['source']['data_ref'],clock_ref=v['source']['clock_ref'],output_ref=ref(p),choices=choices,candidates=len(v['candidates']),successful_null=v['pava_action'] is None))
    save(out/'frozen_inference_before_metrics.json',dict(status='FROZEN4_FIRST_COMPARISON_OUTPUTS_BEFORE_REFERENCE_VALUES', sources=predictions,model_ref=frozen['weights_ref'],baseline_native_budget=budget,reference_values_used=False,no_EM_or_parameter_fit=True,utc=utc()))
    # Only here do the original human interval values enter the comparison.
    reference_rows = {v['name']:v for v in read(ROOT/'confirm4_reference_01/references.json')}
    rows = []
    for v, prediction in zip(items,predictions):
        points = list(map(F,v['clock']['normalized_exact_pts']))
        labels = np.zeros((len(points),10),bool)
        reference = reference_rows[prediction['name']]
        require(len(reference['annotator_intervals_exact_seconds']) == 10, 'All original reviewers')
        for k, spans in enumerate(reference['annotator_intervals_exact_seconds']):
            for a,b in spans:
                require(F(0) <= F(a) < F(b) <= F(v['clock']['physical_end_exact']), 'Unmodified source endpoint fits')
                labels[bisect_left(points,F(a)):bisect_left(points,F(b)),k] = True
        output = np.load(bound(prediction['output_ref']))
        b = metric(v['baseline'],labels)
        results = {name:metric(output[name],labels) for name in selected}
        added = output['pava'] & ~v['baseline']
        vote = labels.mean(1)
        rows.append(dict(sid=prediction['sid'],name=prediction['name'],native_frames=len(points),reviewers=10,baseline=b,results=results,pava_delta=results['pava']['f1']-b['f1'],semantic_delta=results['semantic']['f1']-b['f1'],constant_delta=results['constant']['f1']-b['f1'],pava_minus_semantic=results['pava']['f1']-results['semantic']['f1'],added_frames=int(added.sum()),newframe_reviewer_precision=None if not added.any() else float(vote[added].mean()),successful_null=prediction['successful_null'],brier=float(np.mean((v['p']-vote)**2)),constant_brier=float(np.mean((float(model['rho_train'])-vote)**2)),reference_selected_fraction=float(vote.mean()),choices=prediction['choices']))
    delta = np.asarray([v['pava_delta'] for v in rows])
    summary = dict(sources=4,macro_delta=float(delta.mean()),improved_sources=int((delta>0).sum()),decreased_sources=int((delta<0).sum()),changed_sources=sum(v['added_frames']>0 for v in rows),successful_nulls=sum(v['successful_null'] for v in rows),added_frames=sum(v['added_frames'] for v in rows),worst_delta=float(delta.min()),macro_semantic_delta=float(np.mean([v['semantic_delta']for v in rows])),macro_constant_delta=float(np.mean([v['constant_delta']for v in rows])),macro_pava_minus_semantic=float(np.mean([v['pava_minus_semantic']for v in rows])),macro_brier=float(np.mean([v['brier']for v in rows])),macro_constant_brier=float(np.mean([v['constant_brier']for v in rows])))
    save(out/'result.json',dict(status='COMPLETED_FIRST_FIXED4_CONFIRMATION_RESEARCH_REVIEW_REQUIRED',summary=summary,sources=rows,source_selection_or_method_changed=False,no_fivefold_or_proxy_release_hard_gate=True,global_original_pretraining_overlap='UNKNOWN',reference_task='caption-conditioned manual summary proxy, not official crop/highlight GT',official_joint_score_estimate=None,utc=utc()))
    save(out/'completion.json',dict(status='COMPLETED_FIXED4_COMPARISON_NO_AUTOMATIC_PRODUCTION',result_ref=ref(out/'result.json'),new_fit=0,utc=utc()))
    import json
    print(json.dumps(summary),flush=True)


if __name__ == '__main__':
    main()
