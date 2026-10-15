"""Static evidence only: no decoder, processor, model or remote operation."""
import hashlib,json,sys
from pathlib import Path
from datetime import datetime,timezone
from fractions import Fraction as F
R=Path(__file__).resolve().parent;O=R.parent/'slot6_silver24_v1'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
sys.path.insert(0,str(O));from silver_contract import verify_window,training_schedule
sys.path.insert(0,str(R/'runtime'));from common import load;from objective import target,classify
plan=read(O/'source_window_plan.json');jobs={j['window']['window_id']:j for j in plan['jobs']}
reg=R/'denominator24_v9.json';registry=read(reg);records=registry['records'];refs={}
for key,row in records.items():
 if row.get('reference'):
  assert sha(row['reference']['path'])==row['reference']['sha256'];ref=read(row['reference']['path']);verify_window(ref,jobs[key]);refs[key]=ref
schedule=training_schedule(plan,{k:refs.get(k,dict(training_admitted=False)) for k in jobs})
assert len(schedule['window_ids'])==8 and schedule['updates']==4
run=R.parents[1]/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
parser=load(run/'teacher_student_autopilot_v14/precision_helpers/contracts.py','train8_original_parser')
grammar=load(run/'teacher_student_autopilot_v14/precision_helpers/constrained_json.py','train8_original_grammar')
rows=[]
for key in schedule['window_ids']:
 ref=refs[key];digest=records[key]['reference']['sha256'];sides=[]
 for p in R.glob('*_target_serialization.json'):
  s=read(p)
  if s['window_id']==key and s['reference_sha256']==digest:sides.append((p,s))
 assert len(sides)<=1
 w=jobs[key]['window'];raw,_=target(ref,w,sides[0][1] if sides else None,digest)
 duration=F(w['domain_end_exact'])-F(w['domain_start_exact']);parsed,errors,warnings=parser.parse_segments(raw,duration,allow_empty=True)
 assert parsed is not None and not errors and grammar.BoundedSegmentsGrammar(duration,allow_empty=True).complete(raw)
 assert classify(raw,duration)['parsed_segments']==[[F(str(a)),F(str(b))] for a,b in parsed]
 rows.append(dict(window_id=key,source_group=jobs[key]['source_group'],reference=records[key]['reference'],
  explicit_no_highlight=ref['explicit_no_highlight'],raw_json_target=raw,
  target_sidecar=None if not sides else dict(path=str(sides[0][0]),sha256=sha(sides[0][0])),
  original_parser_grammar_exact_pts_pass=True))
evaluation=[k for k,j in jobs.items() if j['role']!='train']
pending=[k for k in evaluation if k not in refs]
out=dict(status='PASS_STATIC_TRAIN8_TARGETS_NOT_BATCH_RUNTIME_ADMISSION',utc=datetime.now(timezone.utc).isoformat(),
 registry=dict(path=str(reg),sha256=sha(reg)),fixed_denominator=24,train_windows=8,
 train_source_groups=len({row['source_group'] for row in rows}),schedule=schedule,
 train_positive_source_groups=len({row['source_group'] for row in rows if not row['explicit_no_highlight']}),
 explicit_empty_windows=sum(row['explicit_no_highlight'] for row in rows),training_targets=rows,
 evaluation_windows=12,pending_evaluation_references=pending,
 real_linux_native_processor_preflight=False,batch_training_admitted=False,
 model_loaded=False,new_model_calls=0,new_optimizer_updates=0,
 source_upload_permission_still_pending=True)
with (R/'training8_static_readiness_v2.json').open('x',encoding='utf-8') as f:f.write(json.dumps(out,ensure_ascii=False,indent=2,default=str,allow_nan=False))
print(json.dumps({k:out[k] for k in ('status','train_windows','train_source_groups','train_positive_source_groups','explicit_empty_windows','new_optimizer_updates')}))
