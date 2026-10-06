"""Run frozen public development comparisons through the project GPU queue."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from evaluation_v2.temporal import evaluate_rows, compare, read_jsonl

ROOT=Path('/home/inspur/aic_video_work')
PYTHON=str(ROOT/'env/qwen3vl/bin/python')


def write(path,value):
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value,indent=2)+'\n')
    tmp.replace(path)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--dev',required=True)
    ap.add_argument('--output',required=True)
    ap.add_argument('--name-prefix',required=True)
    ap.add_argument('--max-seconds-per-policy',type=int,default=7200)
    args=ap.parse_args()
    out=Path(args.output)
    out.mkdir(exist_ok=False,parents=True)
    frozen=out/'dev_frozen.jsonl'
    frozen.write_bytes(Path(args.dev).read_bytes())
    refs=read_jsonl(frozen)
    if len(refs)<50:
        raise ValueError('full dev comparison requires at least 50 rows')
    hashes={'dev':hashlib.sha256(frozen.read_bytes()).hexdigest()}
    sources=[str(p.relative_to(ROOT)) for p in sorted((ROOT/'inference_v2').glob('*.py'))]
    sources+=['inference/baseline_qwen3vl.py','evaluation_v2/temporal.py',
              'improvement_round1/run_dev_suite.py','improvement_round1/environment.lock.txt']
    for relative in sources:
        hashes[relative]=hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()
    write(out/'input_lock.json',hashes)
    results={}
    for policy in ('single','multi','windowed'):
        for relative, sha in hashes.items():
            if relative!='dev' and hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()!=sha:
                raise RuntimeError('source changed during frozen comparison: '+relative)
        pred=out/(policy+'_predictions.jsonl')
        write(out/'progress.json',dict(status='running',policy=policy,completed=list(results)))
        cmd=[PYTHON,str(ROOT/'improvement_round1/budget_run.py'),
             '--name',args.name_prefix+'_'+policy,'--max-seconds',str(args.max_seconds_per_policy),'--',
             PYTHON,'-m','inference_v2.baseline_v2','--model',str(ROOT/'models/Qwen3-VL-4B-Instruct'),
             '--index',str(frozen),'--temporal-only','--query-aware','--temporal-policy',policy,
             '--constrained-json',
             '--temporal-out',str(pred),'--raw-out',str(out/(policy+'_raw.jsonl'))]
        started=time.monotonic()
        code=subprocess.run(cmd,cwd=ROOT).returncode
        if code:
            write(out/'progress.json',dict(status='failed',policy=policy,returncode=code,completed=list(results)))
            raise SystemExit(code)
        predictions=read_jsonl(pred)
        try:
            report=evaluate_rows(predictions,refs)
            report.update(policy=policy,wall_seconds=time.monotonic()-started,reference_sha256=hashes['dev'],
                          predictions_sha256=hashlib.sha256(pred.read_bytes()).hexdigest())
            if policy!='single' and 'metrics' in results.get('single',{}):
                report['comparison']=compare(report,results['single'])
        except ValueError as error:
            report=dict(policy=policy,status='diagnostic_rejected',reason=str(error),
                        status_counts={status:sum(x.get('status')==status for x in predictions)
                                       for status in set(x.get('status') for x in predictions)})
        write(out/(policy+'_report.json'),report)
        results[policy]=report
    summary={k:{x:y for x,y in v.items() if x!='rows'} for k,v in results.items()}
    qualified=[k for k,v in results.items() if v.get('comparison',{}).get('eligible_dev')]
    qualified.sort(key=lambda k:(-results[k]['metrics']['f1'],results[k]['wall_seconds']))
    write(out/'summary.json',dict(status='completed',results=summary,qualified=qualified,
          holdout_used=False,official_score=None,training_used=False))
    write(out/'progress.json',dict(status='completed',completed=list(results),qualified=qualified))
    print(json.dumps(summary),flush=True)


if __name__=='__main__':
    main()
