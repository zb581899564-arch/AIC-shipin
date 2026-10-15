"""Targeted actual ZIP-row schema check; no video, inference or package write."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
code = (ROOT/'improvement/recall_expansion_verify40_46_v1/merge_keep.py').read_text(encoding='utf8')
script = r'''
import hashlib,json,pathlib,sys,types,zipfile
root=pathlib.Path('/home/inspur/aic_video_work/recall_expansion_verify40_46_20261014_v1')
sys.path.insert(0,str(root/'code'))
module=types.ModuleType('targeted_merge_format_17');sys.modules[module.__name__]=module
exec(compile(__SOURCE_LITERAL__,'targeted_merge_format_17','exec'),module.__dict__)
old=pathlib.Path('/home/inspur/aic_video_work/twenty_hour_five_20261014_v1/temporal_family_native_package_v3')
refs=json.loads((old/'package_inputs.json').read_text())
p=pathlib.Path(refs['metadata']['path']);b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==refs['metadata']['sha256']
meta=json.loads(b)['records'][0]
baseline=old/'package_VERIFY/candidate_TEMPORAL_VERIFY.zip'
assert hashlib.sha256(baseline.read_bytes()).hexdigest()=='86593725c6bad919dc0d342fe98ad65e489a13a6e492da5de3afd247a3226543'
with zipfile.ZipFile(baseline) as z:
 assert z.namelist()==['predictions.jsonl']
 with z.open('predictions.jsonl') as stream:line=stream.readline()
row=json.loads(line);assert row['video_id']==meta['video_id']
records=module.baseline_records(line,{meta['video_id']:{'source':meta}})
assert len(records)==1 and records[0]['original_line']==line and records[0]['model_params_bytes']==b'8.78245912'
print(json.dumps(dict(status='PASS_TARGETED_ACTUAL_BASELINE_ROW_SCHEMA_COMPATIBILITY_NOT_PRODUCTION_QA',
 baseline_zip_sha256='86593725c6bad919dc0d342fe98ad65e489a13a6e492da5de3afd247a3226543',
 merge_source_sha256=hashlib.sha256(__SOURCE_LITERAL__.encode()).hexdigest(),
 actual_first_row_keys=list(row),model_params_bytes_preserved=True,
 inspected_record_count=1,new_model_calls=0,media_decodes=0,new_output_predictions=0,
 production_or_full426_QA_performed=False)))
'''.replace('__SOURCE_LITERAL__', repr(code))
result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=12',
                         'aic-inspur-home', 'python3 -'], input=script, capture_output=True,
                        text=True, encoding='utf8', timeout=30)
if result.returncode:
    raise RuntimeError(result.stderr)
value = json.loads(result.stdout)
target = Path(__file__).with_name('merge_actual_schema_acceptance_17.json')
with target.open('x', encoding='utf8') as stream:
    json.dump(value, stream, ensure_ascii=False, indent=2)
print(json.dumps(value))
