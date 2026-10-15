from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,copy,ast
BASE=Path(__file__).resolve().parent;OLD=BASE/'capacity_v3_network';ROOT=BASE/'capacity_v4_tool_batches'
AUTH=BASE.parent/'teacher_dispatch_capacity_v4_authorization.json'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def write(p,s):
    with Path(p).open('x',encoding='utf-8',newline='') as f:f.write(s)
auth=read(AUTH);assert auth['affected_job_indices']==list(range(6,24)) and auth['global_CLI_numbers']==list(range(28,37)) and auth['timeout_seconds_per_fresh_pair']==7200 and auth['automatic_retry'] is False
evidence=Path(auth['evidence']['path']);assert sha(evidence)==auth['evidence']['sha256']
ROOT.mkdir(exist_ok=False)
write(ROOT/'PROTOCOL.md','''# 固定 fresh 双窗工具批次容量协议 v4

仅前瞻替换尚未执行的 jobs6..23，固定九对 CLI28..36，每对新独立会话7200秒，无自动重试。绑定根主控 teacher_dispatch_capacity_v4_authorization.json 及真实既有 batch stream 证据SHA。当前v3 call01、历史25/75分钟失败、所有冻结/原始输出/费用UNKNOWN保持；未完成HT5 W10不补空、不恢复重问；已完成W02独立证据保持。新授权只涉及工程容量及工具提交粒度，科学协议和准入门不变。

每窗64原始PNG、16组，每组按slot0..3在同一次 agent_response 提交4个独立view_file工具调用；客户端可顺序执行，不能声称工具并发。等待4图实际DONE后立即一次write_to_file本组4条静态事实，之后才可下一组。每图只能读一次，每事实只参考对应单图；subject/composition/subtitle presence+literal/中文visible_fact，身份由程序绑定。不从单帧猜动作、心理、动机或字幕语言。事实成功输出不可覆盖。16组全部封存才读本窗clip一次；随后按冻结顺序同一response提交8个effective student preview独立view_file，全8DONE后才写完整proposal。实际学生native processor64帧，教师只8预览。保持原geometry/RGB/source/domain/PTS/SHA，成功媒体不重新decode。

proposal保持完整连续KEEP/NO/UNKNOWN、独立事件、全部NO理由、事实support、边界不确定range和limitations。短高光包含完整亮点，不把whole-window叙事/持续说话/常态或重复状态/字幕内容自动当高光，不设事件数量配额；真实UNKNOWN/空events合法，不用失败转空。各窗证据独立，禁止旧标签、预测、分数或其他评审。只允许view_file/write_to_file，禁止terminal/code/web/search/其他模型/subagent。已写指定自身输出最多一次写后核对，不得写前读或覆盖。

启动前冻结全部输入、输出/读取白名单、模型gemini-3.8-flash-high、授权/证据、执行代码和prompt模板SHA。独立实核actual工具顺序、4-image barrier、clip+8preview、结构覆盖/identity+geometry、真实终态/rawSHA/账本，错误保存，不自动重试。历史真实batch只证明同response多工具能力，不保证本次时间或语义质量。九对固定顺序，不基于semantic挑窗；根审核无模型dry-run后另发启动消息才注册CLI。结构PASS不是semantic正确/human gold/训练准入，仍需root和独立学生审阅。现金UNKNOWN；本任务新GPU/Qwen/decoder/optimizer/训练/426/100confirm均0。
''')
for name in ('launch.py','run_pair.py','audit_pair.py','admission.py','audit_completed_window.py','progress.py'):
    s=(OLD/name).read_text(encoding='utf-8-sig')
    if name=='launch.py':
        s=s.replace("'--print-timeout','75m'","'--print-timeout','120m'")
        s=s.replace("task='capacity_v2/'+a.name","task='capacity_v4_tool_batches/'+a.name")
        s=s.replace("    fr=read(a/'freeze.json');", "    gate=read(ROOT/'root_start_admission.json');assert gate['status']=='ROOT_APPROVED_START_FIXED_V4' and gate['dry_run_sha256']==sha(ROOT/'dry_run_acceptance.json')\n    prior=read(ROOT.parent/'capacity_v3_network/call01/terminal.json');assert prior['CLI_after']==27\n    counts=[json.loads(s)['global_count'] for s in (ROOT.parent/'global_CLI_ledger.jsonl').read_text(encoding='utf-8').splitlines() if s.strip()]\n    fr=read(a/'freeze.json');assert max(counts)==fr['CLI_before'];")
    if name=='run_pair.py':
        s=s.replace('每次会话75分钟cap','每次会话120分钟cap')
        s=s.replace("assert n in range(1,11)","assert n in range(2,11)")
        s=s.replace("if n>1:assert (ROOT/f'call{n-1:02d}'/'terminal.json').exists()", "if n>2:assert (ROOT/f'call{n-1:02d}'/'terminal.json').exists()")
        s=s.replace('每窗按groups0..15、slot0..3逐张读4原PNG（每图一次），立即write_to_file该group output_path再下一组。','每窗按groups0..15固定顺序；每组必须在同一次 agent_response 提交slot0..3顺序的4个独立view_file工具调用（不是只描述计划），每图一次，工具可顺序执行。全4幅工具实际DONE后，下一次响应立即write_to_file该group output_path，然后才下一组。不可在四图之间逐图等待新agent_response，不可把write提前到未全DONE；不得跨组批量读取。')
        s=s.replace('再按student_previews顺序读8effective图一次。','再在同一次 agent_response 按student_previews固定顺序提交8个独立view_file工具调用（每图一次，工具可顺序执行），全部8图实际DONE后才写proposal。')
    write(ROOT/name,s)
