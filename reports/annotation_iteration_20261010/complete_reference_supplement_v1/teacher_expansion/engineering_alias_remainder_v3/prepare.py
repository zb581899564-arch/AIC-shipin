"""Prepare only: byte-identical aliases, immutable old32 context, three freezes."""
from common import ROOT,BASE,read,sha,key,save,fact_items,expected_core
from prompt import build
from pathlib import Path
from datetime import datetime,timezone
import copy,json,hashlib,struct,ast
OLD=BASE/'capacity_v4_tool_batches';PRIOR=BASE/'remaining_CLI33_36_same_index_selfcheck_v2';P=PRIOR/'call07'
def write_bytes(p,b):
 Path(p).parent.mkdir(parents=True,exist_ok=True)
 with Path(p).open('xb') as f:f.write(b)
def ref(p):return dict(path=str(p),sha256=sha(p))
def frame_identity(f):return {k:f[k] for k in ('slot','frame_id','source_ordinal','global_seconds_exact','local_seconds_exact','png_sha256','rgb_pixel_sha256','geometry') if k in f}
def main():
 assert not(ROOT/'plan.json').exists() and not(ROOT/'root_start_admission.json').exists()
 assert(P/'terminal.json').exists() and read(P/'terminal.json')['CLI_after']==33 and(PRIOR/'stopped.json').exists()
 for p,s in read(P/'freeze.json')['inputs'].items():assert sha(p)==s,(p,'CLI33_INPUT_SHA_DRIFT')
 assert read(P/'request.json')['freeze_sha256']==sha(P/'freeze.json')
 ledger=BASE/'global_CLI_ledger.jsonl';assert max(json.loads(s)['global_count'] for s in ledger.read_text(encoding='utf-8').splitlines() if s.strip())==33
 write_bytes(ROOT/'global_CLI33_ledger_prefix.jsonl',ledger.read_bytes())
 windows={};origins={};old_inputs={}
 for n in (7,8,9,10):
  a=OLD/f'call{n:02d}';idx=read(a/'index.json');fr=read(a/'freeze.json')
  for p,s in fr['inputs'].items():assert sha(p)==s,(p,'ORIGINAL_INPUT_SHA_DRIFT')
  old_inputs.update(fr['inputs']);old_inputs[str(a/'index.json')]=sha(a/'index.json');old_inputs[str(a/'freeze.json')]=sha(a/'freeze.json')
  write_bytes(ROOT/'original_indices'/f'call{n:02d}.json',(a/'index.json').read_bytes())
  for w in idx['windows']:
   if w['job_index']>=17:windows[w['job_index']]=w;origins[w['job_index']]=a
 assert sorted(windows)==list(range(17,24))
 w17=windows[17];raw=(P/'stream.jsonl').read_bytes();assert hashlib.sha256(raw).hexdigest()==read(P/'terminal.json')['stream_sha256']
 full_old_rows=[json.loads(line) for line in raw.splitlines() if line.strip()]
 prior_f35=w17['groups'][8]['frames'][3]
 f35_steps=[r['step_update']['step_index'] for r in full_old_rows if r.get('step_update',{}).get('state')=='DONE' and r['step_update'].get('tool_name')=='view_file' and key(r['step_update'].get('tool_info',{}).get('parameters',{}).get('AbsolutePath',''))==key(prior_f35['path'])]
 assert len(f35_steps)==1 and not Path(w17['groups'][8]['output_path']).exists()
 cutoff=None;position=0;old_rows=[]
 target=key(w17['groups'][7]['output_path'])
 for line in raw.splitlines(keepends=True):
  position+=len(line);r=json.loads(line);old_rows.append(r);t=r.get('step_update',{});params=t.get('tool_info',{}).get('parameters',{})
  if t.get('state')=='DONE' and t.get('tool_name')=='write_to_file' and key(params.get('TargetFile',''))==target:cutoff=position;break
 assert cutoff is not None
 prefix=ROOT/'prior17/CLI33_prior32_actual_stream_prefix.jsonl';write_bytes(prefix,raw[:cutoff])
 old_tools=[r['step_update'] for r in old_rows if r.get('step_update',{}).get('state')=='DONE' and r['step_update'].get('step_type')=='tool']
 def oldsteps(name,p):return [t['step_index'] for t in old_tools if t.get('tool_name')==name and key(t.get('tool_info',{}).get('parameters',{}).get('AbsolutePath') or t.get('tool_info',{}).get('parameters',{}).get('TargetFile'))==key(p)]
 prior_expected=[];package_raw=[];proof_groups=[]
 for g in w17['groups'][:8]:
  file=Path(g['output_path']);b=file.read_bytes();assert not b.startswith(b'\xef\xbb\xbf');doc=read(file);fact_items(doc,g['group']);package_raw.append(b)
  reads=[]
  for f in g['frames']:
   assert sha(f['path'])==f['png_sha256'];s=oldsteps('view_file',f['path']);assert len(s)==1
   prior_expected.append(('view_file',key(f['path'])));reads.append(dict(identity=f,DONE_tool_steps=s))
  s=oldsteps('write_to_file',file);assert len(s)==1;prior_expected.append(('write_to_file',key(file)))
  proof_groups.append(dict(group=g['group'],native_reads=reads,facts=ref(file),fact_write_DONE_steps=s,raw_fact_bytes=len(b),fact_byte_exact_in_context=True))
 pathset={p for _,p in prior_expected};actual=[]
 for t in old_tools:
  p=t.get('tool_info',{}).get('parameters',{});path=key(p.get('AbsolutePath') or p.get('TargetFile'))
  if path in pathset:actual.append((t.get('tool_name'),path))
 assert actual==prior_expected and len(actual)==40
 package=ROOT/'prior17/prior32_facts.json'
 write_bytes(package,b'{"job_index":17,"window_id":'+json.dumps(w17['window_id'],ensure_ascii=False).encode('utf-8')+b',"groups":[\n'+b',\n'.join(package_raw)+b'\n]}\n')
 parsed=read(package);assert parsed['groups']==[read(g['output_path']) for g in w17['groups'][:8]]
 for b in package_raw:assert package.read_bytes().count(b)==1
 proof=ROOT/'prior17/actual_prior32_native_facts_provenance.json'
 save(proof,dict(utc=datetime.now(timezone.utc).isoformat(),status='ACTUAL_OLD32_TOOL_AND_FACT_BYTE_TRANSFER_ONLY_NOT_SEMANTIC_ADMISSION',job_index=17,window_id=w17['window_id'],original_index=ref(origins[17]/'index.json'),original_CLI33_freeze=ref(P/'freeze.json'),original_CLI33_raw=ref(P/'stream.jsonl'),original_CLI33_terminal=ref(P/'terminal.json'),original_CLI33_failed_audit=ref(P/'audit.json'),original_CLI33_engineering_failure=ref(P/'engineering_wrong_native_ordinal_paths_CLI33.json'),immutable_prior32_prefix=ref(prefix),prior32_context_package=ref(package),groups=proof_groups,actual_prior_group_sequence_complete=True,actual_native32_DONE=32,actual_fact_groups8_DONE=8,original_CLI33_strict_failed_preserved=True,old_group8_not_successful=True,old_F35_was_DONE_without_group8_fact=True,old_F35_actual_DONE_steps=f35_steps,old_F35_identity=prior_f35,new_F35_reprovide_reason='Old tool DONE for F35 had no group8 fact; new session must supply all four group8 images to write its first actual facts; other first32 successful images not resupplied',old_first32_not_reread=True,semantic_correctness='UNVERIFIED_ROOT_DECIDES',training_admitted=False))
 alias_rows=[];prepared_windows={};payload_bytes=0
 for job,w in windows.items():
  ww=copy.deepcopy(w);ww['native_identity_all64']=[frame_identity(f)|dict(original_path=f['path']) for g in w['groups'] for f in g['frames']]
  assert len(ww['native_identity_all64'])==64
  start=8 if job==17 else 0;ww['groups']=copy.deepcopy(w['groups'][start:])
  ww['sealed_prior_groups']=list(range(8)) if job==17 else []
  if job==17:ww['prior_context_path']=str(package);ww['prior_facts_provenance_path']=str(proof)
  manifest_path=Path(w['clip_path']).parent/'manifest.json';manifest=read(manifest_path);assert sha(manifest_path)==w['manifest_sha256']
  clocks=Path(manifest['native_clock_path']);assert sha(clocks)==manifest['native_clock_sha256']
  old_inputs[str(manifest_path)]=sha(manifest_path);old_inputs[str(clocks)]=sha(clocks)
  ww['original_source_manifest']=dict(**ref(manifest_path),source_path=manifest['source_path'],source_sha256=manifest['source_sha256'],domain_global_seconds_exact=manifest['domain_global_seconds_exact'],native_clock=ref(clocks),clip_pts_offset_exact=manifest['clip_pts_offset_exact'])
  receipt_path=Path(w['clip_path']).parent/'student_views/receipt.json';assert sha(receipt_path)==w['student_receipt_sha256']
  old_inputs[str(receipt_path)]=sha(receipt_path);ww['original_student_receipt']=ref(receipt_path)
  for kind,frames in [('native',[f for g in ww['groups'] for f in g['frames']]),('effective',ww['student_previews'])]:
   for f in frames:
    original=Path(f['path']);alias=ROOT/'aliases'/f'w{job:02d}'/kind/f"{f['frame_id']}.png";b=original.read_bytes();assert hashlib.sha256(b).hexdigest()==f['png_sha256']
    assert b[:8]==b'\x89PNG\r\n\x1a\n' and list(struct.unpack('>II',b[16:24]))==f['geometry']
    write_bytes(alias,b);assert alias.read_bytes()==b;payload_bytes+=len(b)
    row=dict(job_index=job,kind=kind,alias_path=str(alias),original_path=str(original),**frame_identity(f),payload_bytes=len(b),byte_exact=True,RGB_hash_inherited_by_identical_PNG_not_redecoded=True,prior_F35_DONE_without_facts_reprovided=(job==17 and kind=='native' and f['frame_id']=='F35'))
    alias_rows.append(row);f['original_path']=str(original);f['path']=str(alias)
  clip=ROOT/'aliases'/f'w{job:02d}'/'clip.mp4';clip_bytes=Path(w['clip_path']).read_bytes();assert hashlib.sha256(clip_bytes).hexdigest()==manifest['clip_sha256'];write_bytes(clip,clip_bytes);payload_bytes+=len(clip_bytes)
  alias_rows.append(dict(job_index=job,kind='clip',alias_path=str(clip),original_path=w['clip_path'],payload_sha256=manifest['clip_sha256'],payload_bytes=len(clip_bytes),byte_exact=True,clip_pts_offset_exact=manifest['clip_pts_offset_exact'],native_clock=ref(clocks)))
  ww['original_clip_path']=w['clip_path'];ww['clip_path']=str(clip);prepared_windows[job]=ww
 mapping=ROOT/'alias_original_payload_binding.json';save(mapping,dict(utc=datetime.now(timezone.utc).isoformat(),status='EXACT_ORIGINAL_PAYLOAD_ALIASES_NO_NEW_FRAMES',rows=alias_rows,original_indices={str(p):sha(p) for p in (ROOT/'original_indices').glob('*.json')},total_alias_payload_bytes=payload_bytes,native_aliases=416,effective_aliases=56,clip_aliases=7,RGB_identity_inherited_exact_payload_no_RGB_recompute=True,new_video_decode=0,new_model_calls=0))
 prior_files=[P/n for n in ('freeze.json','terminal.json','stream.jsonl','audit.json','actual_partial_terminal_receipt.json','engineering_wrong_native_ordinal_paths_CLI33.json','w16_completed_scope_audit.json')]+[PRIOR/'PROTOCOL.md',PRIOR/'stopped.json',PRIOR/'full_denominator24_after_CLI33.json',ROOT/'global_CLI33_ledger_prefix.jsonl',prefix,package,proof,mapping]
 prior_files+=[Path(g['output_path']) for g in w17['groups'][:8]]
 runtime={str(p):sha(p) for p in ROOT.glob('*.py')};runtime[str(ROOT/'PROTOCOL.md')]=sha(ROOT/'PROTOCOL.md')
 execution=ROOT/'execution_code_binding.json';save(execution,dict(utc=datetime.now(timezone.utc).isoformat(),sources=runtime,prior_failure_and_transfer_inputs={str(p):sha(p) for p in prior_files},all_prior_STOP_and_costs_preserved=True,new_model_calls=0,requires_root_start_admission=True))
 runtime[str(execution)]=sha(execution)
 routing={34:[17,18],35:[19,20],36:[21,22,23]};calls=[]
 for n,jobs in routing.items():
  a=ROOT/f'call{n}';a.mkdir();idx=dict(index_path=str(a/'index.json'),windows=[copy.deepcopy(prepared_windows[j]) for j in jobs],model_identity_forbidden=True,original_science_unchanged=True)
  for w in idx['windows']:
   for g in w['groups']:g['output_path']=str(a/f"w{w['job_index']:02d}_group{g['group']:02d}.json")
   w['proposal_path']=str(a/f"w{w['job_index']:02d}_proposal.json")
  save(a/'index.json',idx);reads=[str(a/'index.json')];writes=[];inputs=dict(old_inputs);inputs.update(runtime)
  inputs.update({str(p):sha(p) for p in prior_files});inputs[str(a/'index.json')]=sha(a/'index.json')
  for w in idx['windows']:
   if w.get('prior_context_path'):reads.append(w['prior_context_path'])
   for g in w['groups']:
    reads.extend(f['path'] for f in g['frames']);writes.append(g['output_path'])
   reads.append(w['clip_path']);reads.extend(f['path'] for f in w['student_previews']);writes.append(w['proposal_path'])
  for p in reads:inputs[p]=sha(p)
  fr=dict(utc=datetime.now(timezone.utc).isoformat(),inputs=inputs,read_whitelist=reads,self_read_whitelist=writes,write_whitelist=writes,protocol_sha256=sha(ROOT/'PROTOCOL.md'),parent_protocol_sha256=sha(BASE/'PROTOCOL.md'),CLI_before=n-1,CLI_after=n,global_cap=36,timeout_seconds=7200,automatic_retry=False,fixed_job_indices=jobs,expected_core_tool_calls=len(expected_core(idx)),context_read_count=1 if n==34 else 0,execution_binding_sha256=sha(execution),alias_binding_sha256=sha(mapping),old33_not_reclassified=True)
  text,literal=build(idx,fr);write_bytes(a/'frozen_prompt.txt',text.encode('utf-8'));save(a/'literal_execution_parameters.json',literal);inputs[str(a/'frozen_prompt.txt')]=sha(a/'frozen_prompt.txt');inputs[str(a/'literal_execution_parameters.json')]=sha(a/'literal_execution_parameters.json');fr['frozen_prompt_sha256']=sha(a/'frozen_prompt.txt');save(a/'freeze.json',fr)
  assert build(idx,fr)==(text,literal) and fr['expected_core_tool_calls']=={34:141,35:181,36:271}[n]
  calls.append(dict(CLI=n,jobs=jobs,core_tool_calls=fr['expected_core_tool_calls'],context_reads=fr['context_read_count'],index_sha256=sha(a/'index.json'),freeze_sha256=sha(a/'freeze.json'),prompt_sha256=sha(a/'frozen_prompt.txt'),literal_parameter_sha256=sha(a/'literal_execution_parameters.json'),input_count=len(inputs)))
 AST=[]
 for p in ROOT.glob('*.py'):ast.parse(p.read_text(encoding='utf-8-sig'));AST.append(ref(p))
 save(ROOT/'plan.json',dict(utc=datetime.now(timezone.utc).isoformat(),status='PREPARED_FIXED_ALIAS_REMAINDER_PENDING_ROOT_START',routing=routing,calls=calls,fixed_denominator=24,teacher_expansion_denominator=21,global_actual_CLI=33,global_cap=36,timeout_seconds=7200,model='gemini-3.8-flash-high',alias_binding_sha256=sha(mapping),prior32_context_sha256=sha(package),prior32_provenance_sha256=sha(proof),execution_binding_sha256=sha(execution),new_model_calls=0,new_video_decode=0,new_optimizer=0))
 save(ROOT/'dry_run_acceptance.json',dict(utc=datetime.now(timezone.utc).isoformat(),status='PASS_PREPARED_AST_ALIAS_BYTES_CLOCK_PRIOR_FACTS_NO_MODEL_PENDING_ROOT_REVIEW',AST=AST,calls=calls,alias_payloads=len(alias_rows),total_alias_payload_bytes=payload_bytes,prior32_actual_native_and_fact_sequence_verified=True,prior32_group_JSON_bytes_preserved_in_single_context_package=True,F35_prior_DONE_without_fact_explicit_reprovide=True,native_identity_rows_required=448,new_native_alias_arguments=416,effective_alias_arguments=56,original_source_domain_clock_floor64_unchanged=True,RGB_inherited_exact_PNG_byte_identity=True,new_RGB_recompute=0,new_video_decode=0,new_model_calls=0,new_optimizer=0,execution_binding_sha256=sha(execution),requires_root_start_admission=True,global_CLI=33,global_cap=36,root_start_gate_absent=True,cash_cost='UNKNOWN_NOT_ZERO'))
 print(json.dumps(dict(root=str(ROOT),source_sha256=sha(__file__),execution_binding_sha256=sha(execution),dry_run_sha256=sha(ROOT/'dry_run_acceptance.json'),alias_binding_sha256=sha(mapping),prior32_provenance_sha256=sha(proof),calls=calls,new_model_calls=0),ensure_ascii=False))
if __name__=='__main__':main()
