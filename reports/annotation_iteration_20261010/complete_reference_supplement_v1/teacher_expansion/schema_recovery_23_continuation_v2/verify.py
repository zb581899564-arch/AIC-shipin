"""Only new typed39 guard negatives and fresh40 path/text/source projection."""
from common import ROOT,BASE,read,sha,save,expected_core,scientific_core,bootstrap_metadata
from pathlib import Path
import ast,copy,json,subprocess,importlib.util
from prepare import OLD,project

def main():
 from launch import previous39_documents_guard,verify_previous39,command
 binding=read(ROOT/'execution_code_binding.json')
 for p,h in binding['sources'].items():
  assert sha(p)==h
  if p.endswith('.py'):ast.parse(Path(p).read_text(encoding='utf-8'))
 for p,h in binding['actual_prior_bindings'].items():assert sha(p)==h
 retained={}
 for name in ('engine.py','common.py','audit.py','observer.py','run_call.py'):
  assert (ROOT/name).read_bytes()==(OLD/name).read_bytes();retained[name]=sha(ROOT/name)
 recovery=ROOT.parent.parent/'schema_recovery_CLI39_final_selfread_root_recovery_v1.json';confirmed=read(recovery);prev=OLD/'call39'
 terminal=read(prev/'terminal.json');whole=read(prev/'audit.json');scope=read(prev/'w22_completed_scope_audit.json');pw=read(prev/'index.json')['windows'][0];window=pw['window_id'];proposal=pw['proposal_path']
 cases=[]
 def check(name,change=None,accept=False):
  t,w,s,c=map(copy.deepcopy,(terminal,whole,scope,confirmed))
  if change:change(t,w,s,c)
  accepted=True
  try:previous39_documents_guard(t,w,s,c,window,proposal)
  except (AssertionError,KeyError,TypeError):accepted=False
  assert accepted==accept,name;cases.append(dict(name=name,accepted=accepted,expected=accept,memory_only=change is not None))
 check('actual_TYPED_ROOT39_guard_document_positive_no_scope_reaudit',accept=True)
 check('wholePASS_cannot_substitute_REJECT_recovery',lambda t,w,s,c:w.update(status='PASS_WHOLE_ACTUAL_CLI_PENDING_ROOT_SEMANTIC'))
 check('untype_PASS_receipt_rejected',lambda t,w,s,c:c.update(status='PASS_STATIC'))
 check('missing_ROOTscope_confirmation',lambda t,w,s,c:c.update(ROOT_actual_scope_independently_verified=False))
 check('oldwholeREJECT_not_preserved',lambda t,w,s,c:c.update(old_whole_REJECTED_preserved=False))
 check('wrong_receipt_window',lambda t,w,s,c:c.update(window_id='OTHER'))
 check('resultERROR',lambda t,w,s,c:w.update(actual_result_status='ERROR'))
 check('natural_timeout',lambda t,w,s,c:t.update(stop_reason='OWNED_TIMEOUT_NO_RETRY'))
 check('natural_exit_nonzero',lambda t,w,s,c:t.update(exit_code=1))
 check('prespawn_error',lambda t,w,s,c:t.update(launch_exception='ERROR'))
 check('second_wholeissue',lambda t,w,s,c:w['continuation_decision']['issues'].append('OUTSIDE_READ'))
 check('outside_tool_afterfinal',lambda t,w,s,c:w['actual_post_last_proposal_tool_updates'].append(copy.deepcopy(w['actual_post_last_proposal_tool_updates'][1])))
 check('selfread_wrongpath',lambda t,w,s,c:w['actual_post_last_proposal_tool_updates'][0]['tool_info']['parameters'].update(AbsolutePath='OUTSIDE'))
 check('selfread_range',lambda t,w,s,c:w['actual_post_last_proposal_tool_updates'][0]['tool_info']['parameters'].update(StartLine=1))
 check('selfread_wrongstep',lambda t,w,s,c:w['actual_post_last_proposal_tool_updates'][0].update(step_index=205))
 check('selfread_incomplete_metadata',lambda t,w,s,c:w['actual_self_read_proofs'][0].update(complete=False))
 check('mediaERROR',lambda t,w,s,c:w['errored_tool_attempts'].append({'state':'ERROR'}))
 check('unfinished_tool',lambda t,w,s,c:w['unfinished_tool_attempts'].append({'state':'ACTIVE'}))
 check('immutable_drift',lambda t,w,s,c:w['immutable_drift'].append('DRIFT'))
 check('rewritten_output',lambda t,w,s,c:w['rewritten_output_attempts'].append('REWRITE'))
 check('repeated_media',lambda t,w,s,c:w['repeated_media_attempts'].append('REPEAT'))
 check('scope63',lambda t,w,s,c:s['windows'][0].update(bound_rows=63))
 check('scope127core',lambda t,w,s,c:s.update(actual_core_tool_calls=127))
 check('missing_ACKproof',lambda t,w,s,c:s['text_fragment_proofs'][0].update(complete=False))
 a=ROOT/'call40';fr=read(a/'freeze.json');idx=read(a/'index.json');w=idx['windows'][0];old=OLD/'call40';oldidx=read(old/'index.json');oldfr=read(old/'freeze.json')
 for p,h in fr['inputs'].items():assert sha(p)==h
 assert idx['windows']==project(oldidx['windows'],old,a)
 literal=read(a/'literal_execution_parameters.json');assert literal==project(read(old/'literal_execution_parameters.json'),old,a)
 assert (a/'science_verbatim_program_only.txt').read_bytes()==(old/'science_verbatim_program_only.txt').read_bytes()
 assert (a/'prepared_original_pixel_clock_checks.json').read_bytes()==(old/'prepared_original_pixel_clock_checks.json').read_bytes()
 assert read(a/'scientific_text_map.json')==project(read(old/'scientific_text_map.json'),old,a)
 assert expected_core(idx)==expected_core(project(oldidx,old,a)) and len(expected_core(idx))==128 and len(scientific_core(idx))==90
 assert fr['read_whitelist']==project(oldfr['read_whitelist'],old,a) and fr['write_whitelist']==project(oldfr['write_whitelist'],old,a)
 assert fr['self_read_whitelist']==[g['output_path'] for g in w['groups']] and w['proposal_path'] not in fr['read_whitelist']+fr['self_read_whitelist']
 assert len(idx['text_fragments'])==19 and fr['fragment_count']==19 and fr['expected_core_tool_calls']==128 and fr['fixed_job_indices']==[23]
 from prompt import piece,main_body,header_body,native_body,proposal_body
 spec=importlib.util.spec_from_file_location('old_single_prompt',OLD/'prompt.py');oldprompt=importlib.util.module_from_spec(spec);spec.loader.exec_module(oldprompt)
 assert proposal_body(w).split('最终仅用此原白名单TargetFile：')[0]==oldprompt.proposal_body(w).split('最终仅用此原白名单TargetFile：')[0]
 assert native_body(w,0,literal[0])==oldprompt.native_body(w,0,literal[0])
 parts=idx['text_fragments'];headers=[p for p in parts if p['kind']=='header'];science=(a/'science_verbatim_program_only.txt').read_text(encoding='utf-8');short=(a/'short_prompt.txt').read_text(encoding='utf-8')
 white=set(fr['read_whitelist']+fr['self_read_whitelist']);proof=[]
 for p in parts:
  body=main_body(science,headers,40,[23]) if p['kind']=='main' else header_body(w,[q for q in parts if q['kind']=='native_index'],literal[0]) if p['kind']=='header' else proposal_body(w) if p['kind']=='proposal_schema' else native_body(w,p['before_group'],literal[0])
  ack=read(p['expected_ACK_path']);payload=Path(p['path']).read_bytes();assert payload==piece(body,ack,p['ack_path']).encode() and len(payload)<30000 and bootstrap_metadata(payload,f'{len(payload)} bytes, {len(payload.split(bytes([10])))} lines')
  assert p['expected_ACK_path'] not in white and ack['marker'] not in short and ack['marker'] not in (a/'index.json').read_text(encoding='utf-8')
  if p['kind']=='main':assert science in body and 'proposal绝对不得自读' in body and '最终proposal write DONE后立即自然finish' in body and '成功指定facts/proposal' not in body
  if p['kind']=='proposal_schema':assert '禁止proposal自读、facts自读、header自查或任何后续工具' in body
  proof.append(dict(part_id=p['part_id'],sha256=sha(p['path']),bytes=len(payload)))
 verify_previous39({'previous39_recovery':fr['previous39_recovery']})
 assert not(a/'request.json').exists() and not(ROOT/'root_start_admission_CLI40.json').exists() and not any(Path(p).exists() for p in fr['write_whitelist'])
 units=len(subprocess.list2cmdline(command(40,short)).encode('utf-16-le'))//2+1;assert units<1024
 save(ROOT/'independent_CPU_negative_acceptance.json',dict(status='PASS_NECESSARY_TYPED39_RECOVERY_GUARDS_FRESH40_PROJECTION_NO_MODEL_PENDING_ROOT',source_binding_sha256=sha(ROOT/'execution_code_binding.json'),new_cases=cases,retained_original_scientific_engine_sources=retained,actual_recovery_binding=fr['previous39_recovery'],new_text_proofs=proof,exact_science6_bytes_sha256=sha(a/'science_verbatim_program_only.txt'),projection_scope128=True,argv_utf16_units_including_NUL=units,old51_24_68_repeated=False,prior_v1_necessary_CPU_receipt=dict(path=str(OLD/'independent_CPU_negative_acceptance.json'),sha256=sha(OLD/'independent_CPU_negative_acceptance.json')),new_model_calls=0,new_RGB_decode=0,new_decoder_calls=0,new_processor_calls=0))
 print(json.dumps(dict(receipt_sha256=sha(ROOT/'independent_CPU_negative_acceptance.json'),cases=len(cases),argv_units=units,max_text_bytes=max(p['bytes'] for p in proof))))

if __name__=='__main__':main()
