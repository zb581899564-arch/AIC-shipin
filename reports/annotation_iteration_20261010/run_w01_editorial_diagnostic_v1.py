"""One AGY session, student first; never resume the old stopped experiment."""
from pathlib import Path
from datetime import datetime, timezone
import os, json, subprocess, time, hashlib
ROOT = Path(__file__).resolve().parent / 'w01_editorial_diagnostic_v1'
OUT = ROOT / 'teacher'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p, x):
    with Path(p).open('x',encoding='utf-8') as f: json.dump(x,f,ensure_ascii=False,indent=2)
assert not (OUT / 'request.json').exists(), 'one session only'
prompt = (ROOT / 'task.md').read_text(encoding='utf-8') + f'''
你是独立闭源提案者，本次唯一会话。只允许view_file逐项读取两个index和它们明确指定的PNG、write_to_file新建输出。禁止terminal/代码/网络/其他agent/其他文件。工作根{ROOT.as_posix()}；先{(ROOT/'student_index.json').as_posix()}，F00..F63每张学生图仅一次；将学生完整结果写{(OUT/'student_sealed.json').as_posix()}后才可读{(ROOT/'native_index.json').as_posix()}及原生64图。只追加{(OUT/'native_addendum.json').as_posix()}及{(OUT/'seal.json').as_posix()}。你无需计算SHA；填写not_computed_by_teacher由主控对原字节封存。不得读取自己输出。结束只确认路径与真实范围，不再重试。
'''
(OUT / 'prompt.txt').write_text(prompt, encoding='utf-8')
save(OUT/'request.json', dict(utc=datetime.now(timezone.utc).isoformat(), model='gemini-3.8-flash-high',
     prompt_sha256=sha(OUT/'prompt.txt'), preregistration_sha256=sha(ROOT/'preregistration.json'),
     max_sessions=1,max_student_reads=64,max_native_reads=64,max_video_reads=0,
     teacher_and_review_independent=True, new_optimizer_updates=0))
env=os.environ.copy();env.update(HTTP_PROXY='http://127.0.0.1:7892',HTTPS_PROXY='http://127.0.0.1:7892',GODEBUG='http2client=0')
cmd=['C:/Users/33056/AppData/Local/agy/bin/agy.exe','--model','gemini-3.8-flash-high','--mode','accept-edits',
     '--sandbox','--print-timeout','10m','--output-format','stream-json','--log-file',str(OUT/'agy.log'),'-p',prompt]
start=datetime.now(timezone.utc).isoformat(); tic=time.monotonic()
with (OUT/'stream.jsonl').open('xb') as stdout,(OUT/'stderr.txt').open('xb') as stderr:
    p=subprocess.run(cmd,cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
save(OUT/'terminal.json',dict(started_utc=start,finished_utc=datetime.now(timezone.utc).isoformat(),
     exit_code=p.returncode,elapsed_seconds=time.monotonic()-tic,exit_zero_not_acceptance=True,
     outputs={n:dict(bytes=(OUT/n).stat().st_size,sha256=sha(OUT/n)) for n in ('student_sealed.json','native_addendum.json','seal.json') if (OUT/n).exists()},
     new_optimizer_updates=0,cash_cost='UNKNOWN_NOT_ZERO'))
print(json.dumps({'exit_code':p.returncode,'output_folder':str(OUT)},ensure_ascii=False))
