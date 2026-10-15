"""One explicit consensus fixed40 deployment after the real fresh PASS.

Do not run while confirmation is pending. The first SSH call is read-only.
An existing local/incoming/target attempt requires inspection, never a retry.
Only small code and the original silver JSON travel; no media/tensors/weights.
"""
import ast
import base64
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import stat
import subprocess
import zipfile

WORK = Path(__file__).resolve().parents[2]
REPORT = Path(__file__).resolve().parent
MAIN = '/home/inspur/aic_video_work/recall_consensus_verify40_46_20261015_v1'
SSH = 'aic-inspur-home'
PROTOCOL_SHA = 'd71d191c2525402872a866ab513e84c1ee032fdb14858ff9034bdb32f93cb236'
CONSENSUS_SHA = '493602a187c868535a62febed24f0e11623d06cea50d57615b45e480ac3a8297'
MERGE_SHA = '4b3e5b4ba95d9dff278e7dde6b9d4389a09ea538c10fbee05b427dd1f872d277'
OVERLAP_SHA = '4261247b98b18fdc243dce357f4129ecdf92cbc4d6b3cb014d9d7f55d3054099'
REFERENCE_SHA = '37a7c93876334b3a5d0c222e3a7f99727778d50f28f3a1172e860d19d3dc82b8'
REFERENCE_BYTES = 594682
NAMES = ('facts_common.py', 'facts_infer.py', 'facts_verify.py', 'facts_chain.py',
         'facts_prepare.py', 'facts_admit.py', 'source_audit.py', 'facts_veto.py')
CONDITIONS = ('full_group', 'macro_F1_not_lower', 'macro_recall_gain', 'every_source_loss_within_gate',
              'macro_precision_not_lower', 'all_rater_recall_retained', 'all_baseline_native_frames_retained', 'real_changed_sources')
BINDINGS = ('protocol_sha256', 'registration_sha256', 'original_registration_sha256',
            'cpu_acceptance_sha256', 'verification_export_sha256', 'first_B0_QA_sha256', 'reference_completion_sha256')
INCOMING = MAIN+'/incoming_consensus_fixed40_control_15.zip'
BUNDLE = REPORT/'consensus_fixed40_control_15.zip'
PREFLIGHT = REPORT/'consensus_fixed40_preflight_15.json'
RECEIPT = REPORT/'consensus_fixed40_deployment_launch_15.json'
MAX_BUNDLE_BYTES = 1 << 20


def require(value, reason):
    if not value:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save_exclusive(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def remote(script, timeout=90):
    # Python comes from stdin, avoiding Windows command-length and shell quoting
    # issues. Existing host aliases/keys remain unchanged; never use a jump host.
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=12',
        '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=2', SSH, 'python3 -B -'],
        input=script, capture_output=True, text=True, encoding='utf-8', timeout=timeout)
    if result.returncode:
        raise RuntimeError('Remote outcome must be inspected; no automatic retry: '+(result.stderr or result.stdout))
    return json.loads(result.stdout)


def validate_pass_summary(value):
    """Pure negative-testable guard over the read-only remote PASS witness."""
    require(value['status'] == 'PASS_REAL_CONSENSUS_FRESH_PHASE_BEFORE_FIXED40_UPLOAD' and
        value['host'] == 'inspur-NP5570M5' and value['protocol_sha256'] == PROTOCOL_SHA and
        value['target_exists'] is False and value['incoming_exists'] is False and
        value['chain_failure_exists'] is False and value['fresh_chain_process_alive'] is False,
        'Pending, failed, active or previously attempted work cannot admit an upload')
    for key, count, status in (
        ('development', 8, 'PASS_CONSENSUS_DEVELOPMENT_NEEDS_FRESH_CONFIRM'),
        ('confirmation', 4, 'PASS_CONSENSUS_FRESH_CONFIRM_PENDING_FIXED40')):
        result = value[key]
        require(result['status'] == status and len(result['source_ids']) == len(set(result['source_ids'])) == count and
            set(result['conditions']) == set(CONDITIONS) and all(result['conditions'][key] is True for key in CONDITIONS),
            'The full real consensus phase must pass every original quality gate')
    require(set(value['development']['source_ids']).isdisjoint(value['confirmation']['source_ids']) and
        value['chain_status'] == 'PASS_CONSENSUS_FRESH_CONFIRM_PENDING_FIXED40' and
        all(value['confirmation']['bindings'][key] == value['expected_bindings'][key] for key in BINDINGS) and
        value['chain_comparison_sha256'] == value['comparison_sha256'],
        'Fresh source isolation or one of the seven comparison/chain bindings changed')
    require(isinstance(value['preupload_phase_metadata_sha256'], str) and len(value['preupload_phase_metadata_sha256']) == 64 and
        type(value['preupload_phase_metadata_file_count']) is int and value['preupload_phase_metadata_file_count'] > 0,
        'Actual phase/model-stage completion metadata is required')


