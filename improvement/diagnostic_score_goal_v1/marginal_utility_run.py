"""One baseline-conditional CPU utility fit on adopted external group features."""
import argparse
from pathlib import Path
import sys
import traceback
import datetime as dt

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'pair_code_17'))
from pair_common import *
from marginal_utility_head import build_design, fit_heads, predict, select_addition


def run(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'Only CPU utility child masks itself')
    import numpy as np
    import torch
    torch.set_num_threads(2)
    reg=read(root/'marginal_utility_registration_25.json')
    require(reg['schema']=='BASELINE_CONDITIONAL_MARGINAL_UTILITY19_SINGLE_FIT_V25', 'Explicit utility entry')
    require(dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat(reg['deadline_utc'].replace('Z','+00:00')),
            'Inside authorized overall work window')
    require(bound(reg['code'])==Path(__file__).resolve(), 'Frozen utility runner')
    import marginal_utility_head
    require(bound(reg['head_code'])==Path(marginal_utility_head.__file__).resolve(), 'Frozen utility implementation')
    audit=read(bound(reg['marginal_audit']))
    require(audit['status']=='COMPLETE_FIRST_NATIVE_MARGINAL_GAIN_TARGET_AUDIT_ONLY', 'Actual first target audit')
    old=read(bound(reg['pair_registration']))
    for reference in reg['original_feature_output_QA']:
        require(read(bound(reference))['status']=='PASS_ALL_FIRST_OUTPUT_QA_WITHOUT_NEW_FORWARD',
                'Adopt once-completed frozen group-feature QA; do not replay')
    catalog=read(bound(old['assembled_external']))
    source_map={s['id']:s for s in catalog['sources']}
    require(len(source_map)==len(audit['sources'])==25, 'All original external25 identities')
    with np.load(bound(reg['old_unsupervised_transform']),allow_pickle=False) as data:
        transform={'RMS':data['RMS'].copy(),'PCA16':data['PCA'][:,:16].copy()}
    require(transform['RMS'].shape==(8192,) and transform['PCA16'].shape==(8192,16),
            'Adopt fixed first16 train-only PCA directions; never adopt failed old beta')
    out=root/'marginal_utility_25';out.mkdir(exist_ok=False)
    save(out/'claim.json',dict(utc=utc(),pid=os.getpid(),registration=ref(root/'marginal_utility_registration_25.json'),
         new_8B_forwards=0,new_PCA_fits=0,new_optimizer_updates=0))
    done=[]
    try:
        designs,targets,rows={}, {}, {}
        for entry in audit['sources']:
            a=read(bound(entry['result']));sid=a['id'];source=source_map[sid]
            require(a['source_sha256']==source['source_sha256'] and a['role']==source['role'] and
                    a['features']==source['features'] and a['native']==source['native'], 'Actual audit/source/input identities')
            with np.load(bound(a['features']),allow_pickle=False) as data:
                features=data['features'].copy();groups=data['native_group'].copy()
            with np.load(bound(a['native']),allow_pickle=False) as data:
                baseline=data['baseline'].copy();cells=data['groups'].copy()
            require(np.array_equal(groups,cells//2) and baseline.dtype==np.bool_ and
                    features.shape==(source['groups'],8192), 'Accepted original feature/native mapping')
            clips=[x['clip'] for x in a['candidates']]
            design=build_design(features,groups,baseline,clips,transform)
            z=np.asarray([len(groups)/(2*x['clip']['native_frames'])*x['gain']['macro_delta']
                          for x in a['candidates']],dtype=np.float64)
            require(design.shape==(len(clips),19) and z.shape==(len(clips),) and np.isfinite(z).all(),
                    'Complete baseline-conditional design and absolute expected-gain zero')
            designs[sid]=design;targets[sid]=z;rows[sid]=a
        train_ids=sorted(sid for sid,s in source_map.items() if s['role']=='train')
        dev_ids=sorted(sid for sid,s in source_map.items() if s['role']=='dev')
        require(len(train_ids)==20 and len(dev_ids)==5 and not
                ({source_map[s]['source_sha256'] for s in train_ids}&{source_map[s]['source_sha256'] for s in dev_ids}),
                'Original20/5 known-byte disjoint roles')
        oldfit=read(bound(reg['old_transform_report']))
        require(oldfit['train_ids']==train_ids and oldfit['report']['PCA_dimensions']==32 and
                oldfit['report']['train_only_RMS'] is True and oldfit['checkpoint']==reg['old_unsupervised_transform'],
                'The adopted PCA prefix must be the unchanged original20-train-only transform')
        state,report=fit_heads(designs,targets,train_ids)
        require(all(isinstance(x,np.ndarray) and x.dtype.kind in 'fiu' and np.isfinite(x).all() for x in state.values()),
                'Flat finite numeric fitted state only')
        artifact=dict(**state,projection_RMS=transform['RMS'],projection_PCA=transform['PCA16'])
        checkpoint=out/'final_utility.npz'
        with checkpoint.open('xb') as stream:np.savez(stream,**artifact)
        with np.load(checkpoint,allow_pickle=False) as data:restored={k:data[k].copy() for k in state}
        save(out/'fit_report.json',dict(report=report,checkpoint=ref(checkpoint),train_ids=train_ids,dev_ids=dev_ids,
            new_closed_form_fits=2,new_PCA_fits=0,new_optimizer_updates=0,new_8B_forwards=0,
            target='z=N/(2c)*all-original-rater mean paired F1 addition delta; never source-center target',
            source_equal_candidate_average=True,actual_numeric_artifact_elements=sum(x.size for x in artifact.values()),
            conservative_pipeline_parameters=8782557449+sum(x.size for x in artifact.values()),
            original_unsupervised_transform=reg['old_unsupervised_transform'],old_failed_beta_loaded=False))
        scores={}
        for sid,design in designs.items():
            current=predict(state,design);again=predict(restored,design)
            require(set(current)==set(again)=={'VISUAL','METADATA','CONSTANT'} and
                    all(np.array_equal(current[k],again[k]) and np.isfinite(current[k]).all() for k in current),
                    'Exact saved/reloaded new utility readouts')
            scores[sid]=current
            path=out/(sid+'.scores.npz')
            with path.open('xb') as stream:np.savez(stream,**current)
            done.append(dict(id=sid,scores=ref(path)))
        summary={}
        decisions=[]
        for sid,row in rows.items():
            n=row['inventory']['native_frames'];clips=[x['clip'] for x in row['candidates']]
            actual=np.asarray([x['gain']['macro_delta'] for x in row['candidates']])
            before=row['candidates'][0]['gain']['baseline_macro_f1'] if row['candidates'] else None
            require(before is not None, 'Registered external all25 have candidate support')
            oracle=max([0.]+actual.tolist())
            for arm,zpred in scores[sid].items():
                decision=select_addition(clips,zpred,n)
                selected=decision['selected']
                index=next((i for i,c in enumerate(clips) if selected is not None and
                            c['start_group']==selected['start_group']),None)
                gain=0. if index is None else float(actual[index])
                decisions.append(dict(id=sid,role=row['role'],arm=arm,source_sha256=row['source_sha256'],
                    before_F1=before,after_F1=before+gain,delta_F1=gain,oracle_one_addition_delta=oracle,
                    oracle_regret=oracle-gain,added_native_frames=0 if index is None else clips[index]['native_frames'],
                    harmful_addition=bool(gain<0),beneficial_addition=bool(gain>0),
                    source_equal_target_MSE=float(np.mean((zpred-targets[sid])**2)),
                    decision=decision))
        for role in ('train','dev'):
            summary[role]={}
            for arm in ('VISUAL','METADATA','CONSTANT'):
                part=[x for x in decisions if x['role']==role and x['arm']==arm]
                summary[role][arm]=dict(sources=len(part),baseline_F1=float(np.mean([x['before_F1'] for x in part])),
                    proposal_F1=float(np.mean([x['after_F1'] for x in part])),
                    macro_delta_F1=float(np.mean([x['delta_F1'] for x in part])),
                    worst_source_delta=min(x['delta_F1'] for x in part),
                    changed_sources=sum(x['added_native_frames']>0 for x in part),
                    beneficial_sources=sum(x['beneficial_addition'] for x in part),
                    harmful_sources=sum(x['harmful_addition'] for x in part),
                    added_native_frames=sum(x['added_native_frames'] for x in part),
                    source_equal_target_MSE=float(np.mean([x['source_equal_target_MSE'] for x in part])),
                    mean_oracle_regret=float(np.mean([x['oracle_regret'] for x in part])))
        save(out/'result.json',dict(status='COMPLETE_ONE_FROZEN_CONDITIONAL_UTILITY_AND_CONTROLS_NOT_PRODUCTION',
             summary=summary,decisions=decisions,readouts=done,checkpoint=ref(checkpoint),train_ids=train_ids,dev_ids=dev_ids,
             all_original_raters=True,source_equal=True,historical_exposure=True,independent_blind=False,
             baseline_scope='Original external B0 NOT complete40.47',official_joint_metric=False,
             new_PCA_fits=0,new_closed_form_fits=2,new_8B_forwards=0,new_optimizer_updates=0,
             no_threshold_or_lambda_scan=True,production_admitted=False,baseline_frames_removed=0))
        require(not torch.cuda.is_initialized(), 'Utility evaluation remains CPU only')
        print(json.dumps(summary),flush=True)
    except BaseException as error:
        save(out/'failure.json',dict(error=repr(error),traceback=traceback.format_exc(),completed_readouts=done,
            preserve_all_success=True,no_automatic_retry=True))
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);run(p.parse_args().root)
