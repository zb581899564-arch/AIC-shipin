"""First unchanged source quality probe after the failed3fps archive route."""
import hashlib
import io
import json
import zipfile
from pathlib import Path

from deploy_media_batch_04 import PY, REMOTE, REPORT, ssh_script
from stage_common_04 import sha, utc

TEMP = Path('C:/Users/33056/AppData/Local/Temp/aic_third_reference_20261013')


def deploy(files, claim, entry, registration):
    manifest = {name:dict(bytes=path.stat().st_size,sha256=sha(path)) for name,path in files.items()}
    archive=io.BytesIO()
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for name,path in files.items():z.writestr(name,path.read_bytes())
        z.writestr('manifest.json',json.dumps(manifest,indent=2))
    raw=archive.getvalue()
    with (REPORT/(claim+'_control.zip')).open('xb') as f:f.write(raw)
    script='''import datetime,hashlib,io,json,os,pathlib,socket,subprocess,sys,zipfile
base=pathlib.Path(REMOTE)
assert socket.gethostname()=='inspur-NP5570M5'
assert not (base/CLAIM).exists(),'Existing launch claim; never repeat'
raw=sys.stdin.buffer.read();assert len(raw)==SIZE and hashlib.sha256(raw).hexdigest()==DIGEST
z=zipfile.ZipFile(io.BytesIO(raw));assert z.testzip() is None
manifest=json.loads(z.read('manifest.json'));assert set(z.namelist())==set(manifest)|{'manifest.json'}
for name,item in manifest.items():
 p=base/name;assert p.resolve().is_relative_to(base.resolve())
 b=z.read(name);assert len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['sha256']
 if p.exists():assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256']
for name in manifest:
 p=base/name
 if not p.exists():
  p.parent.mkdir(parents=True,exist_ok=True)
  with p.open('xb') as f:f.write(z.read(name))
receipt={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'members':manifest}
argv=[PY,'-B',str(base/ENTRY),str(base/REGISTRATION)]
with (base/CLAIM).open('x') as f:json.dump({'utc':receipt['utc'],'argv':argv,'new_model_calls':0},f,indent=2)
env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']=''
log=(base/(CLAIM+'.log')).open('xb')
p=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
launch={'utc':receipt['utc'],'pid':p.pid,'argv':argv,'new_model_calls':0}
with (base/(CLAIM+'.receipt.json')).open('x') as f:json.dump({'transfer':receipt,'launch':launch},f,indent=2)
print(json.dumps({'transfer':receipt,'launch':launch}))'''
    script=script.replace('REMOTE',repr(REMOTE)).replace('CLAIM',repr(claim+'.json')).replace('ENTRY',repr(entry)).replace('REGISTRATION',repr(registration)).replace('SIZE',str(len(raw))).replace('DIGEST',repr(hashlib.sha256(raw).hexdigest())).replace('PY',repr(PY))
    receipt=ssh_script(script,raw)
    if receipt['transfer']['members']!=manifest or receipt['transfer']['sha256']!=hashlib.sha256(raw).hexdigest():
        raise ValueError('Actual control transfer differs from local')
    with (REPORT/(claim+'_deployment.json')).open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
    return receipt


def fresh_host_snapshot(name):
    script='''import json,pathlib,socket,subprocess,shutil,os
b=pathlib.Path(REMOTE);assert socket.gethostname()=='inspur-NP5570M5'
print(json.dumps({'hostname':socket.gethostname(),'cpu_count':os.cpu_count(),'load':os.getloadavg(),
 'memory':pathlib.Path('/proc/meminfo').read_text(),'disk':list(shutil.disk_usage(b)),
 'jobs':subprocess.run(['ps','-eo','pid,ppid,pcpu,pmem,args','--sort=-pcpu'],capture_output=True,text=True).stdout[:18000],
 'gpu':subprocess.run(['nvidia-smi','--query-gpu=index,name,memory.total,memory.used,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True).stdout}))'''.replace('REMOTE',repr(REMOTE))
    snapshot=ssh_script(script)
    with (REPORT/name).open('x',encoding='utf-8') as f:json.dump(snapshot,f,indent=2)
    return snapshot


