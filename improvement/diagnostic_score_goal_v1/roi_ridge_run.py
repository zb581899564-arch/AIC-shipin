"""A single new source-balanced linear relative-IoU research readout."""
import argparse
import os
from pathlib import Path
import sys
import time
import traceback

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'roi_code_06'))
from roi_runtime import require,read,save,ref,bound,sha,utc,registration
from roi_ridge import ARMS,fit_projection,fit_coefficients,predict,choose


def run(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','New linear research stage CPU only')
    registration(root)
    reg=read(root/'roi_relative_registration_09.json')
    for n,digest in reg['new_code'].items():
        require(sha(root/'roi_relative_code_09'/n)==digest,'Frozen one-version relative readout changed')
    import numpy as np
    import torch
    import resource
    torch.set_num_threads(2)
    out=root/'roi_relative_09';out.mkdir(exist_ok=False)
    save(out/'claim.json',dict(utc=utc(),pid=os.getpid(),registration=ref(root/'roi_relative_registration_09.json'),
         original_MLP_remains_STOP=True,new_8B_calls=0,new_optimizer_updates=0))
    completed=[];start=time.monotonic()
    try:
        fitlock=read(bound(reg['previous_fit_source_lock']))
        previous=read(bound(reg['previous_fit_completion']))
        require(previous['new_real_head_updates']==400,'Previous MLP400 result remains untouched')
        gate=read(bound(reg['input_acceptance']));lock=read(bound(gate['source_lock']));prepared=read(bound(lock['prepared']))
        require(prepared['CPU_targets']==fitlock['CPU_targets'],'Exact original human-target reference lock')
        target_file=bound(prepared['CPU_targets']);target_rows=read(target_file)['sources'];targets={t['item_id']:t for t in target_rows}
        expected={r['item_id']:reference for reference in prepared['entries'] for r in [read(bound(reference))]}
        groups=fitlock['groups']
        require(len(expected)==len(targets)==622 and {k:len(v) for k,v in groups.items()}==dict(train=482,dev=120,screen=20),
                'Frozen unique historical482/120/20 source groups')
        require(set(expected)==set(fitlock['sources'])==set(targets),'Exact same622 feature/reference identities')
        sources={}
        for sid,e in fitlock['sources'].items():
            target=targets[sid];row=read(bound(expected[sid]))
            require(e['input']==expected[sid] and e['role']==target['role']==row['role']
                    and e['source_sha256']==target['source_sha256']==row['source_sha256']
                    and row['candidate_boxes']==e['candidate_boxes'],'Frozen original pool/source role alignment')
            sources[sid]=dict(features=np.load(bound(e['actual_features']),allow_pickle=False),
                              targets=np.asarray(target['candidate_ious'],np.float64))
        require(all({s for s in groups[role]}=={sid for sid,e in fitlock['sources'].items() if e['role']==role}
                    for role in groups),'Group IDs exactly match frozen actual feature roles')
        sets={role:{fitlock['sources'][sid]['source_sha256'] for sid in ids} for role,ids in groups.items()}
        require(not(sets['train']&sets['dev'] or sets['train']&sets['screen'] or sets['dev']&sets['screen']),
                'Train/dev/screen known-byte overlap')
        old=torch.load(bound(reg['train_only_normalization_checkpoint']),map_location='cpu',weights_only=True)
        require(old['train_source_ids']==groups['train'],'Adopted normalization exact482 train identities')
        norm={k:old[k].numpy() for k in ('mean','std')};del old
        state,x,y,w,rows=fit_projection(sources,groups['train'],norm)
        npz=out/'projection.npz'
        with npz.open('xb') as f:np.savez(f,**{k:v for k,v in state.items() if k!='train_ids'})
        with np.load(npz,allow_pickle=False) as f:saved_state={k:f[k] for k in f.files}
        require(all(np.array_equal(saved_state[k],v) for k,v in state.items() if k!='train_ids'),'PCA/normalization save-reload mismatch')
        save(out/'projection_report.json',dict(status='ONE_UNSUPERVISED_TRAIN_ONLY_SOURCE_CENTERED_PCA32',
             projection=ref(npz),train_ids=groups['train'],PCA_candidates_source_equal=True,PCA_per_source_centered=True,
             PCA_seed=20261018,PCA_power_iterations=2,new_optimizer_updates=0,reference_used_for_PCA=False,
             source_equal_nonbaseline_loss_weights_sum=float(w.sum()),baseline_loss_weight_zero=True,
             relative_origin_after_transform='candidate_minus_candidate0_NO_SECOND_CENTERING',
             relative_scale='Train-only source-equal nonbaseline RMS, floor1e-4',
             original_normalization=reg['train_only_normalization_checkpoint']))
        reports={}
        for arm in ARMS:
            dst=out/arm;dst.mkdir(exist_ok=False)
            beta,report=fit_coefficients(x,y,w,arm)
            cp=dst/'beta.npy'
            with cp.open('xb') as f:np.save(f,beta,allow_pickle=False)
            saved_beta=np.load(cp,allow_pickle=False)
            for sid in sources:
                require(np.array_equal(predict(state,beta,sources[sid]['features'],arm),
                                       predict(saved_state,saved_beta,sources[sid]['features'],arm)),
                        'Actual relative model save/reload all622 mismatch')
            save(dst/'fit_report.json',dict(**report,beta=ref(cp),projection=ref(npz),source_groups=groups,
                 all622_save_reload_exact=True,old_MLP_weights_loaded_as_predictor=False,
                 new_8B_calls=0,new_optimizer_updates=0,policy='Best predicted relative IoU strictly>0 else originalbaseline',
                 uncertainty_calibrated=False,video_transfer_guarantee=False))
            completed.append(dict(arm=arm,closed_form_solves=1,beta=ref(cp)))
            byrole={}
            for role in ('dev','screen'):
                output=[]
                for sid in groups[role]:
                    score=predict(saved_state,saved_beta,sources[sid]['features'],arm)
                    chosen=choose(score);truth=sources[sid]['targets'];e=fitlock['sources'][sid]
                    output.append(dict(item_id=sid,source_sha256=e['source_sha256'],role=role,
                         candidate_boxes=e['candidate_boxes'],predicted_relative_IoU=score.tolist(),chosen_index=chosen,
                         original_baseline_iou=float(truth[0]),selected_iou=float(truth[chosen]),
                         delta_iou=float(truth[chosen]-truth[0]),candidate_ious_reference_only=truth.tolist(),
                         real_box_changed=(e['candidate_boxes'][chosen]!=e['candidate_boxes'][0])))
                summary=dict(sources=len(output),mean_baseline_iou=float(np.mean([v['original_baseline_iou'] for v in output])),
                     mean_selected_iou=float(np.mean([v['selected_iou'] for v in output])),
                     mean_delta_iou=float(np.mean([v['delta_iou'] for v in output])),changed_sources=sum(v['real_box_changed'] for v in output),
                     improved_sources=sum(v['delta_iou']>0 for v in output),degraded_sources=sum(v['delta_iou']<0 for v in output),
                     worst_source_delta=min(v['delta_iou'] for v in output),historical_exposure=True,new_blind_sources=0)
                save(dst/(role+'_result.json'),dict(arm=arm,summary=summary,sources=output,policy_fixed_before_scores=True,
                     production_admitted=False,threshold_or_dimension_search=False));byrole[role]=summary
            reports[arm]=byrole
        save(out/'completion.json',dict(status='COMPLETE_NEW_RELATIVE_LINEAR_RESEARCH_NO_PRODUCTION',utc=utc(),
             arms=reports,ROI_minus_geometry_screen_IoU=reports[ARMS[0]]['screen']['mean_selected_iou']-reports[ARMS[1]]['screen']['mean_selected_iou'],
             elapsed_seconds=time.monotonic()-start,max_resident_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
             new_optimizer_updates=0,new_PCA_fits=1,new_closed_form_head_fits=2,new_8B_calls=0,
             original_MLP_and_calibration_unchanged=True,automatic_confirm=False,production_admitted=False,
             scope='Static historically exposed native16 GNMC; no official joint-quality evidence; multiple recipe changes not causal ablation'))
        require(not torch.cuda.is_initialized(),'CPU linear stage initialized CUDA')
    except BaseException as e:
        save(out/'failure.json',dict(error=repr(e),traceback=traceback.format_exc(),completed=completed,
             preserve_all_success=True,do_not_repeat_success=True,failure_is_not_empty=True));raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();run(a.root)
