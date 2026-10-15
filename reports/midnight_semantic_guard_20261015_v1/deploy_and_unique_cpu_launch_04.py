import pathlib,json,hashlib,zipfile,subprocess,os,datetime,time
root=pathlib.Path('/home/inspur/aic_video_work/midnight_semantic_guard_20261015_v1');archive=root/'semantic_guard_dev_control_02.zip'
assert archive.stat().st_size==15218 and hashlib.sha256(archive.read_bytes()).hexdigest()=='6ef184f808c781ad26763d0cd1f412ca9b0f9f2228b572e7e77eb35d9088bfe4'
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 manifest=json.loads(z.read('deployment_manifest.json'));assert set(z.namelist())==set(manifest)|{'deployment_manifest.json'}
 for name,digest in manifest.items():
  p=pathlib.Path(name);assert not p.is_absolute() and '..' not in p.parts and (root/p).resolve().is_relative_to(root) and hashlib.sha256(z.read(name)).hexdigest()==digest
 z.extractall(root)
for name,digest in manifest.items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest
with (root/'deployment_acceptance.json').open('x') as f:json.dump(dict(status='PASS_BYTES_SHA_CRC_MEMBERS_DEPLOYED',bytes=15218,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),members=len(manifest)+1),f)
python='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
with (root/'register_development.log').open('x') as f:
 result=subprocess.run([python,'-B',str(root/'code/register_development.py'),'--root',str(root)],env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'),stdout=f,stderr=subprocess.STDOUT)
with (root/'registration_terminal.json').open('x') as f:json.dump(dict(returncode=result.returncode),f)
if result.returncode:
 print(json.dumps(dict(status='FIRST_REGISTRATION_FAILED_NO_RETRY',log_tail=(root/'register_development.log').read_text()[-2500:])))
 raise SystemExit(result.returncode)
def ref(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
controller=root/'code/run_development.py';registration=root/'development_registration.json';protocol=root/'protocol.json'
authorization=dict(scope='ONE_NEW_SEMANTIC_GUARD_DEVELOPMENT_CPU_COMPARISON',controller_ref=ref(controller),registration_ref=ref(registration),automatic_retry=False,approved_by='MAIN_AGENT_EXPLICIT_POST_REVIEW_CPU_AUTHORIZATION_20261015',utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
with (root/'development_launch_authorization.json').open('x') as f:json.dump(authorization,f,indent=2)
argv=[python,'-B',str(controller)]
with (root/'development_controller.log').open('x') as log:
 process=subprocess.Popen(argv,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 time.sleep(.2)
 receipt=dict(status='UNIQUE_CPU_DEVELOPMENT_LAUNCH_REQUESTED_NOT_QUALITY',pid=process.pid,argv=argv,CUDA_VISIBLE_DEVICES='',returncode_at_receipt=process.poll(),registration_ref=ref(registration),protocol_ref=ref(protocol),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),new_model_calls=0,new_media_downloads=0)
 if process.poll() is None:
  receipt['start_ticks']=pathlib.Path('/proc/'+str(process.pid)+'/stat').read_text().split()[21]
  receipt['actual_cmdline']=[x.decode() for x in pathlib.Path('/proc/'+str(process.pid)+'/cmdline').read_bytes().split(bytes([0])) if x]
 with (root/'unique_cpu_launch_04.json').open('x') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt))
