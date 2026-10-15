"""Small derived external material transfer identity and safe extraction."""
import hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]/'reports/reliable_reference_20261012_v1'
kind=sys.argv[1]; expected=sys.argv[2]
zp=ROOT/(kind+'_material.zip');actual=hashlib.sha256(zp.read_bytes()).hexdigest()
assert actual==expected,(kind,'transfer SHA')
out=ROOT/(kind+'_materials');out.mkdir(exist_ok=False)
with zipfile.ZipFile(zp) as z:
 assert z.testzip() is None
 for n in z.namelist():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts and '\\' not in n
 z.extractall(out)
receipt=json.loads((out/'preparation_receipt.json').read_text())
for r in receipt['records']:
 m=json.loads((out/r['case_id']/'observations.json').read_text());assert m==r
 for s in r['sheets']:
  p=out/s['path'];assert p.stat().st_size==s['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==s['sha256']
result=dict(status='PASS_TRANSFER_CRC_SIZE_SHA_MEMBER_IDENTITY',bytes=zp.stat().st_size,sha256=actual,sources=len(receipt['records']),observations=sum(len(r['observations']) for r in receipt['records']),pages=sum(len(r['sheets']) for r in receipt['records']))
with (ROOT/(kind+'_local_acceptance.json')).open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
print(json.dumps(result))
