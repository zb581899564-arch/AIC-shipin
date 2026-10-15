"""Independent positive-recipe fixed40 B0 upper-bound authority and provenance."""
from fractions import Fraction as F
from pathlib import Path

REFERENCE_SHA = '37a7c93876334b3a5d0c222e3a7f99727778d50f28f3a1172e860d19d3dc82b8'
SCOPE = 'FULL_ORIGINAL_SOURCE_ZERO_ORIGIN_15_STRIDE7_5'
CONDITIONS = ('full_group', 'macro_F1_not_lower', 'macro_recall_gain', 'every_source_loss_within_gate',
    'macro_precision_not_lower', 'all_rater_recall_retained', 'all_baseline_native_frames_retained', 'real_changed_sources')


def common():
    import facts_common
    return facts_common


def ref(path):
    io = common(); path = io.checked(path)
    return dict(path=str(path), sha256=io.sha(path))


def bound(value):
    return common().checked(value['path'], value['sha256'])


def code_files():
    io = common(); return {str(path.resolve()): io.sha(path) for path in Path(__file__).parent.glob('*.py')}


def phase_pass(protocol_ref, protocol, group, result):
    """Pure hard gate: a proposal, old consensus result or partial PASS rejects."""
    io = common()
    expected = 'PASS_ADAPTER_ROLE_DEV_PENDING_NEW_FRESH_CONFIRM' if group == 'dev' else 'PASS_ROLE_FRESH_CONFIRM_PENDING_FIXED40'
    io.require(result['status'] == expected and result['group'] == group and len(result['cases']) == 4 and
        set(result['conditions']) == set(CONDITIONS) and all(value is True for value in result['conditions'].values()) and
        result['bindings']['protocol_ref'] == protocol_ref and result['candidate'] == protocol['candidate'] and
        result['production_admitted'] is False and result['old_failed_gates_changed'] is False,
        'Real complete current positive dev and first-fresh confirmation PASS required; no old consensus or failed confirmation')


def validate_complete_covering_grid(views, clocks, ordinary, sources):
    """Independent pure set QA of a newly registered metadata snapshot.

    The sufficient P bound needs EVERY grid window capable of touching O,
    including overlapping covers and the exact right tail. Equal counts,
    covering each O at least once or per-window legality are insufficient.
    No old source audit, clock measurement or media decode is called here.
    """
    io = common()
    source_by_name = {source['video_id']: source for source in sources}
    io.require(len(source_by_name) == len(sources) and set(clocks) == set(ordinary) == set(source_by_name),
        'Complete distinct source/clock/original-ORDINARY denominator required for geometry QA')
    source_identities = {(s['source_sha256'], s['clock_sha256']) for s in sources}
    io.require(len(source_identities) == len(sources), 'Distinct same-source SHA/clock identities required')
    expected = set()
    for name, source in source_by_name.items():
        clock = clocks[name]; points = list(map(F, clock['original_exact_pts'])); end = F(clock['physical_end_exact'])
        io.require(points and points[0] == 0 and all(a < b for a, b in zip(points, points[1:])) and end > points[-1],
            'Stored complete zero-origin clock and positive exact physical endpoint required')
        observed = []
        for point in ordinary[name]:
            ordinal, timestamp = point['ordinal'], F(point['exact_pts'])
            io.require(point['label'] == 'ORDINARY' and type(ordinal) is int and 0 <= ordinal < len(points) and
                points[ordinal] == timestamp, 'Original ORDINARY ordinal/exact PTS identity differs in geometry QA')
            observed.append(timestamp)
        io.require(observed and len(set(observed)) == len(observed), 'Every ordinary-bearing source requires distinct observed native points')
        # Independent reconstruction of the complete original grid, rather
        # than a subset selected from the registered view list.
        grid = set()
        if end <= 15:
            grid.add((F(0), end))
        else:
            start = F(0)
            while start+15 <= end:
                grid.add((start, start+15))
                start += F(15, 2)
            grid.add((end-15, end))
        for start, stop in grid:
            if any(start <= timestamp < stop for timestamp in observed):
                expected.add((source['source_sha256'], source['clock_sha256'], start, stop))
    registered = []
    for view in views:
        io.require(view['source_name'] in source_by_name, 'Registered window names an unregistered source')
        source = source_by_name[view['source_name']]
        io.require(view['source_sha256'] == source['source_sha256'] and
            view['source_clock_sha256'] == source['clock_sha256'], 'Registered window changed original source/clock SHA')
        registered.append((view['source_sha256'], view['source_clock_sha256'], F(view['window_start']), F(view['window_end'])))
    io.require(len(registered) == len(set(registered)), 'Duplicate normalized source/clock/window geometry, even under different case IDs')
    io.require(set(registered) == expected,
        'Registered geometry must equal ALL original grid windows touching any ORDINARY point; no missing/replaced/extra window')
    return expected


