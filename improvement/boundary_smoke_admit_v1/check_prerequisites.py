"""Named existing evidence for fixed original-screen event; no GT/media read."""
import json
import shlex
import subprocess
PY='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
SSH=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=15','aic-inspur-home']
code=r'''import hashlib,json
from pathlib import Path
base=Path('/home/inspur/aic_video_work/twenty_hour_five_20261014_v1/base_only_pilot')
root=Path('/home/inspur/aic_video_work')
def read(p):return json.loads(Path(p).read_text())
reg=read(base/'registration_input_01.json');e=reg['rows'][0]
assert e['case_id']=='v_fVg3StD8LL0_W000' and e['original_group']=='screen'
meta=read(e['input_path']);cpu=read(e['entry']['proof_path']);done=read(e['original_done_path']);replay=read(e['old_independent_replay_path'])
known=root/'human_reference_iteration_20261013_v1/known_identity_snapshot_01.json';k=read(known)
paths={field:value for field,value in e.items() if isinstance(value,str) and ('path' in field or field.endswith('_sha256')) and 'reference' not in field}
source_hashes={x['source_sha256'] for x in k['training']['sources']+k['testing']['records']}
result={'fixed_first_screen_case':e['case_id'],'registration_row_keys':list(e),'paths':paths,
 'input_metadata_keys':list(meta),'input_bindings':meta.get('bindings'),'CPU_binding_keys':list(cpu.get('bindings',{})),
 'old_done_keys':list(done),'old_request_path':str(Path(e['original_done_path']).with_name('request.json')),
 'old_raw_path':str(Path(e['original_done_path']).with_name('raw.json')),
 'original_B_status':done['status'],'original_B_segment_count':len(done['segments']),
 'old_independent_replay_status':replay['status'],'old_RGB_path':meta['frame_array_path'],
 'old_RGB_file_exists':Path(meta['frame_array_path']).is_file(),
 'known_snapshot_path':str(known),'known_snapshot_status':k['status'],
 'known_training_clips':len(k['training']['sources']),'known_training_groups':len({x['youtube_id'] for x in k['training']['sources']}),
 'known_test_metadata_records':len(k['testing']['records']),
 'known_byte_intersection':meta['source_sha256'] in source_hashes,
 'source_sha256':meta['source_sha256'],'source_name':meta['source_name'],
 'source_separation_fields_in_rows':{key:value for key,value in e.items() if 'separation' in key or 'isolation' in key},
 'source_separation_fields_in_meta':{key:value for key,value in meta.items() if 'separation' in key or 'isolation' in key},
 'all_source_pixel_contents_and_GT_unread':True}
print(json.dumps(result))
'''
if __name__=='__main__':
 r=subprocess.run(SSH+[PY+' -B -c '+shlex.quote(code)],capture_output=True,check=True)
 print(r.stdout.decode(),end='')
