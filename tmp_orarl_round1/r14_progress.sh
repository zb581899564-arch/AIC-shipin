#!/usr/bin/env bash
set -u
R=/home/inspur/aic_video_work/orarl_round1
echo '=== ENV BUILD tail ==='
tail -c 1500 "$R/logs/build_env.log" 2>&1
echo
echo '=== venv size ==='
du -sh "$R/env/orarl_hf" 2>&1
"$R/env/orarl_hf/bin/python" -c 'import torch;print("torch",torch.__version__)' 2>&1 | tail -3
echo
echo '=== MODEL DOWNLOAD ==='
du -sh "$R/model/Video-ORA-4B" 2>&1
ls -la "$R/model/Video-ORA-4B" 2>&1
echo '-- incomplete --'
find "$R/model/Video-ORA-4B/.cache" -name '*.incomplete' -printf '%s\n' 2>/dev/null | sort -rn | awk '{s+=$1} END {printf "incomplete_bytes=%d (%.2f GiB)\n", s, s/1073741824}'
echo '-- proc --'
ps -eo pid,etimes,cmd -ww | grep -E 'r04_down|snapshot_down' | grep -v grep | head -3
echo '(end)'
echo
echo '=== disk ==='
df -B1 /home/inspur/aic_video_work | tail -1
du -s -B1 /home/inspur/aic_video_work
