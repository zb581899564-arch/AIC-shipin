from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,subprocess,os,time
ROOT=Path(__file__).resolve().parent; A=ROOT/'attempt01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
idx=json.loads((ROOT/'teacher_index.json').read_text());freeze=json.loads((ROOT/'freeze.json').read_text())
for n,s in freeze['files'].items():assert sha(ROOT/n)==s
if (A/'request.json').exists():raise ValueError('Never repeat registered one-call test')
lines=[]
for g in idx['groups']:
    lines.append(f"GROUP {g['group']}: after reading exactly these four PNGs in this order, write {Path(g['output_path']).as_posix()}")
    lines.extend(f"slot {r['slot']}: {Path(r['path']).as_posix()}" for r in g['frames'])
prompt=f'''用户授权一个新的独立事实识别方法测试，你未收到本测试的旧模型答案/主控答案/评分/预测。只用view_file和write_to_file；禁止terminal/代码/联网/其他模型/子代理，禁止读目录或查找其他文件。
严格白名单：{(ROOT/'teacher_index.json').as_posix()}、下列20个原PNG、指定5个自身输出。不读任何视频、旧答案、oracle、PROTOCOL、freeze或其他文件。先读teacher_index一次，再依GROUP0..4。
逐张读同一组slot0..3的4个PNG之后，立即写该组JSON；不能读下一组再倒写上一组。每张只读一次。每组写完允许只view_file核对已经写出的自身同组JSON一次，不能读取尚未创建输出；成功输出不覆盖、不修订。工具失败立即停止并如实报告，禁止重复调用或用猜测填缺图。
重要：实际Qwen学生处理器有64张有效输入；旧任务给教师的8张只是教师预览。本测试不提供学生图，仅测20原图的主体/字幕/构图；不做高光选择、不写KEEP/NO、事件、边界、训练标签或音频猜测。
只看每张单图，不要拿邻图内容补当前图：同一主体也可能换景或字幕消失。visible_fact只陈述当前图真的可见内容，不推测跳跃落地、动机或心理。字幕须逐图判断是否存在；能清楚辨认才原样抄写，若存在而无法确认用UNKNOWN（不得沿用邻图字幕）。构图按当前图选择最贴切枚举，真正不确定用UNKNOWN。
输出每组仅JSON对象{{"group":整数,"items":[4条]}}。每条严格这些字段：slot(0..3)、subject(枚举)、composition(枚举)、subtitle_visible(true/false/"UNKNOWN")、subtitle_text(可见清晰文字字符串；无字幕null；存在而不能辨认"UNKNOWN")、visible_fact(中文当前图事实)。不要输出frame_id、ordinal、PTS或自报完成计数；这些身份由外部程序根据slot绑定。
subject枚举：{json.dumps(idx['subject_enum'])}
composition枚举：{json.dumps(idx['composition_enum'])}
PERSON_CHEST=人物胸部以上正面/侧面，PERSON_PARTIAL_EDGE=人物仅剩边缘局部；DOG_HEAD_CHEST=室内犬头胸近景；DOG_FACE_OUTDOOR=户外犬脸近景；DOG_PARTLY_OCCLUDED=犬脸/身部分被白布等遮挡；DOG_EXTREME_FACE=双眼鼻口填满且耳朵不在画面的极近脸；WALL_CLOCK_NO_SUBJECT=空墙钟无人无犬；STAIRS_NO_SUBJECT=台阶门口无人无犬；DOG_ON_STAIRS=犬在台阶或门口可见；DOG_ON_GRASS=草地犬全身/背影；OTHER/UNKNOWN按真实情况。
不设正确数或质量自评分，不称人工gold。只写指定5输出。全部读写完自然停止。
{chr(10).join(lines)}'''
(A/'prompt.txt').write_text(prompt,encoding='utf-8')
cmd=['C:/Users/33056/AppData/Local/agy/bin/agy.exe','--model','gemini-3.8-flash-high','--mode','accept-edits','--sandbox','--print-timeout','10m','--output-format','stream-json','--log-file',str(A/'agy.log'),'-p',prompt]
save(A/'request.json',dict(utc=datetime.now(timezone.utc).isoformat(),freeze_sha256=sha(ROOT/'freeze.json'),prompt_sha256=sha(A/'prompt.txt'),
 model='gemini-3.8-flash-high',new_call_count=1,prior_CLI_calls=22,after_CLI_calls=23,global_cap=36,stage_cap=1,automatic_retry=False))
env=os.environ.copy();env.update(HTTP_PROXY='http://127.0.0.1:7892',HTTPS_PROXY='http://127.0.0.1:7892',GODEBUG='http2client=0')
started=time.monotonic()
with (A/'stream.jsonl').open('xb') as stdout,(A/'stderr.txt').open('xb') as stderr:
    proc=subprocess.Popen(cmd,cwd=A,env=env,stdout=stdout,stderr=stderr)
    save(A/'process.json',dict(pid=proc.pid,command=cmd[:cmd.index('-p')],only_this_owned_child=True))
    try:code=proc.wait(timeout=660);stop=None
    except subprocess.TimeoutExpired:proc.terminate();code=proc.wait(timeout=30);stop='OWNED_TIMEOUT'
save(A/'terminal.json',dict(utc=datetime.now(timezone.utc).isoformat(),exit_code=code,stop_reason=stop,wall_seconds=time.monotonic()-started,
 stream_sha256=sha(A/'stream.jsonl'),groups_written=[g['group'] for g in idx['groups'] if Path(g['output_path']).is_file()],cash_cost='UNKNOWN_NOT_ZERO',new_training=0))
print(json.dumps(dict(exit_code=code,groups_written=[g['group'] for g in idx['groups'] if Path(g['output_path']).is_file()],stop_reason=stop)))