def validate_archive(data, expected):
    """CRC, unique safe members, file type, size and SHA before extraction."""
    require(0 < len(data) < MAX_BUNDLE_BYTES, 'Only this bounded small control bundle is authorized')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)) and set(names) == set(expected)|{'deployment_manifest.json'},
                'Unexpected, duplicate or missing ZIP members')
        for member in archive.infolist():
            name = member.filename
            path = PurePosixPath(name)
            mode = member.external_attr >> 16
            require(name and '\\' not in name and '\x00' not in name and ':' not in name and
                not path.is_absolute() and all(part not in ('', '.', '..') for part in path.parts) and
                str(path) == name and not member.is_dir() and not stat.S_ISLNK(mode) and
                (stat.S_IFMT(mode) in (0, stat.S_IFREG)), 'Unsafe/nonregular ZIP member')
            require(member.file_size <= MAX_BUNDLE_BYTES, 'Unbounded ZIP member')
        require(archive.testzip() is None, 'ZIP CRC failed')
        manifest = json.loads(archive.read('deployment_manifest.json'))
        require(manifest['schema'] == 'CONSENSUS_FIXED40_SMALL_CONTROL_AND_ORIGINAL_SILVER_V1' and
                manifest['files'] == expected, 'ZIP manifest differs from the frozen local member map')
        for name, row in expected.items():
            content = archive.read(name)
            require(len(content) == row['bytes'] and sha(content) == row['sha256'], 'ZIP member bytes/SHA differ: '+name)


def local_files():
    files = {'code/'+name: (WORK/'improvement/recall_consensus_fixed40_v1'/name).read_bytes() for name in NAMES}
    fixed = {
        'code/consensus.py': (WORK/'improvement/recall_consensus_verify40_46_v1/consensus.py', CONSENSUS_SHA),
        'code/merge_keep.py': (WORK/'improvement/recall_expansion_verify40_46_v1/merge_keep.py', MERGE_SHA),
        'code/overlap_plan.py': (WORK/'improvement/recall_expansion_verify40_46_v1/overlap_plan.py', OVERLAP_SHA),
        'reference/coverage_diagnostic_01.json': (WORK/'reports/reliable_reference_20261012_v1/coverage_diagnostic_01.json', REFERENCE_SHA)}
    for name, (path, digest) in fixed.items():
        content = path.read_bytes()
        require(sha(content) == digest, 'Required original artifact changed: '+str(path))
        files[name] = content
    require(len(files['reference/coverage_diagnostic_01.json']) == REFERENCE_BYTES, 'Full original silver reference required')
    for name, content in files.items():
        if name.endswith('.py'):
            ast.parse(content.decode('utf-8-sig'), filename=name)
    return files


