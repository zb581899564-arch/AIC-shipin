"""Bind actual text supply; no change to the running teacher or frozen audits."""
from pathlib import Path
from datetime import datetime,timezone
import json,re,hashlib
R=Path(__file__).parent;V=R/'teacher_expansion/engineering_alias_remainder_v4_bootstrap_file'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def bind(p):return dict(path=str(p),sha256=hashlib.sha256(Path(p).read_bytes()).hexdigest())
proofp=V/'actual_readonly_bootstrap_evidence/CLI34_actual_bootstrap_ACK_supply.json';proof=read(proofp)
prefix=Path(proof['immutable_prefix']['path']).read_bytes()
assert bind(proof['immutable_prefix']['path'])['sha256']==proof['immutable_prefix']['sha256']
assert (V/'call34/stream.jsonl').read_bytes().startswith(prefix)
states={}
for r in map(json.loads,prefix.splitlines()):
 t=r.get('step_update',{})
 if t.get('step_type')=='tool':
  assert t.get('state')!='ERROR'
  states[t['step_index']]=t
tools=[t for _,t in sorted(states.items())]
assert len(tools)==2 and all(t['state']=='DONE' for t in tools)
c=V/'call34';idx=read(c/'index.json');fr=read(c/'freeze.json');req=read(c/'request.json')
assert req['freeze_sha256']==bind(c/'freeze.json')['sha256']
bp=Path(idx['bootstrap_instruction_path']);blob=bp.read_bytes()
assert fr['inputs'][str(bp)]==bind(bp)['sha256']
assert blob.endswith(b'\n') and b'\r' not in blob
t0,t1=tools
assert t0['tool_name']=='view_file' and t0['tool_info']['parameters']=={'AbsolutePath':str(bp)}
assert t1['tool_name']=='write_to_file' and Path(t1['tool_info']['parameters']['TargetFile'])==Path(idx['bootstrap_ack_path'])
out=t0['tool_info']['output'];nbytes=int(re.search(r'(\d+) bytes',out).group(1));nlines=int(re.search(r'(\d+) lines',out).group(1))
assert nbytes==len(blob) and nlines==len(blob.split(b'\n'))==len(blob.splitlines())+1
expected=read(idx['bootstrap_ack_expected_path']);actual=read(idx['bootstrap_ack_path'])
assert actual==expected and expected['marker'] not in (c/'short_prompt.txt').read_text(encoding='utf-8')
assert expected['marker'] not in (c/'index.json').read_text(encoding='utf-8')
assert idx['bootstrap_ack_expected_path'] not in fr['read_whitelist']
op=R/'bootstrap_line_representation_erratum_v1.json'
result=dict(status='PASS_ROOT_ACTUAL_TEXT_LINE_REPRESENTATION_PROOF_NOT_TEACHER_SCOPE_OR_SEMANTIC_ADMISSION',utc=datetime.now(timezone.utc).isoformat(),source=bind(__file__),actual_bootstrap_supply_proof=bind(proofp),actual_two_tool_prefix=proof['immutable_prefix'],bootstrap_instruction=bind(bp),actual_ACK=bind(idx['bootstrap_ack_path']),program_expected_ACK=bind(idx['bootstrap_ack_expected_path']),original_v4_audit_source=bind(V/'audit.py'),original_root_gate=bind(V/'root_start_admission.json'),reported_bytes=nbytes,reported_lines=nlines,python_splitlines_count=len(blob.splitlines()),exact_LF_split_count=len(blob.split(b'\n')),ends_with_LF=True,actual_bytes_and_tail_six_field_ACK_exact=True,scopes_still_incomplete_and_unadmitted=True,rule='For independent future scope reconstruction only: require original reported bytes exactly equal frozen payload; reported lines exactly len(payload.split(LF)); tailLF and noCR; correct unique tail ACK and first view/second write tool order. No plus-or-minus tolerance. Keep original frozen v4 audit rejection and source unchanged; accept no media/error/order/schema exception.',teacher_science_targets_frames_clock_and_quality_gate_changed=False,old_v3_zero_spawn_registration_and_old_real_model_costs_preserved=True,new_model_calls_in_this_CPU_proof=0,new_optimizer_updates=0,cash_cost='UNKNOWN_NOT_ZERO')
with op.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(bind(op),ensure_ascii=False))

