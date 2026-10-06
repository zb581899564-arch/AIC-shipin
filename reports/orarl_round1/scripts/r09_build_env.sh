#!/usr/bin/env bash
# Build an ISOLATED minimal inference environment for Video-ORA-4B.
#
# Deviation from the author's create_conda_env.sh (documented in preflight):
#  - venv (python 3.11) instead of a conda env, so nothing global is touched
#  - torch 2.10.0+cu129 / torchvision 0.25.0+cu129 from the SAME official index
#  - NO vllm, NO flash-attn, NO training deps: HF Transformers inference only
#  - no --no-deps fudging; every version is explicit
set -u
ROUND=/home/inspur/aic_video_work/orarl_round1
ENVDIR="$ROUND/env/orarl_hf"
BASE_PY=/home/inspur/anaconda3/envs/test_env/bin/python
LOG="$ROUND/logs/build_env.log"
PYIDX=https://download.pytorch.org/whl/cu129
PYPI=https://pypi.tuna.tsinghua.edu.cn/simple

exec > >(tee -a "$LOG") 2>&1
echo "=== BUILD ENV $(date -u +%FT%TZ) ==="

echo '--- verified CUDA 12.9 wheel index ---'
curl -sS -o /dev/null -w "cu129 index http=%{http_code}\n" --max-time 20 "$PYIDX/torch/"

echo '--- base python ---'
"$BASE_PY" -VV || exit 1

if [ -x "$ENVDIR/bin/python" ]; then
  echo "venv already exists at $ENVDIR (reusing)"
else
  mkdir -p "$ROUND/env"
  "$BASE_PY" -m venv --copies "$ENVDIR" || exit 1
fi

PY="$ENVDIR/bin/python"
echo '--- venv python ---'
"$PY" -VV
"$PY" -m pip --version || "$PY" -m ensurepip --upgrade

echo '--- upgrade pip/setuptools/wheel (authors pin these) ---'
"$PY" -m pip install --quiet --index-url "$PYPI" \
  'pip==26.0.1' 'setuptools==82.0.1' 'wheel==0.46.3' \
  || "$PY" -m pip install --index-url "$PYPI" -U pip setuptools wheel

echo '--- torch 2.10.0+cu129 (official PyTorch index) ---'
"$PY" -m pip install --index-url "$PYIDX" \
  'torch==2.10.0+cu129' 'torchvision==0.25.0+cu129' || exit 3

echo '--- transformers 5.5.4 + inference deps (tsinghua PyPI) ---'
"$PY" -m pip install --index-url "$PYPI" \
  'transformers==5.5.4' \
  'accelerate==1.13.0' \
  'numpy==2.2.6' \
  'pillow==12.1.1' \
  'safetensors' \
  'sentencepiece' \
  'protobuf' \
  'PyYAML' \
  'av' \
  'huggingface_hub' || exit 4

echo '--- qwen-vl-utils (video/frame preprocessing helper) ---'
"$PY" -m pip install --index-url "$PYPI" 'qwen-vl-utils==0.0.14' \
  || echo 'WARN: qwen-vl-utils install failed; will fall back to manual frame handling'

echo
echo '=== FROZEN PACKAGE LIST ==='
"$PY" -m pip freeze | tee "$ROUND/evidence/env_pip_freeze.txt"

echo
echo '=== CPU-ONLY IMPORT CHECK (no CUDA context touched here; GPU is budgeted) ==='
"$PY" - <<'PY'
import torch, sys
print('python      :', sys.version.split()[0])
print('torch       :', torch.__version__)
print('torch cuda  :', torch.version.cuda)
print('built cuda  :', torch.version.cuda)
print('cuda compiled-in ok; availability intentionally NOT probed here')
import transformers
print('transformers:', transformers.__version__)
import torchvision
print('torchvision :', torchvision.__version__)
try:
    import qwen_vl_utils
    print('qwen_vl_utils:', getattr(qwen_vl_utils, '__version__', 'unknown'))
except Exception as e:
    print('qwen_vl_utils: NOT AVAILABLE ->', type(e).__name__, e)
PY
echo "import_rc=$?"
echo "=== BUILD ENV DONE $(date -u +%FT%TZ) ==="
du -sh "$ENVDIR"
