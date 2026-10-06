"""Supervisor admission for eight CFR non-test sources on final A-PTS revision03.

Native synthetic decoder acceptance is separately required before rematch.
"""
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path('/home/inspur/aic_video_work')
RUN = ROOT/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
CTRL, CODE = RUN/'controller', RUN/'baseline_a_pts_v1'
EXPECTED_LOCK = '94938aca8c47ad02068bebe9c8bfdb34e3219872bfe83d418fb3f48fc55eb0ee'
EXPECTED_PROCESSOR = '95bfc9b104819dc3851317fb053ef27e654389f136b438cf348262894cedfe9b'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text())

if __name__ == '__main__':
    sys.path.insert(0, str(CODE))
    from pts_contract import load_clocks, legacy_manifest
    from run_pts import verify_vendor
    if sha(CODE/'source_lock.json') != EXPECTED_LOCK:
        raise RuntimeError('final admitted source snapshot changed')
    verify_vendor()
    receipt = read(RUN/'baseline_pts_v4/nontest_registry_01/reaudit_receipt.json')
    if (receipt['status'] != 'PASS_ALL_SOURCE_CLOCK_BRANCHES_METADATA_ONLY'
        or receipt['expected_count'] != 8 or receipt['cfr_eligible_sources'] != 8
        or receipt['native_non_cfr_usable_sources'] != 0 or receipt['failed_video_ids']):
        raise RuntimeError('the eight-source CFR-only non-test denominator changed')
    manifest_path, registry_path = Path(receipt['clean_manifest']['path']), Path(receipt['clock_registry']['path'])
    if sha(manifest_path) != receipt['clean_manifest']['sha256']:
        raise RuntimeError('bound non-test manifest changed')
    manifest = read(manifest_path)
    clocks = load_clocks(manifest, registry_path, receipt['clock_registry']['sha256'])
    original = RUN/'baseline_a/inputs/non_test_frozen8.json'
    if sha(original) != '7b3e187451eb15f80647b4441a4a41f030f4be1438a95ef5b7982a53554f153a':
        raise RuntimeError('frozen non-test input changed')
    if legacy_manifest(manifest)['records'] != read(original)['records']:
        raise RuntimeError('non-test records or scopes changed')
    processor_path = CODE/'real_processor_02/processor_receipt.json'
    processor = read(processor_path)
    if (sha(processor_path) != EXPECTED_PROCESSOR or processor['status'] != 'PASS_ACTUAL_PROCESSOR_SYNTHETIC_ONLY'
        or processor['source_lock_sha256'] != EXPECTED_LOCK or not all(r['pass'] for r in processor['records'])
        or processor['models_run'] is not False or processor['GPU_used'] is not False
        or processor['contest_media_read'] is not False):
        raise RuntimeError('actual processor receipt not accepted')
    work = int(subprocess.check_output(['du','-s','-B1',str(ROOT)],text=True).split()[0])
    free = shutil.disk_usage(ROOT).free
    policy = read(ROOT/'resource_policy.json')
    planned = 268435456
    compute = subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,used_memory','--format=csv,noheader'],text=True).strip()
    if compute or (ROOT/'improvement_round1/active_gpu_job.json').exists():
        raise RuntimeError('defer until shared GPU is available')
    if work+planned > policy['added_disk_budget_gib']*2**30 or free < planned:
        raise RuntimeError('capacity does not cover predicted non-test outputs')
    data = {'variant':'A_NATIVE_PTS_COMPAT_V1','stage':'A_PTS_NONTEST_E2E','authorized':True,
        'admitted_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'user_authorization':'2026-10-05 execute the discussed plan and prepare Linux training',
        'scope':'NONTEST_ALL_STAGES','allowed_stages':['preflight','temporal','select','shots','anchors','spatial','compose','package'],
        'space_inference_admitted':True,'budget_runner_required':True,
        'manifest_path':str(manifest_path),'manifest_sha256':sha(manifest_path),
        'clock_registry_path':str(registry_path),'clock_registry_sha256':sha(registry_path),
        'source_lock_sha256':EXPECTED_LOCK,'processor_evidence_sha256':EXPECTED_PROCESSOR,
        'run_dir':str(CODE/'nontest_e2e_01'),'resource_preflight_pass':True,
        'shared_gpu_queue_approved':True,'disk_peak_within_80gib':True,
        'planned_output_bytes':planned,'single_job_max_seconds':1800,
        'capacity_reason':'same frozen eight CFR non-test sources; prior actual 396 selected frames and 68 anchors, new JSONL and ZIP only',
        'live_resources':{'work_bytes':work,'free_bytes':free,'compute':compute},
        'native_branch_model_inference_admitted':False,'formal_C_training_admitted':False,
        'competition_upload_authorized':False,
        'data_use_basis':'previously authorized non-test engineering slice; no new dataset or raw-media publication'}
    with (CTRL/'a_pts_nontest_01.admission.json').open('x') as stream:
        json.dump(data, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'stage':data['stage'],'sources':len(clocks),'scope':data['scope'],
                      'native_branch_model_inference_admitted':False,'competition_upload_authorized':False}))
