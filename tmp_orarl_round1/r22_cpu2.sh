#!/usr/bin/env bash
set -u
R=/home/inspur/aic_video_work/orarl_round1
PY="$R/env/orarl_hf/bin/python"

echo '################ A. OFFICIAL SHA-256 VERIFICATION ################'
python3 "$R/scripts/verify_official_sha256.py"
echo "sha_rc=$?"
echo
echo '################ B. CPU OFFLINE LOAD PROBE (fixed) ################'
env -u HF_HUB_OFFLINE -u TRANSFORMERS_OFFLINE \
  "$PY" "$R/scripts/cpu_load_probe.py" \
  "$R/model/Video-ORA-4B" "$R/evidence/offline_load_probe.json" 2>&1 | tail -25
echo "cpu_probe_rc=${PIPESTATUS[0]}"
