#!/usr/bin/env bash
# temporal_round5 — Phase B: three fixed dev baselines.
set -u
R5=/home/inspur/aic_video_work/temporal_round5
W=/home/inspur/aic_video_work
PQ=$W/env/qwen3vl_isolated_20260910/bin/python
PO=$W/orarl_round1/env/orarl_hf/bin/python
cd "$W" || exit 1

run() {  # name maxsec python script args...
  local name="$1" maxsec="$2"; shift 2
  echo "=== $name  $(date -u +%T)Z ==="
  python3 "$W/improvement_round1/budget_run.py" --name "$name" --max-seconds "$maxsec" -- "$@"
  echo "=== $name rc=$? $(date -u +%T)Z ==="
}

run r5t0 2400 "$PQ" "$R5/scripts/run_baselines_qwen.py" \
    --arm T0_BASE --split dev --out "$R5/outputs/T0_BASE_dev.json"
run r5t1 2400 "$PQ" "$R5/scripts/run_baselines_qwen.py" \
    --arm T1_QVH_LORA --split dev --out "$R5/outputs/T1_QVH_LORA_dev.json"
run r5t2 2400 "$PO" "$R5/scripts/run_baselines_orarl.py" \
    --split dev --out "$R5/outputs/T2_ORARL_TEMPORAL_dev.json"
echo "ALL_PHASE_B_DONE"
