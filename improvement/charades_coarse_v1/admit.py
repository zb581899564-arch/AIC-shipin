"""Freeze actual Charades CPU inputs before one original-B coarse job."""
import argparse
import datetime as dt
import os
from pathlib import Path
import shutil
import subprocess
import sys
import coarse as c


def run(root):
    native = c.CAMPAIGN/'charades_boundary_v2'
    complete = c.read(native/'native_chain_01/completion.json')
    c.require(complete['status'] == 'PASS_V2_NATIVE_CPU_INPUTS_PENDING_MAIN_INDEPENDENT_GPU_ADMISSION', 'Incomplete native chain')
    c.require((complete['sources'], complete['dev'], complete['confirm']) == (21, 11, 10), 'Frozen source roles changed')
    c.require(c.sha(complete['effective_registry_path']) == complete['effective_registry_sha256'], 'Actual registry changed')
    manifest = c.read(native/'coarse_inputs_01.json')
    rows = manifest['rows']
    c.require(manifest['status'] == 'PASS_V2_NATIVE64_COARSE_INPUTS_NOT_GPU_ADMISSION', 'Invalid input manifest')
    c.require(len(rows) == 38 and len({r['case_id'] for r in rows}) == 38 and len({r['source_id'] for r in rows}) == 21, 'Real 21/38 input denominator')
    isolation = c.read(native/'source_isolation_receipt_02.json')
    c.require(isolation['status'].startswith('PASS') and isolation.get('new_model_calls', 0) == 0, 'Known identity/byte isolation receipt missing')
    c.save(root/'coarse_inputs.json', rows)
    frozen = {}
    def add(path, expected=None):
        path = Path(path).resolve()
        c.require(path.is_relative_to(c.ROOT) and path.is_file(), 'Invalid frozen dependency')
        digest = c.sha(path)
        c.require(expected is None or digest == expected, 'Evidence changed '+str(path))
        frozen[str(path)] = digest
    for path in root.glob('*.py'):
        add(path)
    for name in ['coarse_inputs.json', 'protocol.json', 'official_rule_check.json', 'event_extraction_rule.json']:
        add(root/name)
    for name in ['registration_01.json', 'native_chain_01/completion.json', 'coarse_inputs_01.json',
                 'effective_source_registry_02.json', 'input_manifest_fact_review_01.json', 'source_isolation_receipt_02.json']:
        add(native/name)
    config_path = c.RUN/'b_score_aligned_package_v4/config.json'
    config = c.read(config_path)
    add(config_path)
    for directory in (c.RUN/'b_score_aligned_package_v4', c.ROOT/'temporal_refinement_pilot_20261011/dev_01', c.CAMPAIGN/'local_boundary_v1/code'):
        for path in directory.glob('*.py'):
            add(path)
    add(c.RUN/'temporal_sft8b_v1/sft_contract.py')
    add(c.RUN/'b_score_aligned_package_v4/constrained_json.py')
    for path in Path(config['model_dir']).iterdir():
        if path.is_file() and path.suffix in ('.json', '.txt', '.jinja'):
            add(path)
    for row in rows:
        add(row['proof_path'], row['proof_sha256'])
        add(row['input_path'], row['input_sha256'])
        add(row['CPU_completion_path'], row['CPU_completion_sha256'])
        cpu, meta = c.read(row['proof_path']), c.read(row['input_path'])
        c.require(meta['reference_available_to_inference'] is False and meta['audio_observed'] is False, 'GT/audio entered input')
        add(meta['frame_array_path'], meta['frame_array_sha256'])
        add(cpu['encoded_tensor_path'], cpu['encoded_tensor_sha256'])
        for path, digest in cpu['input_evidence'].get('runtime_files', {}).items():
            add(path, digest)
    # Clock and media provenance are already bound to actual native/CPU proofs.
    # No label body, RGB decode, processor encode or tensor load occurs here.
    for source in complete['accepted']:
        preparation = source['preparation']
        add(preparation['native_clock_path'], preparation['native_clock_sha256'])
        add(source['media_receipt_path'], source['media_receipt_sha256'])
    c.save(root/'source_input_lock.json', dict(status='FROZEN_CHARADES21_REAL38_CPU_COARSE_INPUT_CODE_LOCK', files=frozen))
    snapshot = dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        actual_processes=subprocess.check_output(['ps', '-eo', 'pid,ppid,etimes,%cpu,rss,args'], text=True),
        gpu=subprocess.check_output(['nvidia-smi', '--query-gpu=index,name,memory.used,memory.total,utilization.gpu', '--format=csv,noheader'], text=True),
        memory=subprocess.check_output(['free', '-b'], text=True), disk_free_bytes=shutil.disk_usage(root).free,
        resource_reason='Same original B measured peak 22414MiB; current GPU context only 182MiB, no external GPU compute. New outputs only; existing accepted inputs remain. Independent CPU replay serial one thread, Java peer untouched.')
    c.save(root/'resource_snapshot_before_job.json', snapshot)
    c.save(root/'gpu_admission.json', dict(status='PASS_INDEPENDENT_CHARADES_REAL_CPU_COARSE_ADMISSION',
        deadline='2026-10-14T11:56:40Z', gpu_job_name='aic20h_charades21_original_b_coarse38_20261014_v1',
        model_parameters=8782459120, optimizer_updates=0, actual_model_call_budget=len(rows),
        reference_available_to_inference=False, source_input_lock_sha256=c.sha(root/'source_input_lock.json'),
        partial_action_reference_is_highlight_GT=False, resource_snapshot_sha256=c.sha(root/'resource_snapshot_before_job.json'),
        new_input_prepare_calls=0, future_independent_CPU_replays=38))
    admission, actual = c.accepted_inputs(root)
    c.require(len(actual) == 38, 'Independent consumer input admission failed')
    c.save(root/'independent_admission_completion.json', dict(status='PASS_INDEPENDENT_REAL38_INPUT_AND_CONSUMER_CONTRACT_NOT_MODEL_OR_QUALITY',
        inputs=38, sources=21, admission_sha256=c.sha(root/'gpu_admission.json'), source_input_lock_sha256=c.sha(root/'source_input_lock.json'),
        new_media_decodes=0, new_processor_encodes=0, new_model_calls=0))
    print('PASS_REAL38_INPUTS_NO_MODEL', flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--root', required=True)
    root = c.checked_base(p.parse_args().root)
    try:
        run(root)
    except BaseException as error:
        c.save(root/'admission_failure.json', dict(error=repr(error), preserve_all_success=True))
        raise
