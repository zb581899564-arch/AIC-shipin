"""CPU-only processing of completed annotation files; never controls apps or models."""
from pathlib import Path
from datetime import datetime,timezone
import time,json,traceback
from spatial_prepare import ROOT,render,sha,save
from export_preparation import main as export
def run():
    seen={};failures={}
    while True:
        changed=False
        for pattern,version in [('*/draft_01.json','draft_01'),('*/review_01.json','review_01')]:
            for p in sorted((ROOT/'raw/doubao').glob(pattern)):
                if time.time()-p.stat().st_mtime<3:continue
                digest=sha(p)
                if seen.get(str(p))==digest:continue
                try:
                    render(p.parent.name,version);changed=True;seen[str(p)]=digest
                except Exception as exc:
                    if failures.get(str(p),{}).get('sha256')!=digest:
                        failures[str(p)]=dict(sha256=digest,error=repr(exc),traceback=traceback.format_exc())
                        print(json.dumps({'rejected_file':str(p),'error':repr(exc)}),flush=True)
                    seen[str(p)]=digest;changed=True
        signatures=[]
        for pattern in ['*/attempt_01/acceptance.json','*/final_checks_01.json']:
            parent=ROOT/'raw/gemini' if 'acceptance' in pattern else ROOT/'raw/doubao'
            signatures.extend((str(p),sha(p)) for p in sorted(parent.glob(pattern)))
        sig=repr(signatures)
        if sig!=seen.get('export_signature'):
            seen['export_signature']=sig;changed=True
        if changed:
            export()
            save(ROOT/'postprocessing_progress.json',dict(utc=datetime.now(timezone.utc).isoformat(),stage='WATCHING_COMPLETED_FILES',failures=failures,processed_files=len(seen)-1))
        g=ROOT/'gemini_progress.json';d=ROOT/'raw/doubao/batch_progress.json'
        if g.exists() and d.exists():
            try:
                gg=json.loads(g.read_text(encoding='utf-8'));dd=json.loads(d.read_text(encoding='utf-8-sig'))
                # All drafts are only an intermediate milestone: keep this watcher available for UI review output.
                if gg.get('stage')=='COMPLETE' and len(list((ROOT/'raw/doubao').glob('*/review_01.json')))==50:
                    export();print('ALL_TEACHER_PHASES_REVIEW_FILES_PRESENT',flush=True);return
            except (ValueError,OSError):pass
        time.sleep(5)
if __name__=='__main__':run()
