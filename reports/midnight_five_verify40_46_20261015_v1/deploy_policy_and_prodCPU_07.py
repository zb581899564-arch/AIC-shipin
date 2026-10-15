"""New metadata policies and frozen-vision/new-token production CPU preparation."""
from pathlib import Path
import ast,hashlib,json,subprocess,zipfile
W=Path(__file__).resolve().parents[2];R=Path(__file__).resolve().parent
ROOT='/home/inspur/aic_video_work/midnight_five_verify40_46_20261015_v1';PY='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
dest=W/'improvement/midnight_production_runtime_v2';dest.mkdir(exist_ok=False)
for p in (W/'improvement/midnight_relative_runtime_v1').glob('*.py'):(dest/p.name).write_text(p.read_text(encoding='utf8'),encoding='utf8')
(dest/'composed_input.py').write_text((W/'improvement/midnight_five_runtime_v1/composed_input.py').read_text(encoding='utf8'),encoding='utf8')
p=dest/'stages.py';s=p.read_text(encoding='utf8')
old="root,reg=setup(stage);requests=read(checked(reg['requests_ref']))['entries'];out=root/'cpu_01';out.mkdir(exist_ok=False)"
new="""root,reg=setup(stage)
    if reg.get('input_QA_mode')=='ADOPT_FROZEN_VISION_COMPOSE_NEW_TOKENS':
        from composed_input import prepare_composed
        return prepare_composed(root,reg)
    requests=read(checked(reg['requests_ref']))['entries'];out=root/'cpu_01';out.mkdir(exist_ok=False)"""
assert s.count(old)==1;s=s.replace(old,new)
old="entries=entries,unique_gpu_terminal_ref=ref(resource),reference_labels_in_inference=False,old_successful_calls_repeated=0)"
new="entries=entries,structural_skips=read(checked(reg['requests_ref'])).get('structural_skips',[]),unique_gpu_terminal_ref=ref(resource),reference_labels_in_inference=False,old_successful_calls_repeated=0,original_vision_QA_adopted=True)"
assert s.count(old)==1;s=s.replace(old,new);p.write_text(s,encoding='utf8')
p=dest/'controller.py';s=p.read_text(encoding='utf8');old="        command([str(PY),'-B',script,'prepare','--stage',stage],cpu,'cpu.log')"
new="""        if reg.get('cpu_prepared_separately'):
            accepted=read(root/'cpu_01/completion.json')
            require(accepted['status']=='PASS_ALL_FIRST_INPUT_QA' and accepted['registration_ref']==ref(root/'registration.json') and accepted['actual_count']==len(read(checked(reg['requests_ref']))['entries']),'Actual separately completed CPU/registration denominator required')
        else:
            command([str(PY),'-B',script,'prepare','--stage',stage],cpu,'cpu.log')"""
assert s.count(old)==1;p.write_text(s.replace(old,new),encoding='utf8')
files={}
for p in dest.glob('*.py'):files['production_code_v2/'+p.name]=p
for p in (W/'improvement/midnight_five_reference_v1').glob('*.py'):files['reference_code_v3/'+p.name]=p
for p in (W/'improvement/midnight_five_reference_v1/confirm_runtime').glob('*.py'):files['relative_confirm/code/'+p.name]=p
for n in ['confirm_media.py','reference_common.py']:files['relative_confirm/media_code/'+n]=W/'improvement/midnight_five_reference_v1'/n
for p in (W/'improvement/midnight_five_package_v1').glob('*.py'):files['package_code/'+p.name]=p
files['relative_confirm/provider_prefix.json']=R/'provider_prefix_06.json'
files['relative_confirm/original_id_export.json']=W/'reports/recall_expansion_verify40_46_20261014_v1/new8_identity_selection_metadata_01.json'
for name,p in files.items():
 if p.suffix=='.py':ast.parse(p.read_text(encoding='utf8'))
manifest={name:hashlib.sha256(p.read_bytes()).hexdigest() for name,p in files.items()}
archive=R/'policy_and_prodCPU_control_07.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
 for n,p in files.items():z.write(p,n)
 z.writestr('manifest.json',json.dumps(manifest))
