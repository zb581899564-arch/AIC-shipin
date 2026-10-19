"""One source-relative calibration and exact-budget design comparison."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
import sys
from pathlib import Path
from fractions import Fraction as F
from bisect import bisect_left
import numpy as np

ROOT = Path('/home/inspur/aic_video_work/calibrated_event_20261018_v1')
sys.path.insert(0,str(ROOT/'code_v1'))
import calibrate as cal
from event_features import proposals, metric
from multiple_choice import multiple_choice_knapsack
OUT = ROOT/'source_normalized_02'


def normalize(score, groups):
    score = np.asarray(score,np.float64)
    field = score[groups]
    mean, std = float(field.mean()),float(field.std())
    z = (score-mean)/max(std,1e-6)
    cal.require(np.isfinite(z).all(),'Finite deterministic source-relative feature')
    return z,dict(mean=mean,std=std,native_frames=len(field),numeric_floor=1e-6)


def fit():
    cal.deadline()
    OUT.mkdir()
    test_groups=np.asarray([0,0,1],np.int64)
    z,stats=normalize(np.asarray([0.,1.]),test_groups)
    zz,_=normalize(np.asarray([5.,7.]),test_groups)
    constant,_=normalize(np.asarray([3.,3.]),test_groups)
    cal.require(abs(z[test_groups].mean())<1e-12 and abs(z[test_groups].std()-1)<1e-12,'Actual native weights determine zero mean/unit variance')
    cal.require(np.allclose(z,zz,atol=1e-12) and np.array_equal(constant,[0.,0.]),'Positive affine invariance and legitimate constant field')
    cal.save(OUT/'normalization_checks.json',dict(status='PASS_NATIVE_WEIGHT_AFFINE_AND_CONSTANT_CHECKS',model_calls=0,utc=cal.utc()))
    scores, targets, weights, rows, rhos = [],[],[],[],[]
    for source in cal.read(cal.EVENT/'registration.json')['sources']:
        if source['group'] != 'train':
            continue
        d = cal.load_source(source)
        z, stats = normalize(d['score'],d['groups'])
        count = np.bincount(d['groups'],minlength=len(z))
        vote = d['labels'].mean(1)
        target = np.bincount(d['groups'],weights=vote,minlength=len(z))/count
        weight = count/len(vote)
        cal.require(abs(weight.sum()-1)<1e-12,'Exactly one native calibration mass/source')
        scores.append(z);targets.append(target);weights.append(weight);rhos.append(float(vote.mean()))
        rows.append(dict(sid=source['sid'],data_ref=source['data_ref'],normalization=stats))
    cal.require(len(rows)==25,'Same fixed25 calibration training sources')
    model, stats = cal.pava(np.concatenate(scores),np.concatenate(targets),np.concatenate(weights))
    model['rho_train'] = np.asarray(np.mean(rhos))
    with (OUT/'model.npz').open('xb') as f:
        np.savez(f,**model)
    restored = dict(np.load(OUT/'model.npz'))
    cal.require(all(np.array_equal(restored[k],v)for k,v in model.items()),'Actual saved/reloaded mapping equality')
    cal.save(OUT/'frozen_selection.json',dict(status='FROZEN_ONE_NATIVE_SOURCE_Z_PAVA_AND_EXACT_GLOBAL_OPTIONS',model_ref=cal.ref(OUT/'model.npz'),code_ref=cal.ref(Path(__file__)),solver_ref=cal.ref(Path(__file__).parent/'multiple_choice.py'),protocol_ref=cal.ref(ROOT/'source_normalized_protocol_02.json'),fit=stats,train_sources=rows,new_numeric_scalars=sum(v.size for v in model.values()),new_GPU=0,external12_labels_used_by_fit=False,official_test_prior_fit=False,utc=cal.utc()))


def diagnostics():
    cal.deadline()
    frozen = cal.read(OUT/'frozen_selection.json')
    cal.bound(frozen['solver_ref']);cal.bound(frozen['code_ref'])
    zmodel = dict(np.load(cal.bound(frozen['model_ref'])))
    rawmodel = dict(np.load(cal.bound(cal.read(ROOT/'frozen_selection.json')['weights_ref'])))
    old8 = {v['sid']:v for v in cal.read(ROOT/'development_evaluation.json')['sources']}
    new4 = {v['sid']:v for v in cal.read(ROOT/'new4_comparison_01/result.json')['sources']}
    sources = []
    for s in cal.read(cal.EVENT/'registration.json')['sources']:
        if s['group'] != 'check':
            continue
        d = cal.load_source(s)
        d.update(cohort='exposed8',clock=cal.read(cal.bound(s['clock_ref'])),base_metric=old8[s['sid']]['baseline'],old_raw_metric=old8[s['sid']]['candidate'],old_D_metric=old8[s['sid']]['original_semantic_control'],old_raw_output_ref=cal.ref(ROOT/'development_01'/(s['sid']+'_output.npz')))
        sources.append(d)
    refs = {s['name']:s for s in cal.read(ROOT/'confirm4_reference_01/references.json')}
    for s in cal.read(ROOT/'confirm4_02/stages/finalize/completion.json')['sources']:
        v = np.load(cal.bound(s['data_ref']))
        clock = cal.read(cal.bound(s['clock_ref']))
        points = list(map(F,clock['normalized_exact_pts']))
        labels = np.zeros((len(points),10),bool)
        for k, spans in enumerate(refs[s['name']]['annotator_intervals_exact_seconds']):
            for a,b in spans:
                cal.require(F(0)<=F(a)<F(b)<=F(clock['physical_end_exact']),'Adopt unchanged exact native reference')
                labels[bisect_left(points,F(a)):bisect_left(points,F(b)),k]=True
        previous = new4[s['sid']]
        sources.append(dict(sid=s['sid'],cohort='new4_now_exposed',baseline=v['baseline'],groups=v['groups'],score=v['semantic_score'],labels=labels,candidates=proposals(clock,v['baseline']),clock=clock,base_metric=previous['baseline'],old_raw_metric=previous['results']['pava'],old_D_metric=previous['results']['semantic'],old_raw_output_ref=cal.ref(ROOT/'new4_comparison_01'/(s['sid']+'_outputs.npz'))))
    arms = ('RAW_PAVA_GLOBAL_OPTIONS','SOURCE_Z_PAVA_GLOBAL_OPTIONS')
    results = []
    for arm in arms:
        directory = OUT/arm
        directory.mkdir()
        grouped = {}
        fields = {}
        for d in sources:
            score = d['score'] if arm==arms[0] else normalize(d['score'],d['groups'])[0]
            model = rawmodel if arm==arms[0] else zmodel
            p = cal.probability(score,model)[d['groups']]
            gain, stats = cal.gains(d['baseline'],p,d['candidates'])
            grouped[d['sid']] = [dict(candidate_index=i,added_frames=c['added_frames'],predicted_gain=float(gain[i]))for i,c in enumerate(d['candidates'])if gain[i]>0]
            fields[d['sid']] = (p,gain,stats)
        for cohort in ('exposed8','new4_now_exposed'):
            subset = [d for d in sources if d['cohort']==cohort]
            budget = sum(int(d['baseline'].sum())for d in subset)//10
            decision = multiple_choice_knapsack({d['sid']:grouped[d['sid']]for d in subset},budget)
            chosen = decision['chosen']
            rows = []
            for d in subset:
                mask = d['baseline'].copy(); index = chosen.get(d['sid'])
                if index is not None:
                    c = d['candidates'][index];mask[c['left']:c['right']]=True
                p,gain,stats = fields[d['sid']]
                n = metric(mask,d['labels']);added=mask&~d['baseline']
                old = np.load(cal.bound(d['old_raw_output_ref']))
                previous_mask=old['selected']if d['cohort']=='exposed8'else old['pava']
                rows.append(dict(sid=d['sid'],baseline=d['base_metric'],candidate=n,delta=n['f1']-d['base_metric']['f1'],minus_original_D=n['f1']-d['old_D_metric']['f1'],minus_old_raw=n['f1']-d['old_raw_metric']['f1'],added_frames=int(added.sum()),newframe_reviewer_precision=None if not added.any()else float(d['labels'][added].mean()),changed_vs_old_raw=not np.array_equal(mask,previous_mask),brier=float(np.mean((p-d['labels'].mean(1))**2)),chosen=None if index is None else d['candidates'][index],positive_candidates=len(grouped[d['sid']]),feasible_positive_candidates=sum(c['added_frames']<=budget for c in grouped[d['sid']]),estimated_gain=None if index is None else float(gain[index])))
                with (directory/(d['sid']+'.npz')).open('xb')as f:
                    np.savez(f,selected=mask,probability=p,estimated_gain=gain)
            summary=dict(sources=len(rows),macro_delta=float(np.mean([v['delta']for v in rows])),improved=sum(v['delta']>0 for v in rows),decreased=sum(v['delta']<0 for v in rows),changed=sum(v['added_frames']>0 for v in rows),changed_vs_old_raw=sum(v['changed_vs_old_raw']for v in rows),macro_minus_D=float(np.mean([v['minus_original_D']for v in rows])),added_frames=sum(v['added_frames']for v in rows),worst_delta=min(v['delta']for v in rows),macro_brier=float(np.mean([v['brier']for v in rows])))
            cal.save(directory/(cohort+'.json'),dict(summary=summary,sources=rows,solver=decision,all_metrics_explicitly_development_exposed=True,utc=cal.utc()))
            results.append(dict(arm=arm,cohort=cohort,**summary))
    cal.save(OUT/'comparison.json',dict(status='COMPLETED_TWO_EXACT_BUDGET_AND_SOURCE_RELATIVE_CPU_DIAGNOSTICS',results=results,one_new_fit=1,new_8B_or_decode=0,new_blind_claim=False,production_admitted=False,utc=cal.utc()))
    import json
    print(json.dumps(results),flush=True)


if __name__=='__main__':
    try:
        {'fit':fit,'diagnostics':diagnostics}[sys.argv[1]]()
    except BaseException as error:
        import traceback
        cal.save(ROOT/('source_normalized_failure_'+sys.argv[1]+'_'+str(os.getpid())+'.json'),dict(error=repr(error),traceback=traceback.format_exc(),successes_preserved=True,utc=cal.utc()))
        raise