write(ROOT/'controller.py','''from pathlib import Path
from datetime import datetime,timezone
import json,sys,subprocess,hashlib
ROOT=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
gate=read(ROOT/'root_start_admission.json');assert gate['status']=='ROOT_APPROVED_START_FIXED_V4' and gate['dry_run_sha256']==sha(ROOT/'dry_run_acceptance.json')
save(ROOT/'controller_registered.json',dict(utc=datetime.now(timezone.utc).isoformat(),fixed_calls=list(range(2,11)),root_start_admission_sha256=sha(ROOT/'root_start_admission.json'),automatic_retry=False,global_final_cap=36))
for n in range(2,11):
    a=ROOT/f'call{n:02d}';assert not (a/'request.json').exists(),'No repeat model CLI'
    subprocess.run([sys.executable,str(ROOT/'run_pair.py'),str(n)],cwd=ROOT,check=True)
    subprocess.run([sys.executable,str(ROOT/'audit_pair.py'),str(n)],cwd=ROOT,check=True)
    au=read(a/'audit.json');t=read(a/'terminal.json')
    save(ROOT/f"status_after_CLI{t['CLI_after']:02d}.json",dict(utc=datetime.now(timezone.utc).isoformat(),CLI_after=t['CLI_after'],audit_path=str(a/'audit.json'),audit_sha256=sha(a/'audit.json'),terminal_sha256=sha(a/'terminal.json'),raw_sha256=sha(a/'stream.jsonl'),windows=au['windows'],cash_cost='UNKNOWN_NOT_ZERO',training_admitted=False))
    print(json.dumps(dict(event='CALL_TERMINAL_AUDITED',call=n,global_CLI_calls=t['CLI_after'],window_statuses=[dict(job_index=w['job_index'],status=w['status']) for w in au['windows']],terminal_sha256=sha(a/'terminal.json'),raw_sha256=sha(a/'stream.jsonl')),ensure_ascii=False),flush=True)
    if t['exit_code']!=0 or au['tool_issues'] or any(w['schema_issues'] or w['proposal_issues'] for w in au['windows']):
        save(ROOT/'controller_stopped.json',dict(utc=datetime.now(timezone.utc).isoformat(),after_call=n,reason='ENGINEERING_OR_SCHEMA_FAILURE_NO_AUTOMATIC_RETRY',pending_calls=list(range(n+1,11))));sys.exit(2)
    if au.get('actual_result_status')!='SUCCESS' or au.get('error_message_steps'):
        save(ROOT/'controller_awaiting_root.json',dict(utc=datetime.now(timezone.utc).isoformat(),after_call=n,reason='COMPLETE_WORK_WITH_REAL_ERROR_REQUIRES_ROOT_REVIEW',pending_calls=list(range(n+1,11))));sys.exit(3)
save(ROOT/'completion.json',dict(utc=datetime.now(timezone.utc).isoformat(),status='COMPLETE_18_FRESH_TOOL_STRUCTURES_PENDING_SEMANTIC_REVIEW',fixed_fresh_denominator=18,total_reference_denominator=21,global_CLI_calls=36,training_admitted=False,cash_cost='UNKNOWN_NOT_ZERO',new_optimizer_updates=0,new_426=0))
''')
runtime={str(p):sha(p) for p in ROOT.glob('*.py')};runtime[str(ROOT/'PROTOCOL.md')]=sha(ROOT/'PROTOCOL.md')
save(ROOT/'execution_code_binding_v1.json',dict(utc=datetime.now(timezone.utc).isoformat(),sources=runtime,authorization={'path':str(AUTH),'sha256':sha(AUTH)},evidence={'path':str(evidence),'sha256':sha(evidence)},new_model_calls=0))
static=[Path(f['path']) for f in read(evidence)['files'] if 'native_block_00' in f['path'] or 'independent_highlight_pilot_v3' in f['path']]
calls=[]
for n in range(2,11):
    old=OLD/f'call{n:02d}';assert not (old/'request.json').exists();dest=ROOT/f'call{n:02d}';dest.mkdir()
    original=read(old/'index.json');idx=copy.deepcopy(original);writes=[];reads=[str(dest/'index.json')];inp=dict(runtime)
    for w in idx['windows']:
        for g in w['groups']:
            g['output_path']=str(dest/f'w{w["job_index"]:02d}_group{g["group"]:02d}.json');writes.append(g['output_path'])
            for f in g['frames']:assert sha(f['path'])==f['png_sha256'];inp[f['path']]=f['png_sha256'];reads.append(f['path'])
        reads.append(w['clip_path']);inp[w['clip_path']]=sha(w['clip_path'])
        for f in w['student_previews']:assert sha(f['path'])==f['png_sha256'];inp[f['path']]=f['png_sha256'];reads.append(f['path'])
        w['proposal_path']=str(dest/f'w{w["job_index"]:02d}_proposal.json');writes.append(w['proposal_path'])
    save(dest/'index.json',idx);inp[str(dest/'index.json')]=sha(dest/'index.json')
    for p in [AUTH,evidence,ROOT/'execution_code_binding_v1.json',old/'index.json',old/'freeze.json',*static]:inp[str(p)]=sha(p)
    save(dest/'freeze.json',dict(utc=datetime.now(timezone.utc).isoformat(),inputs=inp,read_whitelist=reads,self_read_whitelist=writes,write_whitelist=writes,protocol_sha256=sha(ROOT/'PROTOCOL.md'),parent_protocol_sha256=sha(BASE/'PROTOCOL.md'),fixed_job_indices=[w['job_index'] for w in idx['windows']],CLI_before=25+n,CLI_after=26+n,global_cap=36,timeout_seconds=7200,automatic_retry=False,source_index={'path':str(old/'index.json'),'sha256':sha(old/'index.json')},execution_code_binding_sha256=sha(ROOT/'execution_code_binding_v1.json')))
    restored=copy.deepcopy(idx)
    for nw,ow in zip(restored['windows'],original['windows']):
        nw['proposal_path']=ow['proposal_path']
        for ng,og in zip(nw['groups'],ow['groups']):ng['output_path']=og['output_path']
    assert restored==original,'Only output paths may differ'
    calls.append(dict(call=n,job_indices=[w['job_index'] for w in idx['windows']],path=str(dest),freeze_sha256=sha(dest/'freeze.json'),byte_exact_input_identity=True))
