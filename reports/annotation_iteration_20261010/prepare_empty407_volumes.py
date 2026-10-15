from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parents[2]
out=root/'reports/round6_score_alignment/rematch_discussion/aic_video_empty407_20261010'
body=(out/'context-r00.md').read_text()
# Preserve every JSON value. Only layout is compacted, not evidence omitted.
for p in (root/'reports/annotation_iteration_20261010/quality_result.json',root/'reports/annotation_iteration_20261010/annotation_summary.json'):
    old=p.read_text(encoding='utf-8-sig')
    compact=json.dumps(json.loads(old),ensure_ascii=False,separators=(',',':'))
    assert json.loads(old)==json.loads(compact)
    assert body.count(old)==1
    body=body.replace(old,compact)
body=body.replace('r00完整业务包。','r00b完整业务包；数值JSON仅压缩空白，所有值和代码完整保留。')
body=body.replace('END_EMPTY407_R00','END_EMPTY407_R00B')
path=out/'context-r00b.md'
with path.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
def parts(path):
    content=path.read_text(); lines=content.splitlines(keepends=True);chunks=[];current=''
    for line in lines:
        if current and len((current+line).encode())>105000:chunks.append(current);current=''
        current+=line
    if current:chunks.append(current)
    assert ''.join(chunks)==content
    manifest=[]
    for i,chunk in enumerate(chunks,1):
        target=path.with_name(path.stem+f'-part{i:02}.md')
        with target.open('x',encoding='utf-8',newline='\n') as f:f.write(chunk)
        raw=target.read_bytes();manifest.append({'file':target.name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
    raw=path.read_bytes();meta={'full_file':path.name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'parts':manifest,'parts_concat_exact':True}
    index=path.with_name(path.stem+'-index.md')
    with index.open('x',encoding='utf-8') as f:f.write('# 完整分卷索引\n\nJSON只移除格式空白，所有值均保留；按序拼接分卷与完整文件原字节完全一致。必须完整读取所有分卷，不得以索引或末标冒充完整读取。\n\n```json\n'+json.dumps(meta,ensure_ascii=False,indent=2)+'\n```\n')
    print(json.dumps(meta,ensure_ascii=False));return meta
if __name__=='__main__':parts(path)