def gate_library(common_source):
    """Small read-only phase gates; full prior per-view closure is deferred."""
    source = r'''
import base64,datetime as dt,hashlib,io as bytes_io,json,os,pathlib,shutil,socket,stat,subprocess,sys,traceback,types,zipfile
sys.dont_write_bytecode=True
MAIN=pathlib.Path(__MAIN__)
TARGET=MAIN/'fixed40_01'
INCOMING=pathlib.Path(__INCOMING__)
PROTOCOL_SHA=__PROTOCOL__
COMMON_SOURCE=__COMMON__
def need(value,reason):
 if not value:raise ValueError(reason)
def digest(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
def load(path):return json.loads(pathlib.Path(path).read_text(encoding='utf-8-sig'))
def process_commands():
 result=[]
 for path in pathlib.Path('/proc').glob('[0-9]*/cmdline'):
  try:
   argv=[part.decode(errors='replace') for part in path.read_bytes().split(b'\0') if part]
   if argv:result.append(dict(pid=int(path.parent.name),argv=argv))
  except (FileNotFoundError,PermissionError,ProcessLookupError):pass
 return result
def read_only_gate():
 need(socket.gethostname()=='inspur-NP5570M5' and sys.platform=='linux','Wrong actual host/platform')
 need(not TARGET.exists() and not TARGET.is_symlink(),'Independent fixed40 target already exists; inspect, never overwrite/restart')
 need(not INCOMING.exists() and not INCOMING.is_symlink(),'Incoming artifact exists with unknown outcome; inspect, never retransmit')
 need(not (MAIN/'confirm/chain_02/failure.json').exists(),'Fresh recovery chain has a real failure')
 commands=process_commands()
 fresh=str(MAIN/'recovery_v2/code/pilot_chain_recovery.py')
 need(not any(fresh in row['argv'] for row in commands),'Fresh parent has not naturally exited yet')
 module=types.ModuleType('_consensus_fixed40_readonly_gate_15')
 module.__file__=str(TARGET/'code/facts_common.py')
 sys.modules[module.__name__]=module
 exec(compile(COMMON_SOURCE,module.__file__,'exec'),module.__dict__)
 # Only top-level phase/selection/model-stage counts and small identity/resource
 # receipts are read before upload. No per-view input/proof/raw is opened here.
 phase_files={}
 def phase(path,expected_sha=None):
  path=pathlib.Path(path);actual=digest(path)
  need(expected_sha is None or actual==expected_sha,'A top-level frozen phase reference changed')
  phase_files[str(path)]=actual
  return load(path)
 protocol=phase(MAIN/'protocol.json',PROTOCOL_SHA)
 development=phase(MAIN/'development_01/result.json')
 confirmation=phase(MAIN/'confirm/comparison_01/result.json')
 module.validate_phase_results(protocol,development,confirmation)
 chain=phase(MAIN/'confirm/chain_02/completion.json')
 recovery=phase(MAIN/'fresh_recovery_registration_02.json')
 module.validate_runtime(recovery['runtime'])
 original=phase(MAIN/'fresh_confirm_registration.json',recovery['original_registration_ref']['sha256'])
 selected=phase(MAIN/'selection_before_fresh_confirmation.json',recovery['development_selection_ref']['sha256'])
 need(selected['status']=='FROZEN_CONSENSUS2_AFTER_DEV_PASS' and selected['candidate']==module.CANDIDATE and
  selected['protocol_sha256']==PROTOCOL_SHA and selected['result_sha256']==digest(MAIN/'development_01/result.json') and
  selected['fresh_confirm_metrics_examined'] is False,'Original rule selection changed')
 cpu=phase(MAIN/'cpu_acceptance_confirm_v2.json')
 pointer=phase(MAIN/'reference_completion_confirm.json')
 media=phase(pointer['path'],pointer['sha256'])
 export_path=MAIN/'confirm/VERIFY/verification_export.json'
 phase_files[str(export_path)]=digest(export_path)  # SHA only; no per-event parsing before upload.
 need(chain['status']=='PASS_CONSENSUS_FRESH_CONFIRM_PENDING_FIXED40' and chain['group']=='confirm' and
  chain['registration_sha256']==digest(MAIN/'fresh_recovery_registration_02.json') and
  chain['original_registration_sha256']==digest(MAIN/'fresh_confirm_registration.json') and
  chain['comparison_ref']==dict(path=str(MAIN/'confirm/comparison_01/result.json'),sha256=digest(MAIN/'confirm/comparison_01/result.json')) and
  chain['production_admitted'] is False and chain['successful_calls_or_QA_repeated'] is False,'Natural fresh chain PASS is required')
 need(cpu['status']==module.CPU_STATUS and cpu['source_count']==4 and cpu['expected_input_count']==len(cpu['entries']) and
  media['registration_sha256']==digest(MAIN/'fresh_confirm_registration.json') and len(media['accepted'])==4,'Complete fresh input/media phase required')
 for stage in ('B0','VERIFY'):
  receipt=chain[stage];count=receipt['calls'];stage_root=MAIN/'confirm'/stage
  need(type(count) is int and 0<count<=(48 if stage=='B0' else 240),'Missing actual fresh stage count')
  gate_path=MAIN/('gpu_admission_confirm_'+stage+'_v2.json')
  need(receipt['admission_ref']['path']==str(gate_path),'Wrong fresh stage admission path')
  gate=phase(gate_path,receipt['admission_ref']['sha256'])
  need(gate['group']=='confirm' and gate['stage']==stage and gate['gpu_job_name']==module.FRESH_JOBS[stage] and
   gate['expected_input_count']==count and gate['registration_sha256']==digest(MAIN/'fresh_recovery_registration_02.json') and
   gate['model_parameters']==module.MODEL_PARAMETERS and gate['optimizer_updates']==0,'Fresh model-stage identity changed')
  complete_path=stage_root/'gpu_01/completion.json';qa_path=stage_root/'replay_01/completion.json'
  need(receipt['gpu_completion_ref']['path']==str(complete_path) and receipt['first_QA_completion_ref']['path']==str(qa_path),'Wrong fresh completion paths')
  complete=phase(complete_path,receipt['gpu_completion_ref']['sha256'])
  qa=phase(qa_path,receipt['first_QA_completion_ref']['sha256'])
  need(receipt['resource_ref']['path']==str(module.RUN/'controller'/(module.FRESH_JOBS[stage]+'.resource.json')),'Wrong natural resource path')
  resource=phase(receipt['resource_ref']['path'],receipt['resource_ref']['sha256'])
  need(complete['status']=='PASS_ALL_RECALL_'+stage+'_CALLS_NOT_QUALITY' and complete['calls']==len(complete['entries'])==count and
   complete['admission_sha256']==digest(gate_path) and qa['status']=='PASS_ALL_RECALL_'+stage+'_INDEPENDENT_REPLAYS_NOT_QUALITY' and
   qa['calls']==len(qa['proofs'])==count and qa['CPU_only'] is True and qa['CUDA_initialized'] is False and
   qa['gpu_completion_sha256']==digest(complete_path) and qa['resource_terminal_sha256']==receipt['resource_ref']['sha256'] and
   resource['name']==module.FRESH_JOBS[stage] and resource['status']=='completed' and resource['exit_code']==0 and
   resource==receipt['resource'],'Fresh model/first-QA/natural-resource count is incomplete')
  identity=phase(stage_root/'gpu_01/model_identity.json',complete['model_identity_sha256'])
  module.verify_identity(identity['identity'])
  if stage=='B0':need(count==len(cpu['entries']),'Fresh B0 actual count differs from accepted input count')
 expected=dict(protocol_sha256=digest(MAIN/'protocol.json'),registration_sha256=digest(MAIN/'fresh_recovery_registration_02.json'),
  original_registration_sha256=digest(MAIN/'fresh_confirm_registration.json'),cpu_acceptance_sha256=digest(MAIN/'cpu_acceptance_confirm_v2.json'),
  verification_export_sha256=digest(MAIN/'confirm/VERIFY/verification_export.json'),first_B0_QA_sha256=digest(MAIN/'confirm/B0/replay_01/completion.json'),
  reference_completion_sha256=digest(pointer['path']))
 need(expected['protocol_sha256']==PROTOCOL_SHA,'Wrong consensus protocol')
 need(all(confirmation['bindings'][key]==value for key,value in expected.items()),'One of seven fresh comparison bindings changed')
 summary=lambda value:dict(status=value['status'],source_ids=[row['video_id'] for row in value['cases']],conditions=value['conditions'])
 value=dict(status='PASS_REAL_CONSENSUS_FRESH_PHASE_BEFORE_FIXED40_UPLOAD',utc=module.utc(),host=socket.gethostname(),
  protocol_sha256=PROTOCOL_SHA,target_exists=False,incoming_exists=False,chain_failure_exists=False,fresh_chain_process_alive=False,
  development=summary(development),confirmation=dict(summary(confirmation),bindings=confirmation['bindings']),
  chain_status=chain['status'],comparison_sha256=digest(MAIN/'confirm/comparison_01/result.json'),
  chain_comparison_sha256=chain['comparison_ref']['sha256'],expected_bindings=expected,
  preupload_phase_metadata_file_count=len(phase_files),
  preupload_phase_metadata_sha256=hashlib.sha256(json.dumps(phase_files,sort_keys=True,separators=(',',':')).encode()).hexdigest())
 return value
'''
    for token, value in {'__MAIN__': repr(MAIN), '__INCOMING__': repr(INCOMING),
                         '__PROTOCOL__': repr(PROTOCOL_SHA), '__COMMON__': repr(common_source)}.items():
        source = source.replace(token, value)
    ast.parse(source, filename='<readonly-consensus-gate-15>')
    return source


