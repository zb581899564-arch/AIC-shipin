"""Read-only reconstruction of CLI36 observation supply, never teacher compliance.

Only stdlib is imported. Existing pixel/processor proofs are reused with exact
byte bindings; no image, video, tensor, processor or model is decoded here.
All writes are exclusive creations in this script's own directory.
"""
import argparse
import ast
import copy
import hashlib
import json
import re
import traceback
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

OWN = Path(__file__).resolve().parent
ROOT = OWN.parent
CALL = ROOT / 'teacher_expansion/engineering_CLI36_37_split_fragment_v8v5/call36'
AUDIT_SHA = '69b39eb3aeeab4319c17a5bfb442130ad3ba5377cd5a614a3224902014d077b2'
REVIEW_SHA = 'dd0f7a8b6270edf7f17993f0a3f36c00119db2fb37146bbb5f53305de085e724'
BLOCKER_SHA = '656d1752614ac173d91b74c2a2058b60eaf2726dabf6dda69f5b503b929351d5'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def read(path):
    # Reject duplicate keys instead of silently changing original item values.
    def pairs(items):
        out = {}
        for key, value in items:
            require(key not in out, 'DUPLICATE_JSON_KEY:' + key)
            out[key] = value
        return out
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=pairs)


def key(path):
    return str(Path(path).resolve()).casefold()


def bind(path, expected=None):
    p = Path(path)
    h = sha(p)
    require(expected is None or h == expected, 'SHA_DRIFT:' + str(p))
    return {'path': str(p), 'sha256': h, 'bytes': p.stat().st_size}


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def save(path, value):
    path = Path(path).resolve()
    require(path.parent == OWN, 'WRITE_OUTSIDE_OWN_DIRECTORY')
    data = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    with path.open('x', encoding='utf-8', newline='\n') as handle:
        handle.write(data)
    return bind(path)


def original_fact_validator(common_path):
    # Execute only the original pure function AST, never import its module or
    # helpers that load PIL/numpy/processor/decoder. Whole source is SHA frozen.
    source = Path(common_path).read_text(encoding='utf-8-sig')
    tree = ast.parse(source)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'fact_items')
    require(not any(isinstance(n, (ast.Import, ast.ImportFrom)) for n in ast.walk(node)), 'FACT_VALIDATOR_IMPORT')
    module = ast.Module(body=[node], type_ignores=[])
    namespace = {}
    exec(compile(module, str(common_path), 'exec'), namespace)
    return namespace['fact_items']


def project_fact_container(doc, group, validator):
    require(type(group) is int and group in range(16), 'GROUP_ID')
    original = copy.deepcopy(doc)
    if group < 4:
        require(type(doc) is dict, 'ORIGINAL_CLOSED_CONTAINER_EXPECTED')
        wrapper = doc
    else:
        require(type(doc) is list and len(doc) == 4, 'ORIGINAL_FOUR_DICT_LIST_EXPECTED')
        wrapper = {'group': group, 'items': doc}
    result = validator(wrapper, group)
    require(doc == original and canonical(doc) == canonical(original), 'ITEM_MUTATION')
    return wrapper, result


