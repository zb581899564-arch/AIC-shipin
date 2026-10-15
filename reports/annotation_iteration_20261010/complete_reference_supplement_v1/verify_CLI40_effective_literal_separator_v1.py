"""Twelve bounded in-memory counterexample classes; no actual recovery, pixels or model."""
from pathlib import Path
import ast,copy,json
from datetime import datetime,timezone
import recover_CLI40_effective_literal_separator_v1 as h

def main():
 root=h.R;helpers={str(root/n):h.sha(root/n) for n in h.HELPERS}
 for path in helpers:ast.parse(Path(path).read_text(encoding='utf-8'))
 frames=[dict(path='G:'+chr(92)+'MEMORY'+chr(92)+'engineering_alias_remainder_v3'+chr(92)+'aliases'+chr(92)+'w23'+chr(92)+'effective'+chr(92)+f'F{i:02d}.png') for i in range(8)]
 rows=[]
 for step,frame in zip(h.STEPS,frames):
  path=frame['path'];at=path.index('engineering_alias_remainder_v3')+len('engineering_alias_remainder_v3');actual=path[:at]+chr(92)+path[at:]
  for state in ('ACTIVE','DONE'):rows.append(dict(step_update=dict(step_type='tool',step_index=step,state=state,tool_name='view_file',tool_info=dict(name='view_file',parameters=dict(AbsolutePath=actual)))))
 projected,changes=h.project_rows(rows,frames);assert len(changes)==16
 arrays=('all_raw_tool_state_issues','errored_tool_attempts','unfinished_tool_attempts','reported_nonmedia_errors','error_message_steps')
 terminal=dict(CLI_after=40,child_process_created=True,exit_code=0,stop_reason=None,launch_exception=None)
 whole=dict(status='REJECTED_WHOLE_CLI_KEEP_ALL_ACTUAL_RAW_COST',actual_result_status='SUCCESS',actual_result_error=None,tool_issues=h.expected_issues(changes),actual_core_tool_calls=128,expected_core_tool_calls=128,self_reads={})
 for k in arrays+('actual_post_last_proposal_tool_updates','actual_pre_completion_result_ERRORS','actual_post_completion_result_ERRORS','immutable_drift','repeated_media_attempts','rewritten_output_attempts'):whole[k]=[]
 scope={k:[] for k in arrays};scope.update(status='REJECT_ACTUAL_SCOPE_KEEP_RAW_NO_RETRY',tool_issues=h.expected_issues(changes),actual_core_tool_calls=128,expected_core_tool_calls=128,additional_scope_issues=[],text_fragment_proofs=[dict(complete=True) for _ in range(19)],immutable_actual_outputs=[dict(memory=True) for _ in range(36)],windows=[dict(window_id='Yi4Ij2NM7U4:SLOT6:6',job_index=23,bound_rows=64,bound_fact_rows=[dict(memory=True) for _ in range(64)],core_tool_count=126,scientific_media_fact_tool_count=90,schema_issues=[],proposal_issues=[],local_tool_issues=h.expected_issues(changes),window_core_sequence_complete=True,effective_preview_batch_barrier=dict(two_distinct_forward_four_image_batches_then_proposal=True))])
 h.document_guard(terminal,whole,scope,changes);cases=[]
 def fail(name,operation):
  rejected=False
  try:operation()
  except (AssertionError,KeyError,TypeError,ValueError):rejected=True
  assert rejected,name;cases.append(dict(counterexample_class=name,rejected=True,memory_only=True))
 def altered(change):
  r=copy.deepcopy(rows);change(r);return h.project_rows(r,frames)
 fail('additional_separator_not_allowed',lambda:altered(lambda r:r[0]['step_update']['tool_info']['parameters'].update(AbsolutePath=r[0]['step_update']['tool_info']['parameters']['AbsolutePath'].replace('MEMORY'+chr(92),'MEMORY'+chr(92)*2))))
 fail('wrong_ordinal_or_filename',lambda:altered(lambda r:r[0]['step_update']['tool_info']['parameters'].update(AbsolutePath=r[0]['step_update']['tool_info']['parameters']['AbsolutePath'].replace('F00','F99'))))
 fail('different_case_not_normalized',lambda:altered(lambda r:r[0]['step_update']['tool_info']['parameters'].update(AbsolutePath=r[0]['step_update']['tool_info']['parameters']['AbsolutePath'].replace('aliases','ALIASES'))))
 fail('ranged_view_parameters',lambda:altered(lambda r:r[0]['step_update']['tool_info']['parameters'].update(StartLine=1)))
 fail('ACTIVE_DONE_toolname_conflict',lambda:altered(lambda r:r[0]['step_update'].update(tool_name='other_tool')))
 fail('missing_ACTIVE_or_wrong_step',lambda:h.project_rows(copy.deepcopy(rows[1:]),frames))
 fail('real_media_ERROR',lambda:altered(lambda r:r[1]['step_update'].update(state='ERROR')))
 def guard_mutate(target,key,value):
  t,w,s=map(copy.deepcopy,(terminal,whole,scope));(t,w,s)[target][key]=value;h.document_guard(t,w,s,changes)
 fail('outside_or_extra_issue_not_hidden',lambda:guard_mutate(1,'tool_issues',whole['tool_issues']+[dict(reason='ANY_RAW_OUTSIDE_READ')]))
 fail('not_natural_SUCCESS_or_timeout',lambda:guard_mutate(0,'stop_reason','OWNED_TIMEOUT_NO_RETRY'))
 fail('byte_drift_or_later_write',lambda:guard_mutate(1,'immutable_drift',[dict(memory_drift=True)]))
 fail('missing_128_or_19ACK_completion',lambda:guard_mutate(2,'actual_core_tool_calls',127))
 fail('schema_or_effective_batch_failure',lambda:guard_mutate(2,'windows',[dict(scope['windows'][0],schema_issues=['MEMORY_INVALID_SCHEMA'])]))
 output=root/'CLI40_effective_literal_separator_necessary_CPU_receipt_v1.json';assert not output.exists()
 receipt=dict(status='PASS_NECESSARY_EXACT_EIGHT_SEPARATOR_GUARD_CPU_NO_ACTUAL_RECOVERY',utc=datetime.now(timezone.utc).isoformat(),helpers=helpers,positive=dict(exact_eight_paths_sixteen_ACTIVE_DONE_changes=True,exact_document_guard=True,in_memory_only=True),counterexample_classes=cases,source=h.bind(__file__),new_model_calls=0,new_decoder_calls=0,new_processor_calls=0,actual_recovery_executed=False,old_tests_repeated=False)
 with output.open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
 print(json.dumps(dict(receipt=h.bind(output),helpers=helpers,counterexample_classes=len(cases)),ensure_ascii=False))
if __name__=='__main__':main()