def registration(root):
    io = common(); reg_path = root/'role_fixed40_registration.json'; reg = io.read(reg_path)
    io.require(reg['schema'] == 'ROLE_FIXED40_B0_UPPER_BOUND_REGISTRATION_V1' and
        reg['status'] == 'REGISTERED_ROLE_FIXED40_B0_ONLY_AFTER_DEV_FRESH_CONFIRM_PASS' and
        reg['source_scope'] == 'EXTERNAL_NONTEST_ONLY' and reg['scope'] == SCOPE and
        reg['model_parameters'] == io.MODEL_PARAMETERS and reg['optimizer_updates'] == 0 and
        reg['source_count'] == 9 and reg['unique_input_count'] == 17 and reg['production_admitted'] is False and
        reg['reference_available_to_inference'] is False and reg['next_level_automatically_authorized'] is False,
        'New independent positive B0-only seventeen-window fixed40 registration required')
    io.require(Path(__file__).resolve().parent == root/'code', 'Only independently deployed positive fixed40 code may execute')
    required = reg['required_files']
    dependencies = set(code_files()) | io.runtime_dependencies() | io.processor_assets() | {str(io.CONFIG), str(io.RUNTIME)}
    io.require(dependencies <= set(required) and all(required[name] == digest for name, digest in code_files().items()),
               'All new code/runtime/processor metadata must be frozen before work')
    for name, digest in required.items():
        io.checked(name, digest)
    positive_codes=reg['positive_code_files']
    io.require({'positive_contract.py','positive_io.py','positive_metrics.py','positive_evaluate.py','positive_runtime.py'} <=
        {Path(name).name for name in positive_codes} and
        all(required.get(name)==digest for name,digest in positive_codes.items()),
        'Frozen strict-positive endpoints/admission/union implementation must support the subset proof')
    for name in ('protocol_ref', 'authorization_ref', 'dev_result_ref', 'confirm_result_ref',
                 'source_audit_plan_ref', 'source_audit_completion_ref', 'source_audit_code_ref', 'reference_ref'):
        path = bound(reg[name]); io.require(required.get(str(path)) == reg[name]['sha256'], 'Registered evidence absent from input/code/source closure: '+name)
    # Only a previously measured bit-equivalent reader is accepted. This
    # proves serialization equivalence, not model or scientific quality.
    import ast, hashlib
    for key in ['cache_reader_equivalence_ref','cache_reader_engineering_registration_ref']:
        io.require(required.get(str(bound(reg[key])))==reg[key]['sha256'], 'Actual read-once reader evidence must be frozen')
    check=io.read(reg['cache_reader_equivalence_ref']['path']);engineering=io.read(reg['cache_reader_engineering_registration_ref']['path'])
    text=Path(io.__file__).read_text();tree=ast.parse(text)
    function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='load_cache')
    io.require(check['status']=='PASS_CPU_CACHE_READER_BIT_EQUIVALENCE_NOT_MODEL_OR_QUALITY_QA' and
        check['all_CPU_tensor_keys_shapes_dtypes_bits_identical'] is True and check['source_file_unchanged'] is True and
        check['model_calls']==check['processor_calls']==check['media_decodes']==check['first_input_or_output_QA_runs']==0 and
        check['registration_sha256']==reg['cache_reader_engineering_registration_ref']['sha256'] and
        engineering['new_function_sha256']==hashlib.sha256(ast.get_source_segment(text,function).encode()).hexdigest(),
        'Exact tested single-inflate reader must preserve all original cache bits, not substitute model/QA success')
    separation=reg['source_separation_refs']
    io.require(len(separation)==2 and all(required.get(str(bound(value)))==value['sha256'] for value in separation),
        'Original two external known-ID/byte isolation receipts must remain frozen, not inferred from storage path')
    primary, supplement = [io.read(value['path']) for value in separation]
    io.require(primary['status']=='PASS_KNOWN_SOURCE_ID_AND_EXACT_BYTE_SEPARATION_NOT_SEMANTIC_PROOF' and
        primary['selected_source_groups']==20 and primary['teacher_train_source_intersection']==[] and
        primary['official_exact_sha_intersection']==[] and primary['official_metadata_records']==426 and
        supplement['status']=='PASS_KNOWN_SOURCE_SEPARATION' and supplement['sources']==20 and
        supplement['train_source_group_intersection']==[] and supplement['official_sha_intersection']==[] and
        supplement['official_records']==426 and supplement['semantic_reencoded_separation_proven'] is False,
        'Only existing external40 source/byte-isolated reference, without global semantic claims, may be reused')
    protocol = io.read(reg['protocol_ref']['path'])
    io.require(protocol['schema'] == 'ADAPTER_ROLE_SAME_INPUT_EXTERNAL_DEV_ABLATION_V1' and
        protocol['candidate'] == 'BASE_ONLY_POSITIVE_ADMISSION_SAME_INPUT_PAIR' and
        protocol['single_factor'] == 'BASE_ONLY_FOR_NEW_ADMISSION_TIME_FOR_PROPOSALS' and
        protocol['model_parameters'] == io.MODEL_PARAMETERS and
        protocol['quality_gates']['fixed_40_KEEP_deletion'] == protocol['quality_gates']['fixed_40_ORDINARY_addition'] == 0 and
        protocol['quality_gates']['UNKNOWN_and_old_reference_quality_FAILED_unchanged'] is True,
        'Frozen positive v2 recipe and unchanged known-fact zero gates required')
    for group in ('dev', 'confirm'):
        result_ref = reg[group+'_result_ref']; result = io.read(result_ref['path']); phase_pass(reg['protocol_ref'], protocol, group, result)
        phase = reg['phase_execution'][group]
        for value in phase.values():
            path = bound(value); io.require(required.get(str(path)) == value['sha256'], 'Real phase execution evidence must be frozen')
        chain = io.read(phase['chain_ref']['path']); qa = io.read(phase['output_QA_completion_ref']['path'])
        gpu = io.read(phase['gpu_completion_ref']['path']); gate = io.read(phase['gpu_admission_ref']['path'])
        phase_registration=io.read(phase['registration_ref']['path'])
        model_path=bound(gpu['model_identity_ref']);journal_path=bound(gpu['attempts_ref'])
        io.require(required.get(str(model_path))==gpu['model_identity_ref']['sha256'] and
            required.get(str(journal_path))==gpu['attempts_ref']['sha256'], 'Actual phase model and unique call journal must be registered')
        io.verify_identity(io.read(model_path)['identity']);journal=io.rows(journal_path)
        io.require(len(journal)==2*gpu['calls'], 'Actual dev/fresh unique call journal denominator differs')
        resource, resource_sha = io.terminal(gate)
        input_qa = io.read(phase['input_QA_completion_ref']['path'])
        output_binding = 'output_QA_ref' if group == 'dev' else 'output_QA_completion_ref'
        qa_status = 'PASS_ROLE_ALL10_OUTPUT_QA_NOT_QUALITY' if group == 'dev' else 'PASS_ALL_POSITIVE_OUTPUT_QA_NOT_QUALITY'
        gpu_status = 'PASS_ROLE_ALL10_MODEL_CALLS_NOT_QUALITY' if group == 'dev' else 'PASS_ALL_POSITIVE_CALLS_NOT_QUALITY'
        phase_codes = reg['phase_code_files'][group]
        io.require(len(phase_codes) == (3 if group == 'dev' else 8) and
            all(phase_registration['required_files'].get(name) == digest == required.get(name) for name,digest in phase_codes.items()),
            'Exact actual distinct ROLE development and BASE-confirmation implementations must be frozen')
        io.require(chain['status'] == result['status'] and chain['comparison_ref'] == result_ref and
            qa['status'] == qa_status and qa['calls'] == len(qa['proofs']) == gpu['calls'] == len(gpu['entries']) ==
            gate['expected_input_count'] == input_qa['calls'] == len(input_qa['proofs']) > 0 and
            gpu['status'] == gpu_status and gpu['admission_ref'] == phase['gpu_admission_ref'] and
            gate['first_input_QA_ref'] == phase['input_QA_completion_ref'] and
            qa['gpu_completion_ref'] == phase['gpu_completion_ref'] and qa['resource_terminal_sha256'] == resource_sha and
            phase['resource_ref']['sha256'] == resource_sha and result['bindings'][output_binding] == phase['output_QA_completion_ref'] and
            result['bindings']['registration_ref'] == phase['registration_ref'] and
            qa['CPU_only'] is True and qa['CUDA_initialized'] is False and input_qa['CPU_only'] is True and
            input_qa['CUDA_initialized'] is False,
            'Actual natural ROLE dev/fresh output QA and complete first-input QA must support their unchanged PASS')
        io.require(len({item['case_id'] for item in qa['proofs']}) == qa['calls'] and
            [item['case_id'] for item in qa['proofs']] == [item['case_id'] for item in gpu['entries']] ==
            [item['case_id'] for item in input_qa['proofs']],
            'Complete phase call/QA identity and order required')
        for index,(item,qa_item) in enumerate(zip(gpu['entries'],qa['proofs']),1):
            begun,accepted=journal[2*(index-1):2*index]
            io.require(begun['event']=='BEGIN' and accepted['event']=='ACCEPTED' and
                begun['call_id']==accepted['call_id']==index and begun['case_id']==accepted['case_id']==item['case_id'] and
                accepted['done_ref']==item['done_ref'], 'Actual passing phase output/journal must match exactly')
            done=io.read(bound(item['done_ref'])); proof=io.read(bound(qa_item['proof_ref']));raw=io.read(bound(done['raw_ref']))
            io.require(all(required.get(value['path'])==value['sha256'] for value in
                (item['done_ref'],qa_item['proof_ref'],done['raw_ref'])) and
                proof['done_ref']==item['done_ref'] and proof['decision_result']==done['decision_result'] and
                raw['activation_role']=='BASE_ONLY_FOR_NEW_ADMISSION_TIME_FOR_PROPOSALS' and
                raw['actual_physical_parameters']==8782459120 and raw['activated_base_parameters']==8767123696 and
                raw['adapter_disabled_layers']==[True]*144 and raw['actual_model_call'] is True,
                'Already independently checked actual BASE-only admission, not old TIME decisions, must support this exact recipe')
    pairs=reg['unchanged_admission_contract_pairs']
    io.require(set(pairs)=={'positive_contract.py','positive_grammar.py','positive_metrics.py'},
        'Exact unchanged prompt/grammar/merge semantics pairs required')
    for pair in pairs.values():
        io.require(len(pair)==2 and pair[0]['sha256']==pair[1]['sha256'] and
            all(required.get(str(bound(value)))==value['sha256'] for value in pair),
            'Role change cannot substitute prompt, grammar, endpoints or merge semantics')
    audit_plan = io.read(reg['source_audit_plan_ref']['path']); audit_done = io.read(reg['source_audit_completion_ref']['path'])
    io.require(audit_plan['schema'] == 'RECALL_FIXED40_SOURCE_METADATA_PLAN_V1' and audit_plan['scope'] == SCOPE and
        audit_plan['source_count'] == 9 and audit_plan['unique_input_count'] == 17 and
        audit_plan['ordinary_observation_count'] == 222 and audit_plan['metadata_only'] is True and
        audit_plan['model_calls'] == 0 and audit_plan['GPU_admitted'] is False and
        audit_plan['coverage_pass'] is False and audit_plan['reference_quality_pass'] is False,
        'Adopt the complete already successful source/clock/grid audit; never relabel it model execution or scientific quality PASS')
    io.require(audit_plan['coverage'] == dict(sources=40,keep_sources=6,ordinary_sources=9,two_ended_dense_events=1,
        KEEP=184,ORDINARY=222,UNKNOWN=2675), 'Original silver KEEP/ORDINARY/UNKNOWN coverage metadata must remain exact')
    # source_audit.main's immutable metadata plan itself is its successful
    # receipt. A separate completion must explicitly bind that exact plan.
    io.require(reg['source_audit_completion_ref'] == reg['source_audit_plan_ref'] or
        (audit_done['status'] == 'PASS_FIXED40_SOURCE_AUDIT_METADATA_ONLY' and audit_done['source_plan_ref'] == reg['source_audit_plan_ref'] and
         audit_done['model_calls'] == 0), 'Existing completed audit must be bound without rerunning it')
    io.require(reg['reference_ref']['sha256'] == REFERENCE_SHA and
        audit_plan['reference_ref'] == reg['reference_ref'] and Path(reg['reference_ref']['path']).stat().st_size == 594682,
        'Original full silver bytes/SHA must remain pinned')
    config = io.read(io.CONFIG); contract = reg['capacity_contract']
    io.require(contract['video_size'] == config['video_size'] and contract['video_size']['longest_edge'] == 25165824 and
        required.get(contract['processor_source_path']) == contract['processor_source_sha256'],
        'Original total-video pixel limit/source must be frozen; no capacity workaround')
    io.require(reg['gpu_budget']['max_actual_calls'] == len([v for v in reg['execution_plan'] if v['mode'] == 'NEW']) and
        0 <= reg['gpu_budget']['max_actual_calls'] <= 17 and 0 < reg['gpu_budget']['max_seconds'] <= 1800,
        'Exact new-call denominator and bounded B0-only budget required')
    return reg


