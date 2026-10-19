"""Explicit CPU post-stage sequence only; no GPU launch, retry or waiting."""
import os
import sys
import json
import subprocess
import time
import datetime as dt
import traceback
from pathlib import Path

ROOT = Path('/home/inspur/aic_video_work/relative_precision_event_20261018_v1')
PIPELINE = ROOT/'confirm4c_01'
PY = '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
SEQUENCES = dict(b0_post=['b0_output_qa','verify_prepare','verify_input_qa'],
                verify_post=['verify_output_qa','context_prepare','context_input_qa'],
                context_post=['context_output_qa','finalize'])


def save(p, value):
    with p.open('x') as f:
        json.dump(value,f,indent=2,allow_nan=False)


def main():
    name = sys.argv[1]
    sequence = SEQUENCES[name]
    root = PIPELINE/('sequence_'+name)
    root.mkdir()
    save(root/'launch_claim.json',dict(pid=os.getpid(),stages=sequence,parent_CUDA=os.environ.get('CUDA_VISIBLE_DEVICES'),utc=dt.datetime.now(dt.timezone.utc).isoformat()))
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == '0'
    started = time.monotonic()
    for stage in sequence:
        with (root/(stage+'.log')).open('xb') as f:
            p = subprocess.run([PY,'-B','/home/inspur/aic_video_work/calibrated_event_20261018_v1/confirm_pipeline_code_v1/pipeline.py',str(PIPELINE/'pipeline_config_01.json'),stage],stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,env=os.environ.copy())
        if p.returncode:
            raise RuntimeError(stage+' actual exit '+str(p.returncode))
        if stage == 'verify_prepare':
            done = json.loads((PIPELINE/'stages/verify_prepare/completion.json').read_text())
            assert done['expected_calls'] <= 192, 'Pre-registered first VERIFY call cap exceeded; no GPU automatically'
        if stage == 'context_prepare':
            done = json.loads((PIPELINE/'stages/context_prepare/completion.json').read_text())
            assert done['expected_queries'] <= 1024, 'Pre-registered first context query cap exceeded; no GPU automatically'
    save(root/'completion.json',dict(status='COMPLETED_CPU_SEQUENCE_EXIT0',stages=sequence,elapsed=time.monotonic()-started,utc=dt.datetime.now(dt.timezone.utc).isoformat()))


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        root = PIPELINE/('sequence_'+sys.argv[1])
        if root.exists():
            save(root/'failure.json',dict(error=repr(error),traceback=traceback.format_exc(),successful_stages_preserved=True))
        raise
