from pathlib import Path
import json,hashlib
OUT=Path(__file__).resolve().parents[1]/'round6_score_alignment/rematch_discussion/aic_video_empty407_20261010'
full=(OUT/'context-final.md').read_bytes();parts=[];buf=b''
for line in full.splitlines(keepends=True):
    if buf and len(buf)+len(line)>240000:parts.append(buf);buf=b''
    buf+=line
if buf:parts.append(buf)
assert b''.join(parts)==full and len(parts)<=7
rows=[]
for i,data in enumerate(parts,1):
    p=OUT/f'context-final-wide-part{i:02d}.md'
    with p.open('xb') as f:f.write(data)
    rows.append(dict(file=p.name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
meta=dict(full_bytes=len(full),full_sha256=hashlib.sha256(full).hexdigest(),parts=rows,actual_concat_exact=True)
with (OUT/'context-final-wide-index.md').open('x',encoding='utf-8') as f:f.write('# EMPTY407_FINAL 完整宽卷\n\n8附件限制下完整重分卷，原完整context-final原字节不变。只依序读取本wide索引和wide-part01至末卷，至END_EMPTY407_FINAL。未删摘要或源码。\n\n'+json.dumps(meta,ensure_ascii=False,indent=2))
print(json.dumps(meta,ensure_ascii=False))