def tool_sequence(rows, freeze):
    reads = {key(p) for p in freeze['read_whitelist'] + freeze['self_read_whitelist']}
    writes = {key(p) for p in freeze['write_whitelist']}
    updates = {}
    bare = []
    for position, row in enumerate(rows):
        require(row.get('event') != 'result', 'RESULT_INSIDE_SCOPE_PREFIX')
        t = row.get('step_update', {})
        if t.get('step_type') == 'error_message':
            body = {k: v for k, v in t.items() if k not in {'conversation_id', 'step_index', 'state', 'step_type', 'duration_seconds'} and v not in (None, '', {}, []) and not (isinstance(v, str) and not v.strip())}
            require(not body, 'EXPLICIT_ERROR_MESSAGE')
            bare.append({'position': position, 'actual_metadata': t})
        if t.get('step_type') != 'tool':
            continue
        name = t.get('tool_name')
        params = t.get('tool_info', {}).get('parameters', {})
        require(name in ('view_file', 'write_to_file'), 'OUTSIDE_TOOL')
        if name == 'view_file':
            require(set(params) == {'AbsolutePath'} and key(params['AbsolutePath']) in reads, 'OUTSIDE_READ')
            path = params['AbsolutePath']
        else:
            require(set(params) == {'TargetFile'} and key(params['TargetFile']) in writes, 'OUTSIDE_WRITE')
            path = params['TargetFile']
        require(t.get('state') in ('ACTIVE', 'DONE'), 'ERROR_OR_UNFINISHED_TOOL_STATE')
        step = t['step_index']
        updates.setdefault(step, []).append((position, t))
        text = str(t.get('tool_info', {}).get('output', '')).lower()
        require(not any(s in text for s in ('not found', 'cannot read', 'error reading', 'failed to', 'content truncated')), 'TOOL_OUTPUT_FAILURE')
    tools = []
    for step, pair in sorted(updates.items()):
        require(len(pair) == 2 and [t['state'] for _, t in pair] == ['ACTIVE', 'DONE'], 'NON_UNIQUE_ACTIVE_DONE:' + str(step))
        (active, ta), (done, td) = pair
        require(active < done, 'TOOL_STATE_ORDER')
        identity = lambda t: (t['tool_name'], canonical(t['tool_info']['parameters']))
        require(identity(ta) == identity(td), 'ACTIVE_DONE_LITERAL_IDENTITY_DRIFT')
        require(ta.get('conversation_id') == td.get('conversation_id'), 'CONVERSATION_DRIFT')
        params = td['tool_info']['parameters']
        tools.append({'step': step, 'active': active, 'done': done, 'name': td['tool_name'], 'path': key(params.get('AbsolutePath') or params.get('TargetFile')), 'actual': td})
    require(len({t['step'] for t in tools}) == len(tools), 'DUPLICATE_STEP')
    require([t['active'] for t in tools] == sorted(t['active'] for t in tools), 'STEP_ACTIVE_ORDER_DRIFT')
    return tools, bare


def prior_response(rows, active):
    positions = [i for i, row in enumerate(rows[:active]) if row.get('step_update', {}).get('step_type') == 'agent_response' and row['step_update'].get('state') == 'DONE']
    require(bool(positions), 'MISSING_PLANNING_RESPONSE')
    return positions[-1]


def four_barrier(rows, batch, following_write=None):
    require(len(batch) == 4 and len({t['step'] for t in batch}) == 4, 'NOT_FOUR_DISTINCT_IMAGES')
    plans = [prior_response(rows, t['active']) for t in batch]
    require(len(set(plans)) == 1, 'FOUR_IMAGES_NOT_SAME_RESPONSE')
    proof = {'image_steps': [t['step'] for t in batch], 'planning_response_DONE_position': plans[0], 'ACTIVE_positions': [t['active'] for t in batch], 'DONE_positions': [t['done'] for t in batch], 'same_response_actual': True}
    if following_write is not None:
        plan = prior_response(rows, following_write['active'])
        require(max(t['done'] for t in batch) < plan < following_write['active'] < following_write['done'], 'FACT_WRITE_BEFORE_FOUR_DONE_OR_SAME_RESPONSE')
        proof.update(fact_write_step=following_write['step'], fact_planning_response_DONE_position=plan, fact_write_ACTIVE_position=following_write['active'], fact_write_DONE_position=following_write['done'])
    return proof


def full_text_read(tool, path):
    payload = Path(path).read_bytes()
    output = str(tool['actual']['tool_info'].get('output', ''))
    n = re.search(r'(\d+) bytes', output)
    lines = re.search(r'(\d+) lines', output)
    require(len(payload) < 30000 and payload.endswith(b'\n') and b'\r' not in payload, 'TEXT_PAYLOAD_REPRESENTATION')
    require(n and int(n.group(1)) == len(payload) and lines and int(lines.group(1)) == len(payload.split(b'\n')), 'TEXT_BYTES_OR_GO_LF_LINE_COUNT')
    require(not any(s in output.lower() for s in ('truncat', 'not found', 'cannot read', 'failed', 'error')), 'TEXT_TRUNCATED_OR_FAILED')


