#!/usr/bin/env bash
set -u
R=/home/inspur/aic_video_work/orarl_round1
W=/home/inspur/aic_video_work
echo '=== pre-launch guard ==='
echo "gpu compute apps: [$(nvidia-smi --query-compute-apps=pid,used_memory,process_name --format=csv,noheader | tr '\n' ';')]"
echo "active_gpu_job.json: $(ls $W/improvement_round1/active_gpu_job.json 2>/dev/null || echo none)"
echo "existing job name in ledger:"
grep -c 'orarl_r1_verify' "$W/improvement_round1/gpu_ledger.jsonl" 2>/dev/null || echo 0
echo "budget_run.py present: $(ls -la $W/improvement_round1/budget_run.py | awk '{print $5}') bytes"
echo

setsid nohup bash "$R/scripts/run_gpu_budgeted.sh" orarl_r1_verify 1740 \
  > "$R/logs/gpu_run.nohup.log" 2>&1 < /dev/null &
sleep 5
echo "launched; pid tree:"
ps -eo pid,ppid,cmd -ww | grep -E 'run_gpu_budgeted|budget_run|run_inference' | grep -v grep
sleep 20
echo
echo '=== after 25s ==='
echo "active_gpu_job.json:"; cat "$W/improvement_round1/active_gpu_job.json" 2>/dev/null | head -30
echo
echo "job log tail:"; tail -c 1200 "$W/improvement_round1/orarl_r1_verify.log" 2>&1
echo
echo "nohup tail:"; tail -c 800 "$R/logs/gpu_run.nohup.log" 2>&1
