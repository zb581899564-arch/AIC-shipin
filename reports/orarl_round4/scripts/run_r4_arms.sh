#!/usr/bin/env bash
# Round-4 budgeted GPU runs. Two envs are required because the current
# Qwen3-VL baseline (transformers 4.57.1) and Video-ORA-4B (transformers 5.5.4)
# cannot share one interpreter.
set -u
R4=/home/inspur/aic_video_work/orarl_round4
W=/home/inspur/aic_video_work
PY_QWEN=$W/env/qwen3vl_isolated_20260910/bin/python
PY_ORA=$W/orarl_round1/env/orarl_hf/bin/python

echo "=== arm A (Qwen3-VL): P1 + P3a  $(date -u +%T)Z ==="
cd "$W" || exit 1
python3 "$W/improvement_round1/budget_run.py" --name r4armA --max-seconds 1500 -- \
  "$PY_QWEN" "$R4/scripts/arms_qwen.py" --out-dir "$R4/outputs/arms"
echo "armA rc=$?"

echo "=== arm B (Video-ORA-4B): P2 + P3b  $(date -u +%T)Z ==="
python3 "$W/improvement_round1/budget_run.py" --name r4armB --max-seconds 1500 -- \
  "$PY_ORA" "$R4/scripts/arms_orarl.py" --out-dir "$R4/outputs/arms"
echo "armB rc=$?"
echo "ALL_ROUND4_ARMS_DONE"
