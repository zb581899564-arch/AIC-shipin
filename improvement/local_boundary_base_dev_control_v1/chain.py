"""Exactly one BASE37 shared job followed by37 new output-only CPU replays."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

import cc_common as cc


def GPU_argv(capacity_reason):
    return [str(cc.PY), str(cc.RUN/'resource_unlimited_v1_20261007/gpu_run.py'),
        '--name', cc.NAME, '--max-seconds', str(cc.MAX_GPU_SECONDS),
        '--planned-output-bytes', str(cc.PLANNED_OUTPUT_BYTES), '--capacity-reason', capacity_reason,
        '--queue-seconds', '900', '--', str(cc.PY), '-B', '-u', str(cc.DRIVER_CODE/'driver.py'), 'infer', '--base', str(cc.BASE)]


def main(scope_path):
    cc.host(cpu=False)
    scope_path, scope = cc.scope(scope_path)
    cc.check_deadline(scope)
    cc.unique_job_absent()
    terminal = cc.time_terminal()
    cc.require(terminal is not None, 'BASE chain waits for TIME natural full execution and first37input replay')
    c, io = cc.driver_modules()
    bundle = io.admitted(cc.BASE)
    independent = cc.read(cc.BASE/'gpu_admission_independent_check_01.json')
    cc.require(independent['status'] == 'PASS_BASE37_METADATA_CLOSURE_AND_DRIVER_CONSUMER_NOT_GPU_COMPLETE' and
               independent['gpu_admission_sha256'] == cc.sha(cc.BASE/'gpu_admission.json') and
               independent['registration_sha256'] == cc.sha(cc.BASE/'registration_01.json') and
               independent['source_lock_sha256'] == cc.sha(cc.BASE/'source_lock.json') and
               independent['control_scope_sha256'] == cc.sha(scope_path) and
               independent['driver_code_files'] == io.own_code_files() and
               independent['controller_code_files'] == cc.own_code_files() and
               all(independent[k] == v for k, v in cc.COUNTS.items()), 'Independent BASE consuming gate missing/changed')
    out = cc.BASE/'chain_01'
    out.mkdir(exist_ok=False)
    cc.save(out/'launch_claim.json', dict(pid=os.getpid(), argv=sys.argv, utc=cc.utc(),
        parent_CUDA_VISIBLE_DEVICES=os.environ.get('CUDA_VISIBLE_DEVICES'),
        gpu_admission_sha256=cc.sha(cc.BASE/'gpu_admission.json'), control_scope_sha256=cc.sha(scope_path),
        actual_model_call_budget=37, **cc.COUNTS, old_inputs_and_TIME_replays_not_repeated=True))
    stage = 'resource'
    try:
        snapshot = cc.resource_snapshot()
        snapshot_path = out/'resource_before_unique_BASE_job.json'
        cc.save(snapshot_path, snapshot)
        source_resource = bundle['helpers']['io'].read(cc.RUN/'controller'/(
            cc.read(cc.TIME/'gpu_admission.json')['gpu_job_name']+'.resource.json'))
        prior_peaks = {k: v for k, v in source_resource.items() if 'peak' in k or 'charged' in k}
        reason = json.dumps(dict(scope='37 unchanged accepted native64 inputs, original20events plus3 original structural points',
            workload='same loaded physical8782459120; only TIME activation disabled; no new tensors/processor/media',
            actual_resource_snapshot_path=str(snapshot_path), actual_resource_snapshot_sha256=cc.sha(snapshot_path),
            actual_previous_TIME_resource=prior_peaks, current_GPU=snapshot['GPU'], current_GPU_processes=snapshot['GPU_processes'],
            current_available_RAM_bytes=snapshot['memory'].get('MemAvailable_bytes'), current_disk_free_bytes=snapshot['disk']['free_bytes'],
            registered_output_bytes=cc.PLANNED_OUTPUT_BYTES, shared_reservation_protects_foreign_GPU_jobs=True,
            CPU_child_threads=1, external_Java_not_interrupted=True, no_fixed_memory_or_GPU_GB_admission_line=True), separators=(',', ':'))
        commands = [('gpu', GPU_argv(reason), False),
                    ('replay', [str(cc.PY), '-B', '-u', str(cc.DRIVER_CODE/'driver.py'), 'replay', '--base', str(cc.BASE)], True)]
        for stage, argv, cpu in commands:
            cc.check_deadline(scope)
            env = cc.child_env(cpu)
            cc.save(out/(stage+'_command.json'), dict(argv=argv, child_CUDA_VISIBLE_DEVICES=env.get('CUDA_VISIBLE_DEVICES'), utc=cc.utc()))
            with (out/(stage+'.log')).open('x') as log:
                result = subprocess.run(argv, env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
            cc.save(out/(stage+'_exit.json'), dict(exit_code=result.returncode, utc=cc.utc()))
            if result.returncode:
                raise RuntimeError(stage+' failed; preserve calls/raw and do not retry')
            if stage == 'gpu':
                bundle['helpers']['io'].terminal_resource(cc.NAME)  # natural singleton ledger only
        gpu_path, replay_path = cc.BASE/'gpu_01/completion.json', cc.BASE/'replay_01/completion.json'
        gpu, replay = cc.read(gpu_path), cc.read(replay_path)
        exported = cc.read(cc.BASE/'boundary_prediction_export.json')
        cc.require(gpu['status'] == 'PASS_ALL_BASE_PAIRED_CALLS_NOT_QUALITY' and
                   gpu['actual_model_calls'] == gpu['requests'] == 37 and
                   replay['status'] == 'PASS_ALL_BASE_PAIRED_OUTPUT_REPLAYS_NOT_QUALITY' and replay['requests'] == 37 and
                   all(gpu[k] == replay[k] == exported[k] == v for k, v in cc.COUNTS.items()) and
                   exported['retained_events'] == 20 and exported['full_endpoint_results'] == 40 and
                   exported['actual_model_calls'] == exported['actual_independent_model_replays'] == 37 and
                   exported['structural_geometry_proof_count'] == 3 and exported['removed_events'] == exported['newly_created_events'] == 0,
                   'Complete BASE37 output/replay/full20event denominator failed')
        cc.save(out/'completion.json', dict(status='COMPLETE_REAL_DEV37_BASE_AND_NEW_OUTPUT_ONLY_CPU_REPLAY_NOT_QUALITY',
            gpu_completion_sha256=cc.sha(gpu_path), independent_output_replay_completion_sha256=cc.sha(replay_path),
            export_sha256=cc.sha(cc.BASE/'boundary_prediction_export.json'),
            paired_behavior_export_sha256=cc.sha(cc.BASE/'paired_behavior_export.json'),
            TIME_chain_completion=terminal, actual_model_calls=37, events=20, **cc.COUNTS,
            new_processor_encodes=0, new_media_decodes=0, optimizer_updates=0, new_ZIPs=0, SCI=False, utc=cc.utc()))
    except BaseException as error:
        cc.save(out/'failure.json', dict(stage=stage, error=repr(error), traceback=traceback.format_exc(),
            preserve_success_and_raw=True, successful_or_started_model_calls_must_not_repeat=True,
            no_automatic_retry=True, utc=cc.utc()))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--scope', required=True)
    main(parser.parse_args().scope)
