"""Complete accepted global projection for package_family; never infers or repairs."""
import argparse
from fractions import Fraction as F
import json
import os
from pathlib import Path

import pc_contract as c
import pc_io as io


def absolute(store,ref):
    path=store.checked_ref(ref)
    return dict(path=str(path),sha256=ref['sha256'])


def exact_clock(source,clock,original):
    original=original.get('arrays',original);tick=F(original['raw_time_base'])
    raw=[F(value)*tick for value in original['native_pts_ticks']];origin=F(original['raw_first_pts_ticks'])*tick
    ends=original['native_frame_end_pts_ticks']
    if isinstance(ends,list):
        c.require(len(ends)==len(raw),'Original native end-tick denominator differs');end=F(ends[-1])*tick-origin
    else:
        c.require(ends is None and source['old_clock']['old_terminal_evidence']['kind']=='LEGACY_CFR_N_DIV_FPS',
            'Unknown null original terminal is not a lawful legacy planning branch')
        end=F(source['old_clock']['n_frames']*source['fps_den'],source['fps_num'])
        c.require(end==F(source['old_clock']['planned_physical_end_exact']),'Legacy n/fps exact planning witness changed')
    witness=clock['physical_endpoint_evidence']
    c.require(raw and raw[0]==origin and len(raw)==source['old_clock']['n_frames']==clock['n_frames'] and
        list(map(F,clock['original_exact_pts']))==raw and list(map(F,clock['normalized_exact_pts']))==[p-origin for p in raw] and
        F(clock['first_original_pts_exact'])==origin and F(clock['physical_end_exact'])==end and
        witness['kind']=='LAST_NATIVE_FRAME_PTS_PLUS_POSITIVE_DURATION' and F(witness['last_frame_duration_exact'])>0 and
        F(witness['last_normalized_pts_exact'])==raw[-1]-origin and
        F(witness['last_normalized_pts_exact'])+F(witness['last_frame_duration_exact'])==end and
        clock['source_sha256']==source['source_sha256'] and clock['source_path']==source['source_path'] and
        clock['measured_geometry']==[source['width'],source['height']],
        'Independent complete new/original raw PTS/origin/positive terminal/source/geometry binding failed')
    return True


