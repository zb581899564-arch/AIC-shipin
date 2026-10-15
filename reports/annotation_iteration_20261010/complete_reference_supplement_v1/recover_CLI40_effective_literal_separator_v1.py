"""One typed ROOT recovery of exactly eight CLI40 duplicate separators; never modify raw or call a model."""
from pathlib import Path
import argparse,copy,ctypes,hashlib,importlib.util,json,os
from ctypes import wintypes
from datetime import datetime,timezone
R=Path(__file__).resolve().parent
V=R/'teacher_expansion/schema_recovery_23_continuation_v2'
C=V/'call40'
STEPS=(188,189,190,191,193,194,195,196)
ISSUE='ANY_RAW_VIEW_PARAMETERS_NOT_EXACT_LITERAL'
GATE_STATUS='ROOT_APPROVED_CLI40_EXACT_EIGHT_EFFECTIVE_SINGLE_SEPARATOR_RECOVERY_NO_NEW_MODEL'
STATUS='PASS_TYPED_CLI40_EXACT_EIGHT_SINGLE_SEPARATOR_RECOVERY_OLD_REJECT_PRESERVED_PENDING_SEMANTIC'
RECEIPT=R/'CLI40_effective_literal_separator_recovery_receipt_v1.json'
GATE=R/'CLI40_effective_literal_separator_root_recovery_admission_v1.json'
HELPERS=('recover_CLI40_effective_literal_separator_v1.py','accept_teacher_schema_recovery23_literal_separator_recovery_v3.py')

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):return dict(path=str(Path(p).resolve()),sha256=sha(p))
def load_base():
 p=R/'accept_teacher_schema_recovery23_continuation_v2.py';spec=importlib.util.spec_from_file_location('root_cli40_original_scope_helper',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def required_bindings():
 paths=[*(C/n for n in ('terminal.json','stream.jsonl','audit.json','w23_completed_scope_audit.json','actual_terminal_cost.json','request.json','freeze.json','index.json')),
  V/'root_start_admission_CLI40.json',*(V/n for n in ('execution_code_binding.json','dry_run_acceptance.json','independent_CPU_negative_acceptance.json'))]
 return {str(p):sha(p) for p in paths}

def exact_separator(actual,expected):
 """Accept only one inserted backslash at this one registered anchor; no normalization."""
 anchor='engineering_alias_remainder_v3'+chr(92)+'aliases'+chr(92)+'w23'+chr(92)+'effective'+chr(92)
 assert expected.count(anchor)==1 and expected.endswith('.png')
 position=expected.index(anchor)+len('engineering_alias_remainder_v3')
 assert actual==expected[:position]+chr(92)+expected[position:]
 assert actual.encode('utf-8')==expected[:position].encode('utf-8')+b'\\'+expected[position:].encode('utf-8')
 return position

def project_rows(rows,previews):
 assert len(previews)==8
 out=copy.deepcopy(rows);changes=[];seen={step:[] for step in STEPS}
 for position,r in enumerate(out):
  t=r.get('step_update',{})
  if t.get('step_type')!='tool' or t.get('step_index') not in STEPS:continue
  step=t['step_index'];f=previews[STEPS.index(step)];p=t.get('tool_info',{}).get('parameters',{})
  assert t['tool_name']==t['tool_info']['name']=='view_file' and t['state'] in ('ACTIVE','DONE') and set(p)=={'AbsolutePath'}
  original=p['AbsolutePath'];at=exact_separator(original,f['path']);seen[step].append(t['state'])
  changes.append(dict(raw_row_position=position,step=step,state=t['state'],original_parameters=copy.deepcopy(p),expected_parameters={'AbsolutePath':f['path']},inserted_separator_offset=at))
  p['AbsolutePath']=f['path']
 assert all(states==['ACTIVE','DONE'] for states in seen.values()) and len(changes)==16
 # No row/field/token other than the sixteen explicit AbsolutePath strings changes.
 back=copy.deepcopy(out)
 for change in changes:back[change['raw_row_position']]['step_update']['tool_info']['parameters']=change['original_parameters']
 assert back==rows
 return out,changes

def expected_issues(changes):
 return [dict(reason=ISSUE,step=x['step'],actual_parameters=x['original_parameters'],job_index=23) for x in changes]

def document_guard(terminal,whole,scope,changes):
 issues=expected_issues(changes)
 assert terminal['CLI_after']==40 and terminal['child_process_created'] is True and terminal['exit_code']==0 and terminal['stop_reason'] is None and terminal['launch_exception'] is None
 assert whole['status']=='REJECTED_WHOLE_CLI_KEEP_ALL_ACTUAL_RAW_COST' and whole['actual_result_status']=='SUCCESS' and whole['actual_result_error'] is None
 assert scope['status']=='REJECT_ACTUAL_SCOPE_KEEP_RAW_NO_RETRY'
 assert whole['tool_issues']==scope['tool_issues']==scope['windows'][0]['local_tool_issues']==issues
 assert whole['actual_core_tool_calls']==scope['actual_core_tool_calls']==whole['expected_core_tool_calls']==scope['expected_core_tool_calls']==128
 for obj in (whole,scope):
  for key in ('all_raw_tool_state_issues','errored_tool_attempts','unfinished_tool_attempts','reported_nonmedia_errors','error_message_steps'):assert not obj[key]
 for key in ('actual_post_last_proposal_tool_updates','actual_pre_completion_result_ERRORS','actual_post_completion_result_ERRORS','immutable_drift','repeated_media_attempts','rewritten_output_attempts'):assert not whole[key]
 assert not scope['additional_scope_issues'] and not whole['self_reads']
 w=scope['windows'][0];assert len(scope['windows'])==1 and w['window_id']=='Yi4Ij2NM7U4:SLOT6:6' and w['job_index']==23 and w['bound_rows']==len(w['bound_fact_rows'])==64 and w['core_tool_count']==126 and w['scientific_media_fact_tool_count']==90
 assert not w['schema_issues'] and not w['proposal_issues'] and w['window_core_sequence_complete'] is True and w['effective_preview_batch_barrier']['two_distinct_forward_four_image_batches_then_proposal'] is True
 assert len(scope['text_fragment_proofs'])==19 and all(p['complete'] is True for p in scope['text_fragment_proofs']) and len(scope['immutable_actual_outputs'])==36

def windows_handle_identity(path):
 """Read-only Windows volume/file-index identity from an actual open handle."""
 assert os.name=='nt'
 class Info(ctypes.Structure):
  _fields_=[('attributes',wintypes.DWORD),('creation',wintypes.FILETIME),('access',wintypes.FILETIME),('write',wintypes.FILETIME),('volume',wintypes.DWORD),('size_high',wintypes.DWORD),('size_low',wintypes.DWORD),('links',wintypes.DWORD),('index_high',wintypes.DWORD),('index_low',wintypes.DWORD)]
 kernel=ctypes.WinDLL('kernel32',use_last_error=True)
 kernel.CreateFileW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,wintypes.LPVOID,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE];kernel.CreateFileW.restype=wintypes.HANDLE
 kernel.GetFileInformationByHandle.argtypes=[wintypes.HANDLE,ctypes.POINTER(Info)];kernel.GetFileInformationByHandle.restype=wintypes.BOOL
 kernel.CloseHandle.argtypes=[wintypes.HANDLE];kernel.CloseHandle.restype=wintypes.BOOL
 handle=kernel.CreateFileW(str(path),0,7,None,3,0,None)
 assert handle!=ctypes.c_void_p(-1).value
 try:
  info=Info();assert kernel.GetFileInformationByHandle(handle,ctypes.byref(info))
  assert not info.attributes & 0x400
  return dict(volume_serial=int(info.volume),file_index=(int(info.index_high)<<32)|int(info.index_low),bytes=(int(info.size_high)<<32)|int(info.size_low))
 finally:assert kernel.CloseHandle(handle)

