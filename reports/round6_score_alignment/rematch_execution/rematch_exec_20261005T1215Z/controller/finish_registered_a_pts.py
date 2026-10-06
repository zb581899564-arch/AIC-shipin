"""Finish the already authorized A-PTS machine work behind existing gates.

This is one bounded background continuation, not a recurring scheduler. It
does not upload, train C, change configuration, retry model failures, or kill
any process. Scientific/resource refusal ends the pipeline with evidence.
"""
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

ROOT = Path('/home/inspur/aic_video_work')
RUN = ROOT/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
CTRL, CODE = RUN/'controller', RUN/'baseline_a_pts_v1'
OUTPUT = CODE/'rematch_e2e_01'
LOCK = '86fc0da7cf631a2afe33c54fb5b66246bba88adfd95c1d8ce80ccbf73522d70d'

def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1<<20),b''):
            digest.update(block)
    return digest.hexdigest()

def read(path):
    return json.loads(Path(path).read_text())

def require(ok,message):
    if not ok:
        raise RuntimeError(message)

def checkpoint(stage,**extra):
    record = dict(stage=stage,checked_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        pid=os.getpid(),source_lock_sha256=LOCK,formal_C_training_admitted=False,
        competition_upload_authorized=False,**extra)
    path = CTRL/'a_pts_pipeline_latest.json'
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(record,indent=2)+'\n')
    temporary.replace(path)
    print(json.dumps(record),flush=True)
    return record

def invoke(script,*arguments):
    result = subprocess.run([sys.executable,'-B',str(CTRL/script),*arguments],
        cwd=RUN,capture_output=True,text=True,timeout=180)
    print(result.stdout,flush=True)
    if result.stderr:
        print(result.stderr,flush=True)
    require(result.returncode == 0,'continuation step refused: '+script)

