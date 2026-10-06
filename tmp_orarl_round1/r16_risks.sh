#!/usr/bin/env bash
set -u
echo '=== SYSTEM RAM / CPU ==='
free -g
nproc
echo
echo '=== flash-linear-attention availability (tsinghua) ==='
curl -sS --max-time 25 https://pypi.tuna.tsinghua.edu.cn/simple/flash-linear-attention/ 2>&1 \
  | grep -o -E 'flash[-_]linear[-_]attention-0\.[0-9.]+[^"#<]*\.(whl|tar\.gz)' | sort -u | tail -12
echo '(end fla)'
echo
echo '=== causal-conv1d / mamba-ssm ==='
curl -sS --max-time 20 https://pypi.tuna.tsinghua.edu.cn/simple/causal-conv1d/ 2>&1 | grep -o -E 'causal[-_]conv1d-[0-9][^"#<]*' | sort -u | tail -4
echo '(end cc1d)'
echo
echo '=== cu128 fallback wheel present? ==='
curl -sS -o /dev/null -w 'cu128 index http=%{http_code}\n' --max-time 20 https://download.pytorch.org/whl/cu128/
curl -sS --max-time 25 https://download.pytorch.org/whl/cu128/torch/ 2>&1 \
  | grep -o -E 'torch-2\.10\.0%2Bcu128-cp311[^"#<]*\.whl' | sort -u | head -3
echo '(end cu128)'
echo
echo '=== transformers 5.5.4 present on tsinghua? (confirm) ==='
curl -sS --max-time 25 https://pypi.tuna.tsinghua.edu.cn/simple/transformers/ 2>&1 \
  | grep -c 'transformers-5.5.4-py3-none-any.whl'
echo
echo '=== current driver CUDA capability ==='
nvidia-smi | head -4
python3 -c 'print("system python", __import__("sys").version.split()[0])'
