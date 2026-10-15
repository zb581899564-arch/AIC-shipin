"""Preserve whole rejection and independently identify earlier immutable media prefixes."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path(__file__).resolve().parent;V4=R/'teacher_expansion/engineering_alias_remainder_v4_bootstrap_file';V5=V4.parent/'engineering_alias_remainder_v5_line_representation_controller'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):return dict(path=str(p),sha256=sha(p))
a=V4/'call34';raw=(a/'stream.jsonl').read_bytes();terminal=read(a/'terminal.json');audit=read(a/'audit.json')
assert terminal['stream_sha256']==sha(a/'stream.jsonl') and terminal['child_process_created']
assert audit['actual_result_status']=='ERROR'
fullproof=read(V5/'call34/line_representation_final.json');assert fullproof['status']=='REJECT_ACTUAL_OTHER_FAILURE_NO_MODEL_RETRY'
outside=[i for i in audit['tool_issues'] if i['reason']=='OUTSIDE_READ_WHITELIST_ATTEMPT']
assert [i['step'] for i in outside]==[214,216]
rows=[json.loads(line) for line in raw.splitlines()]
tools=[r['step_update'] for r in rows if r.get('step_update',{}).get('step_type')=='tool' and r['step_update']['state']=='DONE']
prefixes=[]
for job,name in [(17,'17_eyq_w04_lawful_observation_completion.json'),(18,'18_j0n_w02_lawful_observation_completion.json')]:
    p=R/name;media=read(p);prefix=Path(media['stream_prefix']['path']);payload=prefix.read_bytes()
    assert sha(prefix)==media['stream_prefix']['sha256'] and raw.startswith(payload)
    earlier=[json.loads(line) for line in payload.splitlines()]
    prefix_end=max(t['step_update']['step_index'] for t in earlier if t.get('step_update',{}).get('step_type')=='tool')
    assert prefix_end<214
    scope=read(media['prefix_audit']['path']);w=next(w for w in scope['windows'] if w['job_index']==job)
    for fact in w['bound_fact_rows']:assert sha(fact['raw_fact_output']['path'])==fact['raw_fact_output']['sha256']
    assert sha(media['proposal']['path'])==media['proposal']['sha256']
    assert not any(t['step_index']>prefix_end and t.get('tool_name')=='write_to_file' and
        t.get('tool_info',{}).get('parameters',{}).get('TargetFile') in [media['proposal']['path'],*(f['raw_fact_output']['path'] for f in w['bound_fact_rows'])] for t in tools)
    prefixes.append(dict(job_index=job,root_media_receipt=bind(p),immutable_prefix=media['stream_prefix'],last_prefix_tool_step=prefix_end,
        before_actual_outside_steps=True,no_later_rewrite_of_facts_or_proposal=True,current_output_SHAs_equal_sealed_scope=True))
value=dict(status='WHOLE_CLI34_REJECTED_EARLIER_LAWFUL_SCOPE_EVIDENCE_SEPARATELY_PRESERVED',utc=datetime.now(timezone.utc).isoformat(),
    terminal=bind(a/'terminal.json'),raw=bind(a/'stream.jsonl'),whole_original_audit=bind(a/'audit.json'),
    whole_v5_rejection=bind(V5/'call34/line_representation_final.json'),actual_wall_seconds=terminal['wall_seconds'],
    actual_result_status='ERROR',outside_reads=[dict(step=i['step'],reason=i['reason']) for i in outside],
    prefixes=prefixes,whole_call_never_reclassified_as_PASS=True,no_internal_log_read_by_ROOT=True,
    inactive_v5_fullsuccess_start_gate_not_executed=True,unused_model_calls_35_36_not_started=True,no34_retry=True,
    no37=True,new_model_calls=0,new_optimizer_updates=0,cash_cost='UNKNOWN_NOT_ZERO')
out=R/'teacher34_terminal_reconciliation_v1.json'
with out.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
print(json.dumps(bind(out),ensure_ascii=False))
