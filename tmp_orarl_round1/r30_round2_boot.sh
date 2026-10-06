#!/usr/bin/env bash
set -u
W=/home/inspur/aic_video_work
R1=$W/orarl_round1
R2=$W/orarl_round2

echo "=== DATE ==="; date -u +%FT%TZ
echo
echo "=== AGENTS.md anywhere relevant ==="
for d in /home/inspur $W /home/inspur/aic_video_data; do
  find "$d" -maxdepth 2 -iname 'AGENTS.md' 2>/dev/null
done
echo "(end)"
echo
echo "=== GPU / PROCS ==="
nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used --format=csv,noheader
nvidia-smi --query-compute-apps=pid,used_memory,process_name --format=csv,noheader
echo "compute apps above (empty = idle)"
ps -eo pid,etimes,cmd -ww | grep -E 'run_inference|budget_run|orarl' | grep -v grep
echo "(no orarl procs above = clean)"
echo
echo "=== ACTIVE JOB / LOCK ==="
ls -la $W/improvement_round1/active_gpu_job.json 2>&1
fuser -v $W/improvement_round1/gpu.lock 2>&1 | tail -2
echo
echo "=== BUDGET ==="
python3 - <<'PY'
import json
p='/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl'
recs=[json.loads(l) for l in open(p) if l.strip()]
t=7200+sum(r.get('charged_seconds',0) for r in recs)
print('records=%d charged=%.1fs (%.4f h) budget=86400s remaining=%.4f h' % (len(recs), t, t/3600, (86400-t)/3600))
print('round2 cap = 45 min = 2700 s -> allowed:', (86400-t) > 2700+120)
for r in recs[-4:]:
    print('  %-24s %8.1fs %s' % (r['name'], r['charged_seconds'], r['status']))
PY
echo
echo "=== DISK ==="
df -B1 $W | tail -1
echo "work_root_bytes=$(du -s -B1 $W | cut -f1)"
echo "round1_bytes=$(du -s -B1 $R1 | cut -f1)"
echo
echo "=== ROUND1 ARTIFACTS (read-only reuse) ==="
ls -la $R1
echo "-- round1 REPORT exists:"; ls -la $R1/REPORT.md 2>&1
echo "-- round1 model/env:"; du -sh $R1/model/Video-ORA-4B $R1/env/orarl_hf 2>&1
echo
echo "=== CREATE ROUND2 ==="
mkdir -p $R2/{logs,scripts,evidence,outputs,clips,frames,protocol,no_gpu_tests}
ls -la $R2
echo
echo "=== round1 REPORT.md sha256 (for traceability copy) ==="
sha256sum $R1/REPORT.md
