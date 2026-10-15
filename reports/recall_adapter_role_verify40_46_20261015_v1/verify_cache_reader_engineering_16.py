"""One CPU deserialization equivalence check, never a model/processor/QA replay."""
import ast
import base64
import hashlib
import json
from pathlib import Path
import subprocess

REPORT=Path(__file__).resolve().parent;WORK=REPORT.parents[1]
assert not (REPORT/'cache_reader_engineering_16.json').exists()
source=(WORK/'improvement/recall_role_fixed40_v1/facts_common.py').read_text(encoding='utf8')
tree=ast.parse(source);node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='load_cache')
new_function=ast.get_source_segment(source,node)
code=r'''
import ast,base64,datetime as dt,gzip,hashlib,json,os,pathlib,resource,shutil,socket,struct,subprocess,sys,time
h=pathlib.Path('/home/inspur/aic_video_work');main=h/'recall_adapter_role_verify40_46_20261015_v1';fresh=main/'fresh_01'
root=h/'recall_cache_io_engineering_20261015_v2'
assert socket.gethostname()=='inspur-NP5570M5' and not root.exists()
read=lambda p:json.loads(pathlib.Path(p).read_text());sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
cpu=read(fresh/'cpu_acceptance_confirm.json');qa=read(fresh/'confirm/B0/input_qa_01/completion.json')
assert len(cpu['entries'])==qa['calls']==28
entry=cpu['entries'][0];proof=read(entry['proof_path']);cache=pathlib.Path(proof['encoded_tensor_path'])
assert cache.is_relative_to(fresh) and sha(cache)==proof['encoded_tensor_sha256']
with cache.open('rb') as stream:stream.seek(-4,2);uncompressed=struct.unpack('<I',stream.read(4))[0]
assert 0<uncompressed<1<<32
mem={line.split(':')[0]:int(line.split()[1])*1024 for line in pathlib.Path('/proc/meminfo').read_text().splitlines() if line.split(':')[0] in ['MemTotal','MemAvailable']}
assert mem['MemAvailable']>4*uncompressed,'Actual capacity does not admit even this CPU-only equivalence check'
processes=subprocess.run(['ps','-eo','pid,ppid,stat,pcpu,rss,args','--sort=-pcpu','--width','2000'],capture_output=True,text=True,check=True).stdout.splitlines()[:12]
os.environ['CUDA_VISIBLE_DEVICES']='';sys.dont_write_bytecode=True;sys.path.insert(0,str(fresh/'code'))
import model_common as oldio
import torch
assert not torch.cuda.is_initialized()
scope=dict(Path=pathlib.Path,gzip=gzip,os=os,require=oldio.require)
exec(compile(__NEW_FUNCTION__,'<registered_new_single_inflate_reader>','exec'),scope)
root.mkdir()
registration=dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),scope='CPU_CACHE_DESERIALIZATION_ENGINEERING_ONLY',
 source_cache=dict(path=str(cache),sha256=sha(cache),bytes=cache.stat().st_size),
 original_loader=dict(path=str(fresh/'code/model_common.py'),sha256=sha(fresh/'code/model_common.py')),
 new_function_sha256=hashlib.sha256(__NEW_FUNCTION__.encode()).hexdigest(),new_function=__NEW_FUNCTION__,
 actual_uncompressed_bytes=uncompressed,capacity=mem,observed_tasks=processes,disk=list(shutil.disk_usage(h)),gpu=subprocess.run(['nvidia-smi','--query-gpu=index,memory.used,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout,model_calls=0,processor_calls=0,
 decodes=0,first_input_or_output_QA_runs=0,quality_comparisons=0,no_frozen_file_changes=True)
with (root/'registration.json').open('x') as f:json.dump(registration,f,indent=2)
def io_rchar():return int([x.split(':',1)[1] for x in pathlib.Path('/proc/self/io').read_text().splitlines() if x.startswith('rchar:')][0])
def measure(loader):
 before=io_rchar();start=time.perf_counter();v=loader(cache);elapsed=time.perf_counter()-start
 return v,dict(elapsed_seconds=elapsed,process_rchar_bytes=io_rchar()-before)
old,old_stats=measure(oldio.load_cache);new,new_stats=measure(scope['load_cache'])
assert old.keys()==new.keys() and all(a.device.type==b.device.type=='cpu' and a.dtype==b.dtype and a.shape==b.shape and
 torch.equal(a.contiguous().reshape(-1).view(torch.uint8),b.contiguous().reshape(-1).view(torch.uint8)) for a,b in zip(old.values(),new.values()))
assert sha(cache)==proof['encoded_tensor_sha256'] and not torch.cuda.is_initialized()
value=dict(status='PASS_CPU_CACHE_READER_BIT_EQUIVALENCE_NOT_MODEL_OR_QUALITY_QA',utc=dt.datetime.now(dt.timezone.utc).isoformat(),
 registration_sha256=sha(root/'registration.json'),source_cache_sha256=sha(cache),old=old_stats,new=new_stats,
 all_CPU_tensor_keys_shapes_dtypes_bits_identical=True,source_file_unchanged=True,peak_process_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
 tensor_keys=sorted(old),model_calls=0,processor_calls=0,media_decodes=0,first_input_or_output_QA_runs=0,quality_comparisons=0,
 deployed_current_frozen_chain=False,production_admitted=False)
data=json.dumps(value,indent=2).encode()
with (root/'completion.json').open('xb') as f:f.write(data)
print(json.dumps(dict(linux_path=str(root/'completion.json'),bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),base64=base64.b64encode(data).decode())))
'''
# Keep the source snippet in stdin, never interpolate it into a shell command.
code=code.replace('__NEW_FUNCTION__',repr(new_function))
ast.parse(code)
result=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
    '-o','ServerAliveInterval=10','-o','ServerAliveCountMax=2','aic-inspur-home','/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python -B -'],
    input=code,text=True,encoding='utf8',capture_output=True,timeout=120)
if result.returncode:raise RuntimeError('Inspect the unique engineering receipt before an explicit recovery: '+result.stderr[-4000:])
env=json.loads(result.stdout);data=base64.b64decode(env.pop('base64'))
assert len(data)==env['bytes'] and hashlib.sha256(data).hexdigest()==env['sha256']
with (REPORT/'cache_reader_engineering_16.json').open('xb') as f:f.write(data)
with (REPORT/'cache_reader_transfer_16.json').open('x') as f:json.dump(dict(**env,Windows_size_SHA_pass=True),f,indent=2)
print(data.decode())