def deployment_program(common_source, data, manifest, preflight):
    program = gate_library(common_source)+r'''
EXPECTED_PREFLIGHT=__PREFLIGHT__
PAYLOAD=__PAYLOAD__
EXPECTED_BYTES=__BYTES__
EXPECTED_SHA=__SHA__
EXPECTED_MANIFEST=__MANIFEST__
EXPECTED_MEMBERS=set(EXPECTED_MANIFEST)|{'deployment_manifest.json'}
state=read_only_gate()
need(state['preupload_phase_metadata_sha256']==EXPECTED_PREFLIGHT['preupload_phase_metadata_sha256'] and
 state['expected_bindings']==EXPECTED_PREFLIGHT['expected_bindings'],'Frozen fresh evidence changed after the read-only pre-upload gate')
data=base64.b64decode(PAYLOAD,validate=True)
need(len(data)==EXPECTED_BYTES and hashlib.sha256(data).hexdigest()==EXPECTED_SHA and len(data)<1048576,'Incoming bundle bytes/SHA/budget differ')
phase='EXCLUSIVE_INCOMING_WRITE'
child=None
try:
 # Exclusive write prevents an unknown/racing incoming artifact being replaced.
 with INCOMING.open('xb') as stream:
  stream.write(data);stream.flush();os.fsync(stream.fileno())
 need(INCOMING.stat().st_size==EXPECTED_BYTES and digest(INCOMING)==EXPECTED_SHA,'Received incoming bundle differs')
 phase='CRC_MEMBER_SHA_AND_SAFE_PATHS'
 with zipfile.ZipFile(bytes_io.BytesIO(data)) as archive:
  names=archive.namelist()
  need(len(names)==len(set(names)) and set(names)==EXPECTED_MEMBERS,'ZIP members differ')
  for member in archive.infolist():
   name=member.filename;path=pathlib.PurePosixPath(name);mode=member.external_attr>>16
   need(name and '\\' not in name and '\x00' not in name and ':' not in name and not path.is_absolute() and
    all(part not in ('','.','..') for part in path.parts) and str(path)==name and not member.is_dir() and
    not stat.S_ISLNK(mode) and stat.S_IFMT(mode) in (0,stat.S_IFREG) and member.file_size<=1048576,'Unsafe ZIP member')
  need(archive.testzip() is None,'ZIP CRC differs')
  received_manifest=json.loads(archive.read('deployment_manifest.json'))
  need(received_manifest['schema']=='CONSENSUS_FIXED40_SMALL_CONTROL_AND_ORIGINAL_SILVER_V1' and
   received_manifest['files']==EXPECTED_MANIFEST,'Received manifest changed')
  for name,row in EXPECTED_MANIFEST.items():
   content=archive.read(name)
   need(len(content)==row['bytes'] and hashlib.sha256(content).hexdigest()==row['sha256'],'Member byte/SHA differs: '+name)
  TARGET.mkdir()
  for name in names:
   output=TARGET.joinpath(*pathlib.PurePosixPath(name).parts)
   need(output.resolve().is_relative_to(TARGET.resolve()),'Extracted path escaped new target')
   output.parent.mkdir(parents=True,exist_ok=True)
   content=archive.read(name)
   with output.open('xb') as stream:stream.write(content);stream.flush();os.fsync(stream.fileno())
   need(output.stat().st_size==len(content) and digest(output)==hashlib.sha256(content).hexdigest(),'Extracted file actual SHA differs: '+name)
 phase='FROZEN_SOURCE_PLAN_AND_REGISTRATION'
 sys.path.insert(0,str(TARGET/'code'))
 import facts_common as io,source_audit
 need(io.PROTOCOL_SHA==PROTOCOL_SHA and io.FACTS_ROOT==TARGET,'Wrong deployed current facts implementation')
 reference=TARGET/'reference/coverage_diagnostic_01.json'
 document=source_audit.load_reference(reference)
 sources=source_audit.audit_source_descriptors(document)
 views=source_audit.point_covering_views(document,sources)
 need(len(sources)==9 and len(views)==17,'The fixed source/view denominator changed')
 plan=dict(schema='RECALL_CONSENSUS_FIXED40_SOURCE_METADATA_PLAN_V1',scope=source_audit.SCOPE,sources=sources,views=views)
 io.save(TARGET/'source_plan.json',plan)
 need(not (MAIN/'confirm/chain_02/failure.json').exists(),'Fresh chain failure must remain absent')
 files=dict(io.confirmation_metadata_closure(MAIN))
 codes={}
 def add(path,expected=None,code=False):
  path=io.checked(path,expected);actual=io.sha(path)
  need(str(path) not in files or files[str(path)]==actual,'A frozen dependency changed: '+str(path))
  files[str(path)]=actual
  if code:codes[str(path)]=actual
  return dict(path=str(path),sha256=actual)
 refs={}
 canonical=dict(main_protocol_ref=MAIN/'protocol.json',authorization_ref=MAIN/'USER_AUTHORIZATION.json',
  dev_result_ref=MAIN/'development_01/result.json',selection_ref=MAIN/'selection_before_fresh_confirmation.json',
  confirm_result_ref=MAIN/'confirm/comparison_01/result.json',confirm_chain_completion_ref=MAIN/'confirm/chain_02/completion.json',
  fresh_recovery_registration_ref=MAIN/'fresh_recovery_registration_02.json',original_fresh_registration_ref=MAIN/'fresh_confirm_registration.json')
 for key,path in canonical.items():refs[key]=add(path)
 refs.update(source_plan_ref=add(TARGET/'source_plan.json'),reference_ref=add(reference),
  consensus_implementation_ref=add(TARGET/'code/consensus.py',__CONSENSUS__,True),
  merge_implementation_ref=add(TARGET/'code/merge_keep.py',__MERGE__,True))
 recovery=io.read(MAIN/'fresh_recovery_registration_02.json')
 for key in ('capacity_evidence_ref','processor_source_ref'):
  value=recovery[key];refs[key]=add(value['path'],value['sha256'],key=='processor_source_ref')
 for path,expected in io.code_files().items():add(path,expected,True)
 add(TARGET/'code/overlap_plan.py',__OVERLAP__,True)
 for path in io.runtime_dependencies()|io.processor_assets()|{str(io.CONFIG)}:
  add(path,code=path.endswith('.py'))
 for name in ('cv_contract.py','cv_grammar.py','cv_tokens.py'):add(io.CV_CODE/name,code=True)
 add(io.RUN/'resource_unlimited_v1_20261007/gpu_run.py',code=True)
 for source in sources:
  add(source['source_path'],source['source_sha256'])
  add(source['clock_path'],source['clock_sha256'])
 now=dt.datetime.now(dt.timezone.utc)
 registration=dict(schema=io.REGISTRATION_SCHEMA,status=io.REGISTRATION_STATUS,group='facts',source_scope='EXTERNAL_NONTEST_ONLY',
  scope=source_audit.SCOPE,source_count=io.SOURCE_COUNT,unique_input_count=io.INPUT_COUNT,model_parameters=io.MODEL_PARAMETERS,optimizer_updates=0,
  model_identity=dict(base_sha256=io.BASE_SHA,adapter_sha256=io.ADAPTER_SHA,enabled_TIME_layers=144),runtime=recovery['runtime'],
  gpu_budget=dict(io.GPU_BUDGET),gpu_jobs=dict(io.JOB_NAMES),deadline=(now+dt.timedelta(hours=6)).isoformat(),registered_at_utc=now.isoformat(),
  sources=sources,views=views,required_files=files,required_code_files=codes,**refs)
 io.save(TARGET/'registration.json',registration)
 # Static metadata/closure/geometry validation only. No original or new QA is run.
 io.registration(TARGET)
 source_audit.validate_registered_sources(dict(registration,schema='RECALL_FIXED40_EXECUTION_REGISTRATION_V1',status='REGISTERED_FIXED40_EXECUTION_AFTER_DEV_CONFIRM_PASS'))
 import facts_prepare
 facts_prepare.capacity_contract(registration)
 phase='LIVE_ARGV_RESOURCE_AND_UNIQUE_JOB_PREFLIGHT'
 ledger=io.rows(io.HOME_ROOT/'improvement_round1/gpu_ledger.jsonl')
 need(all(not any(row.get('name')==job for row in ledger) and not (io.RUN/'controller'/(job+'.resource.json')).exists()
  for job in io.JOB_NAMES.values()),'This fixed40 job already has a terminal/ledger history; never repeat it')
 active=io.HOME_ROOT/'improvement_round1/active_gpu_job.json'
 if active.exists():need(io.read(active).get('name') not in set(io.JOB_NAMES.values()),'This fixed40 job is already reserved')
 commands=process_commands()
 chain_script=str(TARGET/'code/facts_chain.py')
 need(not any(chain_script in row['argv'] or any(job in row['argv'] for job in io.JOB_NAMES.values()) for row in commands),
  'An actual fixed40 chain/wrapper already exists; no duplicate launcher')
 need(not (TARGET/'facts').exists() and not (TARGET/'inputs_01').exists() and not (TARGET/'admission_01').exists(),
  'Actual inputs or chain work already exist; this is not a resume')
 gpu=subprocess.run(['nvidia-smi','--query-gpu=index,name,memory.total,memory.used,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout
 need(any(line.split(',')[0].strip()=='0' for line in gpu.splitlines()),'Actual CUDA index 0 is unavailable')
 snapshot=dict(utc=io.utc(),host=socket.gethostname(),GPU=gpu,memory=pathlib.Path('/proc/meminfo').read_text(),
  disk=list(shutil.disk_usage(TARGET)),load_average=list(os.getloadavg()),
  active_gpu_job=io.read(active) if active.exists() else None,
  actual_commands=[row for row in commands if any(str(MAIN) in arg or 'gpu_run.py' in arg for arg in row['argv'])],
  processes=subprocess.run(['ps','-eo','pid,ppid,stat,pcpu,pmem,rss,comm','--sort=-pcpu'],capture_output=True,text=True,check=True).stdout.splitlines()[:25])
 io.save(TARGET/'resource_preflight_15.json',snapshot)
 argv=[str(io.HOME_ROOT/'env/qwen3vl_isolated_20260910/bin/python'),'-B','-u',chain_script,'run','--root',str(TARGET),'--group','facts']
 io.save(TARGET/'launch_claim_15.json',dict(utc=io.utc(),argv=argv,parent_CUDA='0',bundle_bytes=EXPECTED_BYTES,
  bundle_sha256=EXPECTED_SHA,registration_sha256=io.sha(TARGET/'registration.json'),production_admitted=False))
 phase='ONE_EXPLICIT_PARENT_START'
 environment=dict(os.environ,CUDA_VISIBLE_DEVICES='0',PYTHONDONTWRITEBYTECODE='1')
 with (TARGET/'parent_15.log').open('xb') as log:
  child=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,env=environment,start_new_session=True)
 process=pathlib.Path('/proc')/str(child.pid)
 ticks=process.joinpath('stat').read_text().split(') ',1)[1].split()[19]
 actual_argv=[part.decode() for part in process.joinpath('cmdline').read_bytes().split(b'\0') if part]
 cuda=[part.split(b'=',1)[1].decode() for part in process.joinpath('environ').read_bytes().split(b'\0') if part.startswith(b'CUDA_VISIBLE_DEVICES=')]
 need(actual_argv==argv and cuda==['0'],'Started parent actual argv/CUDA differs from the unique claim')
 value=dict(status='STARTED_UNIQUE_CONSENSUS_FIXED40_CHAIN_NOT_FACT_GATE',utc=io.utc(),host=socket.gethostname(),pid=child.pid,
  start_ticks=ticks,argv=actual_argv,parent_CUDA=cuda[0],bundle_bytes=EXPECTED_BYTES,bundle_sha256=EXPECTED_SHA,
  CRC_member_SHA_and_safe_paths_passed=True,registration_sha256=io.sha(TARGET/'registration.json'),
  preupload_phase_metadata_sha256=state['preupload_phase_metadata_sha256'],source_count=9,unique_input_count=17,
  fresh_real_PASS_bound=True,fact_quality='NOT_EVALUATED',production_admitted=False,no_426_or_veto_or_package_started=True)
 io.save(TARGET/'chain_launch_15.json',value)
 print(json.dumps(value))
except BaseException as error:
 if TARGET.exists():
  failure=TARGET/'deployment_failure_15.json'
  if not failure.exists():
   with failure.open('x',encoding='utf-8') as stream:
    json.dump(dict(stage=phase,error=repr(error),traceback=traceback.format_exc(),pid=child.pid if child else None,
     preserve_all_success_and_running_children=True,no_automatic_retry_or_retransmission=True),stream,indent=2)
 raise
'''
    values = {'__PREFLIGHT__': repr(preflight), '__PAYLOAD__': repr(base64.b64encode(data).decode('ascii')),
              '__BYTES__': str(len(data)), '__SHA__': repr(sha(data)), '__MANIFEST__': repr(manifest),
              '__CONSENSUS__': repr(CONSENSUS_SHA), '__MERGE__': repr(MERGE_SHA), '__OVERLAP__': repr(OVERLAP_SHA)}
    for token, value in values.items():
        program = program.replace(token, value)
    ast.parse(program, filename='<unique-consensus-fixed40-deployment-15>')
    return program


