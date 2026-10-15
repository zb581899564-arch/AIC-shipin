"""One small-control deployment and one registered eight-view development chain."""
from pathlib import Path
import ast,datetime as dt,hashlib,json,subprocess,zipfile

WORK=Path(__file__).resolve().parents[2]
REPORT=Path(__file__).resolve().parent
ROOT='/home/inspur/aic_video_work/midnight_five_verify40_46_20261015_v1'
PY='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
SSH=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','-o','ServerAliveInterval=10','-o','ServerAliveCountMax=2','aic-inspur-home']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
    with Path(p).open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def remote(code):
    r=subprocess.run(SSH+['python3','-'],input=code,text=True,capture_output=True,check=True);print(r.stdout,end='');return r.stdout

protocol=dict(schema='MIDNIGHT_FIVE_VERIFY40_46_V1',deadline_utc='2026-10-15T16:00:00Z',baseline='USER_VERIFY40.46',
    baseline_sha256='86593725c6bad919dc0d342fe98ad65e489a13a6e492da5de3afd247a3226543',actual_parameters=8782459120,
    model_role='BASE_ONLY_WITH_FROZEN_RESIDENT_TIME_ADAPTER_DISABLED_DURING_GENERATION',new_training_updates=0,
    arms=['ORDINARY','REDUNDANT','ACTION','REACTION','INFORMATION'],
    risk_arms_without_offline_effect_quality_evaluation=['ACTION','REACTION','INFORMATION'],
    deletion_quality_gates=dict(full_group_denominator=4,macro_paired_all_rater_duration_F1_delta_min='0',macro_all_rater_precision_delta_min='0',per_source_F1_delta_min='-1/100',minimum_sources_with_real_changed_native_frames=1,maximum_invalid_decisions=0),
    deletion_protocol_is_new_not_a_relaxation_of_old_recall_gates=True,development_previously_exposed=True,
    old_scientific_STOP_results_unchanged=True,independent_confirmation_required_for_deletion_production=True,
    output_schema='ordinary/redundant candidate index arrays; each recall field [] or [sample_a,sample_b],0<=a<b<=64',
    risky_recall_application='Protected baseline union corresponding category intervals; retain original boxes; new frames use existing accepted continuous spatial field',
    deletion_application='Remove indicated original whole events; union of surviving events intersect protected baseline; preserve original baseline for an otherwise empty source',
    production_new_call_maximum=521,production_GPU_wall_budget_seconds=16200,development_new_calls=8,development_GPU_wall_budget_seconds=900,
    external_labels_in_inference=False,test_labels_or_manual_edits_used=False,automatic_website_submission=False,reference_task='External all-rater event-conditioned human-summary duration proxy, not official unconditional highlight ground truth')
save(REPORT/'protocol.json',protocol)
official=dict(checked_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),reader='agent-reach Jina current official task, notice5307, industry notice index',
    official_urls=['https://www.aicomp.cn/tracks/tracks-6/4267.html','https://www.aicomp.cn/notice/notice-3/5307.html','https://www.aicomp.cn/notice/notice-3/'],
    current_bodies_read=True,current_attachment_links_unchanged='0930 rule, rematch submission -1, rematch notice -1 PDFs',
    unchanged_previously_read_attachment_receipt='reports/recall_expansion_verify40_46_20261014_v1/official_current_01/official_rule_check.json',
    relevant_requirements=['Reproducible automatic open-model predictions and postprocessing','No test labels/manual correction/training/pseudolabels or rule reverse-engineering','No closed model API or third-party test inference','Total physically resident main/auxiliary model+LoRA elements8782459120<=9B','Five submissions daily, user performs submission'],
    conclusion='Rule interpretation: new local open-model inference with frozen reusable vision inputs and deterministic new algorithms fits current public requirements; no organizer special permission claimed',
    no_newer_relevant_notice_in_current_index=True)
save(REPORT/'official_rule_check_01.json',official)
archive=REPORT/'incoming_dev_control_01.zip';files={}
for local,remote_dir in [('midnight_five_runtime_v1','code'),('midnight_five_reference_v1','reference_code')]:
    for path in sorted((WORK/'improvement'/local).glob('*.py')):
        ast.parse(path.read_text(encoding='utf8'));files[remote_dir+'/'+path.name]=path
