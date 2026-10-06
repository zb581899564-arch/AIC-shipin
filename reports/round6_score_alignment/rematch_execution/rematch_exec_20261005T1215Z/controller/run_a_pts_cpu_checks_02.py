"""Recheck final revision03 against both real registries and installed CPU processor."""
import json
import os
from pathlib import Path
import subprocess
import sys

RUN = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
CODE = RUN/'baseline_a_pts_v1'
PTS = RUN/'baseline_pts_v4'

if __name__ == '__main__':
    for name, output in [('nontest_registry_01','static_nontest_03'),('scan_01','static_rematch_03')]:
        r = json.loads((PTS/name/'reaudit_receipt.json').read_text())
        subprocess.run([sys.executable,'-B',str(CODE/'run_pts.py'),'--stage','preflight',
            '--manifest',r['clean_manifest']['path'],'--expected-manifest-sha256',r['clean_manifest']['sha256'],
            '--clock-registry',r['clock_registry']['path'],'--expected-clock-registry-sha256',r['clock_registry']['sha256'],
            '--run-dir',str(CODE/output),'--static-only'],check=True)
    env = dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
        HF_HOME=str(RUN/'cache/hf'),HF_HUB_CACHE=str(RUN/'cache/hf/hub'),TORCH_HOME=str(RUN/'cache/torch'),
        XDG_CACHE_HOME=str(RUN/'cache'),TMPDIR=str(RUN/'tmp'),PYTHONDONTWRITEBYTECODE='1')
    subprocess.run([sys.executable,'-B',str(CODE/'test_processor_synthetic.py'),
        '--base-model','/home/inspur/aic_video_work/models/Qwen3-VL-4B-Instruct',
        '--output-root',str(CODE/'real_processor_02')],check=True,env=env)
