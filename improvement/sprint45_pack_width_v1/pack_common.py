"""CPU package contracts; no launcher or model call."""
import hashlib
import json
from pathlib import Path

TOTAL=8782590234
BASELINE='b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'
HEAD='0a1cb13e90e48da1a349bf9dfba9f2beca7e9fbc8487ec3451c4148a92e3c954'
NORM='df64d309fed205402bff5429ad367ab5bf7ad366715d45a7fac407127ec032aa'
SOURCE='QWEN_BASE_LM_WIDTH_HEAD_SAME_SHOT'


def require(ok,message):
    if not ok:raise ValueError(message)


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def lines(path):return [json.loads(x) for x in Path(path).read_text(encoding='utf-8-sig').splitlines() if x.strip()]


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as handle:
        for part in iter(lambda:handle.read(8<<20),b''):h.update(part)
    return h.hexdigest()


def bound(ref):
    p=Path(ref['path']);require(p.is_absolute() and p.is_file() and sha(p)==ref['sha256'],'Changed/missing frozen file '+str(p));return p


def reference(path):return dict(path=str(Path(path).resolve()),sha256=sha(path))


def save(path,value):
    with Path(path).open('x',encoding='utf-8') as handle:json.dump(value,handle,ensure_ascii=False,indent=2,allow_nan=False);handle.write('\n')


def jsonlines(path,value):
    with Path(path).open('x',encoding='utf-8') as handle:
        for row in value:handle.write(json.dumps(row,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n')


def canonical(rows):
    values=[{k:r[k] for k in ('video_id','targetRatioWH','predictions')} for r in sorted(rows,key=lambda r:r['video_id'])]
    return hashlib.sha256(json.dumps(values,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def boxes(rows):
    result={(r['video_id'],p['frame']):p['bboxes'] for r in rows for p in r['predictions']}
    require(len(result)==sum(len(r['predictions']) for r in rows),'Duplicate selected prediction frame')
    return result
