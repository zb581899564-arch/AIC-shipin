"""Frozen A temporal+CPU scheduling only; space awaits measured frame/anchor count."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

RUN=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
CTRL=RUN/'controller'
if __name__=='__main__':
    admission=CTRL/'a_rematch_temporal_01.admission.json'
    data=json.loads(admission.read_text())
    manifest=Path(data['manifest_path'])
    if hashlib.sha256(manifest.read_bytes()).hexdigest()!=data['manifest_sha256']:
        raise RuntimeError('registered rematch input manifest changed')
    code=RUN/'baseline_production_v1'
    for name,digest in data['source_hashes'].items():
        if hashlib.sha256((code/name).read_bytes()).hexdigest()!=digest:
            raise RuntimeError('frozen production source changed: '+name)
    out=RUN/'baseline_a/rematch_temporal_01'
    for stage in ['preflight','temporal','select','shots','anchors']:
        print('START_STAGE '+stage,flush=True)
        subprocess.run([sys.executable,'-B',str(code/'run_a.py'),'--stage',stage,
            '--manifest',str(manifest),'--expected-manifest-sha256',data['manifest_sha256'],
            '--run-dir',str(out),'--admission',str(admission)],check=True)
    print('PASS_TEMPORAL_AND_ANCHOR_SCHEDULE_SPACE_NOT_STARTED',flush=True)
