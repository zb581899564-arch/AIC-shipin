"""Read actual owned commands and unique metadata/index terminals; never launch work."""
import datetime
import json
import shlex
import subprocess
from pathlib import Path

REPORT = Path(__file__).resolve().parents[2] / 'reports/videoxum_reference_iteration_20261013_v1'
SSH = ['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o',
       'ConnectTimeout=15', '-o', 'ServerAliveInterval=15', 'aic-inspur-home']


def main():
    script = '''import pathlib,json,datetime,socket,subprocess
base=pathlib.Path('/home/inspur/aic_video_work/videoxum_reference_iteration_20261013_v1')
assert socket.gethostname()=='inspur-NP5570M5'
owned=[]
for path in pathlib.Path('/proc').iterdir():
 if not path.name.isdigit():continue
 try:
  args=(path/'cmdline').read_bytes().split(b'\\0')
  if any(arg.startswith((str(base)+'/code/').encode()) for arg in args):
   status=(path/'status').read_text().splitlines()
   owned.append({'pid':int(path.name),'argv':[arg.decode(errors='replace') for arg in args if arg],
      'ppid':next(row.split(':')[1].strip() for row in status if row.startswith('PPid:')),
      'state':next(row for row in status if row.startswith('State:')),'io':(path/'io').read_text(),
      'fds':{item.name:str(item.readlink()) for item in (path/'fd').iterdir()}})
 except (OSError,ProcessLookupError):pass
terminals={}
for folder in ['metadata_01','metadata_02','metadata_03','archive_index_01',
               'media_batch_01','cpu_batch_01','media_native_chain_01',
               'direct_media_probe_05','direct_cpu_probe_05','direct_native_probe_chain_05','direct_cohort_06']:
 terminals[folder]={name:json.loads((base/folder/name).read_text()) for name in ['state.json','completion.json','failure.json'] if (base/folder/name).exists()}
print(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'hostname':socket.gethostname(),
 'actual_owned_commands':owned,'terminals':terminals,
 'gpu':subprocess.run(['nvidia-smi','--query-gpu=name,memory.used,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True).stdout,
 'new_source_video_files':len(list(base.glob('media_batch_*/*.mp4')))+len(list(base.glob('direct_media_*/*.mp4')))+len(list(base.glob('direct_cohort_06/*/media/*.mp4'))),
 'new_gpu_launcher_exists':bool(list(base.glob('*gpu*launch*')))}))
'''
    completed = subprocess.run(SSH + ['python3 -c ' + shlex.quote(script)], capture_output=True, check=True)
    snapshot = json.loads(completed.stdout)
    name = 'live_' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json'
    with (REPORT / name).open('x', encoding='utf-8') as stream:
        json.dump(snapshot, stream, ensure_ascii=False, indent=2)
    index = snapshot['terminals']['archive_index_01']
    print(json.dumps({'receipt': name, 'utc': snapshot['utc'], 'owned_command_count': len(snapshot['actual_owned_commands']),
                      'index_progress': index.get('state.json'), 'index_terminal': {k: v for k, v in index.items() if k != 'state.json'},
                      'media_batch_terminals': {k:v for k,v in snapshot['terminals'].items() if k.startswith(('media_batch','cpu_batch','media_native','direct_'))},
                      'new_source_video_files': snapshot['new_source_video_files'],
                      'new_gpu_launcher_exists': snapshot['new_gpu_launcher_exists']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
