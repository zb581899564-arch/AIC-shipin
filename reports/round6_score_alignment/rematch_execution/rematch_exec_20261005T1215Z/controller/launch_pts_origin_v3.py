"""Registered numeric-only 426-source CPU identity audit, not inference."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess

RUN=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
CTRL=RUN/'controller'
PY='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
if __name__=='__main__':
    code=RUN/'baseline_pts_v3'
    expected={'time_origin_core.py':'ebfc9e0e9b5978fb8bf4503513120d057aab8190a253b5323b3e1e451b3ad5e5',
        'numeric_source_worker.py':'0ab8632ded07c7b3c13c362845d7e46d68f67d721ccd2bd74eff58bb0bd81638',
        'scan_source_origin.py':'71352ff3dd7bd9a45427887002c9818400531360ed1cb75dc24cd48399b7453f'}
    for name,digest in expected.items():
        if hashlib.sha256((code/name).read_bytes()).hexdigest()!=digest:
            raise RuntimeError('frozen CPU source hash mismatch: '+name)
    command=[PY,'-B','-u',str(code/'scan_source_origin.py'),
        '--manifest',str(RUN/'baseline_a/m0_finalize_01/clean_manifest_426.json'),
        '--expected-manifest-sha256','57a6985ad8248ae9ee64d24adc1f84eea1ac9f1b19f90da3c6647d8befa15d32',
        '--output-root',str(code/'scan_01'),
        '--ffprobe','/home/inspur/anaconda3/envs/Andy/bin/ffprobe',
        '--source-timeout-seconds','900','--decord-num-threads','0']
    with (CTRL/'pts_origin_v3.launcher.log').open('x') as log:
        process=subprocess.Popen(command,cwd=RUN,stdin=subprocess.DEVNULL,
            stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    receipt={'task':'pts_origin_v3_scan_01','pid':process.pid,'started_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'command':command,'source_hashes':expected,'gpu_used':False,'models_run':False,
        'images_exported_or_displayed':False,'failure_denominator':426,
        'inference_allowed_by_this_audit':False}
    with (CTRL/'pts_origin_v3.launch.json').open('x') as output:
        json.dump(receipt,output,indent=2)
        output.write('\n')
    print(json.dumps(receipt),flush=True)
