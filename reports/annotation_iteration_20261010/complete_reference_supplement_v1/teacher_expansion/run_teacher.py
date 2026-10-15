from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,os,subprocess,time,sys
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,v):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def run(no):
    a=ROOT/f'call{no:02d}';freeze=read(a/'freeze.json');idx=read(a/'index.json')
    assert sha(ROOT/'PROTOCOL.md')==freeze['protocol_sha256'] and sha(ROOT.parent/'PROTOCOL.md')==freeze['parent_protocol_sha256']
    for p,s in freeze['inputs'].items():assert sha(p)==s,(p,'SHA drift')
    assert not (a/'request.json').exists() and not any(Path(p).exists() for p in freeze['write_whitelist'])
    if no:assert (ROOT/f'call{no-1:02d}'/'terminal.json').exists(),'fixed sequential calls only'
    prompt=f'''你是独立有限媒体观察教师。严格只用view_file/write_to_file；禁止terminal、执行代码、web、目录搜索、旧答案/分数/预测/其他评审、其他模型/子代理。先读 { (a/'index.json').as_posix() } 一次，完整索引中仅本次指定窗与媒体/输出在白名单，manifest/receipt/protocol/freeze都禁止读取。
严格依index windows顺序，但任何事实或语义只用当前窗，不能用另一窗补证据。每窗依groups0..15，每组按slot0..3逐张view_file四张原PNG，每图一次，立即write_to_file该group的output_path后再读下一组。每组输出严格JSON {{"group":整数,"items":[4条]}}，每条严格字段slot(0..3)、subject(中文可见主体或UNKNOWN)、composition(中文静态构图或UNKNOWN)、subtitle_visible(true/false/"UNKNOWN")、subtitle_text(清楚可见原文；无字幕null；辨不清"UNKNOWN")、visible_fact(中文当前单图静态事实)。不得输出frame_id/ordinal/PTS/SHA等身份；身份由外部程序按slot绑定。不要用邻图补主体、字幕、构图；不要由单图推断动作、心理/动机/字幕语言，字幕逐图判断presence和literal。
每窗64条facts全部写出封存后才读该窗clip_path一次，再依student_previews顺序读8张实际effective图片一次。学生真实native processor有64有效输入，8只是教师预览，不可声称只8学生输入。视频无音频，不能推断声音。不要以字幕内容自动推断高光或以全窗叙事作为单个事件。
随后write_to_file该窗proposal_path一次，完整JSON字段为：segments、events、student_visibility、limitations。segments要按local seconds从0到domain末尾完整连续覆盖，每段字段decision(KEEP/NO/UNKNOWN)、start_seconds、end_seconds、reason(具体可见理由，全部NO逐段明确)、fact_support(对应group/slot列表)、start_uncertainty_range_seconds([lower,upper])、end_uncertainty_range_seconds([lower,upper])。只选择有明显短时可见亮点的完整短高光，事件独立判断，不强行拼全窗；平常背景/持续说话/重复状态不自动KEEP。边界可见不足用真实range或UNKNOWN，不编造精确硬切。events字段每项description、decision、start_seconds、end_seconds、fact_support、boundary_reason。student_visibility说明8预览实际可辨认支持与不能确认的内容，不冒充64学生图片逐张复核。limitations说明不确定项。无事件也可以空events，不能靠配额补造。禁止自报训练准入或human gold。
每个已经成功写出的自身指定output允许view_file核对一次（不用也可）；写前不能读，不覆盖/修订成功输出。工具失败立即停止并如实报告，不能重试、猜测填缺图、失败转空。该窗口proposal写出后才开始下一窗。全部完成自然停止。
本次读取白名单：{json.dumps(freeze['read_whitelist'],ensure_ascii=False)}
本次自身已写核对白名单/写白名单：{json.dumps(freeze['write_whitelist'],ensure_ascii=False)}'''
    (a/'prompt.txt').write_text(prompt,encoding='utf-8')
    cmd=['C:/Users/33056/AppData/Local/agy/bin/agy.exe','--model','gemini-3.8-flash-high','--mode','accept-edits','--sandbox','--print-timeout','25m','--output-format','stream-json','--log-file',str(a/'agy.log'),'-p',prompt]
    save(a/'request.json',dict(utc=datetime.now(timezone.utc).isoformat(),model='gemini-3.8-flash-high',freeze_sha256=sha(a/'freeze.json'),prompt_sha256=sha(a/'prompt.txt'),CLI_before=freeze['CLI_before'],CLI_after=freeze['CLI_after'],automatic_retry=False))
    with (ROOT/'global_CLI_ledger.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),event='REGISTERED',call=no,global_count=freeze['CLI_after'],request_sha256=sha(a/'request.json'),cash_cost='UNKNOWN_NOT_ZERO'))+'\n')
    env=os.environ.copy();env.update(HTTP_PROXY='http://127.0.0.1:7892',HTTPS_PROXY='http://127.0.0.1:7892',GODEBUG='http2client=0')
    started=time.monotonic()
    with (a/'stream.jsonl').open('xb') as out,(a/'stderr.txt').open('xb') as err:
        proc=subprocess.Popen(cmd,cwd=a,env=env,stdout=out,stderr=err)
        save(a/'process.json',dict(pid=proc.pid,command=cmd[:cmd.index('-p')],owned_only=True))
        try:code=proc.wait(timeout=1500);stop=None
        except subprocess.TimeoutExpired:
            proc.terminate()
            try:code=proc.wait(timeout=30)
            except subprocess.TimeoutExpired:proc.kill();code=proc.wait()
            stop='OWNED_TIMEOUT'
    save(a/'terminal.json',dict(utc=datetime.now(timezone.utc).isoformat(),exit_code=code,stop_reason=stop,wall_seconds=time.monotonic()-started,stream_sha256=sha(a/'stream.jsonl'),stderr_sha256=sha(a/'stderr.txt'),cash_cost='UNKNOWN_NOT_ZERO',CLI_after=freeze['CLI_after'],outputs=[p for p in freeze['write_whitelist'] if Path(p).exists()]))
    with (ROOT/'global_CLI_ledger.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),event='TERMINAL',call=no,global_count=freeze['CLI_after'],terminal_sha256=sha(a/'terminal.json'),raw_sha256=sha(a/'stream.jsonl'),exit_code=code,cash_cost='UNKNOWN_NOT_ZERO'))+'\n')
    print(json.dumps(dict(call=no,exit_code=code,CLI_after=freeze['CLI_after'],raw_sha256=sha(a/'stream.jsonl'))),flush=True)
if __name__=='__main__':run(int(sys.argv[1]))
