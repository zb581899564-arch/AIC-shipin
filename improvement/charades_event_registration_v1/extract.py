"""Frozen metadata-only event extraction after natural38 calls and replays.

No media/reference body, processor, model, tokenizer or evaluator is imported.
This program cannot launch another inference/replay chain or choose by GT.
"""
import argparse
import datetime as dt
from fractions import Fraction as F
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import sys

CAMPAIGN = Path('/home/inspur/aic_video_work/twenty_hour_five_20261014_v1')
COARSE = CAMPAIGN/'charades_coarse_v1'
NATIVE = CAMPAIGN/'charades_boundary_v2'
NATIVE_ROOTS = (CAMPAIGN/'charades_boundary_v1', NATIVE)
RULE_SHA = '5dfa432b3a9669dd4e1807baae1f2a1d965c986100d73497f41e7c4d59d582a0'
SEP_SHA = '7517b319260fd35a105dace75330cf1e60a18de709a606cc7234a9d9bf61b7f0'
PROMPT_SHA = 'dc0aa31d4a4df1894457a636ace17c55159122d62d7200fd2490ede06e19bce0'


def require(ok, why):
    if not ok:
        raise ValueError(why)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    path = Path(path)
    require(path.suffix in ('.json', '.jsonl', '.py'), 'Only metadata/code is read for event extraction')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())


def ref(path, expected=None, roots=(COARSE,)):
    path = Path(path).resolve()
    require(any(path.is_relative_to(root.resolve()) for root in roots), 'Metadata evidence escaped admitted root')
    digest = sha(path)
    require(expected is None or digest == expected, 'Metadata binding changed: '+str(path))
    return dict(path=str(path), sha256=digest)


def choose(source_order, candidates, cap=20):
    """Two fixed rounds only. No confidence, duration, labels or quality sort."""
    require(len(source_order) == len(set(source_order)), 'Distinct source order required')
    selected = []
    for nth in (0, 1):
        for source_id in source_order:
            ordered = sorted(candidates[source_id], key=lambda row: (row['window_index'], row['original_segment_index']))
            if len(ordered) > nth and len(selected) < cap:
                selected.append(ordered[nth])
    return selected


def window_identity(case_id, source_id):
    match = re.fullmatch(r'CH_([A-Za-z0-9]{5})_W([0-9]{3})', case_id)
    require(match is not None and match.group(1) == source_id, 'Original case/source/window identity changed')
    return int(match.group(2))


def checked_rule(root):
    rule_ref = ref(root/'event_extraction_rule.json', RULE_SHA)
    rule = read(rule_ref['path'])
    require(rule['status'] == 'FROZEN_BEFORE_CHARADES_COARSE_AND_BOUNDARY_RESULTS' and
            rule['roles'] == ['dev', 'confirm'] and rule['minimum_events'] == 10 and rule['GT_used'] is False and
            rule['source_order'] == 'frozen effective_source_registry_02 accepted order within each role' and
            rule['event_order'] == 'window index ascending then original segment index ascending' and
            rule['selection'] == 'round1 first nonempty candidate per registered source; round2 second per source; cap20 each role' and
            rule['confirmation_metric_sealed_until_development_selection'] is True and
            rule['confirmation_extraction_frozen_before_first_development_refiner_result'] is True,
            'Exact frozen extraction rule required')
    return rule_ref


