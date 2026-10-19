"""Output-only first QA/evaluation; preserve failed GPU terminal, no model retry."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
from pathlib import Path
import importlib.util,sys,json
import numpy as np
P=Path('/home/inspur/aic_video_work/visual_pair_reject_20261018_v1/code_v2/visual_pair_v2.py')
spec=importlib.util.spec_from_file_location('_pair_adopted_pure_io',P);base=importlib.util.module_from_spec(spec);sys.modules[spec.name]=base;spec.loader.exec_module(base)
ROOT,W=base.ROOT,base.W
read,save,ref,bound,require=base.read,base.save,base.ref,base.bound,base.require
helper,leaf,deadline=base.helper,base.leaf,base.deadline

def evaluate():
    os.environ['CUDA_VISIBLE_DEVICES']='';deadline()
    reg=read(ROOT/'registration_01.json');gpu=read(ROOT/'adopted_output_registration_03.json');require(gpu['status']=='ADOPT34_ACTUAL_OUTPUTS_GPU_TERMINAL_FLAG_FAILED_NOT_CHAIN_PASS','Explicit output-only engineering adoption')
    outputs={}
    for value in gpu['outputs']:
        done=read(bound(value));raw=read(bound(done['raw_ref']));require(json.loads(raw['raw'])==dict(choice=done['choice']),'Independent untouched raw JSON parse')
        outputs[(done['sid'],done['order'])]=done['choice']
    decisions=[]
    for case in reg['cases']:
        ab=outputs[(case['sid'],'AB')];ba=outputs[(case['sid'],'BA')]
        decisions.append(dict(sid=case['sid'],cohort=case['cohort'],AB=ab,BA=ba,keep=ab=='B' and ba=='A',case=case))
    save(ROOT/'decisions_before_metrics_03.json',dict(status='ALL17_FIXED_ORDER_BALANCED_DECISIONS_BEFORE_CURRENT_METRICS',decisions=decisions,labels_read=False,orders_not_independent=True,utc=helper.utc()))
    # Labels stay outside all model/preparation code, first read below.
    oldm=leaf('_visual_pair_metric_contract',W/'source_consensus_event_20261018_v1/code_v1/source_consensus.py');rows=[]
    for decision in decisions:
        case=decision['case'];sid=case['sid'];data=np.load(bound(case['original_input_ref']),allow_pickle=False);labels=np.load(W/'source_consensus_event_20261018_v1/diagnosis_01'/(sid+'_human_targets.npz'),allow_pickle=False)['labels'];mask=data['baseline'].copy()
        c=case['original_choice'];new=np.zeros(len(mask),bool);new[c['left']:c['right']]=~mask[c['left']:c['right']]
        contrast=float(labels[new].mean()-labels[mask].mean());benefit=contrast>0
        if decision['keep']:mask|=new
        before=oldm.critic.metric(data['baseline'],labels);after=oldm.critic.metric(mask,labels)
        rows.append(dict(sid=sid,keep=decision['keep'],actual_precision_benefit=benefit,actual_precision_contrast=contrast,delta={k:after[k]-before[k] for k in ['precision','recall','f1']},added_frames=int(new.sum()) if decision['keep'] else 0))
    result=dict(status='COMPLETED_ONE_VISUAL_PAIR_REJECT_PILOT_REVIEW_REQUIRED',sources=rows,kept=sum(r['keep'] for r in rows),kept_good=sum(r['keep'] and r['actual_precision_benefit'] for r in rows),kept_bad=sum(r['keep'] and not r['actual_precision_benefit'] for r in rows),rejected_good=sum(not r['keep'] and r['actual_precision_benefit'] for r in rows),rejected_bad=sum(not r['keep'] and not r['actual_precision_benefit'] for r in rows),macro_delta={k:float(np.mean([r['delta'][k] for r in rows])) for k in ['precision','recall','f1']},added_frames=sum(r['added_frames'] for r in rows),all_sources_previously_exposed=True,new_blind_confirmation=False,automatic_production=False,official_joint_score=None,utc=helper.utc())
    save(ROOT/'result_03.json',result);print(json.dumps(result),flush=True)


if __name__=='__main__': evaluate()
