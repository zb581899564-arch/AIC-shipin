"""Bounded continuation after the registered CPU schedule, with no retries."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
import zipfile

ROOT=Path('/home/inspur/aic_video_work')
RUN=ROOT/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
CTRL,CODE,REC=RUN/'controller',RUN/'baseline_a_pts_v1',RUN/'baseline_a_format_recovery_v1'
OUTPUT=CODE/'rematch_e2e_recovery_01'

def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1<<20),b''):digest.update(block)
    return digest.hexdigest()
def read(path):return json.loads(Path(path).read_text())
def require(ok,message):
    if not ok:raise RuntimeError(message)
def checkpoint(stage,**extra):
    result=dict(stage=stage,checked_utc=dt.datetime.now(dt.timezone.utc).isoformat(),pid=os.getpid(),
        variant='A_FORMAT_CONSTRAINED_RECOVERY_V1',formal_C_training_admitted=False,
        competition_upload_authorized=False,**extra)
    path=CTRL/'format_pipeline_latest.json'
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(result,indent=2)+'\n')
    temporary.replace(path)
    print(json.dumps(result),flush=True)
    return result
def invoke(script,*args):
    result=subprocess.run([sys.executable,'-B',str(CTRL/script),*args],cwd=RUN,
        capture_output=True,text=True,timeout=180)
    print(result.stdout,flush=True)
    if result.stderr:print(result.stderr,flush=True)
    require(result.returncode==0,'continuation step refused: '+script)
def wait_resource(phase):
    admission=read(CTRL/('format_'+phase+'_01.admission.json'))
    launch=read(CTRL/('format_'+phase+'_01.launch.json'))
    deadline=dt.datetime.fromisoformat(launch['started_utc']).timestamp()+admission['single_job_max_seconds']+1800+180
    path=CTRL/('rematch_format_'+phase+'_01.resource.json')
    while not path.exists():
        require(time.time()<deadline,'missing bounded shared-runner receipt: '+phase)
        time.sleep(15)
    receipt=read(path)
    require(receipt['status']=='completed' and receipt['exit_code']==0 and receipt['stop_reason'] is None,
        'owned job did not succeed: '+phase)
    return path

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--expected-lock-sha256',required=True)
    args=ap.parse_args()
    completion=CTRL/'format_pipeline_completion.json'
    require(not completion.exists(),'completion already exists; no duplicate continuation')
    with (CTRL/'format_finish.registration.json').open('x') as handle:
        json.dump(dict(pid=os.getpid(),expected_lock_sha256=args.expected_lock_sha256),handle)
    try:
        def verify():
            lock_path=CTRL/'format_recovery_finish_lock.json'
            require(sha(lock_path)==args.expected_lock_sha256,'registered continuation lock changed')
            lock=read(lock_path)
            for name,digest in lock['files'].items():require(sha(CTRL/name)==digest,'finish helper changed: '+name)
            helper=read(CTRL/'format_recovery_controller_lock.json')
            for name,digest in helper['files'].items():require(sha(CTRL/name)==digest,'controller changed: '+name)
            for name,digest in read(REC/'source_lock.json')['files'].items():
                require(sha(REC/name)==digest,'format source changed: '+name)
            require(sha(CODE/'source_lock.json')=='86fc0da7cf631a2afe33c54fb5b66246bba88adfd95c1d8ce80ccbf73522d70d',
                'frozen A-PTS snapshot changed')
        verify()
        checkpoint('WAITING_REGISTERED_CPU_SCHEDULE')
        schedule_resource=wait_resource('schedule')
        verify()
        require(read(OUTPUT/'temporal.stage.json')['invalid_windows']==0
            and read(OUTPUT/'temporal.stage.json')['unchanged_successful_windows']==516,
            'complete temporal recovery not accepted')
        checkpoint('WAITING_LIVE_RESOURCE_FOR_SPACE',schedule_resource_sha256=sha(schedule_resource))
        deadline=time.monotonic()+1800
        while True:
            compute=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,used_memory',
                '--format=csv,noheader'],text=True).strip()
            if not compute and not (ROOT/'improvement_round1/active_gpu_job.json').exists():break
            require(time.monotonic()<deadline,'shared GPU conflict remains; external tasks untouched')
            time.sleep(15)
        verify()
        invoke('admit_format_recovery_stage.py','space')
        admission=read(CTRL/'format_space_01.admission.json')
        checkpoint('SPACE_COMPOSE_PACKAGE_ADMITTED',actual_scheduling=admission['scheduling'],
            single_job_max_seconds=admission['single_job_max_seconds'],planned_output_bytes=admission['planned_output_bytes'])
        verify()
        invoke('launch_format_recovery_stage.py','space')
        checkpoint('WAITING_REGISTERED_SPACE_COMPOSE_PACKAGE',actual_scheduling=admission['scheduling'])
        space_resource=wait_resource('space')
        verify()
        package=read(OUTPUT/'package.stage.json')
        validation=read(OUTPUT/'independent_validation.json')
        candidate=OUTPUT/'candidate_A_PTS.zip'
        require(package['status']=='PASS_FORMAT_PROVENANCE_PACKAGE_NOT_OFFICIALLY_SCORED'
            and package['video_records']==426 and not package['issues']
            and package['weak_roi_inputs_used']==package['old_test_boxes_used']==package['silent_fallbacks']==0
            and validation['status']=='PASS_INDEPENDENT_STRICT_VALIDATION' and all(validation['checks'].values())
            and validation['video_records']==426
            and validation['missing']==validation['extra']==validation['duplicate_frames']==0,
            'complete candidate or independent strict validation failed')
        require(sha(candidate)==package['zip_sha256']==validation['zip_sha256']
            and sha(OUTPUT/'predictions.jsonl')==package['predictions_sha256']==validation['predictions_sha256']
            and sha(OUTPUT/'provenance.jsonl')==validation['provenance_sha256'],'final serialized identity changed')
        with zipfile.ZipFile(candidate) as archive:
            require(archive.namelist()==['predictions.jsonl'] and archive.testzip() is None
                and hashlib.sha256(archive.read('predictions.jsonl')).hexdigest()==package['predictions_sha256'],
                'ZIP content/CRC identity failed')
        invoke('write_artifact_inventory.py','--directory','baseline_a_pts_v1/rematch_e2e_recovery_01',
            '--output','controller/rematch_e2e_recovery_01.inventory.json')
        result=checkpoint('PASS_COMPLETE_426_CANDIDATE_NOT_UPLOADED',candidate=str(candidate),
            candidate_sha256=sha(candidate),candidate_bytes=candidate.stat().st_size,
            predictions_sha256=sha(OUTPUT/'predictions.jsonl'),provenance_sha256=sha(OUTPUT/'provenance.jsonl'),
            selected_frames=package['prediction_frames'],videos=426,unchanged_successful_windows=516,
            recovered_failed_windows=5,original_run_remains_failed=True,space_resource_sha256=sha(space_resource),
            inventory_sha256=sha(CTRL/'rematch_e2e_recovery_01.inventory.json'),official_score=None)
    except Exception as exc:
        result=checkpoint('STOP_FORMAT_CONTINUATION',failure_type=type(exc).__name__,failure=str(exc),
            traceback=traceback.format_exc(),candidate_not_accepted=True)
    with completion.open('x') as handle:handle.write(json.dumps(result,indent=2)+'\n')
    raise SystemExit(0 if result['stage'].startswith('PASS_') else 1)
