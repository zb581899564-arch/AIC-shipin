#!/usr/bin/env bash
set -euo pipefail
R=/home/inspur/aic_video_work/round6_score_alignment/r7_temporal_pool/round7_temporal_pool_20260921T090903Z
B=/home/inspur/aic_video_work/improvement_round1/budget_run.py
PY=/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python
P2=/home/inspur/aic_video_work/round6_score_alignment/p2t_temporal_improvement/round6_p2t2_equal_exposure_20260920T1555Z/runs/full_epochs5/adapter
python3 "$B" --name r7_dev_base_20260921t2349 --max-seconds 900 -- "$PY" -B "$R/code/remote_infer_r7.py" --manifest "$R/inputs/dev_temporal.jsonl" --arm BASE --output "$R/outputs/dev/base.jsonl"
python3 "$B" --name r7_dev_p2t2_20260921t2349 --max-seconds 900 -- "$PY" -B "$R/code/remote_infer_r7.py" --manifest "$R/inputs/dev_temporal.jsonl" --arm P2T2 --adapter "$P2" --output "$R/outputs/dev/p2t2.jsonl"
python3 "$B" --name r7_dev_r7_20260921t2349 --max-seconds 900 -- "$PY" -B "$R/code/remote_infer_r7.py" --manifest "$R/inputs/dev_temporal.jsonl" --arm R7 --adapter "$R/runs/full120/adapter" --output "$R/outputs/dev/r7.jsonl"