files['protocol.json']=REPORT/'protocol.json';files['authorization.md']=REPORT/'USER_AUTHORIZATION.md';files['official_rule_check.json']=REPORT/'official_rule_check_01.json'
manifest={name:sha(path) for name,path in files.items()}
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
    for name,path in files.items():z.write(path,name)
    z.writestr('control_manifest.json',json.dumps(manifest,sort_keys=True))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
digest=sha(archive);size=archive.stat().st_size
save(REPORT/'control_manifest_01.json',dict(bytes=size,sha256=digest,members=manifest))
remote(f"from pathlib import Path\np=Path({ROOT!r});p.mkdir(exist_ok=False)\nprint('NEW_ROOT_CREATED')")
subprocess.run(['scp','-o','BatchMode=yes','-o','ConnectTimeout=12',str(archive),'aic-inspur-home:'+ROOT+'/incoming_dev_control_01.zip'],check=True,capture_output=True)
remote(f'''from pathlib import Path
import hashlib,json,zipfile,subprocess,os
r=Path({ROOT!r});p=r/'incoming_dev_control_01.zip'
assert p.stat().st_size=={size} and hashlib.sha256(p.read_bytes()).hexdigest()=={digest!r}
with zipfile.ZipFile(p) as z:
 assert z.testzip() is None
 m=json.loads(z.read('control_manifest.json'))
 assert set(z.namelist())==set(m)|{{'control_manifest.json'}}
 for name,d in m.items():
  assert not Path(name).is_absolute() and '..' not in Path(name).parts and hashlib.sha256(z.read(name)).hexdigest()==d
  f=r/name;f.parent.mkdir(parents=True,exist_ok=True)
  with f.open('xb') as h:h.write(z.read(name))
(r/'control_acceptance.json').write_text(json.dumps(dict(status='PASS_SMALL_CONTROL_SIZE_SHA_CRC_MEMBER_SHA',bytes={size},sha256={digest!r},members=m)))
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
cmd=[{PY!r},'-B',str(r/'reference_code/map_existing.py'),'--prior-root','/home/inspur/aic_video_work/recall_expansion_verify40_46_20261014_v1','--group','dev','--protocol',str(r/'protocol.json'),'--output',str(r/'dev_mapping')]
subprocess.run(cmd,env=env,check=True)
d=r/'dev';d.mkdir()
ref=lambda p:dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
code={{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'code').glob('*.py')}}
reg=dict(schema='NEW_FIVE_WAY_STAGE_REGISTRATION_V1',stage='dev',requests_ref=ref(r/'dev_mapping/inference_entries.json'),protocol_ref=ref(r/'protocol.json'),authorization_ref=ref(r/'authorization.md'),code_files=code,gpu_job_name='midnight_five_base_editor_dev8_20261015_v1',max_GPU_seconds=900,planned_output_bytes=16777216,registered_before_new_prompt_QA=True,deadline='2026-10-15T16:00:00Z')
(d/'registration.json').write_text(json.dumps(reg,indent=2))
env.update(CUDA_VISIBLE_DEVICES='0',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false')
with (d/'parent.log').open('x') as log:
 proc=subprocess.Popen([{PY!r},'-B',str(r/'code/controller.py'),'--stage','dev'],env=env,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
launch=dict(pid=proc.pid,start_ticks=Path('/proc/'+str(proc.pid)+'/stat').read_text().split()[21],argv=[{PY!r},'-B',str(r/'code/controller.py'),'--stage','dev'],registration_ref=ref(d/'registration.json'),parent_CUDA='0')
(r/'dev_launch_01.json').write_text(json.dumps(launch,indent=2));print(json.dumps(launch))
''')
save(REPORT/'deployment_completion_01.json',dict(status='DEPLOYED_REGISTERED_ONE_DEV_CHAIN_NOT_EFFECT_PASS',bytes=size,sha256=digest,root=ROOT))
