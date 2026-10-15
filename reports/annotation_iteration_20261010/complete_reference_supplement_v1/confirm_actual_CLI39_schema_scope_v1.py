"""Confirm the completed single call's actual scope before explicit CLI40 admission."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys
R=Path(__file__).resolve().parent;N=R/'teacher_expansion/schema_recovery_22_23_v1';A=N/'call39'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
terminal,whole,scope=map(read,[A/'terminal.json',A/'audit.json',A/'w22_completed_scope_audit.json'])
window=read(A/'index.json')['windows'][0]['window_id']
sys.path.insert(0,str(N));from launch import previous39_documents_guard
value=dict(status='ROOT_CONFIRMED_CLI39_NATURAL_SUCCESS_AND_IMMUTABLE_SCOPE',
 utc=datetime.now(timezone.utc).isoformat(),CLI=39,window_id=window,
 ROOT_actual_scope_independently_verified=True,
 bindings={str(A/n):sha(A/n) for n in ('terminal.json','stream.jsonl','audit.json','w22_completed_scope_audit.json','actual_terminal_cost.json')})
previous39_documents_guard(terminal,whole,scope,value,window)
assert sha(A/'stream.jsonl')==terminal['stream_sha256']
assert read(A/'actual_terminal_cost.json')['terminal_sha256']==sha(A/'terminal.json')
assert not any(whole[k] for k in ('immutable_drift','rewritten_output_attempts','repeated_media_attempts'))
prefix=Path(scope['immutable_prefix']['path']);assert sha(prefix)==scope['immutable_prefix']['sha256']
assert (A/'stream.jsonl').read_bytes().startswith(prefix.read_bytes())
for x in scope['immutable_actual_outputs']:
 assert sha(x['original_path'])==x['sha256']==x['sealed_copy_sha256']==sha(x['sealed_copy_path'])
wrapper=R/'22_yi4_w03_lawful_observation_completion_CLI39_v1.json';w=read(wrapper)
assert w['window_id']==window and w['global_CLI']==39 and w['original_pngs_delivered']==64
assert w['effective_pngs_delivered']==8 and w['native_video_delivered'] and not w['tool_issues'] and not w['proposal_geometry_identity_issues']
value['ROOT_actual_helper_acceptance']={'path':str(wrapper),'sha256':sha(wrapper)}
value['semantic_adjudication_still_required']=True
ledger=[json.loads(line) for line in (R/'teacher_expansion/global_CLI_ledger.jsonl').read_text(encoding='utf-8').splitlines()]
assert max(x['global_count'] for x in ledger)==39
terms=[x for x in ledger if x['global_count']==39 and x['event']=='TERMINAL']
assert len(terms)==1 and terms[0]['terminal_sha256']==sha(A/'terminal.json') and terms[0]['raw_sha256']==sha(A/'stream.jsonl')
p=N/'root_actual_CLI39_confirmation.json'
with p.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False)
print(json.dumps({'status':value['status'],'path':str(p),'sha256':sha(p)},ensure_ascii=False))
