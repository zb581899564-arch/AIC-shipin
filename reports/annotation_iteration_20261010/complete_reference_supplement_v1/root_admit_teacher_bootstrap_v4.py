"""Independent ROOT gate: original bytes, actual prespawn recovery, text transport."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,ast,subprocess,sys
R=Path(__file__).parent;D=R/'teacher_expansion/engineering_alias_remainder_v4_bootstrap_file';OLD=D.parent/'engineering_alias_remainder_v3'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not(D/'root_start_admission.json').exists()
eb=read(D/'execution_code_binding.json')
for p,h in {**eb['sources'],**eb['prior_failure_and_transfer_inputs']}.items():assert sha(p)==h,p
sources=list(D.glob('*.py'));assert len(sources)==10
for p in sources:ast.parse(p.read_text(encoding='utf-8-sig'))
ledger=D.parent/'global_CLI_ledger.jsonl'
assert ledger.read_bytes()==(D/'global_registered34_ledger_prefix.jsonl').read_bytes()
rows=[json.loads(s) for s in ledger.read_text(encoding='utf-8').splitlines() if s.strip()]
assert rows[-1]['event']=='REGISTERED' and rows[-1]['global_count']==34 and rows[-1]['task']=='engineering_alias_remainder_v3/call34'
assert sha(OLD/'prespawn_failure_evidence/actual_prespawn_failure.json')=='9a3b342035d88c708857910ab35e16931b4476953982adc6631e92adebfffad9'
assert not(OLD/'call34/process.json').exists() and not(OLD/'call34/terminal.json').exists()
assert (OLD/'call34/stream.jsonl').stat().st_size==(OLD/'call34/stderr.txt').stat().st_size==0
aliases=read(OLD/'alias_original_payload_binding.json');assert len(aliases['rows'])==479
for row in aliases['rows']:
 assert Path(row['alias_path']).read_bytes()==Path(row['original_path']).read_bytes()
 assert sha(row['alias_path'])==(row.get('png_sha256') or row['payload_sha256'])
sys.path.insert(0,str(D))
from bootstrap import build
from launch import command,no_old_owned_processes
owned=no_old_owned_processes()
checks=[]
for n,jobs in ((34,[17,18]),(35,[19,20]),(36,[21,22,23])):
 c=D/f'call{n}';old=OLD/f'call{n}';idx=read(c/'index.json');oi=read(old/'index.json');fr=read(c/'freeze.json')
 assert not(c/'request.json').exists() and not(D/'registered.json').exists()
 assert [w['job_index'] for w in idx['windows']]==jobs
 assert fr['CLI_before']==(34 if n==34 else n-1) and fr['CLI_after']==n and fr['global_cap']==36 and fr['timeout_seconds']==7200 and not fr['automatic_retry']
 for p,h in fr['inputs'].items():assert sha(p)==h,p
 assert all(not Path(p).exists() for p in fr['write_whitelist'])
 original=(old/'frozen_prompt.txt').read_bytes()
 assert (c/'original_v3_frozen_prompt.txt').read_bytes()==original
 ack=read(idx['bootstrap_ack_expected_path'])
 assert set(ack)=={'marker','fixed_job_indices','native_required_counts','native_alias_bounds_per_window','actual_student64_per_window','effective_preview8_per_window'}
 body=(c/'bootstrap_instruction.txt').read_text(encoding='utf-8')
 lit=read(c/'literal_execution_parameters.json')
 assert build(original.decode('utf-8').replace(str(old),str(c)),idx,lit,ack)==body
 assert len(body.splitlines())<=450 and max(map(len,body.splitlines()))<=1000
 short=(c/'short_prompt.txt').read_text(encoding='utf-8')
 assert ack['marker'] not in short and ack['marker'] not in (c/'index.json').read_text(encoding='utf-8')
 assert idx['bootstrap_ack_expected_path'] not in fr['read_whitelist'] and idx['bootstrap_ack_path'] not in fr['self_read_whitelist']
 assert fr['read_whitelist'][0]==idx['bootstrap_instruction_path'] and fr['write_whitelist'][0]==idx['bootstrap_ack_path']
 for w,o in zip(idx['windows'],oi['windows']):
  assert w['native_identity_all64']==o['native_identity_all64'] and w['student_previews']==o['student_previews'] and w['clip_path']==o['clip_path']
  assert w.get('prior_context_path')==o.get('prior_context_path')
  for g,og in zip(w['groups'],o['groups']):
   assert g['frames']==og['frames'] and g['group']==og['group'] and g['output_path']==og['output_path'].replace(str(old),str(c))
  assert w['proposal_path']==o['proposal_path'].replace(str(old),str(c))
 units=len(subprocess.list2cmdline(command(n,short)).encode('utf-16-le'))//2+1
 assert units<1024 and units<32767
 checks.append(dict(CLI=n,jobs=jobs,input_count=len(fr['inputs']),freeze_sha256=sha(c/'freeze.json'),bootstrap_lines=len(body.splitlines()),argv_utf16_units_including_NUL=units))
out=dict(utc=datetime.now(timezone.utc).isoformat(),status='ROOT_APPROVED_START_BOOTSTRAP_V4_FIXED_CLI34_36',dry_run_sha256=sha(D/'dry_run_acceptance.json'),execution_binding_sha256=sha(D/'execution_code_binding.json'),root_verifier_source_sha256=sha(__file__),root_read_protocol_bootstrap_controller_launch_audit_observer_prepare_verify_common_and_run_call=True,root_all_frozen_inputs_byte_bindings_verified=True,root_all479_payload_aliases_byte_exact=True,root_original_native64_and_preview_and_clock_bindings_unchanged=True,root_old_full_prompt_byte_exact_and_only_route_path_projection_and_text_reflow_verified=True,root_actual_old_prespawn_failure_and_unchanged_registration_prefix_verified=True,readonly_owned_process_check=owned,calls=checks,registration_recovery_explanation='The preserved old REGISTERED34 never spawned AGY; recover that not-started model slot once with RECOVERY_REGISTERED34. No ledger rollback or model retry. Request prior_actual_spawned_CLI=33 denotes the fixed historical prespawn recovery checkpoint, not the later live predecessor for 35/36; actual process/request/terminal and tools decide spawned call counts.',global_cap=36,no37=True,automatic_retry=False,cash_cost='UNKNOWN_NOT_ZERO',new_model_calls_at_gate=0,semantic_admission=False,training_admitted=False)
with (D/'root_start_admission.json').open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(dict(gate_sha256=sha(D/'root_start_admission.json'),status=out['status'],calls=checks),ensure_ascii=False))

