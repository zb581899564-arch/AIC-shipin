#!/usr/bin/env bash
set -u
R=/home/inspur/aic_video_work/orarl_round1
echo '=== pip / build procs ==='
ps -eo pid,etimes,pcpu,cmd -ww | grep -E 'pip|r09_build|python' | grep -v grep | head -10
echo '(end)'
echo
echo '=== pip download temp growth ==='
du -sh /home/inspur/.cache/pip 2>/dev/null
du -sh "$R/env/orarl_hf" 2>/dev/null
ls -la /tmp/pip-* 2>/dev/null | head -5
echo
echo '=== full build log size + last lines (raw) ==='
wc -l "$R/logs/build_env.log" 2>&1
tail -5 "$R/logs/build_env.log" 2>&1
echo
echo '=== model dl ==='
du -sh "$R/model/Video-ORA-4B"
ls "$R/model/Video-ORA-4B"/*.safetensors 2>/dev/null | wc -l
find "$R/model/Video-ORA-4B/.cache" -name '*.incomplete' -printf '%s\n' 2>/dev/null | awk '{s+=$1} END {printf "incomplete=%.2f GiB\n", s/1073741824}'
