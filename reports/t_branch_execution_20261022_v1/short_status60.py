"""One bounded read-only snapshot; never launches, restores or transfers evidence."""
import subprocess

REMOTE = r'''
import json,pathlib,subprocess
r=pathlib.Path('/home/inspur/aic_video_work/t_branch_execution_20261022_v1')
o=r/'speech_development60'
def process(pid,expected=None,seen=None):
 seen=set() if seen is None else seen
 if pid in seen:return None
 seen.add(pid);p=pathlib.Path('/proc')/str(pid)
 try:
  stat=(p/'stat').read_text().rsplit(')',1)[1].split()
  if expected is not None and stat[19]!=str(expected):return dict(pid=pid,state='HANDLE_REUSED_DO_NOT_ACT')
  tids=list((p/'task').iterdir());children=set()
  for task in tids:
   try:children.update(map(int,(task/'children').read_text().split()))
   except OSError:pass
  return dict(pid=pid,start_ticks=stat[19],state=stat[0],parent=stat[1],threads=len(tids),
   argv=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(),
   IO=(p/'io').read_text().replace('\n',' '),children=[process(k,seen=seen) for k in sorted(children)])
 except OSError:return dict(pid=pid,state='MISSING_INSPECT_AUTHORITATIVE_TERMINAL_NO_RESTART')
print('HOST',subprocess.check_output(['hostname'],text=True).strip())
print('PROCESS',json.dumps(process(979878,'563370409')))
print('CONTROL5',json.dumps(process(1244689,'491630308'))[:400])
for name in ['failure.json','coarse_terminal.json','coarse_GPU_completion.json','speech_prepare60_terminal.json',
 'verify_CPU_completion.json','verify_terminal.json','verify_GPU_completion.json','speech_review60_terminal.json','review.json','completion.json']:
 p=o/name
 if p.exists():
  x=json.loads(p.read_text());keys=['outputs','semantic','tasks','source_policies','first100_output_QA','adopted_VERIFY_outputs','metrics']
  print(name,json.dumps({k:v for k,v in x.items() if k not in keys})[:3500])
print('FIRST_GREEDY_ACCEPTED',len(list((o/'coarse').glob('*/acceptance.json'))))
print('FIRST_VERIFY_ACCEPTED',len(list((o/'verify_outputs').glob('*/acceptance.json'))))
run=pathlib.Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller')
ledger=pathlib.Path('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl')
rows=[json.loads(l) for l in ledger.read_text().splitlines() if l.strip()]
for phase in ['coarse','verify']:
 job='T_whole_speech_visual_'+phase+'_20261022_v60';p=run/(job+'.resource.json')
 if p.exists():
  x=json.loads(p.read_text());print('RESOURCE',dict(name=job,status=x['status'],exit_code=x['exit_code'],
   charged_seconds=x['charged_seconds'],unique_ledger=[v for v in rows if v.get('name')==job]==[x]))
print('GPU',subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True))
print('CAPACITY',subprocess.check_output(['df','-B1',str(r),'/dev/shm'],text=True))
'''

result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=12',
    'aic-inspur-tailscale', '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python -'],
    input=REMOTE, text=True, capture_output=True, timeout=45)
print(result.stdout)
if result.stderr:
    print(result.stderr)
raise SystemExit(result.returncode)
