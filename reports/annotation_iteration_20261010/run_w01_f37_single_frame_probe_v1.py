"""One new factual diagnostic after the completed W01 protocol, never a gold label."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib,os,subprocess,time
BASE=Path(__file__).resolve().parent/'w01_editorial_diagnostic_v1'
OUT=BASE/'h2_f37_single_frame_v1'
OUT.mkdir(exist_ok=False)
ref=next(r for r in json.loads((BASE/'student_index.json').read_text(encoding='utf-8-sig'))['frames'] if r['frame_id']=='F37')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):
    with p.open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
assert sha(ref['path'])==ref['png_sha256']
request=dict(status='PREREGISTERED_ONE_FRESH_CONTEXT_FACTUAL_PROBE_NOT_EDITORIAL_SFT',utc=datetime.now(timezone.utc).isoformat(),
    hypothesis='Fresh single-frame context may avoid the sealed full-sequence F37 content misassignment; either result remains diagnostic, not proof of a unique cause.',
    source_frame_id=ref['frame_id'],source_ordinal=ref['source_ordinal'],png_sha256=ref['png_sha256'],local_seconds_exact=ref['local_seconds_exact'],
    frozen_complete_diagnostic_sha256=sha(BASE/'final_diagnostic_audit_v1.json'),
    max_sessions=1,max_PNG_reads=1,max_seconds=180,other_image_or_prior_answer_reads_allowed=False,
    conservative_post_stop_new_task_count_including_first_W01=2,distinct_post_stop_windows=1,
    new_optimizer_updates=0,new_426_calls=0,cash_cost='UNKNOWN_NOT_ZERO',no_new_paid_service_or_topup=True)
save(OUT/'request.json',request)
prompt=f'''这是独立单张图片事实核验，不是训练或高光标注。只允许view_file实际读取这一个PNG一次：{Path(ref['path']).as_posix()}。禁止任何其他文件、旧答案、其他图、终端、代码、联网和子任务，不看当前目录文件。读取后用write_to_file新建{(OUT/'observation.json').as_posix()}，JSON字段actual_image_read(bool)、visible_subject(简洁客观描述)、subtitle_text(逐字转录；无字幕写null；不可读写unclear)、subtitle_legibility、visible_details、uncertainties。只描述图中可见内容，不依据路径猜测，不用一张图判断动作经过、人物动机或情绪。没有成功读图就如实标false，不编内容。最后只确认输出路径。'''
(OUT/'prompt.txt').write_text(prompt,encoding='utf-8')
env=os.environ.copy();env.update(HTTP_PROXY='http://127.0.0.1:7892',HTTPS_PROXY='http://127.0.0.1:7892',GODEBUG='http2client=1')
cmd=['C:/Users/33056/AppData/Local/agy/bin/agy.exe','--model','gemini-3.8-flash-high','--mode','accept-edits','--sandbox',
     '--print-timeout','3m','--output-format','stream-json','--log-file',str(OUT/'agy.log'),'-p',prompt]
started=datetime.now(timezone.utc).isoformat();tic=time.monotonic()
with (OUT/'stream.jsonl').open('xb') as stdout,(OUT/'stderr.txt').open('xb') as stderr:
    result=subprocess.run(cmd,cwd=OUT,env=env,stdout=stdout,stderr=stderr)
save(OUT/'terminal.json',dict(started_utc=started,finished_utc=datetime.now(timezone.utc).isoformat(),exit_code=result.returncode,
    elapsed_seconds=time.monotonic()-tic,exit_zero_not_acceptance=True,output_exists=(OUT/'observation.json').exists(),
    output_sha256=sha(OUT/'observation.json') if (OUT/'observation.json').exists() else None,cash_cost='UNKNOWN_NOT_ZERO'))
print(json.dumps({'exit_code':result.returncode,'output_exists':(OUT/'observation.json').exists(),'output_dir':str(OUT)},ensure_ascii=False))
