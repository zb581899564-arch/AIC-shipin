"""Historical prediction-identity audit only; never chooses new model rules."""
from pathlib import Path
import hashlib,json,zipfile
W=Path(__file__).resolve().parents[2];R=Path(__file__).resolve().parent
records=[];non_submission=[]
for p in sorted((W/'deliveries').rglob('*.zip')):
    with zipfile.ZipFile(p) as z:
        if z.namelist()!=['predictions.jsonl']:
            non_submission.append(dict(path=str(p),reason='NOT_SINGLE_PREDICTIONS_JSONL_EVIDENCE_ARCHIVE'))
            continue
        assert z.testzip() is None
        raw=z.read('predictions.jsonl');values=[json.loads(s) for s in raw.splitlines() if s.strip()]
        assert len(values)==426
        relevant=[{k:v[k] for k in ('video_id','targetRatioWH','predictions')} for v in sorted(values,key=lambda v:v['video_id'])]
        digest=hashlib.sha256(json.dumps(relevant,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
        records.append(dict(Windows_path=str(p),filename=p.name,ZIP_SHA256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size,member_SHA256=hashlib.sha256(raw).hexdigest(),canonical_SHA256=digest,records=426))
result=dict(schema='ACTUAL_EXISTING_WINDOWS_DELIVERY_PREDICTION_IDENTITIES_V1',purpose='Only prevent renaming/duplicate predictions; not effect evaluation or test-content parameter selection',records=records,excluded_non_submission_archives=non_submission)
with (R/'windows_existing_delivery_history_12.json').open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print('HISTORICAL_SUBMISSION_ARCHIVES',len(records),'DISTINCT_PREDICTIONS',len({v['canonical_SHA256'] for v in records}),'EVIDENCE_ARCHIVES',len(non_submission))
