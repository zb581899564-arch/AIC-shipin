"""One source-relative event critic; fixed precision objective and no intercept."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ.setdefault('OPENBLAS_NUM_THREADS', '2')
import sys
from pathlib import Path
import json
import numpy as np

W = Path('/home/inspur/aic_video_work')
ROOT = W/'relative_precision_event_20261018_v1'
CAL = W/'calibrated_event_20261018_v1'
EVENT = W/'meaningful_residual_20261018_v1'
sys.path.insert(0, str(CAL/'code_v1'))
from calibrate import read, save, ref, bound, require, utc, deadline
from event_features import projected, proposals, metric
sys.path.insert(0, str(CAL/'source_normalized_code_v2'))
from multiple_choice import multiple_choice_knapsack
sys.path.insert(0, str(W/'coverage_event_20261018_v1/code_v1'))
from coverage_event import catalogue, labels_for


def differences(language, groups, baseline, candidates, pca):
    p = projected(language, pca)
    require(len(groups)==len(baseline) and baseline.dtype==np.bool_ and
            groups.min()==0 and groups.max()+1==len(p), 'Real native/group alignment')
    require(np.isfinite(p).all(), 'Finite original frozen PCA projection')
    native = p[groups]
    if not baseline.any():
        return np.zeros((len(candidates), 32)), dict(anchor_present=False, baseline_frames=0)
    anchor = native[baseline].mean(0)
    x = []
    for c in candidates:
        added = ~baseline[c['left']:c['right']]
        require(int(added.sum())==c['added_frames'] and added.any(), 'Real unique candidate addition')
        x.append(native[c['left']:c['right']][added].mean(0)-anchor)
    x = np.asarray(x, float).reshape(-1, 32)
    require(np.isfinite(x).all(), 'Finite candidate-minus-selected-anchor32')
    return x, dict(anchor_present=True, baseline_frames=int(baseline.sum()), feature_rows=len(p))


def target_differences(baseline, labels, candidates):
    require(labels.dtype==np.bool_ and len(labels)==len(baseline) and baseline.any(),
            'Original all-rater native labels and defined selected anchor')
    selected_precision = labels[baseline].mean(0)
    result = []
    for c in candidates:
        added = ~baseline[c['left']:c['right']]
        local = labels[c['left']:c['right']][added].mean(0)
        result.append(float(np.mean(local-selected_precision)))
    result = np.asarray(result)
    require(np.all((-1<=result)&(result<=1)), 'Literal mean precision contrast in [-1,1]')
    return result


def predict(x, candidates, baseline, model, anchor_present=True):
    raw = (x/model['scale'])@model['coef']
    require(np.isfinite(raw).all(), 'Finite frozen relative prediction')
    q = np.clip(raw, -1, 1)
    k = np.asarray([c['added_frames'] for c in candidates], float)
    gain = k/(int(baseline.sum())+k)*q if len(k) else np.empty(0)
    if not anchor_present:
        gain[:] = 0
    return raw, gain


def checks():
    b, k = 3, 2
    old_precision, add_precision = 2/3, .5
    direct = (b*old_precision+k*add_precision)/(b+k)-old_precision
    require(abs(direct-k/(b+k)*(add_precision-old_precision))<1e-14,
            'Exact per-reviewer and mean precision addition identity')
    x = np.zeros((1, 32));m = dict(scale=np.ones(32),coef=np.ones(32))
    _, gain = predict(x, [dict(added_frames=2)], np.array([1,1,0,0], bool), m)
    require(gain[0]==0, 'No intercept: indistinguishable new/selected features abstain')
    _, positive = predict(np.ones((1,32)), [dict(added_frames=2)], np.array([1,1,0,0],bool), m)
    _, negative = predict(-np.ones((1,32)), [dict(added_frames=2)], np.array([1,1,0,0],bool), m)
    require(positive[0]>0 and negative[0]<0, 'Signed preference, never force a positive action')
    _, empty = predict(np.ones((1,32)), [dict(added_frames=2)], np.zeros(4,bool), m, False)
    require(empty[0]==0, 'Absent selected anchor is an explicit successful null, not execution failure')
    save(ROOT/'targeted_checks.json', dict(status='PASS4_RELATIVE_PRECISION_IDENTITY_SIGN_NULL_CHECKS', old_tests_repeated=False, utc=utc()))


def fit():
    deadline()
    registration = read(ROOT/'registration.json')
    for v in registration['method_refs']:
        bound(v)
    checks()
    pca = dict(np.load(bound(registration['pca_ref'])))
    xall, yall, wall, rows = [], [], [], []
    sources = [s for s in read(EVENT/'registration.json')['sources'] if s['group']=='train']
    require(len(sources)==25, 'Fixed25 original-human training sources')
    for s in sources:
        native = np.load(bound(s['data_ref']))
        clock = read(bound(s['clock_ref']))
        require(len(clock['normalized_exact_pts'])==len(native['baseline']), 'Full native target domain')
        language = np.load(bound(s['language_ref']))
        c = proposals(clock, native['baseline'])
        x, stats = differences(language, native['groups'], native['baseline'], c, pca)
        row = dict(sid=s['sid'], data_ref=s['data_ref'], language_ref=s['language_ref'], candidates=len(c), **stats)
        if stats['anchor_present'] and len(c):
            y = target_differences(native['baseline'], native['labels'], c)
            xall.append(x);yall.append(y);wall.append(np.full(len(x), 1/len(x)))
            row['source_weight'] = 1.;row['target_mean']=float(y.mean())
        else:
            row['source_weight'] = 0.
        rows.append(row)
    x,y,weight = np.concatenate(xall),np.concatenate(yall),np.concatenate(wall)
    require(len(xall)>0 and abs(weight.sum()-len(xall))<1e-10, 'One unit of total weight per eligible source')
    scale = np.maximum(np.sqrt(np.sum(weight[:,None]*x*x,axis=0)/weight.sum()),1e-6)
    z = x/scale
    # Fixed alpha1, one source-equal solve, no intercept and no checkpoint search.
    coef = np.linalg.solve(z.T@(weight[:,None]*z)+np.eye(32), z.T@(weight*y))
    require(np.isfinite(coef).all(), 'Finite final32 ridge coefficients')
    model = dict(coef=coef,scale=scale)
    with (ROOT/'model.npz').open('xb') as f:np.savez(f,**model)
    restored = dict(np.load(ROOT/'model.npz'))
    require(all(np.array_equal(model[k],restored[k]) for k in model), 'Actual final save/reload bit equality')
    save(ROOT/'fit_completion.json', dict(status='ONE_FINAL_SOURCE_RELATIVE_PRECISION_CRITIC_FIT',sources=rows,
        effective_sources=len(xall),rows=len(x),alpha=1.,bias=False,new_model_scalars=64,
        train_weighted_mse=float(np.sum(weight*((z@coef)-y)**2)/weight.sum()),
        weights_ref=ref(ROOT/'model.npz'),pca_ref=registration['pca_ref'], new_8B_calls=0, utc=utc()))


def evaluate():
    deadline()
    registration = read(ROOT/'registration.json')
    model = dict(np.load(ROOT/'model.npz'));pca=dict(np.load(bound(registration['pca_ref'])))
    inputs = []
    outdir = ROOT/'diagnostic_outputs';outdir.mkdir()
    for s in catalogue():
        native=np.load(bound(s['data_ref']));clock=read(bound(s['clock_ref']));language=np.load(bound(s['language_ref']))
        b=native['baseline'];c=proposals(clock,b)
        x,stats=differences(language,native['groups'],b,c,pca)
        raw,gain=predict(x,c,b,model,stats['anchor_present'])
        path=outdir/(s['sid']+'_scores.npz')
        with path.open('xb')as f:np.savez(f,raw_precision_difference=raw,estimated_precision_gain=gain)
        inputs.append(dict(source=s,native=native,clock=clock,baseline=b,candidates=c,raw=raw,gain=gain,
                           stats=stats,output_ref=ref(path)))
    selections={}
    for cohort in ('exposed8','exposed4','exposed4b'):
        items=[x for x in inputs if x['source']['cohort']==cohort]
        budget=sum(int(x['baseline'].sum())for x in items)//10
        options={x['source']['sid']:[dict(candidate_index=i,added_frames=c['added_frames'],predicted_gain=float(x['gain'][i]))for i,c in enumerate(x['candidates'])if x['gain'][i]>0]for x in items}
        selections[cohort]=multiple_choice_knapsack(options,budget)
    frozen=[]
    for x in inputs:
        s=x['source'];index=selections[s['cohort']]['chosen'].get(s['sid']);mask=x['baseline'].copy()
        choice=None if index is None else x['candidates'][index]
        if choice is not None:mask[choice['left']:choice['right']]=True
        require(np.all(x['baseline']<=mask), 'All original baseline frames protected')
        p=outdir/(s['sid']+'_mask.npy')
        with p.open('xb')as f:np.save(f,mask)
        frozen.append(dict(sid=s['sid'],cohort=s['cohort'],mask_ref=ref(p),score_ref=x['output_ref'],choice=choice,
            positive_candidates=int(np.sum(x['gain']>0)),successful_null=not np.any(x['gain']>0),
            raw_predictions_outside_mathematical_range=int(np.sum(np.abs(x['raw'])>1))))
    save(ROOT/'outputs_frozen_before_metrics.json',dict(status='FIXED16_RELATIVE_PRECISION_OUTPUTS_BEFORE_NEW_METRICS',sources=frozen,selections=selections,weights_ref=ref(ROOT/'model.npz'),prior_diagnostic_exposure=True,label_values_used_in_current_inference=False,utc=utc()))
    rows=[]
    for x,frozen_row in zip(inputs,frozen):
        s=x['source'];labels=labels_for(s,x['clock'],x['native']);mask=np.load(bound(frozen_row['mask_ref']));after=metric(mask,labels);before=s['baseline_metric'];added=mask&~x['baseline']
        rows.append(dict(sid=s['sid'],cohort=s['cohort'],baseline=before,candidate=after,
            precision_delta=after['precision']-before['precision'],f1_delta=after['f1']-before['f1'],
            recall_delta=after['recall']-before['recall'],minus_old_semantic=after['f1']-s['old_semantic_metric']['f1'],
            added_frames=int(added.sum()),newframe_reviewer_precision=None if not added.any()else float(labels[added].mean()),
            successful_null=frozen_row['successful_null'],chosen=frozen_row['choice']))
    def summary(items):
        return dict(sources=len(items),macro_precision_delta=float(np.mean([x['precision_delta']for x in items])),
            macro_f1_delta=float(np.mean([x['f1_delta']for x in items])),macro_recall_delta=float(np.mean([x['recall_delta']for x in items])),
            precision_improved=sum(x['precision_delta']>0 for x in items),precision_decreased=sum(x['precision_delta']<0 for x in items),
            f1_improved=sum(x['f1_delta']>0 for x in items),f1_decreased=sum(x['f1_delta']<0 for x in items),
            changed=sum(x['added_frames']>0 for x in items),added_frames=sum(x['added_frames']for x in items),
            successful_nulls=sum(x['successful_null']for x in items),worst_precision_delta=min(x['precision_delta']for x in items),
            worst_f1_delta=min(x['f1_delta']for x in items))
    summaries={cohort:summary([x for x in rows if x['cohort']==cohort])for cohort in selections};summaries['all16']=summary(rows)
    save(ROOT/'result.json',dict(status='COMPLETED_ONE_RELATIVE_PRECISION_DEVELOPMENT_REVIEW_REQUIRED',summary=summaries,sources=rows,
        training_target='All original raters mean precision(newframes)-precision(current selected baseline), not ordinary negatives or official GT',
        official_joint_score_estimate=None,blind_confirmation=False,no_post_metric_variants=True,new_8B_calls=0,utc=utc()))
    save(ROOT/'completion.json',dict(status='COMPLETED_ONE_FINAL_FIT_AND16_DIAGNOSTIC_NO_AUTO_PRODUCTION',result_ref=ref(ROOT/'result.json'),utc=utc()))
    print(json.dumps(summaries),flush=True)


if __name__=='__main__':
    try:
        fit()
        evaluate()
    except BaseException as error:
        import traceback
        save(ROOT/('failure_'+str(os.getpid())+'.json'),dict(error=repr(error),traceback=traceback.format_exc(),successes_preserved=True,utc=utc()))
        raise
