"""Prepare only fixed remaining fresh calls; never launch a teacher."""
from pathlib import Path
from datetime import datetime, timezone
from importlib.util import spec_from_file_location, module_from_spec
import ast, hashlib, json
BASE=Path(__file__).resolve().parent
OLD=BASE/'capacity_v4_tool_batches'
PRIOR=BASE/'remaining_CLI32_36_literal_paths_v1'
ROOT=BASE/'remaining_CLI33_36_same_index_selfcheck_v2'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def write(p,v):
 with Path(p).open('x',encoding='utf-8',newline='') as f:f.write(v)
assert read(PRIOR/'call06/terminal.json')['CLI_after']==32 and (PRIOR/'stopped.json').exists()
ledger=BASE/'global_CLI_ledger.jsonl'
assert max(json.loads(s)['global_count'] for s in ledger.read_text(encoding='utf-8').splitlines() if s.strip())==32
ROOT.mkdir(exist_ok=False)
write(ROOT/'PROTOCOL.md','''# CLI33..36 固定 fresh 同index自检工程协议 v2

仅准备固定旧call07..10、jobs16/17、18/19、20/21、22/23四双窗；global33..36、36硬上限，每call7200秒、gemini-3.8-flash-high，无自动重试。必须主控独立核本版source/AST/SHA/four freezes并写root_start_admission.json后单独授权启动。本次准备新模型0。CLI32自然exit0/SUCCESS但原严格181/191 audit拒绝、11次index读、非媒体metadata及真实费用完整封存；旧32/13不重试、不回写旧失败或成功。旧32实际媒体证据只供root独立判断，不在本版改成PASS。

新index逐字节继承原未执行call07..10，原source1458字节及domain/native64 PNG/16facts绑定/clip/8 effective学生preview/geometry/PTS/所有输入SHA/输出路径不变；不重新decode。新raw/request/terminal/audit写本版目录；事实与提案仅原计划尚不存在的输出。全部原冻结/source/白名单保留。

唯一读取工程变化：初始必须读取本次唯一冻结index；后续必要时可对同一白名单精确路径及SHA绑定字节只读自检。建议整call总≤5次以节省费用，但此建议不构成科学或媒体准入硬次数门。全部真实次数/step顺序/费用记录。审计仅从核心媒体序列剔除同index额外只读；不允许其他index/文件/媒体或未白名单路径，也不把index自检算作媒体观察。不得通过复读修改目标、窗口或质量门。

每窗16组，slot0..3同response四个独立view_file、全4实际DONE后立即write该组4条单帧静态事实。64facts封存后clip一次，随后按原index八条literal AbsolutePath实际读取全部8 preview才proposal；实际学生processor64帧。不得拼目录、推测路径、重复成功媒体或覆盖成功输出；成功自身指定输出最多一次写后核对。移除index自检后核心媒体及输出严格完整匹配原64读+16写+clip+8读+proposal序列。事实程序绑定身份，不由单帧猜动作/心理/动机或字幕语言，不能复制identity。科学KEEP/NO/UNKNOWN/独立事件/边界range/fact支持/所有NO理由不变、无事件配额，不以整窗叙事/字幕内容替代高光。

任何实际媒体tool ERROR、未完成媒体/事实/提案、重复媒体、路径或SHA漂移、其他非法tool/文件、401/认证或工程失败均保留raw并停止，不自动重试或推进。未提供正文的非媒体error_message只是实际metadata，单独记UNKNOWN原因，不冒称媒体读取失败，也不改其原记录。实际CLI exit/result原样保存；非SUCCESS结果或有正文错误仍暂停主控审理，媒体完整不冒充CLI成功。AGY SUCCESS不能覆盖媒体ERROR/缺失/提前终态。所有现金UNKNOWN不记0，stream usage只是实际字段非账单。

禁止旧答案/评分/预测/其他评审/terminal/code/web/其他模型/subagent，教师只看当前window冻结媒体。两窗独立；吞吐batch诊断仅性能记录，不追加质量门。结构与真实供给不等于semantic或训练准入，root+独立student负责；全24分母和21补充分母保留。GPU/Qwen/decoder/训练/optimizer/426/100confirm均0。
''')

