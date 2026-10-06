#!/usr/bin/env bash
set -u
R=/home/inspur/aic_video_work/orarl_round1
W=/home/inspur/aic_video_work
echo '=== run_status.json ==='
cat "$R/outputs/run_status.json" 2>&1 | head -120
echo
echo '=== raw outputs ==='
ls -la "$R/outputs/raw" 2>&1
for f in "$R/outputs/raw"/*; do echo "--- $f"; head -c 600 "$f"; echo; done 2>/dev/null
echo
echo '=== full job log (first 120 lines) ==='
head -120 "$W/improvement_round1/orarl_r1_verify.log" 2>&1
echo
echo '=== resource json ==='
cat "$W/improvement_round1/orarl_r1_verify.resource.json" 2>&1
echo
echo '=== ledger tail (charges) ==='
tail -2 "$W/improvement_round1/gpu_ledger.jsonl" | python3 -c '
import sys, json
for l in sys.stdin:
    d=json.loads(l)
    print(d["name"], "charged=%.1fs"%d["charged_seconds"], "status=", d["status"], "peak=", d.get("sampled_peak_memory_mib"), "exit=", d.get("exit_code"))
'
echo
echo '=== budget after ==='
python3 - <<'PY'
import json
recs=[json.loads(l) for l in open('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl') if l.strip()]
t=7200+sum(r.get('charged_seconds',0) for r in recs)
print('records=%d charged=%.1fs (%.3f h) remaining=%.3f h' % (len(recs), t, t/3600, (86400-t)/3600))
PY
