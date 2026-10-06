"""Reuse complete verified media, repair the manifest, then verify full PTS."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('/home/inspur/aic_video_work')
RUN = ROOT/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
PRIOR_SHA = '7ee28df8b161e9e308060df9696711ce6a42c4f6f6224b075f9596df7f552fda'

if __name__ == '__main__':
    archives = list((ROOT/'round6_score_alignment/rematch_intake/rematch_download_20261005T041135Z/archive').glob('*.zip'))
    if len(archives) != 1:
        raise RuntimeError('registered archive path ambiguous')
    code = RUN/'baseline_m0_v2'
    finalized = RUN/'baseline_a/m0_finalize_01'
    subprocess.run([sys.executable, '-B', str(code/'finalize_existing_m0.py'),
        '--zip', str(archives[0]), '--approval', str(RUN/'controller/input_role_approval_m0.json'),
        '--media-metadata', str(RUN/'baseline_a/m0_426_02/media_metadata.json'),
        '--expected-media-metadata-sha256', PRIOR_SHA,
        '--existing-media-root', str(RUN/'baseline_a/m0_426_02/media'),
        '--output-root', str(finalized)], check=True)
    receipt = json.loads((finalized/'repair_receipt.json').read_text())
    manifest = finalized/'clean_manifest_426.json'
    digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
    if receipt['status'] != 'PASS_EXISTING_M0_FINALIZED_METADATA_ONLY_PTS_PENDING' or digest != receipt['clean_manifest_sha256']:
        raise RuntimeError('finalization receipt or manifest hash mismatch')
    subprocess.run([sys.executable, '-B', str(code/'prepare_full_pts.py'),
        '--manifest', str(manifest), '--expected-manifest-sha256', digest,
        '--output-root', str(RUN/'baseline_a/pts_426_03'),
        '--ffprobe', '/home/inspur/anaconda3/envs/Andy/bin/ffprobe'], check=True)
    print('PASS_M0_REPAIR_AND_FULL_PTS_NO_INFERENCE', flush=True)
