"""Root's complete W02 editing adjudication, independent of candidate output."""
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime,timezone
import json,hashlib,sys
ROOT=Path(__file__).resolve().parent; OLD=ROOT.parent/'slot6_silver24_v1'
OBS=OLD/'observations/01_kLxoNp-UchI_W02'; ATT=OBS/'teacher_attempt01_http1'
sys.path.insert(0,str(OLD))
from silver_contract import verify_window
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bound(p):return dict(path=str(p),sha256=sha(p))
def save(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
plan=read(OLD/'source_window_plan.json');assert sha(OLD/'source_window_plan.json')=='09ecb28971932bd3bf8ac275c30d0a6fd534345442f2d2ec3529fa3f8e1e4b22'
m=read(OBS/'manifest.json');a=read(ATT/'audit.json');facts=read(ROOT/'01_w02_main_native_observations.json')
assert facts['actual_observations']==64 and len(facts['frame_observations'])==64
assert not a['tool_issues'] and not a['proposal_geometry_identity_issues']
for name in ('stream','request','proposal'):assert sha(ATT/(name+('.jsonl' if name=='stream' else '.json')))==a[name+'_sha256']
for row,actual in zip(m['frames'],facts['frame_observations']):
    assert row['frame_id']==actual['frame_id'] and sha(Path(row['path']))==row['png_sha256']==actual['png_sha256']
    assert actual['actual_view_image_read'] and row['source_ordinal']==actual['source_ordinal']
student_path=OLD/'blind_reviews/initial/01_kLxoNp-UchI_W02.independent_student_view_review_v1.json'
student=read(student_path);initial=Path(student['prior_initial_review']['path'])
assert sha(initial)==student['prior_initial_review']['sha256']
assert student['actual_viewing']['frames']==64
views=student['frame_verification'] if 'frame_verification' in student else None
# The original sealed continuation carries its per-image inventory under the actual original key.
if views is None:
    candidates=[v for v in student.values() if isinstance(v,list) and len(v)==64 and isinstance(v[0],dict) and 'actual_view_image_read' in v[0]]
    assert len(candidates)==1;views=candidates[0]
assert all(v['actual_view_image_read'] and v['actual_png_sha256']==v['png_sha256']==sha(Path(v['path'])) for v in views)
machine=OBS/'student_views/receipt.json';assert sha(machine)==student['machine_receipt']['sha256']
extra=read(ROOT/'boundary_w02_v2/receipt.json');assert extra['source_ordinal']==2019 and sha(Path(extra['path']))==extra['png_sha256']
extra2=read(ROOT/'boundary_w02_portrait_end_v1/receipt.json');assert extra2['source_ordinal']==2418 and sha(Path(extra2['path']))==extra2['png_sha256']
extras={'extra':extra,'extra2':extra2}
pts=[F(r['local_seconds_exact']) for r in m['frames']]
gap_pairs=[(1,2),(9,10),(15,'extra'),(40,41),(43,'extra2'),(46,47),(49,50),(61,62)]
decisions=[];mid=[]
inside=[1,10,15,41,43,47,49,62]
for n,(lo,hi) in enumerate(gap_pairs):
    x=pts[lo];y=F(extras[hi]['local_seconds_exact']) if isinstance(hi,str) else pts[hi]
    assert x<y and y-x<=F('0.5');mid.append((x+y)/2)
    decisions.append(dict(uncertainty_start_exact=str(x),uncertainty_end_exact=str(y),
        inside_evidence=f'F{inside[n]:02d}',outside_evidence_or_domain_boundary=f"O{extras[hi]['source_ordinal']:06d}" if isinstance(hi,str) else f'F{hi if inside[n]==lo else lo:02d}',
        interpretation='Finite observed editing boundary range, not measured physical cut'))
keeps=[(F(0),mid[0]),(mid[1],mid[2]),(mid[3],mid[4]),(mid[5],mid[6]),(mid[7],F(30))]
assert all(b<=c for (_,b),(c,_) in zip(keeps,keeps[1:]))
nos=[(keeps[i][1],keeps[i+1][0]) for i in range(len(keeps)-1)]
event_data=[('犬跑远的可见末段',[0,1]),('头贴草地的倾斜犬脸',[10,11,12,13,14,15]),
            ('阳光下清晰侧脸及透光耳',[41,42,43]),('犬转头及眼睑变化的起态与结果',[47,48,49]),('草地半身卧犬的清晰结果',[62,63])]
events=[dict(event_id=f'M{i+1}',local=[str(x) for x in pair],evidence_frame_ids=[f'F{j:02d}' for j in ids],visible_fact=title) for i,(pair,(title,ids)) in enumerate(zip(keeps,event_data))]
review=dict(window_id=m['window_id'],utc=datetime.now(timezone.utc).isoformat(),
 actual_native_observations=bound(ROOT/'01_w02_main_native_observations.json'),boundary_supplement=bound(ROOT/'boundary_w02_v2/receipt.json'),
 portrait_end_supplement=bound(ROOT/'boundary_w02_portrait_end_v1/receipt.json'),
 portrait_end_actual_view='Root viewed O002418: same clear left-facing side portrait and red-translucent ear, continuing established pose without new action. This is outside the chosen short establishing-portrait hold, not a physical scene change.',
 boundary_supplement_actual_view='Root viewed O002019: dog face is increasingly cropped at left, only partial eye/ear, remaining empty grass. F15 retained as end result, O002019 outside.',
 teacher_proposal=bound(ATT/'proposal.json'),independent_native_initial=bound(initial),student64_continuation=bound(student_path),
 no_candidate_prediction_exposure=True,main_exposed_to_prior_history_not_blind=True,human_gold=False,
 disagreements_adjudicated=[
 'Teacher describes F29..33 as defecation/complete event: rejected. Actual images support forward steps only; independent effective views cannot determine a distinct action. Routine forward stepping is NO under this short-highlight editing task, without claiming defecation absent.',
 'Independent initial KEEP F18..24 low-head approach: observable position change but ordinary repetitive soft-focused walking, excluded in final short-highlight judgment.',
 'Teacher whole sharp-portrait hold includes F44..46/F50..54 repetitions. Keep establishing portrait and separate head-turn event, explicitly NO for repeat holds; no event quota drives this separation.',
 'Initial cut UNKNOWNs are inside wholly NO material (distant/partial body, blur or routine walking). They do not affect final KEEP target; no unseen lying-down/standing-up process invented.',
 'Final portrait starts after F61 toward F62, clear result supported by both native and effective views. Boundary is an editing choice within observed gap, not alleged exact refocus cut.'
 ],
 all_NO_ranges=[dict(local=[str(x) for x in pair],reason=reason) for pair,reason in zip(nos,[
 'Distant/empty grass, partial rear/body pan, until the clearly visible tilted face establishes.',
 'Face leaves left edge; low-head approach and forward stepping are routine, heavily blurred nearby views add no distinct visual climax; side-face shot initial focus remains soft.',
 'Established same side portrait held with minimal new information before visible head turn.',
 'Head-turn result then held repetitively; second grass portrait initial focus is foreground grass with dog blurred, until clear final result.'
 ])],
 necessary_preparation_and_result='Retain visible start/result within each selected image-defined event. Window-edge run/finalportrait truncation disclosed; no off-window action invented.',
 student_visibility='Existing sealed actual64 effective view confirms tilted face, sharp side portrait, head turn/eyelids and final grass portrait. New O2019 only refines an editing gap, not a new target event requiring extra student input.',
 boundary_decisions=decisions,events=events,consequential_unknowns=[],teacher_factual_errors_not_supervision=True,
 accepted_complete_finite_editing_reference=True)
save(ROOT/'01_w02_final_main_review.json',review)
record=dict(window_id=m['window_id'],source_sha256=m['source_sha256'],reference_kind='FINITE_OBSERVATION_SILVER_EDITING_ADVICE_NOT_GOLD',
 keep_global_exact=[[str(x+60) for x in pair] for pair in keeps],no_global_exact=[[str(x+60) for x in pair] for pair in nos],unknown_global_exact=[],
 evidence=dict(teacher_observation_audit=bound(ATT/'audit.json'),blind_initial=bound(initial),blind_student_visibility=bound(student_path),student_processor=bound(machine),final_main_review=bound(ROOT/'01_w02_final_main_review.json')),
 main_review_assertions={k:True for k in ('direct_visible_facts_checked','all_NO_ranges_explicitly_reviewed','no_audio_content_invented','necessary_preparation_and_result_considered','no_artificial_event_merging','no_candidate_prediction_exposure_before_reference_freeze','student_visibility_checked')},
 boundary_decisions=decisions,consequential_unknowns=[],events=events,explicit_no_highlight=False,all_target_boundaries_adjudicated=True,student_observable_complete_target=True,training_admitted=True,
 reason='Complete root native image adjudication plus lawful original teacher media and sealed native/student evidence. Silver editing advice, not gold or unseen generalization.',
 supplement_provenance=dict(protocol=bound(ROOT/'PROTOCOL.md'),erratum=bound(ROOT/'PROTOCOL_ERRATUM_W11_AND_BUDGET.md'),new_model_calls=0,new_optimizer_updates=0))
verified=verify_window(record,plan['jobs'][1]);save(ROOT/'01_w02_complete_reference.json',record)
save(ROOT/'w02_admission.json',dict(status='PASS_NEW_W02_COMPLETE_FINITE_SILVER_REFERENCE_NOT_TRAINING_BATCH_ADMISSION',verified={k:str(v) for k,v in verified.items()},reference=bound(ROOT/'01_w02_complete_reference.json'),qualified_windows_total=2,new_model_calls=0,new_optimizer_updates=0))
print(json.dumps(dict(keep_seconds=str(verified['known_keep_seconds']),no_seconds=str(verified['known_no_seconds']),events=len(events),training_batch_admitted=False)))
