"""Expose complete actual fact groups for ROOT reading without giant audit metadata."""
from pathlib import Path
import argparse, hashlib, json
R=Path(__file__).parent
V=R/'teacher_expansion/engineering_CLI36_37_split_fragment_v8v5'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
ap=argparse.ArgumentParser();ap.add_argument('--job',type=int,required=True);ap.add_argument('--first-group',type=int);ap.add_argument('--groups',type=int,default=4);ap.add_argument('--proposal',action='store_true');a=ap.parse_args()
assert a.job in range(19,24)
c=V/f"call{36 if a.job<21 else 37}";p=c/f'w{a.job:02d}_completed_scope_audit.json';d=read(p)
assert d['status']=='PASS_IMMUTABLE_ACTUAL_SCOPE_PENDING_ROOT_SEMANTIC'
prefix=d['immutable_prefix'];assert sha(prefix['path'])==prefix['sha256']
assert (c/'stream.jsonl').read_bytes().startswith(Path(prefix['path']).read_bytes())
for b in d['immutable_actual_outputs']:
 assert sha(b['original_path'])==b['sha256'] and sha(b['sealed_copy_path'])==b['sealed_copy_sha256']
w=next(w for w in d['windows'] if w['job_index']==a.job)
assert w['bound_rows']==64 and not w['schema_issues'] and not w['proposal_issues']
if a.proposal:
 print(json.dumps({'job':a.job,'window_id':w['window_id'],'scope_sha256':sha(p),'proposal':read(w['proposal_path']),'proposal_sha256':sha(w['proposal_path'])},ensure_ascii=False))
else:
 assert a.first_group is not None and 0<=a.first_group<16 and 0<a.groups<=4
 selected=[x for x in w['bound_fact_rows'] if a.first_group<=x['group']<min(16,a.first_group+a.groups)]
 assert len(selected)==min(a.groups,16-a.first_group)*4
 print(json.dumps({'job':a.job,'first_group':a.first_group,'last_group':a.first_group+a.groups-1,'facts':[{'frame_id':x['identity']['frame_id'],'group':x['group'],'slot':x['slot'],'facts':x['facts']} for x in selected]},ensure_ascii=False))
