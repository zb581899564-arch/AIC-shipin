"""One small deployment and CPU-only engineering preview; not risk publication."""
from pathlib import Path
import ast
import hashlib
import json
import subprocess
import zipfile

W = Path(__file__).resolve().parents[2]
R = Path(__file__).resolve().parent
ROOT = '/home/inspur/aic_video_work/midnight_five_verify40_46_20261015_v1'
source = W / 'improvement/midnight_semantic_union_review_v1/preview_union.py'
ast.parse(source.read_text(encoding='utf8'))
name = 'semantic_union_review_code_v1/preview_union.py'
manifest = {name: hashlib.sha256(source.read_bytes()).hexdigest()}
archive = R / 'semantic_union_review_control_27.zip'
with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as z:
    z.write(source, name)
    z.writestr('manifest.json', json.dumps(manifest))
size, digest = archive.stat().st_size, hashlib.sha256(archive.read_bytes()).hexdigest()
remote = f'''from pathlib import Path
import datetime as dt,hashlib,json,os,shutil,socket,subprocess,zipfile
r=Path({ROOT!r});p=r/{archive.name!r}
assert socket.gethostname()=='inspur-NP5570M5'
assert p.stat().st_size=={size} and hashlib.sha256(p.read_bytes()).hexdigest()=={digest!r}
assert not (r/'semantic_union_review_code_v1').exists() and not (r/'semantic_union_review_27').exists()
assert not (r/'semantic_union_review_launch_27.json').exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ref=lambda p:dict(path=str(p),sha256=sha(p))
read=lambda p:json.loads(p.read_text())
def save(p,d):
 with p.open('x') as f:json.dump(d,f,indent=2)
original=read(r/'package_inputs.json')
assert sha(r/'package_inputs.json')=='54eecb2b7e1f062066e9e05611375cd25e1abb9aa30cc9edfda519a1ebbea12d'
assert sha(r/'quality_admission.json')=='5b15615bd5000adcbe55b87908d0a1e5d0babd7d973ccfdc3ff9ff76a7660e38'
current=[ref(r/'packages'/('package_'+arm)/'completion.json') for arm in ['ACTION','REACTION','INFORMATION','ORDINARY']]
source_refs=current[:3]
history=read(r/'delivery_history_pair_supplement_25.json')
assert len(history['records'])==25 and len({{v['canonical_SHA256'] for v in history['records']}})==23
with zipfile.ZipFile(p) as z:
 assert z.testzip() is None
 m=json.loads(z.read('manifest.json')); assert set(z.namelist())==set(m)|{{'manifest.json'}}
 for n,d in m.items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts and hashlib.sha256(z.read(n)).hexdigest()==d
  target=r/n;assert target.resolve().is_relative_to(r);target.parent.mkdir(parents=True,exist_ok=True)
  with target.open('xb') as f:f.write(z.read(n))
codes={{str(r/n):d for n,d in m.items()}}
for n in ['production_evidence.py','package_math.py']:
 q=r/'package_code_v2'/n; assert original['code_files'][str(q)]==sha(q);codes[str(q)]=sha(q)
inputs=dict(publication_authorized=False,scope='PROPOSED_FOURTH_RISK_CPU_ENGINEERING_REVIEW_ONLY',
 source_package_completion_refs=source_refs,current_four_package_refs=current,
 original_package_inputs_ref=ref(r/'package_inputs.json'),protected_baseline_zip_ref=original['protected_baseline_zip_ref'],
 history_ref=ref(r/'delivery_history_pair_supplement_25.json'),code_files=codes,
 maximum_previously_authorized_risk_count=3,proposed_risk_count=4,quality_screening=False,
 union_rule='UNWEIGHTED_EXACT_NATIVE_KEY_UNION_OF_ACTION_REACTION_INFORMATION_ONLY',
 no_new_model_or_input_processing=True,old_failed_quality_results_unchanged=True,UTC=dt.datetime.now(dt.timezone.utc).isoformat())
save(r/'semantic_union_review_inputs_27.json',inputs)
bytes_in=sum((Path(v['path']).parent/n).stat().st_size for v in source_refs for n in ['predictions.jsonl','selected.jsonl','provenance.jsonl','metadata.json'])
mem=Path('/proc/meminfo').read_text();available=int(next(s for s in mem.splitlines() if s.startswith('MemAvailable:')).split()[1])*1024
assert shutil.disk_usage(r).free>bytes_in and available>8*bytes_in
save(r/'semantic_union_review_preflight_27.json',dict(host=socket.gethostname(),UTC=dt.datetime.now(dt.timezone.utc).isoformat(),meminfo=mem,
 disk=dict(zip(('total','used','free'),shutil.disk_usage(r))),actual_source_artifact_bytes=bytes_in,estimated_python_memory_bound_bytes=8*bytes_in,
 capacity_reason='Bounded JSON union only, no tensors or model allocation; estimates scale from actual accepted component sizes',
 actual_processes=subprocess.run(['ps','-eo','pid,ppid,stat,pcpu,pmem,args'],capture_output=True,text=True,check=True).stdout,
 CUDA_VISIBLE_DEVICES='',no_external_process_changes=True))
argv=[str(r.parent/'env/qwen3vl_isolated_20260910/bin/python'),'-B',str(r/{name!r})]
with (r/'semantic_union_review_27.log').open('x') as log:
 child=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
  env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
 proc=Path('/proc')/str(child.pid)
 launch=dict(pid=child.pid,start_ticks=(proc/'stat').read_text().split()[21],argv=argv,actual_cmdline=[v.decode() for v in (proc/'cmdline').read_bytes().split(bytes([0])) if v],
  UTC=dt.datetime.now(dt.timezone.utc).isoformat(),CPU_only=True,publication_authorized=False,control_bytes={size},control_SHA256={digest!r},inputs_ref=ref(r/'semantic_union_review_inputs_27.json'),
  no_new_model_calls=True,automatic_retry=False)
save(r/'semantic_union_review_launch_27.json',launch)
print(json.dumps(launch))
'''
ast.parse(remote)
subprocess.run(['scp', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=12', str(archive),
    'aic-inspur-tailscale:' + ROOT + '/' + archive.name], check=True, capture_output=True)
result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=12',
    'aic-inspur-tailscale', 'python3', '-'], input=remote, text=True, capture_output=True)
with (R / 'union_review_launch_27_receipt.json').open('x', encoding='utf8') as f:
    json.dump(dict(exit=result.returncode, stdout=result.stdout, stderr=result.stderr[-3000:]), f, ensure_ascii=False, indent=2)
print(result.stdout)
print(result.stderr[-1500:])
result.check_returncode()
