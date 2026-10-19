"""Launch once after actual complete CPU input acceptance, on the shared wrapper."""
import os,pathlib,json,hashlib,datetime as dt,subprocess,shutil
W=pathlib.Path('/home/inspur/aic_video_work');F=W/'visual_pair_formal_20261018_v1'
RUN=W/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
PY=W/'env/qwen3vl_isolated_20260910/bin/python';JOB='visual_pair_formal158_base_order316_20261018_v1'
def read(p):return json.loads(p.read_text())
def ref(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def save(p,x):
    with p.open('x') as s:json.dump(x,s,indent=2)
assert os.uname().nodename=='inspur-NP5570M5'
assert dt.datetime.now(dt.timezone.utc)<dt.datetime(2026,10,18,15,35,tzinfo=dt.timezone.utc),'Need enough measured budget for model+terminal+package'
qa=read(F/'input_acceptance_01.json');assert qa['status']=='PASS_REGISTERED_FIRST_INDEPENDENT_REAL_PIXEL_PATCH_TOKEN_SOURCE_PTS_QA' and len(qa['inputs'])==316
assert read(F/'cpu_remaining_chain_05/completion.json')['status']=='PASS_ALL316_FIRST_INPUT_QA_COLOR_REMAINING'
assert not (F/'gpu_launch_01.json').exists() and not (RUN/'controller'/(JOB+'.resource.json')).exists()
ledger=(W/'improvement_round1/gpu_ledger.jsonl').read_text();assert not any(json.loads(x).get('name')==JOB for x in ledger.splitlines() if x.strip())
code=F/'code_v5/visual_pair_formal_v5.py'
resources=dict(host=os.uname().nodename,load=os.getloadavg(),gpu=subprocess.run(['nvidia-smi','--query-gpu=index,memory.used,utilization.gpu','--format=csv,noheader'],capture_output=True,text=True,check=True).stdout.strip(),gpu_apps=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],capture_output=True,text=True,check=True).stdout.strip(),disk_free=shutil.disk_usage(W).free,meminfo=pathlib.Path('/proc/meminfo').read_text())
reason='All316realCPU inputs accepted. Current host/resources '+json.dumps({k:v for k,v in resources.items() if k!='meminfo'})+'. Pilot34 measured117.89seconds including model/terminal,peak17.55GiB;316twoimage calls expected below900sec;persist outputs<=16MiB. ExistingCPU shards finished,protectexternaljobs and CONTROL5STOP. No fixedfreecapacity thresholds.'
command=[str(PY),str(RUN/'resource_unlimited_v1_20261007/gpu_run.py'),'--name',JOB,'--max-seconds','900','--planned-output-bytes','16777216','--capacity-reason',reason,'--queue-seconds','120','--',str(PY),'-B',str(code),'gpu']
save(F/'gpu_launch_01.json',dict(command=command,resources=resources,code_ref=ref(code),input_acceptance_ref=ref(F/'input_acceptance_01.json'),registration_ref=ref(F/'registration_01.json'),utc=dt.datetime.now(dt.timezone.utc).isoformat()))
with (F/'gpu_wrapper_01.log').open('xb') as log:
    p=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES='0'))
ticks=int(pathlib.Path('/proc/'+str(p.pid)+'/stat').read_text().rsplit(') ',1)[1].split()[19])
save(F/'gpu_started_01.json',dict(pid=p.pid,start_ticks=ticks,utc=dt.datetime.now(dt.timezone.utc).isoformat()))
print(json.dumps(dict(status='UNIQUE_FORMAL_GPU_WRAPPER_STARTED',job=JOB,pid=p.pid,calls=316,resources={k:v for k,v in resources.items() if k!='meminfo'})))
