"""Read-only aggregate provenance audit; no decoder/model/optimizer reruns."""
import json
from register_b2_package_v1 import remote, REMOTE, RUN

CODE = r'''
import json, hashlib, socket
from pathlib import Path
assert socket.gethostname() == 'inspur-NP5570M5'
root=Path(ROOT)
def read(p): return json.loads(p.read_bytes())
def rows(p): return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
old=root/'temporal_sft8b_dev_v1'
c=root/'context_advisory_v1'
d=root/'nested_density_v1'
plan=read(c/'input_01/developer_plan.json')
out={'old_decision':read(old/'decision.json'), 'nested_report':read(d/'developer_01/report.json'),
 'plan_keys':list(plan), 'plan_containers':{k:(len(v) if isinstance(v,(dict,list)) else type(v).__name__) for k,v in plan.items()},
 'old_output_exists':(old/'SFT8B.jsonl').is_file(),
 'new_report_paths':[str(p.relative_to(root)) for p in c.glob('*_01/*report*.json')],
 'new_B0_done_paths':[str(p.relative_to(root)) for p in c.rglob('done.json') if '/B0/' in str(p)][:2]}
if out['old_output_exists']:
 oldrows=rows(old/'SFT8B.jsonl')
 out['old_output']={'sha256':sha(old/'SFT8B.jsonl'),'records':len(oldrows),
  'row_keys':list(oldrows[0]),'window_keys':list(oldrows[0]['windows'][0]),
  'first_video_identity':oldrows[0]['windows'][0].get('video_identity'),
  'grids':sorted({str(w['video_identity']['video_grid_thw']) for r in oldrows for w in r['windows'] if 'video_identity' in w})}
out['developer_files']=[str(p.relative_to(root)) for p in c.glob('developer_01/*') if p.is_file()]
job=plan['developer_jobs'][0]
out['job_keys']=list(job)
out['window_keys']=list(job['windows'][0])
out['window_plan_keys']=list(job['windows'][0]['window'])
p=c/'developer_01/local'/hashlib.sha256(json.dumps(job['video_id'],sort_keys=True,separators=(',',':')).encode()).hexdigest()/'0/B0/done.json'
for p in c.glob('developer_01/local/*/0/B0/done.json'):
 v=read(p);out['done_keys']=list(v);out['identity_keys']=list(v['video_identity'])
 out['actual_grid']=v['video_identity'].get('video_grid_thw');break
import importlib.util, statistics, sys, re
def module(p,n):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
cc=module(c/'context_contract.py','audit_cc')
gc=module(root/'teacher_student_autopilot_v14/precision_helpers/constrained_json.py','audit_gc')
old_lookup={r['video_id']:r for r in oldrows}
current_scores=[];old_scores=[];grid_equal=sample_count_equal=old_compact_valid=old_space_only_rejected=old_other_rejected=0
old_noncanonical_whitespace=0;changed_sampling_windows=changed_ordinals=0
for job in plan['developer_jobs']:
 oldr=old_lookup[job['video_id']]; pred=[]
 old_scores.append(cc.weak_metrics(oldr['pred'],job['weak_reference'])['f1'])
 assert len(oldr['windows'])==len(job['windows'])
 for ix,part in enumerate(job['windows']):
  key=cc.digest(job['video_id']);v=read(c/'developer_01/local'/key/str(ix)/'B0/done.json')
  ow=oldr['windows'][ix]; raw=ow['raw_output'];g=gc.BoundedSegmentsGrammar(part['end_sec']-part['start_sec'],allow_empty=False)
  compact=''.join(raw.split())
  valid=g.complete(raw); compact_valid=g.complete(compact)
  old_compact_valid+=int(valid);old_space_only_rejected+=int(not valid and compact_valid)
  old_other_rejected+=int(not valid and not compact_valid)
  old_noncanonical_whitespace+=int(raw!=compact)
  grid_equal+=int(ow['video_identity']['video_grid_thw'][0]==v['video_identity']['video_grid_thw'])
  sample_count_equal+=int(ow['video_identity']['video_grid_thw'][0][0]==v['video_identity']['video_grid_thw'][0])
  w=part['window'];base=w['planned_source_frame_ordinals'];n=w['eligible_source_frame_count'];first=base[0];s=min(64,n)
  nearest=list(range(first,first+n)) if n<=64 else [first+(2*i*(n-1)+63)//126 for i in range(64)]
  assert len(nearest)==len(base) and nearest[0]==base[0] and nearest[-1]==base[-1]
  changed_sampling_windows+=int(nearest!=base);changed_ordinals+=sum(a!=b for a,b in zip(nearest,base))
  for a,b in v['parsed_segments']:
   offset=part['start_sec']-job['clip_start_sec'];pred.append([a+offset,b+offset])
 current_scores.append(cc.weak_metrics(pred,job['weak_reference'])['f1'])
audit={'status':'PASS_READ_ONLY_REMAINING_MECHANISM_PROVENANCE_AUDIT','old_records':len(oldrows),
 'current_records':len(current_scores),'windows':sum(len(j['windows']) for j in plan['developer_jobs']),
 'historical_free_decoder_weak_macro_recomputed':statistics.mean(old_scores),
 'current_native_B0_weak_macro_recomputed':statistics.mean(current_scores),
 'original_report_macro':read(old/'decision.json')['comparisons']['SFT8B']['video_macro']['f1'],
 'historical_raw_already_canonical_grammar_accepts':old_compact_valid,
 'historical_raw_rejected_only_for_json_whitespace':old_space_only_rejected,
 'historical_raw_other_grammar_rejections':old_other_rejected,
 'historical_raw_contains_whitespace':old_noncanonical_whitespace,
 'old_current_video_grids_equal':grid_equal,'old_current_temporal_grid_equal':sample_count_equal,
 'native_floor_vs_training_nearest_windows_changed':changed_sampling_windows,
 'native_floor_vs_training_nearest_ordinals_changed':changed_ordinals,
 'new_model_calls':0,'new_optimizer_updates':0,'new_decoder_replays':0,
 'reference_coverage':'UNKNOWN','observed_dev_not_new_holdout':True,
 'source_bindings':{'original_SFT8B_output':sha(old/'SFT8B.jsonl'),
 'C_plan':sha(c/'input_01/developer_plan.json'),'density_report':sha(d/'developer_01/report.json'),
 'grammar':sha(root/'teacher_student_autopilot_v14/precision_helpers/constrained_json.py')}}
from datetime import datetime,timezone
audit['utc']=datetime.now(timezone.utc).isoformat()
audit['scientific_decision']='REGISTER_ONE_FINITE_NATIVE_NEAREST_64_ALIGNMENT_HYPOTHESIS_NO_PROMPT_PIXEL_DENSITY_SWEEP'
audit['old_vs_current_other_factors_remain_coupled']=True
audit['prediction_or_official_improvement_proven']=False
receipt=root/'controller/REMAINING_MECHANISM_READONLY_AUDIT_20261009.json'
assert not receipt.exists(),'audit already complete; do not rerun'
with receipt.open('x') as f:f.write(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
audit['private_receipt_sha256']=sha(receipt)
print(json.dumps(audit,ensure_ascii=False))
'''

if __name__ == '__main__':
    value=json.loads(remote('ROOT='+repr(REMOTE)+'\n'+CODE,echo=False))
    (RUN/'controller/REMAINING_MECHANISM_READONLY_AUDIT_20261009_summary.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(value,ensure_ascii=False,indent=2))
