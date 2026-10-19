"""Verify the actual final archive received on Windows against Linux receipt."""
import hashlib,json,pathlib,sys,zipfile
ROOT=pathlib.Path('G:/ai/AIC视频')
BASE=ROOT/'deliveries/CONTEXT_SEMANTIC_RESIDUAL_8B_20261016/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip'
def read_zip(path):
    with zipfile.ZipFile(path) as z:
        assert z.namelist()==['predictions.jsonl'] and z.testzip() is None
        data=z.read('predictions.jsonl');rows=[json.loads(line) for line in data.splitlines() if line.strip()]
    assert len(rows)==426 and {r['video_id'] for r in rows}==set(map(str,range(426)))
    result={}
    for row in rows:
        assert row['predictions']
        frames=[]
        for pred in row['predictions']:
            key=(row['video_id'],pred['frame']);assert type(key[1]) is int and key not in result
            result[key]=pred['bboxes'];frames.append(key[1])
        assert frames==sorted(frames)
    canon=[{k:r[k] for k in ['video_id','targetRatioWH','predictions']} for r in sorted(rows,key=lambda r:r['video_id'])]
    return result,hashlib.sha256(data).hexdigest(),hashlib.sha256(json.dumps(canon,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
assert hashlib.sha256(BASE.read_bytes()).hexdigest()=='b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'
baseline,_,_=read_zip(BASE);assert len(baseline)==123506
path=pathlib.Path(sys.argv[1]);receipt=json.loads(pathlib.Path(sys.argv[2]).read_text(encoding='utf-8-sig'))
assert path.stat().st_size==receipt['zip']['bytes'] and hashlib.sha256(path.read_bytes()).hexdigest()==receipt['zip']['sha256']
boxes,member,canonical=read_zip(path)
assert member==receipt['member_sha256'] and canonical==receipt['canonical_sha256'] and len(boxes)==receipt['frames']
assert all(boxes.get(k)==v for k,v in baseline.items())
assert len(boxes.keys()-baseline.keys())==receipt['added_frames'] and receipt['removed_frames']==0
assert receipt['independent11strict'] and receipt['actual_resident_parameters']<=9_000_000_000
result=dict(status='PASS_WINDOWS_FINAL_ZIP_LINUX_SIZE_SHA_CRC_MEMBER_SHA426_ORIGINAL_BASELINE_FRAMES_BOXES',path=str(path.resolve()),bytes=path.stat().st_size,sha256=receipt['zip']['sha256'],canonical_sha256=canonical,frames=len(boxes),added_frames=receipt['added_frames'],removed_frames=0,records=426,baseline_kept=123506,official_score='UNKNOWN')
with path.with_name('windows_delivery_acceptance.json').open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result,ensure_ascii=False))
