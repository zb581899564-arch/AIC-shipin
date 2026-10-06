#!/usr/bin/env bash
# CPU-only verification stage. No CUDA context is created here.
set -u
R=/home/inspur/aic_video_work/orarl_round1
PY="$R/env/orarl_hf/bin/python"

echo '################ A. WEIGHT INTEGRITY + PREFLIGHT ################'
python3 "$R/scripts/verify_and_preflight.py"
echo "integrity_rc=$?"
echo
echo '################ B. CPU OFFLINE LOAD PROBE ################'
env -u HF_HUB_OFFLINE -u TRANSFORMERS_OFFLINE \
  "$PY" "$R/scripts/cpu_load_probe.py" \
  "$R/model/Video-ORA-4B" "$R/evidence/offline_load_probe.json" 2>&1 | tail -40
echo "cpu_probe_rc=${PIPESTATUS[0]}"
echo
echo '################ C. DISK AFTER CPU STAGE ################'
df -B1 /home/inspur/aic_video_work | tail -1
du -s -B1 /home/inspur/aic_video_work
