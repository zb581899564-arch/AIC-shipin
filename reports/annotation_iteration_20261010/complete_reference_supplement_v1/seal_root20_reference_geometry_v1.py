"""Validate new ROOT finite reference geometry; never reclassify teacher output."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from fractions import Fraction as F
from pathlib import Path

R = Path(__file__).parent
OLD = R.parent / 'slot6_silver24_v1'
sys.path.insert(0, str(OLD))
from quality_contract import reference

def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p): return {'path': str(p), 'sha256': sha(p)}
def bound(b):
    assert sha(b['path']) == b['sha256']
    return read(b['path'])
def save_new(p, value):
    serialized = json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    with p.open('x', encoding='utf-8', newline='\n') as f: f.write(serialized)

draft_path = R / '20_cjibt_w13_root_finite_decision_draft_v1.json'
media_path = R / 'root20_observation_recovery_v1/observation_receipt_v2.json'
review_path = R / 'plan_review/root20_observation_v2_independent_narrow_review_v1.json'
draft = read(draft_path)
media = read(media_path)
review = read(review_path)
assert draft['status'] == 'ROOT_FINITE_SEMANTIC_DECISION_PENDING_NEW_OBSERVATION_GEOMETRY'
assert media['status'] == 'OBSERVATION_ONLY_PENDING_ROOT_NEW_SEMANTICS'
assert sha(media_path) == '677e8755b272d5bd0092c8a3b6dbe6933635aa44e217be037e4877c723adca79'
assert sha(review_path) == '480349e4461d5608b8045f2fde51055433c7d4ed37f3735517e46c3323abc672'
assert media['original_teacher_scope_still_REJECT'] and media['original_teacher_proposal_still_REJECT']
assert not media['teacher_instruction_compliance_PASS'] and not media['whole_CLI36_PASS']
assert media['original_pngs_delivered'] == 64 and media['effective_pngs_delivered'] == 8
assert media['native_clip_actual_view_tool_delivered'] and media['actual_student_frames'] == 64
assert media['original_items_preserved'] == 64 and media['original_list_items_wrapped'] == 48
assert media['new_reference_geometry_review'] == 'PENDING_ROOT_SEPARATE_REFERENCE'
artifacts = {key: bound(value) for key,value in media['artifacts'].items()}
rows = artifacts['bound_fact_rows64_v2.json']
proof = artifacts['independent_cpu_proof_v2.json']
history = artifacts['rejected_teacher_history_v2.json']
assert proof['ordered_actual_core_count'] == 202
assert proof['all_tool_ACTIVE_DONE_literal_identity_verified'] and proof['all_actual_tools_DONE_no_ERROR']
assert proof['existing_RGB_geometry_checks_exact_referenced'] == 72
assert proof['actual_student64_patch_inverse_receipt_exact_referenced']
pre = bound(draft['preteacher_main_review'])
pixels = bound(draft['root_actual_postteacher_pixels'])
native = bound(draft['independent_native64'])
student = bound(draft['independent_student64'])
assert not pre['teacher_content_read'] and not draft['candidate_prediction_exposure']
assert draft['root_read_all64_teacher_facts'] and draft['root_read_all64_native_and_student_facts'] and draft['all_NO_ranges_reviewed']
assert pixels['actual_new_native_pngs_viewed'] == 11 and pixels['actual_new_student_pngs_viewed'] == 6
assert draft['window_id'] == media['window_id'] == native['window_id'] == student['window_id'] == pre['window_id']
plan = read(OLD / 'source_window_plan.json')
job = next(j for j in plan['jobs'] if j['window']['window_id'] == draft['window_id'])
assert job['role'] == 'locked_evaluation'
window = job['window']
assert F(window['domain_end_exact']) - F(window['domain_start_exact']) == 30
assert native['source_sha256'] == window['source_sha256']
receipt = bound(media['inputs']['original_student64_processor_receipt'])
assert receipt['patch_inverse_exact'] and len(receipt['frames']) == 64
student_frames = {f['frame_id']: f for f in receipt['frames']}
assert len(rows) == len(native['frames']) == len(student['student_view_inventory']) == 64
for index, row in enumerate(rows):
    nf = native['frames'][index]
    sf = student['student_view_inventory'][index]
    identity = row['identity']
    assert row['group'] == index//4 and row['slot'] == index%4 and row['identity_generated_by_program']
    assert identity['frame_id'] == nf['frame_id'] == sf['frame_id'] == f'F{index:02d}'
    assert F(identity['global_seconds_exact']) - F(window['domain_start_exact']) == F(identity['local_seconds_exact'])
    assert 0 <= F(identity['local_seconds_exact']) <= 30
    for key in ('source_ordinal','global_seconds_exact','local_seconds_exact','png_sha256','rgb_pixel_sha256'):
        assert identity[key] == nf[key]
    for key in ('source_ordinal','global_seconds_exact','local_seconds_exact','png_sha256','rgb_pixel_sha256'):
        assert sf[key] == student_frames[sf['frame_id']][key]
    assert sha(nf['path']) == nf['png_sha256'] and sha(sf['path']) == sf['png_sha256']
assert draft['selected_preteacher_event_indices'] == [0,1,2]
assert draft['consequential_unknowns'] == pre['consequential_unknown_sample_ranges']
assert [(u['first'],u['last']) for u in draft['consequential_unknowns']] == [(15,18)]
event_checks = []
expected_keeps = []
for number in draft['selected_preteacher_event_indices']:
    event = pre['events'][number]
    first,last = event['first'],event['last']
    start = event['editing_start_range_local_exact']
    end = event['editing_end_range_local_exact']
    assert [F(v) for v in start] == [F(native['frames'][i]['local_seconds_exact']) for i in (first-1,first)]
    assert [F(v) for v in end] == [F(native['frames'][i]['local_seconds_exact']) for i in (last,last+1)]
    assert all(0 <= F(a) <= F(b) <= 30 and F(b)-F(a) <= F('0.5') for a,b in (start,end))
    keep = [str((F(a)+F(b))/2) for a,b in (start,end)]
    expected_keeps.append(keep)
    event_checks.append({'event_index':number,'native_and_actual_student_frame_ids':[f'F{i:02d}' for i in range(first,last+1)],'start_pair':start,'end_pair':end,'local_editing_midpoint_pair':keep,'physical_complete_action_boundary_claimed':False})
assert draft['keep_local_exact'] == expected_keeps
assert draft['unknown_local_exact'] == [[expected_keeps[0][1],expected_keeps[1][0]]]
reference([(F(0),F(30))],draft['keep_local_exact'],draft['no_local_exact'],draft['unknown_local_exact'])
actual_scope = bound(draft['original_rejected_scope'])
assert actual_scope['status'] == 'REJECT_ACTUAL_SCOPE_KEEP_RAW_NO_RETRY'
assert not any(actual_scope[k] for k in ('tool_issues','additional_scope_issues','errored_tool_attempts','unfinished_tool_attempts','reported_nonmedia_errors'))
assert actual_scope['windows'][-1]['schema_issues'] and actual_scope['windows'][-1]['proposal_issues']
observation = {
    'status':'PASS_NEW_ROOT_FINITE_REFERENCE_GEOMETRY_WITH_REUSED_ACTUAL_MEDIA_OLD_TEACHER_REJECTED',
    'utc':datetime.now(timezone.utc).isoformat(),'window_id':draft['window_id'],
    'original_pngs_delivered':64,'effective_pngs_delivered':8,'native_video_delivered':True,
    'tool_issues':[], 'proposal_geometry_identity_issues':[],
    'proposal_geometry_identity_scope':'NEW_ROOT_FINITE_REFERENCE_ONLY_NOT_REJECTED_TEACHER_PROPOSAL',
    'new_finite_root_decision':bind(draft_path),'new_actual_root_pixel_review':bind(draft['root_actual_postteacher_pixels']['path']),
    'media_only_recovery':bind(media_path),'media_recovery_independent_review':bind(review_path),
    'original_rejected_teacher_scope':draft['original_rejected_scope'],
    'original_rejected_teacher_proposal':draft['original_rejected_teacher_proposal'],
    'original_rejection_history':media['artifacts']['rejected_teacher_history_v2.json'],
    'old_scope_schema_issues_preserved':actual_scope['windows'][-1]['schema_issues'],
    'old_scope_proposal_issues_preserved':actual_scope['windows'][-1]['proposal_issues'],
    'original_teacher_scope_pass':False,'original_teacher_proposal_pass':False,'whole_CLI36_pass':False,
    'new_reference_geometry_checks':event_checks,'full_exact30_partition_verified':True,
    'original_15_18_consequential_UNKNOWN_preserved':True,'root_exposed_not_new_blind':True,
    'training_admitted':False,'new_model_calls':0,'new_optimizer_updates':0,'new_video_decode':0,
    'verifier_source':bind(__file__),
}
observation_path = R/'20_cjibt_w13_root_new_reference_geometry_v1.json'
save_new(observation_path,observation)
decision = {key:draft[key] for key in ('window_id','selected_preteacher_event_indices','unknown_local_exact','consequential_unknowns','root_read_all64_teacher_facts','root_read_all64_native_and_student_facts','all_NO_ranges_reviewed','candidate_prediction_exposure','differences_adjudicated','actual_root_observation_scope','reference_scope_and_reason')}
decision.update(status='ROOT_SEMANTIC_EVALUATION_ADJUDICATION_COMPLETE',utc=datetime.now(timezone.utc).isoformat(),evidence={
    'preteacher_main_review':draft['preteacher_main_review'],'teacher_observation_audit':bind(observation_path),
    'root_actual_postteacher_pixels':draft['root_actual_postteacher_pixels'],
    'original_rejected_teacher_proposal':draft['original_rejected_teacher_proposal'],
    'original_rejected_teacher_bound_fact_audit':draft['original_rejected_scope'],
    'new_root_finite_semantic_draft':bind(draft_path),'observation_recovery_independent_review':bind(review_path),
    'derived_fact_rows':bind(media['artifacts']['bound_fact_rows64_v2.json']['path']),
})
decision_path=R/'20_cjibt_w13_root_eval_decision_v1.json'
save_new(decision_path,decision)
print(json.dumps({'observation':bind(observation_path),'decision':bind(decision_path),'reference_admitted':False},ensure_ascii=False))
