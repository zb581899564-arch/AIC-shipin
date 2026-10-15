"""Independent PNG/input byte audit and aggregate reconstruction, no media decode/model."""
from pathlib import Path
from fractions import Fraction as F
import hashlib,json,sys,datetime
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'science_runtime'))
import science_contract as contract
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def binding(p):return {'path':str(p),'sha256':sha(p)}
def save(p,v):
 with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
planpath=ROOT/'source_window_plan_v1.json';plan=json.loads(planpath.read_text(encoding='utf-8-sig'));rows=[]
repairs=ROOT/'runtime_independent_repairs_receipt_v1.json';r=json.loads(repairs.read_text(encoding='utf-8-sig'))
assert all(sha(ROOT/name)==s for name,s in r['file_sha256'].items())
for ix,job in enumerate(plan['jobs']):
 out=ROOT/'observations'/f'{ix:03d}';m=json.loads((out/'contact_sheet_manifest.json').read_text(encoding='utf-8'));p=json.loads((out/'student_processor.json').read_text(encoding='utf-8'));w=job['window']
 assert m['window_id']==p['window_id']==w['window_id'] and m['source_sha256']==p['source_sha256']==w['source_sha256']
 assert m['source_plan']['sha256']==sha(planpath) and p['contact_sheet_manifest_sha256']==sha(out/'contact_sheet_manifest.json')
 pixel=contract.verify_contact_sheet_manifest(m,w)
 assert p['patch_inverse_exact'] is True and p['cuda_initialized'] is False and p['new_model_calls']==p['new_optimizer_updates']==0
 assert p['evidence']['source_frame_ids']==w['planned_source_frame_ordinals'] and p['evidence']['frame_pixel_sha256']==[f['pixel_sha256'] for f in m['frames']]
 assert len(p['frames'])==64 and len(p['sheets'])==8 and 0<p['input_tokens']<=16384
 for j,f in enumerate(p['frames']):
  assert f['source_ordinal']==m['frames'][j]['ordinal'] and F(f['global_seconds_exact'])==F(m['frames'][j]['pts_exact'])
  assert sha(f['path'])==f['png_sha256']
 for s in p['sheets']:assert sha(s['image']['path'])==s['image']['sha256']
 rows.append({'index':ix,'role':job['role'],'window_id':w['window_id'],'manifest':binding(out/'contact_sheet_manifest.json'),'student_processor':binding(out/'student_processor.json'),'source_pixel_audit':pixel,'input_tokens':p['input_tokens'],'native_processor_wall_seconds':p['wall_seconds']})
 if ix%8==7:print(json.dumps({'verified_windows':ix+1,'total':96}),flush=True)
assert len(rows)==96
receipt={'status':'PASS_ALL96_ACTUAL_LOCAL_NATIVE64_PROCESSOR_AND_INDEPENDENT_PNG_BYTE_PIXEL_AUDIT_NOT_REFERENCE_ADMISSION','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_plan':binding(planpath),'runtime_repairs':binding(repairs),'windows':96,'native_frames':6144,'student_frames':6144,'native_sheets':768,'student_sheets':768,'roles':{role:sum(j['role']==role for j in plan['jobs']) for role in ['train','process_dev','locked_evaluation']},'rows':rows,'aggregate_report_original_failure':'80-window batch finished every decoder/processor, then final aggregate filename exceeded Windows path limit; original trace retained in tool output, no decoder repeated; short named independent aggregate reconstructed from all completed per-window bytes.','successful_windows_rerun':0,'new_model_calls':0,'new_optimizer_updates':0,'semantic_labels_complete':False,'actual_training_admitted':False,'linux_native_input_verified':False}
save(ROOT/'all96_native_preparation_acceptance_v1.json',receipt)
print(json.dumps({k:v for k,v in receipt.items() if k!='rows'}),flush=True)
