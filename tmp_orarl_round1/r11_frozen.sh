#!/usr/bin/env bash
set -u
FD=/home/inspur/aic_video_work/improvement_round1/frozen_data
echo '=== frozen_data/lock.json ==='
cat "$FD/lock.json"
echo
echo '=== frozen_data/dev.jsonl : first 2 rows, keys only ==='
head -2 "$FD/dev.jsonl" | python3 -c '
import sys, json
for line in sys.stdin:
    d = json.loads(line)
    print("KEYS:", sorted(d.keys()))
    print(json.dumps(d, ensure_ascii=False)[:1500])
    print("---")
'
echo
echo '=== row counts ==='
wc -l "$FD"/*.jsonl
echo
echo '=== labels dir ==='
ls -la /home/inspur/aic_video_data/labels 2>&1
echo
echo '=== test dir ==='
find /home/inspur/aic_video_data/test -maxdepth 3 2>/dev/null | head -20
echo
echo '=== ffprobe sample source videos ==='
for f in /home/inspur/aic_video_data/videos/c/c1lX1gd5I78_660.0_810.0.mp4 /home/inspur/aic_video_data/videos/c/CiRbi0f5Nwo_210.0_360.0.mp4; do
  echo "--- $f"
  ffprobe -v error -select_streams v:0 \
    -show_entries stream=width,height,r_frame_rate,nb_frames,duration,codec_name \
    -show_entries format=duration,size,format_name \
    -of default=noprint_wrappers=0 "$f" 2>&1
  sha256sum "$f"
done
echo
echo '=== videos subdir count ==='
ls /home/inspur/aic_video_data/videos | wc -l
du -sh /home/inspur/aic_video_data/videos
