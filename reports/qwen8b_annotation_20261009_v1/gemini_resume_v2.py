"""Resume interrupted temporal annotation without repeating accepted successes."""
from pathlib import Path
from datetime import datetime,timezone
import json,subprocess,sys
from gemini_batch import ROOT,AGY,MODEL,sha,save,accept,prompt,prior_native_receipt
def main():
    manifests=[json.loads(p.read_text(encoding='utf-8')) for p in (ROOT/'input').glob('*/manifest.json')]
    assert len(manifests)==50
    manifests.sort(key=lambda m:(m['source_id']!='PJrm840pAUI',m['category'],m['source_id']))
    receipts=[];errors=[]
    old=ROOT/'gemini_progress.json';snapshot=ROOT/'temporal_interruption_v1_snapshot.json'
    if not snapshot.exists():
        save(snapshot,dict(utc=datetime.now(timezone.utc).isoformat(),previous_progress=json.loads(old.read_text()),
            observation='Prior gemini_batch.py and agy child absent in live Win32_Process checks; no terminal record for interrupted current source; cause and charged duration UNKNOWN. Original partial tool stream kept.'))
    for m in manifests:
        sid=m['source_id'];base=ROOT/'raw/gemini'/sid;existing=[]
        for path in sorted(base.glob('attempt_*/acceptance.json')):
            r=json.loads(path.read_text(encoding='utf-8'));raw=Path(r['raw']['path'])
            assert r['source_id']==sid and r['media_sha256']==m['media_sha256'] and sha(raw)==r['raw']['sha256']
            existing.append(r)
        if existing:
            assert len(existing)==1;receipts.append(existing[0])
        elif sid=='GsAD1KT1xo8':
            job=base/'attempt_01';job.mkdir(parents=True,exist_ok=True);receipts.append(prior_native_receipt(m,job))
        else:
            # Reconcile any completed raw before a new call. Partial attempt files are preserved.
            complete=[p for p in base.glob('attempt_*') if (p/'highlights.json').exists() and (p/'cli_terminal.json').exists()]
            if complete:
                assert len(complete)==1;receipts.append(accept(m,complete[0]))
            else:
                n=1
                while (base/f'attempt_{n:02d}').exists():n+=1
                job=base/f'attempt_{n:02d}';job.mkdir(parents=True,exist_ok=False)
                task=prompt(m,job);(job/'prompt.txt').write_text(task,encoding='utf-8')
                save(ROOT/'gemini_progress.json',dict(utc=datetime.now(timezone.utc).isoformat(),stage='RUNNING',active_source=sid,active_attempt=job.name,completed=len(receipts),expected=50,errors=errors,controller='gemini_resume_v2'))
                cmd=[str(AGY),'--model',MODEL,'--mode','accept-edits','--sandbox','--output-format','stream-json','--log-file',str(job/'agy.log'),'-p',task]
                with (job/'stream.jsonl').open('wb') as out,(job/'stderr.txt').open('wb') as err:
                    p=subprocess.run(cmd,cwd=ROOT,stdout=out,stderr=err,check=False)
                save(job/'cli_terminal.json',dict(exit_code=p.returncode,finished_utc=datetime.now(timezone.utc).isoformat()))
                try:receipts.append(accept(m,job))
                except Exception as exc:
                    errors.append(dict(source_id=sid,attempt=job.name,status='REJECTED_RAW_PRESERVED',error=repr(exc)));break
        save(ROOT/'gemini_progress.json',dict(utc=datetime.now(timezone.utc).isoformat(),stage='CONTINUING',completed=len(receipts),expected=50,receipts=receipts,errors=errors,controller='gemini_resume_v2'))
        print(json.dumps(dict(source_id=sid,completed=len(receipts))),flush=True)
    state='COMPLETE' if len(receipts)==50 and not errors else 'STOP_PRESERVE_EVIDENCE'
    save(ROOT/'gemini_progress.json',dict(utc=datetime.now(timezone.utc).isoformat(),stage=state,completed=len(receipts),expected=50,receipts=receipts,errors=errors,controller='gemini_resume_v2'))
    if errors:raise SystemExit(1)
if __name__=='__main__':main()
