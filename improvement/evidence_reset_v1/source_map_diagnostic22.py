"""First source-program MAP diagnostic on existing20 initial/final scores."""
import json
import hashlib
from pathlib import Path
import time


def ref(p):
    p=Path(p).resolve(strict=True);b=p.read_bytes()
    return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())


def main():
    import numpy as np
    N=Path(__file__).resolve().parent; start=time.monotonic()
    reg=json.loads((N/'registration22.json').read_text()); assert reg['code_ref']==ref(__file__)
    result=json.loads((N/'gpu_completion20.json').read_text())
    assert ref(N/'remaining_completion21.json')==reg['remaining_completion21_ref']
    assert json.loads((N/'remaining_completion21.json').read_text())['scientific_status']=='PASS_ONE_STEP_OPTIMIZATION_MECHANISM_ONLY'
    targets=json.loads((N/'targets20.json').read_text()); rows=[]
    for target,row in zip(targets['sources'],result['source_reports']):
        assert row['sid']==target['sid']; selected=[]; metrics=[]; modes=[]
        for phase in [0,1]:
            count=0;tp=np.zeros(len(target['gt']),np.int64);union=set(); choices=[]
            for w,logits in zip(target['windows'],row['logits'+str(phase)]):
                choice=int(np.argmax(logits)); count+=w['lengths'][choice];tp+=np.asarray(w['overlap'][choice],np.int64)
                wr=w['window_ref'];assert ref(wr['path'])==wr;old=json.loads(Path(wr['path']).read_text())
                union.update(old['slots'][w['slots'][choice]]['selected_ordinals']);choices.append(w['slots'][choice])
            assert count==len(union)
            gt=np.asarray(target['gt']);den=count+gt
            f1=float(np.divide(2.*tp,den,out=np.ones_like(tp,dtype=float),where=den!=0).mean())
            selected.append(union);metrics.append(dict(F1=f1,selected_frames=count));modes.append(choices)
        rows.append(dict(sid=row['sid'],initial=metrics[0],updated=metrics[1],delta=metrics[1]['F1']-metrics[0]['F1'],
            added=len(selected[1]-selected[0]),deleted=len(selected[0]-selected[1]),
            changed_windows=sum(a!=b for a,b in zip(*modes)),initial_slots=modes[0],updated_slots=modes[1]))
    output=dict(status='TRAINING_MAP_PROGRAM_DIAGNOSTIC_ONLY',rows=rows,
        initial_macro_F1=float(np.mean([v['initial']['F1'] for v in rows])),updated_macro_F1=float(np.mean([v['updated']['F1'] for v in rows])),
        changed_sources=sum(bool(v['added'] or v['deleted']) for v in rows),added=sum(v['added'] for v in rows),deleted=sum(v['deleted'] for v in rows),
        model_calls=0,updates=0,seconds=time.monotonic()-start,production_admitted=False,official_submissions=0)
    with (N/'completion22.json').open('x')as f:json.dump(output,f,indent=2,allow_nan=False)
    print(json.dumps(dict(completion_ref=ref(N/'completion22.json'),summary=output)))


if __name__=='__main__':main()
