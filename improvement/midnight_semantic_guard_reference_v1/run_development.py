"""Unique explicitly approved CPU-only development comparison; no implicit resume."""
import datetime as dt
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import traceback
from reference_common import checked,read,ref,require,save

ROOT=Path('/home/inspur/aic_video_work/midnight_semantic_guard_20261015_v1')
PY=ROOT.parent/'env/qwen3vl_isolated_20260910/bin/python'

def main():
    require(sys.platform=='linux' and socket.gethostname()=='inspur-NP5570M5' and Path(__file__).resolve().parent==ROOT/'code',
        'Exact independent Linux development code/root required')
    authorization=read(ROOT/'development_launch_authorization.json')
    require(authorization['scope']=='ONE_NEW_SEMANTIC_GUARD_DEVELOPMENT_CPU_COMPARISON'
        and authorization['controller_ref']==ref(__file__) and authorization['registration_ref']==ref(ROOT/'development_registration.json')
        and authorization['automatic_retry'] is False, 'Main-agent reviewed unique CPU comparison authorization required')
    require(dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat('2026-10-15T16:00:00+00:00'), 'No new comparison after deadline')
    output=ROOT/'dev_01';output.mkdir(exist_ok=False)
    command=[str(PY),'-B',str(ROOT/'code/evaluate.py'),'--registration',str(ROOT/'development_registration.json'),'--output',str(output/'comparison.json')]
    save(output/'launch.json',dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),pid=os.getpid(),
        argv=command,controller_ref=ref(__file__),registration_ref=ref(ROOT/'development_registration.json'),CPU_only=True,
        model_calls=0,vision_encodes=0,media_decodes=0,QA_replayed=0,automatic_retry=False))
    try:
        with (output/'comparison.log').open('x') as log:
            result=subprocess.run(command,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'),
                stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
        require(result.returncode in (0,5), 'Actual CPU comparison failed; preserve partial evidence without retry')
        value=read(output/'comparison.json')
        save(output/'completion.json',dict(status='NATURAL_COMPLETE_ONE_SEMANTIC_GUARD_CPU_DEVELOPMENT_COMPARISON',
            returncode=result.returncode,comparison_ref=ref(output/'comparison.json'),passed_policies=value['passed_policies'],
            full_source_count=4,adopted_original_answers=8,new_model_calls=0,new_processor_calls=0,new_media_decodes=0,old_QA_repeated=0,
            production_admitted=False,utc=dt.datetime.now(dt.timezone.utc).isoformat()))
        print(dict(status=value['status'],passed=value['passed_policies']))
    except BaseException as error:
        save(output/'failure.json',dict(status='ACTUAL_ENGINEERING_FAILURE_NO_RETRY',error=repr(error),traceback=traceback.format_exc(),
            preserve_all_success=True,new_model_calls=0,old_QA_repeated=0));raise

if __name__=='__main__':main()