def metadata(root, reg):
    """Read stored audited geometry and clocks; no geometry/source audit rerun."""
    io = common(); from native import native_view
    plan = io.read(reg['source_audit_plan_ref']['path']); sources, views = plan['sources'], plan['views']
    io.require(len(sources) == len({s['video_id'] for s in sources}) == 9 and
        len(views) == len({v['case_id'] for v in views}) == 17, 'Complete inherited nine-source/seventeen-view geometry required')
    source_by_id, clocks = {}, {}
    for source in sources:
        for pathkey, shakey in (('source_path', 'source_sha256'), ('clock_path', 'clock_sha256')):
            io.require(reg['required_files'].get(source[pathkey]) == source[shakey], 'Every original media/clock identity must be in new lock')
            io.checked(source[pathkey], source[shakey])
        original = io.read(source['clock_path']); pts = original['pts_rational']; end = original['physical_endpoint_rational']
        io.require(original['source_sha256'] == source['source_sha256'] and original['raw_origin_sec'] == 0 and
            original['source_path'] == source['source_path'] and source['source_sha256'] == source['source_key'] and
            len(pts) == original['n_frames'] == source['n_frames'], 'Inherited full original clock/source binding changed')
        clock = dict(original_exact_pts=pts, physical_end_exact=end, native_frames=len(pts),
            original_zero_origin_verified=True, first_original_pts_exact=pts[0],
            timeline_shift_applied=False, last_frame_duration_exact=str(F(end)-F(pts[-1])),
            **{key: original[key] for key in ('width','height','fps_num','fps_den')})
        source_by_id[source['video_id']] = source; clocks[source['video_id']] = clock
    actual = [native_view(v, source_by_id[v['source_name']], clocks[v['source_name']]) for v in views]
    execution = reg['execution_plan']
    io.require([row['case_id'] for row in execution] == [v['case_id'] for v in actual] and
        all(row['mode'] in ('NEW', 'ADOPT') for row in execution), 'Explicit complete ordered per-window NEW/ADOPT denominator required')
    reference = io.read(reg['reference_ref']['path'])
    io.require(reference['status'] == 'STOP_REFERENCE_COVERAGE_INSUFFICIENT' and reference['coverage_pass'] is False and
        reference['reference_quality_pass'] is False and reference['old_formal_quality_failed_preserved'] is True,
        'Silver reference FAILED/UNKNOWN facts must remain unchanged')
    ordinary = {}
    for row in reference['rows']:
        if row['video_id'] not in source_by_id:
            continue
        source = source_by_id[row['video_id']]; clock = clocks[row['video_id']]
        io.require(row['source_key'] == source['source_key'] and row['clock_sha256'] == source['clock_sha256'] and
            row['case_id'] == source['case_id'], 'Original observed point/source identity differs')
        points = [p for p in row['points'] if p['label'] == 'ORDINARY']
        for point in points:
            io.require(type(point['ordinal']) is int and 0 <= point['ordinal'] < len(clock['original_exact_pts']) and
                F(clock['original_exact_pts'][point['ordinal']]) == F(point['exact_pts']), 'Ordinary observation is not the same actual native frame')
        ordinary[row['video_id']] = points
    io.require(len(ordinary) == 9 and sum(map(len, ordinary.values())) == 222, 'Original complete 222 ORDINARY facts required')
    validate_complete_covering_grid(actual, clocks, ordinary, sources)
    return sources, clocks, actual, ordinary