def aggregate(registration_path):
    io.host();ctx=io.load(registration_path);store=ctx['store'];plan=ctx['plan']
    from pr_contract import batch_membership,source_video_projection
    coverage=c.full_coverage(plan,ctx['batches'],batch_membership);projection=source_video_projection(plan)
    endpoints={};verification={};clocks={};events=[];accepted=[];batch_terminals=[];source_bindings={};witnesses={}
    out=io.BASE/'exports_01';out.mkdir(exist_ok=False)
    # Every consumer must be accepted exactly once and every declared new RGB released exactly once.
    lifecycle=io.rows(store.base/'permanent/lifecycle.jsonl')
    accepted_rows=[row for row in lifecycle if row['event']=='CONSUMER_ACCEPTED']
    released=[row for row in lifecycle if row['event']=='RGB_RELEASED']
    c.require(len(accepted_rows)==len(plan['consumers']) and {row['consumer'] for row in accepted_rows}==set(plan['consumers']) and
        len({row['consumer'] for row in accepted_rows})==len(accepted_rows),'Missing/repeated actual first consumer acceptance')
    c.require(len(released)==len(plan['RGB_groups']) and {row['lease_id'] for row in released}==set(plan['RGB_groups']) and
        all(row['RGB_present'] is False and row['canonical_files_retained'] is True and row['old_success_files_deleted']==0 for row in released),
        'Missing/repeated/unsafe actual new-RGB lease closure')
    expected_operations={('SOURCE_PREPARE',source['source_id']) for source in plan['sources']}
    for batch in ctx['batches']:
        bid=batch['batch_id']
        if batch.get('cpu_only_empty_batch') is True:
            empty=io.read(io.BASE/'run_01'/('empty_'+bid+'.json'))
            c.require(empty['status']=='PASS_CPU_ONLY_EMPTY_SOURCE_BLOCK_NO_GPU_JOB' and empty['actual_model_calls']==0 and
                empty['source_ids']==batch['source_ids'],'Complete empty-source coverage receipt missing')
            continue
        expected_operations|={(phase,bid) for phase in ('BATCH_INPUT_ADMIT','GPU_WRAPPER','TERMINAL_CAPTURE','OUTPUT_REPLAY','LEASE_CLOSE')}
        expected_operations|={('FIRST_INPUT_REPLAY',rid) for rid in batch['request_ids']}
        root=io.RUNTIME/'runs'/bid
        closure_ref=io.read(root/'closure_pointer.json')['completion_ref'];closure=io.read(store.checked_ref(closure_ref))
        c.require(closure['status']=='PASS_BATCH_CONSUMER_CLOSURE_NEW_RGB_RELEASE_NOT_QUALITY' and closure['batch_id']==bid and
            closure['accepted_consumers']==batch['request_ids'] and closure['global_graph_sha256']==ctx['reg']['global_graph_sha256'] and
            closure['batch_sha256']==io.sha(io.RUNTIME/'batches'/(bid+'.json')) and closure['old_success_files_deleted']==0,
            'Batch actual complete close proof differs')
        replay=io.read(store.checked_ref(closure['output_replay_completion_ref']))
        resource=io.read(store.checked_ref(closure['resource_ref']))
        ledger=io.rows(store.checked_ref(closure['ledger_ref']))
        c.require(resource['name']==batch['gpu_job_name'] and resource['status']=='completed' and type(resource['exit_code'])is int and resource['exit_code']==0 and
            [row for row in ledger if row.get('name')==resource['name']]==[resource], 'Unique independent natural terminal/immutable ledger binding failed')
        batch_terminals.append(dict(batch_id=bid,gpu_job_name=batch['gpu_job_name'],resource_ref=absolute(store,closure['resource_ref']),
            ledger_ref=absolute(store,closure['ledger_ref']),closure_ref=absolute(store,closure_ref)))
        c.require([row['consumer'] for row in replay['proofs']]==batch['request_ids'],'Actual output QA missing/repeated consumer')
        for row in replay['proofs']:
            proof=io.read(store.checked_ref(row['proof_ref']))
            c.require(proof['status']=='PASS_FIRST_INDEPENDENT_REPLAY' and proof['consumer']==row['consumer'] and
                proof['output_token_decode_grammar_parser_native_verified'] is True and proof['actual_weight_identity_verified'] is True and
                proof['normal_processor_from_original_RGB_verified'] is True and proof['gpu_job_name']==batch['gpu_job_name'],
                'Real input/output/GPU/weights first independent acceptance proof incomplete')
            acceptance=next(item for item in accepted_rows if item['consumer']==row['consumer'])
            c.require(acceptance['proof_ref']==row['proof_ref'] and acceptance['resource_ref']==closure['resource_ref'] and
                acceptance['ledger_ref']==closure['ledger_ref'],'Actual critic consumer acceptance belongs to different proof/terminal')
            manifest=io.read(store.checked_ref(proof['input_manifest_ref']))
            for ref in (manifest['private_ref'],manifest['visual_ref']):
                if ref:store.checked_ref(ref) # Immutable bytes; do not repeat normal processor or full tensor replay.
            for ref in proof['retained_evidence_refs'].values():store.checked_ref(ref)
            accepted.append(dict(consumer=row['consumer'],first_independent_replay_ref=absolute(store,row['proof_ref']),
                resource_ref=absolute(store,closure['resource_ref']),ledger_ref=absolute(store,closure['ledger_ref'])))
        for row in replay['outputs']:
            rid=row['consumer'];output=row['output'];sid=row['source_id']
            c.require(row['video_id']==projection[sid] and sid in batch['source_ids'],'Output source hash/video projection differs')
            if row['kind']=='ENDPOINT':
                c.require(rid not in endpoints and output['request_id']==rid,'Duplicate or reassigned endpoint ID');endpoints[rid]=output
            else:
                eid=output['event_id'];c.require(eid not in verification and rid==eid+'.verify','Duplicate or reassigned VERIFY ID');verification[eid]=output
    # GLOBAL_AGGREGATE is currently BEGIN and is recorded COMPLETE after this program exits0.
    journal=io.rows(io.BASE/'run_01/journal.jsonl')
    c.validate_stage_journal([row for row in journal if row['phase']!='GLOBAL_AGGREGATE'],expected_operations)
    for source in plan['sources']:
        sid=source['source_id'];vid=str(projection[sid])
        complete_ref=store.ref('permanent/proofs/source_'+sid+'_completion.json');complete=io.read(store.checked_ref(complete_ref))
        clock_ref=complete['new_clock_ref'];clock=io.read(store.checked_ref(clock_ref))['clock']
        original_ref=source['original_clock_ref'];original=io.read(io.bound(original_ref,(io.RUN,)))
        exact_clock(source,clock,original)
        equality_ref=store.write_metadata('permanent/proofs/control_v1/native_equality_'+sid+'.json',dict(
            status='PASS_INDEPENDENT_FULL_NATIVE_PTS_ORIGIN_POSITIVE_TERMINAL_EQUALITY',source_id=sid,video_id=vid,
            original_clock_ref=original_ref,new_clock_ref=clock_ref,source_completion_ref=complete_ref,
            verifier_code_sha256=io.sha(__file__),no_epsilon_clip_or_CFR_substitution=True,new_model_calls=0,new_media_decodes=0))
        clocks[vid]=dict(clock,video_id=vid,native_input_source_id=sid)
        witnesses[vid]=clock['physical_endpoint_evidence']
        source_bindings[vid]=dict(original_clock_ref=original_ref,new_clock_ref=absolute(store,clock_ref),
            source_CPU_completion_ref=absolute(store,complete_ref),independent_equality_ref=absolute(store,equality_ref))
        for window in source['windows']:
            for event in window['events']:
                events.append(dict(event,source_id=vid,native_input_source_id=sid,physical_end_exact=clock['physical_end_exact']))
    wanted_endpoints={event['event_id']+'.'+side for event in events for side in ('start','end')}
    c.require(len(events)==665 and len(clocks)==426 and set(clocks)=={str(i) for i in range(426)} and
        len(endpoints)==1330 and set(endpoints)==wanted_endpoints and len(verification)==665 and set(verification)=={e['event_id'] for e in events} and
        len(accepted)==len(plan['consumers']) and {row['consumer'] for row in accepted}==set(plan['consumers']),
        'Strict full426/665/1330/actual-MODEL complete global denominator failed')
    export_refs={}
    for name,value in [('events',events),('endpoints',endpoints),('verification',verification),('source_clocks',clocks)]:
        path=out/(name+'.json');io.save(path,value);export_refs[name]=dict(path=str(path),sha256=io.sha(path))
    selection=ctx['context']['protocol']['selected_uniform_development_role_ref']
    selected=io.read(selection['path'])
    role=ctx['context']['protocol']['endpoint_model_role']
    c.require(selected['global_refiner_role']==role and selected['global_VERIFY_role']=='TIME_ENABLED','Actual frozen selection role differs')
    io.save(out/'global_completion.json',dict(status='PASS_COMPLETE_ALL_PROSPECTIVE_TEMPORAL_REQUESTS_AND_FIRST_INDEPENDENT_REPLAYS',
        accepted_export_refs=export_refs,frozen_development_selection_ref=selection,global_refiner_role=role,global_VERIFY_role='TIME_ENABLED',
        engineering_failed_requests=0,missing_requests=0,physical_model_parameters=8782459120,optimizer_updates=0,
        test_GT_or_annotation_read=False,native_clock_matches_original_full_PTS=True,
        accepted_endpoint_request_ids=list(endpoints),accepted_verification_event_ids=list(verification),actual_source_ids=list(clocks),
        actual_unique_MODEL_ids=[row['consumer'] for row in accepted],actual_unique_MODEL_proofs=accepted,
        native_clock_terminal_witnesses=witnesses,native_clock_original_bindings=source_bindings,
        batch_natural_terminals=batch_terminals,source_id_to_video_id=projection,global_graph_sha256=ctx['reg']['global_graph_sha256'],
        scientific_quality_claim=False,old_scientific_failed_gates_changed=False,five_ZIPs_claimed=False,
        actual_new_calls_in_aggregate=0,all_canonical_inputs_raw_and_proofs_retained=True,all_only_new_RGB_leases_closed=True,
        controller_launch_claim_sha256=io.sha(io.BASE/'run_01/launch_claim.json'),stage_journal_sha256_at_aggregate=io.sha(io.BASE/'run_01/journal.jsonl')))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--registration',required=True,type=Path);args=parser.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES']='';aggregate(args.registration)