prompt=(PRIOR/'prompt.py').read_text(encoding='utf-8-sig')
needle="先view_file { (a/'index.json').as_posix() } 一次。"
assert prompt.count(needle)==1
prompt=prompt.replace(needle,"先view_file { (a/'index.json').as_posix() } 完整读取一次。后续仅在确有必要时可复读这一同路径、同冻结字节的index自查，建议整会话总读取≤5次以节省费用；这只是建议，不是媒体准入次数门。不能改读其他index或文件，不能借自查重复媒体或改变范围；尽量在组完整写出后或预览全8DONE后核对，四图全DONE后仍立即写本组。")
write(ROOT/'prompt.py',prompt)
pair=(PRIOR/'run_pair.py').read_text(encoding='utf-8-sig').replace('range(6,11)','range(7,11)')
write(ROOT/'run_pair.py',pair)
launch=(PRIOR/'launch.py').read_text(encoding='utf-8-sig')
launch=launch.replace('ROOT_APPROVED_START_FIXED_LITERAL_CLI32_36','ROOT_APPROVED_START_FIXED_SELF_CHECK_CLI33_36')
launch=launch.replace("ROOT.parent/'capacity_v4_tool_batches/call05/terminal.json'","ROOT.parent/'remaining_CLI32_36_literal_paths_v1/call06/terminal.json'").replace("prior['CLI_after']==31","prior['CLI_after']==32")
launch=launch.replace('remaining_CLI32_36_literal_paths_v1/','remaining_CLI33_36_same_index_selfcheck_v2/')
launch=launch.replace("ROOT.parent/'remaining_CLI33_36_same_index_selfcheck_v2/call06/terminal.json'","ROOT.parent/'remaining_CLI32_36_literal_paths_v1/call06/terminal.json'")
write(ROOT/'launch.py',launch)
write(ROOT/'supply_policy.py','''"""Only exact frozen index rereads are engineering selfchecks, not media."""
from pathlib import Path
def key(p):return str(Path(p).resolve()).casefold()
def index_selfchecks(steps,index_path):
    target=key(index_path);kept=[];checks=[]
    for t in steps:
        p=t.get('tool_info',{}).get('parameters',{})
        if t.get('tool_name')=='view_file' and key(p.get('AbsolutePath',''))==target:
            checks.append(dict(step=t.get('step_index'),path=p.get('AbsolutePath'),core_tools_before=len(kept),initial=(len(checks)==0)))
            if len(checks)==1:kept.append(t)
        else:kept.append(t)
    return kept,dict(exact_index_path=str(index_path),DONE_read_count=len(checks),extra_read_count=max(0,len(checks)-1),reads=checks,advisory_total_max=5,hard_count_limit=False,index_is_not_media=True)
def classify_nonmedia_errors(steps):
    metadata={'conversation_id','step_index','state','step_type','duration_seconds'}
    bare=[];reported=[]
    for t in steps:
        body={k:v for k,v in t.items() if k not in metadata and v not in (None,'',{},[]) and not (isinstance(v,str) and not v.strip())}
        if body:reported.append(t)
        else:bare.append(dict(actual_metadata=t,cause='UNKNOWN_NO_BODY_IN_ACTUAL_STREAM',is_media_read_failure=False))
    return bare,reported
''')
audit=(PRIOR/'audit_pair.py').read_text(encoding='utf-8-sig')
audit=audit.replace('import json,hashlib,sys','import json,hashlib,sys\nfrom supply_policy import index_selfchecks,classify_nonmedia_errors')
needle="    # Exact model supply contract. Optional one self-read may occur after its write."
audit=audit.replace(needle,"    steps,index_checks=index_selfchecks(steps,a/'index.json')\n"+needle)
needle="    out=dict(utc=datetime.now(timezone.utc).isoformat()"
audit=audit.replace(needle,"    nonmedia_steps=[r['step_update'] for r in rows if r.get('step_update',{}).get('step_type')=='error_message']\n    bare_metadata,reported_errors=classify_nonmedia_errors(nonmedia_steps)\n"+needle)
audit=audit.replace("tool_issues=issues,self_reads=selfcounts", "tool_issues=issues,index_selfchecks=index_checks,bare_nonmedia_error_metadata=bare_metadata,reported_nonmedia_errors=reported_errors,self_reads=selfcounts")
write(ROOT/'audit_pair.py',audit)
completed=(PRIOR/'audit_completed_window.py').read_text(encoding='utf-8-sig')
completed=completed.replace('import json, hashlib, sys','import json, hashlib, sys\nfrom supply_policy import index_selfchecks')
completed=completed.replace("    steps=[r['step_update'] for r in valid", "    all_prefix_tools=[r['step_update'] for r in valid if r.get('step_update',{}).get('step_type')=='tool']\n    latest_prefix_tools={t['step_index']:t for t in all_prefix_tools}\n    allowed_read_paths={key(p) for p in fr['read_whitelist']+fr['self_read_whitelist']}\n    for t in latest_prefix_tools.values():\n        if t.get('state') in ('ERROR','ACTIVE'):issues.append(dict(reason='PREFIX_TOOL_ERROR_OR_UNFINISHED',step=t['step_index'],actual_state=t.get('state')))\n        if t.get('tool_name') not in ('view_file','write_to_file'):issues.append(dict(reason='PREFIX_ILLEGAL_TOOL',step=t['step_index']))\n    for t in all_prefix_tools:\n        if t.get('tool_name')=='view_file' and key(t.get('tool_info',{}).get('parameters',{}).get('AbsolutePath','')) not in allowed_read_paths:issues.append(dict(reason='PREFIX_OUTSIDE_READ_WHITELIST_ATTEMPT',step=t['step_index']))\n    steps=[r['step_update'] for r in valid")
completed=completed.replace("    expected=[('view_file',key(a/'index.json'))]", "    steps,index_checks=index_selfchecks(steps,a/'index.json')\n    expected=[('view_file',key(a/'index.json'))]")
completed=completed.replace("actual_supply=supply,native_read_done=64", "actual_supply=supply,index_selfchecks=index_checks,native_read_done=64")
write(ROOT/'audit_completed_window.py',completed)
write(ROOT/'progress.py',(PRIOR/'progress.py').read_text(encoding='utf-8-sig'))
controller=(PRIOR/'controller.py').read_text(encoding='utf-8-sig')
controller=controller.replace('ROOT_APPROVED_START_FIXED_LITERAL_CLI32_36','ROOT_APPROVED_START_FIXED_SELF_CHECK_CLI33_36')
controller=controller.replace('==31','==32').replace('range(6,11)','range(7,11)').replace('range(6, 11)','range(7, 11)').replace('range(14,24)','range(16,24)').replace('range(32,37)','range(33,37)')
controller=controller.replace("fresh_continuation_after_CLI30_v1/full_denominator24_after_CLI31.json", "remaining_CLI32_36_literal_paths_v1/full_denominator24_after_CLI32.json")
controller=controller.replace("or audit.get('error_message_steps') or audit.get('errored_tool_attempts')", "or audit.get('reported_nonmedia_errors') or audit.get('errored_tool_attempts')")
controller=controller.replace('COMPLETE_FIXED10_FRESH_STRUCTURES','COMPLETE_FIXED8_FRESH_STRUCTURES').replace('fresh_windows=10','fresh_windows=8')
controller=controller.replace('FRESH_AFTER_CLI30_TERMINAL_AUDITED','FRESH_AFTER_CLI32_TERMINAL_AUDITED')
write(ROOT/'controller.py',controller)
observer=(PRIOR/'observe_receipts.py').read_text(encoding='utf-8-sig').replace('remaining_CLI32_36_literal_paths_v1','remaining_CLI33_36_same_index_selfcheck_v2').replace('range(6, 11)','range(7, 11)')
write(ROOT/'observe_receipts.py',observer)
prefix=ROOT/'global_CLI32_ledger_prefix.jsonl'
with prefix.open('xb') as f:f.write(ledger.read_bytes())
preserved=[Path(__file__),prefix,BASE/'readonly_protocol_composed_media_inquiry_CLI31.json',PRIOR/'PROTOCOL.md',PRIOR/'controller.py',PRIOR/'registered.json',PRIOR/'stopped.json',PRIOR/'root_start_admission.json',PRIOR/'full_denominator24_after_CLI32.json']
preserved += [PRIOR/'call06'/n for n in ('freeze.json','request.json','terminal.json','stream.jsonl','audit.json','actual_partial_terminal_receipt.json','actual_tool_batch_audit.json','step1_nonmedia_metadata_readonly_diagnosis.json','actual_media_completion_evidence_original_strict_failed.json','w14_completed_scope_audit.json','w14_program_bound_facts.json','w15_program_bound_facts.json')]
runtime={str(p):sha(p) for p in ROOT.glob('*.py')};runtime[str(ROOT/'PROTOCOL.md')]=sha(ROOT/'PROTOCOL.md')
execution=ROOT/'execution_code_binding.json'
save(execution,dict(utc=datetime.now(timezone.utc).isoformat(),sources=runtime,prior_failure_inputs={str(p):sha(p) for p in preserved},new_model_calls=0,requires_root_start_admission=True))
runtime[str(execution)]=sha(execution)
spec=spec_from_file_location('selfcheck_v2_prompt',ROOT/'prompt.py');m=module_from_spec(spec);spec.loader.exec_module(m)
calls=[]
for n in range(7,11):
 old=OLD/f'call{n:02d}';of=read(old/'freeze.json')
 assert not (old/'request.json').exists() and not (PRIOR/f'call{n:02d}/request.json').exists()
 for p,s in of['inputs'].items():assert sha(p)==s,(p,'OLD_INPUT_DRIFT')
 assert not any(Path(p).exists() for p in of['write_whitelist'])
 dest=ROOT/f'call{n:02d}';dest.mkdir()
 with (dest/'index.json').open('xb') as f:f.write((old/'index.json').read_bytes())
 inputs=dict(of['inputs']);inputs.update(runtime);inputs.update({str(p):sha(p) for p in [old/'index.json',old/'freeze.json',dest/'index.json',*preserved]})
 reads=[str(dest/'index.json') if Path(p)==old/'index.json' else p for p in of['read_whitelist']]
 freeze=dict(utc=datetime.now(timezone.utc).isoformat(),inputs=inputs,read_whitelist=reads,self_read_whitelist=of['self_read_whitelist'],write_whitelist=of['write_whitelist'],protocol_sha256=sha(ROOT/'PROTOCOL.md'),parent_protocol_sha256=sha(BASE/'PROTOCOL.md'),fixed_job_indices=of['fixed_job_indices'],CLI_before=of['CLI_before'],CLI_after=of['CLI_after'],global_cap=36,timeout_seconds=7200,automatic_retry=False,original_index_byte_exact=True,original_output_paths_preserved=True,source_index=dict(path=str(old/'index.json'),sha256=sha(old/'index.json')),execution_binding_sha256=sha(execution),same_index_selfcheck=dict(exact_path=str(dest/'index.json'),advisory_total_max=5,hard_count_limit=False))
 save(dest/'freeze_render_inputs.json',freeze)
 original=m.read;m.read=lambda p:read(dest/'freeze_render_inputs.json') if Path(p).name=='freeze.json' else original(p)
 text,literals=m.build_prompt(dest);m.read=original
 write(dest/'frozen_prompt.txt',text)
 for w,l in zip(read(dest/'index.json')['windows'],literals):
  assert [x['AbsolutePath'] for x in l['ordered_view_file_arguments']]==[f['path'] for f in w['student_previews']]
  assert len(l['ordered_view_file_arguments'])==8
 save(dest/'literal_preview_arguments.json',dict(source_index_sha256=sha(dest/'index.json'),windows=literals,paths_are_exact_index_values=True,path_construction_or_directory_guessing=False))
 inputs[str(dest/'frozen_prompt.txt')]=sha(dest/'frozen_prompt.txt');inputs[str(dest/'literal_preview_arguments.json')]=sha(dest/'literal_preview_arguments.json')
 freeze['frozen_prompt_sha256']=sha(dest/'frozen_prompt.txt');save(dest/'freeze.json',freeze)
 assert m.build_prompt(dest)==(text,literals)
 calls.append(dict(call=n,jobs=freeze['fixed_job_indices'],CLI_after=freeze['CLI_after'],input_count=len(inputs),old_index_sha256=sha(old/'index.json'),new_index_sha256=sha(dest/'index.json'),freeze_sha256=sha(dest/'freeze.json'),prompt_sha256=sha(dest/'frozen_prompt.txt'),literal_preview_arguments_sha256=sha(dest/'literal_preview_arguments.json'),all_old_inputs_SHA_verified=True))
