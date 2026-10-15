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


def exact_clock(source,clock,original,packet_source,terminal):
    """Independent full-clock identity + actual decoder-duration/packet equality.

    The old end is audited, never used as the new physical endpoint or rewritten.
    A terminal-equality-only old FAIL remains an old FAIL in this new reader scope.
    """
    original=original.get('arrays',original);tick=F(original['raw_time_base'])
    raw=[F(value)*tick for value in original['native_pts_ticks']];origin=F(original['raw_first_pts_ticks'])*tick
    c.require(raw and tick>0 and all(type(value)is int for value in original['native_pts_ticks']) and
        all(a<b for a,b in zip(raw,raw[1:])), 'Original complete integer PTS identity invalid')
    obs=terminal['observations'];video=obs['video_stream'];matches=obs['matching_packets']
    c.require(len(matches)==1,'Exactly one matching terminal packet required')
    packet=matches[0];duration=F(packet['duration_seconds_exact']);end=raw[-1]-origin+duration
    c.require(packet_source['source_sha256']==obs['actual_source_sha256']==source['source_sha256'] and
        packet_source['source_path']==source['source_path'] and
        packet_source['source_stat']['bytes']==obs['source_SHA_read_bytes']==source['source_bytes'] and
        packet_source['n_frames']==source['old_clock']['n_frames'] and
        packet_source['clock_array_ref']==source['original_clock_ref'] and
        [packet_source['width'],packet_source['height']]==[video['width'],video['height']]==[source['width'],source['height']],
        'Packet registration/observation/source/old-clock identity differs')
    c.require(F(packet_source['original_raw_first_frame_pts_exact'])==origin and
        F(packet_source['original_raw_last_frame_pts_exact'])==raw[-1] and
        F(packet['raw_display_pts_exact'])==F(obs['max_display_packet_pts_exact'])==raw[-1] and
        type(packet['pts'])is int and F(packet['pts'])*F(packet['time_base_exact'])==raw[-1] and
        type(packet['duration'])is int and packet['duration']>0 and duration>0 and
        F(packet['duration'])*F(packet['time_base_exact'])==duration and
        type(packet['size'])is int and packet['size']>0 and packet['stream_index']==video['index'] and
        isinstance(packet['compressed_packet_sha256'],str) and len(packet['compressed_packet_sha256'])==64 and
        obs['AV_open_calls']==obs['demux_calls']==1 and obs['actual_frame_decode_calls']==0 and obs['PyAV_version']=='17.1.0',
        'Unique max-display packet/positive actual duration/reader evidence differs')
    status=terminal['status'];ends=original['native_frame_end_pts_ticks']
    if isinstance(ends,list):
        c.require(len(ends)==len(raw) and type(ends[-1])is int,'Old explicit end array identity invalid')
        legacy_end=F(ends[-1])*tick-origin;kind='OLD_EXPLICIT_END_TICKS_RECIPE_REFERENCE'
        c.require(F(packet_source['old_explicit_raw_end_exact'])==legacy_end+origin,'Old registered explicit endpoint changed')
    else:
        c.require(ends is None and source['old_clock']['old_terminal_evidence']['kind']=='LEGACY_CFR_N_DIV_FPS' and
            packet_source['old_explicit_raw_end_exact'] is None,'Unknown null old terminal cannot be substituted')
        legacy_end=F(source['old_clock']['n_frames']*source['fps_den'],source['fps_num'])
        kind='OLD_CFR_N_DIV_FPS_RECIPE_REFERENCE_NOT_PHYSICAL'
    c.require(F(source['old_clock']['legacy_planned_end_exact'])==legacy_end,'Immutable legacy end audit changed')
    if status=='FAIL_PACKET_TERMINAL_WITNESS_NO_FALLBACK':
        c.require(kind=='OLD_EXPLICIT_END_TICKS_RECIPE_REFERENCE' and end!=legacy_end and
            terminal['error']=='Measured packet end differs from old explicit native end ticks',
            'Only the explicitly registered old endpoint-equality failure belongs to this new reader scope')
    else:
        c.require(status=='PASS_MATCHING_MAX_DISPLAY_PACKET_POSITIVE_DURATION_NOT_FRAME_DECODE' and
            F(terminal['physical_end_exact'])==end,'Old identity/demux/other failure cannot be admitted as native evidence')
    witness=clock['physical_endpoint_evidence']
    decoder=clock['first_RGB_decoder_terminal_witness'];audit=clock['packet_terminal_evidence']
    c.require(raw and raw[0]==origin and len(raw)==source['old_clock']['n_frames']==clock['n_frames'] and
        list(map(F,clock['original_exact_pts']))==raw and list(map(F,clock['normalized_exact_pts']))==[p-origin for p in raw] and
        F(clock['first_original_pts_exact'])==origin and F(clock['physical_end_exact'])==end and
        witness['kind']=='LAST_NATIVE_FRAME_PTS_PLUS_POSITIVE_DURATION' and F(witness['last_frame_duration_exact'])>0 and
        F(witness['last_normalized_pts_exact'])==raw[-1]-origin and
        F(clock['last_frame_duration_exact'])==F(witness['last_frame_duration_exact'])==duration and
        F(clock['native_duration_by_ordinal'][str(len(raw)-1)])==duration and
        F(witness['last_normalized_pts_exact'])+duration==end and
        clock['source_sha256']==source['source_sha256'] and clock['source_path']==source['source_path'] and
        clock['measured_geometry']==[source['width'],source['height']] and
        clock['reader_version']==decoder['reader_version']==obs['PyAV_version'] and
        clock['video_stream_index']==video['index'] and F(clock['stream_time_base_exact'])==F(video['time_base_exact']) and
        decoder['status']=='PASS_ACTUAL_FULL_PTS_AND_FRAME_DURATION_EXACT_PACKET_EQUALITY' and
        F(decoder['last_original_pts_exact'])==raw[-1] and F(decoder['last_normalized_pts_exact'])==raw[-1]-origin and
        F(decoder['last_frame_duration_exact'])==duration and F(decoder['physical_end_exact'])==end and
        decoder['packet_terminal_observation_ref']==clock['packet_terminal_observation_ref']==
        witness['packet_terminal_observation_ref']==audit['observation_ref']==source['packet_terminal_observation_ref'] and
        clock['packet_registration_ref']==source['packet_registration_ref'] and
        audit['old_validation_status']==status and audit['old_FAIL_promoted_to_PASS'] is False and
        audit['new_full_frame_decode_required'] is True and audit['exact_old_last_frame_pts_match'] is True and
        audit['unique_maxdisplay_packet'] is True and audit['source_sha256']==source['source_sha256'] and
        F(audit['last_original_pts_exact'])==raw[-1] and F(audit['packet_duration_exact'])==duration and
        F(audit['physical_end_exact'])==end,
        'Independent complete old-PTS/new-decoder/packet/positive-terminal/source witness binding failed')
    return dict(scope='NEW_PYAV17_READER_NATIVE_TERMINAL_SCOPE_V4_VERIFY_ORDINAL_CONTEXT',old_validation_status=status,
        old_FAIL_promoted_to_PASS=False,old_terminal_equality_required_for_new_scope=False,
        legacy_end_exact=str(legacy_end),legacy_terminal_provenance=kind,
        legacy_end_equals_new_native_end=legacy_end==end,new_native_end_exact=str(end),
        actual_first_RGB_decoder_Frame_duration_equals_packet=True,original_full_PTS_count_origin_geometry_equal=True)


