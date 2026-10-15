"""One fresh8 CPU-only cohort under its independent root; no GPU launcher."""
import hashlib
import io
import json
import shlex
import subprocess
import zipfile
from pathlib import Path

from sparse_stage_common_02 import BASE, RUN, read, save, sha, utc

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT/'reports/sparse_context_iteration_20261013_v1'
OLD = ROOT/'reports/videoxum_reference_iteration_20261013_v1'
PY = '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
SSH = ['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=15',
       '-o', 'ServerAliveInterval=15', 'aic-inspur-home']


def remote(script, raw=None):
    response = subprocess.run(SSH+[PY+' -B -c '+shlex.quote(script)], input=raw, capture_output=True)
    if response.returncode:
        raise RuntimeError('Strict SSH control failed: '+response.stderr.decode(errors='replace'))
    return json.loads(response.stdout)


def main():
    registration_path = REPORT/'new_confirm_CPU_registration_02.json'
    if registration_path.exists() or (REPORT/'new_confirm_CPU_launch_02.json').exists():
        raise ValueError('Fresh8 preparation registered/claimed already; inspect actual stage instead of relaunch')
    selection = read(REPORT/'new_confirm_source_registration_01.json')
    schema = read(REPORT/'new_confirm_reference_schema_transfer_01.json')
    routes = read(REPORT/'new_confirm_route_acceptance_01.json')
    chosen = read(REPORT/'screen_01/selection_before_new_confirm.json')
    if chosen['chosen'] != 'SPARSE50_POST025' or selection['frozen_candidate_sha256'] != sha(REPORT/'screen_01/selection_before_new_confirm.json'):
        raise ValueError('Frozen sparse post-only development selection changed')
    if schema['sources'] != 24 or schema['bytes'] != (REPORT/'new_confirm_reference_pool_01.json').stat().st_size or schema['sha256'] != sha(REPORT/'new_confirm_reference_pool_01.json'):
        raise ValueError('Unmodified reference schema and transfer receipt required')
    if routes['routes_sha256'] != sha(REPORT/'new_confirm_routes_01.json') or len(selection['selection']) != 8:
        raise ValueError('Registered fresh8 identities and public object routes changed')
    live_script = '''import pathlib,socket,json,subprocess,os,shutil,datetime
b=pathlib.Path(BASE);assert socket.gethostname()=='inspur-NP5570M5'
root=pathlib.Path('/home/inspur/aic_video_work'); assert not (b/'new_confirm_CPU_launch_02.json').exists()
print(json.dumps(dict(hostname=socket.gethostname(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),load=os.getloadavg(),memory=pathlib.Path('/proc/meminfo').read_text(),disk=list(shutil.disk_usage(root)),gpu=subprocess.run(['nvidia-smi','--query-gpu=index,name,memory.total,memory.used,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True).stdout,jobs=subprocess.run(['ps','-eo','pid,ppid,pcpu,pmem,args','--sort=-pcpu'],capture_output=True,text=True).stdout[:18000],CPU_only=True,new_model_calls=0)))'''.replace('BASE', repr(str(BASE)))
    live = remote(live_script)
    save(REPORT/'new_confirm_CPU_host_resources_02.json', live)
    # Individual source geometry determines RGB capacity in the child. No fixed utilization threshold.
    if selection['maximum_selected_and_reserve_pool_bytes'] > live['disk'][2]:
        raise ValueError('Actual registered public candidate pool exceeds current storage capacity')
    exclusions = read(OLD/'known_source_exclusions_01.json')
    exclusions['youtube_ids'] = sorted(set(exclusions['youtube_ids']) | {x[2:] for x in selection['old_exposed_source_ids']})
    old_payload = read(OLD/'cohort_external_export_08/developer_prediction_export.json')
    exclusions['known_media_sha256'] = sorted(set(exclusions['known_media_sha256']) | {x['native_clock']['source_sha256'] for x in old_payload['rows']})
    exclusions.update(additional_old20_actual_media_hashes=20, original_known_sources_and_test_exclusion_unchanged=True,
        old40_SourceID_exposure_excluded=True, hidden_test_alias_or_subclip_semantic_disjointness_verified=False)
    save(REPORT/'known_source_exclusions_01.json', exclusions)
    scope = dict(status='REGISTERED_FRESH_PUBLIC_PRIVATE_RESEARCH_VALIDATION_SCOPE_NOT_MEDIA_COPYRIGHT_TRANSFER', utc=utc(),
        publisher='TornadoLabs/activitynet', publisher_revision=selection['publisher_revision'],
        source_url='https://huggingface.co/datasets/TornadoLabs/activitynet', annotation_url='https://huggingface.co/datasets/jylins/videoxum',
        annotation_license='Apache-2.0 annotations only', media_license='Academic source terms and original uploader rights; no blanket commercial grant',
        purpose='Private external reference validation; no model training or raw-video redistribution',
        original_source_byte_identity_verified=False, known_ID_and_whole_file_byte_isolation_required=True,
        hidden_test_alias_and_semantic_subclip_overlap_unverified=True, caption_text_available_to_model=False,
        source_selection_uses_predictions_or_quality_scores=False, native_end_and_real_CPU_inputs_required_before_B=True,
        user_public_source_to_Linux_continuing_exception='允许直接从linux下载，以后不要问我，你这个路线除外',
        selected_payload_bytes=selection['selected_media_payload_bytes'], maximum_selected_plus_reserve_pool_bytes=selection['maximum_selected_and_reserve_pool_bytes'],
        route='Normal public publisher CDN directly to Linux; no Windows video relay or Mac', new_model_calls=0)
    save(REPORT/'source_scope_02.json', scope)
    names = ['new_confirm_source_registration_01.json', 'new_confirm_reference_pool_01.json', 'new_confirm_reference_schema_transfer_01.json',
             'new_confirm_routes_01.json', 'new_confirm_route_acceptance_01.json', 'known_source_exclusions_01.json', 'source_scope_02.json',
             'PROTOCOL.md', 'registration_01.json', 'official_rules_before_registration_01.json', 'screen_01/selection_before_new_confirm.json']
    files = {name: REPORT/name for name in names}
    for name in ('sparse_stage_common_02.py', 'native_profile_01.py', 'native_profile_04.py', 'download_confirm_media_02.py',
                 'prepare_confirm_cpu_02.py', 'prepare_confirm8_cohort_02.py'):
        files['code/'+name] = Path(__file__).parent/name
    required = {name: sha(path) for name, path in files.items()}
    reg = dict(status='REGISTERED_NEW_CONFIRM8_PRIVATE_NATIVE64_CPU_COHORT_BEFORE_ANY_FRESH_MODEL_RESULT', utc=utc(),
        output_directory='new_confirm_CPU_02', routes_path='new_confirm_routes_01.json', required_files=required,
        sources=8, screen=0, confirm=8, candidate=chosen['chosen'], new_optimizer_updates=0,
        native_frames=64, maximum_window_seconds=30, max_input_tokens=16384, min_pixels=131072, max_pixels=131072,
        actual_model_parameters=8782459120, maximum_registered_pool_bytes=selection['maximum_selected_and_reserve_pool_bytes'],
        all_old_success_stages_forbidden_to_repeat=True, original_author_annotations_reused_no_download=True,
        only_preordered_new_reserves_on_actual_origin_or_manual_endpoint_rejection=True,
        new_model_calls=0, GPU_launch_admitted=False, independent_input_source_lock_and_wrapper_required=True)
    save(registration_path, reg)
    files[registration_path.name] = registration_path
    manifest = {name: dict(bytes=path.stat().st_size, sha256=sha(path)) for name, path in files.items()}
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, path in files.items():
            archive.writestr(name, path.read_bytes())
        archive.writestr('manifest.json', json.dumps(manifest, indent=2))
    raw = buffer.getvalue()
    with (REPORT/'new_confirm_CPU_control_02.zip').open('xb') as stream:
        stream.write(raw)
    control_digest = hashlib.sha256(raw).hexdigest()
    script = '''import datetime,hashlib,io,json,os,pathlib,socket,subprocess,sys,zipfile
b=pathlib.Path(BASE);assert socket.gethostname()=='inspur-NP5570M5'
assert not (b/'new_confirm_CPU_launch_02.json').exists(),'Existing unique launch; do not repeat'
raw=sys.stdin.buffer.read();assert len(raw)==SIZE and hashlib.sha256(raw).hexdigest()==DIGEST
z=zipfile.ZipFile(io.BytesIO(raw));assert z.testzip() is None
manifest=json.loads(z.read('manifest.json'));assert set(z.namelist())==set(manifest)|{'manifest.json'} and len(z.namelist())==len(set(z.namelist()))
for name,item in manifest.items():
 p=b/name;assert p.resolve().is_relative_to(b.resolve());data=z.read(name)
 assert len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['sha256']
 if p.exists():assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256']
for name in manifest:
 p=b/name
 if not p.exists():
  p.parent.mkdir(parents=True,exist_ok=True)
  with p.open('xb') as stream:stream.write(z.read(name))
argv=[PY,'-B',str(b/'code/prepare_confirm8_cohort_02.py'),str(b/'new_confirm_CPU_registration_02.json')]
claim=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),argv=argv,control_bytes=len(raw),control_sha256=hashlib.sha256(raw).hexdigest(),new_model_calls=0)
with (b/'new_confirm_CPU_launch_02.json').open('x') as stream:json.dump(claim,stream,indent=2)
env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']=''
log=(b/'new_confirm_CPU_02.log').open('xb')
p=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
receipt=dict(transfer=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),members=manifest),launch=dict(**claim,pid=p.pid))
with (b/'new_confirm_CPU_launch_receipt_02.json').open('x') as stream:json.dump(receipt,stream,indent=2)
print(json.dumps(receipt))'''.replace('BASE', repr(str(BASE))).replace('SIZE', str(len(raw))).replace('DIGEST', repr(control_digest)).replace('PY', repr(PY))
    receipt = remote(script, raw)
    if receipt['transfer']['sha256'] != control_digest or receipt['transfer']['members'] != manifest:
        raise ValueError('Actual strict control transfer does not match local manifest')
    save(REPORT/'new_confirm_CPU_launch_02.json', receipt)
    print(json.dumps(dict(status='UNIQUE_FRESH_CONFIRM8_CPU_COHORT_STARTED_NO_GPU', control_bytes=len(raw),
        control_sha256=control_digest, selected_video_bytes=selection['selected_media_payload_bytes'],
        maximum_pool_video_bytes=selection['maximum_selected_and_reserve_pool_bytes'], argv=receipt['launch']['argv'],new_model_calls=0)))


if __name__ == '__main__':
    main()
