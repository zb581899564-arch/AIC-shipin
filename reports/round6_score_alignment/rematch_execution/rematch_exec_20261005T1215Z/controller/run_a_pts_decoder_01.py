"""Run the independent marker-video test with GPU hidden and bounded outputs."""
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
    result = subprocess.run([sys.executable, '-B',
        str(RUN/'baseline_a_pts_v1/test_decoder_synthetic.py'),
        '--ffmpeg', '/home/inspur/anaconda3/envs/Andy/bin/ffmpeg',
        '--ffprobe', '/home/inspur/anaconda3/envs/Andy/bin/ffprobe',
        '--output-root', str(RUN/'baseline_a_pts_v1/real_decoder_01')], env=env)
    raise SystemExit(result.returncode)
