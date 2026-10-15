"""Complete-window silver admission. Evidence fields are not semantic truth proofs."""
from pathlib import Path
from fractions import Fraction as F
import json,hashlib
from quality_contract import reference,duration,schedule

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read_bound(row):
    path=Path(row['path'])
    if not path.is_file() or sha(path)!=row['sha256']:raise ValueError('Evidence byte identity differs: '+str(path))
    return json.loads(path.read_text(encoding='utf-8-sig'))

def verify_window(record,planned):
    """Accept only a separately adjudicated complete list, never teacher raw alone."""
    w=planned['window'];a,b=F(w['domain_start_exact']),F(w['domain_end_exact'])
    if record['window_id']!=w['window_id'] or record['source_sha256']!=w['source_sha256']:raise ValueError('Window identity differs')
    if record.get('reference_kind')!='FINITE_OBSERVATION_SILVER_EDITING_ADVICE_NOT_GOLD':raise ValueError('Reference scope not declared')
    d,k,n,u=reference([(a,b)],record['keep_global_exact'],record['no_global_exact'],record['unknown_global_exact'])
    evidence={name:read_bound(row) for name,row in record['evidence'].items()}
    if not {'teacher_observation_audit','blind_initial','blind_student_visibility','student_processor','final_main_review'}<=set(evidence):raise ValueError('Required observations/reviews absent')
    obs=evidence['teacher_observation_audit'];student=evidence['student_processor'];blind=evidence['blind_initial']
    if obs.get('original_pngs_delivered')!=64 or obs.get('effective_pngs_delivered')!=8 or not obs.get('native_video_delivered'):raise ValueError('Explicit media delivery incomplete')
    if obs.get('tool_issues') or obs.get('proposal_geometry_identity_issues'):raise ValueError('Unresolved teacher observation contract')
    if student.get('patch_inverse_exact') is not True or len(student.get('frames',[]))!=64:raise ValueError('Actual student view evidence incomplete')
    if blind.get('blind_attestation',{}).get('teacher_content_received') is not False:raise ValueError('Initial blind review exposed to proposal')
    # These assertions bind an accountable review; they do not certify model attention or human gold.
    reviewed=record.get('main_review_assertions',{})
    required=('direct_visible_facts_checked','all_NO_ranges_explicitly_reviewed','no_audio_content_invented',
              'necessary_preparation_and_result_considered','no_artificial_event_merging',
              'no_candidate_prediction_exposure_before_reference_freeze','student_visibility_checked')
    if not all(reviewed.get(key) is True for key in required):raise ValueError('Main semantic adjudication incomplete')
    for boundary in record.get('boundary_decisions',[]):
        if F(boundary['uncertainty_end_exact'])-F(boundary['uncertainty_start_exact'])>F('0.5'):raise ValueError('Unresolved boundary uncertainty exceeds frozen allowance')
        if not boundary.get('inside_evidence') or not boundary.get('outside_evidence_or_domain_boundary'):raise ValueError('Boundary lacks reviewed support')
    if record.get('training_admitted'):
        if u or record.get('consequential_unknowns'):raise ValueError('UNKNOWN cannot enter complete JSON SFT')
        if record.get('student_observable_complete_target') is not True:raise ValueError('Complete target not observable to student')
        if len(record.get('events',[]))>5 or len(k)>5:raise ValueError('Full event reference not expressible by fixed grammar')
        if (not k)!=(record.get('explicit_no_highlight') is True):raise ValueError('Empty semantics differ')
        if not record.get('all_target_boundaries_adjudicated'):raise ValueError('Unresolved target boundaries')
    return dict(window_id=w['window_id'],role=planned['role'],source_group=planned['source_group'],
        admitted=record.get('training_admitted') is True,known_keep_seconds=duration(k),known_no_seconds=duration(n),unknown_seconds=duration(u))

def training_schedule(plan,records):
    expected={j['window']['window_id']:j for j in plan['jobs']}
    if set(records)!=set(expected):raise ValueError('All 24 denominators must be recorded, including pending/rejected')
    accepted=[]
    for key,row in records.items():
        if row.get('training_admitted'):
            job=expected[key]
            if job['role']!='train':raise ValueError('Evaluation source in training')
            verified=verify_window(row,job)
            accepted.append((key,job['source_group'],verified['known_keep_seconds']>0))
    if len({g for _,g,p in accepted if p})<2:raise ValueError('Positives from fewer than two source groups')
    accepted.sort()
    s=schedule([g for _,g,_ in accepted])
    return dict(window_ids=[k for k,_,_ in accepted],**s)
