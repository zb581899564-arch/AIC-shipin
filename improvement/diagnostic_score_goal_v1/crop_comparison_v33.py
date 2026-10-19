"""One final500 screen comparison; no model, processor, threshold search or package."""
import argparse
import hashlib
import importlib.util
import os
from pathlib import Path
import sys
import traceback
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pair_code_17'))
from pair_common import read,save,ref,bound,require,utc


def _module(reference,name):
    path=bound(reference);spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module


def run(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','Only independent CPU comparison')
    import numpy as np
    reg=read(root/'crop_remaining_admission_33.json');original=read(bound(reg['original_pilot_registration']))
    require(bound(reg['comparison_code'])==Path(__file__).resolve(),'Exact frozen33 comparison')
    cpu=read(bound(original['CPU_registration']));gate=read(bound(original['input_acceptance']));prepared=read(bound(gate['prepared']))
    policy=_module(reg['policy_code'],'_frozen_crop_policy33');geom=_module(cpu['geometry_code'],'_frozen_crop_geometry31_comparison')
    baseline=read(bound(reg['BASE_output_acceptance']));trained_ref=root/'crop_TRAINED_output_acceptance_33.json';trained=read(trained_ref)
    require(baseline['status']=='PASS_CROP_BASE_SCREEN_AND_PILOT4_FIRST_QA' and
        trained['status']=='PASS_CROP_TRAINED_SCREEN_FINAL500_FIRST_QA' and trained['registration']==ref(root/'crop_remaining_admission_33.json') and
        trained['engineering']['adopted_BASE_acceptance']==reg['BASE_output_acceptance'] and
        trained['original_GPU_registration']==baseline['original_GPU_registration']==reg['original_pilot_registration'],
        'Actual first independent complete BASE/final500 output acceptance')
    final=read(bound(trained['training_completion']))
    require(final['completed_updates']==500 and final['successful_micro']==2000 and final['adapter_reload_all288_exact'] is True,
            'Only fixed-final500 complete comparison; no checkpoint selection')
    catalog=read(bound(prepared['source_catalog']));sources={s['source_id']:s for s in catalog['sources']}
    target_ref=reg['CPU_targets'];targets=read(bound(target_ref));bytarget={s['source_id']:s for s in targets['sources']}
    plan=read(bound(prepared['case_plan']));require(plan['GT_used_for_input_or_pair_choice'] is False,'Frozen GT-free inputs/pairs')
    require(set(sources)==set(bytarget) and len(sources)==622 and len(bytarget)==622,'Exact602train+20screen target/source binding')
    for sid,source in sources.items():
        target=bytarget[sid]
        require(target['source_sha256']==source['source_sha256'] and target['role']==source['role'] and
            target['reference_modified'] is False and len(target['candidate_ious'])==len(source['pool']),
            'Original source/role/reference/candidate count differs')
        expected=[geom.crop_iou(box,target['original_reference_xywh']) for box in source['pool']]
        require(np.array_equal(np.asarray(expected,np.float64),np.asarray(target['candidate_ious'],np.float64)),
                'New candidate/reference IoU target indexing differs')
    out=root/'crop_comparison_33';out.mkdir(exist_ok=False)
    save(out/'claim.json',dict(utc=utc(),registration=ref(root/'crop_remaining_admission_33.json'),
        primary='TRAINED',historical_exposure=True,model_calls=0,old_raw_QA_repeated=False))
    try:
        fit_rows=[dict(source_id=sid,width=s['width'],height=s['height'],pool=s['pool'],candidate_ious=bytarget[sid]['candidate_ious'])
            for sid,s in sources.items() if s['role']=='train']
        require(len(fit_rows)==602,'Only author-train602 in diagnostic geometry control')
        coeff=policy.fit_geometry(fit_rows);p=out/'geometry_control.npz'
        with p.open('xb') as f:np.savez(f,beta=coeff)
        with np.load(p,allow_pickle=False) as z:reloaded=z['beta'].copy()
        require(coeff.shape==(13,) and coeff.dtype==np.float64 and np.array_equal(coeff.view(np.uint8),reloaded.view(np.uint8)),
                'New diagnostic13 coefficient exact save/reload')
        geometry_choices={sid:policy.geometry_select(s['pool'],s['width'],s['height'],reloaded,baseline_index=0)
            for sid,s in sources.items() if s['role']=='screen'}
        expected_ids={e['id'] for e in prepared['screen_inputs']};exports={};reports={}
        for name,accepted in [('BASE',baseline),('TRAINED',trained)]:
            predictions=accepted['predictions'];require(len(predictions)==len(expected_ids) and {r['id'] for r in predictions}==expected_ids,
                'Exactly one already accepted raw-derived probability per screen input')
            predictions={r['id']:r for r in predictions};rows=[];self_pass=0;pair_rows=[]
            for sid,source in sources.items():
                if source['role']!='screen':continue
                pairs=[];own=[]
                for pair in plan['pair_index']:
                    if pair['source_id']!=sid:continue
                    a,b=predictions[pair['first_id']],predictions[pair['reverse_id']]
                    require(a['source_id']==b['source_id']==sid and a['source_sha256']==b['source_sha256']==source['source_sha256'],
                            'Accepted pair source identity differs')
                    if pair['same_crop']:own.append(a['probabilities3'])
                    else:pairs.append(dict(candidate_index=pair['candidate_index'],forward_probs=a['probabilities3'],reverse_probs=b['probabilities3']))
                require(len(own)==1,'Exactly one actual samecrop control per source')
                self_pass+=int(policy.strict_tie(own[0]));chosen=policy.select_pool(source['pool'],0,pairs)
                ious=bytarget[sid]['candidate_ious'];geometry=geometry_choices[sid]
                rows.append(dict(source_id=sid,source_sha256=source['source_sha256'],baseline_iou=ious[0],selected_iou=ious[chosen],
                    geometry_iou=ious[geometry],oracle_iou=max(ious),baseline_index=0,selected_index=chosen,geometry_index=geometry,
                    baseline_box=source['pool'][0],selected_box=source['pool'][chosen],original_reference_modified=False))
                pair_rows.append(dict(source_id=sid,pairs=pairs,samecrop_probs=own[0]))
            summary=policy.summarize(rows);quality=policy.quality_checks(summary,'screen20',self_pass,0)
            reports[name]=dict(summary=summary,quality=quality,samecrop_strict_TIE=self_pass,pairs=pair_rows,
                accepted_predictions_scope='Already first-QAd raw; no second raw or input QA')
            exports[name]=rows
        save(out/'geometry_control_receipt.json',dict(coefficients=ref(p),parameters=13,new_fits=1,new_PCA=0,new_optimizer=0,
            training_sources=602,source_equal_candidate_loss=True,ridge=0.01,intercept_penalized=False,
            not_loaded_in_production=True,eval_target_fitted=False))
        qualified=reports['TRAINED']['quality']['admitted']
        save(out/'result.json',dict(status='PASS_NATIVE_CROP_SCREEN_ONLY' if qualified else 'STOP_NATIVE_CROP_SCREEN',
            primary='TRAINED',reports=reports,selected=exports,confirm_admitted=qualified,production_prepare_approved=False,
            fixed_final_checkpoint=True,no_threshold_search=True,new_model_calls=0,new_gradient_updates=0,new_closed_form_fits=1,
            historical_exposure=True,new_blind_sources=0,single_editor_reference=True,official_joint_metric=False,
            BASE_acceptance=reg['BASE_output_acceptance'],TRAINED_acceptance=ref(trained_ref),CPU_targets=target_ref,
            registration=ref(root/'crop_remaining_admission_33.json'),policy_code=reg['policy_code'],
            geometry_control=ref(out/'geometry_control_receipt.json'),adapter_weights=final['adapter_weights'],
            note='Staticnative16 research only. Production RGB/profile/temporal applicability must be separately established; no automatic426 orZIP.'))
        print('CROP_SCREEN',qualified,reports['TRAINED']['summary'],flush=True)
    except BaseException as error:
        save(out/'failure.json',dict(error=repr(error),traceback=traceback.format_exc(),preserve_all_success=True,no_automatic_retry=True))
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);run(parser.parse_args().root)
