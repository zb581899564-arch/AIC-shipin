"""Actual local checkpoint; does not imply remote/runtime/model acceptance."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):return dict(path=str(p),sha256=sha(p))
p=R/'denominator24_v16.json';r=read(p);old=read(R/'denominator24_v9.json')
assert (r['qualified_references'],r['rejected_references'],r['pending_references'],r['accepted_train_windows'])==(15,4,5,8)
current_train={k:v['reference']['sha256'] for k,v in r['records'].items() if v['training_admitted']}
old_train={k:v['reference']['sha256'] for k,v in old['records'].items() if v['training_admitted']}
assert current_train==old_train and len(current_train)==8
references=[]
for key,row in r['records'].items():
    if row.get('reference'):
        assert sha(row['reference']['path'])==row['reference']['sha256']
        references.append(dict(window_id=key,training_admitted=row['training_admitted'],reference=row['reference']))
validation=read(R/'runtime_validation_v5.json')
assert validation['tests']==51 and validation['AST_files']==23
for path,s in validation['sources'].items():assert sha(path)==s
baseline=R.parents[2]/'deliveries/ANNOTATION_ITERATION_20261010/SAFE_37_66/candidate_SAFE_37_66.zip'
assert baseline.stat().st_size==306167 and sha(baseline)=='07730c9e02e68d1a1ce54e7ef5a8aa616346cf8f2f8d78426ed36bc3eb481496'
out=R/'root_checkpoint15_references_not_training_v1.json'
value=dict(status='PASS_LOCAL15_REFERENCE_BINDINGS_UNCHANGED_TRAIN8_AND_RUNTIME_NOT_REMOTE_ACCEPTANCE',
    utc=datetime.now(timezone.utc).isoformat(),registry=bind(p),qualified_references=15,rejected_references=4,pending_references=5,
    accepted_train_windows=8,training_targets_unchanged_since_readiness_v2=True,training_static_readiness=bind(R/'training8_static_readiness_v2.json'),
    runtime_static_validation=bind(R/'runtime_validation_v5.json'),all23_runtime_source_SHAs_unchanged=True,
    baseline=bind(baseline),baseline_bytes=306167,new_training_started=False,new_optimizer_updates=0,
    new_evaluation_model_calls=0,new426_model_calls=0,new_submission_ZIP_exists=False,
    source_transfer_permission_pending=True,source_upload_completed=False,all12_evaluation_references_required=True,
    references=references)
with out.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
print(json.dumps(bind(out),ensure_ascii=False))