def main():
    require(not any(path.exists() or path.is_symlink() for path in (BUNDLE, PREFLIGHT, RECEIPT)),
            'Local deployment artifacts already exist; inspect their outcomes without rerunning')
    files = local_files()
    common_source = files['code/facts_common.py'].decode('utf-8-sig')
    # Nothing has been uploaded/written remotely before this read-only gate.
    preflight = remote(gate_library(common_source)+'\nprint(json.dumps(read_only_gate()))\n')
    validate_pass_summary(preflight)
    save_exclusive(PREFLIGHT, preflight)
    manifest = {name: dict(bytes=len(content), sha256=sha(content)) for name, content in files.items()}
    files['deployment_manifest.json'] = json.dumps(dict(schema='CONSENSUS_FIXED40_SMALL_CONTROL_AND_ORIGINAL_SILVER_V1',
        files=manifest, no_media_tensors_or_weights=True), ensure_ascii=False, sort_keys=True).encode('utf-8')
    with zipfile.ZipFile(BUNDLE, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    data = BUNDLE.read_bytes()
    validate_archive(data, manifest)
    # The second call repeats the read-only evidence comparison before its first
    # exclusive incoming write. A lost connection is an unknown outcome, not retry authority.
    receipt = remote(deployment_program(common_source, data, manifest, preflight), timeout=180)
    receipt['preupload_gate'] = preflight
    save_exclusive(RECEIPT, receipt)
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == '__main__':
    main()
