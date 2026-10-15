"""New complete reference, using a distinct lawful original observation chain."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys
ROOT=Path(__file__).resolve().parent; ITER=ROOT.parent;OLD=ITER/'slot6_silver24_v1';V3=ITER/'independent_highlight_pilot_v3'
sys.path.insert(0,str(OLD))
from silver_contract import verify_window
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bound(p):return dict(path=str(p),sha256=sha(p))
def save(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
plan=read(OLD/'source_window_plan.json');assert sha(OLD/'source_window_plan.json')=='09ecb28971932bd3bf8ac275c30d0a6fd534345442f2d2ec3529fa3f8e1e4b22'
obs=OLD/'observations/00_kLxoNp-UchI_W01';attempt=obs/'teacher_attempt01_http1';audit=read(attempt/'audit.json')
pilot=read(OLD/'pilot_execution_receipt_v1.json')['rows'][0]
assert sha(attempt/'audit.json')==pilot['audit_sha256']
for name,field in [('stream.jsonl','stream_sha256'),('request.json','request_sha256'),('proposal.json','proposal_sha256')]:assert sha(attempt/name)==audit[field]
assert not audit['tool_issues'] and not audit['proposal_geometry_identity_issues']
assert audit['original_pngs_delivered']==64 and audit['effective_pngs_delivered']==8 and audit['native_video_delivered']
manifest=read(obs/'manifest.json');student=read(obs/'student_views/receipt.json')
rows=[json.loads(s) for s in (attempt/'stream.jsonl').read_text(encoding='utf-8-sig').splitlines() if s.strip()]
calls=[r['step_update'] for r in rows if r.get('step_update',{}).get('state')=='DONE' and r['step_update'].get('step_type')=='tool']
supplied=set()
for c in calls:
    if c['tool_name']=='view_file':
        p=c.get('tool_info',{}).get('parameters',{}).get('AbsolutePath')
        if p:supplied.add(str(Path(p).resolve()).casefold())
for f in manifest['frames']+student['frames'][::8]:
    assert str(Path(f['path']).resolve()).casefold() in supplied
    assert sha(Path(f['path']))==f['png_sha256']
assert str(Path(manifest['clip_path']).resolve()).casefold() in supplied
assert sha(Path(manifest['clip_path']))==manifest['clip_sha256']
assert sha(Path(manifest['source_path']))==manifest['source_sha256']
prior=read(V3/'acceptance.json');assert prior['status']=='STOP_FIRST_PILOT_DO_NOT_EXPAND_OR_TRAIN'
record=read(V3/'main_adjudication/window_reference.json')
assert sha(V3/'main_adjudication/final_review.json')==record['evidence']['final_main_review']['sha256']
for item in record['evidence'].values():assert sha(Path(item['path']))==item['sha256']
for kind in ('blind_native','blind_student'):
    seal=read(V3/kind/'seal.json');assert sha(V3/kind/'proposal.json')==seal['proposal_sha256']
    assert len(read(V3/kind/'proposal.json')['frame_observations'])==64
record['evidence']['teacher_observation_audit']=bound(attempt/'audit.json')
record['training_admitted']=True
record['reason']='New complete-reference supplement; original lawful media observation and sealed independent proposals plus exposed main adjudication. Not reversal of v3.'
record['supplement_provenance']=dict(protocol=bound(ROOT/'PROTOCOL.md'),
 original_observation_attempt=bound(attempt/'audit.json'),original_observation_old_proposal_not_target=True,
 prior_v3_STOP=bound(V3/'acceptance.json'),prior_v3_audit_not_used_for_admission=bound(V3/'teacher_attempt01/audit.json'),
 main_actual_images=bound(V3/'main_adjudication/observations.json'),
 fixed20_field_evidence=bound(ITER/'frame_binding_four_image_v1/program_bound_facts.json'),
 fixed20_free_text_rejections=bound(ITER/'frame_binding_four_image_v1/main_fact_review.json'),
 main_exposed_not_blind=True,human_gold=False,new_media_observations=0,new_model_calls=0)
verified=verify_window(record,plan['jobs'][0])
save(ROOT/'00_w01_complete_reference.json',record)
denominator={j['window']['window_id']:dict(window_id=j['window']['window_id'],role=j['role'],source_group=j['source_group'],
 state='QUALIFIED_SUPPLEMENT' if i==0 else 'PENDING_EXISTING_FIXED_ORDER',training_admitted=i==0,
 reference=bound(ROOT/'00_w01_complete_reference.json') if i==0 else None) for i,j in enumerate(plan['jobs'])}
save(ROOT/'denominator24_v1.json',denominator)
save(ROOT/'w01_admission.json',dict(status='PASS_NEW_W01_COMPLETE_FINITE_SILVER_REFERENCE_NOT_TRAINING_BATCH_ADMISSION',utc=datetime.now(timezone.utc).isoformat(),
 verified={k:str(v) for k,v in verified.items()},reference=bound(ROOT/'00_w01_complete_reference.json'),original_contract=bound(OLD/'silver_contract.py'),
 original_lawful_observation_audit=bound(attempt/'audit.json'),prior_v3_preserved=bound(V3/'acceptance.json'),
 historical_exposure_declared=True,teacher_semantics_not_auto_labels=True,qualified_windows=1,training_batch_admitted=False,new_model_calls=0,new_optimizer_updates=0))
print(json.dumps(dict(qualified_windows=1,keep_seconds=str(verified['known_keep_seconds']),no_seconds=str(verified['known_no_seconds']),unknown_seconds=str(verified['unknown_seconds']),new_model_calls=0,training_batch_admitted=False)))
