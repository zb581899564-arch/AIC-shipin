#!/usr/bin/env bash
set -u
R=/home/inspur/aic_video_work/orarl_round1
DEADLINE=$(( $(date +%s) + ${1:-420} ))
while :; do
  if [ -f "$R/evidence/env_pip_freeze.txt" ] && ! pgrep -f 'r09_build_env.sh' > /dev/null; then
    echo "ENV_BUILD_FINISHED"; break
  fi
  echo "$(date -u +%T)Z venv=$(du -sh "$R/env/orarl_hf" 2>/dev/null | cut -f1) building=$(pgrep -fc 'r09_build_env.sh' 2>/dev/null || echo 0)"
  if [ "$(date +%s)" -ge "$DEADLINE" ]; then echo "TIMEOUT"; break; fi
  sleep 20
done
echo
echo '=== build log tail ==='
tail -c 3000 "$R/logs/build_env.log" 2>&1
echo
echo '=== freeze ==='
cat "$R/evidence/env_pip_freeze.txt" 2>&1 | head -60
echo
echo '=== import check result in log ==='
grep -E 'torch|transformers|python |cuda|OK|FAIL|Error|rc=' "$R/logs/build_env.log" 2>/dev/null | tail -20