def accepted_b0(root, group, cpu_path=None, lock_path=None):
    io = common(); reg = registration(root); io.require(group == 'facts', 'Only facts B0 scope required')
    gate_path = root/'gpu_admission_B0.json'; gate = io.read(gate_path)
    actual_cpu = root/'cpu_acceptance.json'; actual_lock = root/'source_lock_B0.json'
    io.require(cpu_path is None or Path(cpu_path).resolve() == actual_cpu, 'Explicit CPU acceptance disagrees')
    io.require(lock_path is None or Path(lock_path).resolve() == actual_lock, 'Explicit input lock disagrees')
    io.require(gate['status'] == 'PASS_ROLE_FIXED40_B0_GPU_ADMISSION' and gate['stage'] == 'B0' and gate['group'] == group and
        gate['registration_ref'] == ref(root/'role_fixed40_registration.json') and gate['cpu_ref'] == ref(actual_cpu) and
        gate['source_lock_ref'] == ref(actual_lock), 'New current-recipe all-first-input-QA GPU admission required')
    files = io.validate_lock(actual_lock, set(code_files()) | set(reg['required_files']) | {str(actual_cpu)})
    cpu = io.read(actual_cpu); expected = [row['case_id'] for row in reg['execution_plan'] if row['mode'] == 'NEW']
    io.require(cpu['status'] == 'PASS_ROLE_FIXED40_ALL_NEW_INPUTS_FIRST_QA_PRE_GPU' and
        [e['case_id'] for e in cpu['entries']] == expected and cpu['first_input_QA_calls'] == len(expected) and
        cpu['CPU_only'] is True and cpu['CUDA_initialized'] is False and gate['expected_input_count'] == len(expected),
        'Every exact registered NEW input must have real first independent QA before GPU')
    values = []; runtime = io.runtime_only()
    for entry in cpu['entries']:
        meta = io.read(io.locked_ref(entry['input_path'], entry['input_sha256'], files)); io.validate_native(meta)
        proof = io.read(io.locked_ref(entry['proof_path'], entry['proof_sha256'], files))
        first = io.read(io.locked_ref(proof['first_input_QA_path'], proof['first_input_QA_sha256'], files))
        io.require(first['status'] == 'PASS_FIRST_INDEPENDENT_ROLE_FIXED40_INPUT_QA_PRE_GPU' and
            proof['input_evidence'] == first['input_evidence'] and proof['case_id'] == first['case_id'] == meta['case_id'] == entry['case_id'] and
            meta['reference_available_to_inference'] is False and meta['audio_observed'] is False,
            'Actual immutable primary/native/first-input-QA binding differs')
        cache = io.load_cache(io.locked_ref(proof['encoded_tensor_path'], proof['encoded_tensor_sha256'], files))
        io.require(runtime.tensor_signature(cache) == proof['input_evidence']['tensor_signature'] and
                   int(cache['input_ids'].shape[1]) == proof['input_tokens'], 'Accepted actual input cache changed')
        values.append((entry, proof, meta)); del cache
    return gate, cpu, files, values, gate_path, actual_cpu, actual_lock


