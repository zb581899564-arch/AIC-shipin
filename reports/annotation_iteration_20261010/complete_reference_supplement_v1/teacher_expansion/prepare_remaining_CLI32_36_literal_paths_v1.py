"""Prepare only: preserve exact old indices/media and freeze literal preview requests."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import json

BASE = Path(__file__).resolve().parent
OLD = BASE / 'capacity_v4_tool_batches'
ROOT = BASE / 'remaining_CLI32_36_literal_paths_v1'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open('x', encoding='utf-8') as output:
        json.dump(value, output, ensure_ascii=False, indent=2)


def write(path, value):
    with path.open('x', encoding='utf-8', newline='') as output:
        output.write(value)


ROOT.mkdir(exist_ok=False)
write(ROOT / 'PROTOCOL.md', '''# CLI32..36 fixed fresh 逐字预览路径协议

仅准备旧固定 call06..10/jobs14..23/CLI32..36，五独立双窗，每call7200秒，无自动重试，gemini-3.8-flash-high。Root审查本版source/AST/全部SHA并单独写root_start_admission.json后才可启动；本次准备新模型0。旧CLI31 native64/clip成功观察不重读，job13原失败及工具ERROR/拒绝保留，不合并媒体、不重试13。全部历史raw/终态/费用不回写。

新index为旧未执行index逐字节复制，连输出路径也保持原计划；写输出仅指向原teacher_expansion下尚不存在的call06..10预定文件，所有新request/raw/terminal/audit在本新版本目录。旧index/freeze/执行source不修改。domain/source/RGB/geometry/PTS/64PNG/clip/8学生预览/实际student64和SHA全部原字节继承，不重新decode。

每窗16组逐组按slot0..3，一response提交4个view_file；4图真实DONE后立即写本组4条静态事实。不拼媒体目录、文件名或路径，不由单图猜动作/心理/字幕语言，不复制identity，成功文件不覆盖。全部64facts封存后clip一次，再一response提交8预览工具。新request给出两窗各8个独立完整AbsolutePath参数，由index.windows[].student_previews[].path逐字提取，禁止推测目录名或用学生预览字段名拼路径。全8实际DONE才能proposal；任一ERROR立即如实停，不能称完成，更不能因最终AGY resultSUCCESS让缺媒体进入准入。真实ERROR记录与未终态ACTIVE区分，旧CLI31audit不回写。

完整KEEP/NO/UNKNOWN、独立事件、全部NO理由、fact支持及边界range科学schema/目标不变，不设事件配额，不把字幕/常态/叙事自动当短高光。两窗完全独立。仅view_file/write_to_file及冻结白名单，禁止旧标签/评分/预测/其他评审/terminal/code/web/search/其他模型/subagent。已写指定输出最多一次写后核对。吞吐batch诊断仅性能证据，真实供给与顺序仍是科学要件。

真实认证/工具/结构失败自然终态后停止，不自动重试或推进下一call。global36硬上限。已完成第一窗可独立保留合法scope，不因第二窗失败撤销其实际供给；主控仍负责语义和训练准入。现金UNKNOWN不为0。固定24分母由CLI31快照移交，仅新增这些fresh结构状态。新GPU/Qwen/decoder/训练/optimizer/426/100confirm0。
''')

# Preserve the old science prompt, adding only exact path supply and error semantics.
source = (OLD / 'run_pair.py').read_text(encoding='utf-8-sig')
begin = source.index("prompt=f'''")
finish = source.index('\nlaunch(a,prompt)', begin)
body = source[begin:finish]
needle = '视频无音频。'
assert body.count(needle) == 1
body = body.replace(needle, needle + '\n预览路径必须逐字取本次index.windows[].student_previews[].path，禁止拼接或猜测目录名、替换路径字段。以下是从index逐字提取的每窗8个有序view_file AbsolutePath参数；调用时复制对应整条AbsolutePath，不把student_previews字段名当目录：{json.dumps(literal_previews,ensure_ascii=False)}。每窗只用自己的8条，全8实际DONE后才proposal。任一tool ERROR必须立即停止如实报告，不得把ERROR视为DONE，不得宣称该窗或全部任务成功完成；最终会由真实工具审计区分CLI退出与任务完成。')
write(ROOT / 'prompt.py', "from pathlib import Path\nimport json\n\ndef read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))\n\ndef build_prompt(a):\n    fr=read(a/'freeze.json');idx=read(a/'index.json')\n    literal_previews=[dict(job_index=w['job_index'],window_id=w['window_id'],ordered_view_file_arguments=[dict(AbsolutePath=f['path']) for f in w['student_previews']]) for w in idx['windows']]\n" + '\n'.join('    ' + line for line in body.splitlines()) + '\n    return prompt,literal_previews\n')
write(ROOT / 'run_pair.py', '''from launch import ROOT,read,launch
from prompt import build_prompt
import sys
n=int(sys.argv[1]);assert n in range(6,11)
a=ROOT/f'call{n:02d}';prompt,paths=build_prompt(a)
assert prompt==(a/'frozen_prompt.txt').read_text(encoding='utf-8')
launch(a,prompt)
''')
launch = (OLD / 'launch.py').read_text(encoding='utf-8-sig')
launch = launch.replace("gate=read(ROOT/'root_start_admission.json');assert gate['status']=='ROOT_APPROVED_START_FIXED_V4' and gate['dry_run_sha256']==sha(ROOT/'dry_run_acceptance.json')", "gate=read(ROOT/'root_start_admission.json');assert gate['status']=='ROOT_APPROVED_START_FIXED_LITERAL_CLI32_36' and gate['dry_run_sha256']==sha(ROOT/'dry_run_acceptance.json') and gate['execution_binding_sha256']==sha(ROOT/'execution_code_binding.json')")
launch = launch.replace("prior=read(ROOT.parent/'capacity_v3_network/call01/terminal.json');assert prior['CLI_after']==27", "prior=read(ROOT.parent/'capacity_v4_tool_batches/call05/terminal.json');assert prior['CLI_after']==31")
launch = launch.replace("    (a/'prompt.txt').write_text(prompt,encoding='utf-8')", "    assert sha(a/'frozen_prompt.txt')==fr['frozen_prompt_sha256'] and prompt==(a/'frozen_prompt.txt').read_text(encoding='utf-8')\n    with (a/'prompt.txt').open('x',encoding='utf-8',newline='') as output:output.write(prompt)")
launch = launch.replace("task='capacity_v4_tool_batches/'+a.name", "task='remaining_CLI32_36_literal_paths_v1/'+a.name")
launch = launch.replace("conversation_id=conversation,CLI_before", "root_start_admission_sha256=sha(ROOT/'root_start_admission.json'),literal_preview_argument_receipt_sha256=sha(a/'literal_preview_arguments.json'),conversation_id=conversation,CLI_before")
write(ROOT / 'launch.py', launch)

# New audit distinguishes ERROR terminal tools from still ACTIVE tools and rejects both.
audit = (OLD / 'audit_pair.py').read_text(encoding='utf-8-sig')
needle = "    unfinished_attempts=[s for s in all_tool_updates if s.get('state')=='ACTIVE' and s.get('step_index') not in done_step_ids]"
assert audit.count(needle) == 1
audit = audit.replace(needle, """    last_tool_updates={s.get('step_index'):s for s in all_tool_updates}
    errored_attempts=[s for s in last_tool_updates.values() if s.get('state')=='ERROR']
    unfinished_attempts=[s for s in last_tool_updates.values() if s.get('state')=='ACTIVE']
    def owner_job(path):
        for w in idx['windows']:
            if path.startswith(key(Path(w['clip_path']).parent)+'\\\\') or path.startswith(key(Path(w['clip_path']).parent)+'/'):
                return w['job_index']
        return None
    allowed_reads={key(p) for p in fr['read_whitelist']}|{key(p) for p in fr['self_read_whitelist']}
    for s in errored_attempts:
        p=s.get('tool_info',{}).get('parameters',{});path=key(p.get('AbsolutePath') or p.get('TargetFile'))
        issues.append(dict(reason='TOOL_ERROR_TERMINAL',step=s.get('step_index'),tool=s.get('tool_name'),path=path,job_index=owner_job(path)))
    for s in all_tool_updates:
        if s.get('state')!='ACTIVE' or s.get('tool_name')!='view_file':continue
        p=s.get('tool_info',{}).get('parameters',{});path=key(p.get('AbsolutePath'))
        if path not in allowed_reads:issues.append(dict(reason='OUTSIDE_READ_WHITELIST_ATTEMPT',step=s.get('step_index'),path=path,job_index=owner_job(path)))""")
audit = audit.replace("global_disallowed=[i for i in issues if i['reason'] not in ('SUPPLY_ORDER_BARRIER_OR_WHITELIST',)]", "global_disallowed=[i for i in issues if i['reason'] not in ('SUPPLY_ORDER_BARRIER_OR_WHITELIST',) and i.get('job_index') in (None,w['job_index'])]")
audit = audit.replace("self_reads=selfcounts,unfinished_tool_attempts=unfinished_attempts", "self_reads=selfcounts,errored_tool_attempts=errored_attempts,unfinished_tool_attempts=unfinished_attempts,teacher_task_completed=(not issues and not errored_attempts and not unfinished_attempts and all(w['status']=='PASS_TOOL_STRUCTURE_PENDING_SEMANTIC_REVIEW' for w in wins)),AGY_result_SUCCESS_does_not_override_missing_or_ERROR_tools=True")
write(ROOT / 'audit_pair.py', audit)
for name in ('audit_completed_window.py', 'progress.py'):
    write(ROOT / name, (OLD / name).read_text(encoding='utf-8-sig'))

controller = (BASE / 'fresh_continuation_after_CLI30_v1/run.py').read_text(encoding='utf-8-sig')
controller = controller.replace("OWN = Path(__file__).resolve().parent\nBASE = OWN.parent\nROOT = BASE / 'capacity_v4_tool_batches'", "OWN = Path(__file__).resolve().parent\nBASE = OWN.parent\nROOT = OWN")
start = controller.index("binding_path = OWN / 'binding.json'")
end = controller.index('\n\ndef snapshot24', start)
controller = controller[:start] + '''gate=read(ROOT/'root_start_admission.json')
assert gate['status']=='ROOT_APPROVED_START_FIXED_LITERAL_CLI32_36'
assert gate['dry_run_sha256']==sha(ROOT/'dry_run_acceptance.json') and gate['execution_binding_sha256']==sha(ROOT/'execution_code_binding.json')
assert max(json.loads(line)['global_count'] for line in (BASE/'global_CLI_ledger.jsonl').read_text(encoding='utf-8').splitlines() if line.strip())==31
for number in range(6,11):
    call=ROOT/f'call{number:02d}';fr=read(call/'freeze.json')
    assert not (call/'request.json').exists() and fr['CLI_after']==26+number and fr['timeout_seconds']==7200
    for path,digest in fr['inputs'].items():assert sha(Path(path))==digest
save(OWN/'registered.json',dict(utc=datetime.now(timezone.utc).isoformat(),runner_pid=os.getpid(),runner_command=sys.orig_argv,runner_source_sha256=sha(Path(__file__)),root_start_admission_sha256=sha(ROOT/'root_start_admission.json'),fixed_calls=list(range(6,11)),fixed_jobs=list(range(14,24)),CLI_numbers=list(range(32,37)),global_cap=36,automatic_retry=False,cash_cost='UNKNOWN_NOT_ZERO'))
''' + controller[end:]
controller = controller.replace("previous = read(ROOT / 'full_denominator24_after_CLI30.json')", "previous = read(BASE / 'fresh_continuation_after_CLI30_v1/full_denominator24_after_CLI31.json')")
controller = controller.replace("ROOT / 'full_denominator24_after_CLI30.json'", "BASE / 'fresh_continuation_after_CLI30_v1/full_denominator24_after_CLI31.json'")
controller = controller.replace('range(5, 11)', 'range(6, 11)').replace('COMPLETE_FIXED12_FRESH_STRUCTURES', 'COMPLETE_FIXED10_FRESH_STRUCTURES').replace('fresh_windows=12', 'fresh_windows=10')
controller = controller.replace("failed_job11_not_retried=True", "failed_job13_not_retried=True")
controller = controller.replace("if audit.get('actual_result_status') != 'SUCCESS' or audit.get('error_message_steps'):", "if audit.get('actual_result_status') != 'SUCCESS' or audit.get('error_message_steps') or audit.get('errored_tool_attempts') or audit.get('unfinished_tool_attempts'):")
write(ROOT / 'controller.py', controller)

observer = (BASE / 'observe_fresh_after_CLI30_receipts.py').read_text(encoding='utf-8-sig')
observer = observer.replace("ROOT = BASE / 'capacity_v4_tool_batches'\nSTOPROOT = BASE / 'fresh_continuation_after_CLI30_v1'", "ROOT = BASE / 'remaining_CLI32_36_literal_paths_v1'\nSTOPROOT = ROOT")
observer = observer.replace('range(5, 11)', 'range(6, 11)')
write(ROOT / 'observe_receipts.py', observer.replace("BASE = Path(__file__).resolve().parent", "BASE = Path(__file__).resolve().parent.parent"))

ledger = BASE / 'global_CLI_ledger.jsonl'
assert max(json.loads(line)['global_count'] for line in ledger.read_text(encoding='utf-8').splitlines() if line.strip()) == 31
prefix = ROOT / 'global_CLI31_ledger_prefix.jsonl'
with prefix.open('xb') as output:
    output.write(ledger.read_bytes())
preserved = [Path(__file__), prefix, BASE / 'readonly_protocol_composed_media_inquiry_CLI31.json', BASE / 'fresh_continuation_after_CLI30_v1/run.py', BASE / 'fresh_continuation_after_CLI30_v1/registered.json', BASE / 'fresh_continuation_after_CLI30_v1/stopped.json', BASE / 'fresh_continuation_after_CLI30_v1/full_denominator24_after_CLI31.json', OLD / 'call05/terminal.json', OLD / 'call05/stream.jsonl', OLD / 'call05/audit.json', OLD / 'call05/engineering_wrong_preview_paths_CLI31.json', OLD / 'call05/actual_partial_terminal_receipt.json', OLD / 'call05/w12_completed_scope_audit.json', OLD / 'call05/w12_proposal.json']
runtime = {str(path): sha(path) for path in ROOT.glob('*.py')}
runtime[str(ROOT / 'PROTOCOL.md')] = sha(ROOT / 'PROTOCOL.md')
execution = ROOT / 'execution_code_binding.json'
save(execution, dict(utc=datetime.now(timezone.utc).isoformat(), sources=runtime, prior_failure_inputs={str(path): sha(path) for path in preserved}, new_model_calls=0, requires_root_start_admission=True))
runtime[str(execution)] = sha(execution)
calls = []
from importlib.util import spec_from_file_location, module_from_spec
spec = spec_from_file_location('literal_preview_prompt_preparation', ROOT / 'prompt.py')
module = module_from_spec(spec)
spec.loader.exec_module(module)
for number in range(6, 11):
    old = OLD / f'call{number:02d}'
    old_freeze = read(old / 'freeze.json')
    assert not (old / 'request.json').exists()
    for path, digest in old_freeze['inputs'].items():
        assert sha(Path(path)) == digest
    assert not any(Path(path).exists() for path in old_freeze['write_whitelist'])
    dest = ROOT / f'call{number:02d}'
    dest.mkdir()
    with (dest / 'index.json').open('xb') as output:
        output.write((old / 'index.json').read_bytes())
    assert sha(dest / 'index.json') == sha(old / 'index.json')
    inputs = dict(old_freeze['inputs'])
    inputs.update(runtime)
    inputs.update({str(path): sha(path) for path in [old / 'index.json', old / 'freeze.json', dest / 'index.json', *preserved]})
    reads = [str(dest / 'index.json') if Path(path) == old / 'index.json' else path for path in old_freeze['read_whitelist']]
    assert reads[0] == str(dest / 'index.json')
    freeze = dict(utc=datetime.now(timezone.utc).isoformat(), inputs=inputs, read_whitelist=reads, self_read_whitelist=old_freeze['self_read_whitelist'], write_whitelist=old_freeze['write_whitelist'], protocol_sha256=sha(ROOT / 'PROTOCOL.md'), parent_protocol_sha256=sha(BASE / 'PROTOCOL.md'), fixed_job_indices=old_freeze['fixed_job_indices'], CLI_before=old_freeze['CLI_before'], CLI_after=old_freeze['CLI_after'], global_cap=36, timeout_seconds=7200, automatic_retry=False, original_index_byte_exact=True, original_output_paths_preserved=True, source_index=dict(path=str(old / 'index.json'), sha256=sha(old / 'index.json')), execution_binding_sha256=sha(execution))
    # Prompt rendering needs only the whitelist, not the final prompt SHA binding.
    save(dest / 'freeze_render_inputs.json', freeze)
    module.read_original = module.read
    module.read = lambda path, m=module: read(dest / 'freeze_render_inputs.json') if Path(path).name == 'freeze.json' else m.read_original(path)
    prompt, literals = module.build_prompt(dest)
    module.read = module.read_original
    write(dest / 'frozen_prompt.txt', prompt)
    for window, literal in zip(read(dest / 'index.json')['windows'], literals):
        assert [item['AbsolutePath'] for item in literal['ordered_view_file_arguments']] == [item['path'] for item in window['student_previews']]
        assert len(literal['ordered_view_file_arguments']) == 8
    save(dest / 'literal_preview_arguments.json', dict(utc=datetime.now(timezone.utc).isoformat(), source_index_sha256=sha(dest / 'index.json'), windows=literals, paths_are_exact_index_values=True, path_construction_or_directory_guessing=False))
    inputs[str(dest / 'frozen_prompt.txt')] = sha(dest / 'frozen_prompt.txt')
    inputs[str(dest / 'literal_preview_arguments.json')] = sha(dest / 'literal_preview_arguments.json')
    freeze['frozen_prompt_sha256'] = sha(dest / 'frozen_prompt.txt')
    save(dest / 'freeze.json', freeze)
    actual_prompt, actual_literals = module.build_prompt(dest)
    assert actual_prompt == prompt and actual_literals == literals
    calls.append(dict(call=number, jobs=freeze['fixed_job_indices'], CLI_after=freeze['CLI_after'], input_count=len(inputs), old_index_sha256=sha(old / 'index.json'), new_index_sha256=sha(dest / 'index.json'), literal_preview_arguments_sha256=sha(dest / 'literal_preview_arguments.json'), prompt_sha256=sha(dest / 'frozen_prompt.txt'), freeze_sha256=sha(dest / 'freeze.json'), all_old_inputs_SHA_verified=True))
ast_checks = []
for path in ROOT.glob('*.py'):
    ast.parse(path.read_text(encoding='utf-8-sig'))
    ast_checks.append(dict(path=str(path), sha256=sha(path), AST_PASS=True))
save(ROOT / 'plan.json', dict(utc=datetime.now(timezone.utc).isoformat(), fixed_calls=list(range(6, 11)), fixed_jobs=list(range(14, 24)), CLI_numbers=list(range(32, 37)), calls=calls, global_cap=36, model='gemini-3.8-flash-high', failed_job13_not_retried=True, new_model_calls=0, requires_separate_root_start_authorization=True))
receipt = ROOT / 'dry_run_acceptance.json'
save(receipt, dict(utc=datetime.now(timezone.utc).isoformat(), status='PASS_AST_ACTUAL_SHA_LITERAL_PATHS_PREPARED_NO_MODEL_PENDING_ROOT_START', AST=ast_checks, calls=calls, all_original_indices_byte_exact=True, all_original_outputs_paths_preserved=True, original_media_and_frozen_inputs_unchanged=True, exact_eight_AbsolutePath_arguments_per_window=True, explicit_ERROR_tools_reject_task_completion=True, old_failed_or_successful_audits_not_modified=True, fixed_denominator=24, teacher_expansion_denominator=21, actual_student_frames=64, timeout_seconds=7200, model='gemini-3.8-flash-high', global_cap=36, new_model_calls=0, new_decode=0, new_optimizer_updates=0, new_426=0, execution_binding_sha256=sha(execution), requires_root_start_admission=True, cash_cost='UNKNOWN_NOT_ZERO'))
print(json.dumps(dict(root=str(ROOT), controller_sha256=sha(ROOT / 'controller.py'), launch_sha256=sha(ROOT / 'launch.py'), prompt_source_sha256=sha(ROOT / 'prompt.py'), execution_binding_sha256=sha(execution), dry_run_sha256=sha(receipt), new_model_calls=0), ensure_ascii=False))
