#!/usr/bin/env bash
set -u
R=/home/inspur/aic_video_work/orarl_round1
echo '=== /home/inspur/aic_video_data (top level) ==='
ls -la /home/inspur/aic_video_data 2>&1 | head -40
echo
echo '=== sizes ==='
du -sh /home/inspur/aic_video_data/* 2>/dev/null | sort -h | tail -20
echo
echo '=== frozen_data ==='
ls -la "$R/../improvement_round1/frozen_data" 2>&1
echo
echo '=== data_qvh_confirmed_20260910 ==='
find /home/inspur/aic_video_work/data_qvh_confirmed_20260910 -maxdepth 3 2>/dev/null | head -40
echo
echo '=== sample video files anywhere in data dirs (first 25) ==='
find /home/inspur/aic_video_data /home/inspur/aic_video_work/data_qvh_confirmed_20260910 /home/inspur/aic_video_work/data_qvh_v2 -maxdepth 4 -type f \( -iname '*.mp4' -o -iname '*.mkv' -o -iname '*.webm' -o -iname '*.avi' \) 2>/dev/null | head -25
echo '(end)'
echo
echo '=== ENV BUILD PROGRESS ==='
tail -c 1200 "$R/logs/build_env.log" 2>&1
echo
echo '=== MODEL DOWNLOAD PROGRESS ==='
du -sh "$R/model/Video-ORA-4B" 2>&1
ls -la "$R/model/Video-ORA-4B"/*.safetensors 2>&1
