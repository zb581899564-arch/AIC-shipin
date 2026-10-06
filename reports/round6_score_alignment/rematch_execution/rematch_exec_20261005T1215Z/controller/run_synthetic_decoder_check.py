"""Only CPU black synthetic media, no contest images/labels/models."""
from pathlib import Path
import subprocess
import sys
RUN=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
if __name__=='__main__':
    command=[sys.executable,'-B',str(RUN/'baseline_pts_v3/test_decoder_synthetic.py'),
        '--output-root',str(RUN/'baseline_pts_v3/synthetic_decoder_01'),
        '--ffmpeg','/home/inspur/anaconda3/envs/Andy/bin/ffmpeg',
        '--ffprobe','/home/inspur/anaconda3/envs/Andy/bin/ffprobe','--decord-num-threads','0']
    raise SystemExit(subprocess.call(command))