def completed_inputs(root):
    """Read only38 metadata proof chains after the unique producer completed."""
    chain_ref = ref(root/'chain_01/completion.json')
    chain = read(chain_ref['path'])
    require(chain['status'] == 'COMPLETE_NEW38_CHARADES_ORIGINAL_B_AND_INDEPENDENT_CPU_REPLAY_NOT_QUALITY' and
            chain['actual_model_calls'] == chain['actual_independent_CPU_replays'] == 38 and chain['optimizer_updates'] == 0,
            'Natural complete38 calls and first independent replay required')
    require(not (root/'chain_01/failure.json').exists() and not (root/'gpu_01/failure.json').exists() and
            not (root/'replay_failure.json').exists(), 'Failed/incomplete producer cannot be silently reused')
    gpu_ref = ref(root/'gpu_01/completion.json', chain['gpu_completion_sha256'])
    replay_ref = ref(root/'replay_01/completion.json', chain['replay_completion_sha256'])
    gpu, replay = read(gpu_ref['path']), read(replay_ref['path'])
    require(gpu['status'] == 'PASS_NEW_CHARADES_COARSE_CALLS_NOT_QUALITY' and gpu['calls'] == 38 and
            replay['status'] == 'PASS_ALL_NEW_CHARADES_COARSE_INPUT_OUTPUT_REPLAYS_NOT_QUALITY' and
            replay['calls'] == 38 and replay['new_model_calls'] == 0 and
            replay['gpu_completion_sha256'] == gpu_ref['sha256'], 'Bound natural GPU/replay denominator')
    admission_ref = ref(root/'gpu_admission.json', gpu['admission_sha256'])
    admission = read(admission_ref['path'])
    require(admission['status'] == 'PASS_INDEPENDENT_CHARADES_REAL_CPU_COARSE_ADMISSION' and
            admission['actual_model_call_budget'] == 38 and admission['model_parameters'] == 8782459120 and
            admission['optimizer_updates'] == 0 and admission['reference_available_to_inference'] is False,
            'Original no-reference38 input admission changed')
    lock_ref = ref(root/'source_input_lock.json', admission['source_input_lock_sha256'])
    files = read(lock_ref['path'])['files']
    rows_ref = ref(root/'coarse_inputs.json', files[str(root/'coarse_inputs.json')])
    effective_ref = ref(NATIVE/'effective_source_registry_02.json', files[str(NATIVE/'effective_source_registry_02.json')], NATIVE_ROOTS)
    rows = read(rows_ref['path'])
    effective = read(effective_ref['path'])
    require((effective['sources'], effective['dev'], effective['confirm']) == (21, 11, 10) and
            len(effective['accepted']) == 21 and len(rows) == 38 and len({x['case_id'] for x in rows}) == 38,
            'Frozen source/input scope changed')
    source_order = {role: [x['source_id'] for x in effective['accepted'] if x['role'] == role]
                    for role in ('dev', 'confirm')}
    require(len(source_order['dev']) == 11 and len(source_order['confirm']) == 10 and
            not set(source_order['dev']) & set(source_order['confirm']), 'Frozen source role identities')
    sources = {x['source_id']: x for x in effective['accepted']}
    separated_ref = ref(NATIVE/'source_separation_v3_03.json', SEP_SHA, NATIVE_ROOTS)
    separation = read(separated_ref['path'])
    require(separation['known_current_b_training_and_426_test_identities_complete'] is True and
            separation['identity_intersections'] == separation['byte_intersections'] == [] and
            separation['actual_sources'] == 21 and set(separation['actual_source_ids']) == set(sources),
            'Exact scoped known-source separation missing')
    gpu_entries = {x['case_id']:x for x in gpu['entries']}
    replay_entries = {x['case_id']:x for x in replay['proofs']}
    cases = [x['case_id'] for x in rows]
    require(len(gpu['entries']) == len(replay['proofs']) == 38 and
            set(gpu_entries) == set(replay_entries) == set(cases), '38 actual answer/replay identities')
    journal_ref = ref(root/'gpu_01/attempts.jsonl', gpu['attempts_sha256'])
    journal = [json.loads(x) for x in Path(journal_ref['path']).read_text().splitlines() if x.strip()]
    require(len(journal) == 76, 'Unique BEGIN/ACCEPTED model calls')
    result = []
    for ordinal, row in enumerate(rows):
        case, sid, role = row['case_id'], row['source_id'], row['source_role']
        require(sid in sources and role == sources[sid]['role'] and row['source_name'] == sid and
                row['worker_subject_id'] == sources[sid]['worker_subject_id'], 'Registered case/source/role identity')
        wi = window_identity(case, sid)
        require(journal[2*ordinal]['event'] == 'BEGIN' and journal[2*ordinal+1]['event'] == 'ACCEPTED' and
                all(x['case_id'] == case and x['call_id'] == ordinal+1 for x in journal[2*ordinal:2*ordinal+2]),
                'Actual call order/denominator changed')
        evidence = dict(input=ref(row['input_path'], row['input_sha256'], NATIVE_ROOTS),
                        cpu_proof=ref(row['proof_path'], row['proof_sha256'], NATIVE_ROOTS),
                        done=ref(root/'gpu_01'/case/'done.json', gpu_entries[case]['done_sha256']),
                        independent_replay=ref(root/'replay_01'/(case+'.json'), replay_entries[case]['proof_sha256']),
                        source_separation=separated_ref)
        require(gpu_entries[case]['done_path'] == evidence['done']['path'] and
                replay_entries[case]['proof_path'] == evidence['independent_replay']['path'], 'Canonical original output paths')
        meta, cpu, done, replay_proof = [read(evidence[k]['path']) for k in ('input', 'cpu_proof', 'done', 'independent_replay')]
        evidence['raw'] = ref(root/'gpu_01'/case/'raw.json', done['raw_sha256'])
        evidence['request'] = ref(root/'gpu_01'/case/'request.json', done['request_sha256'])
        raw, request = read(evidence['raw']['path']), read(evidence['request']['path'])
        evidence['clock'] = ref(meta['native_clock_path'], meta['native_clock_sha256'], NATIVE_ROOTS)
        clock = read(evidence['clock']['path'])['clock']
        require(all(x['case_id'] == case for x in (meta, cpu, done, replay_proof, request)) and
                all(x['source_name'] == sid for x in (meta, cpu, done, replay_proof, request)) and
                meta['source_id'] == sid and meta['source_role'] == role and meta['source_group'] == 'Charades:'+sid,
                '38 input/proof/done/request/replay source-role binding')
        require(meta['reference_available_to_inference'] is False and meta['reference_labels_used_for_sampling'] is False and
                meta['audio_observed'] is False and request['reference_labels_read'] is False and raw['actual_model_call'] is True,
                'No-reference original model call required')
        require(any(Path(meta['source_path']).resolve().is_relative_to(p/'media_01'/sid) for p in NATIVE_ROOTS),
                'Only actual admitted Charades original media paths, metadata check only')
        require(cpu['status'] == 'PASS_CPU_ORIGINAL_B_NATIVE64_PROCESSOR_INPUT' and cpu['CPU_only'] is True and
                cpu['new_model_calls'] == cpu['new_optimizer_updates'] == 0 and
                replay_proof['status'] == 'PASS_INDEPENDENT_CPU_TENSOR_TOKEN_PARSER_NATIVE_REPLAY' and
                replay_proof['CPU_only'] is True and replay_proof['new_model_calls'] == replay_proof['new_optimizer_updates'] == 0 and
                done['status'] in ('MODEL_OK', 'LEGAL_EMPTY') and done['new_optimizer_updates'] == 0,
                'Accepted input/output/replay statuses changed')
        require(cpu['input_sha256'] == request['input_sha256'] == evidence['input']['sha256'] and
                request['input_path'] == evidence['input']['path'] and
                request['CPU_proof_sha256'] == evidence['cpu_proof']['sha256'] and
                done['raw_path'] == evidence['raw']['path'] and
                replay_proof['done_sha256'] == evidence['done']['sha256'] and replay_proof['raw_sha256'] == evidence['raw']['sha256'] and
                cpu['input_evidence'] == done['input_evidence'] == request['input_evidence'] == raw['input_evidence'] == replay_proof['input_evidence'],
                'Existing38 strict evidence linkage changed')
        require(hashlib.sha256(request['prompt'].encode()).hexdigest() == PROMPT_SHA and
                cpu['input_evidence']['prompt_sha256'] == PROMPT_SHA and request['adapter_enabled'] is True,
                'Original B0/timeLoRA prompt identity changed')
        require(clock['source_id'] == sid and clock['source_sha256'] == meta['source_sha256'] and
                clock['normalized_exact_pts'] == meta['all_source_exact_pts'] and
                clock['first_original_pts_exact'] == meta['original_clock_origin_exact'] and
                clock['n_frames'] == meta['source_total_frames'] and clock['positive_last_frame_duration_verified'] is True,
                'Original complete native clock identity changed')
        lo, hi = F(meta['window_start']), F(meta['window_end'])
        require(str(lo) == done['source_start_exact'] and str(hi) == done['source_end_exact'] and
                0 <= lo < hi <= F(clock['physical_end_exact']) and len(meta['source_frame_ordinals']) == 64 and
                len(set(meta['source_frame_ordinals'])) == 64, 'Original native64 window binding')
        require(done['segments'] == replay_proof['segments'] and done['native_ranges'] == replay_proof['native_ranges'] and
                (done['status'] == 'LEGAL_EMPTY') == (len(done['segments']) == 0) and
                len(done['segments']) == len(done['native_ranges']) <= 5 and not done['parse_errors'],
                'Original parser/native replay changed')
        candidates = []
        for si, segment in enumerate(done['segments']):
            require(len(segment) == 2, 'Original segment interval shape')
            a, b = map(lambda x:F(str(x)), segment)
            require(0 <= a < b <= hi-lo, 'Original segment endpoint identity')
            candidates.append(dict(event_id=case+'.S'+str(si).zfill(2), original_case_id=case,
                original_segment_index=si, original_interval_exact=[str(lo+a), str(lo+b)],
                clock_object_keys=['clock'], original_evidence=evidence, window_index=wi,
                source_id=sid, source_role=role))
        result.append(dict(case_id=case, source_id=sid, source_role=role, window_index=wi,
                           input_ref=evidence['input'], candidates=candidates, status=done['status']))
    for sid in sources:
        indices = sorted(x['window_index'] for x in result if x['source_id'] == sid)
        require(indices == list(range(len(indices))) and indices, 'Complete contiguous source coarse windows')
    provenance = dict(chain=chain_ref,gpu=gpu_ref,replay=replay_ref,admission=admission_ref,
                      input_lock=lock_ref,inputs=rows_ref,effective_sources=effective_ref,
                      source_separation=separated_ref,attempt_journal=journal_ref)
    return source_order, result, provenance