def reconstruct():
    contract = ROOT / 'plan_review/ROOT20_finite_reference_route_contract_review_v1.json'
    audit_path = CALL / 'w20_completed_scope_audit.json'
    blocker = ROOT / 'teacher_semantic_crosschecks_v1/20_cjibtmSLxQ4_W13.teacher_semantic_crosscheck_v1.json'
    inputs = {'independent_route_contract_review': bind(contract, REVIEW_SHA), 'rejected_original_scope': bind(audit_path, AUDIT_SHA), 'original_crosscheck_blocker': bind(blocker, BLOCKER_SHA)}
    audit = read(audit_path)
    require(audit['status'] == 'REJECT_ACTUAL_SCOPE_KEEP_RAW_NO_RETRY', 'OLD_SCOPE_RECLASSIFICATION_FORBIDDEN')
    for field in ('tool_issues', 'all_raw_tool_state_issues', 'errored_tool_attempts', 'unfinished_tool_attempts', 'reported_nonmedia_errors', 'additional_scope_issues'):
        require(not audit[field], 'ORIGINAL_TRANSPORT_OR_PIXEL_FAILURE:' + field)
    original_window = next(w for w in audit['windows'] if w['job_index'] == 20)
    require(original_window['status'] == 'REJECTED_OR_INCOMPLETE_KEEP_RAW' and original_window['proposal_issues'], 'REJECT_HISTORY_MISSING')
    require([x['group'] for x in original_window['schema_issues']] == list(range(4, 16)), 'UNEXPECTED_OLD_FACT_FAILURE_SCOPE')
    freeze = read(CALL / 'freeze.json')
    index = read(CALL / 'index.json')
    request = read(CALL / 'request.json')
    inputs.update(freeze=bind(CALL / 'freeze.json', request['freeze_sha256']), index=bind(CALL / 'index.json', audit['index_sha256']), request=bind(CALL / 'request.json'))
    require(audit['freeze_sha256'] == inputs['freeze']['sha256'], 'AUDIT_FREEZE_IDENTITY')
    require(request['CLI_after'] == freeze['CLI_after'] == 36 and request['fixed_job_indices'] == freeze['fixed_job_indices'] == [19, 20], 'FIXED_SCOPE')
    require(request['model'] == freeze['model'] == 'gemini-3.8-flash-high' and freeze['global_cap'] == 37 and freeze['timeout_seconds'] == 7200 and freeze['automatic_retry'] is False and request['automatic_retry'] is False, 'FROZEN_ROUTE_DRIFT')
    inputs['original_root_start_gate'] = bind(CALL.parent / 'root_start_admission.json', request['root_start_admission_sha256'])
    frozen_bindings = [bind(p, h) for p, h in freeze['inputs'].items()]
    inputs['full_frozen_input_bindings'] = frozen_bindings
    common_path = CALL.parent / 'common.py'
    require(str(common_path) in freeze['inputs'], 'FACT_VALIDATOR_NOT_FROZEN')
    validator = original_fact_validator(common_path)
    prefix = Path(audit['immutable_prefix']['path']).read_bytes()
    inputs['immutable_prefix'] = bind(audit['immutable_prefix']['path'], audit['immutable_prefix']['sha256'])
    require(len(prefix) == audit['immutable_prefix']['bytes'], 'PREFIX_LENGTH')
    full = (CALL / 'stream.jsonl').read_bytes()
    require(full.startswith(prefix), 'CURRENT_STREAM_PREFIX_DRIFT')
    rows = [json.loads(line) for line in prefix.splitlines()]
    tools, bare = tool_sequence(rows, freeze)
    # Original malformed outputs are immutable values, never overwritten.
    snapshots = {}
    for item in audit['immutable_actual_outputs']:
        orig = bind(item['original_path'], item['sha256'])
        sealed = bind(item['sealed_copy_path'], item['sealed_copy_sha256'])
        require(orig['sha256'] == sealed['sha256'], 'SNAPSHOT_IDENTITY')
        require(key(item['original_path']) not in snapshots, 'DUPLICATE_SNAPSHOT')
        snapshots[key(item['original_path'])] = {'original': orig, 'sealed_copy': sealed}
    prior_scope_path = CALL / 'w19_completed_scope_audit.json'
    prior_scope = read(prior_scope_path)
    inputs['prior19_immutable_scope_binding_for_full_prefix_outputs'] = bind(prior_scope_path)
    require(prior_scope['status'] == 'PASS_IMMUTABLE_ACTUAL_SCOPE_PENDING_ROOT_SEMANTIC', 'PRIOR19_SCOPE_BYTE_BINDING')
    prior_snapshots = {}
    for item in prior_scope['immutable_actual_outputs']:
        orig = bind(item['original_path'], item['sha256'])
        sealed = bind(item['sealed_copy_path'], item['sealed_copy_sha256'])
        require(orig['sha256'] == sealed['sha256'], 'PRIOR19_SNAPSHOT_IDENTITY')
        prior_snapshots[key(item['original_path'])] = {'original': orig, 'sealed_copy': sealed}
    # No successful output/media replay after completion is licensed by recovery.
    post = [json.loads(line) for line in full[len(prefix):].splitlines()]
    require(not any(r.get('step_update', {}).get('step_type') == 'tool' for r in post), 'POST_COMPLETION_TOOL_REPLAY')
    parts = {p['part_id']: p for p in index['text_fragments']}
    expected = []
    required_parts = []
    def add_part(pid):
        p = parts[pid]
        required_parts.append(p)
        expected.extend([('view_file', key(p['path'])), ('write_to_file', key(p['ack_path']))])
    add_part(index['main_fragment_id'])
    require([w['job_index'] for w in index['windows']] == [19, 20], 'INDEX_WINDOWS')
    for w in index['windows']:
        add_part(w['header_fragment_id'])
        for group in w['groups']:
            if group['group'] % 4 == 0:
                add_part(w['native_fragment_ids'][group['group'] // 4])
            expected.extend(('view_file', key(f['path'])) for f in group['frames'])
            expected.append(('write_to_file', key(group['output_path'])))
        expected.append(('view_file', key(w['clip_path'])))
        expected.extend(('view_file', key(f['path'])) for f in w['student_previews'])
        expected.append(('write_to_file', key(w['proposal_path'])))
    require([(t['name'], t['path']) for t in tools] == expected and len(tools) == freeze['expected_core_tool_calls'] == 202, 'FULL_ORDER_OR_UNEXPECTED_TOOL')
    # This actual prefix has no self-reads; reject additions rather than widening
    # an already completed route's whitelist/order under recovery.
    lookup = {(t['name'], t['path']): t for t in tools}
    require(len(lookup) == len(tools), 'REPEATED_MEDIA_OR_OUTPUT')
    require({t['path'] for t in tools if t['name'] == 'write_to_file'} == set(snapshots) | set(prior_snapshots), 'UNBOUND_FULL_PREFIX_WRITTEN_OUTPUT')
    def find(name, path):
        return lookup[(name, key(path))]
    textproof = []
    reads = {key(p) for p in freeze['read_whitelist'] + freeze['self_read_whitelist']}
    for part in required_parts:
        view = find('view_file', part['path'])
        write = find('write_to_file', part['ack_path'])
        full_text_read(view, part['path'])
        actual = read(part['ack_path'])
        expected_ack = read(part['expected_ACK_path'])
        require(actual == expected_ack and key(part['expected_ACK_path']) not in reads and key(part['ack_path']) not in reads, 'ACK_OR_HIDDEN_EXPECTED_READ')
        require(Path(part['path']).read_text(encoding='utf-8').rstrip().endswith(expected_ack['marker']), 'ACK_MARKER')
        response = prior_response(rows, write['active'])
        require(view['active'] < view['done'] < response < write['active'] < write['done'], 'ACK_BEFORE_READ_DONE_OR_SAME_RESPONSE')
        require(tools.index(write) == tools.index(view) + 1, 'ACK_NOT_IMMEDIATE_NEXT_TOOL')
        textproof.append({'part_id': part['part_id'], 'input': bind(part['path'], part['input_sha256']), 'actual_ACK': bind(part['ack_path']), 'expected_ACK': bind(part['expected_ACK_path'], part['expected_ACK_sha256']), 'read_step': view['step'], 'write_step': write['step'], 'read_DONE_position': view['done'], 'distinct_ACK_response_DONE_position': response, 'ACK_ACTIVE_position': write['active']})
    w = index['windows'][-1]
    require(w['job_index'] == 20 and len(w['groups']) == 16 and len(w['native_identity_all64']) == 64 and len(w['student_previews']) == 8, 'WINDOW_COUNTS')
    manifest = read(w['original_source_manifest']['path'])
    inputs['source_manifest'] = bind(w['original_source_manifest']['path'], w['original_source_manifest']['sha256'])
    inputs['native_clock'] = bind(w['original_source_manifest']['native_clock']['path'], w['original_source_manifest']['native_clock']['sha256'])
    clock = read(inputs['native_clock']['path'])
    require(manifest['window_id'] == w['window_id'] and manifest['source_sha256'] == w['original_source_manifest']['source_sha256'] and manifest['role'] == w['role'] == 'locked_evaluation', 'SOURCE_WINDOW_ROLE_IDENTITY')
    inputs['actual_original_source_media'] = bind(manifest['source_path'], manifest['source_sha256'])
    require(manifest['clip_pts_offset_exact'] == w['clip_pts_offset_exact'] == w['original_source_manifest']['clip_pts_offset_exact'], 'CLIP_PTS_OFFSET')
    inputs['original_clip'] = bind(w['original_clip_path'], manifest['clip_sha256'])
    inputs['clip_alias'] = bind(w['clip_path'], manifest['clip_sha256'])
    clock_map = {f['source_ordinal']: f for f in clock}
    require(len(clock_map) == len(clock), 'CLOCK_DUPLICATE_ORDINAL')
    pixel_checks = audit['actual_png_pixel_checks']
    require(len(pixel_checks) == 72, 'EXISTING_PIXEL_PROOF_NOT_COMPLETE')
    pixels = {(p['kind'], p['frame_id']): p for p in pixel_checks}
    require(len(pixels) == 72, 'DUPLICATE_EXISTING_PIXEL_PROOF')
    inputs['existing_RGB_geometry_verifier_source'] = bind(CALL.parent / 'audit.py', freeze['inputs'][str(CALL.parent / 'audit.py')])
    student = read(w['original_student_receipt']['path'])
    inputs['original_student64_processor_receipt'] = bind(w['original_student_receipt']['path'], w['original_student_receipt']['sha256'])
    require(student['status'] == 'PASS_ACTUAL_LOCAL_CPU_NATIVE_PROCESSOR_TENSOR_VIEWS' and student['patch_inverse_exact'] is True and len(student['frames']) == 64 and student['manifest_sha256'] == inputs['source_manifest']['sha256'] and student['window_id'] == w['window_id'], 'STUDENT_PROCESSOR_PROOF')
    require(student['student_width'] == w['student_width'] == 480 and student['student_height'] == w['student_height'] == 352 and student['video_grid_thw'] == [[32, 22, 30]] and student['actual_tensor_shape'] == [21120, 1536], 'FROZEN_STUDENT_GEOMETRY')
    require(student['new_model_calls'] == 0 and student['new_optimizer_updates'] == 0 and student['cuda_initialized'] is False, 'ORIGINAL_CPU_PROOF_TYPE')
    student_frames = {f['frame_id']: f for f in student['frames']}
    require(len(student_frames) == 64, 'STUDENT_DUPLICATE_ID')
    def pixel_binding(kind, f):
        old = pixels[(kind, f['frame_id'])]
        for field, expected_value in [('alias_path', f['path']), ('original_path', f['original_path']), ('png_sha256', f['png_sha256']), ('rgb_pixel_sha256', f['rgb_pixel_sha256']), ('geometry', f['geometry'])]:
            require(old[field] == expected_value, 'EXISTING_PIXEL_PROOF_IDENTITY:' + f['frame_id'] + ':' + field)
        return {'alias': bind(f['path'], f['png_sha256']), 'original': bind(f['original_path'], f['png_sha256']), 'RGB_geometry_exact_reused_from': inputs['rejected_original_scope'], 'existing_successful_pixel_check': old, 'new_pixel_decode': 0}
    bound = []
    containers = []
    barriers = []
    for group in w['groups']:
        number = group['group']
        require(number == len(containers), 'GROUP_ORDER')
        raw = read(group['output_path'])
        require(key(group['output_path']) in snapshots, 'UNSEALED_FACT_OUTPUT')
        wrapper, items = project_fact_container(raw, number, validator)
        batch = [find('view_file', f['path']) for f in group['frames']]
        barrier = four_barrier(rows, batch, find('write_to_file', group['output_path']))
        barriers.append(barrier)
        containers.append({'group': number, 'original_shape': 'closed_group_items_object' if number < 4 else 'bare_four_dict_list', 'original_output': snapshots[key(group['output_path'])], 'derived_container': wrapper, 'payload_value_sha256': hashlib.sha256(canonical(items)).hexdigest(), 'original_item_values_preserved': items == (raw['items'] if number < 4 else raw), 'original_fact_items_passed_after_memory_only_wrapper': True, 'reserialized_bytes_equal_original_NOT_claimed': True})
        for slot, f in enumerate(group['frames']):
            i = number * 4 + slot
            identity = w['native_identity_all64'][i]
            require(f['frame_id'] == identity['frame_id'] == manifest['frames'][i]['frame_id'] == f'F{i:02d}' and f['slot'] == identity['slot'] == slot, 'FRAME_SLOT_ORDER')
            for field in ('source_ordinal', 'global_seconds_exact', 'local_seconds_exact', 'png_sha256', 'rgb_pixel_sha256'):
                require(f[field] == identity[field] == manifest['frames'][i][field], 'MANIFEST_IDENTITY:' + field)
            require(f['geometry'] == identity['geometry'] == [480, 360] and key(f['original_path']) == key(identity['original_path']) == key(manifest['frames'][i]['path']), 'ORIGINAL_PATH_GEOMETRY')
            require(clock_map[f['source_ordinal']]['global_seconds_exact'] == f['global_seconds_exact'] and clock_map[f['source_ordinal']]['local_seconds_exact'] == f['local_seconds_exact'], 'NATIVE_CLOCK_FRAME_IDENTITY')
            require(Fraction(f['global_seconds_exact']) - Fraction(f['local_seconds_exact']) == Fraction(manifest['domain_global_seconds_exact'][0]), 'GLOBAL_LOCAL_ORIGIN')
            sf = student_frames[f['frame_id']]
            for field in ('source_ordinal', 'global_seconds_exact', 'local_seconds_exact'):
                require(sf[field] == f[field], 'STUDENT_NATIVE_IDENTITY:' + field)
            bind(sf['path'], sf['png_sha256'])
            bound.append({'group': number, 'slot': slot, 'identity': identity, 'facts': items[slot], 'identity_generated_by_program': True, 'origin': 'ORIGINAL_ACTUAL_OBSERVATION_LOSSLESS_CONTAINER_PROJECTION_NOT_NEW_TEACHER_OUTPUT', 'raw_fact_output': snapshots[key(group['output_path'])], 'tool_provenance': barrier, 'native_pixel_binding': pixel_binding('native', f), 'actual_student64_identity': sf, 'student_patch_inverse_proof': inputs['original_student64_processor_receipt']})
    effective = []
    for first in (0, 4):
        frames = w['student_previews'][first:first + 4]
        batch = [find('view_file', f['path']) for f in frames]
        proof = four_barrier(rows, batch)
        for f in frames:
            sf = student_frames[f['frame_id']]
            require(all(f[k] == sf[k] for k in ('png_sha256', 'rgb_pixel_sha256', 'source_ordinal', 'global_seconds_exact', 'local_seconds_exact')), 'EFFECTIVE_STUDENT_PROOF')
            pixel_binding('effective', f)
        proof['frames'] = frames
        effective.append(proof)
    clip = find('view_file', w['clip_path'])
    require(barriers[-1]['fact_write_DONE_position'] < clip['active'] < clip['done'] < effective[0]['planning_response_DONE_position'], 'CLIP_ORDER')
    require(max(effective[0]['DONE_positions']) < effective[1]['planning_response_DONE_position'], 'PREVIEW_BATCH_BARRIER')
    proposal_tool = find('write_to_file', w['proposal_path'])
    require(max(effective[1]['DONE_positions']) < prior_response(rows, proposal_tool['active']) < proposal_tool['active'], 'PREVIEW_BEFORE_REJECTED_PROPOSAL_WRITE')
    require(rows[-1]['step_update']['step_index'] == proposal_tool['step'] and rows[-1]['step_update']['state'] == 'DONE', 'PREFIX_NOT_FIRST_PROPOSAL_DONE')
    native_review = ROOT / 'native_reviews/20_cjibtmSLxQ4_W13.native_review.json'
    student_review = ROOT / 'student_reviews/20_cjibtmSLxQ4_W13.independent_student64_review_v1.json'
    n = read(native_review)
    s = read(student_review)
    require(n['teacher_content_received'] is False and n['candidatePredictionExposure'] is False and s['teacher_content_received'] is False and s['candidate_predictions_received'] is False, 'ORIGINAL_BLIND_ATTESTATION')
    require(len(n['frames']) == len(s['student_view_inventory']) == 64 and n['manifest_sha256'] == inputs['source_manifest']['sha256'], 'BLIND_REVIEW_COUNTS_OR_MANIFEST')
    for i, row in enumerate(bound):
        native = n['frames'][i]
        effective_frame = s['student_view_inventory'][i]
        for field in ('frame_id', 'source_ordinal', 'global_seconds_exact', 'local_seconds_exact'):
            require(native[field] == effective_frame[field] == row['identity'][field], 'BLIND_REVIEW_FRAME_IDENTITY:' + field)
        require(native['png_sha256'] == row['identity']['png_sha256'] and effective_frame['png_sha256'] == row['actual_student64_identity']['png_sha256'], 'BLIND_REVIEW_IMAGE_SHA')
    inputs.update(original_blind_native_review=bind(native_review), original_blind_student_review=bind(student_review), original_finite_preteacher_review=bind(ROOT / '20_cjibt_w13_main_preteacher_review_v2.json'))
    # Keep all rejected proposal contents untouched; no defaults, new opinions,
    # new boundary support or student_visibility reinterpretation are generated.
    require(snapshots[key(w['proposal_path'])]['original']['sha256'] == original_window['proposal_sha256'], 'REJECTED_PROPOSAL_ORIGINAL_SHA')
    inputs['original_terminal_history_not_reclassified'] = bind(CALL / 'terminal.json')
    rejected = {'original_scope_status': audit['status'], 'window_status': original_window['status'], 'original_fact_schema_issues': original_window['schema_issues'], 'original_proposal_schema_issues': original_window['proposal_issues'], 'original_proposal': snapshots[key(w['proposal_path'])], 'original_scope_bound_fact_rows': original_window['bound_rows'], 'teacher_proposal_compliance': False, 'teacher_proposal_schema_rejection_preserved': True, 'whole_CLI_not_reclassified': True}
    return {'inputs': inputs, 'rows': bound, 'containers': containers, 'proof': {'ordered_actual_core_count': len(tools), 'all_tool_ACTIVE_DONE_literal_identity_verified': True, 'all_actual_tools_DONE_no_ERROR': True, 'actual_text_ACK_barriers': textproof, 'native_group_four_image_barriers': barriers, 'effective_two_four_image_batches': effective, 'clip_actual_tool': clip, 'bare_nonmedia_error_metadata': bare, 'full_prefix_all_written_outputs': list(prior_snapshots.values()) + list(snapshots.values()), 'new_decodes': 0, 'existing_RGB_geometry_checks_exact_referenced': 72, 'actual_student64_patch_inverse_receipt_exact_referenced': True}, 'rejected_history': rejected}


def run():
    target = OWN / 'observation_receipt.json'
    require(not target.exists(), 'ALREADY_COMPLETE_NO_REPEAT')
    for name in ('derived_fact_containers.json', 'bound_fact_rows64.json', 'independent_cpu_proof.json', 'rejected_teacher_history.json'):
        require(not (OWN / name).exists(), 'PARTIAL_OUTPUT_PRESENT_NO_OVERWRITE:' + name)
    data = reconstruct()
    # All checks complete before any successful artifact is serialized.
    references = {}
    for name, value in [('derived_fact_containers.json', data['containers']), ('bound_fact_rows64.json', data['rows']), ('independent_cpu_proof.json', data['proof']), ('rejected_teacher_history.json', data['rejected_history'])]:
        references[name] = save(OWN / name, value)
    receipt = {'status': 'OBSERVATION_ONLY_PENDING_ROOT_NEW_SEMANTICS', 'utc': datetime.now(timezone.utc).isoformat(), 'window_id': 'cjibtmSLxQ4:SLOT6:13', 'global_CLI': 36, 'original_pngs_delivered': 64, 'effective_pngs_delivered': 8, 'native_clip_actual_view_tool_delivered': True, 'native_video_semantic_view_by_this_CPU_script': False, 'actual_student_frames': 64, 'inputs': data['inputs'], 'artifacts': references, 'verifier_source': bind(__file__), 'independent_CPU_observation_provenance_reconstructed': True, 'original_items_preserved': 64, 'original_list_items_wrapped': 48, 'original_closed_object_items_retained': 16, 'RGB_geometry_proof_mode': 'EXACT_SHA_REUSE_OF_SUCCESSFUL_72_PNG_CPU_PIXEL_CHECKS_AND_ORIGINAL_64_PROCESSOR_PATCH_INVERSE_NO_NEW_DECODE', 'original_teacher_scope_still_REJECT': True, 'original_teacher_proposal_still_REJECT': True, 'teacher_instruction_compliance_PASS': False, 'semantic_truth_or_reference_admission': False, 'new_reference_geometry_review': 'PENDING_ROOT_SEPARATE_REFERENCE', 'new_ROOT_complete_semantic_review': 'PENDING', 'new_blind_review': False, 'consequential_F15_F18_UNKNOWN_not_cleared': True, 'training_admitted': False, 'quality_gate_passed': False, 'whole_CLI36_PASS': False, 'new_model_calls': 0, 'new_processor_calls': 0, 'new_source_decodes': 0, 'new_png_decodes': 0, 'new_image_views': 0, 'new_boundary_or_label_changes': 0, 'original_costs_and_rejections_preserved': True}
    return save(target, receipt)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        print(json.dumps(run(), ensure_ascii=False))
    except Exception:
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
        failure = {'status': 'FAILED_OBSERVATION_RECONSTRUCTION_NO_ACCEPTANCE', 'utc': datetime.now(timezone.utc).isoformat(), 'verifier_source': bind(__file__), 'traceback': traceback.format_exc(), 'original_scope_rejection_preserved': True, 'training_admitted': False, 'new_model_calls': 0, 'new_decoder_calls': 0}
        save(OWN / ('failure_' + stamp + '.json'), failure)
        raise
