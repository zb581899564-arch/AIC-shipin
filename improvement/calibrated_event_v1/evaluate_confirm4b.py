"""First distinct4 prospective comparison of the frozen exact-budget arm."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
import sys
from pathlib import Path
from fractions import Fraction as F
from bisect import bisect_left
import numpy as np
ROOT=Path('/home/inspur/aic_video_work/calibrated_event_20261018_v1')
sys.path.insert(0,str(ROOT/'code_v1'))
from calibrate import read,ref,bound,require,save,utc,probability,gains,metric,knapsack
from event_features import proposals
sys.path.insert(0,str(ROOT/'source_normalized_code_v2'))
from multiple_choice import multiple_choice_knapsack


def main():
    cohort=ROOT/'confirm4b_01'
    reg=read(ROOT/'new4b_confirmation_registration_02.json')
    for item in reg['freeze_model_refs']:
        bound(item)
    prepared=read(cohort/'stages/finalize/completion.json')
    require(prepared['status']=='PASS' and not prepared['labels_read'] and len(prepared['sources'])==4,'Complete actual new4b model and independent QA before evaluation')
    frozen=read(ROOT/'frozen_selection.json')
    model=dict(np.load(bound(frozen['weights_ref'])))
    require(frozen['weights_ref']['sha256']==reg['method']['weights_sha256'],'Exactly frozen raw PAVA, never sourceZ or EM')
    out=ROOT/'new4b_comparison_01';out.mkdir()
    inputs=[];all_options={}
    for source in prepared['sources']:
        data=np.load(bound(source['data_ref']));clock=read(bound(source['clock_ref']))
        baseline,groups,score=data['baseline'],data['groups'],data['semantic_score']
        require(baseline.dtype==np.bool_ and len(baseline)==len(groups)==len(clock['normalized_exact_pts']) and groups.min()==0 and groups.max()+1==len(score) and np.isfinite(score).all(),'Actual complete native semantic field')
        candidates=proposals(clock,baseline);p=probability(score,model)[groups]
        gain,stats=gains(baseline,p,candidates)
        actions=[dict(candidate_index=i,added_frames=c['added_frames'],predicted_gain=float(gain[i]))for i,c in enumerate(candidates)if gain[i]>0]
        all_options[source['sid']]=actions
        top=None if not actions else dict(sid=source['sid'],**max(actions,key=lambda a:a['predicted_gain']))
        prefix=np.r_[0.,np.cumsum(score[groups].astype(float)*(~baseline))]
        means=np.asarray([(prefix[c['right']]-prefix[c['left']])/c['added_frames']for c in candidates])
        semantic=None
        if len(means):
            i=int(means.argmax());semantic=dict(sid=source['sid'],candidate_index=i,added_frames=candidates[i]['added_frames'],predicted_gain=float(1/(1+np.exp(-np.clip(means[i],-30,30)))))
        inputs.append(dict(source=source,clock=clock,baseline=baseline,candidates=candidates,p=p,gain=gain,top=top,semantic=semantic))
    budget=sum(int(v['baseline'].sum())for v in inputs)//10
    exact=multiple_choice_knapsack(all_options,budget)
    original_top=knapsack([v['top']for v in inputs if v['top']],budget)
    semantic_ids=knapsack([v['semantic']for v in inputs if v['semantic']],budget)
    old_utility=sum(v['top']['predicted_gain']for v in inputs if v['source']['sid']in original_top)
    require(exact['total_utility']>=old_utility-1e-12,'Exact source alternatives cannot underperform feasible two-stage objective')
    predictions=[]
    for v in inputs:
        sid=v['source']['sid'];indices={'pava_exact':exact['chosen'].get(sid),'pava_top1':v['top']['candidate_index']if sid in original_top else None,'semantic':v['semantic']['candidate_index']if sid in semantic_ids else None};masks={};choices={}
        for name,index in indices.items():
            mask=v['baseline'].copy();choice=None
            if index is not None:
                choice=v['candidates'][index];mask[choice['left']:choice['right']]=True
            require(np.all(v['baseline']<=mask),'All original baseline source frames retained')
            masks[name]=mask;choices[name]=choice
        path=out/(sid+'_outputs.npz')
        with path.open('xb')as f:np.savez(f,baseline=v['baseline'],probability=v['p'],estimated_gain=v['gain'],**masks)
        predictions.append(dict(sid=sid,name=v['source']['name'],output_ref=ref(path),clock_ref=v['source']['clock_ref'],data_ref=v['source']['data_ref'],choices=choices,successful_null=not all_options[sid],candidate_count=len(v['candidates'])))
    save(out/'frozen_outputs_before_metrics.json',dict(status='PASS4B_PROSPECTIVE_FIXED_METHOD_OUTPUTS_BEFORE_METRICS',sources=predictions,model_ref=frozen['weights_ref'],source_registration_ref=ref(ROOT/'new4b_confirmation_registration_02.json'),solver=exact,old_top1_utility=old_utility,budget=budget,labels_used=False,utc=utc()))
    refs={v['name']:v for v in read(cohort/'references/references.json')}
    rows=[]
    for v,prediction in zip(inputs,predictions):
        points=list(map(F,v['clock']['normalized_exact_pts']));labels=np.zeros((len(points),10),bool)
        for reviewer,spans in enumerate(refs[prediction['name']]['annotator_intervals_exact_seconds']):
            for a,b in spans:
                require(F(0)<=F(a)<F(b)<=F(v['clock']['physical_end_exact']),'Exact unmodified original native reference domain')
                labels[bisect_left(points,F(a)):bisect_left(points,F(b)),reviewer]=True
        output=np.load(bound(prediction['output_ref']));b=metric(v['baseline'],labels)
        results={name:metric(output[name],labels)for name in ('pava_exact','pava_top1','semantic')};added=output['pava_exact']&~v['baseline'];vote=labels.mean(1)
        rows.append(dict(sid=prediction['sid'],name=prediction['name'],baseline=b,results=results,delta=results['pava_exact']['f1']-b['f1'],minus_D=results['pava_exact']['f1']-results['semantic']['f1'],minus_top1=results['pava_exact']['f1']-results['pava_top1']['f1'],added_frames=int(added.sum()),successful_null=prediction['successful_null'],newframe_reviewer_precision=None if not added.any()else float(vote[added].mean()),brier=float(np.mean((v['p']-vote)**2)),constant_brier=float(np.mean((float(model['rho_train'])-vote)**2)),choices=prediction['choices']))
    summary=dict(sources=4,macro_delta=float(np.mean([v['delta']for v in rows])),improved=sum(v['delta']>0 for v in rows),decreased=sum(v['delta']<0 for v in rows),changed=sum(v['added_frames']>0 for v in rows),added_frames=sum(v['added_frames']for v in rows),successful_nulls=sum(v['successful_null']for v in rows),macro_minus_D=float(np.mean([v['minus_D']for v in rows])),macro_minus_top1=float(np.mean([v['minus_top1']for v in rows])),worst_delta=min(v['delta']for v in rows),macro_brier=float(np.mean([v['brier']for v in rows])),macro_constant_brier=float(np.mean([v['constant_brier']for v in rows])))
    save(out/'result.json',dict(status='COMPLETED_FIRST4B_FROZEN_RAW_PAVA_EXACT_BUDGET_REVIEW_REQUIRED',summary=summary,sources=rows,method_or_sources_changed_after_metrics=False,no_proxy_hard_gate_or_threshold_scan=True,global_original_source_pretraining_overlap='UNKNOWN',reference_scope='Original all10 caption-conditioned manual summary interval proxy; not official joint GT',official_joint_score_estimate=None,utc=utc()))
    save(out/'completion.json',dict(status='COMPLETED_FIRST4B_NO_AUTO_PRODUCTION',result_ref=ref(out/'result.json'),new_fit=0,utc=utc()))
    import json
    print(json.dumps(summary),flush=True)


if __name__=='__main__':
    main()
