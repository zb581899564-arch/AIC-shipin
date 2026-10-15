"""Bounded resume: preserve invalid raw, retry in a new attempt, never trim invented time."""
from pathlib import Path
from datetime import datetime,timezone
import json,subprocess
from gemini_batch import ROOT,AGY,MODEL,sha,save,accept,prompt,prior_native_receipt
def main():
    manifests=[json.loads(p.read_text(encoding='utf-8')) for p in (ROOT/'input').glob('*/manifest.json')]
    assert len(manifests)==50
    manifests.sort(key=lambda m:(m['source_id']!='PJrm840pAUI',m['category'],m['source_id']))
    receipts=[];rejections=[];unresolved=[]
    old=ROOT/'gemini_progress.json';snap=ROOT/'temporal_v2_stop_snapshot.json'
    if not snap.exists():save(snap,json.loads(old.read_text(encoding='utf-8')))
    for m in manifests:
        sid=m['source_id'];base=ROOT/'raw/gemini'/sid;existing=list(base.glob('attempt_*/acceptance.json'))
        if existing:
            assert len(existing)==1;r=json.loads(existing[0].read_text(encoding='utf-8'));assert r['source_id']==sid and r['media_sha256']==m['media_sha256'] and sha(Path(r['raw']['path']))==r['raw']['sha256'];receipts.append(r);continue
        if sid=='GsAD1KT1xo8':
            job=base/'attempt_01';job.mkdir(parents=True,exist_ok=True);receipts.append(prior_native_receipt(m,job));continue
        for job in sorted(base.glob('attempt_*')):
            if not (job/'highlights.json').exists() or not (job/'cli_terminal.json').exists():continue
            try:r=accept(m,job)
            except Exception as exc:
                raw=json.loads((job/'highlights.json').read_text(encoding='utf-8-sig'))
                bad=[dict(event_index=i,start=e.get('start_seconds'),end=e.get('end_seconds_exclusive')) for i,e in enumerate(raw.get('events',[])) if not (isinstance(e.get('start_seconds'),(float,int)) and isinstance(e.get('end_seconds_exclusive'),(float,int)) and 0<=e['start_seconds']<e['end_seconds_exclusive']<=m['source_duration_seconds']+1e-6)]
                record=dict(source_id=sid,attempt=job.name,error=repr(exc),raw_sha256=sha(job/'highlights.json'),source_duration_seconds=m['source_duration_seconds'],out_of_domain_events=bad,status='REJECTED_RAW_PRESERVED_NO_CLIPPING')
                if not (job/'rejection.json').exists():save(job/'rejection.json',record)
                rejections.append(record)
            else:receipts.append(r);break
        if receipts and receipts[-1]['source_id']==sid:continue
        succeeded=False
        for retry in range(2):
            n=1
            while (base/f'attempt_{n:02d}').exists():n+=1
            job=base/f'attempt_{n:02d}';job.mkdir(parents=True,exist_ok=False)
            task=prompt(m,job)+f'\n硬时间边界：本源仅{m["source_duration_seconds"]}秒。任何事件、观察时间戳均不得超过这个值；不得沿用其他视频时钟。工具返回内部采样有限时，只标实际可见事件，未观察的尾部保持UNKNOWN。写出前逐条确认时间范围，不得编造后续事件。'
            (job/'prompt.txt').write_text(task,encoding='utf-8')
            save(old,dict(utc=datetime.now(timezone.utc).isoformat(),stage='RUNNING',active_source=sid,active_attempt=job.name,completed=len(receipts),expected=50,rejected_attempts=rejections,controller='gemini_resume_v3'))
            cmd=[str(AGY),'--model',MODEL,'--mode','accept-edits','--sandbox','--output-format','stream-json','--log-file',str(job/'agy.log'),'-p',task]
            with (job/'stream.jsonl').open('wb') as out,(job/'stderr.txt').open('wb') as err:p=subprocess.run(cmd,cwd=ROOT,stdout=out,stderr=err,check=False)
            save(job/'cli_terminal.json',dict(exit_code=p.returncode,finished_utc=datetime.now(timezone.utc).isoformat()))
            try:r=accept(m,job)
            except Exception as exc:
                record=dict(source_id=sid,attempt=job.name,error=repr(exc),status='REJECTED_RAW_PRESERVED',raw_sha256=sha(job/'highlights.json') if (job/'highlights.json').exists() else None)
                save(job/'rejection.json',record);rejections.append(record)
            else:receipts.append(r);succeeded=True;break
        if not succeeded:unresolved.append(sid)
        save(old,dict(utc=datetime.now(timezone.utc).isoformat(),stage='CONTINUING',completed=len(receipts),expected=50,receipts=receipts,rejected_attempts=rejections,unresolved=unresolved,controller='gemini_resume_v3'))
        print(json.dumps(dict(source_id=sid,completed=len(receipts),unresolved=unresolved)),flush=True)
    save(old,dict(utc=datetime.now(timezone.utc).isoformat(),stage='COMPLETE' if len(receipts)==50 else 'COMPLETE_WITH_UNRESOLVED',completed=len(receipts),expected=50,receipts=receipts,rejected_attempts=rejections,unresolved=unresolved,controller='gemini_resume_v3'))
if __name__=='__main__':main()
