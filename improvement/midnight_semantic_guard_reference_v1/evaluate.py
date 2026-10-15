"""First and only human-reference comparison of the preregistered semantic guard."""
import argparse
from fractions import Fraction as F
import os
from pathlib import Path
import sys
from adopted_bindings import checked_decisions
from reference_common import (checked,exact_metrics,frames,merged,metrics,read,ref,require,save,serialized,validate_gates)
from semantic_rule import POLICY,RULE,decide

ROOT=Path('/home/inspur/aic_video_work/midnight_semantic_guard_20261015_v1')

def evaluate(registration_path,output):
    reg=read(registration_path);protocol=read(checked(reg['protocol_ref']));validate_gates(protocol)
    require(reg['status']=='REGISTERED_ONE_NEW_SEMANTIC_GUARD_DEVELOPMENT_CPU_COMPARISON' and reg['group']=='dev'
        and protocol['policy']==POLICY and protocol['rule']==RULE
        and protocol['mechanism_gates']==dict(minimum_sources_with_real_restored_native_frames_vs_unprotected_worst_all=1,
            minimum_sources_with_real_deleted_native_frames_vs_original_VERIFY=1), 'One exact fixed development rule and mechanism gate required')
    for name,digest in reg['code_files'].items():checked(dict(path=name,sha256=digest))
    manifest=read(checked(reg['source_manifest_ref']));completion=read(checked(reg['source_completion_ref']))
    inputs=read(checked(manifest['inputs_ref']))
    require(manifest['group']==inputs['group']=='dev' and len(manifest['sources'])==4
        and manifest['exposure_label']=='development_previously_exposed' and inputs['all_sources_previously_exposed'] is True
        and reg['source_manifest_ref']==protocol['source_manifest_ref'] and reg['source_completion_ref']==protocol['source_completion_ref']
        and manifest['protocol_ref']==inputs['protocol_ref']==protocol['original_relative_prompt_protocol_ref'],
        'Complete exposed development denominator required')
    checked_decisions(inputs,completion,Path(reg['source_completion_ref']['path']).parent)
    answers={}
    for row in completion['entries']:
        done=read(checked(row['decision_ref']));answers[row['case_id']]=done['parsed']
    require(len(answers)==len(inputs['entries'])==8, 'All eight actual independently accepted old answers required')
    names=[s['source_name'] for s in manifest['sources']]
    require(len(set(names))==4 and {e['source_name'] for e in inputs['entries']}<=set(names), 'Never omit any source')
    event_ids=[v['event_id'] for e in inputs['entries'] for v in e['candidate_events']]
    require(len(event_ids)==len(set(event_ids)), 'Repeated event across original cases is an engineering failure')
    prior=read(checked(protocol['original_unprotected_result_ref']))
    require(prior['group']=='dev' and prior['bindings']['manifest_ref']==reg['source_manifest_ref']
        and prior['bindings']['decisions_ref']==reg['source_completion_ref']
        and prior['bindings']['protocol_ref']==protocol['original_relative_prompt_protocol_ref'], 'Exact previously completed WORST_ALL control binding required')
    prior_cases={c['source_name']:c for c in prior['arms']['redundant']['cases']}
    cases=[];proofs=[];native_predictions=[]
    for source in manifest['sources']:
        name=source['source_name'];clock=read(checked(source['clock_ref']));points=list(map(F,clock['original_exact_pts']))
        require(points and points[0]==0 and points==sorted(set(points)) and len(points)==clock['native_frames']
            and clock['original_zero_origin_verified'] is True and clock['timeline_shift_applied'] is False,
            'Exact complete original zero-origin source clock required')
        entries=[e for e in inputs['entries'] if e['source_name']==name]
        baseline=merged([v['selected_interval_exact'] for e in entries for v in e['candidate_events']])
        require(serialized(baseline)==source['baseline_spans'], 'Original VERIFY contribution union must remain exact')
        retained=[];unprotected=[];deleted_ids=[];guarded_ids=[]
        for entry in entries:
            require(entry['source_sha256']==source['source_sha256'], 'Source bytes crossed')
            decision=decide(entry,answers[entry['case_id']],points)
            proofs.append(dict(case_id=entry['case_id'],source_name=name,**decision))
            for index,event in enumerate(entry['candidate_events']):
                if index not in decision['unprotected_worst_indices']:unprotected.append(event['selected_interval_exact'])
                if index not in decision['delete_indices']:retained.append(event['selected_interval_exact'])
                else:deleted_ids.append(event['event_id'])
            if decision['guarded']:guarded_ids.append(decision['weak_event_id'])
        candidate=merged(retained);worst_all=merged(unprotected)
        old_frames=frames(baseline,points);candidate_frames=frames(candidate,points);worst_frames=frames(worst_all,points)
        require(worst_frames<=candidate_frames<=old_frames, 'Guard can only restore original frames; never introduce new frames')
        # WORST_ALL is adopted only as an exact native set for the mechanism; its old quality is not recomputed.
        require(serialized(worst_all)==prior_cases[name]['candidate_spans'], 'Unprotected native-set control must match the original frozen result')
        reference=read(checked(source['reference_ref']));raters=reference['annotator_intervals_exact_seconds']
        require(len(raters)==reference['annotator_count']>=2, 'Every original rater required')
        average=lambda spans:{k:sum((metrics(spans,r)[k] for r in raters),F(0))/len(raters) for k in ('f1','precision','recall')}
        before=average(baseline);after=average(candidate)
        require(all(str(v)==prior_cases[name]['baseline'][k]['exact'] for k,v in before.items()), 'Baseline must equal the original complete accepted metric')
        cases.append(dict(source_name=name,source_id=source['source_id'],annotator_count=len(raters),baseline=before,candidate=after,
            baseline_spans=serialized(baseline),candidate_spans=serialized(candidate),unprotected_WORST_ALL_spans=serialized(worst_all),
            removed_native_frames=len(old_frames-candidate_frames),added_native_frames=len(candidate_frames-old_frames),
            restored_native_frames_vs_unprotected_WORST_ALL=len(candidate_frames-worst_frames),
            guarded_event_ids=guarded_ids,deleted_event_ids=deleted_ids,clock_ref=source['clock_ref'],reference_ref=source['reference_ref']))
        native_predictions.append(dict(source_name=name,source_sha256=source['source_sha256'],native_ordinals=sorted(candidate_frames)))
    macro={key:{part:dict(exact=str(value),value=float(value)) for part,value in dict(
        baseline=sum((c['baseline'][key] for c in cases),F(0))/4,candidate=sum((c['candidate'][key] for c in cases),F(0))/4,
        delta=sum((c['candidate'][key]-c['baseline'][key] for c in cases),F(0))/4).items()} for key in ('f1','precision','recall')}
    gates=dict(full_group=True,macro_F1_not_lower=F(macro['f1']['delta']['exact'])>=0,
        macro_precision_not_lower=F(macro['precision']['delta']['exact'])>=0,
        every_source_F1_loss_at_most_001=all(c['candidate']['f1']-c['baseline']['f1']>=F(-1,100) for c in cases),
        invalid_decisions_zero=True,full_original_rater_denominator=True,
        real_changed_sources=any(c['removed_native_frames']>0 for c in cases),
        no_new_native_frames=all(c['added_native_frames']==0 for c in cases),
        semantic_guard_really_restores_native_frames_vs_WORST_ALL=any(c['restored_native_frames_vs_unprotected_WORST_ALL']>0 for c in cases),
        semantic_guard_still_deletes_native_frames_vs_original_VERIFY=any(c['removed_native_frames']>0 for c in cases))
    passed=all(gates.values());policy=dict(PASS=passed,gates=gates,macro=macro,
        cases=[dict(c,baseline=exact_metrics(c['baseline']),candidate=exact_metrics(c['candidate'])) for c in cases],
        decision_proofs=proofs,prediction_native_sets=native_predictions,
        mechanism=dict(sources_with_real_restoration_vs_WORST_ALL=sum(c['restored_native_frames_vs_unprotected_WORST_ALL']>0 for c in cases),
            sources_with_real_deletion_vs_original_VERIFY=sum(c['removed_native_frames']>0 for c in cases)))
    result=dict(schema='MIDNIGHT_SEMANTIC_GUARD_COMPARISON_V1',status='SEMANTIC_GUARD_DEVELOPMENT_PASS_FROZEN_PENDING_FRESH' if passed else 'STOP_SEMANTIC_GUARD_DEVELOPMENT_REJECTED',
        group='dev',policies={POLICY:policy},passed_policies={POLICY:passed},passed_arms={POLICY:passed},selected_policies=[POLICY] if passed else [],
        full_source_count=4,bindings=dict(protocol_ref=reg['protocol_ref'],registration_ref=ref(registration_path),manifest_ref=reg['source_manifest_ref'],
            decisions_ref=reg['source_completion_ref'],prior_unprotected_result_ref=protocol['original_unprotected_result_ref'],prior_pair_failure_ref=protocol['prior_pair_failure_ref']),
        all_sources_previously_exposed=True,model_answers_modified=False,source_model_answers_modified=False,new_model_calls=0,new_processor_calls=0,new_media_decodes=0,old_QA_repeated=0,
        old_WORST_ALL_quality_comparison_repeated=False,old_scientific_failures_changed=False,official_improvement='UNKNOWN',production_admitted=False)
    save(output,result)
    if passed:
        save(output.with_name('development_selection.json'),dict(schema='MIDNIGHT_SEMANTIC_GUARD_DEV_SELECTION_V1',policy=POLICY,
            selected_policies=[POLICY],passed_arms={POLICY:True},result_ref=ref(output),protocol_ref=reg['protocol_ref'],confirm_metrics_examined=False,
            source_selection_or_acquisition_yet_performed=False,production_admitted=False))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--registration',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    require(sys.platform=='linux' and a.registration.resolve()==ROOT/'development_registration.json'
        and a.output.resolve()==ROOT/'dev_01/comparison.json', 'Exact independent registered Linux development output required')
    launch=read(ROOT/'dev_01/launch.json')
    require(launch['registration_ref']==ref(a.registration) and launch['pid']!=os.getpid()
        and launch['CPU_only'] is True and launch['automatic_retry'] is False and os.environ.get('CUDA_VISIBLE_DEVICES')=='',
        'First explicitly authorized separate CPU comparison process required')
    result=evaluate(a.registration,a.output);print(dict(status=result['status'],passed=result['passed_policies']))
    sys.exit(0 if result['passed_policies'][POLICY] else 5)
