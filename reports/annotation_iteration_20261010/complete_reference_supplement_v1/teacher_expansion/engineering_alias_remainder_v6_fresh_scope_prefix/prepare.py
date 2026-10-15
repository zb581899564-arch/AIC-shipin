"""One preparation invocation only, no child/API/model calls."""
from common import ROOT,BASE,read,sha,save,key,expected_core
from pathlib import Path
import ast,copy,json,subprocess,uuid,hashlib
OLD=BASE/'engineering_alias_remainder_v4_bootstrap_file'
V3=BASE/'engineering_alias_remainder_v3'
V5=BASE/'engineering_alias_remainder_v5_line_representation_controller'

def put(p,b):
 with Path(p).open('xb') as f:f.write(b)

def prerequisites():
 root=BASE.parent;rec=root/'teacher34_terminal_reconciliation_v1.json'
 assert sha(rec)=='4422fab887a72627d2acd223d8a1e6b0864f860e40b0b72fa806ced8ac3b75cb'
 d=read(rec);assert d['whole_call_never_reclassified_as_PASS'] and d['unused_model_calls_35_36_not_started']
 assert d['actual_result_status']=='ERROR' and [r['step'] for r in d['outside_reads']]==[214,216]
 prior=[rec,root/'bootstrap_line_representation_erratum_v1.json',root/'root_teacher_line_v5_preparation_review.json',root/'accept_teacher_bootstrap_scope_v5_representation.py']
 for field in ('terminal','raw','whole_original_audit','whole_v5_rejection'):
  p=Path(d[field]['path']);assert sha(p)==d[field]['sha256'];prior.append(p)
 terminal=read(d['terminal']['path']);assert terminal['child_process_created'] and terminal['stream_sha256']==d['raw']['sha256'] and terminal['wall_seconds']==d['actual_wall_seconds']
 cost=V5/'call34/actual_terminal_cost.json';prior.append(cost);assert sha(cost)=='64abc19ff41855a571f2d1b0836fd2102f86fc7b6c7b000db245b97f621d1cc5'
 assert not read(d['whole_v5_rejection']['path'])['status'].startswith('PASS')
 raw=Path(d['raw']['path']).read_bytes()
 for z in d['prefixes']:
  assert z['job_index'] in (17,18) and z['before_actual_outside_steps'] and z['no_later_rewrite_of_facts_or_proposal'] and z['current_output_SHAs_equal_sealed_scope']
  for field in ('root_media_receipt','immutable_prefix'):
   p=Path(z[field]['path']);assert sha(p)==z[field]['sha256'];prior.append(p)
  p=z['immutable_prefix'];assert raw[:p['bytes']]==Path(p['path']).read_bytes()
  proof=read(z['root_media_receipt']['path']);assert proof['status'].startswith('PASS_ROOT_INDEPENDENT_BOOTSTRAP_FIXED_SCOPE_MEDIA')
 ledger=BASE/'global_CLI_ledger.jsonl';rows=[json.loads(s) for s in ledger.read_text(encoding='utf-8').splitlines()]
 assert max(r['global_count'] for r in rows)==34
 terms=[r for r in rows if r['global_count']==34 and r['event']=='TERMINAL'];assert len(terms)==1 and terms[0]['terminal_sha256']==d['terminal']['sha256'] and terms[0]['raw_sha256']==d['raw']['sha256']
 forbidden=[]
 for n in (35,36):forbidden.extend(str(p) for p in BASE.glob(f'*/call{n}/request.json'))
 assert not forbidden,('ALREADY_STARTED_UNUSED_CALL',forbidden)
 put(ROOT/'actual_global34_ledger_prefix.jsonl',ledger.read_bytes());prior.append(ROOT/'actual_global34_ledger_prefix.jsonl')
 return prior,d

