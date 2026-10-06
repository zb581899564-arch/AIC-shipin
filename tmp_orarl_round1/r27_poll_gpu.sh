#!/usr/bin/env bash
set -u
R=/home/inspur/aic_video_work/orarl_round1
W=/home/inspur/aic_video_work
J="$W/improvement_round1/orarl_r1_verify2.log"
DEADLINE=$(( $(date +%s) + ${1:-600} ))
while :; do
  if [ -f "$W/improvement_round1/orarl_r1_verify2.resource.json" ]; then
    echo "JOB_SETTLED"; break
  fi
  echo "--- $(date -u +%T)Z elapsed=$(python3 -c "
import json;print(int(json.load(open('$W/improvement_round1/active_gpu_job.json')).get('elapsed_seconds',0)))" 2>/dev/null || echo '?')s"
  grep -E 'TASK |valid=|valid_tasks|input tokens|EXCEPTION|generation|decord|torchvision' "$J" 2>/dev/null | tail -6
  if [ "$(date +%s)" -ge "$DEADLINE" ]; then echo "POLL_TIMEOUT"; break; fi
  sleep 25
done
echo
echo '=== FINAL JOB LOG ==='
grep -vE '^\s*[0-9]+%\|' "$J" 2>/dev/null | tail -80
echo
echo '=== RESOURCE ==='
python3 -c "
import json
d=json.load(open('$W/improvement_round1/orarl_r1_verify2.resource.json'))
print('charged=%.1fs peak=%s status=%s exit=%s stop=%s' % (d['charged_seconds'], d.get('sampled_peak_memory_mib'), d['status'], d.get('exit_code'), d.get('stop_reason')))
" 2>&1
echo
echo '=== BUDGET ==='
python3 - <<'PY'
import json
recs=[json.loads(l) for l in open('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl') if l.strip()]
t=7200+sum(r.get('charged_seconds',0) for r in recs)
print('records=%d charged=%.1fs (%.4f h) remaining=%.4f h' % (len(recs), t, t/3600, (86400-t)/3600))
for r in recs[-3:]:
    print('  %-22s %8.1fs %s' % (r['name'], r['charged_seconds'], r['status']))
PY
