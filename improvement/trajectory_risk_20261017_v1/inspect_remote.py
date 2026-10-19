import json,pathlib,subprocess,shutil,socket
W=pathlib.Path('/home/inspur/aic_video_work')
assert socket.gethostname()=='inspur-NP5570M5'
p=W/'twenty_hour_five_20261014_v1/temporal_family_native_package_v3/package_inputs.json'
v=json.loads(p.read_text())
print(json.dumps({'inputs':v,'free_bytes':shutil.disk_usage(W).free},ensure_ascii=False))
for key in ['source_manifest','metadata']:
 m=json.loads(pathlib.Path(v[key]['path']).read_text());print(key, 'keys',list(m));
 if 'records' in m:print('record_keys',list(m['records'][0]))
for name in ['field_frames.jsonl','field_shots.jsonl','anchor_requests.jsonl','anchor_output.jsonl']:
 f=pathlib.Path(v['source_field_files'][name]['path']); row=json.loads(next(f.open()));print(name,'bytes',f.stat().st_size,'keys',list(row))
print('baseline_completion', (W/'semantic_context_production_20261016_v1/package/completion.json').read_text())
cmd=subprocess.check_output(['ps','-eo','pid,ppid,stat,etimes,args','--width','500']).decode().splitlines()
print('relevant_processes',json.dumps([s for s in cmd if ('python' in s or 'ffmpeg' in s or 'gpu_run' in s) and '[' not in s]))
