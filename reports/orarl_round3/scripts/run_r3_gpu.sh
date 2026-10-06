#!/usr/bin/env bash
# Round-3 budgeted GPU runs: S2 (keyframe + public grounding) then S1 (tracking).
set -u
R3=/home/inspur/aic_video_work/orarl_round3
W=/home/inspur/aic_video_work
PY=/home/inspur/aic_video_work/orarl_round1/env/orarl_hf/bin/python
MODEL=/home/inspur/aic_video_work/orarl_round1/model/Video-ORA-4B

run() {
  local rid="$1" cases="$2" maxsec="$3"
  echo "=== $rid cases=$cases max=$maxsec $(date -u +%T)Z ==="
  cd "$W" || exit 1
  python3 "$W/improvement_round1/budget_run.py" \
    --name "$rid" --max-seconds "$maxsec" -- \
    "$PY" "$R3/scripts/orarl_verify.py" \
         --model "$MODEL" --cases "$cases" \
         --out-root "$R3/outputs" --run-id "$rid" --attn sdpa
  echo "=== $rid rc=$? $(date -u +%T)Z ==="
}

run r3s2 "$R3/cases/cases_s2.jsonl" 1200
run r3s1 "$R3/cases/cases_s1.jsonl" 900
echo "ALL_ROUND3_JOBS_DONE"
