#!/usr/bin/env bash
set -u
R=/home/inspur/aic_video_work/orarl_round2
W=/home/inspur/aic_video_work
echo "now: $(date -u +%T)Z"
echo "job proc alive: $(pgrep -fc 'orarl_verify.py' 2>/dev/null || echo 0)"
echo "active_gpu_job: $(ls $W/improvement_round1/active_gpu_job.json 2>/dev/null || echo none)"
echo "resource json: $(ls $W/improvement_round1/r2tr.resource.json 2>/dev/null || echo none)"
echo
echo "=== elapsed ==="
python3 -c "
import json
try:
    d=json.load(open('$W/improvement_round1/active_gpu_job.json'))
    print('elapsed=%.0fs peak=%s' % (d.get('elapsed_seconds',0), d.get('sampled_peak_memory_mib')))
except Exception as e:
    print('no active job:', e)
"
echo
echo "=== cases completed so far ==="
python3 -c "
import json,pathlib
p=pathlib.Path('$R/outputs/r2tr/run_status.json')
if p.exists():
    st=json.loads(p.read_text())
    print('cases written:', len(st['cases']))
    for c in st['cases']:
        print('  %-18s parseable=%-5s protocol=%-5s success=%-5s distinct=%s' % (
            c['case_id'], c['output_parseable'], c['protocol_complete'], c['task_success'],
            (c.get('parsed') or {}).get('distinct_boxes_n')))
else:
    print('not started yet')
"
echo
echo "=== log tail ==="
grep -vE '^\s*[0-9]+%\|' "$W/improvement_round1/r2tr.log" 2>/dev/null | tail -12