size=archive.stat().st_size;digest=hashlib.sha256(archive.read_bytes()).hexdigest()
subprocess.run(['scp','-o','BatchMode=yes','-o','ConnectTimeout=12',str(archive),'aic-inspur-home:'+ROOT+'/'+archive.name],check=True,capture_output=True)
code=f'''from pathlib import Path
import json,zipfile,hashlib,subprocess,os,datetime as dt
r=Path({ROOT!r});p=r/{archive.name!r}
assert p.stat().st_size=={size} and hashlib.sha256(p.read_bytes()).hexdigest()=={digest!r}
with zipfile.ZipFile(p) as z:
 assert z.testzip() is None;m=json.loads(z.read('manifest.json'));assert set(z.namelist())==set(m)|{{'manifest.json'}}
 for n,d in m.items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts and hashlib.sha256(z.read(n)).hexdigest()==d
  f=r/n;f.parent.mkdir(parents=True,exist_ok=True)
  with f.open('xb') as h:h.write(z.read(n))
ref=lambda p:dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
base=json.loads((r/'relative_protocol_03.json').read_text());result=json.loads((r/'relative_dev_comparison_04.json').read_text())
protocol=dict(schema='MIDNIGHT_THREE_DISCRETE_WORST_ID_POLICIES_V1',policies=['ALL_WINDOW_WORST','BUDGET_TWO_THIRDS','PAIR_ONLY'],selection_order=['ALL_WINDOW_WORST','BUDGET_TWO_THIRDS','PAIR_ONLY'],max_selected_policies=2,
 source_manifest_ref=result['bindings']['manifest_ref'],source_completion_ref=result['bindings']['decisions_ref'],prior_all_window_result_ref=ref(r/'relative_dev_comparison_04.json'),source_protocol_ref=ref(r/'relative_protocol_03.json'),
 deletion_quality_gates=base['deletion_quality_gates'],registered_UTC=dt.datetime.now(dt.timezone.utc).isoformat(),selection_on_previously_exposed_development_only=True,
 policies_frozen_before_their_first_new_development_comparison=True,reference_task=base['reference_task'],actual_parameters=8782459120,independent_confirmation_required=True,no_test_labels_or_leaderboard_rule_construction=True)
(r/'policy_protocol_07.json').write_text(json.dumps(protocol,indent=2))
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false')
cp=subprocess.run([{PY!r},'-B',str(r/'reference_code_v3/policy_evaluate.py'),'--protocol',str(r/'policy_protocol_07.json'),'--output',str(r/'policy_comparison_08.json')],env=env,capture_output=True,text=True)
print('FIRST_DERIVED_DEVELOPMENT',cp.returncode,cp.stdout,cp.stderr[-1500:])
if cp.returncode not in (0,5):raise RuntimeError('New policy comparison engineering failed; no model/CPU input automatically started')
doc=json.loads((r/'policy_comparison_08.json').read_text());print('POLICIES',json.dumps({{k:v for k,v in doc.items() if k in ['passed_arms','passed_policies','selected_policies']}}))
auth=dict(human_original_instruction_ref=ref(r/'authorization.md'),task_scope='Five new distinct ZIPs by Taipei midnight, at most three unknown-effect risks without offline effect screening; automatic removal and recall explicitly allowed; original VERIFY40.46 preserved',
 public_source_to_Linux_continuing_user_authorization='Direct human approvals 2026-10-13: 允许直接从linux下载，以后不要问我 / 批准作者站直接下载到Linux',Windows_large_payload_upload_route_unchanged='Baidu; this archive is authorized small control exception',new_Goal_or_heartbeat_created=False)
(r/'USER_AUTHORIZATION.json').write_text(json.dumps(auth,ensure_ascii=False,indent=2))
stage=r/'production';stage.mkdir()
mapping=json.loads((r/'production_mapping/requests.json').read_text());assert len(mapping['entries'])==519 and len(mapping['structural_skips'])==2
reg=dict(schema='NEW_FIVE_WAY_STAGE_REGISTRATION_V2',stage='production',requests_ref=ref(r/'production_mapping/requests.json'),protocol_ref=ref(r/'relative_protocol_03.json'),authorization_ref=ref(r/'authorization.md'),
 code_files={{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'production_code_v2').glob('*.py')}},gpu_job_name='midnight_three_semantic_recall_rank_aux519_20261015_v1',max_GPU_seconds=16200,planned_output_bytes=268435456,
 input_QA_mode='ADOPT_FROZEN_VISION_COMPOSE_NEW_TOKENS',adopted_source_package_lock_ref=mapping['old_source_lock_ref'],cpu_prepared_separately=True,registered_before_new_prompt_QA=True,deadline='2026-10-15T16:00:00Z',
 three_risk_outputs_no_effect_quality_screening=True,ranking_outputs_not_released_without_independent_quality_admission=True,old_successful_model_or_vision_operations_repeated=0)
(stage/'registration.json').write_text(json.dumps(reg,indent=2))
probe='import sys;sys.path.insert(0,'+repr(str(r/'production_code_v2'))+');import mf_common;mf_common.library();import composed_input;print("NEW_PRODUCTION_NAMESPACE_IMPORT_PASS_NO_MODEL")'
subprocess.run([{PY!r},'-B','-c',probe],env=env,check=True)
with (stage/'cpu.log').open('x') as log:
 child=subprocess.Popen([{PY!r},'-B',str(r/'production_code_v2/stages.py'),'prepare','--stage','production'],env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
launch=dict(pid=child.pid,start_ticks=Path('/proc/'+str(child.pid)+'/stat').read_text().split()[21],argv=[{PY!r},'-B',str(r/'production_code_v2/stages.py'),'prepare','--stage','production'],CPU_only=True,new_model_calls=0,registration_ref=ref(stage/'registration.json'),control_bytes={size},control_sha256={digest!r})
(r/'production_CPU_launch_08.json').write_text(json.dumps(launch,indent=2));print(json.dumps(launch))
'''
res=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','aic-inspur-home','python3','-'],input=code,text=True,capture_output=True)
print(res.stdout);print(res.stderr[-2300:] if res.returncode else '');res.check_returncode()
with (R/'policy_and_production_CPU_launch_08.json').open('x',encoding='utf8') as f:json.dump(dict(bytes=size,sha256=digest,output=res.stdout),f,indent=2)