save(ROOT/'plan.json',dict(utc=datetime.now(timezone.utc).isoformat(),fresh_windows=18,total_denominator=21,calls=calls,CLI_numbers=list(range(28,37)),max_after=36,parent_authorization_sha256=sha(AUTH),current_v3_call01_unchanged=True,model='gemini-3.8-flash-high',new_model_calls=0,training_admitted=False))
ast_checks=[]
for p in ROOT.glob('*.py'):ast.parse(p.read_text(encoding='utf-8-sig'));ast_checks.append(dict(path=str(p),sha256=sha(p),AST_PASS=True))
all_inputs=sum(len(read(Path(c['path'])/'freeze.json')['inputs']) for c in calls)
save(ROOT/'dry_run_acceptance.json',dict(utc=datetime.now(timezone.utc).isoformat(),status='PASS_IMPLEMENTATION_AST_CPU_SHA_NO_MODEL_PENDING_ROOT_LAUNCH',AST=ast_checks,fresh_calls=9,fresh_windows=18,fixed_job_indices=list(range(6,24)),CLI_numbers=list(range(28,37)),timeout_seconds=7200,all_frozen_input_SHA_verified=True,input_bindings=all_inputs,source_indices_restored_equal=True,only_output_paths_changed=True,native_PNG_per_window=64,groups_per_window=16,student_preview_per_window=8,actual_student_frames=64,group_dispatch='one agent_response / 4 ordered tools / all DONE / immediate fact write',preview_dispatch='one agent_response / 8 ordered tools / all DONE / proposal',serial_tools_not_concurrent=True,model='gemini-3.8-flash-high',authorization_sha256=sha(AUTH),batch_evidence_sha256=sha(evidence),execution_code_binding_sha256=sha(ROOT/'execution_code_binding_v1.json'),new_model_calls=0,new_optimizer_updates=0,new_decode=0,new_426=0,existing_v3_inputs_and_source_files_not_written=True,current_call01_timeout_unchanged=4500,requires_root_start_admission=True,cash_cost='UNKNOWN_NOT_ZERO'))
print(json.dumps(dict(root=str(ROOT),dry_run_sha256=sha(ROOT/'dry_run_acceptance.json'),fresh_calls=9,all_AST_SHA_input_identity_PASS=True,new_model_calls=0),ensure_ascii=False))
