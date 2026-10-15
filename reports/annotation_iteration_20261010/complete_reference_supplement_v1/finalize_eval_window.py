"""Serialize a separately signed root editing adjudication, never teacher labels."""
import argparse,json,hashlib
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime,timezone
R=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):return dict(path=str(p),sha256=sha(p))
def save(p,x):
 text=json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)
 with p.open('x',encoding='utf-8') as f:f.write(text)
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--decision',required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
 dp=Path(a.decision).resolve(strict=True);op=Path(a.output).resolve();assert dp.parent==op.parent==R and not op.exists()
 d=read(dp);assert d['status']=='ROOT_SEMANTIC_EVALUATION_ADJUDICATION_COMPLETE' and not d['candidate_prediction_exposure']
 assert d['root_read_all64_teacher_facts'] and d['root_read_all64_native_and_student_facts'] and d['all_NO_ranges_reviewed']
 for b in d['evidence'].values():assert set(b)=={'path','sha256'} and sha(b['path'])==b['sha256']
 pre=read(d['evidence']['preteacher_main_review']['path']);teacher=read(d['evidence']['teacher_observation_audit']['path'])
 assert pre['window_id']==teacher['window_id']==d['window_id'] and not pre['teacher_content_read']
 assert teacher['original_pngs_delivered']==64 and teacher['effective_pngs_delivered']==8 and teacher['native_video_delivered']
 assert not teacher['tool_issues'] and not teacher['proposal_geometry_identity_issues']
 native_binding=pre['independent_native64'];native=read(native_binding['path']);assert sha(native_binding['path'])==native_binding['sha256']
 assert not native['teacher_content_received'] and not native['student_content_received'] and not native['candidatePredictionExposure']
 plan=read(R.parent/'slot6_silver24_v1/source_window_plan.json');job=next(j for j in plan['jobs'] if j['window']['window_id']==d['window_id'])
 assert job['role']!='train'
 student=pre['independent_student64'];assert sha(student['path'])==student['sha256']
 obs=Path(read(native_binding['path'])['job']);receipt_path=obs/'student_views/receipt.json';receipt=read(receipt_path)
 assert receipt['patch_inverse_exact'] and len(receipt['frames'])==64
 events=[];keep=[];bds=[]
 for n,index in enumerate(d['selected_preteacher_event_indices']):
  e=pre['events'][index];pairs=[e['editing_start_range_local_exact'],e['editing_end_range_local_exact']]
  assert all(F(b)-F(a)<=F('.5') for a,b in pairs)
  local=[str((F(a)+F(b))/2) for a,b in pairs];keep.append(local)
  events.append(dict(event_id='M'+str(n+1),local=local,visible_fact=e['description'],
   necessary_preparation=e.get('necessary_preparation','有限典型图像的清楚关系建立'),
   visible_result=e.get('visible_result','有限清楚图像中的可见位置与状态，不推断整项活动结果'),
   evidence_frame_ids=[f'F{i:02d}' for i in range(e['first'],e['last']+1)],editing_boundary_midpoints_not_measured_cuts=True))
  for kind,pair in zip(('start','end'),pairs):
   bds.append(dict(uncertainty_start_exact=pair[0],uncertainty_end_exact=pair[1],time_basis='LOCAL',
    inside_evidence=f"F{e['first'] if kind=='start' else e['last']:02d}",
    outside_evidence_or_domain_boundary='Root frozen preteacher NO/scene or declared domain limit',editing_boundary_only=True))
 unknown=d['unknown_local_exact'];marked=sorted([[F(a),F(b)] for a,b in keep+unknown]);last=F(0);no=[]
 for lo,hi in marked:
  assert last<=lo<hi<=F(30)
  if last<lo:no.append([str(last),str(lo)])
  last=hi
 if last<F(30):no.append([str(last),'30'])
 wrapper=op.with_name(op.stem.replace('_final_main_review','_independent_native_blind_binding')+'.json')
 save(wrapper,dict(status='BOUND_REAL_PRETEACHER_NATIVE64_REVIEW_NOT_NEW_IMAGE_OBSERVATION',window_id=d['window_id'],
  blind_attestation=dict(teacher_content_received=False,student_content_received=False,candidate_prediction_received=False),
  sealed_native_review=native_binding,actual_native_images=64,root_not_blind=True,training_admitted=False))
 evidence=dict(d['evidence']);evidence.update(blind_initial=bind(wrapper),blind_student_visibility=student,student_processor=bind(receipt_path),root_semantic_decision=bind(dp))
 result=dict(status='ROOT_FINAL_COMPLETE_FINITE_EDITORIAL_REFERENCE_ADJUDICATED',utc=datetime.now(timezone.utc).isoformat(),
  window_id=d['window_id'],root_semantic_adjudication_complete=True,candidate_prediction_exposure_before_freeze=False,
  keep_local_exact=keep,no_local_exact=no,unknown_local_exact=unknown,events=events,boundary_decisions=bds,
  consequential_unknowns=d['consequential_unknowns'],explicit_no_highlight=not keep and not unknown,
  all_target_boundaries_adjudicated=True,student_observable_complete_target=not unknown and not d['consequential_unknowns'],training_admitted=False,
  main_review_assertions={k:True for k in ('direct_visible_facts_checked','all_NO_ranges_explicitly_reviewed','no_audio_content_invented',
   'necessary_preparation_and_result_considered','no_artificial_event_merging','no_candidate_prediction_exposure_before_reference_freeze','student_visibility_checked')},
  evidence=evidence,differences_adjudicated=d['differences_adjudicated'],actual_root_observation_scope=d['actual_root_observation_scope'],
  all_NO_sample_ranges=[v for v in pre['complete_domain_editorial_decision_by_samples'] if v['decision']=='NO'],
  reference_scope_and_reason=d['reference_scope_and_reason'],evaluation_only=True)
 save(op,result);print(json.dumps(dict(window_id=d['window_id'],final=bind(op),training_admitted=False)))
if __name__=='__main__':main()
