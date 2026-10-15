"""Conditional new first-layer facts deployment; fresh PASS is checked before mutation."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

from deploy_dev_02 import remote, save

REPORT = Path(__file__).resolve().parent
WORK = REPORT.parents[1]
MAIN = '/home/inspur/aic_video_work/recall_adapter_role_verify40_46_20261015_v1'
ROOT = MAIN+'/fixed40_upper_bound_01'


def main():
    assert not (REPORT/'role_fixed40_launch_12.json').exists()
    pre = remote(r'''
import datetime as dt,hashlib,json,pathlib,shutil,socket,subprocess
main=pathlib.Path('__MAIN__');r=pathlib.Path('__ROOT__');h=main.parent
assert socket.gethostname()=='inspur-NP5570M5' and not r.exists() and not (main/'incoming_role_fixed40_12.zip').exists()
read=lambda p:json.loads(pathlib.Path(p).read_text());sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
protocolp=main/'protocol.json';protocol=read(protocolp);protocol_ref=dict(path=str(protocolp),sha256=sha(protocolp))
assert protocol_ref['sha256']=='c2e2b7a47e511703ca30ddb57a27dc84e5584c605cac8013ae4cdd1c8ab2f149'
conditions={'full_group','macro_F1_not_lower','macro_recall_gain','every_source_loss_within_gate','macro_precision_not_lower','all_rater_recall_retained','all_baseline_native_frames_retained','real_changed_sources'}
controller=h/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller'
ledger=[json.loads(line) for line in (h/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
for group in ('dev','confirm'):
 chain=main/'chain_01' if group=='dev' else main/'fresh_01/confirm/chain_01'
 resultp=main/'comparison_01/result.json' if group=='dev' else main/'confirm/comparison_01/result.json'
 result=read(resultp);completed=read(chain/'completion.json')
 expected='PASS_ADAPTER_ROLE_DEV_PENDING_NEW_FRESH_CONFIRM' if group=='dev' else 'PASS_ROLE_FRESH_CONFIRM_PENDING_FIXED40'
 assert result['status']==completed['status']==expected and result['group']==group
 assert len(result['cases'])==4 and set(result['conditions'])==conditions and all(value is True for value in result['conditions'].values())
 assert result['bindings']['protocol_ref']==protocol_ref and result['candidate']==protocol['candidate']
 assert result['production_admitted'] is False and result['old_failed_gates_changed'] is False
 assert completed['comparison_ref']==dict(path=str(resultp),sha256=sha(resultp)) and not (chain/'failure.json').exists()
 base=main if group=='dev' else main/'confirm/POSITIVE'
 gatep=main/'gpu_admission.json' if group=='dev' else main/'gpu_admission_confirm_POSITIVE.json';gate=read(gatep)
 gpu=read(base/'gpu_01/completion.json');inputqa=read(gate['first_input_QA_ref']['path']);outputqa=read(base/'output_qa_01/completion.json')
 assert gpu['status']==('PASS_ROLE_ALL10_MODEL_CALLS_NOT_QUALITY' if group=='dev' else 'PASS_ALL_POSITIVE_CALLS_NOT_QUALITY')
 assert outputqa['status']==('PASS_ROLE_ALL10_OUTPUT_QA_NOT_QUALITY' if group=='dev' else 'PASS_ALL_POSITIVE_OUTPUT_QA_NOT_QUALITY')
 assert gpu['calls']==len(gpu['entries'])==inputqa['calls']==len(inputqa['proofs'])==outputqa['calls']==len(outputqa['proofs'])==gate['expected_input_count']>0
 assert outputqa['CPU_only'] is True and outputqa['CUDA_initialized'] is False
 key='output_QA_ref' if group=='dev' else 'output_QA_completion_ref'
 assert result['bindings'][key]==dict(path=str(base/'output_qa_01/completion.json'),sha256=sha(base/'output_qa_01/completion.json'))
 resourcep=controller/(gate['gpu_job_name']+'.resource.json');resource=read(resourcep)
 assert resource['status']=='completed' and resource['exit_code']==0 and [row for row in ledger if row['name']==gate['gpu_job_name']]==[resource]
 assert outputqa['resource_terminal_sha256']==sha(resourcep)
reference=h/'reliable_reference_20261012_v1/coverage_diagnostic_01.json'
resident_reference=reference.is_file()
if resident_reference:
 assert reference.stat().st_size==594682 and sha(reference)=='37a7c93876334b3a5d0c222e3a7f99727778d50f28f3a1172e860d19d3dc82b8','Never replace a different resident reference'
else:
 reference=r/'reference/coverage_diagnostic_01.json'
owned=[]
for p in pathlib.Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  argv=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
  if str(main) in argv:
   stat=(p/'stat').read_text().rsplit(')',1)[1].split()
   owned.append(dict(pid=p.name,ppid=stat[1],state=stat[0],start_ticks=stat[19],argv=argv,io=(p/'io').read_text()))
 except OSError:pass
assert not owned,'Actual prior chain must naturally exit before new independent facts work'
print(json.dumps(dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),host=socket.gethostname(),owned=owned,
 actual_positive_dev_and_first_fresh_eight_gate_PASS=True,reference_path=str(reference),resident_reference_reused=resident_reference,
 disk=list(shutil.disk_usage(main)),memory=pathlib.Path('/proc/meminfo').read_text(),
 tasks=subprocess.run(['ps','-eo','pid,ppid,stat,pcpu,rss,args','--sort=-pcpu','--width','2500'],capture_output=True,text=True,check=True).stdout.splitlines()[:18],
 gpu=subprocess.run(['nvidia-smi','--query-gpu=index,name,memory.used,memory.total,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout,
 compute=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout)))
'''.replace('__MAIN__',MAIN).replace('__ROOT__',ROOT))
    save('role_fixed40_preflight_12.json',pre)
    files = {}
    for path in (WORK/'improvement/recall_role_fixed40_v1').iterdir():
        if path.is_file() and path.suffix in ('.py','.md'):
            if path.suffix=='.py': ast.parse(path.read_text(encoding='utf8'))
            files['code/'+path.name]=path.read_bytes()
    assert len([name for name in files if name.endswith('.py')])==9
    files['metadata_code/source_audit.py']=(WORK/'improvement/recall_consensus_fixed40_v1/source_audit.py').read_bytes()
    for name in ['source_separation_audit.json','supplement_source_separation_audit.json']:
        files['reference/'+name]=(WORK/'reports/reliable_reference_20261012_v1'/name).read_bytes()
    files['role_fixed40_upper_bound_review_12.md']=(REPORT/'role_fixed40_upper_bound_review_12.md').read_bytes()
    if not pre['resident_reference_reused']:
        original=(WORK/'reports/reliable_reference_20261012_v1/coverage_diagnostic_01.json').read_bytes()
        assert len(original)==594682 and hashlib.sha256(original).hexdigest()=='37a7c93876334b3a5d0c222e3a7f99727778d50f28f3a1172e860d19d3dc82b8'
        files['reference/coverage_diagnostic_01.json']=original
    files['manifest.json']=json.dumps(dict(files={name:dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest()) for name,data in files.items()}),sort_keys=True).encode()
    bundle=REPORT/'role_fixed40_control_12.zip'
    with zipfile.ZipFile(bundle,'x',compression=zipfile.ZIP_DEFLATED) as archive:
        for name,data in files.items():archive.writestr(name,data)
    data=bundle.read_bytes();digest=hashlib.sha256(data).hexdigest();assert len(data)<262144
    sent=subprocess.run(['scp','-q','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
        str(bundle),'aic-inspur-home:'+MAIN+'/incoming_role_fixed40_12.zip'],capture_output=True,text=True,timeout=60)
    if sent.returncode:raise RuntimeError('Inspect unknown transfer result before any explicit recovery: '+sent.stderr)
    result=remote(r'''
import ast,datetime as dt,hashlib,json,os,pathlib,socket,subprocess,sys,zipfile
main=pathlib.Path('__MAIN__');r=pathlib.Path('__ROOT__');h=main.parent
assert socket.gethostname()=='inspur-NP5570M5' and not r.exists()
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
bundle=main/'incoming_role_fixed40_12.zip';assert bundle.stat().st_size==__BYTES__ and sha(bundle)=='__SHA__'
with zipfile.ZipFile(bundle) as archive:
 assert len(archive.namelist())==len(set(archive.namelist())) and archive.testzip() is None
 manifest=json.loads(archive.read('manifest.json'))['files'];assert set(archive.namelist())==set(manifest)|{'manifest.json'}
 for name,row in manifest.items():
  path=pathlib.PurePosixPath(name);assert not path.is_absolute() and '..' not in path.parts
  data=archive.read(name);assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
 r.mkdir()
 for name in manifest:
  path=r/name;path.parent.mkdir(parents=True,exist_ok=True)
  with path.open('xb') as stream:stream.write(archive.read(name))
sys.dont_write_bytecode=True;sys.path[:0]=[str(r/'code'),str(r/'metadata_code')]
import facts_common as io,source_audit
from registration import registration,metadata
reference=pathlib.Path('__REFERENCE__')
assert reference.stat().st_size==594682 and sha(reference)==source_audit.REFERENCE_SHA
# New immutable registration snapshot of resident clock metadata, no media decode/clock measurement.
document=source_audit.load_reference(reference);sources=source_audit.audit_source_descriptors(document);views=source_audit.point_covering_views(document,sources)
plan=dict(schema='RECALL_FIXED40_SOURCE_METADATA_PLAN_V1',scope=source_audit.SCOPE,sources=sources,views=views,
 reference_ref=dict(path=str(reference),sha256=sha(reference)),reference_level=source_audit.REFERENCE_LEVEL,coverage=source_audit.EXPECTED_COVERAGE,
 coverage_pass=False,reference_quality_pass=False,source_count=9,unique_input_count=17,ordinary_observation_count=222,metadata_only=True,model_calls=0,GPU_admitted=False)
# Before registering any NEW operation, guard prior completed recall contexts.
# A candidate match requires an explicit full CPU/model adoption audit instead
# of blindly preparing or calling the same context again.
from fractions import Fraction as F
wanted={(v['source_sha256'],F(v['window_start']),F(v['window_end'])) for v in views}
prior_contexts=[]
for dirname in ['recall_expansion_verify40_46_20261014_v1','recall_consensus_verify40_46_20261015_v1','recall_positive_admission_verify40_46_20261015_v1','recall_adapter_role_verify40_46_20261015_v1']:
 parent=h/dirname
 for directory in [parent,parent/'fresh_01']:
  for receipt in directory.glob('cpu_acceptance*.json'):
   old=io.read(receipt)
   for entry in old.get('entries',[]):
    path=entry.get('input_path') or entry.get('input_ref',{}).get('path')
    if not path:continue
    meta=io.read(path)
    if {'source_sha256','window_start','window_end'} <= set(meta) and (meta['source_sha256'],F(meta['window_start']),F(meta['window_end'])) in wanted:
     prior_contexts.append(dict(old_CPU_receipt=str(receipt),old_input=str(path),case_id=entry['case_id']))
io.save(r/'prior_context_audit.json',dict(exact_context_candidates=prior_contexts,metadata_only=True,new_model_calls=0,new_encodes=0))
assert not prior_contexts,'Explicit existing-input/model adoption audit required before NEW registration; do not repeat successful work'
io.save(r/'source_plan.json',plan)
devreg=io.read(main/'registration.json');confirmreg=io.read(main/'registration_confirm.json');required=dict(devreg['required_files'])
for name,digest in confirmreg['required_files'].items():
 assert name not in required or required[name]==digest
 required[name]=digest
def add(path,expected=None):
 path=pathlib.Path(path).resolve();data_root=pathlib.Path('/home/inspur/aic_video_data/videos')
 assert (path.is_relative_to(h) or (path.is_relative_to(data_root) and expected is not None)) and path.is_file()
 actual=sha(path);assert expected is None or actual==expected
 assert str(path) not in required or required[str(path)]==actual
 required[str(path)]=actual;return dict(path=str(path),sha256=actual)
for path in (r/'code').glob('*.py'):ast.parse(path.read_text());add(path)
for path in io.runtime_dependencies()|io.processor_assets()|{str(io.CONFIG),str(io.RUNTIME)}:add(path)
for path in (io.RUN/'resource_unlimited_v1_20261007').glob('*.py'):add(path)
for name in ['cv_contract.py','cv_tokens.py','cv_grammar.py']:add(io.CV_CODE/name)
positive_codes={str(path.resolve()):sha(path) for directory in [main/'confirm_code',main.parent/'recall_positive_admission_verify40_46_20261015_v1/code'] for path in directory.glob('*.py')}
for name,digest in positive_codes.items():add(name,digest)
phase_codes={group:{str(path):sha(path) for path in (main/('code' if group=='dev' else 'confirm_code')).glob('*.py')} for group in ('dev','confirm')}
for paths in phase_codes.values():
 for name,digest in paths.items():add(name,digest)
pairs={name:[add(main.parent/'recall_positive_admission_verify40_46_20261015_v1/code'/name),add(main/'confirm_code'/name)] for name in ['positive_contract.py','positive_grammar.py','positive_metrics.py']}
for source in sources:
 for key,digest in [('source_path','source_sha256'),('clock_path','clock_sha256')]:add(source[key],source[digest])
phase_execution={}
for group in ['dev','confirm']:
 base=main if group=='dev' else main/'confirm/POSITIVE';gatepath=main/'gpu_admission.json' if group=='dev' else main/'gpu_admission_confirm_POSITIVE.json';gate=io.read(gatepath)
 phase=dict(chain_ref=add(main/'chain_01/completion.json' if group=='dev' else main/'fresh_01/confirm/chain_01/completion.json'),
  registration_ref=add(main/'registration.json' if group=='dev' else main/'registration_confirm.json'),gpu_admission_ref=add(gatepath),
  gpu_completion_ref=add(base/'gpu_01/completion.json'),output_QA_completion_ref=add(base/'output_qa_01/completion.json'),
  input_QA_completion_ref=add(gate['first_input_QA_ref']['path'],gate['first_input_QA_ref']['sha256']),
  resource_ref=add(io.RUN/'controller'/(gate['gpu_job_name']+'.resource.json')))
 gpu=io.read(base/'gpu_01/completion.json');outqa=io.read(base/'output_qa_01/completion.json')
 for key in ['model_identity_ref','attempts_ref']:add(gpu[key]['path'],gpu[key]['sha256'])
 for entry,proof in zip(gpu['entries'],outqa['proofs']):
  add(entry['done_ref']['path'],entry['done_ref']['sha256']);add(proof['proof_ref']['path'],proof['proof_ref']['sha256'])
  done=io.read(entry['done_ref']['path']);add(done['raw_ref']['path'],done['raw_ref']['sha256'])
 phase_execution[group]=phase
refs=dict(cache_reader_equivalence_ref=add(h/'recall_cache_io_engineering_20261015_v2/completion.json'),
 cache_reader_engineering_registration_ref=add(h/'recall_cache_io_engineering_20261015_v2/registration.json'),
 protocol_ref=add(main/'protocol.json'),authorization_ref=add(main/'USER_AUTHORIZATION.json'),
 dev_result_ref=add(main/'comparison_01/result.json'),confirm_result_ref=add(main/'confirm/comparison_01/result.json'),
 source_audit_plan_ref=add(r/'source_plan.json'),source_audit_completion_ref=add(r/'source_plan.json'),
 source_audit_code_ref=add(r/'metadata_code/source_audit.py'),reference_ref=add(reference))
add(r/'role_fixed40_upper_bound_review_12.md')
separation_refs=[add(r/'reference'/name) for name in ['source_separation_audit.json','supplement_source_separation_audit.json']]
processor=h/'env/qwen3vl_isolated_20260910/lib/python3.10/site-packages/transformers/models/qwen3_vl/video_processing_qwen3_vl.py'
processor_ref=add(processor);job='recall_role_fixed40_upper17_b0_20261015_v1'
assert not (io.RUN/'controller'/(job+'.resource.json')).exists() and not any(row['name']==job for row in io.rows(h/'improvement_round1/gpu_ledger.jsonl'))
now=dt.datetime.now(dt.timezone.utc)
reg=dict(schema='ROLE_FIXED40_B0_UPPER_BOUND_REGISTRATION_V1',status='REGISTERED_ROLE_FIXED40_B0_ONLY_AFTER_DEV_FRESH_CONFIRM_PASS',
 source_scope='EXTERNAL_NONTEST_ONLY',scope=source_audit.SCOPE,model_parameters=8782459120,optimizer_updates=0,source_count=9,unique_input_count=17,
 production_admitted=False,reference_available_to_inference=False,next_level_automatically_authorized=False,
 required_files=required,source_separation_refs=separation_refs,positive_code_files=positive_codes,phase_code_files=phase_codes,unchanged_admission_contract_pairs=pairs,phase_execution=phase_execution,
 capacity_contract=dict(video_size=io.read(io.CONFIG)['video_size'],processor_source_path=processor_ref['path'],processor_source_sha256=processor_ref['sha256']),
 deadline=(now+dt.timedelta(hours=6)).isoformat(),registered_at_utc=now.isoformat(),
 gpu_budget=dict(max_actual_calls=17,max_seconds=1800,gpu_job_name=job),execution_plan=[dict(case_id=v['case_id'],mode='NEW') for v in views],**refs)
io.save(r/'role_fixed40_registration.json',reg);registration(r);metadata(r,reg)
indices=subprocess.run(['nvidia-smi','--query-gpu=index','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout.splitlines()
assert indices and indices[0].strip()=='0'
env=dict(os.environ,CUDA_VISIBLE_DEVICES=indices[0].strip(),PYTHONDONTWRITEBYTECODE='1')
argv=[str(h/'env/qwen3vl_isolated_20260910/bin/python'),'-B','-u',str(r/'code/chain.py'),'--root',str(r)]
io.save(r/'launch_claim_12.json',dict(utc=io.utc(),argv=argv,parent_CUDA=env['CUDA_VISIBLE_DEVICES'],registration_sha256=sha(r/'role_fixed40_registration.json')))
with (r/'chain_12.log').open('xb') as log:parent=subprocess.Popen(argv,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
stat=(pathlib.Path('/proc')/str(parent.pid)/'stat').read_text().rsplit(')',1)[1].split()
value=dict(utc=io.utc(),host=socket.gethostname(),pid=parent.pid,start_ticks=stat[19],argv=argv,parent_CUDA=env['CUDA_VISIBLE_DEVICES'],
 bundle_bytes=__BYTES__,bundle_sha256='__SHA__',CRC_and_member_SHA_pass=True,registration_sha256=sha(r/'role_fixed40_registration.json'),
 source_count=9,complete_ordinary_touching_windows=17,registered_new_B0_calls=17,actual_new_model_calls_at_launch=0,
 old_successful_work_repeated=False,source_audit_snapshot_is_new_metadata_not_old_execution=True,production_admitted=False,next_level_started=False,new_ZIPs=0)
io.save(r/'launch_12.json',value);print(json.dumps(value))
'''.replace('__MAIN__',MAIN).replace('__ROOT__',ROOT).replace('__BYTES__',str(len(data))).replace('__SHA__',digest).replace('__REFERENCE__',pre['reference_path']))
    save('role_fixed40_launch_12.json',result)
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
