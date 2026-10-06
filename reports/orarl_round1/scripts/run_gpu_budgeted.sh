#!/usr/bin/env bash
# Budgeted GPU verification run.
#
# Everything that touches CUDA goes through the project's existing
# improvement_round1/budget_run.py so it is serialized against other jobs,
# charged to the 24 h campaign budget, and given offline env vars.
# Reserved wall time for this round: 1740 s (29 min), inside the 30 min cap.
set -u
ROUND=/home/inspur/aic_video_work/orarl_round1
WORK=/home/inspur/aic_video_work
PY="$ROUND/env/orarl_hf/bin/python"
NAME="${1:-orarl_r1_verify}"
MAXSEC="${2:-1740}"

cd "$WORK" || exit 1
echo "budget job name : $NAME"
echo "max seconds     : $MAXSEC"
echo "python          : $PY"

python3 "$WORK/improvement_round1/budget_run.py" \
  --name "$NAME" \
  --max-seconds "$MAXSEC" \
  -- "$PY" "$ROUND/scripts/run_inference.py" \
       --model "$ROUND/model/Video-ORA-4B" \
       --samples "$ROUND/evidence/sample_manifest.json" \
       --out "$ROUND/outputs" \
       --attn sdpa \
       --tasks spatial_grounding,temporal_grounding,tracking
rc=$?
echo "budget_run rc=$rc"
echo "--- job log tail ---"
tail -c 3000 "$WORK/improvement_round1/$NAME.log" 2>&1
exit $rc
