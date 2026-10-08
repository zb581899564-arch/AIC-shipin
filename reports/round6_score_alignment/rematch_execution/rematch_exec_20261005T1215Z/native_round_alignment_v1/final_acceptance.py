"""Independent full source/response/ZIP/ledger closure, no GPU generation."""
import subprocess
import statistics
import zipfile
import nr_common as c

def main():
    c.verify();rt,ex,cc,student,old,frames,production=c.helpers()
    # Independently reconstruct the gate from all actual developer raw answers.
    # This repeats aggregate arithmetic only, never accepted decoder/model work.
    plan=c.read(c.HERE/'input_01/developer_plan.json');rows=[];proofs={}
    replay=c.read(c.HERE/'developer_01/replay_acceptance.json')
    fresh=c.read(c.HERE/'input_01/resume_manifest.json')['changed_windows']['developer']
    c.require(replay['status']=='PASS_ALL_SCOPE_NATIVE_ROUND_ALIGNMENT_NATIVE_CPU_REPLAY' and len(replay['proofs'])==fresh and
        replay['exact_original_success_reused']==112-fresh,'full developer CPU receipt')
    for proof in replay['proofs']:
        c.require(proof['actual_native_processor_raw_validator_equal'] and proof['new_model_calls']==0,'unaccepted developer replay')
        proofs[proof['path']]=proof
    for job in plan['developer_jobs']:
        arms={}
        for arm in ('Q','B0'):
            intervals=[];ids=set()
            for ix,part in enumerate(job['windows']):
                if arm=='Q':
                    path=c.done_path('developer',job,ix,'Q',cc);v=c.checked(path,job,ix,'Q',ex)
                    if part['window']!=part['base_window']:
                        c.require(str(path) in proofs and c.sha(path)==proofs[str(path)]['done_sha256'],'accepted developer done bytes changed')
                    else:c.require('/context_advisory_v1/' in str(path),'unchanged request must reuse original success')
                else:v=c.checked_base('developer',job,ix)
                base=part['window']['planned_source_frame_ordinals'][0]
                for a,b in v['native_frame_realizability']['ranges']:ids.update(range(base+a,base+b))
                offset=part['start_sec']-job.get('clip_start_sec',0)
                intervals.extend([[offset+a,offset+b] for a,b in v['parsed_segments']])
            arms[arm]=dict(native_source_ordinals=sorted(ids),segments=intervals,legal_empty=not intervals,
                closed_world_output_agreement=cc.weak_metrics(intervals,job['weak_reference']))
        rows.append(dict(video_id=job['video_id'],source_group=job['source_group'],arms=arms))
    c.require(rows==c.read(c.HERE/'developer_01/matched_rows.json'),'full developer gate rows differ from raw')
    pilot=set(plan['pilot_source_groups']);expanded=[r for r in rows if r['source_group'] not in pilot]
    c.require(len(rows)==104 and len(proofs)==fresh and len(expanded)==80 and len({r['source_group'] for r in expanded})==72,'final gate denominators')
    delta=lambda r:r['arms']['Q']['closed_world_output_agreement']['f1']-r['arms']['B0']['closed_world_output_agreement']['f1']
    groups={r['source_group'] for r in rows}
    changed=sum(r['arms']['Q']['native_source_ordinals']!=r['arms']['B0']['native_source_ordinals'] for r in rows)
    down=sum(statistics.mean(delta(r) for r in rows if r['source_group']==g)<0 for g in groups)
    from nr_report import gate
    original=rt.load(c.CAD/'report.py','nr_final_bootstrap_only')
    all_metric=original.bootstrap_video_macro([delta(r) for r in rows],rows)
    expanded_metric=original.bootstrap_video_macro([delta(r) for r in expanded],expanded)
    registered=c.read(c.HERE/'developer_01/report.json')
    c.require(registered['all104_Q_minus_B0']==all_metric and registered['expanded72_Q_minus_B0']==expanded_metric and
        registered['changed_native_sets']==changed and registered['groups_down']==down,'actual gate arithmetic or group bootstrap differs')
    c.require(len(groups)==96 and gate(all_metric['mean'],expanded_metric['mean'],changed,down/96),'independent fixed investment gate rejected')
    c.require(registered['status']=='GO_ONE_NATIVE_ROUND_ALIGNMENT_RISK_PACKAGE','actual controller gate missing')
    reports={}
    for scope,count,windows in (('nontest',8,8),('rematch',426,521)):
        out=c.HERE/(scope+'_01');plan=c.read(c.HERE/'input_01'/(scope+'_plan.json'))
        ref,manifest,clocks=old.inputs(scope);temporal=old.rows(out/'temporal.jsonl')
        c.require(len(temporal)==len(plan['jobs'])==count and {x['video_id'] for x in temporal}=={x['video_id'] for x in manifest['records']} and
            sum(len(x['windows']) for x in temporal)==windows,'complete final scope identity')
        for job in plan['jobs']:
            record=next(x for x in temporal if x['video_id']==job['video_id'])
            for ix,part in enumerate(job['windows']):
                value=c.checked(c.done_path(scope,job,ix,'Q',cc),job,ix,'Q',ex)
                c.require(value['parsed_segments']==record['windows'][ix]['parsed_segments'] and value['model_identity']==
                    c.read(c.HERE/'input_01/resume_manifest.json')['model_identity'],'final raw response/model identity')
        candidate=out/'candidate_NATIVE_ROUND_ALIGNMENT_8B.zip';independent=out/'final_independent_validation.json'
        subprocess.run([c.PY,'-B',str(c.RUN/'baseline_a_pts_v1/vendor/independent_validate.py'),
            '--strict-loader-root',str(c.RUN/'baseline_a_pts_v1/vendor/frozen_strict_loader'),
            '--metadata',str(out/'metadata.json'),'--selected',str(out/'selected.jsonl'),
            '--predictions',str(out/'predictions.jsonl'),'--provenance',str(out/'provenance.jsonl'),
            '--zip',str(candidate),'--report',str(independent)],check=True)
        accepted=c.read(independent);production.check_independent(accepted,scope,len(old.rows(out/'selected.jsonl')))
        c.require(accepted['zip_sha256']==c.sha(candidate) and accepted['predictions_sha256']==c.sha(out/'predictions.jsonl'),'actual final bytes differ')
        with zipfile.ZipFile(candidate) as z:
            c.require(z.namelist()==['predictions.jsonl'] and z.testzip() is None and z.read('predictions.jsonl')==(out/'predictions.jsonl').read_bytes(),'actual ZIP CRC/unique JSONL/original bytes')
        space=c.read(out/'spatial.stage.json')
        c.require(space['status']=='PASS_EMPTY_SPACE_NO_MODEL_CALL' or space.get('reused_cache') is True,'unregistered fresh spatial inference')
        reports[scope]={'records':count,'windows':windows,'all_11_checks':accepted['checks'],
            'actual_generation':c.read(out/(scope+'.completion.json')),
            'independent_report_sha256':c.sha(independent),'candidate':str(candidate),'zip_bytes':candidate.stat().st_size,'zip_sha256':c.sha(candidate)}
    ledger=old.rows('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl');resources={}
    for name in ('nontest','developer','rematch'):
        runname='aic_NRA_v1_'+name;p=c.RUN/'controller'/(runname+'.resource.json');v=c.read(p)
        c.require([r for r in ledger if r.get('name')==runname]==[v] and v['status']=='completed' and
            v['exit_code']==0 and v['stop_reason'] is None and v['charged_seconds']>0,'new GPU unique terminal receipt')
        resources[name]={'path':str(p),'sha256':c.sha(p),'charged_seconds':v['charged_seconds']}
    original_v14={}
    for name in ('student_train','nontest_temporal','rematch_temporal'):
        p=c.RUN/'controller'/('rematch_TAUTO_v14_'+name+'.resource.json');v=c.read(p)
        c.require([r for r in ledger if r.get('name')==v['name']]==[v] and v['status']=='completed' and
            v['exit_code']==0 and v['stop_reason'] is None and v['charged_seconds']>0,'original V14 accounting differs')
        original_v14[name]={'path':str(p),'sha256':c.sha(p),'charged_seconds':v['charged_seconds']}
    c.save(c.HERE/'final_acceptance.json',{'status':'PASS_INDEPENDENT_NATIVE_ROUND_ALIGNMENT_FINAL',
        'utc':c.utc(),'candidate':reports['rematch']['candidate'],'zip_bytes':reports['rematch']['zip_bytes'],
        'zip_sha256':reports['rematch']['zip_sha256'],'reports':reports,'resource_receipts':resources,
        'original_costs_preserved':c.read(c.HERE/'input_01/resume_manifest.json')['resources'],
        'original_V14_costs_preserved':original_v14,
        'ledger_historical_offset':7200,'new_cpu_model_calls':0,'new_optimizer_updates':0,'new_32B_calls':0,
        'new_overview_calls':0,'new_spatial_calls':0,'production_weight':'ORIGINAL_B_8B',
        'native_nearest64_same_count_grid_endpoints':True,'no_native_PTS_rounding':True,
        'new_training':False,'original_B0_prompt_allow_empty':True,'official_score':None,
        'independent_gate_reconstructed_from_all104_raw':True,'developer_replay_done_SHA_count':len(proofs),
        'not_guaranteed_to_exceed_37_63':True,'source_lock_sha256':c.sha(c.HERE/'source_lock.json')})

if __name__=='__main__':main()
