"""Independently accept completed window supply, then accountable editorial reference."""
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime,timezone
import json,hashlib,sys
from PIL import Image
ROOT=Path(__file__).resolve().parent; OLD=ROOT.parent/'slot6_silver24_v1'; CALL=ROOT/'teacher_expansion/capacity_v3_network/call01'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bound(p):return dict(path=str(p),sha256=sha(p))
def save(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def norm(p):return str(Path(p)).lower()
auditpath=CALL/'w04_completed_scope_audit.json';audit=read(auditpath)
assert audit['issues']==[] and audit['parent_CLI_terminal_present'] is False
for key in ['proposal','program_bound_facts','stream_prefix','freeze','index','request']:
    assert sha(Path(audit[key]['path']))==audit[key]['sha256']
freeze=read(CALL/'freeze.json')
for p,h in freeze['inputs'].items():assert sha(Path(p))==h
index=read(CALL/'index.json')['windows'][0]; assert index['job_index']==4
steps={}
for line in Path(audit['stream_prefix']['path']).read_text(encoding='utf-8-sig').splitlines():
    d=json.loads(line)
    if d.get('event')=='step_update':
        s=d['step_update']; steps[s['step_index']]=s
tools=[]
for ix,s in sorted(steps.items()):
    if s['step_type']!='tool':continue
    assert s['state']=='DONE' and s['tool_name'] in ['view_file','write_to_file']
    args=s['tool_info']['parameters']; p=args.get('AbsolutePath',args.get('TargetFile'));assert p
    tools.append((s['tool_name'],norm(p)))
expected=[('view_file',norm(CALL/'index.json'))]
for group in index['groups']:
    for f in group['frames']:
        assert sha(Path(f['path']))==f['png_sha256']
        with Image.open(f['path']) as image:assert list(image.size)==f['geometry']
        expected.append(('view_file',norm(f['path'])))
    expected.append(('write_to_file',norm(group['output_path'])))
expected.append(('view_file',norm(index['clip_path'])))
for f in index['student_previews']:
    assert sha(Path(f['path']))==f['png_sha256']
    with Image.open(f['path']) as image:assert list(image.size)==f['geometry']
    expected.append(('view_file',norm(f['path'])))
expected.append(('write_to_file',norm(index['proposal_path'])))
assert tools==expected and len(tools)==91
facts=read(Path(audit['program_bound_facts']['path']))['rows'];assert len(facts)==64
for row in facts:
    group=index['groups'][row['group']]; f=group['frames'][row['slot']]
    assert row['source_ordinal']==f['source_ordinal'] and row['png_sha256']==f['png_sha256']
    assert row['raw_output_sha256']==sha(Path(group['output_path'])) and row['identity_generated_by_program'] is True
proposal=read(Path(index['proposal_path']));cursor=F(0)
for seg in proposal['segments']:
    assert F(str(seg['start_seconds']))==cursor and seg['decision'] in ['KEEP','NO','UNKNOWN'];cursor=F(str(seg['end_seconds']))
assert cursor==30
observation_path=ROOT/'04_ht5_w02_lawful_observation_completion.json'
save(observation_path,dict(status='PASS_ROOT_INDEPENDENT_COMPLETED_WINDOW_MEDIA_SCOPE_WITH_ERROR_METADATA_PRESERVED',utc=datetime.now(timezone.utc).isoformat(),window_id=index['window_id'],original_pngs_delivered=64,effective_pngs_delivered=8,native_video_delivered=True,tool_issues=[],proposal_geometry_identity_issues=[],ordered_tool_count=91,
 prefix_audit=bound(auditpath),stream_prefix=audit['stream_prefix'],proposal=audit['proposal'],program_bound_facts=audit['program_bound_facts'],parent_CLI_terminal_present=False,parent_job_cost='PENDING_ACTUAL_TERMINAL',
 error_message_steps=audit['error_message_steps'],error_body_unavailable_in_stream=True,error_not_rewritten_as_success=True,whole_CLI_status_not_inferred=True,
 teacher_semantic_proposal_not_truth=True,semantic_rejections=['Static sample alone does not prove stationary vehicle. F61 closed-door claim is not used. Root does not infer rescue, towing force or audio absence from teacher narration.'],new_optimizer_updates=0))
name='04_HT5vyqe0Xaw_W02';obs=OLD/'observations'/name;m=read(obs/'manifest.json');job=read(OLD/'source_window_plan.json')['jobs'][4]
np=ROOT/'native_reviews'/(name+'.native_review.json');sp=ROOT/'student_reviews'/(name+'.independent_student64_review_v1.json');n=read(np);s=read(sp)
assert n['teacher_content_received'] is False and n['candidatePredictionExposure'] is False and n['student_content_received'] is False
blindpath=ROOT/'04_ht5_w02_independent_native_blind_binding.json'
save(blindpath,dict(status='BOUND_REAL_PRETEACHER_NATIVE64_REVIEW_NOT_NEW_IMAGE_OBSERVATION',window_id=m['window_id'],blind_attestation=dict(teacher_content_received=False,candidate_prediction_received=False,student_content_received=False),sealed_native_review=bound(np),actual_native_images=64,root_not_blind=True,training_admitted=False))
prepath=ROOT/'04_ht5_w02_main_preteacher_review.json';pre=read(prepath);extra=read(ROOT/'boundary_ht5_w02_end_v1/main_observation.json')
assert extra['root_actually_viewed_image'] is True
pts=[F(f['local_seconds_exact']) for f in m['frames']];endpt=F(extra['reviewed_local_bracket_exact'][1]);a=(pts[30]+pts[31])/2;b=(pts[39]+endpt)/2
boundaries=[dict(uncertainty_start_exact=str(pts[30]),uncertainty_end_exact=str(pts[31]),inside_evidence='F31',outside_evidence_or_domain_boundary='F30 partial tire view'),dict(uncertainty_start_exact=str(pts[39]),uncertainty_end_exact=str(endpt),inside_evidence='F39',outside_evidence_or_domain_boundary='O002361 repeats established representative shot')]
assert all(F(x['uncertainty_end_exact'])-F(x['uncertainty_start_exact'])<=F('0.5') for x in boundaries)
events=pre['decision']['events'];events[0]['local']=[str(a),str(b)]
mainpath=ROOT/'04_ht5_w02_final_main_review.json'
main=dict(window_id=m['window_id'],utc=datetime.now(timezone.utc).isoformat(),preteacher_main_review=bound(prepath),teacher_observation=bound(observation_path),teacher_proposal=audit['proposal'],independent_native_initial=bound(np),student64_review=bound(sp),boundary_actual_observation=bound(ROOT/'boundary_ht5_w02_end_v1/main_observation.json'),
 actual_observation_scope='Delegated independent native and student reviewers actually inspected each64. Root read all per-image facts and directly inspected 5 native images, 2 effective images, plus one separately registered interior native image. Root does not claim direct64 inspection.',
 differences_adjudicated=['Teacher and student initial NO both depend on absence of an action event. Root retains a short clear typical image of complete vehicle/door/forest-road relation under the pre-registered visual editing definition, without inferring action or rescue. Native independent initial KEEP supports that typical-image interpretation. All initial judgments remain unchanged.',
 'Teacher proposal uncertainty ranges are not copied into the target. Root exact observed onset F30/F31 and actual interior end F39/O002361 are independently reviewed editorial ranges, not measured scene cuts. Short target is not selected to satisfy a positive-source quota.',
 'Source-specific unseen movement/audio and semantics remain outside this finite visual target; no candidate prediction has been exposed.'],
 events=events,boundary_decisions=boundaries,all_NO_ranges=[dict(local=['0',str(a)],reason=pre['decision']['no_ranges'][0]['reason']),dict(local=[str(b),'30'],reason=pre['decision']['no_ranges'][1]['reason'])],
 student_observable_complete_target=True,consequential_unknowns=[],no_candidate_prediction_exposure=True,main_exposed_not_blind=True,human_gold=False)
save(mainpath,main);start=F(job['window']['domain_start_exact'])
record=dict(window_id=m['window_id'],source_sha256=m['source_sha256'],reference_kind='FINITE_OBSERVATION_SILVER_EDITING_ADVICE_NOT_GOLD',keep_global_exact=[[str(start+a),str(start+b)]],no_global_exact=[[str(start),str(start+a)],[str(start+b),str(start+30)]],unknown_global_exact=[],
 evidence=dict(teacher_observation_audit=bound(observation_path),blind_initial=bound(blindpath),blind_student_visibility=bound(sp),student_processor=bound(obs/'student_views/receipt.json'),final_main_review=bound(mainpath)),
 main_review_assertions={k:True for k in ['direct_visible_facts_checked','all_NO_ranges_explicitly_reviewed','no_audio_content_invented','necessary_preparation_and_result_considered','no_artificial_event_merging','no_candidate_prediction_exposure_before_reference_freeze','student_visibility_checked']},
 boundary_decisions=boundaries,events=events,consequential_unknowns=[],explicit_no_highlight=False,all_target_boundaries_adjudicated=True,student_observable_complete_target=True,training_admitted=True,
 reason='Complete separately adjudicated finite visual editing advice. Real completed supply is independently verified even though parent CLI remains active and error metadata is preserved. Not gold or unseen generalization.',supplement_provenance=dict(protocol=bound(ROOT/'PROTOCOL.md'),erratum=bound(ROOT/'PROTOCOL_ERRATUM_W11_AND_BUDGET.md'),new_optimizer_updates=0))
sys.path.insert(0,str(OLD));from silver_contract import verify_window
verified=verify_window(record,job);refpath=ROOT/'04_ht5_w02_complete_reference.json';save(refpath,record)
save(ROOT/'04_ht5_w02_admission.json',dict(status='PASS_COMPLETE_FINITE_VISUAL_REFERENCE_NOT_TRAINING_BATCH_ADMISSION',verified={k:str(v) for k,v in verified.items()},reference=bound(refpath),new_optimizer_updates=0))
print(json.dumps(dict(window=m['window_id'],keep_seconds=str(verified['known_keep_seconds']),no_seconds=str(verified['known_no_seconds']),training_batch_admitted=False)))