def aggregate(registration_path):
    io.host();ctx=io.load(registration_path);store=ctx['store'];plan=ctx['plan']
    from pr_contract import batch_membership,source_video_projection
    coverage=c.full_coverage(plan,ctx['batches'],batch_membership);projection=source_video_projection(plan)
    endpoints={};verification={};clocks={};events=[];accepted=[];batch_terminals=[];source_bindings={};witnesses={};old_status_counts={}
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
        packet_reg_ref=source['packet_registration_ref'];packet_reg=io.read(io.bound(packet_reg_ref,(io.CAMPAIGN,)))
        packet_sources=[row for row in packet_reg['sources'] if str(row['video_id'])==vid]
        c.require(len(packet_sources)==1,'Packet registration has no unique original video identity')
        packet_source=packet_sources[0]
        c.require(c.digest(packet_source)==source['physical_plan_clock']['packet_registration_source_sha256'],
            'Frozen packet registration source entry changed')
        packet_completion_ref=source['packet_completion_ref']
        packet_completion=io.read(io.bound(packet_completion_ref,(io.CAMPAIGN,)))
        refs=[mapping[vid] for name in ('success_terminal_refs','failure_terminal_refs')
              if vid in (mapping:=packet_completion[name])]
        packet_ref=source['packet_terminal_observation_ref']
        c.require(refs==[packet_ref],'Registered packet completion/source observation join differs')
        terminal=io.read(io.bound(packet_ref,(io.CAMPAIGN,)))
        audit=exact_clock(source,clock,original,packet_source,terminal)
        old_status_counts[audit['old_validation_status']]=old_status_counts.get(audit['old_validation_status'],0)+1
        equality_ref=store.write_metadata('permanent/proofs/control_v3/native_equality_'+sid+'.json',dict(
            status='PASS_INDEPENDENT_OLD_FULL_PTS_NEW_READER_FRAME_DURATION_EXACT_PACKET_EQUALITY',source_id=sid,video_id=vid,
            original_clock_ref=original_ref,new_clock_ref=clock_ref,source_completion_ref=complete_ref,
            packet_terminal_observation_ref=packet_ref,packet_registration_ref=packet_reg_ref,
            packet_completion_ref=packet_completion_ref,old_clock_audit=audit,
            verifier_code_sha256=io.sha(__file__),no_epsilon_clip_or_CFR_substitution=True,new_model_calls=0,new_media_decodes=0))
        clocks[vid]=dict(clock,video_id=vid,native_input_source_id=sid,legacy_recipe_clock_audit=audit)
        witnesses[vid]=clock['physical_endpoint_evidence']
        source_bindings[vid]=dict(original_clock_ref=original_ref,new_clock_ref=absolute(store,clock_ref),
            source_CPU_completion_ref=absolute(store,complete_ref),independent_equality_ref=absolute(store,equality_ref),
            packet_terminal_observation_ref=packet_ref,packet_registration_ref=packet_reg_ref,
            packet_completion_ref=packet_completion_ref,original_packet_validation_status=audit['old_validation_status'],
            old_FAIL_promoted_to_PASS=False,legacy_recipe_clock_audit=audit,
            first_RGB_decoder_terminal_witness=clock['first_RGB_decoder_terminal_witness'])
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
        native_terminal_scope='NEW_PYAV17_READER_NATIVE_TERMINAL_SCOPE_V4_VERIFY_ORDINAL_CONTEXT',
        dual_coordinate_application='LEGACY_RECIPE_KEEP_UNKNOWN_NATIVE_CUT_ONLY_MOVED_REFINE',
        old_packet_terminal_diagnostic_status_counts=old_status_counts,old_packet_FAIL_reclassified=False,
        batch_natural_terminals=batch_terminals,source_id_to_video_id=projection,global_graph_sha256=ctx['reg']['global_graph_sha256'],
        scientific_quality_claim=False,old_scientific_failed_gates_changed=False,five_ZIPs_claimed=False,
        actual_new_calls_in_aggregate=0,all_canonical_inputs_raw_and_proofs_retained=True,all_only_new_RGB_leases_closed=True,
        controller_launch_claim_sha256=io.sha(io.BASE/'run_01/launch_claim.json'),stage_journal_sha256_at_aggregate=io.sha(io.BASE/'run_01/journal.jsonl')))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--registration',required=True,type=Path);args=parser.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES']='';aggregate(args.registration)
