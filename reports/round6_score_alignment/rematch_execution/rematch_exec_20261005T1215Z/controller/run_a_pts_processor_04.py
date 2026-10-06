"""Recheck processor with runtime revision recorded from the actual lock.

The previous receipt is retained: its source-lock SHA is correct, but the
separate revision label was a stale test-only literal. No production change.
"""
import os
from pathlib import Path
import subprocess
import sys

RUN = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
if __name__ == '__main__':
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
        HF_HOME=str(RUN/'cache/hf'), HF_HUB_CACHE=str(RUN/'cache/hf/hub'),
        TORCH_HOME=str(RUN/'cache/torch'), XDG_CACHE_HOME=str(RUN/'cache'),
        TMPDIR=str(RUN/'tmp'), PYTHONDONTWRITEBYTECODE='1')
    subprocess.run([sys.executable,'-B',str(RUN/'baseline_a_pts_v1/test_processor_synthetic.py'),
        '--base-model','/home/inspur/aic_video_work/models/Qwen3-VL-4B-Instruct',
        '--output-root',str(RUN/'baseline_a_pts_v1/real_processor_04')], env=env,check=True)
