"""Sequential authorized agy annotation with raw tool-call receipts and exact resume."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import subprocess
import hashlib
import json
import math
import sys

ROOT=Path(__file__).resolve().parent
AGY=Path('C:/Users/33056/AppData/Local/agy/bin/agy.exe')
MODEL='gemini-3.8-flash-high'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');tmp.replace(p)
def number(x):return isinstance(x,(float,int)) and not isinstance(x,bool) and math.isfinite(x)
def prior_native_receipt(manifest,job):
    base=ROOT.parent/'gemini_distillation_data_20261009'
    prior=base/'native_video_acceptance.json'
    old=json.loads(prior.read_text(encoding='utf-8-sig'))
    item=old['raw_files'][0];raw=Path(item['path'])
    assert old['source_id']==manifest['source_id']=='GsAD1KT1xo8'
    assert old['source_sha256']==manifest['media_sha256']
    assert old['native_mp4_read_entry_observed_in_ui'] is True
    assert sha(raw)==item['sha256']=='49ccffb856b1786504c7f1e731dd9a5a5576e5de8f7def111fa0be3ecad4bfd5'
    doc=json.loads(raw.read_text(encoding='utf-8-sig'))
    assert doc['native_video_accepted'] is True
    for row in doc['events']:
        a,b=row['start_seconds'],row['end_seconds_exclusive']
        assert row['state'] in ('KEEP','UNKNOWN') and number(a) and number(b)
        assert 0<=a<b<=manifest['source_duration_seconds']+1e-6
    receipt=dict(utc=datetime.now(timezone.utc).isoformat(),status='EXACT_PRIOR_NATIVE_UI_RECEIPT_REUSED',
        source_id=manifest['source_id'],media_sha256=manifest['media_sha256'],model='Gemini 3.8 Flash High (prior UI)',
        states=dict(Counter(r['state'] for r in doc['events'])),new_model_calls=0,
        raw={'path':str(raw),'sha256':sha(raw)},prior_acceptance={'path':str(prior),'sha256':sha(prior)},
        full_source_frame_observation_independently_proven=False,cli_stream_available=False,
        no_unobserved_to_negative=True)
    save(job/'acceptance.json',receipt)
    return receipt
def accept(manifest,job):
    doc=json.loads((job/'highlights.json').read_text(encoding='utf-8-sig'))
    terminal=json.loads((job/'cli_terminal.json').read_text(encoding='utf-8-sig'))
    events=[json.loads(line) for line in (job/'stream.jsonl').read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    init=next(e for e in events if e.get('event')=='init')['init']
    final=next(e for e in reversed(events) if e.get('event')=='result')['result']
    video_calls=[]
    for e in events:
        step=e.get('step_update',{})
        info=step.get('tool_info',{})
        if step.get('state')=='DONE' and step.get('tool_name')=='view_file':
            path=info.get('parameters',{}).get('AbsolutePath','')
            if path.replace('\\','/').endswith('/'+manifest['media_file']):video_calls.append(step)
    assert terminal['exit_code']==0 and final['status']=='SUCCESS'
    assert init['model']==MODEL and video_calls
    assert doc['source_id']==manifest['source_id'] and doc['native_video_accepted'] is True
    assert doc['actual_tool_name']=='view_file' and isinstance(doc['events'],list)
    for row in doc['events']:
        assert row['state'] in ('KEEP','UNKNOWN') and row.get('visible_evidence')
        a,b=row['start_seconds'],row['end_seconds_exclusive']
        assert number(a) and number(b) and 0<=a<b<=manifest['source_duration_seconds']+1e-6
    receipt=dict(utc=datetime.now(timezone.utc).isoformat(),status='PASS_NATIVE_VIDEO_TOOL_CALL_AND_EVENT_SCHEMA',
        source_id=manifest['source_id'],media_sha256=manifest['media_sha256'],model=MODEL,
        states=dict(Counter(row['state'] for row in doc['events'])),native_video_completed_tool_calls=len(video_calls),
        full_source_frame_observation_independently_proven=False,
        declared_timestamps_are_model_report_not_independent_tool_frame_receipt=True,
        raw={'path':str(job/'highlights.json'),'sha256':sha(job/'highlights.json')},
        stream_sha256=sha(job/'stream.jsonl'),conversation_id=final['conversation_id'],
        usage=final.get('usage'),duration_seconds=final.get('duration_seconds'),no_unobserved_to_negative=True)
    save(job/'acceptance.json',receipt)
    return receipt
def prompt(manifest,job):
    sid=manifest['source_id'];dest=ROOT/'input'/sid
    return f'''为Qwen8B做真实视频高光标注准备，只处理源{sid}。
用户已授权本批TVSum视频标注。先原生view_file读取{dest.as_posix()}/manifest.json，再原生view_file直接查看{dest.as_posix()}/{sid}.mp4。
不得运行终端/脚本/代码、浏览器、联网搜索、外部API、其他模型或子代理；不读PNG、人类评分、其他源视频或其他模型标签，不训练。
根据实际视觉内容给精彩事件候选，KEEP或UNKNOWN；不凑数、不编造音频。原生工具若是内部抽样，就如实写实际可见时间点、观察域和限制，不能声称连续播放或逐帧全看；不把未观察间隙变成负例。
事件相对视频开始时钟0至{manifest['source_duration_seconds']}秒；每条start_seconds、end_seconds_exclusive、state、event_type、visible_evidence、boundary_uncertainty_seconds（未知null）、confidence LOW/MEDIUM/HIGH。看不清事件边界不要编造0.5秒精度，记null或实际不确定性。
只用write_to_file写{(job/'highlights.json').as_posix()}；已存在不能覆盖。
顶层source_id、input_mode、actual_tool_name、native_video_accepted、observed_timestamps_seconds（不知道准确观察戳就空并说明）、observation_scope、audio_observed（无真实音频false）、events、unobserved_domain_policy、limitations。
失败则写{(job/'failure.json').as_posix()}，保留具体工具错误停止。完成简短汇报实际路径和数量。'''
def main():
    source_manifests=[json.loads(p.read_text(encoding='utf-8')) for p in sorted((ROOT/'input').glob('*/manifest.json'))]
    assert len(source_manifests)==50
    results=[];errors=[]
    first='PJrm840pAUI'
    source_manifests.sort(key=lambda m:(m['source_id']!=first,m['category'],m['source_id']))
    for manifest in source_manifests:
        sid=manifest['source_id'];job=ROOT/'raw/gemini'/sid/'attempt_01'
        job.mkdir(parents=True,exist_ok=True)
        if sid=='GsAD1KT1xo8':
            try:receipt=prior_native_receipt(manifest,job)
            except Exception as exc:
                errors.append(dict(source_id=sid,error=repr(exc),status='PRIOR_IDENTITY_REJECTED'));break
            results.append(receipt)
            print(json.dumps(dict(status='PRIOR_NATIVE_EXACT_REUSE',source_id=sid)),flush=True)
        elif (job/'highlights.json').exists() and (job/'cli_terminal.json').exists():
            try:receipt=accept(manifest,job)
            except Exception as exc:
                errors.append(dict(source_id=sid,error=repr(exc),status='EXISTING_RAW_REJECTED_PRESERVED'));break
            results.append(receipt)
            print(json.dumps(dict(status='EXACT_ACCEPTED_REUSE',source_id=sid,states=receipt['states'])),flush=True)
        else:
            if any(job.iterdir()):
                errors.append(dict(source_id=sid,status='PARTIAL_JOB_PRESERVED_REQUIRES_RECONCILIATION'));break
            task=prompt(manifest,job);(job/'prompt.txt').write_text(task,encoding='utf-8')
            save(ROOT/'gemini_progress.json',dict(utc=datetime.now(timezone.utc).isoformat(),stage='RUNNING',active_source=sid,completed=len(results),expected=50,errors=errors))
            cmd=[str(AGY),'--model',MODEL,'--mode','accept-edits','--sandbox','--output-format','stream-json','--log-file',str(job/'agy.log'),'-p',task]
            with (job/'stream.jsonl').open('wb') as out,(job/'stderr.txt').open('wb') as err:
                process=subprocess.run(cmd,cwd=ROOT,stdout=out,stderr=err,check=False)
            save(job/'cli_terminal.json',dict(exit_code=process.returncode,finished_utc=datetime.now(timezone.utc).isoformat()))
            try:receipt=accept(manifest,job)
            except Exception as exc:
                errors.append(dict(source_id=sid,error=repr(exc),status='RAW_OR_TOOL_FAILURE_PRESERVED'));break
            results.append(receipt)
            print(json.dumps(dict(status='NEW_ACCEPTED',source_id=sid,states=receipt['states'])),flush=True)
        save(ROOT/'gemini_progress.json',dict(utc=datetime.now(timezone.utc).isoformat(),stage='CONTINUING',completed=len(results),expected=50,receipts=results,errors=errors))
    status='COMPLETE' if len(results)==50 and not errors else 'STOP_PRESERVE_EVIDENCE'
    save(ROOT/'gemini_progress.json',dict(utc=datetime.now(timezone.utc).isoformat(),stage=status,completed=len(results),expected=50,receipts=results,errors=errors))
    print(json.dumps(dict(status=status,completed=len(results),errors=errors)),flush=True)
    if errors:raise SystemExit(1)
if __name__=='__main__':main()
