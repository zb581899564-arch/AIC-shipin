"""Main registers the unchanged B smoke after the corrected complete A package."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path('/home/inspur/aic_video_work')
RUN = ROOT/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
CTRL = RUN/'controller'
HERE = RUN/'temporal_sft8b_v1'
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):
    return json.loads(Path(path).read_text())
def require(ok, message):
    if not ok:
        raise RuntimeError(message)

if __name__ == '__main__':
    lock_path = HERE/'smoke_source_lock.json'
    require(sha(lock_path) == '806deb54de18835ee6841a1a921f015cd0d8b82ad65268e016af3144cb19ff93', 'B recipe lock changed')
    lock = read(lock_path)
    for name, digest in lock['files'].items():
        require(sha(HERE/name) == digest, 'B recipe input/code changed: '+name)
    completion_path = RUN/'spatial_identity_recovery_v1/recover_01/recovery_completion.json'
    complete = read(completion_path)
    require(complete['status'] == 'PASS_COMPLETE_426_CANDIDATE_NOT_UPLOADED' and
            complete['videos'] == 426 and complete['frames'] == 93155 and complete['anchors'] == 13022 and
            complete['unchanged_successful_spatial_lines_byte_identical'] is True and
            complete['silent_fallbacks'] == 0, 'corrected A candidate not accepted')
    require(sha(complete['candidate']) == complete['candidate_sha256'], 'accepted candidate bytes changed')
    resource = read(CTRL/'rematch_spatial_identity_02.resource.json')
    require(resource['status'] == 'completed' and resource['exit_code'] == 0, 'owned recovery job not completed')
    compute = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,used_memory', '--format=csv,noheader'], text=True).strip()
    require(not compute and not (ROOT/'improvement_round1/active_gpu_job.json').exists(), 'live shared resource conflict; untouched')
    config_path = HERE/'smoke_config_PREPARED_NOT_ADMITTED.json'
    config = read(config_path)
    planned = 15335424*4*2+config['updates']*config['grad_accum']*config['max_sequence_length']*32+33554432
    work = int(subprocess.check_output(['du', '-s', '-B1', str(ROOT)], text=True).split()[0])
    free = shutil.disk_usage(ROOT).free
    require(work+planned <= read(ROOT/'resource_policy.json')['added_disk_budget_gib']*2**30 and free >= planned,
            'capacity cannot cover the registered SFT adapter/evidence plan')
    authority_path = HERE/'training_authorization_B_SMOKE.json'
    admission = dict(schema='aic_temporal_sft8b_admission_v1', scope='TEMPORAL_8B_SFT_SMOKE_NONTEST', authorized=True,
        registered_route='TEMPORAL_8B_INTERVAL_SFT', training_authorized_by_user=True,
        training_authorization_evidence=dict(path=str(authority_path), sha256=sha(authority_path)),
        config_sha256=sha(config_path), train_manifest_sha256=config['train_manifest']['sha256'],
        r7_train_registry_sha256=config['r7_train_registry']['sha256'], model_receipt_sha256=config['model_receipt']['sha256'],
        source_code_sha256={name: sha(HERE/name) for name in ['train_sft.py', 'sft_contract.py']},
        resource_preflight_pass=True, shared_gpu_queue_approved=True, disk_peak_within_80gib=True,
        budget_runner_required=True, formal_c_bce_admitted=False,
        A_completed_evidence_sha256=sha(completion_path), planned_output_bytes=planned,
        live_resource=dict(work_bytes=work, free_bytes=free), main_registration_entry_sha256=sha(__file__),
        previous_queue_completion_sha256=sha(CTRL/'sft8b_queue_completion.json'),
        previous_queue_failure_preserved=True, unchanged_B_smoke_recipe=True)
    admission_path = CTRL/'sft8b_smoke_02.admission.json'
    with admission_path.open('x') as stream:
        stream.write(json.dumps(admission, indent=2)+'\n')
    subprocess.run([sys.executable, '-B', str(HERE/'train_sft.py'), '--config', str(config_path),
                    '--admission', str(admission_path), '--check-only'], check=True, timeout=300)
    print(json.dumps({'status': 'REGISTERED_AND_STDLIB_BYTE_CONTRACT_PASSED', 'admission': str(admission_path),
                      'admission_sha256': sha(admission_path), 'planned_output_bytes': planned, 'training_started': False}), flush=True)
