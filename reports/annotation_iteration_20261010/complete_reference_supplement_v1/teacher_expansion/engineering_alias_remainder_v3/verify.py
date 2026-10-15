"""No-model independent prepared aliases, routing, literal and negative checks."""
from common import ROOT,BASE,read,sha,key,save,expected_core,fact_items
from prompt import build
from datetime import datetime,timezone
from pathlib import Path
import ast,json,struct,hashlib
def main():
 assert not(ROOT/'root_start_admission.json').exists() and not(ROOT/'registered.json').exists()
 binding=read(ROOT/'execution_code_binding.json')
 for p,s in {**binding['sources'],**binding['prior_failure_and_transfer_inputs']}.items():assert sha(p)==s
 aliases=read(ROOT/'alias_original_payload_binding.json');assert len(aliases['rows'])==479
 for row in aliases['rows']:
  a=Path(row['alias_path']);o=Path(row['original_path']);assert a.read_bytes()==o.read_bytes()
  assert sha(a)==sha(o)==(row.get('png_sha256') or row['payload_sha256'])
  if row['kind']!='clip':assert list(struct.unpack('>II',a.read_bytes()[16:24]))==row['geometry']
 proof=read(ROOT/'prior17/actual_prior32_native_facts_provenance.json');package=read(ROOT/'prior17/prior32_facts.json');raw_package=(ROOT/'prior17/prior32_facts.json').read_bytes()
 assert proof['actual_native32_DONE']==32 and proof['actual_fact_groups8_DONE']==8 and proof['old_F35_actual_DONE_steps']==[193]
 assert proof['original_CLI33_strict_failed_preserved'] and proof['old_group8_not_successful']
 for g in proof['groups']:
  p=Path(g['facts']['path']);assert sha(p)==g['facts']['sha256'] and raw_package.count(p.read_bytes())==1
  assert package['groups'][g['group']]==read(p);fact_items(read(p),g['group'])
  for f in g['native_reads']:assert sha(f['identity']['path'])==f['identity']['png_sha256'] and len(f['DONE_tool_steps'])==1
 calls=[]
 for n,jobs in [(34,[17,18]),(35,[19,20]),(36,[21,22,23])]:
  a=ROOT/f'call{n}';idx=read(a/'index.json');fr=read(a/'freeze.json');literal=read(a/'literal_execution_parameters.json')
  assert [w['job_index'] for w in idx['windows']]==jobs==fr['fixed_job_indices']
  assert fr['CLI_before']==n-1 and fr['CLI_after']==n<=36 and fr['timeout_seconds']==7200
  assert not(a/'request.json').exists() and all(not Path(p).exists() for p in fr['write_whitelist'])
  for p,s in fr['inputs'].items():assert sha(p)==s,(p,'FROZEN_INPUT_DRIFT')
  assert build(idx,fr)==((a/'frozen_prompt.txt').read_text(encoding='utf-8'),literal)
  assert len(expected_core(idx))=={34:141,35:181,36:271}[n]
  scope_counts={}
  for w,l in zip(idx['windows'],literal):
   assert len(w['native_identity_all64'])==64 and w['actual_student_frames']==64 and len(w['student_previews'])==8
   assert [f['frame_id'] for f in w['native_identity_all64']]==[f'F{i:02d}' for i in range(64)]
   assert [g['group'] for g in w['groups']]==list(range(8 if w['job_index']==17 else 0,16))
   assert [x['AbsolutePath'] for batch in l['effective_preview_batches'] for x in batch]==[f['path'] for f in w['student_previews']]
   assert [x['AbsolutePath'] for g in l['native_groups'] for x in g['view_file']]==[f['path'] for g in w['groups'] for f in g['frames']]
   native=[f['path'] for g in w['groups'] for f in g['frames']]
   assert all(Path(p).name.startswith('F') and '_O' not in Path(p).name for p in native)
   identity={f['frame_id']:f for f in w['native_identity_all64']}
   for f in [f for g in w['groups'] for f in g['frames']]:
    original=identity[f['frame_id']]
    assert all(f[k]==original[k] for k in ('source_ordinal','global_seconds_exact','local_seconds_exact','geometry','png_sha256','rgb_pixel_sha256'))
    assert f['original_path']==original['original_path']
   if w['job_index']==17:
    assert [Path(p).name for p in native]==[f'F{i:02d}.png' for i in range(32,64)]
    assert w['prior_context_path'] in fr['read_whitelist'] and all(f['original_path'] not in fr['read_whitelist'] for f in w['native_identity_all64'])
   scope_counts[w['job_index']]=len(expected_core(idx,w['job_index']))
  assert scope_counts==({17:51,18:141} if n==34 else {19:91,20:181} if n==35 else {21:91,22:181,23:271})
  calls.append(dict(CLI=n,jobs=jobs,core_tool_calls=len(expected_core(idx)),context_steps=fr['context_read_count'],scope_prefix_core_counts=scope_counts,input_count=len(fr['inputs']),freeze_sha256=sha(a/'freeze.json'),index_sha256=sha(a/'index.json'),prompt_sha256=sha(a/'frozen_prompt.txt'),literal_sha256=sha(a/'literal_execution_parameters.json'),all_inputs_SHA_verified=True))
 AST=[]
 for p in ROOT.glob('*.py'):ast.parse(p.read_text(encoding='utf-8-sig'));AST.append(dict(path=str(p),sha256=sha(p)))
 assert len(AST)==9
 # Synthetic negative test is in memory only; no fake observation/raw/facts/proposal saved.
 from audit import inspect
 a=ROOT/'call35';w=read(a/'index.json')['windows'][0];f=w['groups'][0]['frames'][0]
 synthetic=json.dumps(dict(event='step_update',step_update=dict(step_index=1,state='ERROR',step_type='tool',tool_name='view_file',tool_info=dict(parameters=dict(AbsolutePath=f['path']))))).encode('utf-8')
 rejected=inspect(a,synthetic)
 assert len(rejected['errored_tool_attempts'])==1 and not rejected['teacher_task_completed'] and all(not r['status'].startswith('PASS_') for r in rejected['windows'])
 assert not any((ROOT/f'call{n}/request.json').exists() for n in (34,35,36))
 prior=BASE/'remaining_CLI33_36_same_index_selfcheck_v2/call07';assert sha(prior/'stream.jsonl')=='c40bf772414233d23abce940a44d53a00efa339063edec464c7321bc602907ba' and sha(prior/'audit.json')=='e644195a494e654e88f7ceffb5999fcb0e58d5b4a4ac9f3ce8803e3c7cb48977'
 assert max(json.loads(s)['global_count'] for s in(BASE/'global_CLI_ledger.jsonl').read_text(encoding='utf-8').splitlines() if s.strip())==33
 out=dict(utc=datetime.now(timezone.utc).isoformat(),status='PASS_INDEPENDENT_ALIAS_AND_LITERAL_CLOCK_TRANSFER_PREPARATION_NO_MODEL',verifier_source_sha256=sha(__file__),AST=AST,calls=calls,alias_binding_sha256=sha(ROOT/'alias_original_payload_binding.json'),execution_binding_sha256=sha(ROOT/'execution_code_binding.json'),dry_run_sha256=sha(ROOT/'dry_run_acceptance.json'),all479_alias_payloads_byte_exact=True,native64_identity_per_window_preserved=True,old32_facts_JSON_raw_bytes_exact=True,F35_old_DONE193_without_fact_explicit=True,all_scope_prefix_dynamic_counts_verified=True,in_memory_media_ERROR_negative_test_rejects=True,synthetic_test_is_not_actual_observation_evidence=True,original33_raw_audit_unchanged=True,global_CLI=33,global_cap=36,root_start_gate_absent=True,new_model_calls=0,new_video_decode=0,new_optimizer=0,cash_cost='UNKNOWN_NOT_ZERO')
 save(ROOT/'independent_preparation_acceptance.json',out)
 print(json.dumps(dict(receipt_sha256=sha(ROOT/'independent_preparation_acceptance.json'),protocol_sha256=sha(ROOT/'PROTOCOL.md'),AST_count=len(AST),calls=calls,new_model_calls=0),ensure_ascii=False))
if __name__=='__main__':main()
