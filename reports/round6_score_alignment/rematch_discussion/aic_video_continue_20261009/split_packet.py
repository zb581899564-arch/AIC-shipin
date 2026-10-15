"""Lossless MD volumes for a site's attachment failure; no UI or model calls."""
from pathlib import Path
import hashlib, json, sys
root = Path(__file__).resolve().parent
source = root / (sys.argv[1] if len(sys.argv) > 1 else 'context-r00.md')
data = source.read_text(encoding='utf-8')
lines = data.splitlines(keepends=True)
chunks, block, size = [], [], 0
for line in lines:
    if block and size + len(line.encode()) > 62000:
        chunks.append(''.join(block)); block = []; size = 0
    block.append(line); size += len(line.encode())
if block: chunks.append(''.join(block))
refs=[]
for i, chunk in enumerate(chunks, 1):
    p=root / f'{source.stem}-volume-{i:02d}.md'
    with p.open('x',encoding='utf-8',newline='') as f: f.write(chunk)
    refs.append({'file':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
assert b''.join((root/r['file']).read_bytes() for r in refs)==source.read_bytes()
index=root/f'{source.stem}-index.md'
with index.open('x',encoding='utf-8') as f:
    f.write('# 完整MD分卷索引\n\n任务 AIC-VIDEO-REMATCH-NEXT-20261005。接续20261009。\n\n'
            '按编号连接全部卷可逐字节还原完整原信息包；分卷在原始换行处切开，代码围栏可能跨卷，不能只读索引。'
            '没有删减任何上下文。原包SHA256 '+hashlib.sha256(source.read_bytes()).hexdigest()+'\n\n'+json.dumps(refs,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'index':str(index),'volumes':refs,'lossless':True},ensure_ascii=False))
