"""Deploy small explicit production control, bind real review, start once."""
import ast
import base64
import hashlib
import io
import json
from pathlib import Path
import subprocess
import zipfile

HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'bottleneck_24h_v1';REPORT=HERE.parents[1]/'reports/bottleneck_24h_20261019_v1'
names=('prepare_formal41.py','generate_formal41.py','qa_outputs41.py','package_five41.py','run_formal_chain41.py')
helpers=('summary_contract.py','summary_context_pixels.py','summary_grammar6.py','summary_output.py')
files={name:(HERE/name).read_bytes() for name in names}
files.update({name:(OLD/name).read_bytes() for name in helpers})
for name,data in files.items():ast.parse(data.decode('utf-8-sig'),filename=name)
files['delivered_history41.json']=(REPORT/'delivery_history_sprint41.json').read_bytes()
zbuffer=io.BytesIO()
with zipfile.ZipFile(zbuffer,'w',zipfile.ZIP_DEFLATED) as archive:
    for name,data in files.items():archive.writestr(name,data)
payload=zbuffer.getvalue();members={name:hashlib.sha256(data).hexdigest() for name,data in files.items()}
script=r'''
import base64,datetime,hashlib,io,json,os,pathlib,re,shutil,subprocess,urllib.request,zipfile
W=pathlib.Path('/home/inspur/aic_video_work');P=W/'bottleneck_24h_20261019_v1';R=W/'five_summary_sprint_20261019_v41'
RUN=W/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z';PY=W/'env/qwen3vl_isolated_20260910/bin/python'
assert os.uname().nodename=='inspur-NP5570M5'
assert not (R/'input_registration41.json').exists() and not (R/'code_formal41').exists(),'Existing registered formal task: inspect, no duplicate deploy/launch'
assert (R/'pilot_comparison42.json').exists(),'Real first CPU review required'
review=json.loads((R/'pilot_comparison42.json').read_text());assert review['broad_collapse_check_pass'] is True
assert review['original_GPU_status']=='failed' and review['post_generation_base_hash_not_executed'] is True
apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True).strip()
assert not apps,'Protect shared external GPU jobs'
payload=base64.b64decode('__PAYLOAD__');assert len(payload)==__SIZE__ and hashlib.sha256(payload).hexdigest()=='__SHA__'
expected=__MEMBERS__;z=zipfile.ZipFile(io.BytesIO(payload));assert z.testzip() is None and set(z.namelist())==set(expected)
for name in z.namelist():assert pathlib.PurePosixPath(name).name==name and hashlib.sha256(z.read(name)).hexdigest()==expected[name]
def read(p):return json.loads(p.read_text())
def ref(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def save(p,value):
 with p.open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False)
rules=R/'rules41';rules.mkdir()
urls={'track':'https://www.aicomp.cn/tracks/tracks-6/4267.html','notice':'https://www.aicomp.cn/notice/notice-3/5307.html','index':'https://www.aicomp.cn/notice/notice-3/'}
pages={}
for name,url in urls.items():
 req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
 with urllib.request.urlopen(req,timeout=18) as response:data=response.read(524289)
 assert 1000<len(data)<=524288,'Unexpected official page response'
 path=rules/(name+'.html');path.write_bytes(data);pages[name]=dict(url=url,**ref(path))
oldrules=read(P/'official_rule_check_before_summary05.json')
def pdfs(text):return sorted(set(re.findall(r'https?://[^\s"<>]+\.pdf',text,re.I)))
track=(rules/'track.html').read_text(errors='replace');notice=(rules/'notice.html').read_text(errors='replace')
assert pdfs(track)==pdfs(pathlib.Path(oldrules['current_track']['path']).read_text(errors='replace')),'Track attachment links changed; review before production'
assert pdfs(notice)==pdfs(pathlib.Path(oldrules['current_notice']['path']).read_text(errors='replace')),'Notice attachment links changed; review before production'
plain=re.sub('<[^>]+>','',track)
assert '9B' in plain and '空predictions' in plain and '人工修正' in plain and '反向构造规则' in plain,'Current published scope terms missing'
rulecheck=dict(status='CURRENT_PRIMARY_TRACK_NOTICE_INDEX_READ_LINKS_UNCHANGED_PRIOR_FULL_PDF_READ_ADOPTED_41',
 pages=pages,prior_rule_check_ref=ref(P/'official_rule_check_before_summary05.json'),prior_full_PDF_read_ref=oldrules['prior_full_read'],
 current_attachment_links=pdfs(track)+pdfs(notice),attachment_bytes_redownloaded=False,
 summary_production_scope_checked=True,not_official_special_permission=True,official_empty_predictions_allowed=True,
 no_test_teacher_training_manual_or_score_reverse_rules=True,total_main_auxiliary_limit=9000000000,
 utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
save(R/'official_rule_check41.json',rulecheck)
C=R/'code_formal41';C.mkdir();(R/'deployment_formal41.zip').write_bytes(payload)
for name in z.namelist():
 dest=(R/name) if name.endswith('.json') else (C/name)
 with dest.open('xb') as f:f.write(z.read(name))
oldreg=read(P/'summary_generation_registration_10.json');oldprod=read(W/'semantic_context_production_20261016_v1/production_registration.json')
headref=oldprod['selected_head'];head=pathlib.Path(headref['path']);assert ref(head)['sha256']==headref['sha256']
inventory_code="import torch,json;d=torch.load("+repr(str(head))+",map_location='cpu',weights_only=False);assert set(d)=={'network.0.weight','network.0.bias','network.2.weight','network.2.bias'};print(json.dumps({'count':sum(t.numel() for t in d.values()),'shapes':{k:list(v.shape) for k,v in d.items()}}))"
count=json.loads(subprocess.check_output([str(PY),'-B','-c',inventory_code],text=True));assert count['count']==98329
pipeline=8782459120+count['count'];assert pipeline==oldprod['actual_resident_parameters']==8782557449
by_policy={str(i):(pipeline if i in (1,2,5) else 8782459120) for i in range(1,6)}
save(R/'pipeline_inventory41.json',dict(actual_resident_parameters=8782459120,actual_pipeline_parameters=pipeline,
 actual_pipeline_parameters_by_policy=by_policy,base_parameters=8767123696,original_TIME_parameters=15335424,
 inherited_baseline_head_parameters=count['count'],inherited_baseline_head_ref=ref(head),inherited_head_shapes=count['shapes'],
 participating_roles_frozen=True,shared_BASE_counted_once=True,new_training=0,BASE_role_adapter_loaded_but_disabled=True))
admission=dict(status='ADMIT_FROZEN_ORIGINAL_TIME_BASE_426_TWO_VIEW_41',production_allowed=True,allow_first_formal_inputs=True,
 main_review_completed=True,original_TIME_ref=oldreg['initial_TIME_ref'],actual_pipeline_parameters=pipeline,
 external_evaluation_ref=ref(R/'pilot_comparison42.json'),external_first_output_QA_ref=ref(R/'first_independent_partial_output_QA42.json'),
 adopted_original_TIME_QA_ref=oldreg.get('adopted_TIME_output_QA_ref',ref(P/'summary_generation_10/INIT_TIME/first_independent_output_QA.json')),
 original_BASE_pilot_GPU_status_preserved='failed',raw43_adopted_for_exposed_development_only=True,
 missing_post_generation_base_hash_not_claimed=True,known_exit_flag_failure_and_formal_finally_restoration_reviewed=True,
 formal_actual_forward_role_hook_required=True,formal_natural_completed_exit0_and_fullQA_required=True,
 fixed_spatial_eligibility_policy_ref=ref(P/'summary_field_eligibility_scope_16.json'),
 official_empty_predictions_allowed=True,old_nonempty_quality_gate_not_rewritten=True,
 risk_policies=[3,4,5],quality_rationale='OriginalTIME and common-add tiny exposed proxy gains; BASE/P2/P5 negative or mixed. No catastrophic collapse; fixed unknown-effect exploration only, no improvement assertion.',
 official_improvement_asserted=False,new_fit=0,old_failed_weights_forbidden=True,
 utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
save(R/'production_admission41.json',admission)
history=read(R/'delivered_history41.json');meta=read(P/'summary_production_cache_metadata_13.json')
code={name:ref(C/name) for name in expected if name.endswith('.py')}
renderer_paths=[str(RUN/'b_score_aligned_package_v4'),str(RUN/'baseline_a_pts_v1'),str(RUN/'baseline_a_pts_v1/vendor')]
reg=dict(schema='FIVE_SUMMARY_SPRINT_V41',root=str(R),code=code,roles=['TIME','BASE'],
 model_config_ref=oldreg['model_config_ref'],original_TIME_ref=oldreg['initial_TIME_ref'],
 original_CPU_acceptance_ref=meta['original_CPU_acceptance_ref'],metadata_cache_ref=ref(P/'summary_production_cache_metadata_13.json'),
 pixel_dictionary_ref=oldreg['pixel_dictionary_ref'],pixel_codec_ref=oldreg['pixel_codec_ref'],
 production_admission_ref=ref(R/'production_admission41.json'),expected_sources=426,expected_windows=522,
 actual_resident_parameters=8782459120,actual_pipeline_parameters=pipeline,actual_pipeline_parameters_by_policy=by_policy,
 pipeline_inventory_ref=ref(R/'pipeline_inventory41.json'),python=str(PY),gpu_index=0,cpu_threads=4,
 cpu_thread_basis='One source-serial patch comparison/tokenization; current load near1 on96 CPU; four torch threads measured in prior bounded source work, no affinity pinning or admission quota',
 gpu_wrapper_ref=ref(RUN/'resource_unlimited_v1_20261007/gpu_run.py'),output_directory=str(R/'formal_outputs_41'),
 job_name='five_summary_original_TIME_BASE1044_20261019_v41',max_gpu_seconds=10000,
 max_gpu_seconds_by_role={'TIME':4800,'BASE':4800},model_start_cutoff_utc='2026-10-19T11:52:37Z',deadline_utc='2026-10-19T15:52:37Z',
 stage_output_estimates={'first_inputs':134217728,'generation':67108864,'first_output_QA':33554432},
 stage_RAM_estimates={'first_inputs':8589934592,'generation':42949672960,'first_output_QA':2147483648},
 package_inputs_ref=ref(W/'twenty_hour_five_20261014_v1/temporal_family_native_package_v3/package_inputs.json'),
 spatial_eligibility_policy_ref=ref(P/'summary_field_eligibility_scope_16.json'),official_empty_predictions_allowed=True,
 renderer_import_paths=renderer_paths,
 renderer_code_refs={'field_contract.py':ref(RUN/'b_score_aligned_package_v4/field_contract.py'),'pts_contract.py':ref(RUN/'baseline_a_pts_v1/pts_contract.py')},
 protected_baseline_ref=ref(W/'semantic_context_production_20261016_v1/package/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip'),
 historical_prediction_sha256=history['prediction_hashes'],history_inventory_ref=ref(R/'delivered_history41.json'),
 independent_validator_ref=ref(RUN/'baseline_a_pts_v1/vendor/independent_validate.py'),strict_loader_root=str(RUN/'baseline_a_pts_v1/vendor/frozen_strict_loader'),
 rule_check_before_package_ref=ref(R/'official_rule_check41.json'),
 policies={'1':'B|(T&C)','2':'B&(T|C)','3':'T','4':'C','5':'(B&(T|C))|(T&C)'},
 protected_40_47_unchanged=True,user_authorization='现在开始启动',new_goal=False,new_automation=False)
assert reg['protected_baseline_ref']['sha256']=='b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'
save(R/'input_registration41.json',reg)
save(R/'formal_deployment_acceptance41.json',dict(bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest(),CRC=True,members=expected,code=code))
cmd=[str(PY),'-B',str(C/'run_formal_chain41.py'),'--registration',str(R/'input_registration41.json')]
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',PYTHONDONTWRITEBYTECODE='1')
with (R/'formal_chain41.log').open('xb') as f:proc=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,cwd=str(C),env=env,start_new_session=True)
launch=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=proc.pid,
 start_ticks=pathlib.Path('/proc',str(proc.pid),'stat').read_text().split(') ',1)[1].split()[19],command=cmd,
 registration_ref=ref(R/'input_registration41.json'),deployment_bytes=len(payload),deployment_sha256=hashlib.sha256(payload).hexdigest(),
 stage='FIRST_FORMAL_INPUTS_RUNNING_GPU_ONLY_AFTER_ALL522_ACCEPTED',expected_first_inputs=522,expected_model_outputs=1044,
 pipeline_parameters_by_policy=by_policy)
save(R/'formal_chain_launch41.json',launch);print(json.dumps(launch,ensure_ascii=False))
'''
script=script.replace('__PAYLOAD__',base64.b64encode(payload).decode()).replace('__SIZE__',str(len(payload))).replace('__SHA__',hashlib.sha256(payload).hexdigest()).replace('__MEMBERS__',repr(members))
result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','-o','ConnectionAttempts=1','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=2',
    'aic-inspur-tailscale','python3 -'],input=script,text=True,capture_output=True,timeout=95,encoding='utf-8')
print(result.stdout);print(result.stderr)
result.check_returncode();receipt=json.loads(result.stdout.strip().splitlines()[-1])
with (REPORT/'five_sprint_formal_launch41.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