def validated(gate_path):
 gate_path=Path(gate_path).resolve();assert gate_path==GATE
 gate=read(gate_path);assert gate['status']==GATE_STATUS and gate['CLI']==40 and gate['job_index']==23 and gate['window_id']=='Yi4Ij2NM7U4:SLOT6:6' and gate['automatic_retry'] is False and gate['no_new_model'] is True and gate['old_REJECTED_preserved'] is True
 assert gate['helpers']=={str(R/n):sha(R/n) for n in HELPERS} and gate['bindings']==required_bindings()
 negative=gate['negative_receipt_binding'];assert sha(negative['path'])==negative['sha256'];negative_doc=read(negative['path']);assert negative_doc['status']=='PASS_NECESSARY_EXACT_EIGHT_SEPARATOR_GUARD_CPU_NO_ACTUAL_RECOVERY' and negative_doc['helpers']==gate['helpers'] and negative_doc['new_model_calls']==0
 root=gate['root_samefile_identity_binding'];assert Path(root['path']).resolve()==R/'root_actual_CLI40_separator_identity_v1.json' and sha(root['path'])==root['sha256']=='1772717c43c1dc926177944cc2cb36b4e03b24b3bf7e8780b88ca55b79fd9a60'
 root_identity=read(root['path']);assert root_identity['status']=='PASS_ROOT_ACTUAL_WINDOWS_SAMEFILE_AND_FROZEN_SHA_EIGHT_SEPARATOR_ONLY_NOT_SCOPE_ADMISSION'
 independent=gate['independent_recovery_review_binding'];assert Path(independent['path']).resolve()==R/'plan_review/CLI40_effective_separator_independent_recovery_v1.json' and sha(independent['path'])==independent['sha256']=='c3eef4b766a50857093d34fa37a54d4db5d1f2636ff928118180db82d3304e01'
 base=load_base();fr=read(C/'freeze.json');idx=read(C/'index.json');w=idx['windows'][0];scope=read(C/'w23_completed_scope_audit.json');whole=read(C/'audit.json');terminal=read(C/'terminal.json');cost=read(C/'actual_terminal_cost.json');raw=(C/'stream.jsonl').read_bytes();prefix=Path(scope['immutable_prefix']['path']).read_bytes()
 assert sha(C/'stream.jsonl')==terminal['stream_sha256']==cost['raw_sha256'] and cost['terminal_sha256']==sha(C/'terminal.json') and cost['wall_seconds']==terminal['wall_seconds'] and cost['actual_result_status']=='SUCCESS' and cost['whole_status']==whole['status'] and cost['new_fee_ledger_entry'] is False
 assert raw.startswith(prefix) and hashlib.sha256(prefix).hexdigest()==scope['immutable_prefix']['sha256']==scope['actual_stream_SHA'] and len(prefix)==scope['immutable_prefix']['bytes']
 rows=list(map(json.loads,prefix.splitlines()));projected,changes=project_rows(rows,w['student_previews']);document_guard(terminal,whole,scope,changes)
 for path,digest in fr['inputs'].items():assert sha(path)==digest
 assert idx['scope_core_counts']==[128] and idx['core_per_window']==126 and fr['fixed_job_indices']==[23] and fr['CLI_after']==40
 for x in scope['immutable_actual_outputs']:assert sha(x['original_path'])==x['sha256']==x['sealed_copy_sha256']==sha(x['sealed_copy_path'])
 images=[]
 assert len(root_identity['checks'])==8
 for step,f,prior in zip(STEPS,w['student_previews'],root_identity['checks']):
  updates=[r['step_update'] for r in rows if r.get('step_update',{}).get('step_index')==step and r['step_update'].get('step_type')=='tool'];assert [t['state'] for t in updates]==['ACTIVE','DONE']
  actual=updates[0]['tool_info']['parameters']['AbsolutePath'];expected=f['path'];exact_separator(actual,expected)
  assert prior['step']==step and prior['actual_path']==actual and prior['expected_literal']==expected and prior['actual_windows_samefile'] is True and prior['actual_DONE_tool_record']==updates[1] and prior['tool_image_output_metadata']=='ABSENT_NOT_INFERRED'
  assert 'output' not in updates[1]['tool_info'] and Path(actual).resolve(strict=True)==Path(expected).resolve(strict=True) and os.path.samefile(actual,expected)
  actual_id=windows_handle_identity(actual);canonical_id=windows_handle_identity(expected);assert actual_id==canonical_id
  assert actual_id['file_index']==prior['actual_file_identity']['inode'] and actual_id['bytes']==prior['actual_file_identity']['bytes']
  assert sha(actual)==sha(expected)==sha(f['original_path'])==f['png_sha256']==prior['png_sha256']
  assert fr['inputs'][expected]==f['png_sha256']
  images.append(dict(step=step,actual_path=actual,expected_literal=expected,original_path=f['original_path'],same_windows_handle_identity=actual_id,Path_resolve_equal=True,png_sha256=f['png_sha256'],actual_DONE_tool_record=updates[1],DONE_image_output_metadata='ABSENT_NOT_INFERRED',existing_frozen_geometry=f['geometry'],existing_RGB_proof=f['rgb_pixel_sha256']))
 with base.current_engine() as (common,engine):
  actual=engine.inspect(C,prefix,23)
  for key in ('actual_supply','text_fragment_proofs','scientific_core_expected','windows','tool_issues'):assert json.loads(json.dumps(actual[key],ensure_ascii=False))==scope[key]
  projected_bytes=b''.join((json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n').encode() for r in projected)
  exact=engine.inspect(C,projected_bytes,23)
  for key in ('tool_issues','all_raw_tool_state_issues','errored_tool_attempts','unfinished_tool_attempts','reported_nonmedia_errors'):assert not exact[key]
  assert exact['bootstrap_successful_complete'] and exact['bootstrap_ack_complete'] and exact['teacher_task_completed'] and exact['actual_core_tool_calls']==128
  tools=base.raw_tools(rows,fr);core,textproof,selfchecks=base.verify_core_and_text(rows,tools,idx,[w],common);assert len(core)==128 and len(textproof)==19
  ar=scope['windows'][0]
  for i,(row,identity) in enumerate(zip(ar['bound_fact_rows'],w['native_identity_all64'])):
   g=w['groups'][i//4];assert row['identity']==identity and row['identity_generated_by_program'] is True and row['group']==i//4 and row['slot']==i%4 and row['facts']==common.fact_items(read(g['output_path']),i//4)[i%4] and row['tool_provenance']['four_image_barrier']['all_four_DONE_before_fact_planning_response'] is True
  common.proposal_schema(w['proposal_path'],w)
 pixel=base.verify_prior_pixel_clock_binding(C,w,scope,fr)
 for r in base.parsed(raw[len(prefix):]):assert r.get('step_update',{}).get('step_type')!='tool'
 results=[r['result'] for r in base.parsed(raw) if r.get('event')=='result'];assert len(results)==1 and results[0]['status']=='SUCCESS'
 ledger=[json.loads(line) for line in (V.parent/'global_CLI_ledger.jsonl').read_text(encoding='utf-8').splitlines()];assert max(r['global_count'] for r in ledger)==40
 registered=[r for r in ledger if r['global_count']==40 and r['event']=='REGISTERED'];terms=[r for r in ledger if r['global_count']==40 and r['event']=='TERMINAL'];assert len(registered)==len(terms)==1 and registered[0]['request_sha256']==sha(C/'request.json') and terms[0]['terminal_sha256']==sha(C/'terminal.json') and terms[0]['raw_sha256']==sha(C/'stream.jsonl')
 base.verify_actual_previous39(read(V/'root_start_admission_CLI40.json'))
 # Race check immediately before a new receipt; do not overwrite any old bytes.
 assert gate['bindings']==required_bindings()
 for x in scope['immutable_actual_outputs']:assert sha(x['original_path'])==x['sha256']==sha(x['sealed_copy_path'])
 return dict(status=STATUS,utc=datetime.now(timezone.utc).isoformat(),CLI=40,window_id=w['window_id'],root_recovery_gate=bind(gate_path),helpers=gate['helpers'],bindings=gate['bindings'],original_strict_scope_status=scope['status'],original_strict_whole_status=whole['status'],old_REJECTED_preserved=True,original_scope_rejection_issues=scope['tool_issues'],exact_sixteen_raw_parameter_differences=changes,effective_file_identity_proofs=images,root_actual_samefile_evidence=root,independent_recovery_review_binding=independent,original_immutable_prefix=scope['immutable_prefix'],original_immutable_outputs=scope['immutable_actual_outputs'],original_actual_supply=scope['actual_supply'],original_bound_fact_rows=scope['windows'][0]['bound_fact_rows'],full_text_delivery_proofs=textproof,exact_original_core_count=len(core),unchanged_engine_projection_proof=dict(engine=bind(V/'engine.py'),in_memory_only=True,only_parameter_differences=16,projected_bytes_sha256=hashlib.sha256(projected_bytes).hexdigest(),strict_structure_after_exact_identity_substitution=True,not_original_raw_or_whole_PASS=True),existing_pixel_clock_success_binding=pixel,natural_terminal=bind(C/'terminal.json'),actual_cost=bind(C/'actual_terminal_cost.json'),training_admitted=False,semantic_admission_pending=True,new_model_calls=0,new_decoder_calls=0,new_processor_calls=0)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--gate',default=str(GATE));p.add_argument('--output',default=str(RECEIPT));a=p.parse_args();output=Path(a.output).resolve();assert output==RECEIPT and not output.exists()
 result=validated(a.gate)
 with output.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False)
 print(json.dumps(bind(output),ensure_ascii=False))
if __name__=='__main__':main()
