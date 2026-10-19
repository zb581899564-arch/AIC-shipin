"""Pure posthoc fixed-control promotion and geometry-only gain; no IO/fit/GT."""
from __future__ import annotations
import copy
import re
import numpy as np
import direct_box_math_v84 as geometry84

STATUS='QUALIFIED_GEOM129_FOR_SEPARATE_FROZEN_FRESH8_TRIAL_NOT_PRODUCTION'
POLICY='TRUST124_THEN_GEOM129_GAIN_STRICTLY_POSITIVE'
PIPELINE_PARAMETERS=8790372845
ORIGINAL_CHECKS={'exact_sources','minimum_gain','at_least5_improved','worst_loss_at_most_point1','actual_change','invalid0',
    'beats_OLD70_BETA_GEOMETRY','beats_OLD47_GEOM11','beats_OLD33_GEOM13'}


def require(value,message):
    if not value:raise ValueError(message)


def _ref(value):
    require(isinstance(value,dict) and set(value)=={'path','sha256'} and isinstance(value['path'],str) and value['path']
        and isinstance(value['sha256'],str) and re.fullmatch('[0-9a-f]{64}',value['sha256']) is not None,'Explicit immutable artifact reference, externally SHA-bound by caller')
    return copy.deepcopy(value)


def geometry11(box,W,H):
    require(geometry84.legal_native(box,W,H),'Only actual legal native3 baseline/proposal')
    x,y,w=np.asarray(box,np.float64)/np.array([W,H,W],np.float64);h=9*float(box[2])/(16*H)
    return np.array([x,y,w,h,x*x,y*y,w*w,h*h,x*y,x*w,y*h],np.float64)


def geometry_gain(state,baseline,proposal,W,H):
    """Exact frozen128 GEOM11 score; mean/PCA/h are neither needed nor read."""
    rms=state['RMS'];beta=state['GEOM11_beta']
    require(isinstance(rms,np.ndarray) and rms.dtype==np.float64 and rms.shape==(107,)
        and isinstance(beta,np.ndarray) and beta.dtype==np.float64 and beta.shape==(11,)
        and bool(np.isfinite(rms[:11]).all()) and bool((rms[:11]>0).all()) and bool(np.isfinite(beta).all()),'Original frozen128 F64 GEOM11 coefficients and exact first11 RMS')
    value=float(((geometry11(proposal,W,H)-geometry11(baseline,W,H))/rms[:11])@beta)
    require(np.isfinite(value),'Finite fixed geometry gain')
    return value


def validate_promotion(old128result,*,result_ref,state_ref,model_refs):
    """Inspect saved development evidence only; caller binds actual ref bytes.

    This does not authorize a worker or establish fresh8/production quality.
    No coefficients, PCA, labels or old development predictions are refitted.
    """
    _ref(result_ref);_ref(state_ref)
    require(set(model_refs)=={'training_completion','adapter_weights','head_weights'},'Exact final105 three model references')
    for reference in model_refs.values():_ref(reference)
    r=old128result
    require(r['status']=='STOP_DIRECT_BOX128_NATIVE20_AND_HISTORICAL19_RELATIVE_CRITIC' and r['admitted_arms']==[]
        and r['state']==state_ref and all(r[k]==v for k,v in model_refs.items()) and r['exact_save_reload'] is True,
        'Old128 remains real STOP; exact original saved/reloaded state and supervised model only')
    fit=r['fit'];require(fit['fit_count']==1 and fit['train_sources']==602 and fit['projections']==7224 and fit['rows']==14448,
        'One original602 counterfactual fit only; no new PCA/ridge/threshold or coefficient fit')
    require(r['additional_parameters']==135393 and r['pipeline_parameters']==PIPELINE_PARAMETERS,'Conservative unchanged full128 state parameter count')
    require(set(r['evaluations'])=={'native20','historical19'},'Both exposed development groups independently retained')
    development={}
    for scope,n in (('native20',20),('historical19',19)):
        arm=r['evaluations'][scope]['arms']['GEOM11'];summary=arm['summary'];checks=arm['quality']['checks'];rows=arm['rows']
        require(arm['quality']['admitted'] is True and set(checks)==ORIGINAL_CHECKS and all(v is True for v in checks.values())
            and summary['sources']==n and len(rows)==n and len({x['source_id'] for x in rows})==n
            and summary['mean_gain']>=.01 and summary['improved']>=5 and summary['worst_loss']<=.1
            and summary['changed']>=1 and summary['invalid']==0,'Both GEOM development groups pass every unchanged original gate')
        rejected=sum(x['trust_changed'] and not x['changed'] for x in rows)
        require(rejected>=1 and sum(bool(x['changed']) for x in rows)==summary['changed'],'GEOM truly rejects changed trust proposals and retains real changes')
        development[scope]=dict(summary=copy.deepcopy(summary),original_checks=copy.deepcopy(checks),changed_trust_rejected=int(rejected),
            historical_not_blind=True,development_not_confirmation=True)
    native=r['evaluations']['native20']['arms'];delta=float(native['GEOM11']['summary']['mean_selected_iou']-native['ALWAYS_ACCEPT124']['summary']['mean_selected_iou'])
    require(np.isfinite(delta) and delta<0 and native['JOINT']['quality']['admitted'] is False,
        'Retain native20 GEOM loss versus always124 and failed JOINT; do not relabel128 admission')
    return dict(schema='POSTHOC_FROZEN_GEOM11_CONTROL_PROMOTION_V129',status=STATUS,policy=POLICY,
        source_result=_ref(result_ref),source_status=r['status'],state=_ref(state_ref),**copy.deepcopy(model_refs),
        development=development,negative_evidence=dict(native20_GEOM_minus_ALWAYS_ACCEPT124=delta,native20_lost_to_always124=True,
            old_JOINT_not_qualified=True),posthoc_control_promotion=True,old128_STOP_unchanged=True,
        coefficients_not_refitted=True,coefficient_keys=['RMS[:11]','GEOM11_beta'],PCA_or_hidden_used_by_critic=False,
        gain_threshold=0.,comparison='STRICTLY_GREATER_THAN',additional_parameters_conservatively_counted=135393,
        pipeline_parameters=PIPELINE_PARAMETERS,fresh8_quality_established=False,production_admitted=False,
        model_calls=0,new_fit=0,old39_re_evaluated=False)
