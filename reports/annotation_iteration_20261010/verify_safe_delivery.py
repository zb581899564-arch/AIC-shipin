"""Independent local validation of the historical usable fallback, byte-exact copy."""
import hashlib,json,zipfile,shutil
from fractions import Fraction
from pathlib import Path
H=Path(__file__).resolve().parent;PROJECT=H.parent.parent
src=PROJECT/'deliveries/BALANCED_TWO_WINDOW_8B_20261009/candidate_BALANCED_TWO_WINDOW_8B.zip'
expected='07730c9e02e68d1a1ce54e7ef5a8aa616346cf8f2f8d78426ed36bc3eb481496'
manifest=PROJECT/'reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller/pts_v4_scan_01/clean_manifest_v2.json'
raw=src.read_bytes();assert len(raw)==306167 and hashlib.sha256(raw).hexdigest()==expected
assert hashlib.sha256(manifest.read_bytes()).hexdigest()=='ceb91ee9434ce3de6a55abf727e613b83368b547d3be3d1e71b46414c2f019f8'
m=json.loads(manifest.read_text(encoding='utf-8-sig'));lookup={r['video_id']:r for r in m['records']};assert len(lookup)==426
with zipfile.ZipFile(src) as z:
    assert z.namelist()==['predictions.jsonl'] and z.testzip() is None
    content=z.read('predictions.jsonl')
rows=[json.loads(s) for s in content.decode('utf-8').splitlines()]
assert len(rows)==426 and {r['video_id'] for r in rows}==set(lookup)
frames=0
for r in rows:
    assert set(r)=={'video_id','targetRatioWH','predictions'}
    meta=lookup[r['video_id']];assert r['targetRatioWH']==meta['targetRatioWH']
    ratio=Fraction(str(r['targetRatioWH'][1]))/Fraction(str(r['targetRatioWH'][0]))
    previous=-1
    for item in r['predictions']:
        assert set(item)=={'frame','bboxes'}
        frame=item['frame'];assert type(frame) is int and previous<frame<meta['n_frames'];previous=frame
        box=item['bboxes'];assert type(box) is list and len(box)==3 and all(type(x) is int for x in box)
        x,y,w=box;h=w*ratio
        assert x>=0 and y>=0 and w>0 and x+w<=meta['width'] and y+h<=meta['height']
        frames+=1
assert frames==102112
dest=PROJECT/'deliveries/ANNOTATION_ITERATION_20261010/SAFE_37_66'
dest.mkdir(parents=True,exist_ok=True);target=dest/'candidate_SAFE_37_66.zip'
if target.exists():assert target.read_bytes()==raw
else:shutil.copyfile(src,target)
assert target.read_bytes()==raw
report={'status':'PASS_CURRENT_LOCAL_426_NATIVE_SCHEMA_CRC_AND_EXACT_HISTORICAL_COPY','zip':str(target),'bytes':len(raw),
        'sha256':expected,'video_records':426,'prediction_frames':frames,'predictions_sha256':hashlib.sha256(content).hexdigest(),
        'historical_user_reported_score':37.66,'new_training_package':False,'new_official_submission':False,
        'manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),'prior_independent_provenance_validation_preserved':True}
with (dest/'acceptance.json').open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
(dest/'README.txt').write_text('这是已提交并由用户反馈37.66的历史包，原字节保留，本轮再次核验426身份/帧/框/CRC/SHA。不是本轮新微调候选。新实验未达质量门时作为保底；无自动官网提交。\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
