"""Actual original silver/denominator/target acceptance after both semantic reviews."""
from pathlib import Path
from datetime import datetime,timezone
from fractions import Fraction as F
import json,hashlib,sys
R=Path(__file__).resolve().parent;O=R.parent/'slot6_silver24_v1'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bound(p):return dict(path=str(p),sha256=sha(p))
p=R/'denominator24_v21.json';reg=read(p);rows=reg['records']
assert (reg['fixed_denominator'],reg['qualified_references'],reg['rejected_references'],reg['pending_references'],reg['accepted_train_windows'])==(24,20,4,0,8)
plan=read(O/'source_window_plan.json');jobs={j['window']['window_id']:j for j in plan['jobs']}
assert set(rows)==set(jobs)
sys.path.insert(0,str(O));from silver_contract import verify_window,training_schedule
from quality_contract import duration
refs={};accepted=[]
for key,row in rows.items():
 assert row['role']==jobs[key]['role'] and row['source_group']==jobs[key]['source_group']
 if row.get('reference'):
  b=row['reference'];assert sha(b['path'])==b['sha256'];ref=read(b['path'])
  result=verify_window(ref,jobs[key]);assert ref['training_admitted']==row['training_admitted']
  refs[key]=ref;accepted.append(dict(reference=b,actual_original_silver_result=result))
 else:assert row.get('status',row.get('state','')).startswith('REJECTED') and row['training_admitted'] is False
schedule=training_schedule(plan,{k:refs.get(k,dict(training_admitted=False)) for k in jobs})
assert len(schedule['window_ids'])==8 and schedule['updates']==4
sys.path.insert(0,str(R/'runtime'));from common import evaluation_keys
from objective import target,classify
dev,locked=evaluation_keys(jobs);evaluation=sorted(dev+locked)
assert len(dev)==4 and len(locked)==8 and len(evaluation)==12 and all(k in refs for k in evaluation)
assert {jobs[k]['source_group'] for k in schedule['window_ids']}.isdisjoint({jobs[k]['source_group'] for k in evaluation})
known=sum(not refs[k]['unknown_global_exact'] and not refs[k].get('consequential_unknowns') for k in locked)
assert known==6
groups={}
for k in locked:
 g=groups.setdefault(jobs[k]['source_group'],dict(keep=[],no=[]))
 g['keep']+=refs[k]['keep_global_exact'];g['no']+=refs[k]['no_global_exact']
assert len(groups)==4 and sum(duration(g['keep'])>0 for g in groups.values())>=3
assert all(duration(g['keep'])>0 or duration(g['no'])>=5 for g in groups.values())
assert sum(duration(g['no'])>=5 for g in groups.values())>=2
targets=[]
for k in schedule['window_ids']:
 b=rows[k]['reference'];matches=[]
 for side in R.glob('*_target_serialization.json'):
  s=read(side)
  if s['window_id']==k and s['reference_sha256']==b['sha256']:matches.append((side,s))
 assert len(matches)<=1
 raw,exact=target(refs[k],jobs[k]['window'],matches[0][1] if matches else None,b['sha256'])
 w=jobs[k]['window'];parsed=classify(raw,F(w['domain_end_exact'])-F(w['domain_start_exact']))
 assert parsed['status'] in ('MODEL_OK','LEGAL_EMPTY')
 targets.append(dict(window_id=k,target_json=raw,exact_local=exact,status=parsed['status']))
runtime=R/'runtime_validation_v5.json';v=read(runtime)
assert v['tests']==51 and len(v['sources'])==23
for source,h in v['sources'].items():assert sha(source)==h
result=dict(status='PASS_ROOT_FINAL24_ORIGINAL_SILVER_TARGET_SOURCE_SPLIT_READY_FOR_REMOTE_PREFLIGHT_NOT_TRAINING',
 utc=datetime.now(timezone.utc).isoformat(),registry_binding=bound(p),denominator=dict(total=24,qualified=20,rejected=4,pending=0),
 train_windows=8,evaluation_windows=12,fully_known_locked=known,original_silver_actual_verified=True,
 original_silver_actual_results=accepted,schedule=schedule,actual_training_targets=targets,
 canonical_record_states={k:row.get('status',row.get('state')) for k,row in rows.items()},
 historical_state_aliases_preserved=True,current_status_has_precedence=True,
 frozen_runtime_validation=bound(runtime),runtime_current23_SHA_equal=True,new_tests=0,
 remote_native_processor_parity_still_required=True,new_model_calls=0,new_optimizer_updates=0,
 reference_kind='FINITE_OBSERVATION_SILVER_EDITING_ADVICE_NOT_GOLD',production_replaced=False)
out=R/'dataset24_final_admission_schema_recovery_v1.json'
with out.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False,default=str)
print(json.dumps(dict(status=result['status'],path=str(out),sha256=sha(out)),ensure_ascii=False))
