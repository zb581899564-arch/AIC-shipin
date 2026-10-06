"""Execute only the explicitly admitted A-PTS stage list under shared GPU lock."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

RUN = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
CODE = RUN/'baseline_a_pts_v1'
SCOPES = {
    'NONTEST_ALL_STAGES': ['preflight','temporal','select','shots','anchors','spatial','compose','package'],
    'REMATCH_TEMPORAL_SCHEDULING': ['preflight','temporal','select','shots','anchors'],
    'REMATCH_SPACE_AND_PACKAGE': ['spatial','compose','package'],
}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--admission', type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.admission.read_text())
    stages = SCOPES.get(data.get('scope'))
    if (stages is None or data.get('allowed_stages') != stages or data.get('authorized') is not True
        or data.get('competition_upload_authorized') is not False):
        raise RuntimeError('registered A-PTS stage scope missing or changed')
    for key in ('manifest','clock_registry'):
        if sha(data[key+'_path']) != data[key+'_sha256']:
            raise RuntimeError('registered A-PTS '+key+' identity changed')
    if sha(CODE/'source_lock.json') != data['source_lock_sha256']:
        raise RuntimeError('registered A-PTS source lock changed')
    for stage in stages:
        print('START_A_PTS_STAGE '+stage, flush=True)
        subprocess.run([sys.executable,'-B',str(CODE/'run_pts.py'),'--stage',stage,
            '--manifest', data['manifest_path'], '--expected-manifest-sha256',data['manifest_sha256'],
            '--clock-registry',data['clock_registry_path'],
            '--expected-clock-registry-sha256',data['clock_registry_sha256'],
            '--run-dir',data['run_dir'],'--admission',str(args.admission)], check=True)
    print('PASS_ADMITTED_A_PTS_STAGES '+data['scope'], flush=True)
