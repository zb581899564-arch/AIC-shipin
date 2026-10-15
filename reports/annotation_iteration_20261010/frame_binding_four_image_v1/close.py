from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
ROOT=Path(__file__).resolve().parent; PRIOR=ROOT.parent/'independent_highlight_pilot_v3'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def bound(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
audit=read(ROOT/'audit.json'); main=read(ROOT/'main_fact_review.json');freeze=read(ROOT/'freeze.json')
for n,s in freeze['files'].items():assert bound(ROOT/n)['sha256']==s
assert bound(ROOT/'program_bound_facts.json')['sha256']==audit['program_bound_facts_sha256']
assert audit['status']=='FIELD_COMPARISON_PASS_PENDING_MAIN_FACT_REVIEW'
assert read(PRIOR/'acceptance.json')['status']=='STOP_FIRST_PILOT_DO_NOT_EXPAND_OR_TRAIN'
safe=ROOT.parents[2]/'deliveries/ANNOTATION_ITERATION_20261010/SAFE_37_66/candidate_SAFE_37_66.zip'
assert bound(safe)['sha256']=='07730c9e02e68d1a1ce54e7ef5a8aa616346cf8f2f8d78426ed36bc3eb481496'
out=dict(status='PARTIAL_METHOD_GAIN_NO_COMPLETE_REFERENCE_ADMISSION',utc=datetime.now(timezone.utc).isoformat(),
 structured_field_comparison_pass=True,structured_facts=20,checks_per_fact=4,program_identity_rows=20,
 free_text_rejections=3,fully_accepted_minimum_method_test=False,full_window_qualified=False,
 evidence={n:bound(ROOT/n) for n in ('freeze.json','audit.json','program_bound_facts.json','main_fact_review.json')},
 prior_v3_acceptance=bound(PRIOR/'acceptance.json'),safe_baseline=bound(safe),
 terminal=bound(ROOT/'attempt01/terminal.json'),new_CLI_calls=1,total_registered_CLI=23,CLI_cap=36,
 cash_cost='UNKNOWN_NOT_ZERO',new_training=0,new_GPU=0,new_426=0,new_Pro=0,new_zip=False,
 repeat_same_hypothesis_calls=False,expanded_other_windows=False,
 remaining_evidence='This fact-only sample neither resolves complete highlight preference nor produces a new complete-window reference. Original pilot STOP and all train/locked/spatial gates remain.',
 minimum_external_review_if_needed='Independent editor may start with this fixed30s window using native64 plus actual student64 and the fixed boundary observation ranges; review every KEEP/NO and each boundary. No new user media required; editor need not be user. Full admission still requires original 8-12 train windows/at least4sources and locked at least6/8 across all4sources. Human spatial gold requires a separate qualified reference and is not supplied by this model test.')
with (ROOT/'acceptance.json').open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(status=out['status'],fields='80/80',free_text_rejections=3,total_CLI=23,new_training=0,new_zip=False,baseline_sha=bound(safe)['sha256']),ensure_ascii=False))
