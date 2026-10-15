"""Prepare reviewable fixed-source upload; does not perform network transfer."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,zipfile
ROOT=Path(__file__).resolve().parent
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
    return h.hexdigest()
planpath=ROOT.parent/'slot6_silver24_v1/source_window_plan.json'
plan=json.loads(planpath.read_text(encoding='utf-8-sig'))
sources=[s for role in plan['sources'].values() for s in role]
assert len(sources)==12 and len({s['media_sha256'] for s in sources})==12
out=ROOT/'source_transfer_v1';out.mkdir(exist_ok=False)
manifest=[]
for s in sources:
    p=Path(s['media_path']);assert p.stat().st_size==s['media_bytes'] and sha(p)==s['media_sha256']
    manifest.append(dict(source_id=s['source_id'],source_group=s['source_group'],local_path=str(p),archive_name=s['source_id']+'.mp4',bytes=s['media_bytes'],sha256=s['media_sha256']))
mp=out/'fixed12_sources_manifest.json'
mp.write_text(json.dumps(dict(plan_sha256=sha(planpath),fixed_denominator=24,sources=manifest),ensure_ascii=False,indent=2),encoding='utf-8')
zp=out/'fixed12_native_sources.zip'
with zipfile.ZipFile(zp,'x',compression=zipfile.ZIP_STORED,allowZip64=True) as z:
    z.write(mp,'fixed12_sources_manifest.json')
    for s in manifest:z.write(s['local_path'],s['archive_name'])
with zipfile.ZipFile(zp) as z:
    assert z.testzip() is None and set(z.namelist())=={'fixed12_sources_manifest.json'}|{s['archive_name'] for s in manifest}
    for s in manifest:assert hashlib.sha256(z.read(s['archive_name'])).hexdigest()==s['sha256']
receipt=dict(status='PASS_LOCAL_TRANSFER_ARTIFACT_NOT_UPLOADED',utc=datetime.now(timezone.utc).isoformat(),path=str(zp),bytes=zp.stat().st_size,sha256=sha(zp),manifest_sha256=sha(mp),source_bytes=sum(s['bytes'] for s in manifest),source_count=12,contains_only_fixed24_source_videos_and_manifest=True,crc_and_all_source_sha_pass=True,uploaded=False,new_model_calls=0,new_optimizer_updates=0)
(out/'preparation_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False))
