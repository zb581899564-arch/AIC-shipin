"""Fixed real CPU ROI/geometry-control fit, final checkpoints and screen readout.

No backbone, new images, test sources or inference-time labels. Running this
file requires both actual first spatial-feature stages and their CPU QA.
"""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import sys
import traceback

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'roi_code_06'))
from roi_runtime import registration,read,save,ref,bound,require,utc,sha
from roi_head import ARMS,fit,predict_scores,calibrate_margin,select_candidate,CandidateIoUHead


def run(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','Head fit is CPU only')
    reg=registration(root)
    fit_registration=read(root/'roi_fit_registration_07.json')
    require(fit_registration['fit_code']['path']==str(Path(__file__).resolve())
            and fit_registration['fit_code']['sha256']==sha(Path(__file__))
            and fit_registration['new_real_updates']==400 and fit_registration['arms']==list(ARMS),
            'Frozen exact CPU-fit code/400-update budget binding')
    import numpy as np
    import torch
    torch.set_num_threads(2)
    out=root/'roi_fit_07';out.mkdir(exist_ok=False)
    save(out/'claim.json',dict(utc=utc(),pid=os.getpid(),registration=ref(root/'roi_registration_06.json'),
         fit_code=ref(Path(__file__)),fit_registration=ref(root/'roi_fit_registration_07.json'),
         new_real_optimizer_updates_per_arm=200,new_8B_updates=0))
    completed=[]
    try:
        input_gate=read(root/'roi_inputs_06/input_acceptance.json')
        require(input_gate['status']=='PASS_ALL622_FIRST_ROI_INPUT_QA','All actual frozen input QA')
        input_lock=read(bound(input_gate['source_lock']))
        prepared=read(bound(input_lock['prepared']));target_file=bound(prepared['CPU_targets'])
        frozen_refs={(e['entry']['path'],e['entry']['sha256']) for e in input_lock['entries']}
        require(frozen_refs=={(e['path'],e['sha256']) for e in prepared['entries']} and len(frozen_refs)==622,
                'Frozen prepared/source lock exact622 input references')
        target_rows=read(target_file)['sources'];targets={r['item_id']:r for r in target_rows}
        require(len(targets)==len(target_rows)==622,'Exact separate original CPU target sources')
        sources={};source_evidence={};feature_QAs=[];actual_source_refs=set()
        for stage,expected in [('pilot32',32),('remaining590',590)]:
            terminal=read(root/('roi_'+stage+'_terminal_06.json'))
            resource=read(root/('roi_'+stage+'_resource_06.json'))
            require(terminal['exit_code']==0 and resource['record']['status']=='completed'
                    and resource['record']['exit_code']==0 and resource['unique_ledger_entries']==1,
                    'Actual unique natural GPU terminal before real head fit')
            qpath=root/('roi_'+stage+'_06/output_acceptance.json');qa=read(qpath)
            require(qa['status']=='PASS_ALL_FIRST_INDEPENDENT_ROI_OUTPUT_QA_NOT_QUALITY'
                    and qa['sources']==expected and len(qa['entries'])==expected,
                    'All actual first spatial feature QA before real head fit')
            feature_QAs.append(ref(qpath))
            for result_ref in qa['entries']:
                result=read(bound(result_ref));row=read(bound(result['source']));sid=row['item_id'];target=targets[sid]
                exact_ref=(result['source']['path'],result['source']['sha256'])
                require(exact_ref in frozen_refs and exact_ref not in actual_source_refs
                        and row['role']==result['role'], 'Actual GPU source/role is not the frozen admitted input')
                actual_source_refs.add(exact_ref)
                x=np.load(bound(result['features']),allow_pickle=False)
                y=np.asarray(target['candidate_ious'],dtype=np.float64)
                require(sid not in sources and result['source_sha256']==row['source_sha256']==target['source_sha256']
                        and row['role']==target['role'] and x.shape==(len(y),12296),
                        'Unique actual feature/reference role/source/candidate alignment')
                sources[sid]=dict(features=x,targets=y)
                source_evidence[sid]=dict(role=row['role'],source_sha256=row['source_sha256'],input=result['source'],
                     actual_features=result['features'],original_baseline_box=row['candidate_boxes'][0],
                     candidate_boxes=row['candidate_boxes'],baseline_is_observed_model=row['baseline_is_observed_model'])
        # Keep the deterministic original602 input order, independent of target.
        ids_by_role={role:[read(bound(r))['item_id'] for r in prepared['entries']
                          if read(bound(r))['role']==role] for role in ('train','dev','screen')}
        require({k:len(v) for k,v in ids_by_role.items()}==dict(train=482,dev=120,screen=20)
                and len(sources)==622 and actual_source_refs==frozen_refs,'Exact registered source-disjoint482/120/20')
        hashes={role:{source_evidence[sid]['source_sha256'] for sid in ids} for role,ids in ids_by_role.items()}
        require(not(hashes['train']&hashes['dev'] or hashes['train']&hashes['screen'] or hashes['dev']&hashes['screen']),
                'Byte identities cross research groups')
        require(all(source_evidence[s]['baseline_is_observed_model'] for s in ids_by_role['screen']),
                'Screen candidate0 must be actual previous model box')
        save(out/'fit_source_lock.json',dict(feature_QAs=feature_QAs,CPU_targets=ref(target_file),
             groups=ids_by_role,sources=source_evidence,global_source_independence='UNKNOWN',historical_exposure=True,
             official_sources_used=False,screen_or_confirm_in_fit=False))
        reports={}
        for arm in ARMS:
            dst=out/arm;dst.mkdir(exist_ok=False)
            model,norm,report=fit(sources,ids_by_role['train'],arm=arm,updates=200)
            cp=dst/'final.pt'
            torch.save(dict(state_dict=model.state_dict(),mean=torch.from_numpy(norm['mean']),std=torch.from_numpy(norm['std']),
                            arm=arm,updates=200,train_source_ids=ids_by_role['train']),cp)
            # The actual final checkpoint is reloaded, never re-trained or chosen
            # by its eventual screen metrics.
            saved=torch.load(cp,map_location='cpu',weights_only=True);reloaded=CandidateIoUHead(saved['arm'])
            reloaded.load_state_dict(saved['state_dict']);saved_norm={k:saved[k].numpy() for k in ('mean','std')}
            require(saved['train_source_ids']==ids_by_role['train'] and saved['updates']==200,'Saved actual fit recipe')
            for sid in sources:
                before=predict_scores(model,norm,sources[sid]['features'])
                after=predict_scores(reloaded,saved_norm,sources[sid]['features'])
                require(np.array_equal(before,after),'Final save/reload prediction mismatch')
            save(dst/'training_report.json',dict(**report,checkpoint_artifact=ref(cp),save_reload_all622_bit_equal=True))
            completed.append(dict(arm=arm,checkpoint=ref(cp),optimizer_updates=200))
            dev_scores={sid:predict_scores(reloaded,saved_norm,sources[sid]['features']) for sid in ids_by_role['dev']}
            calibration=calibrate_margin(dev_scores,{sid:sources[sid]['targets'] for sid in ids_by_role['dev']})
            save(dst/'calibration.json',dict(**calibration,checkpoint=ref(cp),fit_source_lock=ref(out/'fit_source_lock.json')))
            rows=[]
            for sid in ids_by_role['screen']:
                score=predict_scores(reloaded,saved_norm,sources[sid]['features']);truth=sources[sid]['targets']
                chosen=select_candidate(score,calibration['threshold']);e=source_evidence[sid]
                rows.append(dict(item_id=sid,source_sha256=e['source_sha256'],scores=score.tolist(),chosen_index=chosen,
                     candidate_boxes=e['candidate_boxes'],original_baseline_iou=float(truth[0]),selected_iou=float(truth[chosen]),
                     delta_iou=float(truth[chosen]-truth[0]),real_box_changed=(e['candidate_boxes'][chosen]!=e['candidate_boxes'][0]),
                     candidate_ious_reference_only=truth.tolist(),original_reference_changed=False))
            result=dict(arm=arm,checkpoint=ref(cp),calibration=ref(dst/'calibration.json'),threshold=calibration['threshold'],
                 sources=rows,mean_baseline_iou=float(np.mean([v['original_baseline_iou'] for v in rows])),
                 mean_selected_iou=float(np.mean([v['selected_iou'] for v in rows])),
                 mean_delta_iou=float(np.mean([v['delta_iou'] for v in rows])),
                 changed_sources=sum(v['real_box_changed'] for v in rows),
                 improved_sources=sum(v['delta_iou']>0 for v in rows),degraded_sources=sum(v['delta_iou']<0 for v in rows),
                 worst_source_delta=min(v['delta_iou'] for v in rows),historical_exposure=True,new_blind_sources=0,
                 static16_scope_only=True,production_admitted=False)
            save(dst/'screen_result.json',result);reports[arm]=result
        rr=read(out/'ROI/training_report.json');gr=read(out/'GEOMETRY_CONTROL/training_report.json')
        require(rr['batch_sequence_sha256']==gr['batch_sequence_sha256'] and rr['normalization_sha256']==gr['normalization_sha256'],
                'Two controlled arms diverged in batch or normalization')
        roi,control=reports['ROI'],reports['GEOMETRY_CONTROL']
        save(out/'completion.json',dict(status='COMPLETE_FIXED400_CPU_HEAD_UPDATES_AND_SCREEN_NOT_PRODUCTION',utc=utc(),
             arms={k:{f:v[f] for f in ('checkpoint','calibration','threshold','mean_baseline_iou','mean_selected_iou',
                    'mean_delta_iou','changed_sources','improved_sources','degraded_sources','worst_source_delta')} for k,v in reports.items()},
             ROI_minus_geometry_mean_iou=roi['mean_selected_iou']-control['mean_selected_iou'],
             new_real_head_updates=400,new_8B_updates=0,new_model_calls=0,automatic_confirm=False,production_admitted=False,
             scope='Previously exposed static native16 GNMC file-level research; video/joint transfer UNKNOWN'))
        require(not torch.cuda.is_initialized(),'CPU head fit initialized CUDA')
    except BaseException as e:
        save(out/'failure.json',dict(error=repr(e),traceback=traceback.format_exc(),completed=completed,
             preserve_all_success=True,do_not_repeat_success=True,failure_not_empty=True));raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();run(a.root)
