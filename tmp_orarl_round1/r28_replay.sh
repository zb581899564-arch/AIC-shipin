#!/usr/bin/env bash
set -u
R=/home/inspur/aic_video_work/orarl_round1
W=/home/inspur/aic_video_work
J="$W/improvement_round1/orarl_r1_replay_sg.log"
DEADLINE=$(( $(date +%s) + ${1:-420} ))
while :; do
  if [ -f "$W/improvement_round1/orarl_r1_replay_sg.resource.json" ]; then echo "SETTLED"; break; fi
  if [ "$(date +%s)" -ge "$DEADLINE" ]; then echo "POLL_TIMEOUT"; break; fi
  sleep 15
done
echo
echo '=== replay job log (no tqdm) ==='
grep -vE '^\s*[0-9]+%\|' "$J" 2>/dev/null | tail -25
echo
echo '=== replay resource ==='
cat "$W/improvement_round1/orarl_r1_replay_sg.resource.json" 2>&1 | python3 -c "
import sys, json
d=json.load(sys.stdin)
print('name=%s charged=%.1fs status=%s exit=%s peak=%s' % (d['name'], d['charged_seconds'], d['status'], d.get('exit_code'), d.get('sampled_peak_memory_mib')))
print('stop_reason=', d.get('stop_reason'))
"
echo
echo '=== replay raw output ==='
cat "$R/outputs/raw/spatial_grounding.raw.txt" 2>&1
echo
echo '=== offline env vars used by budget_run.py ==='
grep -o 'HF_HUB_OFFLINE=1\|TRANSFORMERS_OFFLINE=1' $W/improvement_round1/budget_run.py | sort -u
echo
echo '=== FINAL BUDGET / DISK ==='
python3 - <<'PY'
import json, subprocess
recs=[json.loads(l) for l in open('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl') if l.strip()]
t=7200+sum(r.get('charged_seconds',0) for r in recs)
mine=[r for r in recs if r['name'].startswith(('orarl_r1_verify','orarl_r1_replay'))]
print('campaign records=%d charged=%.1fs (%.4f h) remaining=%.4f h' % (len(recs), t, t/3600, (86400-t)/3600))
print('round jobs:')
for r in mine:
    print('  %-24s %7.1fs %-9s peak=%s' % (r['name'], r['charged_seconds'], r['status'], r.get('sampled_peak_memory_mib')))
print('round total = %.1f s (cap 1800)' % sum(r['charged_seconds'] for r in mine))
PY
W=/home/inspur/aic_video_work
echo "work_root_bytes_now=$(du -s -B1 $W | cut -f1)"
echo "fs_free_bytes=$(df -B1 $W | tail -1 | awk '{print $4}')"
