#!/usr/bin/env bash
# Download the official Video-ORA-4B snapshot at the pinned revision.
# Non-GPU, network-only work: intentionally NOT run under budget_run.py
# (budget_run.py forces offline mode and only governs GPU jobs).
set -u
ROUND=/home/inspur/aic_video_work/orarl_round1
MODEL="$ROUND/model/Video-ORA-4B"
REV=01850297d5ab2adaaf130f700ed7cec52993d956
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_DISABLE_TELEMETRY=1
export PYTHONUNBUFFERED=1

PY=/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python
if [ ! -x "$PY" ]; then PY=$(which python3); fi
echo "python: $PY"
"$PY" -c "import huggingface_hub as h; print('huggingface_hub', h.__version__)"

mkdir -p "$MODEL"
echo "=== START $(date -u +%FT%TZ) ==="
"$PY" - <<PY
from huggingface_hub import snapshot_download
import time
t0 = time.time()
p = snapshot_download(
    repo_id="OraRL/Video-ORA-4B",
    revision="$REV",
    local_dir="$MODEL",
    ignore_patterns=["code/*", "assets/*", "*.gif", "*.mp4", "*.png", "*.svg"],
    max_workers=4,
)
print("snapshot_download ->", p)
print("elapsed_seconds %.1f" % (time.time() - t0))
PY
echo "=== snapshot_rc=$? $(date -u +%FT%TZ) ==="
echo "=== DONE $(date -u +%FT%TZ) ==="
du -sh "$MODEL" 2>&1
ls -la "$MODEL"
