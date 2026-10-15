"""ROOT actual identity proof for the eight recorded separator-only deviations."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,os
R=Path(__file__).resolve().parent
C=R/'teacher_expansion/schema_recovery_23_continuation_v2/call40'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):return {'path':str(p),'sha256':sha(p)}
idx=read(C/'index.json');scope=read(C/'w23_completed_scope_audit.json');whole=read(C/'audit.json');term=read(C/'terminal.json')
assert term['exit_code']==0 and term['stop_reason'] is None and term['launch_exception'] is None
assert whole['actual_result_status']=='SUCCESS' and whole['status']=='REJECTED_WHOLE_CLI_KEEP_ALL_ACTUAL_RAW_COST'
assert scope['status']=='REJECT_ACTUAL_SCOPE_KEEP_RAW_NO_RETRY'
for k in ('all_raw_tool_state_issues','errored_tool_attempts','unfinished_tool_attempts','reported_nonmedia_errors','immutable_drift','repeated_media_attempts','rewritten_output_attempts','actual_post_last_proposal_tool_updates'):assert not whole[k],k
assert whole['actual_core_tool_calls']==whole['expected_core_tool_calls']==128
assert len(whole['tool_issues'])==16 and all(x['reason']=='ANY_RAW_VIEW_PARAMETERS_NOT_EXACT_LITERAL' for x in whole['tool_issues'])
rows=[json.loads(x) for x in (C/'stream.jsonl').read_text(encoding='utf-8').splitlines()]
steps=[188,189,190,191,193,194,195,196];checks=[]
for step,f in zip(steps,idx['windows'][0]['student_previews']):
 updates=[r['step_update'] for r in rows if r.get('step_update',{}).get('step_index')==step and r.get('step_update',{}).get('step_type')=='tool']
 assert [t['state'] for t in updates]==['ACTIVE','DONE']
 expected=f['path'];actual=expected.replace('engineering_alias_remainder_v3\\aliases','engineering_alias_remainder_v3\\\\aliases')
 assert actual!=expected and actual.count('\\\\')==1 and '..' not in actual and actual.startswith('G:\\ai\\AIC视频\\')
 for t in updates:assert t['tool_name']=='view_file' and t['tool_info']['parameters']=={'AbsolutePath':actual}
 assert Path(actual).resolve(strict=True)==Path(expected).resolve(strict=True)
 assert os.path.samefile(actual,expected)
 sa,se=os.stat(actual),os.stat(expected);assert (sa.st_dev,sa.st_ino,sa.st_size)==(se.st_dev,se.st_ino,se.st_size)
 assert sha(actual)==sha(expected)==sha(f['original_path'])==f['png_sha256']
 info=updates[-1]['tool_info'];assert set(info)=={'name','parameters'} and info['name']=='view_file'
 checks.append(dict(step=step,actual_path=actual,expected_literal=expected,actual_windows_samefile=True,actual_file_identity=dict(device=sa.st_dev,inode=sa.st_ino,bytes=sa.st_size),png_sha256=f['png_sha256'],actual_DONE_tool_record=updates[-1],tool_image_output_metadata='ABSENT_NOT_INFERRED'))
fr=read(C/'freeze.json')
for p,h in fr['inputs'].items():assert sha(p)==h,p
assert sha(C/'stream.jsonl')==term['stream_sha256']
pref=scope['immutable_prefix'];assert sha(pref['path'])==pref['sha256'] and (C/'stream.jsonl').read_bytes().startswith(Path(pref['path']).read_bytes())
for x in scope['immutable_actual_outputs']:assert sha(x['original_path'])==x['sha256']==x['sealed_copy_sha256']==sha(x['sealed_copy_path'])
v=dict(status='PASS_ROOT_ACTUAL_WINDOWS_SAMEFILE_AND_FROZEN_SHA_EIGHT_SEPARATOR_ONLY_NOT_SCOPE_ADMISSION',utc=datetime.now(timezone.utc).isoformat(),checks=checks,frozen_inputs_checked=len(fr['inputs']),immutable_outputs_checked=len(scope['immutable_actual_outputs']),original_strict_REJECT_preserved=True,original_literal_noncompliance_preserved=True,new_model_calls=0,new_decoder_calls=0,new_processor_calls=0,semantic_review=False,bindings={n:bind(C/n) for n in ('terminal.json','audit.json','w23_completed_scope_audit.json','stream.jsonl','actual_terminal_cost.json')})
p=R/'root_actual_CLI40_separator_identity_v1.json'
with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
print(json.dumps(bind(p),ensure_ascii=False))
