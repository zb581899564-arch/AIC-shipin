"""Windows-only final ZIP acceptance. No data/model/remote operations."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

BASE_SHA='b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def contents(path):
    with zipfile.ZipFile(path)as z:
        assert z.namelist()==['predictions.jsonl'] and z.testzip()is None,'Single JSONL/CRC failed'
        raw=z.read('predictions.jsonl');rows=[json.loads(s)for s in raw.decode('utf-8-sig').splitlines()if s.strip()]
    return raw,rows

def canonical(rows):
    v=[{k:r[k]for k in ('video_id','targetRatioWH','predictions')}for r in sorted(rows,key=lambda r:r['video_id'])]
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--zip',required=True,type=Path);p.add_argument('--linux-receipt',required=True,type=Path);p.add_argument('--baseline',required=True,type=Path);p.add_argument('--deliveries',required=True,type=Path);p.add_argument('--report',required=True,type=Path);args=p.parse_args()
    receipt=json.loads(args.linux_receipt.read_text(encoding='utf-8-sig'))
    assert args.zip.stat().st_size==receipt['zip']['bytes']and digest(args.zip)==receipt['zip']['sha256'],'Windows/Linux size or ZIP SHA mismatch'
    assert digest(args.baseline)==BASE_SHA,'Protected local40.47 changed'
    raw,rows=contents(args.zip);_,base=contents(args.baseline)
    assert hashlib.sha256(raw).hexdigest()==receipt['member_sha256'],'Windows/Linux member SHA mismatch'
    assert len(rows)==426 and {r['video_id']for r in rows}=={str(i)for i in range(426)},'Complete426 unique IDs'
    assert all(r['predictions']for r in rows),'Protected baseline sources must remain nonempty'
    assert all(0<r['model_params_b']<=9 and abs(r['model_params_b']-receipt['actual_resident_parameters']/1e9)<1e-12 for r in rows),'Actual complete parameter declaration'
    b={(r['video_id'],v['frame']):v['bboxes']for r in base for v in r['predictions']};n={(r['video_id'],v['frame']):v['bboxes']for r in rows for v in r['predictions']}
    assert len(b)==123506 and set(b)<=set(n)and all(n[k]==v for k,v in b.items()),'Original40.47 frame/box retention'
    assert len(n)==receipt['frames']and len(set(n)-set(b))==receipt['added_frames']>0 and receipt['removed_frames']==0,'Actual novel native selection denominator'
    candidate=canonical(rows);assert candidate==receipt['canonical_sha256']and candidate!=canonical(base),'Canonical prediction differs from Linux or protected baseline'
    checked=[];skipped=[]
    for old in sorted(args.deliveries.rglob('candidate*.zip')):
        if old.resolve()==args.zip.resolve():continue
        try:_,past=contents(old);prior=canonical(past)
        except (ValueError,KeyError,AssertionError,zipfile.BadZipFile)as error:
            skipped.append(dict(path=str(old),reason=repr(error)));continue
        assert candidate!=prior,'Duplicate historical real predictions: '+str(old)
        checked.append(dict(path=str(old),canonical_sha256=prior))
    result=dict(status='PASS_WINDOWS_FINAL_ZIP_LINUX_IDENTITY_BASELINE_RETENTION_AND_HISTORY',zip_path=str(args.zip.resolve()),bytes=args.zip.stat().st_size,sha256=digest(args.zip),member_sha256=hashlib.sha256(raw).hexdigest(),canonical_sha256=candidate,records=426,frames=len(n),added_frames=len(set(n)-set(b)),removed_frames=0,all_original_boxes_unchanged=True,protected_baseline_sha256=BASE_SHA,actual_resident_parameters=receipt['actual_resident_parameters'],Linux_independent11strict=receipt['independent11strict'],history_checked=checked,noncanonical_historical_files=skipped,official_score='UNKNOWN',website_submitted=False)
    with args.report.open('x',encoding='utf8')as f:json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:v for k,v in result.items()if k not in ['history_checked','noncanonical_historical_files']},ensure_ascii=False))

if __name__=='__main__':main()
