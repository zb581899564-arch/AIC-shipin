"""Explicit metadata/video intake and separate automatic PTS gate. No models."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path('/home/inspur/aic_video_work')
RUN=ROOT/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
if __name__=='__main__':
    files=list((ROOT/'round6_score_alignment/rematch_intake/rematch_download_20261005T041135Z/archive').glob('*.zip'))
    if len(files)!=1:
        raise RuntimeError('registered archive path is ambiguous')
    stage=RUN/'baseline_a/m0_426_02'
    subprocess.run([sys.executable,'-B',str(RUN/'baseline_a/prepare_rematch_m0.py'),
        '--zip',str(files[0]),'--approval',str(RUN/'controller/input_role_approval_m0.json'),
        '--output-root',str(stage),'--ffprobe','/home/inspur/anaconda3/envs/Andy/bin/ffprobe'],check=True)
    manifest=stage/'clean_manifest_426.json'
    receipt=json.loads((stage/'m0_receipt.json').read_text())
    digest=hashlib.sha256(manifest.read_bytes()).hexdigest()
    if digest!=receipt['manifest_sha256']:
        raise RuntimeError('clean metadata manifest changed')
    subprocess.run([sys.executable,'-B',str(RUN/'baseline_a/prepare_full_pts.py'),
        '--manifest',str(manifest),'--expected-manifest-sha256',digest,
        '--output-root',str(RUN/'baseline_a/pts_426_02'),
        '--ffprobe','/home/inspur/anaconda3/envs/Andy/bin/ffprobe'],check=True)
    print('PASS_M0_AND_SEPARATE_PTS_NO_INFERENCE',flush=True)
