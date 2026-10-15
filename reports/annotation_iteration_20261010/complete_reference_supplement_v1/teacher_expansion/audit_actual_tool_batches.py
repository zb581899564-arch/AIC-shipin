"""Independent post-terminal audit of actual response ownership and image barriers."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def key(p):return str(Path(p).resolve()).casefold()
a=Path(sys.argv[1]).resolve();idx=read(a/'index.json');terminal=read(a/'terminal.json')
assert sha(a/'stream.jsonl')==terminal['stream_sha256']
rows=[json.loads(s) for s in (a/'stream.jsonl').read_text(encoding='utf-8-sig').splitlines() if s.strip()]
owner=None;tools=[]
for r in rows:
    t=r.get('step_update',{})
    if t.get('state')!='DONE':continue
    if t.get('step_type')=='agent_response':owner=t.get('step_index')
    if t.get('step_type')=='tool':
        p=t.get('tool_info',{}).get('parameters',{})
        tools.append(dict(step=t.get('step_index'),response_step=owner,tool=t.get('tool_name'),path=key(p.get('AbsolutePath') or p.get('TargetFile'))))
wins=[];allissues=[]
for w in idx['windows']:
    groups=[];issues=[]
    for g in w['groups']:
        expected=[key(f['path']) for f in g['frames']]
        observed=[t for t in tools if t['tool']=='view_file' and t['path'] in expected]
        writes=[t for t in tools if t['tool']=='write_to_file' and t['path']==key(g['output_path'])]
        if len(observed)!=4 or [t['path'] for t in observed]!=expected or len({t['response_step'] for t in observed})!=1:
            issues.append(dict(reason='GROUP_NOT_FOUR_ORDERED_READS_IN_ONE_RESPONSE',group=g['group']))
        if len(writes)!=1 or len(observed)!=4 or writes[0]['response_step'] is None or writes[0]['response_step']<=max(t['step'] for t in observed):
            issues.append(dict(reason='FACT_WRITE_REQUESTED_BEFORE_MODEL_RECEIVED_ALL_FOUR_DONE',group=g['group']))
        groups.append(dict(group=g['group'],reads=observed,writes=writes))
    previews=[t for t in tools if t['tool']=='view_file' and t['path'] in {key(f['path']) for f in w['student_previews']}]
    expectedpreview=[key(f['path']) for f in w['student_previews']]
    if len(previews)!=8 or [t['path'] for t in previews]!=expectedpreview or len({t['response_step'] for t in previews})!=1:
        issues.append(dict(reason='PREVIEWS_NOT_EIGHT_ORDERED_READS_IN_ONE_RESPONSE'))
    proposals=[t for t in tools if t['tool']=='write_to_file' and t['path']==key(w['proposal_path'])]
    if len(proposals)!=1 or len(previews)!=8 or proposals[0]['response_step'] is None or proposals[0]['response_step']<=max(t['step'] for t in previews):
        issues.append(dict(reason='PROPOSAL_REQUESTED_BEFORE_MODEL_RECEIVED_ALL_EIGHT_PREVIEW_DONE'))
    wins.append(dict(job_index=w['job_index'],window_id=w['window_id'],status='PASS_ACTUAL_RESPONSE_BATCHES_AND_OBSERVATION_BARRIERS' if not issues else 'REJECT_BATCH_DISPATCH_KEEP_RAW',groups=groups,previews=previews,proposal_write=proposals,issues=issues))
    allissues.extend(dict(job_index=w['job_index'],**i) for i in issues)
v=dict(utc=datetime.now(timezone.utc).isoformat(),status='PASS_ACTUAL_TOOL_BATCHES_NOT_SEMANTIC_ADMISSION' if not allissues else 'REJECT_BATCH_DISPATCH_KEEP_RAW',windows=wins,issues=allissues,terminal_sha256=sha(a/'terminal.json'),raw_sha256=sha(a/'stream.jsonl'),auditor_sha256=sha(Path(__file__)),new_model_calls=0,semantic_correctness='PENDING_ROOT_REVIEW',training_admitted=False)
out=a/'actual_tool_batch_audit.json'
with out.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(path=str(out),sha256=sha(out),status=v['status'],issues=len(allissues)),ensure_ascii=False))
