#!/usr/bin/env bash
# Budgeted GPU runner for round 2.
# usage: run_gpu_round2.sh RUN_ID CASES_JSONL MAX_SECONDS [extra orarl_verify args...]
set -u
ROUND2=/home/inspur/aic_video_work/orarl_round2
W=/home/inspur/aic_video_work
PY=/home/inspur/aic_video_work/orarl_round1/env/orarl_hf/bin/python
MODEL=/home/inspur/aic_video_work/orarl_round1/model/Video-ORA-4B

RUN_ID="$1"; CASES="$2"; MAXSEC="$3"; shift 3
cd "$W" || exit 1
echo "run_id=$RUN_ID cases=$CASES max_seconds=$MAXSEC extra=$*"
python3 "$W/improvement_round1/budget_run.py" \
  --name "$RUN_ID" --max-seconds "$MAXSEC" -- \
  "$PY" "$ROUND2/scripts/orarl_verify.py" \
       --model "$MODEL" \
       --cases "$CASES" \
       --out-root "$ROUND2/outputs" \
       --run-id "$RUN_ID" \
       --attn sdpa "$@"
rc=$?
echo "budget_run_rc=$rc"
