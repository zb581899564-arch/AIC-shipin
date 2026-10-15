"""Deploy new small fixed-fact controls only after actual dev/confirm PASS.

This is not a recovery/overwrite/production launcher. The separate fact chain
has its own one-shot registration, first CPU inputs, shared jobs and terminal.
"""
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

WORK = Path(__file__).resolve().parents[2]
REPORT = Path(__file__).resolve().parent
REMOTE_ROOT = '/home/inspur/aic_video_work/recall_expansion_verify40_46_20261014_v1'
SSH = 'aic-inspur-home'
NAMES = ('facts_common.py', 'facts_infer.py', 'facts_verify.py', 'facts_chain.py',
         'facts_prepare.py', 'facts_admit.py', 'source_audit.py', 'facts_veto.py')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def remote(script, timeout=50):
    command = 'python3 -c "import base64;exec(base64.b64decode(\'' + base64.b64encode(script.encode()).decode() + '\'))"'
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=12',
                             SSH, command], capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stderr or result.stdout)
    return json.loads(result.stdout)


def main():
    # The first remote operation is read-only. A failed/pending confirmation
    # never uploads, writes a registration, acquires a model or starts a chain.
    gate = remote(r'''
import datetime,hashlib,json,pathlib,socket
r=pathlib.Path('__MAIN__')
assert socket.gethostname()=='inspur-NP5570M5'
protocol_sha=hashlib.sha256((r/'protocol.json').read_bytes()).hexdigest()
assert protocol_sha=='9b7c5936ad1abcb08ae863e3ff03e968b6fa765936250fdbd27a23fc706be201'
for group,chain in [('dev','chain_02'),('confirm','chain_03')]:
 c=json.loads((r/group/chain/'completion.json').read_text())
 p=r/group/'comparison_01/result.json';x=json.loads(p.read_text())
 assert c['status']=='COMPLETE_EXTERNAL_GROUP_PROXY_PASS_PENDING_FIXED_FACTS'
 assert c['comparison_sha256']==hashlib.sha256(p.read_bytes()).hexdigest()
 assert x['status']=='PASS_REGISTERED_PROXY_GROUP_PENDING_FIXED_FACT_GATE' and x['group']==group
 assert x['bindings']['protocol_sha256']==protocol_sha and x['conditions'] and all(v is True for v in x['conditions'].values()) and len(x['cases'])==4
 assert not (r/group/chain/'failure.json').exists()
control=json.loads((r/'confirm/control_07/completion.json').read_text())
assert control['status']=='COMPLETE_EXTERNAL_GROUP_PROXY_PASS_PENDING_FIXED_FACTS' and control['chain_completion_sha256']==hashlib.sha256((r/'confirm/chain_03/completion.json').read_bytes()).hexdigest()
assert not (r/'confirm/control_07/failure.json').exists()
target=r/'fixed40_01';assert not target.exists(),'Independent fixed40 root already exists; explicit inspection required, no overwrite/restart'
print(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),host=socket.gethostname(),dev_confirm_pass=True,protocol_sha256=protocol_sha)))
'''.replace('__MAIN__', REMOTE_ROOT))
    files = {'code/'+name: (WORK/'improvement/recall_fixed40_v1'/name).read_bytes() for name in NAMES}
    for name in ('merge_keep.py', 'overlap_plan.py'):
        files['code/'+name] = (WORK/'improvement/recall_expansion_verify40_46_v1'/name).read_bytes()
    reference = (WORK/'reports/reliable_reference_20261012_v1/coverage_diagnostic_01.json').read_bytes()
    assert len(reference) == 594682 and sha(reference) == '37a7c93876334b3a5d0c222e3a7f99727778d50f28f3a1172e860d19d3dc82b8'
    files['reference/coverage_diagnostic_01.json'] = reference
    manifest = {name: dict(bytes=len(data), sha256=sha(data)) for name, data in files.items()}
    files['deployment_manifest.json'] = json.dumps(dict(schema='FIXED40_SMALL_CONTROL_AND_ORIGINAL_FACT_METADATA_V1',
        files=manifest, no_media_or_tensor_or_old_full_export=True), ensure_ascii=False, sort_keys=True).encode()
    bundle = REPORT/'fixed40_control_13.zip'
    with zipfile.ZipFile(bundle, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    size, digest = bundle.stat().st_size, sha(bundle.read_bytes())
    assert size < 1 << 20, 'Only necessary small control/fact metadata is authorized here'
    incoming = REMOTE_ROOT+'/incoming_fixed40_control_13.zip'
    existence = remote("import json,pathlib; p=pathlib.Path("+repr(incoming)+");print(json.dumps({'exists':p.exists()}))")
    if existence['exists']:
        raise RuntimeError('Incoming artifact already exists; inspect/reuse it explicitly without retransmission')
    upload = subprocess.run(['scp', '-q', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=12',
                             str(bundle), SSH+':'+incoming], capture_output=True, text=True, timeout=75)
    if upload.returncode:
        raise RuntimeError('Small upload outcome requires remote size/SHA inspection; no automatic retransmission: '+upload.stderr)
    script = r'''
import datetime as dt,hashlib,json,os,pathlib,shutil,socket,subprocess,sys,zipfile
main=pathlib.Path('__MAIN__');root=main/'fixed40_01';bundle=pathlib.Path('__BUNDLE__')
assert socket.gethostname()=='inspur-NP5570M5' and not root.exists()
assert bundle.stat().st_size==__SIZE__ and hashlib.sha256(bundle.read_bytes()).hexdigest()=='__SHA__'
with zipfile.ZipFile(bundle) as z:
 assert z.testzip() is None
 manifest=json.loads(z.read('deployment_manifest.json'))['files']
 assert set(z.namelist())==set(manifest)|{'deployment_manifest.json'}
 for name,row in manifest.items():
  p=pathlib.PurePosixPath(name);assert not p.is_absolute() and '..' not in p.parts
  data=z.read(name);assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
 root.mkdir();z.extractall(root)
sys.path.insert(0,str(root/'code'))
import facts_common as io,source_audit
protocol_ref=dict(path=str(main/'protocol.json'),sha256=io.sha(main/'protocol.json'))
assert protocol_ref['sha256']=='9b7c5936ad1abcb08ae863e3ff03e968b6fa765936250fdbd27a23fc706be201'
refs=dict(main_protocol_ref=protocol_ref,authorization_ref=dict(path=str(main/'USER_AUTHORIZATION.json'),sha256=io.sha(main/'USER_AUTHORIZATION.json')))
for group,chain in [('dev','chain_02'),('confirm','chain_03')]:
 p=main/group/'comparison_01/result.json';result=io.read(p);complete=io.read(main/group/chain/'completion.json')
 assert complete['status']=='COMPLETE_EXTERNAL_GROUP_PROXY_PASS_PENDING_FIXED_FACTS' and complete['comparison_sha256']==io.sha(p)
 assert result['status']=='PASS_REGISTERED_PROXY_GROUP_PENDING_FIXED_FACT_GATE' and result['conditions'] and all(v is True for v in result['conditions'].values()) and len(result['cases'])==4
 refs[group+'_result_ref']=dict(path=str(p),sha256=io.sha(p))
control=io.read(main/'confirm/control_07/completion.json')
assert control['status']=='COMPLETE_EXTERNAL_GROUP_PROXY_PASS_PENDING_FIXED_FACTS' and control['chain_completion_sha256']==io.sha(main/'confirm/chain_03/completion.json')
assert not (main/'confirm/control_07/failure.json').exists()
reference=root/'reference/coverage_diagnostic_01.json'
document=source_audit.load_reference(reference);sources=source_audit.audit_source_descriptors(document);views=source_audit.point_covering_views(document,sources)
plan=dict(schema='RECALL_FIXED40_SOURCE_METADATA_PLAN_V1',scope=source_audit.SCOPE,sources=sources,views=views)
io.save(root/'source_plan.json',plan)
refs.update(source_plan_ref=dict(path=str(root/'source_plan.json'),sha256=io.sha(root/'source_plan.json')),
 reference_ref=dict(path=str(reference),sha256=io.sha(reference)),
 merge_implementation_ref=dict(path=str(root/'code/merge_keep.py'),sha256=io.sha(root/'code/merge_keep.py')))
files=dict(io.code_files())
for p in io.runtime_dependencies()|io.processor_assets()|{str(io.CONFIG)}:
 files[p]=io.sha(p)
for name in ['cv_contract.py','cv_grammar.py','cv_tokens.py']:
 p=io.CV_CODE/name;files[str(p)]=io.sha(p)
for value in refs.values():files[value['path']]=value['sha256']
p=root/'code/overlap_plan.py';files[str(p)]=io.sha(p)
for source in sources:
 for key,digest in [('source_path','source_sha256'),('clock_path','clock_sha256')]:
  p=pathlib.Path(source[key]);assert p.is_file() and io.sha(p)==source[digest];files[str(p)]=source[digest]
for group in ('dev','confirm'):
 for p in [main/('cpu_acceptance_'+group+'.json'),main/group/'VERIFY/verification_export.json']:
  files[str(p)]=io.sha(p)
now=dt.datetime.now(dt.timezone.utc)
registration=dict(schema=io.REGISTRATION_SCHEMA,status=io.REGISTRATION_STATUS,group='facts',source_scope='EXTERNAL_NONTEST_ONLY',
 scope=source_audit.SCOPE,source_count=9,unique_input_count=17,model_parameters=io.MODEL_PARAMETERS,optimizer_updates=0,
 model_identity=dict(base_sha256=io.BASE_SHA,adapter_sha256=io.ADAPTER_SHA,enabled_TIME_layers=144),
 gpu_budget=io.GPU_BUDGET,deadline=(now+dt.timedelta(hours=6)).isoformat(),registered_at_utc=now.isoformat(),
 sources=sources,views=views,required_files=files,required_code_files=io.code_files(),**refs)
io.save(root/'registration.json',registration)
# All source/implementation closure and both full PASS gates are checked before
# any first input/model operation. This loop does not create any CPU evidence.
io.registration(root);source_audit.validate_registered_sources(registration)
ledger=io.rows(io.HOME_ROOT/'improvement_round1/gpu_ledger.jsonl')
assert all(not any(row.get('name')==job for row in ledger) and not (io.RUN/'controller'/(job+'.resource.json')).exists() for job in io.JOB_NAMES.values()),'A previous successful/failed job history needs explicit inspection; never repeat it'
gpu=subprocess.run(['nvidia-smi','--query-gpu=index,name,memory.total,memory.used,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout
assert any(line.split(',')[0].strip()=='0' for line in gpu.splitlines())
actual_commands=[]
for p in pathlib.Path('/proc').glob('[0-9]*/cmdline'):
 try:
  args=[part.decode(errors='replace') for part in p.read_bytes().split(b'\0') if part]
  assert str(root/'code/facts_chain.py') not in args,'Actual independent chain already exists; no second launcher'
  if any(str(main) in arg for arg in args):actual_commands.append(dict(pid=int(p.parent.name),argv=args))
 except (FileNotFoundError,PermissionError,ProcessLookupError):pass
snap=dict(utc=io.utc(),host=socket.gethostname(),GPU=gpu,memory=pathlib.Path('/proc/meminfo').read_text(),disk=list(shutil.disk_usage(root)),actual_commands=actual_commands,
 ps=subprocess.run(['ps','-eo','pid,ppid,stat,pcpu,pmem,args','--sort=-pcpu'],capture_output=True,text=True,check=True).stdout.splitlines()[:25])
io.save(root/'resource_preflight_13.json',snap)
argv=[str(io.HOME_ROOT/'env/qwen3vl_isolated_20260910/bin/python'),'-B','-u',str(root/'code/facts_chain.py'),'run','--root',str(root),'--group','facts']
io.save(root/'launch_claim_13.json',dict(argv=argv,utc=io.utc(),registration_sha256=io.sha(root/'registration.json')))
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0')
with (root/'parent_13.log').open('xb') as log:
 child=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,env=env,start_new_session=True)
ticks=(pathlib.Path('/proc')/str(child.pid)/'stat').read_text().split(') ',1)[1].split()[19]
receipt=dict(utc=io.utc(),host=socket.gethostname(),pid=child.pid,start_ticks=ticks,argv=argv,parent_CUDA='0',
 bundle_bytes=__SIZE__,bundle_sha256='__SHA__',CRC_and_member_SHA_passed=True,registration_sha256=io.sha(root/'registration.json'),
 dev_confirm_pass=True,source_count=9,unique_input_count=17,production_admitted=False)
io.save(root/'chain_launch_13.json',receipt);print(json.dumps(receipt))
'''
    for token, value in {'__MAIN__': REMOTE_ROOT, '__BUNDLE__': incoming, '__SIZE__': str(size), '__SHA__': digest}.items():
        script = script.replace(token, value)
    receipt = remote(script, timeout=60)
    receipt['preupload_gate'] = gate
    path = REPORT/'fixed40_deployment_launch_13.json'
    with path.open('x', encoding='utf8') as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == '__main__':
    main()