def main():
    if (REPORT/'direct_source_registration_05.json').exists():
        raise ValueError('Direct source registration exists; inspect, do not repeat')
    fresh_host_snapshot('direct_source_host_resources_05.json')
    inventory=json.loads((TEMP/'raw_media_effective20_inventory_05.json').read_text())
    original=REPORT/'metadata_export_01/metadata_02/source_registration_01.json'
    scope=dict(status='DIRECT_PUBLIC_SOURCE_RESEARCH_SCOPE_PENDING_REAL_NATIVE_ACCEPTANCE',utc=utc(),
        publisher='TornadoLabs/activitynet',revision=inventory['metadata_revision'],
        publisher_card_sha256=sha(TEMP/'tornadolabs_card_05.md'),
        metadata_inventory_sha256=sha(TEMP/'tornadolabs_metadata.jsonl'),
        purpose='Private external research validation, no model training or raw media redistribution',
        source_quality='Publisher claim; independent original PTS/RGB/native64 validation required',
        rights='Academic source terms; videos retain original uploader rights. Not a commercial-rights grant.',
        access_uses_credentials_or_bypasses_restrictions=False,
        user_public_source_to_Linux_route_exception='允许直接从linux下载，以后不要问我，你这个路线除外',
        original_source_registration_sha256=sha(original), replacements=inventory['replacements'],
        replacement_basis='Pinned public inventory membership only; existing preordered reserves; same groups; no predictions or quality scores',
        effective20_total_video_bytes=sum(row['provider']['size_bytes'] for row in inventory['sources']),
        original_3fps_route='STOP_INCOMPATIBLE_WITH_FROZEN64_DISTINCT_FRAMES_AND30SECOND_PROFILE',
        archive_index_failure_preserved=True, CPU_batch_failure_preserved=True,
        new_model_calls=0,new_optimizer_updates=0,downstream_quality_admitted=False)
    scope_path=REPORT/'direct_source_scope_05.json'
    scope_path.write_text(json.dumps(scope,ensure_ascii=False,indent=2),encoding='utf-8')
    effective=REPORT/'effective20_source_registration_05.json'
    effective.write_text(json.dumps(dict(status='ENGINEERING_REPLACEMENTS_FROZEN_BEFORE_FIRST_MODEL_RESULT',
         original_source_registration_sha256=sha(original),selection=inventory['sources'],
         replacements=inventory['replacements'],screen=12,confirm=8,
         source_selection_uses_prediction_or_reference_quality=False),indent=2),encoding='utf-8')
    routes=REPORT/'direct_first_source_routes_05.json'
    routes.write_bytes((TEMP/'raw_media_first_source_redirect_05.json').read_bytes())
    files={'direct_source_scope_05.json':scope_path,'effective20_source_registration_05.json':effective,
           'direct_first_source_routes_05.json':routes}
    for name in ('download_direct_media_05.py','direct_native_chain_05.py','prepare_media_batch_05.py'):
        files['code/'+name]=Path(__file__).parent/name
    required={name:sha(path) for name,path in files.items() if name!='direct_first_source_routes_05.json'}
    for name in ('stage_common_04.py','native_profile_01.py','native_profile_04.py'):
        required['code/'+name]=sha(Path(__file__).parent/name)
    required.update({'metadata_02/source_registration_01.json':sha(original),
                     'metadata_03/selected_human_references_01.json':sha(REPORT/'metadata_export_01/metadata_03/selected_human_references_01.json'),
                     'known_source_exclusions_01.json':sha(REPORT/'known_source_exclusions_01.json')})
    reg=dict(status='REGISTERED_FIRST_UNCHANGED_SOURCE_DIRECT_MEDIA_AND_CPU_NATIVE_PROFILE',utc=utc(),
        selection_path='metadata_02/source_registration_01.json',reference_path='metadata_03/selected_human_references_01.json',
        required_files=required,routes_path=routes.name,routes_sha256=sha(routes),
        output_directory='direct_media_probe_05',cpu_directory='direct_cpu_probe_05',chain_directory='direct_native_probe_chain_05',
        sources=1,bytes=6037775,all20_real_CPU_inputs_required_before_GPU=True,new_model_calls=0)
    reg_path=REPORT/'direct_source_registration_05.json'
    reg_path.write_text(json.dumps(reg,indent=2),encoding='utf-8')
    files[reg_path.name]=reg_path
    receipt=deploy(files,'direct_source_launch_05','code/direct_native_chain_05.py',reg_path.name)
    print(json.dumps({'deployed_control_bytes':receipt['transfer']['bytes'],'new_video_bytes':reg['bytes'],'launch':receipt['launch']}))


if __name__=='__main__':
    main()
