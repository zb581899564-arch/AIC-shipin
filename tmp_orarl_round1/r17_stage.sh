#!/usr/bin/env bash
# Stage the round's scripts into the remote scripts/ directory and syntax-check.
set -u
R=/home/inspur/aic_video_work/orarl_round1
mkdir -p "$R/scripts" "$R/logs" "$R/evidence" "$R/clips" "$R/frames" "$R/outputs"
echo '=== staged files ==='
for f in prepare_samples.sh run_inference.py make_overlays.py verify_and_preflight.py run_gpu_budgeted.sh; do
  if [ -f "$R/scripts/$f" ]; then
    echo "  $f  $(wc -c < "$R/scripts/$f") bytes  $(sha256sum "$R/scripts/$f" | cut -c1-16)"
  else
    echo "  MISSING $f"
  fi
done
echo
echo '=== syntax check (system python3.9 for py, bash -n for sh) ==='
python3 -m py_compile "$R/scripts/run_inference.py" && echo 'run_inference.py OK' || echo 'run_inference.py SYNTAX ERROR'
python3 -m py_compile "$R/scripts/make_overlays.py" && echo 'make_overlays.py OK' || echo 'make_overlays.py SYNTAX ERROR'
python3 -m py_compile "$R/scripts/verify_and_preflight.py" && echo 'verify_and_preflight.py OK' || echo 'verify_and_preflight.py SYNTAX ERROR'
bash -n "$R/scripts/prepare_samples.sh" && echo 'prepare_samples.sh OK' || echo 'prepare_samples.sh SYNTAX ERROR'
bash -n "$R/scripts/run_gpu_budgeted.sh" && echo 'run_gpu_budgeted.sh OK' || echo 'run_gpu_budgeted.sh SYNTAX ERROR'