def wait_resource(name,admission,extra_seconds=180):
    started = dt.datetime.fromisoformat(read(CTRL/(name+'.launch.json'))['started_utc'])
    deadline = started.timestamp()+admission['single_job_max_seconds']+1800+extra_seconds
    path = CTRL/('rematch_'+name+'.resource.json')
    while not path.exists():
        require(time.time() < deadline,'missing shared-runner receipt after the bounded job window')
        time.sleep(15)
    result = read(path)
    require(result['status'] == 'completed' and result['exit_code'] == 0
        and result['stop_reason'] is None,'owned job did not complete successfully: '+name)
    return path,result

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--helpers-sha256',required=True)
    args = parser.parse_args()
    completion = CTRL/'a_pts_pipeline_completion.json'
    try:
        require(not completion.exists(),'completion already recorded; never overwrite or rerun')
        helpers_path = CTRL/'background_pipeline_helpers.json'
        require(sha(helpers_path) == args.helpers_sha256,'registered continuation helper inventory changed')
        helpers = read(helpers_path)
        def verify_helpers():
            for name,digest in helpers['files'].items():
                require(sha(CTRL/name) == digest,'continuation helper changed: '+name)
            require(sha(CODE/'source_lock.json') == LOCK,'A-PTS production snapshot changed')
        verify_helpers()
        authorization = read(CTRL/'authorization.json')
        require(authorization['competition_upload_authorized'] is False
            and 'complete rematch baseline generation after input contract and regression' in authorization['scope'],
            'current user authorization does not include baseline generation')
        temporal_admission = read(CTRL/'a_pts_temporal_01.admission.json')
        require(temporal_admission['source_lock_sha256'] == LOCK
            and temporal_admission['scope'] == 'REMATCH_TEMPORAL_SCHEDULING'
            and temporal_admission['space_inference_admitted'] is False,'wrong temporal admission')
        checkpoint('WAITING_REGISTERED_TEMPORAL_AND_CPU_SCHEDULING')
        temporal_resource_path,temporal_resource = wait_resource('a_pts_temporal_01',temporal_admission)
        verify_helpers()
        require(read(OUTPUT/'temporal.stage.json')['status'] == 'PASS_TEMPORAL_EXECUTION'
            and read(OUTPUT/'temporal.stage.json')['videos'] == 426
            and read(OUTPUT/'temporal.stage.json')['windows'] == 521
            and read(OUTPUT/'temporal.stage.json')['invalid_windows'] == 0,'complete temporal denominator failed')
        # Wait only for a resource conflict, before creating an admission.
        # Model, identity, capacity or evidence failures never get blind retries.
        checkpoint('WAITING_LIVE_SHARED_RESOURCE_FOR_SPACE',
            temporal_resource_sha256=sha(temporal_resource_path))
        queue_deadline = time.monotonic()+1800
        while True:
            compute = subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,used_memory',
                '--format=csv,noheader'],text=True).strip()
            if not compute and not (ROOT/'improvement_round1/active_gpu_job.json').exists():
                break
            require(time.monotonic() < queue_deadline,'shared GPU remains occupied; leave external tasks untouched')
            time.sleep(15)
        verify_helpers()
        invoke('admit_a_pts_stage.py','space','--expected-source-lock',LOCK,
            '--processor-name','real_processor_04','--decoder-name','real_decoder_02')
        space_admission_path = CTRL/'a_pts_space_01.admission.json'
        space_admission = read(space_admission_path)
        checkpoint('SPACE_COMPOSE_PACKAGE_ADMITTED',
            actual_scheduling=space_admission['scheduling'],
            single_job_max_seconds=space_admission['single_job_max_seconds'],
            planned_output_bytes=space_admission['planned_output_bytes'])
        verify_helpers()
        invoke('launch_registered_a_pts_v2.py','a_pts_space_01')
        checkpoint('WAITING_REGISTERED_SPACE_COMPOSE_PACKAGE')
        space_resource_path,space_resource = wait_resource('a_pts_space_01',space_admission)
        verify_helpers()
        package = read(OUTPUT/'package.stage.json')
        validation = read(OUTPUT/'independent_validation.json')
        candidate = OUTPUT/'candidate_A_PTS.zip'
        require(package['status'] == 'PASS_FORMAT_PROVENANCE_PACKAGE_NOT_OFFICIALLY_SCORED'
            and package['source_lock_sha256'] == LOCK and package['video_records'] == 426
            and not package['issues'] and package['weak_roi_inputs_used'] == 0
            and package['old_test_boxes_used'] == 0 and package['silent_fallbacks'] == 0
            and validation['status'] == 'PASS_INDEPENDENT_STRICT_VALIDATION'
            and all(validation['checks'].values()) and validation['video_records'] == 426
            and validation['missing'] == validation['extra'] == validation['duplicate_frames'] == 0,
            'final candidate integrity or complete denominator failed')
        require(sha(candidate) == package['zip_sha256'] == validation['zip_sha256']
            and sha(OUTPUT/'predictions.jsonl') == package['predictions_sha256'] == validation['predictions_sha256']
            and sha(OUTPUT/'provenance.jsonl') == validation['provenance_sha256'],
            'final serialized candidate changed after independent validation')
        with zipfile.ZipFile(candidate) as archive:
            require(archive.namelist() == ['predictions.jsonl'] and archive.testzip() is None
                and hashlib.sha256(archive.read('predictions.jsonl')).hexdigest() == package['predictions_sha256'],
                'final ZIP identity/content failed')
        invoke('write_artifact_inventory.py','--directory','baseline_a_pts_v1/rematch_e2e_01',
            '--output','controller/rematch_e2e_01.inventory.json')
        result = checkpoint('PASS_COMPLETE_426_CANDIDATE_NOT_UPLOADED',candidate=str(candidate),
            candidate_sha256=sha(candidate),candidate_bytes=candidate.stat().st_size,
            predictions_sha256=sha(OUTPUT/'predictions.jsonl'),
            provenance_sha256=sha(OUTPUT/'provenance.jsonl'),
            selected_frames=package['prediction_frames'],videos=426,
            space_resource_sha256=sha(space_resource_path),
            inventory_sha256=sha(CTRL/'rematch_e2e_01.inventory.json'),official_score=None)
    except Exception as exc:
        result = checkpoint('STOP_BACKGROUND_CONTINUATION',failure_type=type(exc).__name__,
            failure=str(exc),traceback=traceback.format_exc(),candidate_not_accepted=True)
    with completion.open('x') as stream:
        json.dump(result,stream,indent=2)
        stream.write('\n')
    raise SystemExit(0 if result['stage'].startswith('PASS_') else 1)
