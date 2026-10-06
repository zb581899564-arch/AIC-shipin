"""Check the two remaining generation policies, then run the full dev suite."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path('/home/inspur/aic_video_work')
C=ROOT/'improvement_round1'
PY=str(ROOT/'env/qwen3vl/bin/python')


def main():
    for policy,count in [('multi',20),('windowed',3)]:
        name='constrained_'+policy+'_smoke'
        pred=C/(name+'.jsonl')
        cmd=[PY,str(C/'budget_run.py'),'--name',name,'--max-seconds','1200','--',PY,
             '-m','inference_v2.baseline_v2','--index',str(C/'frozen_data/dev.jsonl'),
             '--temporal-only','--query-aware','--constrained-json','--temporal-policy',policy,
             '--num-videos',str(count),'--temporal-out',str(pred),'--raw-out',str(C/(name+'_raw.jsonl'))]
        code=subprocess.run(cmd,cwd=ROOT).returncode
        if code:
            raise SystemExit(code)
        rows=[json.loads(s) for s in pred.read_text().splitlines()]
        accepted=len(rows)==count and all(x['status'] in ('ok','valid_empty') for x in rows)
        report=dict(status='passed' if accepted else 'failed',policy=policy,rows=len(rows),
                    invalid=[{'video_id':x['video_id'],'reason':x['reason']} for x in rows if x['status']=='invalid'],
                    empty=sum(x['status']=='valid_empty' for x in rows),performance_metric_used=False)
        (C/(name+'_acceptance.json')).write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report),flush=True)
        if not accepted:
            raise RuntimeError('model output smoke failed; do not launch the full comparison')
    state=json.loads((C/'campaign_state.json').read_text())
    state.update(status='dev_comparison_running',dev_run=str(ROOT/'runs/improvement_dev_v2'),constrained_json=True)
    (C/'campaign_state.json').write_text(json.dumps(state,indent=2)+'\n')
    cmd=[PY,str(C/'run_dev_suite.py'),'--dev',str(C/'frozen_data/dev.jsonl'),
         '--output',str(ROOT/'runs/improvement_dev_v2'),'--name-prefix','dev_v2','--max-seconds-per-policy','7200']
    raise SystemExit(subprocess.run(cmd,cwd=ROOT).returncode)


if __name__=='__main__':
    main()