def completed_job(out, gate, gate_path, count):
    io = common(); complete = io.read(out/'completion.json')
    io.require(complete['status'] == 'PASS_ROLE_FIXED40_B0_NEW_CALLS_NOT_FACT_QUALITY' and complete['group'] == 'facts' and
        complete['calls'] == len(complete['entries']) == count and complete['admission_sha256'] == io.sha(gate_path) and
        complete['attempts_sha256'] == io.sha(out/'attempts.jsonl') and
        complete['model_identity_sha256'] == io.sha(out/'model_identity.json'), 'Complete new actual B0 execution evidence required')
    io.verify_identity(io.read(out/'model_identity.json')['identity'])
    by_id = {row['case_id']: row for row in complete['entries']}; journal = io.rows(out/'attempts.jsonl')
    io.require(len(by_id) == count and len(journal) == 2*count, 'Unique actual B0 call/journal denominator required')
    for index, row in enumerate(complete['entries'],1):
        begin, done = journal[2*(index-1):2*index]
        io.require(begin['event'] == 'BEGIN' and done['event'] == 'ACCEPTED' and
            begin['case_id'] == done['case_id'] == row['case_id'] and begin['call_id'] == done['call_id'] == index and
            done['done_sha256'] == row['done_sha256'] and done['done_path'] == row['done_path'], 'Actual B0 journal identity/order differs')
    return complete, by_id
