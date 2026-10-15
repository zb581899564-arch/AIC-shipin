"""One finite serialization recovery of already-viewed images; preserve failed original."""
from pathlib import Path
from datetime import datetime,timezone
import os,json,hashlib,subprocess,time
ROOT=Path(__file__).resolve().parent/'w01_editorial_diagnostic_v1';PRIOR=ROOT/'h3_second_half32_factual_v1';OUT=ROOT/'h3_second_half32_serialization_recovery_v1'
term=json.loads((PRIOR/'terminal.json').read_text(encoding='utf-8-sig'));assert not term['output_exists'] and not (PRIOR/'facts.json').exists()
rows=[json.loads(s) for s in (PRIOR/'stream.jsonl').read_text(encoding='utf-8-sig').splitlines() if s.strip()]
refs=json.loads((PRIOR/'input_index.json').read_text(encoding='utf-8-sig'))['frames']
calls=[r['step_update'] for r in rows if r.get('step_update',{}).get('step_type')=='tool' and r['step_update'].get('state')=='DONE']
readpaths=[str(Path(c['tool_info']['parameters']['AbsolutePath']).resolve()) for c in calls if c['tool_name']=='view_file']
assert all(readpaths.count(str(Path(r['path']).resolve()))==1 for r in refs)
cid=rows[0]['conversation_id'];assert cid=='5538cc82-a7fc-4228-9fa5-9671ed34064f'
OUT.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):
    with p.open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
prior_stream_sha256=sha(PRIOR/'stream.jsonl')
save(OUT/'request.json',dict(status='ONE_SERIALIZATION_RECOVERY_SAME_INCOMPLETE_FACTUAL_PROPOSAL',utc=datetime.now(timezone.utc).isoformat(),
    conversation_id=cid,prior_stream_sha256=sha(PRIOR/'stream.jsonl'),prior_terminal_sha256=sha(PRIOR/'terminal.json'),
    prior_32_unique_PNG_reads_verified=True,prior_one_session_and_strict_240_second_wall_protocol_not_pass=True,
    recovery_scientific_no_new_image_evidence=True,max_sessions=1,max_additional_PNG_reads=0,max_print_seconds=180,
    conservative_post_stop_new_model_task_count=4,distinct_post_stop_windows=1,additional_recovery_after_this_allowed=False,
    cash_cost='UNKNOWN_NOT_ZERO',training_admitted=False,new_optimizer_updates=0,new_426_calls=0))
chunks=[]
for n in range(8):
    compact=[{k:r[k] for k in ('frame_id','source_ordinal','local_seconds_exact')} for r in refs[n*4:n*4+4]]
    chunks.append(dict(output_path=(OUT/f'facts_chunk_{n+1:02d}.json').as_posix(),identities=compact))
prompt='''这是同一份未完成32张事实任务的唯一工程恢复。原CLI打印超时而非新图任务；前面F32..F63已逐张实际view_file成功，无须也禁止再读任何PNG/index/文件，禁止其他工具。仅从同会话已经实际看到的图生成事实记录；记不清就写unclear，不猜。分八份输出，每四张一份，逐份用write_to_file写出下面新路径，禁止改原失败记录。每文件JSON含frame_observations数组4行，每行字段frame_id、source_ordinal、local_seconds_exact、actual_image_read、visible_subject（一句客观主体/构图）、subtitle_text（逐字转录，无null、不确定unclear）、subtitle_legibility、uncertainties，以及training_admitted:false。不得输出事件/高光取舍/情绪/动机。不知道内容如实标unclear，但必须使用原身份。只确认八个输出实际存在，不要求再计算SHA。以下只重复原输入的身份元数据，不包含任何旧答案/字幕提示：\n'''+json.dumps(chunks,ensure_ascii=False)
(OUT/'prompt.txt').write_text(prompt,encoding='utf-8')
env=os.environ.copy();env.update(HTTP_PROXY='http://127.0.0.1:7892',HTTPS_PROXY='http://127.0.0.1:7892',GODEBUG='http2client=1')
cmd=['C:/Users/33056/AppData/Local/agy/bin/agy.exe','--conversation',cid,'--model','gemini-3.8-flash-high','--mode','accept-edits','--sandbox',
    '--print-timeout','3m','--output-format','stream-json','--log-file',str(OUT/'agy.log'),'-p',prompt]
started=datetime.now(timezone.utc).isoformat();tic=time.monotonic()
with (OUT/'stream.jsonl').open('xb') as stdout,(OUT/'stderr.txt').open('xb') as stderr:
    result=subprocess.run(cmd,cwd=OUT,env=env,stdout=stdout,stderr=stderr)
save(OUT/'terminal.json',dict(started_utc=started,finished_utc=datetime.now(timezone.utc).isoformat(),exit_code=result.returncode,elapsed_seconds=time.monotonic()-tic,
    output_files=[dict(path=str(p),sha256=sha(p)) for p in sorted(OUT.glob('facts_chunk_*.json'))],original_stream_unchanged=sha(PRIOR/'stream.jsonl')==prior_stream_sha256,cash_cost='UNKNOWN_NOT_ZERO'))
print(json.dumps({'exit_code':result.returncode,'chunks_written':len(list(OUT.glob('facts_chunk_*.json'))),'out':str(OUT)},ensure_ascii=False))
