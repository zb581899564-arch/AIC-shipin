"""All matched contexts, independent weak direction, and real terminal accounting."""
import statistics
import bdiag_common as c
import bdiag_engine as engine


def main():
    c.verify()
    cad,ex,student,old,teacher,boundary=c.helpers()
    plan=c.read(c.HERE/'input_01/plan.json')
    rows=[];cpu_proofs=[]
    for i,seed in enumerate(plan['events']):
        values=[]
        for variant in seed['variants']:
            out=c.HERE/'run_01/events'/seed['event_key']/variant['name']
            done=c.read(out/'done.json')
            for p,wanted in done['bound_files'].items():c.require(c.sha(p)==wanted,'original diagnostic raw changed')
            if i!=0:cpu_proofs.append(engine.check_done(out,seed,variant,student,teacher,boundary))
            values.append({'variant':variant['name'],**done['matched_projection']})
        matched=[v['candidate_boundary_seconds'] for v in values if v['candidate_boundary_seconds'] is not None]
        complete=len(matched)==len(values)
        ref=seed['weak_direction_reference']
        delta=[c.iou(v,ref)-c.iou(seed['raw_source_event_seconds'],ref) for v in matched] if complete and ref else None
        gap=statistics.median([b-a for a,b in zip(seed['original_window']['planned_actual_pts_sec'],seed['original_window']['planned_actual_pts_sec'][1:])])
        spread=[max(v[k] for v in matched)-min(v[k] for v in matched) for k in (0,1)] if complete else None
        rows.append({'event_key':seed['event_key'],'source_group':seed['source_group'],'contexts':values,
            'all_contexts_unique_temporal_overlap':complete,'same_event_identity':'UNKNOWN_NOT_HUMAN_VERIFIED',
            'endpoint_spread_seconds':spread,'original_median_sample_gap_seconds':gap,
            'spread_within_original_sample_gap':bool(complete and max(spread)<=gap),
            'independent_weak_reference_status':seed['weak_reference_status'],
            'independent_weak_reference_coverage':'UNKNOWN','per_context_external_weak_IoU_delta_vs_B':delta,
            'candidate_outside_unknown_not_negative':True})
    resource=c.read(c.RUN/'controller/aic_BBOUND_v1_diagnostic.resource.json')
    ledger=old.rows('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl')
    c.require([r for r in ledger if r.get('name')=='aic_BBOUND_v1_diagnostic']==[resource]
        and resource['status']=='completed' and resource['exit_code']==0 and resource['stop_reason'] is None
        and resource['charged_seconds']>0,'actual new32B unique GPU terminal ledger')
    deltas=[statistics.mean(r['per_context_external_weak_IoU_delta_vs_B']) for r in rows if r['per_context_external_weak_IoU_delta_vs_B'] is not None]
    c.save(c.HERE/'matched_rows.json',rows)
    c.save(c.HERE/'diagnostic_completion.json',{'status':'PASS_REAL_MATCHED_32B_BOUNDARY_DIAGNOSTIC_AND_CPU_ACCOUNTING',
        'utc':c.utc(),'events':16,'context_attempts':plan['variant_denominator'],'engineering_failures':0,
        'all_contexts_unique_temporal_overlap_events':sum(r['all_contexts_unique_temporal_overlap'] for r in rows),
        'spread_within_original_sample_gap_events':sum(r['spread_within_original_sample_gap'] for r in rows),
        'independent_weak_direction_events':len(deltas),'external_weak_event_macro_delta':statistics.mean(deltas) if deltas else None,
        'reference_coverage_and_semantic_truth':'UNKNOWN','stability_is_not_boundary_truth':True,
        'training_admitted':False,'new_optimizer_updates':0,'new_8B_calls':0,
        'actual_new_32B_calls':plan['variant_denominator'],'actual_GPU_charge_seconds':resource['charged_seconds'],
        'new_CPU_acceptance_model_calls':0,'other_context_CPU_proofs':cpu_proofs,
        'first_context_CPU_proof_sha256':c.sha(c.HERE/'first_real_acceptance.json'),
        'ledger_unique_terminal_match':True,'ledger_historical_offset':7200,
        'next':'AGENT_DECIDE_CONCRETE_BOUNDARY_REFINEMENT_FROM_MATCHED_AND_INDEPENDENT_DIRECTION_EVIDENCE',
        'no_final_426_ZIP':True,'no_user_confirmation_required':True})
    c.progress('BOUNDARY_DIAGNOSTIC_COMPLETE_AGENT_CONTINUES_FROM_EVIDENCE',events=16,
        actual_new_32B_calls=plan['variant_denominator'],training_admitted=False)


if __name__=='__main__':main()
