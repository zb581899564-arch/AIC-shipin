"""Mac-jump small metadata only; reuse existing local tokenizer by actual SHA."""
from pathlib import Path
import json,hashlib,subprocess,shutil
HERE=Path(__file__).resolve().parent/'slot6_silver24_v1'
OLD=HERE.parents[1]/'qwen8b_annotation_20261009_v1/training_v2/processor_snapshot'
PY='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
code='''from pathlib import Path
import json,hashlib,platform
p=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/models/Qwen3-VL-8B-Instruct')
names=('config.json','preprocessor_config.json','video_preprocessor_config.json','processor_config.json','tokenizer_config.json','tokenizer.json','vocab.json','merges.txt','chat_template.json','chat_template.jinja','added_tokens.json','special_tokens_map.json')
rows=[]
for name in names:
 f=p/name
 if f.is_file():
  b=f.read_bytes();rows.append(dict(file=name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),text=b.decode() if len(b)<=65536 else None))
print(json.dumps(dict(host=platform.node(),rows=rows)))
'''
proc=subprocess.run(['ssh','-J','macmini','aic-inspur-home',PY,'-B','-'],input=code,encoding='utf-8',capture_output=True,timeout=60)
assert proc.returncode==0,proc.stderr
d=json.loads(proc.stdout);assert d['host']=='inspur-NP5570M5'
target=HERE/'actual_processor_snapshot';target.mkdir(exist_ok=False)
for row in d['rows']:
    p=target/row['file']
    if row['text'] is not None:
        with p.open('xb') as f:f.write(row['text'].encode())
    else:
        old=OLD/row['file'];assert old.is_file() and hashlib.sha256(old.read_bytes()).hexdigest()==row['sha256'], 'Existing tokenizer identity differs; do not download or silently substitute'
        shutil.copy2(old,p)
    assert p.stat().st_size==row['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
with (HERE/'actual_processor_binding.json').open('x',encoding='utf-8') as f:json.dump(dict(status='PASS_REAL_LINUX_METADATA_AND_LOCAL_TOKENIZER_SHA_BINDING',
    route='ssh -J macmini aic-inspur-home; small JSON/Jinja metadata and SHA only',bytes_from_remote=len(proc.stdout.encode()),
    rows=[{k:v for k,v in row.items() if k!='text'} for row in d['rows']],weights_downloaded=False,linux_processor_execution=False),f,indent=2)
print(json.dumps(dict(status='PASS_REAL_LINUX_METADATA_AND_LOCAL_TOKENIZER_SHA_BINDING',files=len(d['rows']),bytes_from_remote=len(proc.stdout.encode()),weights_downloaded=False)))
