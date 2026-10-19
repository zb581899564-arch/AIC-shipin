"""First remaining evaluation only after axis-QA failure; never refit."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
from pathlib import Path
import importlib.util,sys,json,uuid,traceback
P=Path('/home/inspur/aic_video_work/source_consensus_event_20261018_v1/code_v1/source_consensus.py')
spec=importlib.util.spec_from_file_location('_source_consensus_adopted_v1',P);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
ROOT=m.ROOT;read,save,ref,bound,require=m.read,m.save,m.ref,m.bound,m.require
np=m.np;npz=m.npz;critic=m.critic;helper=m.helper;multiple_choice_knapsack=m.multiple_choice_knapsack;lower_scores=m.lower_scores

def main():
    m.deadline()
    recovery=read(ROOT/'remaining_evaluation_registration_03.json')
    fit=read(bound(recovery['successful_fit_ref']))
    require(fit['status']=='COMPLETED_ONE_FIXED32_WHOLE_SOURCE_BOOTSTRAP_ENSEMBLE','Adopt actual successful one fit')
    require(not list((ROOT/'evaluation_01').iterdir()),'No successful old inference file to repeat')
    model=dict(np.load(bound(fit['weights_ref']),allow_pickle=False))
    manifest=read(bound(recovery['original_inputs_ref']))
    out=ROOT/'evaluation_remaining_03';out.mkdir();inputs=[]
    for row in manifest['external']:
        data=np.load(bound(row['input_ref']),allow_pickle=False)
        lower,gain,members=lower_scores(data['difference32'],row['candidates'],data['baseline'],model)
        require(np.all(np.isfinite(members)) and np.allclose(members[:,0],np.sum(data['difference32']/model['scale']*model['coefs'][0],axis=1),atol=1e-12,rtol=1e-10),'First direct new member/output check')
        path=out/(row['sid']+'_scores.npz');npz(path,lower_precision_difference=lower,gain=gain,members=members)
        inputs.append(dict(row=row,data=data,lower=lower,gain=gain,output_ref=ref(path)))
    selections={}
    for cohort in sorted({v['row']['cohort'] for v in inputs}):
        group=[v for v in inputs if v['row']['cohort']==cohort]
        options={v['row']['sid']:[dict(candidate_index=i,added_frames=c['added_frames'],predicted_gain=float(v['gain'][i])) for i,c in enumerate(v['row']['candidates']) if v['gain'][i]>0] for v in group}
        selections[cohort]=multiple_choice_knapsack(options,sum(int(v['data']['baseline'].sum()) for v in group)//10)
    frozen=[]
    for v in inputs:
        row=v['row'];sid=row['sid'];index=selections[row['cohort']]['chosen'].get(sid);mask=v['data']['baseline'].copy()
        choice=None if index is None else row['candidates'][index]
        if choice is not None:mask[choice['left']:choice['right']]=True
        path=out/(sid+'_mask.npy')
        with path.open('xb') as f:np.save(f,mask)
        frozen.append(dict(sid=sid,cohort=row['cohort'],mask_ref=ref(path),score_ref=v['output_ref'],choice=choice,positive_candidates=int(np.sum(v['gain']>0)),successful_null=not np.any(v['gain']>0),lower_at_choice=None if index is None else float(v['lower'][index])))
    save(out/'frozen_before_metrics.json',dict(status='ALL19_FROZEN_BEFORE_CURRENT_REPAIR_METRICS',sources=frozen,selections=selections,weights_ref=ref(ROOT/'model.npz'),all19_previously_exposed=True,old_prospective3_no_longer_blind=True,utc=helper.utc()))
    rows=[]
    for v,f in zip(inputs,frozen):
        row=v['row'];sid=row['sid'];human=np.load(ROOT/'diagnosis_01'/(sid+'_human_targets.npz'),allow_pickle=False)['labels']
        mask=np.load(bound(f['mask_ref']),allow_pickle=False);before=critic.metric(v['data']['baseline'],human);old=critic.metric(v['data']['original_selected'],human);after=critic.metric(mask,human);added=mask&~v['data']['baseline']
        rows.append(dict(sid=sid,cohort=row['cohort'],before=before,old_relative=old,after=after,delta={k:after[k]-before[k] for k in ['precision','recall','f1']},minus_old={k:after[k]-old[k] for k in ['precision','recall','f1']},added_frames=int(added.sum()),old_added_frames=int(np.sum(v['data']['original_selected']&~v['data']['baseline'])),successful_null=f['successful_null'],newframe_human_precision=None if not added.any() else float(human[added].mean())))
    def summary(group):
        return dict(sources=len(group),macro_delta={k:float(np.mean([r['delta'][k] for r in group])) for k in ['precision','recall','f1']},macro_minus_old={k:float(np.mean([r['minus_old'][k] for r in group])) for k in ['precision','recall','f1']},precision_up=sum(r['delta']['precision']>0 for r in group),precision_down=sum(r['delta']['precision']<0 for r in group),f1_up=sum(r['delta']['f1']>0 for r in group),f1_down=sum(r['delta']['f1']<0 for r in group),added_frames=sum(r['added_frames'] for r in group),changed=sum(r['added_frames']>0 for r in group),successful_nulls=sum(r['successful_null'] for r in group),worst_f1=min(r['delta']['f1'] for r in group))
    result=dict(status='COMPLETED_SINGLE_SOURCE_STABILITY_REPAIR_REVIEW_REQUIRED',summary={**{c:summary([r for r in rows if r['cohort']==c]) for c in selections},'all19':summary(rows)},sources=rows,automatic_production=False,all19_previously_exposed=True,calibrated_confidence_claim=False,official_joint_score=None,new_8B_calls=0,formal_data_read=False,utc=helper.utc())
    save(out/'result.json',result);print(json.dumps(result['summary']),flush=True)


if __name__=='__main__':
    try: main()
    except BaseException as error:
        save(ROOT/('remaining_eval_failure_'+uuid.uuid4().hex+'.json'),dict(error=repr(error),traceback=traceback.format_exc(),fit_preserved=True,no_automatic_retry=True))
        raise
