#!/usr/bin/env bash
set -u
R=/home/inspur/aic_video_work/orarl_round1
echo '=== download procs (single-quote safe) ==='
ps -eo pid,ppid,etimes,cmd -ww | grep -i -E 'snapshot|huggingface|r04_down|python' | grep -v grep
echo '(end)'
echo
echo '=== log tail ==='
tail -c 1500 "$R/logs/download_model.log" 2>&1
echo
echo
echo '=== model dir size ==='
du -sh "$R/model/Video-ORA-4B" 2>&1
echo
echo '=== safetensors present ==='
ls -la "$R/model/Video-ORA-4B"/*.safetensors 2>&1
echo
echo '=== dir listing ==='
ls -la "$R/model/Video-ORA-4B" 2>&1
echo
echo '=== incomplete blobs ==='
find "$R/model/Video-ORA-4B/.cache" -name '*.incomplete' -exec ls -la {} \; 2>&1
echo '(end)'
