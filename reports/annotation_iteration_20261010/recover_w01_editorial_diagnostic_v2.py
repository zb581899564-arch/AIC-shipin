"""One bounded continuation of the same proposal, preserving the timed-out attempt."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, os, subprocess, time, sys
ROOT=Path(__file__).resolve().parent/'w01_editorial_diagnostic_v1'
OUT=ROOT/'teacher'
transport_retry=len(sys.argv)>1 and sys.argv[1]=='--transport-retry-once'
http2_recovery=len(sys.argv)>1 and sys.argv[1]=='--http2-proven-recovery'
assert len(sys.argv)==1 or transport_retry or http2_recovery
REC=OUT/('engineering_recovery_v4_http2' if http2_recovery else 'engineering_recovery_v3_transport_retry' if transport_retry else 'engineering_recovery_v2')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
if transport_retry or http2_recovery:
    prior=OUT/('engineering_recovery_v3_transport_retry' if http2_recovery else 'engineering_recovery_v2')
    assert json.loads((prior/'terminal.json').read_text())['exit_code']==1
    assert 'Eligibility check failed' in (prior/'stderr.txt').read_text()
    prior_rows=[json.loads(s) for s in (prior/'stream.jsonl').read_text(encoding='utf-8-sig').splitlines() if s.strip()]
    assert not any(r.get('step_update',{}).get('step_type')=='tool' for r in prior_rows)
    if http2_recovery:
        assert json.loads((OUT/'transport_probe_http2_models.json').read_text())['exit_code']==0
REC.mkdir(exist_ok=False)
rows=[json.loads(s) for s in (OUT/'stream.jsonl').read_text(encoding='utf-8-sig').splitlines() if s.strip()]
result=next(r['result'] for r in reversed(rows) if r.get('event')=='result')
conversation=result['conversation_id']
native=json.loads((ROOT/'native_index.json').read_text())['frames']
calls=[r['step_update'] for r in rows if r.get('step_update',{}).get('step_type')=='tool' and r['step_update'].get('state')=='DONE']
done=[]
for c in calls:
    if c.get('tool_name')=='view_file':
        pars=c.get('tool_info',{}).get('parameters',{})
        path=pars.get('AbsolutePath')
        done.extend(r['frame_id'] for r in native if path and Path(path).resolve()==Path(r['path']).resolve())
assert done==['F00','F01','F02','F03'],done
assert 'print timeout after 10m0s with turn in progress' in (OUT/'agy.log').read_text(encoding='utf-8-sig')
assert (OUT/'student_sealed.json').exists() and not (OUT/'native_addendum.json').exists()
before=sha(OUT/'student_sealed.json')
prompt=f'''继续同一个W01独立提案，不是第二份标注，不可改变已经封存的学生选择。上一CLI在打印时限退出，任务未完成。原始失败、费用、stream与学生原字节全部保留。
你已实际看完64学生图并写student_sealed，及原生F00..F03。禁止重复读取它们、禁止读自己输出、其他答案或任何历史标签，不新生成学生提案。仅继续下面F04..F63共60张剩余原生图逐项view_file一次，完成原注册native_addendum.json与seal.json；两者仍只在{OUT.as_posix()}新建。仍只允许view_file白名单图和write_to_file这两文件，不可terminal/代码/联网/其他模型。
native_addendum的64帧事实可引用本会话记忆F00..F03，剩余60必须实际供给；逐帧frame_id/source_ordinal/local_seconds_exact/actual_view_image_read/visible_fact/subtitle_text/subtitle_legibility，使用紧凑JSON减少输出空白但不可省字段或观察。保留原任务全窗coverage/events、具体NO理由、具体有后果U与叙事归属依据。学生图选择只比对、不得回填原图才可读出的文字。没有改变也记录依据，不追求数量目标、不自动用于训练。seal披露一次打印超时后同一conversation工程恢复、所有实际未完成项与是否意外看过其他答案/已知容量规则，SHA可写not_computed_by_teacher。若再次未完成如实结束，不第三次续跑。
剩余原生图索引（metadata已经读过，不重复）：
{json.dumps(native[4:],ensure_ascii=False,separators=(',',':'))}
'''
(REC/'prompt.txt').write_text(prompt,encoding='utf-8')
save(REC/'request.json',dict(utc=datetime.now(timezone.utc).isoformat(),conversation_id=conversation,
    status='ONE_ENGINEERING_RECOVERY_OF_SAME_PROPOSAL_NOT_NEW_SCIENTIFIC_RECIPE',
    prior_preregistration_sha256=sha(ROOT/'preregistration.json'),prior_stream_sha256=sha(OUT/'stream.jsonl'),
    prior_terminal_sha256=sha(OUT/'terminal.json'),prior_audit_v2_sha256=sha(OUT/'audit_v2.json'),
    deviation='Original preregistered max_new_agy_sessions=1 is not met: a second CLI session resumes the exact same incomplete proposal; original failure remains invalid as complete run',
    original_scientific_criteria_unchanged=True,max_additional_sessions=1,max_additional_seconds=600,
    transport_retry_once=transport_retry,
    prior_transport_failure_no_tools=transport_retry,
    process_only_http2_enabled_after_read_only_probe=http2_recovery,
    completed_student_reads_not_repeated=64,completed_native_reads_not_repeated=4,remaining_native_reads=60,
    student_sha256_before=before,prompt_sha256=sha(REC/'prompt.txt'),new_teacher_proposals=0,
    automatic_training=False,new_optimizer_updates=0,new_426_calls=0,cash_cost='UNKNOWN_NOT_ZERO'))
env=os.environ.copy();env.update(HTTP_PROXY='http://127.0.0.1:7892',HTTPS_PROXY='http://127.0.0.1:7892',GODEBUG='http2client=0')
if http2_recovery:env['GODEBUG']='http2client=1'
cmd=['C:/Users/33056/AppData/Local/agy/bin/agy.exe','--conversation',conversation,'--model','gemini-3.8-flash-high',
    '--mode','accept-edits','--sandbox','--print-timeout','10m','--output-format','stream-json','--log-file',str(REC/'agy.log'),'-p',prompt]
tic=time.monotonic();start=datetime.now(timezone.utc).isoformat()
with (REC/'stream.jsonl').open('xb') as stdout,(REC/'stderr.txt').open('xb') as stderr:
    p=subprocess.run(cmd,cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
save(REC/'terminal.json',dict(started_utc=start,finished_utc=datetime.now(timezone.utc).isoformat(),exit_code=p.returncode,
    elapsed_seconds=time.monotonic()-tic,exit_zero_not_completion=True,student_sha256_after=sha(OUT/'student_sealed.json'),
    student_seal_bytes_unchanged=before==sha(OUT/'student_sealed.json'),
    output_files={n:dict(bytes=(OUT/n).stat().st_size,sha256=sha(OUT/n)) for n in ('native_addendum.json','seal.json') if (OUT/n).exists()},
    new_optimizer_updates=0,new_426_calls=0,cash_cost='UNKNOWN_NOT_ZERO'))
print(json.dumps({'exit_code':p.returncode,'student_unchanged':before==sha(OUT/'student_sealed.json')},ensure_ascii=False))
