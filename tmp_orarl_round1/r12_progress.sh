#!/usr/bin/env bash
set -u
R=/home/inspur/aic_video_work/orarl_round1
echo '=== ENV BUILD tail ==='
tail -c 2000 "$R/logs/build_env.log" 2>&1
echo
echo '=== env venv exists? ==='
ls -la "$R/env/orarl_hf/bin/python" 2>&1
du -sh "$R/env/orarl_hf" 2>&1
echo
echo '=== MODEL DOWNLOAD ==='
du -sh "$R/model/Video-ORA-4B" 2>&1
ls -la "$R/model/Video-ORA-4B" 2>&1
echo '-- incomplete blobs --'
find "$R/model/Video-ORA-4B/.cache" -name '*.incomplete' -printf '%s %p\n' 2>/dev/null | sort -rn
echo '-- download proc alive? --'
ps -eo pid,etimes,cmd -ww | grep -E 'snapshot|huggingface|r04_down' | grep -v grep
echo '(end)'
echo
echo '=== ffmpeg / ffprobe anywhere ==='
which ffmpeg ffprobe 2>&1
ls /home/inspur/anaconda3/bin/ffmpeg /home/inspur/anaconda3/bin/ffprobe 2>&1
find /home/inspur/anaconda3/envs -maxdepth 3 -name ffprobe 2>/dev/null | head -5
echo
echo '=== disk now ==='
df -B1 /home/inspur/aic_video_work
du -s -B1 /home/inspur/aic_video_work
