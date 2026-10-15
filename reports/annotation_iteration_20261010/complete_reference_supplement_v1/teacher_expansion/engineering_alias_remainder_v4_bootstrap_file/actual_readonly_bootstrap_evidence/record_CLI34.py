"""Actual read-only bootstrap/ACK prefix evidence; never reclassifies frozen audit."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;a=ROOT/'call34'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def key(p):return str(Path(p).resolve()).casefold()
idx=read(a/'index.json');raw=(a/'stream.jsonl').read_bytes();done=[];cut=None;position=0
for line in raw.splitlines(keepends=True):
 position+=len(line)
 try:r=json.loads(line)
 except Exception:break
 t=r.get('step_update',{})
 if t.get('step_type')=='tool' and t.get('state')=='DONE':
  done.append(t);p=t.get('tool_info',{}).get('parameters',{})
  if t.get('tool_name')=='write_to_file' and key(p.get('TargetFile',''))==key(idx['bootstrap_ack_path']):cut=position;break
assert cut is not None and len(done)==2 and done[0]['tool_name']=='view_file' and done[1]['tool_name']=='write_to_file'
assert key(done[0]['tool_info']['parameters']['AbsolutePath'])==key(idx['bootstrap_instruction_path'])
assert read(idx['bootstrap_ack_path'])==read(idx['bootstrap_ack_expected_path'])
file=Path(idx['bootstrap_instruction_path']);payload=file.read_bytes()
lf_count=len(payload.split(bytes([10])))
assert done[0]['tool_info']['output']==f"{lf_count} lines, {len(payload)} bytes"
prefix=HERE/'CLI34_bootstrap_ACK_actual_immutable_prefix.jsonl'
with prefix.open('xb') as f:f.write(raw[:cut])
fr=read(a/'freeze.json')
assert all(sha(p)==s for p,s in fr['inputs'].items())
out=dict(utc=datetime.now(timezone.utc).isoformat(),status='ACTUAL_BOOTSTRAP_ACK_SUPPLY_EVIDENCE_NOT_FROZEN_AUDIT_PASS',CLI=34,actual_DONE_tools=done,bootstrap_instruction_path=str(file),bootstrap_SHA=sha(file),bootstrap_actual_reported_output=done[0]['tool_info']['output'],byte_count=len(payload),python_splitlines_count=len(payload.splitlines()),split_LF_count=len(payload.split(b'\n')),ends_with_LF=payload.endswith(b'\n'),actual_ack_path=idx['bootstrap_ack_path'],actual_ack_SHA=sha(idx['bootstrap_ack_path']),actual_ack_matches_all_six_expected_fields=True,expected_ack_path=idx['bootstrap_ack_expected_path'],expected_ack_SHA=sha(idx['bootstrap_ack_expected_path']),immutable_prefix=dict(path=str(prefix),sha256=sha(prefix),bytes=cut),request_SHA=sha(a/'request.json'),freeze_SHA=sha(a/'freeze.json'),root_gate_SHA=sha(ROOT/'root_start_admission.json'),registered_SHA=sha(ROOT/'registered.json'),actual_AGY_pid=read(a/'process.json')['pid'],all_frozen_inputs_verified=len(fr['inputs']),frozen_audit_line_representation='Python splitlines expects212; actual AGY tool reports213 with trailing LF; frozen source unchanged and not reclassified',limited_evidence='Exact tool paths/order/DONE/full-byte metadata and unique tail ACK match. No claim of complete textual attention, semantics or training admission.',cash_cost='UNKNOWN_NOT_ZERO',automatic_retry=False)
receipt=HERE/'CLI34_actual_bootstrap_ACK_supply.json'
with receipt.open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(receipt_path=str(receipt),receipt_SHA=sha(receipt),prefix_SHA=sha(prefix),actual_ack_SHA=sha(idx['bootstrap_ack_path']),DONE_steps=[t['step_index'] for t in done]),ensure_ascii=False))
