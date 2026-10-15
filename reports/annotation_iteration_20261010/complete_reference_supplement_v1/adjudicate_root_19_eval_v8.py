"""Sign ROOT's reviewed finite editorial decision; teacher all-NO is not adopted."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path(__file__).parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):return {'path':str(p),'sha256':sha(p)}
pre=R/'19_j0n_w11_main_preteacher_review_v2.json'
cross=R/'teacher_semantic_crosschecks_v1/19_J0nA4VgnoCo_W11.teacher_semantic_crosscheck_v2.json'
media=R/'19_j0n_w11_lawful_observation_completion_v2.json'
scope=R/'teacher_expansion/engineering_CLI36_37_split_fragment_v8v5/call36/w19_completed_scope_audit.json'
proposal=R/'teacher_expansion/engineering_CLI36_37_split_fragment_v8v5/call36/w19_proposal.json'
before=read(pre);mc=read(media);sc=read(scope);cc=read(cross)
assert before['window_id']==mc['window_id']==cc['window_id']
assert mc['global_CLI']==36 and mc['original_pngs_delivered']==64 and mc['effective_pngs_delivered']==8 and mc['native_video_delivered']
assert not mc['tool_issues'] and not mc['proposal_geometry_identity_issues']
assert sc['status']=='PASS_IMMUTABLE_ACTUAL_SCOPE_PENDING_ROOT_SEMANTIC'
assert sc['windows'][-1]['bound_rows']==64
assert cc['inputs']['root_lawful_media_completion_v2']==bind(media)
assert before['root_read_all64_native_static_facts_and_all64_student_static_facts']
evidence={'preteacher_main_review':bind(pre),'teacher_observation_audit':bind(media),'original_teacher_proposal':bind(proposal),'original_teacher_bound_fact_audit':bind(scope),'boundary_observations':before['boundary_observations'],'exposed_independent_semantic_crosscheck':bind(cross),'root_actual_postteacher_pixels':bind(R/'19_j0n_w11_root_actual_postteacher_pixels_v1.json')}
for b in evidence.values():assert sha(Path(b['path']))==b['sha256']
d={'status':'ROOT_SEMANTIC_EVALUATION_ADJUDICATION_COMPLETE','utc':datetime.now(timezone.utc).isoformat(),'window_id':before['window_id'],'candidate_prediction_exposure':False,'root_read_all64_teacher_facts':True,'root_read_all64_native_and_student_facts':True,'all_NO_ranges_reviewed':True,'selected_preteacher_event_indices':[0,1],'unknown_local_exact':[],'consequential_unknowns':[],'evidence':evidence,'differences_adjudicated':[
 'Teacher all-NO is rejected for the two finite representative visual excerpts already selected before teacher/predictions. F04..07 supplies clear tread lines and finger relation; F14..18 supplies local outward wheel tilt and exposed wheelarch. Neither target is a complete repair action.',
 'ROOT actually re-inspected original F04/F07/F14/F18 after reading all64 teacher rows. F14 hand/held object and wheel centre are occluded; F18 wheel is outside and tilted from arch. Installed, tightened, axle-engaged and repair-completed claims are not accepted.',
 'Ordinary holding F00..03, repeated tread touch F08..13, prolonged obscured wheel-centre operation F19..51, ordinary withdrawal/standing F52..58 and passing people F59..63 retain their frozen NO reasons. Original native E3 is not restored as an extra event.',
 'Exposed independent review actually checked native F24 and found the extra tyre upright/leaning, rather than teacher flat-on-ground claim. Old/new/spare/removed identity, force, wear diagnosis, mechanical security and load-bearing state are not labelled.',
 'Teacher proposed internal ranges5..6 and26..27 are width1s; their limitations saying about0.5s does not narrow them. The reference uses only previously signed finite editing bounds and accepted tread interior probe12, without new boundary observations or epsilon.',
 'Original student complete install/tightening and release uncertainty1001/2000>0.5 remain unchanged. These hidden physical outcomes are outside the preregistered limited targets, not converted into a complete physical target or cleared to satisfy coverage.',
 'ROOT serialization failure was confined to writing its own receipt and did not alter teacher raw, facts, proposal or pixels. The original partial file and failure receipt remain; the new independently completed media receipt is used. Whole CLI36 remains pending its natural terminal; this scope does not claim whole-session success.'
 ],'actual_root_observation_scope':{'native_sample_indices':before['root_actually_viewed_native_samples'],'student_sample_indices':before['root_actually_viewed_student_samples'],'additional_postteacher_native_samples':[4,7,14,18],'read_native_static_facts':64,'read_student_static_facts':64,'read_teacher_static_facts':64,'root_direct64_image_review':False,'root_native_video_view':False,'teacher_actual_video_delivery':True,'original_parent_terminal_not_inferred':True,'current_teacher_native_images':64,'earlier_native_images_transferred':0},'reference_scope_and_reason':'Locked evaluation finite visual editorial silver, with two independently preselected typical-image/local relationship targets and explicit ordinary-operation NO. Full repair/installation/tightening and exact release remain unknown in sealed source records outside these finite targets. Not human gold or official score; no target, source, boundary or quality threshold was added after predictions.'}
out=R/'19_j0n_w11_root_eval_decision.json'
text=json.dumps(d,ensure_ascii=False,indent=2)
with out.open('x',encoding='utf-8') as f:f.write(text)
print(json.dumps(bind(out),ensure_ascii=False))
