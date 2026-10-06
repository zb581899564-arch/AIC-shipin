#!/usr/bin/env bash
set -u
echo '=== uv / conda / python3.11 availability ==='
which uv 2>&1
uv --version 2>&1
which conda 2>&1
ls /home/inspur/anaconda3/bin/conda 2>&1
echo '-- python3.11 binaries --'
ls -la /usr/bin/python3.1* 2>&1
for p in /home/inspur/anaconda3/envs/*/bin/python; do
  v=$("$p" -c 'import sys;print("%d.%d"%sys.version_info[:2])' 2>/dev/null)
  if [ "$v" = "3.11" ]; then echo "3.11 FOUND: $p"; fi
done
echo '(end 3.11 scan)'
echo
echo '=== PyPI (tsinghua mirror) availability ==='
T=https://pypi.tuna.tsinghua.edu.cn/simple
for pkg in transformers torch vllm accelerate qwen-vl-utils decord av torchcodec; do
  echo "--- $pkg ---"
  curl -sS --max-time 25 "$T/$pkg/" 2>&1 | grep -o -E "$pkg-[0-9][^\"#<]*\.whl" | tail -6
done
echo
echo '=== does transformers 5.5.4 exist? ==='
curl -sS --max-time 25 "$T/transformers/" 2>&1 | grep -o -E 'transformers-5\.5\.[0-9]+[^"#<]*' | sort -u | head -20
echo '(end)'
echo
echo '=== torch versions available (manylinux cp311) ==='
curl -sS --max-time 30 "$T/torch/" 2>&1 | grep -o -E 'torch-2\.1[0-9]\.[0-9]+[^"#<]*cp311[^"#<]*manylinux[^"#<]*\.whl' | sort -u | head -20
echo '(end torch)'
echo
echo '=== pytorch wheel mirrors reachable? ==='
for u in https://mirrors.tuna.tsinghua.edu.cn/pytorch-wheels/ https://mirror.sjtu.edu.cn/pytorch-wheels/ https://download.pytorch.org/whl/cu129/; do
  curl -sS -o /dev/null -w "$u -> %{http_code} t=%{time_total}\n" --max-time 15 "$u" 2>&1
done
echo
echo '=== DOWNLOAD PROGRESS ==='
du -sh /home/inspur/aic_video_work/orarl_round1/model/Video-ORA-4B 2>&1
ls -la /home/inspur/aic_video_work/orarl_round1/model/Video-ORA-4B/*.safetensors 2>&1
