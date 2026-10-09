"""Independent full source/response/ZIP/ledger closure, no GPU generation."""
import subprocess
import statistics
import zipfile
import bw_common as c

def main():
    c.verify();rt,ex,cc,student,old,frames,production=c.helpers()
    proofs={}
    for scope in ('developer','rematch'):
        replay=c.read(c.HERE/(scope+'_01/replay_acceptance.json'));plan,jobs=c.jobs_for(scope)
        expected=c.read(c.HERE/'prepared.json')['counts'][scope]['changed']
        c.require(replay['status']=='PASS_ALL_BALANCED_NEW_REQUESTS_CPU_REPLAY' and len(replay['proofs'])==expected,'complete independent replay')
        accepted={p['path']:p for p in replay['proofs']}
        for job in jobs:
            for ix,part in enumerate(job['windows']):
                p=c.done_path(scope,job,ix,'BW',cc);v=c.checked(p,job,ix,'BW',ex)
                if c.is_changed(part):c.require(str(p) in accepted and c.sha(p)==accepted[str(p)]['done_sha256'],'accepted done bytes changed')
        proofs.update(accepted)
    c.require(c.read(c.HERE/'developer_01/report.json')['status']=='PASS_ENGINEERING_USER_ACCEPTED_RISK_CONTINUE_426','user risk recipe engineering not complete')
    reports={}
    for scope,count,windows in (('nontest',8,8),('rematch',426,521)):
        out=c.HERE/(scope+'_01');plan=c.read(c.HERE/'input_01'/(scope+'_plan.json'))
        ref,manifest,clocks=old.inputs(scope);temporal=old.rows(out/'temporal.jsonl')
        c.require(len(temporal)==len(plan['jobs'])==count and {x['video_id'] for x in temporal}=={x['video_id'] for x in manifest['records']} and
            sum(len(x['windows']) for x in temporal)==windows,'complete final scope identity')
        for job in plan['jobs']:
            record=next(x for x in temporal if x['video_id']==job['video_id'])
            for ix,part in enumerate(job['windows']):
                value=c.checked(c.done_path(scope,job,ix,'BW',cc),job,ix,'BW',ex)
                c.require(value['parsed_segments']==record['windows'][ix]['parsed_segments'] and value['model_identity']==
                    c.read(c.HERE/'input_01/resume_manifest.json')['model_identity'],'final raw response/model identity')
        # An independent normalized full-clock replay of every raw interval.
        from fractions import Fraction as F
        from bisect import bisect_left
        expected_keys=set()
        for job in plan['jobs']:
            clock=clocks[job['video_id']];a=clock['arrays'];tick=F(a['raw_time_base']);origin=a['raw_first_pts_ticks']*tick
            exact=[p*tick-origin for p in a['native_pts_ticks']];floats=[float(x) for x in exact]
            for ix,part in enumerate(job['windows']):
                v=c.checked(c.done_path(scope,job,ix,'BW',cc),job,ix,'BW',ex)
                for left,right in v['parsed_segments']:
                    if c.is_changed(part):
                        start=F(part['window']['exact_normalized_start']);lo,hi=start+F(str(left)),start+F(str(right))
                        first,stop=bisect_left(exact,lo),bisect_left(exact,hi)
                    else:
                        start=F(str(part['start_sec']));first=bisect_left(floats,float(start+F(str(left))));stop=bisect_left(floats,float(start+F(str(right))))
                    c.require(first<stop,'independent full-clock interval has no frame')
                    expected_keys.update((job['video_id'],i) for i in range(first,stop))
        selected=old.rows(out/'selected.jsonl')
        c.require(len(selected)==len(expected_keys) and {(r['video_id'],r['source_frame']) for r in selected}==expected_keys,
            'independent new-domain selected key set differs')
        candidate=out/'candidate_BALANCED_TWO_WINDOW_8B.zip';independent=out/'final_independent_validation.json'
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
    new_keys={(r['video_id'],r['source_frame']) for r in old.rows(c.HERE/'rematch_01/selected.jsonl')}
    old_keys={(r['video_id'],r['source_frame']) for r in old.rows(c.RUN/'teacher_student_autopilot_v14/rematch_01/selected.jsonl')}
    output_effect=dict(new_selected_frames=len(new_keys),original_V14_selected_frames=len(old_keys),
        added_keys=len(new_keys-old_keys),removed_keys=len(old_keys-new_keys),selected_key_set_changed=new_keys!=old_keys,
        identity_audit_not_quality_metric=True)
    ledger=old.rows('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl');resources={}
    for name in ('developer','rematch'):
        runname='aic_BW_risk_v3_'+name;p=c.RUN/'controller'/(runname+'.resource.json');v=c.read(p)
        c.require([r for r in ledger if r.get('name')==runname]==[v] and v['status']=='completed' and
            v['exit_code']==0 and v['stop_reason'] is None and v['charged_seconds']>0,'new GPU unique terminal receipt')
        resources[name]={'path':str(p),'sha256':c.sha(p),'charged_seconds':v['charged_seconds']}
    prior=c.read(c.HERE/'engineering_handoff.json')['prior_failed_resource']
    prior_value=c.read(prior['path'])
    c.require(c.sha(prior['path'])==prior['sha256'] and [r for r in ledger if r.get('name')==prior_value['name']]==[prior_value] and prior_value['charged_seconds']>0 and prior_value['status']=='failed' and prior_value['exit_code']==1 and prior_value['stop_reason'] is None,'previous failed GPU actual accounting changed')
    origin=c.read(c.HERE/'accounting_origin.json')
    ledger_bytes=__import__('pathlib').Path('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl').read_bytes().splitlines(keepends=True)
    c.require(__import__('hashlib').sha256(b''.join(ledger_bytes[:origin['lines']])).hexdigest()==origin['prefix_sha256'],'historical append ledger bytes changed')
    original_v14={}
    for name in ('student_train','nontest_temporal','rematch_temporal'):
        p=c.RUN/'controller'/('rematch_TAUTO_v14_'+name+'.resource.json');v=c.read(p)
        c.require([r for r in ledger if r.get('name')==v['name']]==[v] and v['status']=='completed' and
            v['exit_code']==0 and v['stop_reason'] is None and v['charged_seconds']>0,'original V14 accounting differs')
        original_v14[name]={'path':str(p),'sha256':c.sha(p),'charged_seconds':v['charged_seconds']}
    c.save(c.HERE/'final_acceptance.json',{'status':'PASS_INDEPENDENT_BALANCED_TWO_WINDOW_RISK_FINAL',
        'utc':c.utc(),'candidate':reports['rematch']['candidate'],'zip_bytes':reports['rematch']['zip_bytes'],
        'zip_sha256':reports['rematch']['zip_sha256'],'reports':reports,'resource_receipts':resources,
        'original_costs_preserved':{'spatial_and_V14_original_terminal_costs_preserved':True},
        'fresh_temporal_calls':132,'new_calls_in_this_engineering_version':131,'exact_recovered_prior_calls':1,'prior_failed_resource':prior,'exact_old_temporal_calls':{'developer':96,'nontest':8,'rematch':405},
        'original_V14_costs_preserved':original_v14,
        'ledger_historical_offset':7200,'new_cpu_model_calls':0,'new_optimizer_updates':0,'new_32B_calls':0,
        'new_overview_calls':0,'new_spatial_calls':0,'production_weight':'ORIGINAL_B_8B',
        'balanced_two_windows_exact_midpoint':True,'no_native_PTS_rounding':True,
        'new_training':False,'original_B0_prompt_allow_empty':True,'official_score':None,
        'output_effect_vs_V14':output_effect,'original_space_gpu_seconds_preserved':18723.876,
        'user_explicitly_accepted_experiment_risk':True,'independent_quality_reference':'UNKNOWN','developer_replay_done_SHA_count':len(proofs),
        'not_guaranteed_to_exceed_37_63':True,'source_lock_sha256':c.sha(c.HERE/'source_lock.json')})

if __name__=='__main__':main()
