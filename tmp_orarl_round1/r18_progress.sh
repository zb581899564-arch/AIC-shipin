#!/usr/bin/env bash
set -u
R=/home/inspur/aic_video_work/orarl_round1
echo '=== ENV BUILD state ==='
tail -3 "$R/logs/build_env.log" 2>&1
echo "venv size: $(du -sh "$R/env/orarl_hf" 2>/dev/null | cut -f1)"
ls "$R/env/orarl_hf/lib/python3.11/site-packages" 2>/dev/null | grep -c . 
echo "torch installed: $(ls -d "$R/env/orarl_hf/lib/python3.11/site-packages/torch" 2>/dev/null || echo NO)"
echo "transformers installed: $(ls -d "$R/env/orarl_hf/lib/python3.11/site-packages/transformers" 2>/dev/null || echo NO)"
echo
echo '=== stale zombie processes for the round ==='
ps -eo pid,etimes,cmd -ww | grep -E 'r09_build|r04_down|pip install|snapshot_download' | grep -v grep
echo '(end)'
echo
echo '=== MODEL ==='
du -sh "$R/model/Video-ORA-4B"
ls "$R/model/Video-ORA-4B"/*.safetensors 2>/dev/null | wc -l
find "$R/model/Video-ORA-4B/.cache" -name '*.incomplete' -printf '%s\n' 2>/dev/null | awk '{s+=$1} END {printf "incomplete=%.2f GiB\n", s/1073741824}'
echo
echo '=== logged nvidia-smi driver vs installed cuda runtime hint ==='
nvidia-smi --query-gpu=driver_version --format=csv,noheader
