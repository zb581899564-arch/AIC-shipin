"""Deploy only the independent remaining-package CPU code and immutable bindings."""
from pathlib import Path
import ast
import hashlib
import json
import subprocess
import zipfile

W = Path(__file__).resolve().parents[2]
R = Path(__file__).resolve().parent
ROOT = '/home/inspur/aic_video_work/midnight_five_verify40_46_20261015_v1'
names = ['package_five.py', 'package_math.py', 'production_evidence.py',
         'supplement_quality.py', 'finalize_supplement.py']
files = {'pair_supplement_package_code_v1/' + name:
         W / 'improvement/midnight_pair_supplement_package_v1' / name for name in names}
for path in files.values():
    ast.parse(path.read_text(encoding='utf8'))
manifest = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in files.items()}
archive = R / 'pair_package_control_25.zip'
with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as z:
    for name, path in files.items():
        z.write(path, name)
    z.writestr('manifest.json', json.dumps(manifest))
size, digest = archive.stat().st_size, hashlib.sha256(archive.read_bytes()).hexdigest()
subprocess.run(['scp', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=12', str(archive),
    'aic-inspur-tailscale:' + ROOT + '/' + archive.name], capture_output=True, check=True)
code = f'''from pathlib import Path
import datetime as dt,hashlib,json,socket,zipfile
r=Path({ROOT!r}); p=r/{archive.name!r}
assert socket.gethostname()=='inspur-NP5570M5'
assert p.stat().st_size=={size} and hashlib.sha256(p.read_bytes()).hexdigest()=={digest!r}
assert not (r/'pair_supplement_package_code_v1').exists()
assert not (r/'packages/package_REDUNDANT').exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ref=lambda p:dict(path=str(p),sha256=sha(p))
read=lambda p:json.loads(p.read_text())
def save(p,d):
 with p.open('x') as f:json.dump(d,f,indent=2)
original_inputs=ref(r/'package_inputs.json'); original_quality=ref(r/'quality_admission.json')
assert original_inputs['sha256']=='54eecb2b7e1f062066e9e05611375cd25e1abb9aa30cc9edfda519a1ebbea12d'
assert original_quality['sha256']=='5b15615bd5000adcbe55b87908d0a1e5d0babd7d973ccfdc3ff9ff76a7660e38'
q=read(r/'quality_admission.json')['arms']['REDUNDANT']
assert q['status']=='FAILED_FIXED_NEW_CONFIRMATION' and q['confirmation_ref']==ref(r/'relative_confirm/policy_fresh_comparison.json')
with zipfile.ZipFile(p) as z:
 assert z.testzip() is None
 m=json.loads(z.read('manifest.json')); assert set(z.namelist())==set(m)|{{'manifest.json'}}
 for name,d in m.items():
  assert not Path(name).is_absolute() and '..' not in Path(name).parts and hashlib.sha256(z.read(name)).hexdigest()==d
  target=r/name; assert target.resolve().is_relative_to(r); target.parent.mkdir(parents=True,exist_ok=True)
  with target.open('xb') as f:f.write(z.read(name))
history=read(r/'delivery_history_13.json'); records=list(history['records']); assert len(records)==21
existing=[]
for arm in ['ACTION','REACTION','INFORMATION','ORDINARY']:
 path=r/'packages'/('package_'+arm)/'completion.json'; d=read(path); zp=Path(d['zip'])
 assert d['arm']==arm and d['records']==426 and d['independent11strict'] is True
 assert zp.stat().st_size==d['bytes'] and sha(zp)==d['SHA256']
 existing.append(ref(path))
 records.append(dict(filename=zp.name,ZIP_SHA256=d['SHA256'],canonical_SHA256=d['canonical_SHA256'],zip_ref=dict(path=str(zp),sha256=d['SHA256']),source_receipt_ref=ref(path)))
assert len(records)==25 and len({{v['canonical_SHA256'] for v in records}})==23
history_path=r/'delivery_history_pair_supplement_25.json'
save(history_path,dict(schema='EXACT_25_REGISTERED_DELIVERIES_23_CANONICAL_IDENTITIES',records=records,original_history_ref=ref(r/'delivery_history_13.json'),existing_four_package_refs=existing,only_duplicate_prevention_not_quality_evaluation=True))
deployment=dict(status='INDEPENDENT_REMAINING_PAIR_CPU_CODE_FROZEN_NO_PACKAGE_OR_MODEL',control_bytes={size},control_SHA256={digest!r},
 code_files={{str(r/n):d for n,d in m.items()}},original_package_inputs_ref=original_inputs,original_quality_admission_ref=original_quality,
 original_nonapplicable_confirmation_ref=q['confirmation_ref'],history_ref=ref(history_path),existing_four_package_refs=existing,
 new_model_calls=0,new_packages=0,old_results_changed=False,UTC=dt.datetime.now(dt.timezone.utc).isoformat())
save(r/'pair_supplement_package_deployment_25.json',deployment)
print(json.dumps(deployment))
'''
result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=12',
    'aic-inspur-tailscale', 'python3', '-'], input=code, capture_output=True, text=True)
receipt = dict(exit=result.returncode, stdout=result.stdout, stderr=result.stderr[-3000:])
with (R / 'pair_package_deployment_25_result.json').open('x', encoding='utf8') as stream:
    json.dump(receipt, stream, ensure_ascii=False, indent=2)
print(result.stdout)
print(result.stderr[-1500:])
result.check_returncode()
