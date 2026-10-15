"""One bounded fresh-context factual batch; no editorial selection or training."""
from pathlib import Path
from datetime import datetime,timezone
import os,json,hashlib,subprocess,time
ROOT=Path(__file__).resolve().parent/'w01_editorial_diagnostic_v1'
OUT=ROOT/'h3_second_half32_factual_v1';OUT.mkdir(exist_ok=False)
refs=json.loads((ROOT/'student_index.json').read_text(encoding='utf-8-sig'))['frames'][32:]
assert len(refs)==32
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):
    with p.open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
for row in refs:assert sha(row['path'])==row['png_sha256']
save(OUT/'input_index.json',dict(frames=refs))
save(OUT/'request.json',dict(status='ONE_PREREGISTERED_FIXED_SECOND_HALF32_FACTUAL_DIAGNOSTIC',utc=datetime.now(timezone.utc).isoformat(),
    hypothesis='Fresh 32-frame factual-only context may avoid full-sequence content misassignment; fixed contiguous half, not posthoc easy frame selection.',
    input_index_sha256=sha(OUT/'input_index.json'),max_sessions=1,max_PNG_reads=32,max_seconds=240,
    prior_answers_or_editorial_or_quota_hints_in_prompt=False,conservative_post_stop_new_task_count=3,distinct_post_stop_windows=1,
    cash_cost='UNKNOWN_NOT_ZERO',training_admitted=False,new_optimizer_updates=0,new_426_calls=0))
prompt=f'''这是独立图片事实核验，不是高光编辑。只允许view_file先读取{(OUT/'input_index.json').as_posix()}，再按index对F32..F63这32张PNG逐张实际读取，每图仅一次。禁止其他文件、原图、旧答案、终端、代码、联网和子任务，不读自己输出。不要推测未读图片内容。所有图片读取完后用write_to_file新建{(OUT/'facts.json').as_posix()}，只写JSON：{{"frame_observations":[...] ,"failed_frame_ids":[],"training_admitted":false}}。每帧精简字段：frame_id、source_ordinal、local_seconds_exact、actual_image_read、visible_subject（一句客观主体/构图，不写情绪动机）、subtitle_text（逐字转录，无写null，不可读写unclear）、subtitle_legibility、uncertainties。必须绑定当前图与当前frame_id，不能把相邻图字幕或主体移到当前编号；不要输出事件、区间、KEEP/NO、情绪或跨图动作推断。读取失败如实标false，不补猜。结束只确认实际读图数量与输出路径。'''
(OUT/'prompt.txt').write_text(prompt,encoding='utf-8')
env=os.environ.copy();env.update(HTTP_PROXY='http://127.0.0.1:7892',HTTPS_PROXY='http://127.0.0.1:7892',GODEBUG='http2client=1')
cmd=['C:/Users/33056/AppData/Local/agy/bin/agy.exe','--model','gemini-3.8-flash-high','--mode','accept-edits','--sandbox',
    '--print-timeout','4m','--output-format','stream-json','--log-file',str(OUT/'agy.log'),'-p',prompt]
started=datetime.now(timezone.utc).isoformat();tic=time.monotonic()
with (OUT/'stream.jsonl').open('xb') as stdout,(OUT/'stderr.txt').open('xb') as stderr:
    res=subprocess.run(cmd,cwd=OUT,env=env,stdout=stdout,stderr=stderr)
save(OUT/'terminal.json',dict(started_utc=started,finished_utc=datetime.now(timezone.utc).isoformat(),exit_code=res.returncode,
    elapsed_seconds=time.monotonic()-tic,exit_zero_not_acceptance=True,output_exists=(OUT/'facts.json').exists(),
    output_sha256=sha(OUT/'facts.json') if (OUT/'facts.json').exists() else None,cash_cost='UNKNOWN_NOT_ZERO'))
print(json.dumps({'exit_code':res.returncode,'output_exists':(OUT/'facts.json').exists(),'out':str(OUT)},ensure_ascii=False))
