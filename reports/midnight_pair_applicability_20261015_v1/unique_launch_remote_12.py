expected_route_bytes=17564
expected_route_sha='3dc1bcade7adc0be868e34f735120b6e5978aa97f4bbfb529274a6cc2a64942f'
import pathlib,hashlib,json,subprocess,os,time,datetime,socket
root=pathlib.Path('/home/inspur/aic_video_work/midnight_pair_applicability_20261015_v1');p=root/'public_routes.json'
assert socket.gethostname()=='inspur-NP5570M5' and p.stat().st_size==expected_route_bytes and hashlib.sha256(p.read_bytes()).hexdigest()==expected_route_sha
routes=json.loads(p.read_text());assert len(routes['routes'])==6 and routes['windows_video_body_bytes']==0
assert routes['source_candidates_sha256']==hashlib.sha256((root/'source_candidates.json').read_bytes()).hexdigest()
manifest=json.loads((root/'deployment_manifest.json').read_text());controller=root/'controller.py'
assert hashlib.sha256(controller.read_bytes()).hexdigest()==manifest['controller.py'] and not(root/'control_01').exists()
authorization=dict(scope='ONE_SUPPLEMENTAL_SHORT_PAIR_MEDIA_CPU_GPU_CHAIN',root=str(root),controller_sha256=manifest['controller.py'],no_automatic_retry=True,approved_by='MAIN_AGENT_EXPLICIT_REVIEW_AND_UNIQUE_LAUNCH_AUTHORIZATION_20261015',utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
with (root/'launch_authorization.json').open('x') as f:json.dump(authorization,f,indent=2)
argv=['/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python','-B',str(controller)]
with (root/'controller_01.log').open('x') as log:
 process=subprocess.Popen(argv,env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1'),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 time.sleep(.2)
 receipt=dict(status='UNIQUE_LAUNCH_REQUESTED_NOT_COMPLETION',pid=process.pid,returncode_at_receipt=process.poll(),argv=argv,parent_CUDA='0',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),controller_sha256=manifest['controller.py'],routes_bytes=expected_route_bytes,routes_sha256=expected_route_sha,new_selection_sha256=hashlib.sha256((root/'new_selection.json').read_bytes()).hexdigest(),explicit_remaining_deployment_recovery_07=True)
 if process.poll() is None:
  receipt['start_ticks']=pathlib.Path('/proc/'+str(process.pid)+'/stat').read_text().split()[21]
  receipt['actual_cmdline']=[x.decode() for x in pathlib.Path('/proc/'+str(process.pid)+'/cmdline').read_bytes().split(bytes([0])) if x]
 with (root/'unique_launch_12.json').open('x') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt))
