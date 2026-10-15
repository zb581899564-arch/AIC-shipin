"""Final local submission bytes/CRC/source/geometry audit; no model invocation."""
import hashlib,json,shutil,zipfile
from fractions import Fraction
from pathlib import Path
H=Path(__file__).resolve().parent;PROJECT=H.parent.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    src=H/'contest_results/rematch_01/candidate_IMAGE_SCORE_237STEP_8B.zip'
    receipt=json.loads((src.parent/'package_receipt.json').read_text());assert sha(src)==receipt['zip_sha256'] and src.stat().st_size==receipt['zip_bytes']
    metadata=PROJECT/'reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller/pts_v4_scan_01/clean_manifest_v2.json'
    assert sha(metadata)=='ceb91ee9434ce3de6a55abf727e613b83368b547d3be3d1e71b46414c2f019f8'
    m={r['video_id']:r for r in json.loads(metadata.read_text(encoding='utf-8-sig'))['records']};assert len(m)==426
    with zipfile.ZipFile(src) as z:
        assert z.namelist()==['predictions.jsonl'] and z.testzip() is None;raw=z.read('predictions.jsonl')
    records=[json.loads(s) for s in raw.decode('utf-8-sig').splitlines() if s.strip()]
    assert len(records)==426 and len({r['video_id'] for r in records})==426 and {r['video_id'] for r in records}==set(m)
    total=0
    for r in records:
        source=m[r['video_id']];assert set(r)=={'video_id','targetRatioWH','predictions'} and r['targetRatioWH']==source['targetRatioWH']
        previous=-1;tw,th=r['targetRatioWH']
        for p in r['predictions']:
            assert set(p)=={'frame','bboxes'} and type(p['frame']) is int and previous<p['frame']<source['n_frames'];previous=p['frame']
            box=p['bboxes'];assert len(box)==3 and all(type(v) is int for v in box)
            x,y,w=box;h=Fraction(w*th,tw)
            assert x>=0 and y>=0 and w>0 and x+w<=source['width'] and y+h<=source['height'];total+=1
    assert total==receipt['selected_frames']
    independent=json.loads((src.parent/'independent_validation.json').read_text())
    assert hashlib.sha256(raw).hexdigest()==independent['predictions_sha256'] and all(independent['checks'].values())
    dest=PROJECT/'deliveries/ANNOTATION_ITERATION_20261010/NEW_237STEP_EXPERIMENTAL';dest.mkdir(parents=True,exist_ok=True)
    target=dest/src.name;assert not target.exists();shutil.copyfile(src,target);assert target.read_bytes()==src.read_bytes()
    actual=dict(receipt,local_candidate=str(target),local_zip_sha256=sha(target),local_crc_source_geometry_pass=True,
      historical_safe_candidate=str(PROJECT/'deliveries/ANNOTATION_ITERATION_20261010/SAFE_37_66/candidate_SAFE_37_66.zip'))
    with (dest/'acceptance.json').open('x') as f:json.dump(actual,f,indent=2)
    with (dest/'README.txt').open('x',encoding='utf-8') as f:f.write('本轮237步新微调image-score时间选择器实验包。426视频与11strict/CRC/源帧/框几何验收通过。官网分未知，TVSum已见开发集代理不保证超过历史37.66；native代理F改善95区间跨0。原B生产与SAFE_37_66保底均保留。ZIP仅含predictions.jsonl，可手工提交；未代提交。\n')
    print(json.dumps({k:actual[k] for k in ('status','local_candidate','zip_bytes','zip_sha256','videos','selected_frames','empty_videos')}))
if __name__=='__main__':main()
