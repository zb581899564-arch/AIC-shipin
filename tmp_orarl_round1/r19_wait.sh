#!/usr/bin/env bash
# Poll until env build and model download both settle (or timeout).
set -u
R=/home/inspur/aic_video_work/orarl_round1
DEADLINE=$(( $(date +%s) + ${1:-540} ))
while :; do
  now=$(date +%s)
  env_done=0; dl_done=0
  if [ -d "$R/env/orarl_hf/lib/python3.11/site-packages/transformers" ] \
     && ! pgrep -f 'r09_build_env.sh' > /dev/null; then env_done=1; fi
  nshards=$(ls "$R/model/Video-ORA-4B"/*.safetensors 2>/dev/null | wc -l)
  if [ "$nshards" -ge 5 ]; then dl_done=1; fi
  echo "$(date -u +%T)Z env_done=$env_done shards=$nshards/5 venv=$(du -sh "$R/env/orarl_hf" 2>/dev/null | cut -f1) model=$(du -sh "$R/model/Video-ORA-4B" 2>/dev/null | cut -f1)"
  if [ "$env_done" -eq 1 ] && [ "$dl_done" -eq 1 ]; then
    echo "BOTH_DONE"; break
  fi
  if [ "$now" -ge "$DEADLINE" ]; then echo "TIMEOUT_WAITING"; break; fi
  sleep 30
done

echo
echo '=== ENV BUILD tail ==='
tail -c 2500 "$R/logs/build_env.log" 2>&1
echo
echo '=== env pip freeze ==='
if [ -f "$R/evidence/env_pip_freeze.txt" ]; then cat "$R/evidence/env_pip_freeze.txt"; else echo '(not yet)'; fi
echo
echo '=== model download log tail ==='
tail -c 800 "$R/logs/download_model.log" 2>&1
echo
echo '=== model dir ==='
ls -la "$R/model/Video-ORA-4B" 2>&1
echo
echo '=== disk ==='
df -B1 /home/inspur/aic_video_work | tail -1
du -s -B1 /home/inspur/aic_video_work
