#!/usr/bin/env bash
set -u
echo "=== MIRROR REACHABILITY ==="
probe() { curl -sS -o /dev/null -w "$1 http=%{http_code} t=%{time_total}\n" --max-time 12 "$2" 2>&1; }
probe "ghproxy.net          " https://ghproxy.net/
probe "gh-proxy.com         " https://gh-proxy.com/
probe "ghfast.top           " https://ghfast.top/
probe "hub.gitmirror.com    " https://hub.gitmirror.com/
probe "kkgithub.com         " https://kkgithub.com/
probe "gitee.com            " https://gitee.com/
probe "gitclone.com         " https://gitclone.com/
probe "hf-mirror.com        " https://hf-mirror.com/
probe "modelscope.cn        " https://www.modelscope.cn/
probe "pypi.tuna.tsinghua   " https://pypi.tuna.tsinghua.edu.cn/simple/
probe "mirrors.aliyun pypi  " https://mirrors.aliyun.com/pypi/simple/
echo
echo "=== HF MODEL METADATA VIA hf-mirror ==="
curl -sS --max-time 30 https://hf-mirror.com/api/models/OraRL/Video-ORA-4B 2>&1 | head -c 4000
echo
echo
echo "=== ANACONDA ENVS ==="
ls -la /home/inspur/anaconda3/envs 2>&1
echo "-- base python --"
/home/inspur/anaconda3/bin/python -VV 2>&1
echo
echo "=== EXISTING ENV: qwen3vl ==="
/home/inspur/aic_video_work/env/qwen3vl/bin/python -VV 2>&1
/home/inspur/aic_video_work/env/qwen3vl/bin/pip list 2>/dev/null | grep -i -E 'torch|transformers|accelerate|qwen|flash|vision|numpy|pillow|decord|av|opencv' 
echo
echo "=== EXISTING ENV: qwen3vl_isolated ==="
/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python -VV 2>&1
/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/pip list 2>/dev/null | grep -i -E 'torch|transformers|accelerate|qwen|flash|vision|numpy|pillow|decord|av|opencv'
echo
echo "=== EXISTING MODEL DIRS ==="
du -sh /home/inspur/aic_video_work/models/* 2>/dev/null
echo
echo "=== CACHE DIRS ==="
ls -la /home/inspur/.cache 2>&1
du -sh /home/inspur/.cache/* 2>/dev/null
echo
echo "=== nvcc / cuda ==="
which nvcc 2>&1; nvcc --version 2>&1 | tail -3
ls -d /usr/local/cuda* 2>&1
