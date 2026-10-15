"""Bind real C7 completion to the frozen renderer; no risk admission or model."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess

R = Path('/home/inspur/aic_video_work/twenty_hour_five_20261014_v1')
C7 = R / 'temporal_global_recovery_control7_v1'
B = R / 'temporal_family_package_bootstrap_control7_v1'
W = R / 'cpu_finalization_control7_01'
ROOT = R / 'temporal_family_native_package_v3'
PY = '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'


def ref(path):
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def save(path, value):
    with path.open('x', encoding='utf8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.flush()
        os.fsync(f.fileno())


def main():
    assert socket.gethostname() == 'inspur-NP5570M5'
    done = json.loads((C7 / 'run_01/completion.json').read_text())
    assert done['status'] == 'PASS_CONTROL7_REMAINING_AGGREGATE_RECOVERY_NO_NEW_MODEL_OR_QA_NOT_QUALITY'
    assert all(type(done[k]) is int and done[k] == 0 for k in (
        'actual_new_model_calls_in_recovery', 'actual_first_QA_calls_in_recovery',
        'old_successful_operations_repeated'))
    assert not (W / 'binder').exists() and not (W / 'binder_wrapper_launch.json').exists()
    assert not (ROOT / 'technical_preparation_receipt.json').exists()
    old_template = R / 'temporal_family_package_bootstrap_control6_v2/config_template_01.json'
    config = json.loads(old_template.read_text())
    config['schema'] = 'TEMPORAL_FAMILY_PACKAGE_BOOTSTRAP_CONTROL7_V1'
    config['draft_status'] = 'ACTUAL_ALL_COMPLETIONS_BOUND_METADATA_ONLY_NO_RISK_ADMISSION'
    config['production_completion_ref'] = ref(C7 / 'exports_01/global_completion.json')
    config['controller_completion_ref'] = ref(C7 / 'run_01/completion.json')
    for name in ('authorization', 'official_rule_check'):
        config['package_document_refs'][name] = ref(ROOT / (name + '.json'))
    assert config['package_document_refs']['official_rule_check']['sha256'] == '7450752081c20971616444c43c21e57d44cf09d552ef5247c9c97d9e7eb9df68'
    config['required_binder_code_files'] = {
        str(p): ref(p)['sha256'] for p in sorted((B / 'code').glob('*.py'))}
    assert len(config['required_binder_code_files']) == 4
    assert config['required_binder_code_files'][str(B / 'code/bind.py')] == '13a2148ce2741158f73a2ffb1a6807c3e90be63cfc3efaed2b63d664cfeeb93b'
    config['additional_metadata_refs'] += [ref(p) for p in (
        C7 / 'registration.json', C7 / 'main_execution_admission.json',
        C7 / 'chain_launch.json', C7 / 'run_01/aggregate_natural_terminal.json',
        R / 'actual_global_aggregate_identity_diagnosis_01.json', W / 'registration.json',
        B / 'configurator_01.py')]
    config['_pending_fields'] = []
    config['_pending_root_deployment'] = []
    config['_current_template_is_not_permission_or_PASS'] = False
    config['_old_template_exact_reference'] = ref(old_template)
    config['_actual_new_global_recovery_without_model_or_QA'] = dict(
        registration_ref=ref(C7 / 'registration.json'), old_C6_failure_preserved=True,
        model_calls=0, first_QA_calls=0, scientific_quality_claim=False)
    config['_root_auto_fill_only_after_real_natural_terminal']['production_completion_ref.sha256']['path'] = str(C7 / 'exports_01/global_completion.json')
    config['_root_auto_fill_only_after_real_natural_terminal']['controller_completion_ref.sha256'].update(
        path=str(C7 / 'run_01/completion.json'), required_status=done['status'])
    save(B / 'config_01.json', config)
    argv = [PY, '-B', '-u', str(W / 'run_once_01.py'), '--stage', 'binder']
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1')
    with (W / 'binder_wrapper.log').open('xb') as log:
        child = subprocess.Popen(argv, cwd=R, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    ticks = int((Path('/proc') / str(child.pid) / 'stat').read_text().rsplit(')', 1)[1].split()[19])
    launch = dict(pid=child.pid, start_ticks=ticks, argv=argv,
                  config_ref=ref(B / 'config_01.json'), UTC=dt.datetime.now(dt.timezone.utc).isoformat())
    save(W / 'binder_wrapper_launch.json', launch)
    print(json.dumps(launch))


if __name__ == '__main__':
    main()
