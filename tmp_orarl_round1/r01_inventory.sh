#!/usr/bin/env bash
# Read-only inventory: ledger, budget, disk, GPUs, network reachability.
set -u

echo "=== DATE ==="
date -u +%Y-%m-%dT%H:%M:%SZ
echo

echo "=== LEDGER SUMMARY ==="
cd /home/inspur/aic_video_work/improvement_round1 || exit 1
python3 - <<'PY'
import json
recs = [json.loads(l) for l in open('gpu_ledger.jsonl') if l.strip()]
print('record_count:', len(recs))
tot = sum(r.get('charged_seconds', 0) for r in recs)
print('sum_charged_seconds: %.1f (%.3f h)' % (tot, tot / 3600))
print('initial_conservative_charge_seconds: 7200')
print('total_charged_seconds: %.1f (%.3f h)' % (7200 + tot, (7200 + tot) / 3600))
print('budget_seconds: 86400 (24.0 h)')
print('remaining_seconds: %.1f (%.3f h)' % (86400 - 7200 - tot, (86400 - 7200 - tot) / 3600))
print()
for r in recs:
    print('%-30s %8.2f min  %-9s  peak=%s' % (
        r.get('name', '?')[:30],
        r.get('charged_seconds', 0) / 60,
        r.get('status'),
        r.get('sampled_peak_memory_mib')))
PY
echo

echo "=== ACTIVE JOB / LOCK STATE ==="
ls -la active_gpu_job.json 2>&1
echo "-- gpu.lock holders --"
fuser -v gpu.lock 2>&1 || echo "(no holder reported)"
echo

echo "=== DISK ==="
df -B1 /home/inspur/aic_video_work
du -s -B1 /home/inspur/aic_video_work
echo

echo "=== ORARL TRACES ==="
find /home/inspur -maxdepth 5 -iname '*OraRL*' 2>/dev/null | head -50
echo "(end find)"
echo

echo "=== PYTHON / ENVS ==="
which -a python3 python 2>&1
python3 -VV
echo "-- existing envs --"
ls -la /home/inspur/aic_video_work/env 2>&1
echo "-- conda/pip --"
ls -d /home/inspur/*conda* /opt/*conda* 2>/dev/null
echo

echo "=== GPU ==="
nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used --format=csv
nvidia-smi --query-compute-apps=pid,used_memory,process_name --format=csv
echo

echo "=== NETWORK: github + hf ==="
curl -sS -o /dev/null -w 'github.com http=%{http_code} time=%{time_total}\n' --max-time 20 https://github.com/ 2>&1
curl -sS -o /dev/null -w 'huggingface.co http=%{http_code} time=%{time_total}\n' --max-time 20 https://huggingface.co/ 2>&1
curl -sS -o /dev/null -w 'hf-mirror.com http=%{http_code} time=%{time_total}\n' --max-time 20 https://hf-mirror.com/ 2>&1
curl -sS -o /dev/null -w 'pypi.org http=%{http_code} time=%{time_total}\n' --max-time 20 https://pypi.org/simple/ 2>&1
echo
echo "=== HF env ==="
env | grep -i -E 'HF_|HUGGING|TRANSFORMERS|PIP_' || echo "(none)"
