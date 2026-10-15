"""Complete visual editing adjudications for the two existing mechanical-source windows."""
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime,timezone
import json,hashlib,sys
ROOT=Path(__file__).resolve().parent;OLD=ROOT.parent/'slot6_silver24_v1'
sys.path.insert(0,str(OLD))
from silver_contract import verify_window
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bound(p):return dict(path=str(p),sha256=sha(p))
def save(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
plan=read(OLD/'source_window_plan.json');assert sha(OLD/'source_window_plan.json')=='09ecb28971932bd3bf8ac275c30d0a6fd534345442f2d2ec3529fa3f8e1e4b22'
for i,name in [(2,'02_AwmHb44_ouw_W10'),(3,'03_AwmHb44_ouw_W11')]:
    stem='02_w10' if i==2 else '03_w11';obs=OLD/'observations'/name;m=read(obs/'manifest.json');job=plan['jobs'][i]
    student_path=OLD/'blind_reviews/initial'/(name+'.independent_student_view_review_v1.json')
    student=read(student_path);initial=Path(student['prior_initial_review']['path']);assert sha(initial)==student['prior_initial_review']['sha256']
    assert student['actual_viewing']['frames']==64
    inventories=[v for v in student.values() if isinstance(v,list) and len(v)==64 and isinstance(v[0],dict) and 'actual_view_image_read' in v[0]]
    assert len(inventories)==1
    assert all(v['actual_view_image_read'] and v['actual_png_sha256']==v['png_sha256']==sha(Path(v['path'])) for v in inventories[0])
    machine=obs/'student_views/receipt.json';assert sha(machine)==student['machine_receipt']['sha256']
    extra_evidence={}
    if i==2:
        observations=ROOT/'02_w10_main_native_observations.json';actual=read(observations)
        assert actual['actual_observations']==64
        for r,f in zip(m['frames'],actual['frame_observations']):assert r['png_sha256']==f['png_sha256']==sha(Path(r['path'])) and f['actual_view_image_read']
        audit_path=obs/'teacher_attempt01_http1/audit.json';audit=read(audit_path)
        assert not audit['tool_issues'] and not audit['proposal_geometry_identity_issues']
        for n in ('stream','request','proposal'):assert sha(audit_path.parent/(n+('.jsonl' if n=='stream' else '.json')))==audit[n+'_sha256']
        proposal_path=audit_path.parent/'proposal.json'
        pts=[F(r['local_seconds_exact']) for r in m['frames']];transition=(pts[4]+pts[5])/2;finish=(pts[8]+pts[9])/2
        assert pts[5]-pts[4]<=F('0.5') and pts[9]-pts[8]<=F('0.5')
        keeps=[(F(0),finish)];nos=[(finish,F(30))]
        events=[dict(event_id='M1',local=['0',str(transition)],evidence_frame_ids=[f'F{j:02d}' for j in range(5)],visible_fact='手指与轮圈内小凸点接触关系的清晰细节展示，不称完成泄气/修复'),
                dict(event_id='M2',local=[str(transition),str(finish)],evidence_frame_ids=[f'F{j:02d}' for j in range(5,9)],visible_fact='轮胎、朝上金属轮圈、白喷壶与小工具的全貌建立镜头')]
        boundaries=[dict(uncertainty_start_exact=str(pts[4]),uncertainty_end_exact=str(pts[5]),inside_evidence='F04,F05 (both KEEP)',outside_evidence_or_domain_boundary='Domain; internal distinct event transition'),
                    dict(uncertainty_start_exact=str(pts[8]),uncertainty_end_exact=str(pts[9]),inside_evidence='F08',outside_evidence_or_domain_boundary='F09 repetitive established layout')]
        differences=[
          'Root initial NO is preserved. After considering the independent native/student technical-detail judgment, retain brief hand/object contact and whole wheel/tool establishing view as clear representative technical imagery. No completion of repair is asserted; this is editorial adjudication before candidate predictions, not a positive-count quota.',
          'Do not retain the entire long tire hold proposed by teacher. From the established layout onward, only repeated near-static composition is visible.',
          'Unknown physical cut within F04/F05 does not create UNKNOWN target coverage because both adjacent event units are retained. Events are separately registered although their KEEP intervals touch.',
          'Independent audio-meaning UNKNOWN is preserved in its original review. This final target addresses the registered finite visual highlight task only; no speech meaning is inferred. Talking-head mouth/eyelid variation supplies no salient visual event, so it is NO for this task, not a claim that speech is unimportant.'
        ]
        no_reason='After brief clear wheel/tool establishment, F09..23 repeat the same stationary layout; F24..63 are fixed talking-head close-up with small mouth/eye movements, no visually distinctive action, object demonstration or new result. Audio content is unavailable and not fabricated.'
        extra_evidence=dict(student_batch_erratum=bound(OLD/'blind_reviews/initial/independent_completion_and_W10_batch_errata_v1.json'),student_actual_batch_binding=bound(OLD/'blind_reviews/initial/W10_actual_batch_binding_v1.json'))
        actual_scope='Root individually viewed all64 native PNG; existing independent student reviewer actually viewed all64 effective PNG (13 actual batches, erratum bound).'
    else:
        observations=ROOT/'native_reviews/03_AwmHb44_ouw_W11.native_review.json';actual=read(observations)
        assert actual['frame_count']==64 and actual['teacher_content_received'] is False and actual['candidatePredictionExposure'] is False
        for r,f in zip(m['frames'],actual['frames']):assert r['png_sha256']==f['current_png_sha256']==sha(Path(r['path'])) and f['visually_inspected_original_png']
        audit_path=ROOT/'03_w11_lawful_observation_completion.json';audit=read(audit_path)
        assert audit['status']=='PASS_ACTUAL_COMPLETE_LAWFUL_MEDIA_AND_PROPOSAL_WITH_EARLY_TRANSPORT_ERROR_PRESERVED'
        proposal_path=Path(audit['proposal']['path']);assert sha(proposal_path)==audit['proposal']['sha256']
        keeps=[];a,b=F(job['window']['domain_start_exact']),F(job['window']['domain_end_exact']);nos=[(F(0),b-a)];events=[];boundaries=[]
        differences=[
          'Independent initial/student UNKNOWN concerns possible important spoken explanation. Their original UNKNOWN bytes stay intact. In the registered finite visual task, unavailable speech meaning is not invented as a target; all64 native/effective observations show the same fixed portrait with minor mouth/eye/head changes and no salient visual event.',
          'Root read all64 delegated per-image facts and directly spot-checked native F00/F20/F40/F63. The full64 actual native observer is the named independent agent, not root; the existing sealed reviewer performed full64 effective review. Main is accountable for this combined complete visual NO judgment.',
          'New legitimate teacher observation uses exact post-error completed work. Early API error, old timeout, failed eligibility, AGY resultERROR and old W11 self-proposal violation remain. No failure is converted to empty output: a real single full-domain NO proposal exists after all required actual media.',
        ]
        no_reason='Whole visual window is one continuous outdoor portrait with ordinary mouth movement, blinking and tiny head adjustments; no hand gesture, tool manipulation, distinctive new framing or visible result. This finite visual NO label says nothing about unobserved audio importance.'
        actual_scope='Independent named native agent individually viewed64 and sealed all per-image facts; root reviewed all facts and spot-checked4 actual PNG; existing independent reviewer actually viewed64 effective PNG.'
    main=dict(window_id=m['window_id'],utc=datetime.now(timezone.utc).isoformat(),actual_native_observations=bound(observations),
       actual_observation_scope=actual_scope,teacher_proposal=bound(proposal_path),independent_native_initial=bound(initial),student64_continuation=bound(student_path),
       differences_adjudicated=differences,all_NO_ranges=[dict(local=[str(x) for x in pair],reason=no_reason) for pair in nos],
       events=events,boundary_decisions=boundaries,consequential_unknowns=[],no_candidate_prediction_exposure=True,
       preparation_and_result_considered='Clear representative detail and whole-object relation considered. No invisible physical completion, audio meaning, off-window action or mental state invented.',
       student_observable_complete_target=True,main_exposed_not_blind=True,human_gold=False,**extra_evidence)
    main_path=ROOT/(stem+'_final_main_review.json');save(main_path,main)
    start=F(job['window']['domain_start_exact'])
    record=dict(window_id=m['window_id'],source_sha256=m['source_sha256'],reference_kind='FINITE_OBSERVATION_SILVER_EDITING_ADVICE_NOT_GOLD',
       keep_global_exact=[[str(x+start) for x in pair] for pair in keeps],no_global_exact=[[str(x+start) for x in pair] for pair in nos],unknown_global_exact=[],
       evidence=dict(teacher_observation_audit=bound(audit_path),blind_initial=bound(initial),blind_student_visibility=bound(student_path),student_processor=bound(machine),final_main_review=bound(main_path)),
       main_review_assertions={k:True for k in ('direct_visible_facts_checked','all_NO_ranges_explicitly_reviewed','no_audio_content_invented','necessary_preparation_and_result_considered','no_artificial_event_merging','no_candidate_prediction_exposure_before_reference_freeze','student_visibility_checked')},
       boundary_decisions=boundaries,consequential_unknowns=[],events=events,explicit_no_highlight=not keeps,all_target_boundaries_adjudicated=True,
       student_observable_complete_target=True,training_admitted=True,reason='Complete finite visual editing reference; original independent audio UNKNOWNs preserved, no claim of human gold.',
       supplement_provenance=dict(protocol=bound(ROOT/'PROTOCOL.md'),erratum=bound(ROOT/'PROTOCOL_ERRATUM_W11_AND_BUDGET.md'),new_optimizer_updates=0))
    verified=verify_window(record,job);refpath=ROOT/(stem+'_complete_reference.json');save(refpath,record)
    save(ROOT/(stem+'_admission.json'),dict(status='PASS_COMPLETE_FINITE_VISUAL_REFERENCE_NOT_TRAINING_BATCH_ADMISSION',verified={k:str(v) for k,v in verified.items()},reference=bound(refpath),new_optimizer_updates=0))
    print(json.dumps(dict(window=stem,keep_seconds=str(verified['known_keep_seconds']),no_seconds=str(verified['known_no_seconds']),new_optimizer_updates=0)))