def extract(root):
    require(socket.gethostname() == 'inspur-NP5570M5' and sys.platform == 'linux' and
            os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'Verified Linux CPU-only extraction process required')
    root = Path(root).resolve()
    require(root == COARSE, 'Fixed independent coarse output root')
    rule_ref = checked_rule(root)
    order, inputs, provenance = completed_inputs(root)
    output = root/'event_extraction_01'
    output.mkdir(exist_ok=False)
    save(output/'claim.json', dict(pid=os.getpid(), utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        rule=rule_ref, code=dict(path=str(Path(__file__).resolve()),sha256=sha(__file__)), provenance=provenance,
        new_model_calls=0, new_media_reads=0, GT_reads=0, independent_replays_repeated=0))
    try:
        coverage, files = {}, {}
        for role in ('dev', 'confirm'):
            candidates = {sid:[event for item in inputs if item['source_id']==sid for event in item['candidates']]
                          for sid in order[role]}
            selected = choose(order[role], candidates)
            events = []
            for event in selected:
                sid = event['source_id']
                reusable = [x['input_ref'] for x in sorted(inputs,key=lambda x:x['window_index']) if x['source_id']==sid]
                require(event['original_evidence']['input'] in reusable, 'Original input absent from same-source RGB reuse refs')
                events.append({**event,'reuse_rgb_inputs':reusable})
            events_path = output/(role+'_events.json')
            save(events_path,events)
            files[role] = ref(events_path)
            source_rows = [dict(source_id=sid, coarse_windows=sum(x['source_id']==sid for x in inputs),
                candidate_count=len(candidates[sid]), selected_events=[x['event_id'] for x in events if x['source_id']==sid],
                empty_coarse_source=not candidates[sid], retained_in_coverage=True) for sid in order[role]]
            coverage[role] = dict(source_count=len(order[role]), source_order=order[role], sources=source_rows,
                original_candidate_count=sum(map(len,candidates.values())), selected_event_count=len(events),
                minimum_events=10, minimum_met=len(events)>=10, cap=20,
                insufficient_events_action='KEEP_FROZEN_RULE_NO_NEW_SOURCE_OR_THRESHOLD' if len(events)<10 else None,
                GT_used=False, confidence_or_duration_sort_used=False, reference_metrics_read=False)
        save(output/'coverage.json',coverage)
        save(output/'completion.json',dict(status='COMPLETE_FROZEN_EVENT_EXTRACTION_NOT_QUALITY_OR_GPU_ADMISSION',
            utc=dt.datetime.now(dt.timezone.utc).isoformat(),rule=rule_ref,provenance=provenance,events=files,
            coverage_path=str(output/'coverage.json'),coverage_sha256=sha(output/'coverage.json'),
            role_event_counts={role:coverage[role]['selected_event_count'] for role in coverage},
            role_minimum_met={role:coverage[role]['minimum_met'] for role in coverage},
            exact_coarse_windows=38,exact_source_denominator=21,dev_sources=11,confirm_sources=10,
            confirmation_extraction_frozen_before_development_refiner_results=True,
            confirmation_metrics_sealed=True,new_model_calls=0,new_media_reads=0,new_processor_encodes=0,
            independent_replays_repeated=0,GT_reads=0,GPU_admitted=False))
        print(json.dumps(dict(status='COMPLETE_FROZEN_EVENT_EXTRACTION_NOT_QUALITY_OR_GPU_ADMISSION',
            output_path=str(output),role_event_counts={r:coverage[r]['selected_event_count'] for r in coverage},
            minimum_met={r:coverage[r]['minimum_met'] for r in coverage},new_model_calls=0)))
    except BaseException as error:
        save(output/'failure.json',dict(error=repr(error),keep_all_outputs=True,no_original_stage_repetition=True,
            new_model_calls=0,new_media_reads=0,GT_reads=0))
        raise


