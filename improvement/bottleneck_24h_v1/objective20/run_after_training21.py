"""Finite dependency chain for the already launched objective20 training.

Never launches/resumes training. One final-model43 job, new comparison, then stop.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import traceback

W = Path('/home/inspur/aic_video_work')
P = W/'bottleneck_24h_20261019_v1'
R = P/'summary_objective_v20'
RUN = W/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
PY = str(W/'env/qwen3vl_isolated_20260910/bin/python')


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def ref(path):
    path = Path(path).resolve(strict=True)
    return dict(path=str(path), bytes=path.stat().st_size, sha256=sha(path))


def bound(reference):
    path = Path(reference['path']).resolve(strict=True)
    assert path.is_relative_to(W) and path.is_file() and sha(path) == reference['sha256']
    return path


def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.flush(); os.fsync(stream.fileno())


def event(stage, **values):
    with (R/'after_training_sequence_21.jsonl').open('a') as stream:
        stream.write(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(), stage=stage,
                                    **values), allow_nan=False)+'\n')
        stream.flush(); os.fsync(stream.fileno())


def resource_terminal(job):
    path = RUN/'controller'/(job+'.resource.json')
    if not path.exists():
        return None
    terminal = read(path)
    ledger = [json.loads(line) for line in (W/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
              if line.strip() and json.loads(line).get('name') == job]
    if ledger != [terminal]:
        return None  # Atomic resource/ledger publication may still be in flight.
    return terminal, ref(path)


def wait_existing_training(reg):
    launch = read(bound(reg['already_launched_training_ref']))
    started = read(bound(reg['already_started_training_ref']))
    expected = launch['command']; missing = 0
    event('WAIT_ALREADY_LEGAL_TRAINING_NO_RESTART', job=reg['training_job'])
    while True:
        terminal = resource_terminal(reg['training_job'])
        if terminal is not None:
            value, reference = terminal
            assert value['status'] == 'completed' and value['exit_code'] == 0, 'Actual training failed; no automatic recovery'
            return reference
        proc = Path('/proc')/str(started['pid'])
        try:
            argv = (proc/'cmdline').read_bytes().decode().strip('\0').split('\0')
            ticks = int((proc/'stat').read_text().rsplit(') ',1)[1].split()[19])
            live = argv == expected and ticks == started['start_ticks']
        except (FileNotFoundError, ProcessLookupError):
            live = False
        missing = 0 if live else missing+1
        assert missing < 4, 'Exact registered wrapper missing and no authoritative terminal after publication settling; preserve and stop'
        # Observation waits never relaunch a model, transform failure to empty,
        # or decide that a live process failed because training is taking time.
        time.sleep(30)


def cpu(stage, script, args=()):
    event('BEGIN_'+stage)
    with (R/(stage+'.log')).open('xb') as log:
        proc = subprocess.run([PY, '-B', str(script), *map(str,args)], stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1'))
    save(R/(stage+'_terminal.json'), dict(exit_code=proc.returncode, automatic_retry=False,
         utc=datetime.now(timezone.utc).isoformat()))
    assert proc.returncode == 0, stage+' CPU failure; preserve all successes and stop'
    event('COMPLETE_'+stage)


def main():
    assert os.uname().nodename == 'inspur-NP5570M5'
    assert os.environ.get('CUDA_VISIBLE_DEVICES') not in (None, ''), 'Parent retains actual CUDA; CPU children only mask themselves'
    reg = read(R/'after_training_registration_21.json')
    for name, reference in reg['code'].items():
        assert bound(reference) == Path(__file__).resolve().parent/name
    bound(reg['generation_registration_ref'])
    assert read(bound(reg['scientific_repair_registration_ref']))['only_loss_reduction_changed'] is True
    save(R/'after_training_claim_21.json', dict(pid=os.getpid(),
        start_ticks=int(Path('/proc/self/stat').read_text().rsplit(') ',1)[1].split()[19]),
        registration_ref=ref(R/'after_training_registration_21.json'), automatic_retry=False,
        training_launch_or_resume=False, automatic_production_or_package=False))
    train_resource = wait_existing_training(reg)
    cpu('first_final_training_QA_21', bound(reg['code']['final_training_qa.py']))
    complete = read(R/'summary_model_20/full_completion.json')
    assert complete['status'] == 'PASS_SUMMARY_FINAL559_SINGLE_EPOCH'
    assert complete['completed_updates'] == 559 and complete['successful_micro'] == 2236
    bound(complete['adapter_weights_ref'])
    save(R/'summary_final_weights_frozen_10.json', dict(status='FINAL559_WEIGHTS_FROZEN_BEFORE_DEV_METRICS',
        scientific_version=20, final_adapter_ref=complete['adapter_weights_ref'],
        training_completion_ref=ref(R/'summary_model_20/full_completion.json'), resource_ref=train_resource,
        first_independent_training_acceptance_ref=ref(R/'first_final_training_acceptance_21.json'),
        original_recipe_final_only=True, new_dev_metrics_read=False, utc=datetime.now(timezone.utc).isoformat()))
    assert datetime.now(timezone.utc) < datetime(2026,10,19,11,52,37,tzinfo=timezone.utc), 'Original20h new-model cutoff'
    gen = read(bound(reg['generation_registration_ref'])); job = gen['job_names']['TRAINED']
    assert resource_terminal(job) is None and not (RUN/'controller'/(job+'.resource.json')).exists()
    assert not any(json.loads(line).get('name') == job for line in (W/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip())
    current = dict(host=os.uname().nodename, load=os.getloadavg(), disk_free=shutil.disk_usage(W).free,
        mem_available=int(next(line for line in Path('/proc/meminfo').read_text().splitlines()
                              if line.startswith('MemAvailable:')).split()[1])*1024,
        gpu=subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used,memory.total,utilization.gpu','--format=csv,noheader'],text=True).strip(),
        gpu_apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True).strip())
    assert current['host'] == 'inspur-NP5570M5' and not current['gpu_apps'], 'External job appeared; do not interfere or launch'
    assert current['disk_free'] > reg['generation_planned_output_bytes']
    assert current['mem_available'] > reg['generation_host_working_estimate'], 'Actual declared working set does not fit'
    command = [PY, str(bound(reg['gpu_wrapper_ref'])), '--name', job,
        '--max-seconds','1200','--planned-output-bytes',str(reg['generation_planned_output_bytes']),
        '--capacity-reason','One fixed-loss20 final559 on same accepted43 inputs; no oldINIT/replay, new-data or media. '
        'Actual frozen model and first state QA passed. '+json.dumps(current), '--queue-seconds','120', '--',
        PY, '-B', str(bound(reg['code']['summary_generate.py'])), '--role','TRAINED']
    save(R/'trained43_gpu_launch_21.json', dict(command=command, current_resources=current,
        actual_input_acceptance_ref=gen['first_dev_input_acceptance_ref'], frozen_weights_ref=ref(R/'summary_final_weights_frozen_10.json'),
        utc=datetime.now(timezone.utc).isoformat()))
    event('BEGIN_NEW_TRAINED43_ONLY', job=job)
    with (R/'trained43_gpu_wrapper_21.log').open('xb') as log:
        proc = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES=current['gpu'].split(',')[0].strip(), PYTHONDONTWRITEBYTECODE='1'))
    assert proc.returncode == 0, 'New43 actual wrapper failure; preserve every raw and no retry'
    terminal = resource_terminal(job); assert terminal is not None
    value, gen_resource = terminal
    assert value['status'] == 'completed' and value['exit_code'] == 0
    cpu('first_TRAINED43_output_QA_21', bound(reg['code']['summary_output_qa.py']), ['--role','TRAINED'])
    old = read(bound(reg['adopted_previous_evaluation_ref']))
    manifest = dict(dev_prepared_ref=old['dev_prepared_ref'],
        baseline_human_adoption_ref=old['baseline_human_adoption_ref'],
        adopted_previous_evaluation_ref=reg['adopted_previous_evaluation_ref'],
        final_adapter_ref=complete['adapter_weights_ref'], frozen_selection_ref=ref(R/'summary_final_weights_frozen_10.json'),
        trained_resource_ref=gen_resource,
        trained_output_QA_ref=ref(R/'summary_generation_10/TRAINED/first_independent_output_QA.json'))
    save(R/'comparison_manifest_21.json', manifest)
    cpu('fixed_comparison_21', bound(reg['code']['evaluate_loss20.py']), ['--manifest', R/'comparison_manifest_21.json'])
    save(R/'after_training_completion_21.json', dict(status='COMPLETE_LOSS_ONLY20_NEW43_COMPARISON_REQUIRES_MAIN_REVIEW',
        result_ref=ref(R/'evaluation_20/result.json'), training_resource_ref=train_resource,
        generation_resource_ref=gen_resource, old_INIT_or_control_metrics_repeated=False,
        automatic_production=False, automatic_package=False, official_improvement_asserted=False,
        utc=datetime.now(timezone.utc).isoformat()))


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        failure = R/'after_training_failure_21.json'
        if not failure.exists():
            save(failure, dict(error=repr(error), traceback=traceback.format_exc(), automatic_retry=False,
                all_successes_preserved=True, production_or_package=False,
                utc=datetime.now(timezone.utc).isoformat()))
        raise
