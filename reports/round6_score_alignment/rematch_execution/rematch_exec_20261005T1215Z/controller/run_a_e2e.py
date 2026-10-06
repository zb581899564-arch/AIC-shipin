"""Single registered non-test regression of the new A production entry."""
import hashlib
import argparse
from pathlib import Path
import subprocess
import sys

RUN=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
BASE=RUN/'baseline_a'
MANIFEST=BASE/'inputs/non_test_frozen8.json'
EXPECTED='7b3e187451eb15f80647b4441a4a41f030f4be1438a95ef5b7982a53554f153a'
OUT=BASE/'nontest_e2e_01'
ADMISSION=RUN/'controller/a_nontest_admission.json'

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--attempt',choices=['01','02','03','04'],default='01')
    args=parser.parse_args()
    if args.attempt!='01':
        OUT=BASE/('nontest_e2e_'+args.attempt)
        ADMISSION=RUN/'controller'/('a_nontest_admission_'+args.attempt+'.json')
    if hashlib.sha256(MANIFEST.read_bytes()).hexdigest()!=EXPECTED:
        raise RuntimeError('frozen non-test manifest identity mismatch')
    for stage in ['preflight','temporal','select','shots','anchors','spatial','compose','package']:
        print('START_STAGE '+stage,flush=True)
        subprocess.run([sys.executable,'-B',str(BASE/'run_a.py'),'--stage',stage,
            '--manifest',str(MANIFEST),'--expected-manifest-sha256',EXPECTED,
            '--run-dir',str(OUT),'--admission',str(ADMISSION)],check=True)
    print('PASS_A_NEW_ENTRY_NONTEST_E2E',flush=True)