def pure_check():
    source_order=['SYN01','SYN02','SYN03']
    c=lambda label,w,s:dict(event_id=label,window_index=w,original_segment_index=s)
    data={'SYN01':[c('a2',1,0),c('a1',0,1),c('a0',0,0)],'SYN02':[],
          'SYN03':[c('b1',1,0),c('b0',0,0)]}
    require([x['event_id'] for x in choose(source_order,data)]==['a0','b0','a1','b1'],
            'Hand oracle fixed rounds/source/window/segment order')
    require(not choose(source_order,{x:[] for x in source_order}),'Legal all-empty selection remains empty')
    order=['SRC'+str(i).zfill(2) for i in range(11)]
    data={sid:[c(sid+'.0',0,0),c(sid+'.1',0,1),c(sid+'.2',0,2)] for sid in order}
    picked=choose(order,data)
    require(len(picked)==20 and [x['event_id'] for x in picked]==[sid+'.0' for sid in order]+[sid+'.1' for sid in order[:9]],
            'Cap20 does not introduce third round or source/duration ranking')
    require(window_identity('CH_LJ2J6_W002','LJ2J6')==2,'Exact original window identity')
    try:window_identity('CH_LJ2J6_W002','2JTRG')
    except ValueError:pass
    else:raise ValueError('Mismatched source accepted')
    print(json.dumps(dict(status='PASS_METADATA_SELECTOR_HAND_ORACLES_ONLY_NO_REAL_ANSWERS_READ',checks=5,
        code_sha256=sha(__file__),real_coarse_answer_reads=0,real_replay_reads=0,GT_reads=0,
        media_reads=0,processor_encodes=0,model_calls=0,actual_extraction_runs=0)))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',default=str(COARSE))
    parser.add_argument('--pure-check',action='store_true')
    args=parser.parse_args()
    pure_check() if args.pure_check else extract(args.root)
