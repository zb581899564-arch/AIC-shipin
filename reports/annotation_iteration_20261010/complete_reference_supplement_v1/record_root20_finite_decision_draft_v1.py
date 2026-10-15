"""Record ROOT's actual finite semantic judgment; admission still requires proof."""
import hashlib
import json
from datetime import datetime, timezone
from fractions import Fraction as F
from pathlib import Path

R = Path(__file__).parent
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p): return {'path': str(p), 'sha256': sha(p)}
prepath = R / '20_cjibt_w13_main_preteacher_review_v2.json'
pixelpath = R / '20_cjibt_w13_root_actual_postteacher_pixels_v1.json'
pre = read(prepath)
pixels = read(pixelpath)
assert pre['window_id'] == pixels['window_id'] == 'cjibtmSLxQ4:SLOT6:13'
assert not pre['teacher_content_read'] and not pixels['candidate_prediction_exposure']
assert pixels['root_read_all64_teacher_facts'] and pixels['root_read_all64_native_and_student_facts']
assert pixels['actual_new_native_pngs_viewed'] == 11 and pixels['actual_new_student_pngs_viewed'] == 6
selected = [0, 1, 2]
keeps = []
for index in selected:
    event = pre['events'][index]
    ranges = [event['editing_start_range_local_exact'], event['editing_end_range_local_exact']]
    assert all(0 <= F(a) <= F(b) <= 30 and F(b)-F(a) <= F('0.5') for a,b in ranges)
    keeps.append([str((F(a)+F(b))/2) for a,b in ranges])
unknown = [[keeps[0][1], keeps[1][0]]]
assert F(unknown[0][0]) < F(unknown[0][1])
marked = sorted([[F(a), F(b)] for a,b in keeps+unknown])
cursor = F(0)
no = []
for lo,hi in marked:
    assert cursor <= lo < hi <= 30
    if cursor < lo: no.append([str(cursor), str(lo)])
    cursor = hi
if cursor < 30: no.append([str(cursor), '30'])
document = {
    'status': 'ROOT_FINITE_SEMANTIC_DECISION_PENDING_NEW_OBSERVATION_GEOMETRY',
    'utc': datetime.now(timezone.utc).isoformat(), 'window_id': pre['window_id'],
    'selected_preteacher_event_indices': selected,
    'keep_local_exact': keeps, 'unknown_local_exact': unknown, 'no_local_exact': no,
    'consequential_unknowns': pre['consequential_unknown_sample_ranges'],
    'preteacher_main_review': bind(prepath), 'root_actual_postteacher_pixels': bind(pixelpath),
    'independent_native64': pre['independent_native64'], 'independent_student64': pre['independent_student64'],
    'original_rejected_teacher_proposal': pixels['original_rejected_teacher_proposal'],
    'original_rejected_scope': pixels['original_rejected_scope'],
    'root_read_all64_teacher_facts': True, 'root_read_all64_native_and_student_facts': True,
    'all_NO_ranges_reviewed': True, 'candidate_prediction_exposure': False,
    'differences_adjudicated': [
        'Keep only the three finite targets chosen before teacher exposure: local elbow flexion and return; visible upright/tilted-to-low long-object relation; local approach to ledge and partial body behind window frame. No extra target is derived from the descriptive rejected proposal.',
        'F12/F14 and actual studentF14 support local flexion/extension rather than mere continued hanging. Complete initial grasp and release are still unknown outside this finite target.',
        'F15..18 remains consequential UNKNOWN. Original native calls the small form inverted while student and teacher descriptions differ; actualF17 native/student does not settle a complete handstand or precise hidden body/object relation.',
        'F24/F27/F28 native and actual student images support upright/tilted/low long-object position change. TeacherF26..28 running/sliding/rolling and F20 force/stretch are not adopted. Causality, intent, actor contact, authenticity and complete destruction are not asserted.',
        'F33/F34 supports high ledge stance and upper body behind frame with legs still outside. Teacher successful complete entry is rejected; full entry outcome stays unknown outside the limited relation target.',
        'All NO bands were reviewed: ordinary sand-ground movement0..2; repeated dark face3..9; indoor occlusion/ordinary face35..42; residential walking43..58; ordinary doorway interaction59..63. Subtitle/children/voice do not create new highlights.',
        'Exact editing boundaries are the original preteacher midpoint choices with each uncertainty range <=0.5s; they are not measured cuts or complete physical action boundaries. Adjacent independent targets remain separate events. No new boundary request, epsilon, target extension or UNKNOWN deletion.',
        'Actual student means the frozen Qwen processor64 input, with teacher effective8 and independent student64 review. The classroom-student statement is rejected. ROOT is exposed; genuine earlier blind reviews retain their original attestations.',
        'Original malformed proposal, schema errors, scope REJECT and whole36 REJECT remain authoritative for the old run. This new ROOT finite semantic judgment does not make that teacher instruction-compliant or release CLI37/training.',
    ],
    'actual_root_observation_scope': {
        'prior_native_sample_indices': pre['root_actually_viewed_native_samples'],
        'prior_student_sample_indices': pre['root_actually_viewed_student_samples'],
        'additional_postteacher_native_samples': [12,14,17,24,27,28,33,34,42,57,61],
        'additional_postteacher_student_samples': [14,17,24,27,28,34],
        'read_native_static_facts': 64, 'read_student_static_facts': 64, 'read_teacher_static_facts': 64,
        'root_direct64_image_review': False, 'root_native_video_view': False, 'root_not_blind': True,
    },
    'reference_scope_and_reason': 'Locked evaluation finite visual editorial silver only. Three preregistered visible local targets and all ordinary NO are independently adjudicated; forest ambiguity15..18 remains UNKNOWN. Not full physical action truth, human gold, blind generalization, training or official quality.',
    'new_model_calls': 0, 'new_optimizer_updates': 0, 'training_admitted': False,
    'reference_admitted': False,
}
destination = R / '20_cjibt_w13_root_finite_decision_draft_v1.json'
text = json.dumps(document, ensure_ascii=False, indent=2) + '\n'
with destination.open('x', encoding='utf-8', newline='\n') as f: f.write(text)
print(json.dumps(bind(destination), ensure_ascii=False))
