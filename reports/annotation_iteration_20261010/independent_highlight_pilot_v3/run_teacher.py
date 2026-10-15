"""One new independent proposal through existing AGY CLI; no automatic retry."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,os,time
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)

def main():
    packet=HERE/'teacher_packet.json';m=json.loads(packet.read_text());out=HERE/'teacher_attempt01/proposal.json';attempt=out.parent
    if (attempt/'request.json').exists():raise ValueError('do not repeat a registered attempt')
    originals='\n'.join(r['frame_id']+' '+Path(r['path']).as_posix() for r in m['original_frames'])
    effective='\n'.join(r['frame_id']+' '+Path(r['path']).as_posix() for r in m['effective_frames'])
    prompt=f'''用户授权新独立短高光编辑初判。严格白名单只有 {packet.as_posix()}、{Path(m['clip_path']).as_posix()}、下列64个原图及8个有效图、唯一输出 {out.as_posix()}。禁止任何旧标签/人工评分/预测/其他评审/其他目录；禁止terminal/代码/联网/其他模型/子代理。只用view_file、write_to_file，不修改旧文件。
先读取packet完整frames/PTS元数据（最多4段）；只读取一次指定native clip，记录实际工具观察范围/内部采样不透明，不称全原生帧已观察。再按F00..F63逐张view_file 64PNG，不能用接触表代替；最后逐张8个实际学生视图。读取不完整、工具失败都如实记录，不自行重试，不编造。
任务：{m['task']}
所有取舍与边界是有限观察下编辑建议，不冒充gold。其余空隙不自动NO，具体且影响取舍的疑问保留UNKNOWN；一般未采样风险放limitations。不得把静态/模糊/相同主体机械判NO；不得以动作或字幕丰富机械KEEP。无需凑事件或区间数、保留比例或正负配额。必要准备/结果只解释突出内容，不为叙事完整保留大段无贡献素材。不能猜音频/动机/未见动作。clip本地时间需加offset {m['clip_pts_offset_exact']}。
输出JSON：window_id={m['window_id']}、source_sha256={m['source_sha256']}、clip_sha256={m['clip_sha256']}、model、native_video_actual_scope、full_native_frames_observed(false)、frame_observations(64条F00..F63,frame_id/source_ordinal/local_seconds_exact/observed/visible_fact)、effective_view_observations(8条同样字段)、window_coverage(完整互斥半开[0,30)区间：start/end字符串、label KEEP/NO/UNKNOWN、visible_basis、editorial_reason、evidence_frame_ids)、events(全部保留单元：event_id/visible_facts/highlight_reason/evidence_frame_ids/proposed_local_seconds/start_uncertainty_range/end_uncertainty_range/boundary_inside_frame_ids/boundary_outside_frame_ids/limitations)、consequential_unknowns、explicit_no_highlight、student_visibility_limitations、limitations、training_admitted(false)、blind_attestation(旧答案/分数/预测是否接收)。失败也保留具体缺口，不写空segments冒充成功。只写唯一proposal.json，禁止其他写入。
64原图：
{originals}
8学生有效图：
{effective}'''
    (attempt/'prompt.txt').write_text(prompt,encoding='utf-8')
    cmd=['C:/Users/33056/AppData/Local/agy/bin/agy.exe','--model','gemini-3.8-flash-high','--mode','accept-edits','--sandbox','--print-timeout','10m','--output-format','stream-json','--log-file',str(attempt/'agy.log'),'-p',prompt]
    save(attempt/'request.json',dict(started_utc=datetime.now(timezone.utc).isoformat(),packet_sha256=sha(packet),protocol_sha256=sha(HERE/'PROTOCOL.md'),prompt_sha256=sha(attempt/'prompt.txt'),
         max_clip_reads=1,max_original_reads=64,max_effective_reads=8,model='gemini-3.8-flash-high',historical_CLI_calls=21,global_CLI_cap=36,stage_CLI_cap=2,automatic_retry=False))
    env=os.environ.copy();env.update(HTTP_PROXY='http://127.0.0.1:7892',HTTPS_PROXY='http://127.0.0.1:7892',GODEBUG='http2client=0')
    started=time.monotonic()
    with (attempt/'stream.jsonl').open('xb') as stdout,(attempt/'stderr.txt').open('xb') as stderr:
        proc=subprocess.Popen(cmd,cwd=attempt,env=env,stdout=stdout,stderr=stderr)
        save(attempt/'process.json',dict(pid=proc.pid,started_utc=datetime.now(timezone.utc).isoformat(),command=cmd[:cmd.index('-p')],only_this_owned_child=True))
        try:code=proc.wait(timeout=660);stop=None
        except subprocess.TimeoutExpired:proc.terminate();code=proc.wait(timeout=30);stop='OWNED_STAGE_TIMEOUT'
    save(attempt/'terminal.json',dict(ended_utc=datetime.now(timezone.utc).isoformat(),exit_code=code,stop_reason=stop,wall_seconds=time.monotonic()-started,stream_sha256=sha(attempt/'stream.jsonl'),
         proposal_exists=out.is_file(),cash_cost='UNKNOWN_NOT_ZERO',exit_zero_not_acceptance=True,new_optimizer_updates=0))
    print(json.dumps(dict(exit_code=code,proposal_exists=out.is_file(),stop_reason=stop)))

if __name__=='__main__':main()