AST=[]
for p in ROOT.glob('*.py'):
 ast.parse(p.read_text(encoding='utf-8-sig'));AST.append(dict(path=str(p),sha256=sha(p),AST_PASS=True))
# No model: verify exact index filtering has no numerical reject gate and leaves other paths.
spec=spec_from_file_location('selfcheck_v2_policy',ROOT/'supply_policy.py');policy=module_from_spec(spec);spec.loader.exec_module(policy)
sample_index=ROOT/'call07/index.json'
def t(i,p,name='view_file'):return dict(step_index=i,tool_name=name,tool_info=dict(parameters=dict(AbsolutePath=str(p))))
sample=[t(i,sample_index) for i in range(11)]+[t(11,ROOT/'not_whitelisted.json')]
kept,checks=policy.index_selfchecks(sample,sample_index)
assert len(kept)==2 and checks['DONE_read_count']==11 and not checks['hard_count_limit']
bare,reported=policy.classify_nonmedia_errors([dict(step_index=1,step_type='error_message',state='DONE',duration_seconds=0),dict(step_index=2,step_type='error_message',message='UNAUTHENTICATED HTTP401')])
assert len(bare)==1 and len(reported)==1
save(ROOT/'plan.json',dict(utc=datetime.now(timezone.utc).isoformat(),fixed_calls=list(range(7,11)),fixed_jobs=list(range(16,24)),CLI_numbers=list(range(33,37)),calls=calls,global_cap=36,model='gemini-3.8-flash-high',failed_jobs13_14_15_not_retried=True,new_model_calls=0,requires_separate_root_start_authorization=True))
save(ROOT/'dry_run_acceptance.json',dict(utc=datetime.now(timezone.utc).isoformat(),status='PASS_AST_SHA_LITERAL_PATHS_INDEX_POLICY_NO_MODEL_PENDING_ROOT_START',AST=AST,calls=calls,all_original_indices_byte_exact=True,all_original_media_inputs_SHA_verified=True,all_original_outputs_paths_preserved=True,exact_eight_AbsolutePath_arguments_per_window=True,same_index_filter_no_hard_count_gate_verified=True,other_path_retained_for_whitelist_rejection=True,bare_nonmedia_UNKNOWN_and_reported401_distinguished=True,actual_media_ERROR_still_rejects=True,old_audits_not_modified=True,fixed_denominator=24,teacher_expansion_denominator=21,actual_student_frames=64,timeout_seconds=7200,model='gemini-3.8-flash-high',global_cap=36,new_model_calls=0,new_decode=0,new_optimizer_updates=0,new_426=0,execution_binding_sha256=sha(execution),requires_root_start_admission=True,cash_cost='UNKNOWN_NOT_ZERO'))
print(json.dumps(dict(root=str(ROOT),source_sha256=sha(Path(__file__)),controller_sha256=sha(ROOT/'controller.py'),launch_sha256=sha(ROOT/'launch.py'),prompt_source_sha256=sha(ROOT/'prompt.py'),execution_binding_sha256=sha(execution),dry_run_sha256=sha(ROOT/'dry_run_acceptance.json'),new_model_calls=0),ensure_ascii=False))
