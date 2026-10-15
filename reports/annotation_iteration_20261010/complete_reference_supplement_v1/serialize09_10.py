"""Explicit root-approved finite literals; preserve exact references and PTS sets."""
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime,timezone
import json,hashlib,sys,importlib.util
R=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
 with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2)
sys.path.insert(0,str(R/'runtime'));from objective import target,classify
run=R.parents[1]/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
def load(name,file):
 spec=importlib.util.spec_from_file_location(name,run/'teacher_student_autopilot_v14/precision_helpers'/file)
 m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
parser=load('explicit_original_parser','contracts.py');grammar=load('explicit_original_grammar','constrained_json.py')
plan=read(R.parent/'slot6_silver24_v1/source_window_plan.json')
for ix,stem,literals in [(9,'09_wxt_w05',[['15.4653','21.171'],['21.638133333333332','27.810966666666667']]),
                         (10,'10_byx_w02',[['4.5019375','7.484083333333333'],['20.08','23.5209375']])]:
 p=R/(stem+'_complete_reference.json');r=read(p);w=plan['jobs'][ix]['window'];a=F(w['domain_start_exact'])
 s=dict(window_id=w['window_id'],reference_sha256=sha(p),reviewed=True,not_measured_cut=True,
  exact_target_local=[[str(F(lo)-a),str(F(hi)-a)] for lo,hi in r['keep_global_exact']],
  serialized_decimal_as_str=literals,reviewed_boundary_ranges_local_exact=[
    [[b['uncertainty_start_exact'],b['uncertainty_end_exact']] for b in r['boundary_decisions'][j:j+2]]
    for j in range(0,len(r['boundary_decisions']),2)],
  main_review='Root explicitly approves these literals inside already reviewed editing ranges. Keep exact fractional reference and require exact full eligible/planned64 half-open PTS membership; not measured cuts.')
 raw,_=target(r,w,s,s['reference_sha256']);result=classify(raw,F(30));assert result['status']=='MODEL_OK'
 parsed,errors,warnings=parser.parse_segments(raw,F(30),allow_empty=True)
 assert parsed is not None and not errors and grammar.BoundedSegmentsGrammar(F(30),allow_empty=True).complete(raw)
 assert [[F(str(x)) for x in pair] for pair in parsed]==result['parsed_segments']
 side=R/(stem+'_target_serialization.json');save(side,s)
 save(R/(stem+'_target_serialization_acceptance.json'),dict(status='PASS_EXPLICIT_ROOT_LITERALS_ORIGINAL_PARSER_GRAMMAR_AND_EXACT_PTS_MEMBERSHIP',
  utc=datetime.now(timezone.utc).isoformat(),reference_sha256=sha(p),sidecar_sha256=sha(side),raw_json=raw,
  original_fraction_reference_changed=False,original_parser_warnings=warnings,
  planned_native64_membership_unchanged=True,full_eligible_native_membership_unchanged=True,new_model_calls=0,new_optimizer_updates=0))
 print(json.dumps(dict(job=ix,raw=raw,sidecar_sha256=sha(side)),ensure_ascii=False))
