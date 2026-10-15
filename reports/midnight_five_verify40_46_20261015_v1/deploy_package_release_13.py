"""Freeze publication mapping and final CPU packaging code; no package/model yet."""
from pathlib import Path
import ast,hashlib,json,subprocess,zipfile
W=Path(__file__).resolve().parents[2];R=Path(__file__).resolve().parent
ROOT='/home/inspur/aic_video_work/midnight_five_verify40_46_20261015_v1'
files={'package_code_v2/'+n:W/'improvement/midnight_five_package_v1'/n for n in ['package_five.py','package_math.py','production_evidence.py']}
files['windows_existing_delivery_history_12.json']=R/'windows_existing_delivery_history_12.json'
for p in files.values():
    if p.suffix=='.py':ast.parse(p.read_text(encoding='utf8'))
manifest={n:hashlib.sha256(p.read_bytes()).hexdigest() for n,p in files.items()}
archive=R/'package_release_control_13.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
    for n,p in files.items():z.write(p,n)
    z.writestr('manifest.json',json.dumps(manifest))
size=archive.stat().st_size;digest=hashlib.sha256(archive.read_bytes()).hexdigest()
subprocess.run(['scp','-o','BatchMode=yes','-o','ConnectTimeout=12',str(archive),'aic-inspur-tailscale:'+ROOT+'/'+archive.name],check=True,capture_output=True)
code=f'''from pathlib import Path
import json,hashlib,zipfile,datetime as dt
r=Path({ROOT!r});p=r/{archive.name!r};assert p.stat().st_size=={size} and hashlib.sha256(p.read_bytes()).hexdigest()=={digest!r}
with zipfile.ZipFile(p) as z:
 assert z.testzip() is None;m=json.loads(z.read('manifest.json'));assert set(z.namelist())==set(m)|{{'manifest.json'}}
 for n,d in m.items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts and hashlib.sha256(z.read(n)).hexdigest()==d
  f=r/n;f.parent.mkdir(parents=True,exist_ok=True)
  with f.open('xb') as h:h.write(z.read(n))
ref=lambda p:dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
read=lambda p:json.loads(p.read_text())
o=r.parent/'twenty_hour_five_20261014_v1/temporal_family_native_package_v3'
old_inputs=read(o/'package_inputs.json');old_history=read(Path(old_inputs['history']['path']))
assert hashlib.sha256(Path(old_inputs['history']['path']).read_bytes()).hexdigest()==old_inputs['history']['sha256']
records=list(old_history)
for p in sorted(o.glob('package_*/completion.json')):
 d=read(p);assert d['arm'] in ['START','END','BOTH','VERIFY','VERIFY_BOTH']
 records.append(dict(filename=Path(d['zip']).name,ZIP_SHA256=d['SHA256'],canonical_SHA256=d['canonical_SHA256'],zip_ref=dict(path=d['zip'],sha256=d['SHA256']),source_receipt_ref=ref(p)))
local=read(r/'windows_existing_delivery_history_12.json')
assert len(local['records'])==21 and len(records)==21
assert {{v['canonical_SHA256'] for v in local['records']}}<={{v['canonical_SHA256'] for v in records}}
history=dict(schema='COMPLETE_REGISTERED_DELIVERY_IDENTITY_HISTORY_21_V1',records=records,Windows_actual_inventory_ref=ref(r/'windows_existing_delivery_history_12.json'),only_duplicate_prevention_not_quality_evaluation=True)
with (r/'delivery_history_13.json').open('x') as f:json.dump(history,f,indent=2)
selection=read(r/'policy_comparison_08_selection.json')
selected=selection.get('selected_policies');assert selected==['ALL_WINDOW_WORST','PAIR_ONLY'],selection
protocol=dict(schema='MIDNIGHT_FIVE_PUBLICATION_FROZEN_POLICY_MAPPING_V1',arms=['ORDINARY','REDUNDANT','ACTION','REACTION','INFORMATION'],
 deletion_application_policy=dict(ORDINARY='WORST_ALL',REDUNDANT='WORST_PAIR_ONLY'),development_selection_ref=ref(r/'policy_comparison_08_selection.json'),policy_protocol_ref=ref(r/'policy_protocol_07.json'),
 original_model_prompt_protocol_ref=ref(r/'relative_protocol_03.json'),risk_arms=['ACTION','REACTION','INFORMATION'],risk_effect_quality_screening=False,
 empty_source_guard='PRESERVE_ORIGINAL_VERIFY40_46_SOURCE_SELECTION',test_content_or_leaderboard_parameter_selection=False,
 original_baseline_ZIP_unchanged=True,retained_original_frame_boxes_unchanged=True,actual_model_parsed_unchanged=True,
 independent_new_confirmation_required_for_each_deletion_policy=True,policy_map_fixed_before_first_fresh_model_or_quality_result=True,
 actual_parameters=8782459120,publication_limit=5,deadline_UTC='2026-10-15T16:00:00Z',UTC=dt.datetime.now(dt.timezone.utc).isoformat())
assert not (r/'relative_confirm_rank_10/completion.json').exists(),'Must freeze publication map before first new confirmation metrics'
with (r/'publication_protocol_13.json').open('x') as f:json.dump(protocol,f,indent=2)
receipt=dict(status='FINAL_CPU_PACKAGE_CODE_AND_PUBLICATION_MAPPING_FROZEN_NOT_PACKAGED',control_bytes={size},control_SHA256={digest!r},code_files={{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'package_code_v2').glob('*.py')}},history_ref=ref(r/'delivery_history_13.json'),protocol_ref=ref(r/'publication_protocol_13.json'),new_model_calls=0,new_packages=0,UTC=protocol['UTC'])
with (r/'package_release_deployment_13.json').open('x') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt))
'''
res=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','aic-inspur-tailscale','python3','-'],input=code,text=True,capture_output=True)
print(res.stdout);print(res.stderr[-3000:])
with (R/'package_release_deployment_13_result.json').open('x',encoding='utf8') as f:json.dump(dict(exit=res.returncode,stdout=res.stdout,stderr=res.stderr[-3000:]),f,indent=2)
res.check_returncode()
