"""Small explicit control deployment through the existing strict SSH endpoint."""
import base64
import hashlib
import io
import json
from pathlib import Path
import subprocess
import zipfile


def main():
    source = Path(__file__).resolve().parent
    workspace = source.parents[3]
    protection = workspace / 'reports/round6_score_alignment/p2r9_native_portrait_reference/round6_p2r9_20260920T040552Z/protected_input_registry.json'
    protocol = dict(schema='SUBJECT_EXTENT_EXTERNAL_NATIVE16_20261024_V1',
        human_authorization='2026-10-24: noon deadline, execute evidence-based spatial pilot; 40.48 protected',
        deadline_utc='2026-10-24T04:00:00+00:00', dev_count=20, confirm_count=20,
        dev_scope='Deterministic20 of historically exposed S1 development; no new blind development claim',
        confirmation_scope='Only after dev selection frozen; author test filenames excluded from all known GNMC historical inputs, SHA and dHash isolation required',
        use_scope='User explicitly noncommercial student competition/research; original GNMC PolyForm NC, no raw redistribution',
        original_source_and_pretraining_independence='UNKNOWN',
        candidate='One exact PR8 BASE subject extent + same-frame foreground + explicit containment geometry',
        temporal_membership='40.48 unchanged; native9:16 unchanged; no temporal edits',
        quality_gates=dict(mean_delta_min=.01, content_minus_shift_min=.01, losses_over_010_max=2, changed_min=5,
                           median_delta_min=0, invalid=0),
        spatial_config=dict(context_fraction=.20, minimum_width_fraction=.55, tracker_long_edge=480,
                            max_subjects=3, foreground_iterations=2, foreground_expansion=.15, minimum_foreground_support=.08),
        dev_gpu_command_seconds_max=900, total_new_gpu_command_seconds_max=1800, total_new_generations_max=80,
        currently_admitted='First20 exposed development only; stop on fixed failure, no parameter rescue',
        negative_control='Cyclic shift normalized raw subject boxes by1 in fixed selected-file order, then same image foreground/geometry',
        baseline='Adopt exact historical BASE center/max-width for same pixels; confirmation requires first exact control',
        tracking='Not qualified by static images; old G COST_STOP/untrusted motion immutable; no automatic production',
        training_updates=0, new_model_downloads=0, CPU_threads_max=2,
        CPU_review='First tensor identity, all output token grammar/parser, native box geometry, independent IoU; full CPU numeric logits not claimed',
        confirm_and_production_automatic=False, new_goal=False, new_automation=False)
    files = {'code/' + p.name: p.read_bytes() for p in source.glob('*.py') if p.name != 'deploy.py'}
    for name, raw in files.items():
        compile(raw, name, 'exec')
    files['protocol.json'] = json.dumps(protocol, indent=2).encode()
    files['historical_protected.json'] = protection.read_bytes()
    manifest = {n: dict(bytes=len(b), sha256=hashlib.sha256(b).hexdigest()) for n, b in files.items()}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as archive:
        for n, b in files.items():
            archive.writestr(n, b)
    payload = buf.getvalue()
    code = '''import base64,hashlib,io,json,os,pathlib,subprocess,zipfile
root=pathlib.Path('/home/inspur/aic_video_work/subject_extent_pilot_20261024_v1')
raw=base64.b64decode(PAYLOAD)
assert hashlib.sha256(raw).hexdigest()==EXPECTED
manifest=MANIFEST
assert not root.exists(), 'Independent run root already exists; inspect, never overwrite or relaunch'
checkout=pathlib.Path('/home/inspur/aic_video_work/final_sprint_temporal_field_checkout_20261023_v6')
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=checkout,text=True).strip()=='8dcde128be0ffe2df3ccba75d69929b7a9769a6f'
root.mkdir()
with zipfile.ZipFile(io.BytesIO(raw)) as z:
 assert z.testzip() is None and set(z.namelist())==set(manifest)
 for n in z.namelist():
  p=root/n;assert p.resolve().is_relative_to(root)
  b=z.read(n);assert len(b)==manifest[n]['bytes'] and hashlib.sha256(b).hexdigest()==manifest[n]['sha256']
  p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
assets=json.loads(pathlib.Path('/home/inspur/aic_video_work/final_sprint_temporal_r_production_20261023_v6/assets.json').read_text())
spec=assets['qwen'];assert not spec.get('adapter_dir')
(root/'model_spec.json').write_text(json.dumps(spec,indent=2))
(root/'deployment.json').write_text(json.dumps(dict(control_bytes=len(raw),control_sha256=EXPECTED,members=manifest),indent=2))
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
py='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
with (root/'controller.log').open('x') as log:
 p=subprocess.Popen([py,'-u','-B',str(root/'code/controller.py')],cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 ticks=pathlib.Path('/proc/'+str(p.pid)+'/stat').read_text().rsplit(')',1)[1].split()[19]
 result=dict(pid=p.pid,start_ticks=ticks,control_bytes=len(raw),control_sha256=EXPECTED)
 (root/'launch.json').write_text(json.dumps(result,indent=2))
 print(json.dumps(result))
'''
    code = code.replace('PAYLOAD', repr(base64.b64encode(payload).decode())).replace('EXPECTED', repr(hashlib.sha256(payload).hexdigest())).replace('MANIFEST', repr(manifest))
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=12',
                             'aic-inspur-home', 'python3', '-'], input=code, text=True, capture_output=True, timeout=35)
    print(result.stdout)
    if result.returncode:
        raise RuntimeError(result.stderr)


if __name__ == '__main__':
    main()