def main():
 assert not(ROOT/'plan.json').exists() and not(ROOT/'root_start_admission.json').exists()
 prior,rec=prerequisites();sources={str(p):sha(p) for p in list(ROOT.glob('*.py'))+[ROOT/'PROTOCOL.md']}
 assert len(list(ROOT.glob('*.py')))==10
 for directory in (V3,OLD,V5):
  for name in ('execution_code_binding.json','root_start_admission.json','dry_run_acceptance.json','plan.json','PROTOCOL.md'):
   p=directory/name
   if p.exists():prior.append(p)
  prior.extend(directory.glob('*.py'))
 prior.extend([V3/'prespawn_failure_evidence/actual_prespawn_failure.json',V3/'alias_original_payload_binding.json',OLD/'call34/request.json',OLD/'call34/freeze.json',OLD/'call34/actual_terminal_receipt.json',OLD/'stopped.json'])
 prior=[p for p in prior if p.exists()]
 bindings={str(p):sha(p) for p in prior};save(ROOT/'readiness_actual34.json',dict(status='ACTUAL34_REJECTED_ROOT_SCOPE17_18_ACCEPTED_UNUSED35_36_PENDING_ROOT_GATE',actual_bindings=bindings,actual_global=34,unique_actual34terminal=True,unused35_36_request_count=0,actual34_wall_seconds=rec['actual_wall_seconds'],actual34_result_status='ERROR',no_oldwhole_PASS_claim=True,no_model_calls=0,cash_cost='UNKNOWN_NOT_ZERO'))
 binding=ROOT/'execution_code_binding.json';save(binding,dict(sources=sources,actual_prior_bindings=bindings,readiness_sha256=sha(ROOT/'readiness_actual34.json'),no_model_calls=0,whole34_REJECT_preserved=True,requires_root_start_admission=True))
 aliases=read(V3/'alias_original_payload_binding.json');selected=[r for r in aliases['rows'] if r['job_index'] in range(19,24)];assert len(selected)==365
 aliaschecks=[]
 for r in selected:
  a=Path(r['alias_path']);o=Path(r['original_path']);assert a.read_bytes()==o.read_bytes()
  aliaschecks.append(dict(r,actual_payload_sha256=sha(a),actual_original_sha256=sha(o)))
 save(ROOT/'exact_scientific_alias_transfer.json',dict(status='EXACT_ORIGINAL_ALIAS_BYTES_320_NATIVE_40_EFFECTIVE_5_CLIP',rows=aliaschecks,no_new_frame=True,new_video_decode=0))
 calls=[]
 from prompt import build
 from launch import command
 from audit import verify_png_pixels
 for n in (35,36):
  old=OLD/f'call{n}';a=ROOT/f'call{n}';a.mkdir();fr0=read(old/'freeze.json');idx=copy.deepcopy(read(old/'index.json'))
  project=lambda p:p.replace(str(old),str(a))
  idx['index_path']=str(a/'index.json');idx['bootstrap_instruction_path']=str(a/'bootstrap_instruction.txt');idx['bootstrap_ack_path']=str(a/'bootstrap_ack.json');idx['bootstrap_ack_expected_path']=str(a/'bootstrap_ack_expected.json')
  for w in idx['windows']:
   assert len(w['groups'])==16 and len(w['native_identity_all64'])==64 and len(w['student_previews'])==8 and not w.get('prior_context_path')
   for g in w['groups']:g['output_path']=project(g['output_path'])
   w['proposal_path']=project(w['proposal_path'])
  save(a/'index.json',idx)
  lit=copy.deepcopy(read(old/'literal_execution_parameters.json'))
  for w in lit:
   assert not w['sealed_prior_groups'] and not w.get('prior_context_AbsolutePath')
   for g in w['native_groups']:g['write_to_file']['TargetFile']=project(g['write_to_file']['TargetFile'])
   w['proposal_write_to_file']['TargetFile']=project(w['proposal_write_to_file']['TargetFile'])
  save(a/'literal_execution_parameters.json',lit)
  original=(V3/f'call{n}/frozen_prompt.txt').read_bytes();put(a/'original_v3_frozen_prompt.txt',original)
  projected=original.decode('utf-8').replace(str(V3/f'call{n}'),str(a))
  ack=dict(marker='FRESH_V6_END_'+uuid.uuid4().hex,fixed_job_indices=fr0['fixed_job_indices'],native_required_counts={str(w['job_index']):64 for w in idx['windows']},native_alias_bounds_per_window={str(w['job_index']):dict(first=w['groups'][0]['frames'][0]['path'],last=w['groups'][-1]['frames'][-1]['path']) for w in idx['windows']},actual_student64_per_window={str(w['job_index']):64 for w in idx['windows']},effective_preview8_per_window={str(w['job_index']):8 for w in idx['windows']})
  save(a/'bootstrap_ack_expected.json',ack);body=build(projected,idx,lit,ack);payload=body.encode('utf-8');put(a/'bootstrap_instruction.txt',payload)
  assert body.endswith('\n') and '\r' not in body and len(body.splitlines())<=450 and max(map(len,body.splitlines()))<=1000
  short=f"First view_file the ENTIRE file at AbsolutePath {idx['bootstrap_instruction_path']} exactly once, no range. Follow it: write its tail ACK before index, then fixed media and proposals. Any error/missing ACK: STOP, no retry. Only view_file/write_to_file."
  put(a/'short_prompt.txt',short.encode('utf-8'));assert ack['marker'] not in short and ack['marker'] not in (a/'index.json').read_text(encoding='utf-8')
  inputs=dict(fr0['inputs']);inputs.update(sources);inputs.update(bindings);inputs[str(ROOT/'readiness_actual34.json')]=sha(ROOT/'readiness_actual34.json');inputs[str(binding)]=sha(binding);inputs[str(ROOT/'exact_scientific_alias_transfer.json')]=sha(ROOT/'exact_scientific_alias_transfer.json')
  for p in a.iterdir():inputs[str(p)]=sha(p)
  fr=copy.deepcopy(fr0);fr.update(inputs=inputs,read_whitelist=[project(p) for p in fr0['read_whitelist']],self_read_whitelist=[project(p) for p in fr0['self_read_whitelist']],write_whitelist=[project(p) for p in fr0['write_whitelist']],protocol_sha256=sha(ROOT/'PROTOCOL.md'),execution_binding_sha256=sha(binding),bootstrap_instruction_path=idx['bootstrap_instruction_path'],bootstrap_ack_path=idx['bootstrap_ack_path'],bootstrap_ack_expected_path=idx['bootstrap_ack_expected_path'],bootstrap_sha256=sha(a/'bootstrap_instruction.txt'),short_prompt_sha256=sha(a/'short_prompt.txt'),CLI_before=n-1,CLI_after=n,fresh_unused_call=True,recovery_registered=False,original_media_core_tool_calls=181 if n==35 else 271,expected_core_tool_calls=len(expected_core(idx)),context_read_count=0,prior_actual_spawned_CLI=34,ledger_prefix_sha256=sha(ROOT/'actual_global34_ledger_prefix.jsonl'))
  assert not any(Path(p).exists() for p in fr['write_whitelist']);assert key(idx['bootstrap_ack_expected_path']) not in {key(p) for p in fr['read_whitelist']+fr['self_read_whitelist']}
  save(a/'freeze.json',fr)
  pixels=[dict(job_index=w['job_index'],checks=verify_png_pixels(w)) for w in idx['windows']]
  save(a/'prepared_png_pixel_checks.json',dict(status='CPU_EXISTING_PLANNED_PNG_BYTES_RGB_GEOMETRY_MATCH_ORIGINAL_NO_VIDEO_DECODE',windows=pixels))
  length=len(subprocess.list2cmdline(command(n,short)).encode('utf-16-le'))//2+1;assert length<1024 and length<32767
  calls.append(dict(CLI=n,jobs=fr['fixed_job_indices'],core=fr['expected_core_tool_calls'],input_count=len(inputs),argv_utf16_units_including_NUL=length,freeze_sha256=sha(a/'freeze.json'),index_sha256=sha(a/'index.json'),bootstrap_sha256=sha(a/'bootstrap_instruction.txt'),bootstrap_bytes=len(payload),Go_LF_lines=len(payload.split(b'\n')),Python_splitlines=len(payload.splitlines()),tailLF=True,noCR=True,short_sha256=sha(a/'short_prompt.txt'),pixel_checks_sha256=sha(a/'prepared_png_pixel_checks.json')))
 AST=[]
 for p in ROOT.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'));AST.append(dict(path=str(p),sha256=sha(p)))
 save(ROOT/'plan.json',dict(status='PREPARED_FRESH_UNUSED35_36_V6_PENDING_ROOT_REVIEW_NO_START',routing={'35':[19,20],'36':[21,22,23]},calls=calls,fixed_denominator=24,teacher_supplement_denominator=21,actual_global=34,global_cap=36,root_gate_status_required='ROOT_APPROVED_START_FRESH_SCOPE_V6_FIXED_CLI35_36',new_model_calls=0))
 save(ROOT/'dry_run_acceptance.json',dict(status='PASS_10_AST_EXACT_ORIGINAL_MEDIA_NEW_FROZEN_PATHS_NO_MODEL_PENDING_ROOT',AST=AST,calls=calls,execution_binding_sha256=sha(binding),readiness_sha256=sha(ROOT/'readiness_actual34.json'),reconciliation_sha256=sha(BASE.parent/'teacher34_terminal_reconciliation_v1.json'),planned_aliases=365,new_model_calls=0,new_video_decode=0,requires_independent_CPU_negative_receipt=True,cash_cost='UNKNOWN_NOT_ZERO'))
 print(json.dumps(dict(root=str(ROOT),calls=calls,source_binding_sha256=sha(binding),dry_run_sha256=sha(ROOT/'dry_run_acceptance.json')),ensure_ascii=False))
if __name__=='__main__':main()
