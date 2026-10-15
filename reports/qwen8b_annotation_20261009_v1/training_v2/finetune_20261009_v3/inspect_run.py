"""Compact read-only snapshot of this run; never starts or resumes a stage."""
import json
import os
from pathlib import Path

r=Path('/home/inspur/aic_video_work/runs/annotation_finetune_20261009_v3')
state=json.loads((r/'state.json').read_text())
result={'state':state,'failures':{},'train':{},'predictions':{}}
for name in ('failure.json','completion.json'):
    p=r/name
    if p.exists():
        value=json.loads(p.read_text())
        if name=='completion.json':result['completion']={'status':value['status'],'metrics':value['metrics']}
        else:result['failures'][name]=value
for task in ('crop','temporal'):
    p=r/(task+'_train')/'optimizer_observations.jsonl'
    if p.exists():
        rows=[json.loads(s) for s in p.read_text().splitlines() if s.strip()]
        result['train'][task]={'last_events':rows[-3:],'first_gradient':next((x for x in rows if x['stage']=='FIRST_REAL_GRADIENTS'),None),
                               'first_step':next((x for x in rows if x.get('global_step')==1 and x['stage']=='REAL_OPTIMIZER_STEP'),None)}
    for condition in ('adapter','base'):
        p=r/f'{task}_{condition}_predictions.jsonl'
        if p.exists():
            rows=[json.loads(s) for s in p.read_text().splitlines() if s.strip()]
            result['predictions'][task+'_'+condition]={'rows':len(rows),'valid':sum(x['valid'] for x in rows)}
active=Path('/home/inspur/aic_video_work/improvement_round1/active_gpu_job.json')
if active.exists():
    value=json.loads(active.read_text())
    if value['name'].startswith('aic_ANNOTV2_'):
        result['active_resource']=value
        pid=value['child_pid'];proc=Path('/proc')/str(pid)
        if proc.exists():
            result['owned_child']={'pid':pid,'pgid':os.getpgid(pid),'status':(proc/'status').read_text().splitlines()[:7],
                                   'command':(proc/'cmdline').read_bytes().replace(b'\0',b' ').decode(),
                                   'io':(proc/'io').read_text()}
if 'job' in state:
    log=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller')/(state['job']+'.log')
    if log.exists():result['latest_gpu_log']=log.read_text(errors='replace')[-2400:]
print(json.dumps(result))
