"""Explicit-scope bounded read-only status; never discovers latest or launches work."""
import argparse
import json
from pathlib import Path
import subprocess

REMOTE = r'''
import json,pathlib,socket,subprocess
scope=json.loads(SCOPE_JSON)
root=pathlib.Path('/home/inspur/aic_video_work/t_branch_execution_20261022_v1')
stage=root/scope['stage']
if socket.gethostname()!='inspur-NP5570M5':raise ValueError('Actual host differs')
def process(pid,expected=None,seen=None):
 seen=set() if seen is None else seen
 if pid in seen:return None
 seen.add(pid);p=pathlib.Path('/proc')/str(pid)
 try:
  state=(p/'stat').read_text().rsplit(')',1)[1].split()
  if expected is not None and state[19]!=str(expected):return dict(pid=pid,status='REUSED_HANDLE_DO_NOT_ACT')
  children=set();threads=list((p/'task').iterdir())
  for t in threads:
   try:children.update(map(int,(t/'children').read_text().split()))
   except OSError:pass
  return dict(pid=pid,start_ticks=state[19],state=state[0],parent=state[1],threads=len(threads),
   argv=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(),IO=(p/'io').read_text().replace('\n',' '),
   children=[process(n,seen=seen) for n in sorted(children)])
 except OSError:return dict(pid=pid,status='MISSING_CHECK_TERMINAL_NEVER_RESTART_FROM_THIS_ALONE')
print('HOST',socket.gethostname())
print('FAMILY',json.dumps(process(scope['parent_pid'],scope['parent_start_ticks'])))
for name in scope['files']:
 p=stage/name
 if p.exists():
  x=json.loads(p.read_text());print(name,json.dumps({k:v for k,v in x.items() if k not in scope['omit_fields']})[:5500])
for label,pattern in scope['counts'].items():print('COUNT',label,len(list(stage.glob(pattern))))
run=root.parent/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller'
p=run/(scope['job']+'.resource.json') if scope.get('job') else None
if p is not None and p.exists():
 x=json.loads(p.read_text());rows=[json.loads(line) for line in (root.parent/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
 print('RESOURCE',dict(status=x['status'],exit_code=x['exit_code'],charged_seconds=x['charged_seconds'],
  unique_ledger=[v for v in rows if v.get('name')==scope['job']]==[x]))
print('GPU',subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True))
print('CAPACITY',subprocess.check_output(['df','-B1',str(root),'/dev/shm'],text=True))
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scope', required=True, type=Path)
    args = parser.parse_args(); scope = json.loads(args.scope.read_text(encoding='utf-8'))
    if not scope['stage'].isidentifier() or any('/' in name or '\\' in name for name in scope['files']):
        raise ValueError('Only one explicit registered stage and file basename accepted')
    script = REMOTE.replace('SCOPE_JSON', repr(json.dumps(scope)))
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=12',
        'aic-inspur-tailscale', '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python -'],
        input=script, text=True, capture_output=True, timeout=45)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
