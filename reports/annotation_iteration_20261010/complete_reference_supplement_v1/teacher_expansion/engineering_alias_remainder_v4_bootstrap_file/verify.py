"""Independent CPU-only verification; in-memory negative cases are not observations."""
from pathlib import Path
from datetime import datetime,timezone
import ast,json,hashlib,subprocess,struct
from common import ROOT,BASE,read,sha,key,save,expected_core
OLD=BASE/'engineering_alias_remainder_v3'
def main():
 assert not(ROOT/'root_start_admission.json').exists() and not(ROOT/'registered.json').exists()
 binding=read(ROOT/'execution_code_binding.json')
 for p,s in {**binding['sources'],**binding['prior_failure_and_transfer_inputs']}.items():assert sha(p)==s
 assert (BASE/'global_CLI_ledger.jsonl').read_bytes()==(ROOT/'global_registered34_ledger_prefix.jsonl').read_bytes()
 from launch import no_old_owned_processes,command
 owned=no_old_owned_processes()
 aliases=read(OLD/'alias_original_payload_binding.json')
 for row in aliases['rows']:
  assert Path(row['alias_path']).read_bytes()==Path(row['original_path']).read_bytes()
  assert sha(row['alias_path'])==(row.get('png_sha256') or row['payload_sha256'])
  if row['kind']!='clip':assert list(struct.unpack('>II',Path(row['alias_path']).read_bytes()[16:24]))==row['geometry']
 calls=[]
 for n,jobs in ((34,[17,18]),(35,[19,20]),(36,[21,22,23])):
  a=ROOT/f'call{n}';old=OLD/f'call{n}';idx=read(a/'index.json');oi=read(old/'index.json');fr=read(a/'freeze.json')
  assert [w['job_index'] for w in idx['windows']]==jobs
  for p,s in fr['inputs'].items():assert sha(p)==s
  assert not(a/'request.json').exists() and all(not Path(p).exists() for p in fr['write_whitelist'])
  assert idx['bootstrap_instruction_path']==fr['bootstrap_instruction_path']
  original=(old/'frozen_prompt.txt').read_bytes();bootstrap=(a/'bootstrap_instruction.txt').read_bytes()
  assert (a/'original_v3_frozen_prompt.txt').read_bytes()==original
  from bootstrap import build
  assert bootstrap==build(original.decode('utf-8').replace(str(old),str(a)),idx,read(a/'literal_execution_parameters.json'),read(idx['bootstrap_ack_expected_path'])).encode('utf-8')
  assert len(bootstrap.splitlines())<=450 and max(map(len,bootstrap.decode('utf-8').splitlines()))<=1000
  marker=read(idx['bootstrap_ack_expected_path'])['marker']
  assert marker not in (a/'short_prompt.txt').read_text(encoding='utf-8') and marker not in (a/'index.json').read_text(encoding='utf-8')
  assert idx['bootstrap_ack_expected_path'] not in fr['read_whitelist'] and idx['bootstrap_ack_path'] not in fr['self_read_whitelist']
  assert fr['write_whitelist'][0]==idx['bootstrap_ack_path']
  assert fr['read_whitelist'][0]==str(a/'bootstrap_instruction.txt')
  for w,o in zip(idx['windows'],oi['windows']):
   assert w['native_identity_all64']==o['native_identity_all64'] and w['student_previews']==o['student_previews'] and w['clip_path']==o['clip_path']
   assert w.get('prior_context_path')==o.get('prior_context_path')
   assert len(w['native_identity_all64'])==64 and len(w['student_previews'])==8 and w['actual_student_frames']==64
   for g,og in zip(w['groups'],o['groups']):
    assert g['frames']==og['frames'] and g['group']==og['group']
    assert g['output_path']==og['output_path'].replace(str(old),str(a))
   assert w['proposal_path']==o['proposal_path'].replace(str(old),str(a))
  assert len(expected_core(idx))=={34:143,35:183,36:273}[n]
  scope={w['job_index']:len(expected_core(idx,w['job_index'])) for w in idx['windows']}
  assert scope==({17:53,18:143} if n==34 else {19:93,20:183} if n==35 else {21:93,22:183,23:273})
  cmd=command(n,(a/'short_prompt.txt').read_text(encoding='utf-8'));units=len(subprocess.list2cmdline(cmd).encode('utf-16-le'))//2+1
  assert units<1024 and units<32767
  calls.append(dict(CLI=n,jobs=jobs,core_with_bootstrap_ack=len(expected_core(idx)),context_steps=fr['context_read_count'],scope_prefix_core_counts=scope,argv_utf16_units_including_NUL=units,input_count=len(fr['inputs']),freeze_sha256=sha(a/'freeze.json'),index_sha256=sha(a/'index.json'),bootstrap_sha256=sha(a/'bootstrap_instruction.txt'),short_prompt_sha256=sha(a/'short_prompt.txt')))
 AST=[]
 for p in ROOT.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'));AST.append(dict(path=str(p),sha256=sha(p)))
 from audit import inspect
 a=ROOT/'call35';idx=read(a/'index.json')
 def tool(step,path,state='DONE',output='',parameters=None):return dict(event='step_update',step_update=dict(step_index=step,state=state,step_type='tool',tool_name='view_file',tool_info=dict(parameters=parameters or {'AbsolutePath':path},output=output)))
 def test(rows):return inspect(a,b'\n'.join(json.dumps(r).encode('utf-8') for r in rows))
 bp=idx['bootstrap_instruction_path'];size=Path(bp).stat().st_size;lines=len(Path(bp).read_bytes().splitlines());full=f'{lines} lines, {size} bytes'
 cases=[('missing',[]),('error',[tool(1,bp,'ERROR')]),('truncated',[tool(1,bp,output=f'{lines} lines, {size-1} bytes')]),('repeat',[tool(1,bp,output=full),tool(2,bp,output=full)]),('not_first',[tool(1,idx['index_path']),tool(2,bp,output=full)]),('range',[tool(1,bp,output=full,parameters={'AbsolutePath':bp,'StartLine':1})])]
 for name,rows in cases:
  d=test(rows);assert not d['bootstrap_successful_complete'] and not d['teacher_task_completed'],name
 correct=test([tool(1,bp,output=full)]);assert correct['bootstrap_successful_complete'] and not correct['bootstrap_ack_complete'] and not correct['teacher_task_completed']
 media=test([tool(1,bp,output=full),tool(2,idx['windows'][0]['groups'][0]['frames'][0]['path'],'ERROR')]);assert media['errored_tool_attempts'] and not media['teacher_task_completed']
 # ACK ordering/content acceptance tested using only in-memory read substitution; no output/raw file created.
 import audit as am
 original_read=am.read
 def ack_read(path):return read(idx['bootstrap_ack_expected_path']) if key(path)==key(idx['bootstrap_ack_path']) else original_read(path)
 am.read=ack_read
 ack_tool=dict(event='step_update',step_update=dict(step_index=2,state='DONE',step_type='tool',tool_name='write_to_file',tool_info=dict(parameters={'TargetFile':idx['bootstrap_ack_path']})))
 good_ack=test([tool(1,bp,output=full),ack_tool,tool(3,idx['index_path'])]);assert good_ack['bootstrap_ack_complete'] and not good_ack['teacher_task_completed']
 wrong_order=test([tool(1,bp,output=full),tool(3,idx['index_path']),ack_tool]);assert not wrong_order['bootstrap_ack_complete']
 def wrong_read(path):return {'marker':'WRONG'} if key(path)==key(idx['bootstrap_ack_path']) else original_read(path)
 am.read=wrong_read
 wrong_ack=test([tool(1,bp,output=full),ack_tool,tool(3,idx['index_path'])]);assert not wrong_ack['bootstrap_ack_complete']
 am.read=original_read
 save(ROOT/'independent_preparation_acceptance.json',dict(status='PASS_CPU_PREPARATION_BOOTSTRAP_TRANSPORT_NO_MODEL',utc=datetime.now(timezone.utc).isoformat(),AST=AST,calls=calls,all479_alias_payloads_byte_exact=True,all_native_clock_identity_preview_original_paths_unchanged=True,original_prompt_byte_exact_and_projection_only=True,in_memory_bootstrap_negative_cases=[x[0] for x in cases],in_memory_media_ERROR_rejects=True,synthetic_cases_not_actual_observation=True,readonly_no_v3_owned_process=owned,prespawn_failure_sha256=sha(OLD/'prespawn_failure_evidence/actual_prespawn_failure.json'),execution_binding_sha256=sha(ROOT/'execution_code_binding.json'),dry_run_sha256=sha(ROOT/'dry_run_acceptance.json'),root_gate_absent=True,global_registered=34,prior_actual_spawned_CLI=33,global_cap=36,new_model_calls=0,new_video_decode=0,cash_cost='UNKNOWN_NOT_ZERO'))
 print(json.dumps(dict(receipt_sha256=sha(ROOT/'independent_preparation_acceptance.json'),protocol_sha256=sha(ROOT/'PROTOCOL.md'),AST_count=len(AST),calls=calls),ensure_ascii=False))
if __name__=='__main__':main()
