"""Once-only Linux teacher -> reviewed labels -> T training -> one local ZIP."""
from autopilot_common import *
import argparse
import fcntl
import math
import shutil
import socket
import subprocess
import sys
import time
import traceback


def gpu(name, command, maximum, planned, explanation):
    verify()
    runner = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'
    progress('RUNNING_' + name.upper(), maximum_seconds=maximum, planned_output_bytes=planned)
    with (HERE / (name + '.wrapper.log')).open('x') as log:
        result = subprocess.run([str(PY), '-B', str(runner), '--name', 'rematch_TAUTO_v3_' + name,
              '--max-seconds', str(maximum), '--planned-output-bytes', str(planned),
              '--capacity-reason', explanation, '--queue-seconds', str(3 * 86400), '--',
              str(PY), '-B', *map(str, command)], stdin=subprocess.DEVNULL,
              stdout=log, stderr=subprocess.STDOUT, cwd=RUN)
    receipt = RUN / 'controller' / ('rematch_TAUTO_v3_' + name + '.resource.json')
    require(result.returncode == 0 and receipt.is_file() and read(receipt)['status'] == 'completed',
            'GPU stage did not complete: ' + name)
    return read(receipt)


def cpu(name, command, maximum):
    verify()
    progress('RUNNING_' + name.upper())
    with (HERE / (name + '.cpu.log')).open('x') as log:
        result = subprocess.run([str(PY), '-B', *map(str, command)], stdin=subprocess.DEVNULL,
              stdout=log, stderr=subprocess.STDOUT, cwd=RUN, timeout=maximum)
    require(result.returncode == 0, 'CPU stage did not complete: ' + name)


def wait_dependencies(config):
    start = time.monotonic()
    download = RUN / 'teacher32b_linux_download_v1/completion.json'
    runtime = RUN / 'teacher32b_runtime_v2/runtime_build_completion.json'
    z = RUN / 'next_round_v1/completion.json'
    while time.monotonic() - start < 3 * 86400:
        verify()
        d = read(download) if download.exists() else None
        r = read(runtime) if runtime.exists() else None
        z_state = read(z) if z.exists() else None
        require(d is None or d.get('status') == 'PASS_PINNED_TEACHER_WEIGHTS_ON_LINUX', 'teacher download stopped; preserve partials')
        require(r is None or r.get('status') == 'PASS_PINNED_CUDA_RUNTIME_BUILD_ONLY', 'pinned CUDA build stopped')
        if d is not None and r is not None and z_state is not None:
            # Z's quality/package success is not a dependency for T training.
            return d, r, z_state
        progress('WAITING_REGISTERED_LINUX_PREPARATION_AND_EXISTING_Z_TERMINAL',
                 download_ready=d is not None, runtime_ready=r is not None,
                 Z_terminal=z_state is not None, Z_quality_required=False,
                 model_payload_download_host='Linux', Windows_bulk_transfer=False)
        time.sleep(30)
    raise TimeoutError('bounded dependency wait expired; no duplicate or external termination')


def freeze_z_cache(z_state):
    if z_state.get('stage') != 'PASS_COMPLETE_426_Z8B_READY_FOR_DELIVERY':
        write(HERE / 'cache_01/no_valid_Z_cache.json', {'status': 'NO_COMPLETE_Z_CACHE_REUSE', 'Z_terminal': z_state}, fresh=True)
        return
    import train_student
    train_student.helper_paths(RUN)
    import common as old
    old.verify()
    for scope in ('nontest', 'rematch'):
        cache = RUN / 'next_round_v1' / (scope + '_01')
        source, _, _ = old.inputs(scope)
        names = ('field_frames.jsonl', 'field_shots.jsonl', 'anchor_requests.jsonl',
                 'anchor_output.jsonl', 'schedule.stage.json', 'spatial.stage.json',
                 'package.stage.json', 'independent_validation.json')
        require(all((cache / name).is_file() for name in names), 'complete Z cache has missing evidence')
        require(read(cache / 'spatial.stage.json')['status'] == 'PASS_STRICT_SOURCE_FIELD_SPATIAL', 'Z spatial field invalid')
        identities = {name: sha(cache / name) for name in names}
        write(HERE / 'cache_01' / (scope + '.json'), {
            'status': 'PASS_FROZEN_Z_SOURCE_FIELD_CACHE', 'utc': utc(), 'cache': str(cache), 'files': identities,
            'Z_completion_sha256': sha(RUN / 'next_round_v1/completion.json'),
            'source_lock_sha256': sha(RUN / 'next_round_v1/source_lock.json'),
            'manifest_sha256': source['manifest_sha256'], 'clock_registry_sha256': source['registry_sha256'],
            'model_receipt_sha256': old.read(RUN / 'next_round_v1/config.json')['model_receipt']['sha256'],
            'time_adapter_enabled': False}, fresh=True)


def teacher_admission(download, runtime):
    verify()
    recipe = read(RUN / 'teacher32b_linux_download_v1/recipe.json')
    expected = {row['path']: row for row in recipe['files']}
    weights = download['files']
    require(len(weights) == 2 and {Path(w['path']).name for w in weights} == set(expected), 'teacher file set differs')
    for weight in weights:
        path = Path(weight['path'])
        row = expected[path.name]
        require(path.is_file() and path.stat().st_size == row['size_bytes'] and
                weight['sha256'] == row['lfs_sha256'] and sha(path) == row['lfs_sha256'], 'teacher artifact SHA failed')
    binary = next(row for row in runtime['binaries'] if Path(row['path']).name == 'llama-server')
    require(sha(binary['path']) == binary['sha256'] and runtime['source_revision'] ==
            '5ad1c5da0ad7f6176256b823925aad19134f0263', 'teacher runtime identity differs')
    model = next(w['path'] for w in weights if not Path(w['path']).name.startswith('mmproj-'))
    projector = next(w['path'] for w in weights if Path(w['path']).name.startswith('mmproj-'))
    with socket.socket() as server:
        server.bind(('127.0.0.1', 0)); port = server.getsockname()[1]
    command = [binary['path'], '--model', model, '--mmproj', projector,
         '--n-gpu-layers', '99', '--host', '127.0.0.1', '--port', str(port), '--parallel', '1',
         '--ctx-size', '65536', '--no-context-shift', '--log-verbosity', '10',
         '--image-min-tokens', '8', '--image-max-tokens', '768', '--flash-attn', 'on']
    value = {'status': 'ADMITTED_PENDING_REAL_TEACHER_PROBE', 'utc': utc(),
         'base_model_id': 'Qwen/Qwen3-VL-32B-Instruct', 'model_id': recipe['repo'],
         'model_revision': recipe['revision'], 'runtime_revision': runtime['source_revision'],
         'job_source_lock_sha256': sha(HERE / 'source_lock.json'), 'production_test_access': False,
         'weight_files': weights, 'max_sequence_length': 65536, 'max_pixels_per_frame': 786432,
         'image_min_tokens': 8, 'image_max_tokens': 768, 'max_new_tokens': 8192,
         'server_binary_sha256': binary['sha256'], 'server_command': command,
         'server_url': 'http://127.0.0.1:' + str(port),
         'physical_admission': {'mode': 'ACTUAL_CAPACITY_ONLY', 'disk_free_bytes': shutil.disk_usage(HERE).free,
                                'actual_gpu_peak_pending_probe': True, 'external_compute_not_preempted': True},
         'server_parallel': 1, 'server_log_verbosity': 10}
    write(HERE / 'teacher_admission.json', value, fresh=True)
    return value


def teacher_command(config, admission, phase):
    selection = Path(config['selection_dir'])
    return [HERE / 'teacher_label.py', '--run-dir', RUN, '--out-dir', HERE / 'teacher_01',
         '--selected-train', selection / 'selected_train.jsonl', '--selected-dev', selection / 'selected_dev.jsonl',
         '--selection-receipt', selection / 'selection_receipt.json', '--teacher-admission', HERE / 'teacher_admission.json',
         '--server-url', admission['server_url'], '--start-server', '--phase', phase,
         '--ffprobe', config['ffprobe_path']]


def probe_output_estimate(config):
    selection = Path(config['selection_dir'])
    populations = [rows(selection / (split + '.jsonl')) for split in ('selected_train', 'selected_dev')]
    largest = []
    for population in populations:
        values = []
        for row in population:
            output = subprocess.check_output([config['ffprobe_path'], '-v', 'error', '-select_streams', 'v:0',
                 '-show_entries', 'stream=width,height', '-of', 'json', row['source_path']], text=True, timeout=30)
            geometry = json.loads(output)['streams'][0]
            values.append(geometry['width'] * geometry['height'] * 3 * len(row['planned_source_frame_ordinals']))
        largest.append(max(values))
    # PNG + original request JSON + review request JSON; probe is only two windows.
    return math.ceil(sum(largest) * 4.1 + 8_000_000)


def directory_bytes(path):
    return sum(p.stat().st_size for p in Path(path).rglob('*') if p.is_file())


def student_config(config):
    import train_student as student
    teacher = HERE / 'teacher_01'
    labels = teacher / 'validated'
    require(read(teacher / 'teacher_completion.json')['status'] == 'PASS_VALIDATED_WEAK_TEACHER_LABELS' and
            read(teacher / 'semantic_review.json')['status'] == 'PASS_AUTOMATED_WEAK_SEMANTIC_REVIEW',
            'teacher observation/label/semantic gate not ready')
    selection = read(Path(config['selection_dir']) / 'selection_receipt.json')
    template = read(RUN / 'next_round_v1/supervision/train_config_template.json')
    previous = read(RUN / 'next_round_v1/config.json')
    model = dict(template['model'])
    model['model_receipt'] = previous['model_receipt']
    model['initial_adapter_config_sha256'] = sha(Path(model['initial_adapter_dir']) / 'adapter_config.json')
    optimization = {key: template['optimization'][key] for key in
         ('lr', 'optimizer', 'betas', 'eps', 'weight_decay', 'grad_clip_norm', 'effective_batch_windows',
          'max_epochs', 'smoke_update_limit', 'seed', 'precision', 'attn_implementation', 'gradient_checkpointing_use_reentrant')}
    optimization.update(microbatch_windows=1, gradient_accumulation_steps=16)
    # No circular config/source-lock hash: actual labels and review have separate references.
    value = {'schema': 'aic_t_student_config_v1', 'authorized': True,
         'formal_C_BCE_admitted': False, 'official_upload_authorized': False,
         'source_lock': {'path': str(HERE / 'source_lock.json'), 'sha256': sha(HERE / 'source_lock.json')},
         'model': model, 'data': {
            'approved_train_manifest': {k: selection['manifests']['train'][k] for k in ('path', 'sha256')},
            'approved_dev_manifest': {k: selection['manifests']['dev'][k] for k in ('path', 'sha256')},
            'validation_receipt': {'path': str(labels / 'validation_receipt.json'), 'sha256': sha(labels / 'validation_receipt.json')},
            'semantic_review_receipt': {'path': str(teacher / 'semantic_review.json'), 'sha256': sha(teacher / 'semantic_review.json')}},
         'input_contract': student.INPUT_CONTRACT, 'optimization': optimization,
         'dev_stop_rule': {'all_selected_fraction': 0.99, 'widespread_degraded_group_fraction': 0.75,
                           'widespread_macro_f1_drop': 0.05}}
    write(HERE / 'student_config.json', value, fresh=True)
    return value


def selected_pipeline(scope):
    out = HERE / (scope + '_01')
    command = [HERE / 'production_t.py']
    gpu(scope + '_temporal', command + ['temporal', scope, out], 14400, 60_000_000,
        'registered source/window denominator; 8B actual non-test generation identity and no test retuning')
    cpu(scope + '_scheduling', command + ['scheduling', scope, out], 14400)
    if not (out / 'spatial.stage.json').exists():
        schedule = read(out / 'schedule.stage.json')
        if schedule['anchors']:
            measure = read(RUN / 'next_round_v1/nontest_01/spatial.stage.json')
            maximum = max(3600, math.ceil(schedule['anchors'] * measure['measured_seconds_per_anchor'] * 2 + 1200))
            planned = schedule['anchors'] * 6000 + schedule['selected_frames'] * 2500 + 20_000_000
            gpu(scope + '_spatial', command + ['spatial', scope, out], maximum, planned,
                'same pinned 8B source field; actual registered anchor count times real non-test measured cost')
        else:
            cpu(scope + '_empty_space', command + ['spatial', scope, out], 120)
    cpu(scope + '_finish', command + ['finish', scope, out], 1800)
    package = read(out / 'package.stage.json')
    require(package['video_records'] == (8 if scope == 'nontest' else 426) and package['issues'] == [],
            'strict source denominator failed')
    return out / 'candidate_T_8B.zip'


def preflight():
    config = verify()
    ffprobe = Path(config['ffprobe_path'])
    require(ffprobe.is_file() and sha(ffprobe) == config['ffprobe_sha256'], 'existing ffprobe identity differs')
    subprocess.run([str(ffprobe), '-version'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
    require(read(HERE / 'authorization.json')['automatic_teacher_student_pipeline_approved'] is True, 'user pipeline authority missing')
    policy = read(ROOT / 'resource_policy.json')
    require(policy['disk_usage_mode'] == 'ACTUAL_CAPACITY_ONLY' and
            all(policy[k] is None for k in ('project_disk_limit_bytes', 'project_ram_limit_bytes', 'project_vram_limit_bytes')),
            'current physical-only policy differs')
    selection = read(Path(config['selection_dir']) / 'selection_receipt.json')
    require(selection['status'] == 'PASS_CPU_SELECTION_UNLABELLED' and
            selection['confirm_opened'] is False and selection['contest_assets_opened'] is False, 'selection is not isolated')
    for name in ('selected_train.jsonl', 'selected_dev.jsonl'):
        require(sha(Path(config['selection_dir']) / name) == selection['files'][name], 'selected windows changed')
    import train_student as student
    require(config['student_input_contract'] == student.INPUT_CONTRACT, 'production/student input contract mismatch')
    student.helper_paths(RUN)
    import common as old
    old.verify()
    require(config['official_upload_authorized'] is False and config['automatic_return'] is False, 'unapproved external delivery')
    return config


def measured_window_seconds(probe):
    values = probe['per_window_wall_sec']
    require(isinstance(values, list) and len(values) == len(probe['window_ids']) and values,
            'real probe timing list missing or incomplete')
    require(all(type(v) in (int, float) and math.isfinite(v) and v > 0 for v in values),
            'real probe timing is not finite positive')
    return max(values)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--preflight', action='store_true')
    args = parser.parse_args()
    config = preflight()
    if args.preflight:
        print(json.dumps({'status': 'PASS_CPU_SOURCE_SELECTION_ROUTE_AND_PIPELINE_PREFLIGHT', 'GPU_started': False}))
        return 0
    lock = (HERE / 'controller.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    write(HERE / 'registration.json', {'pid': os.getpid(), 'utc': utc(),
         'source_lock_sha256': sha(HERE / 'source_lock.json'), 'config_sha256': sha(HERE / 'config.json')}, fresh=True)
    try:
        download, runtime, z_state = wait_dependencies(config)
        freeze_z_cache(z_state)
        admission = teacher_admission(download, runtime)
        probe_bytes = probe_output_estimate(config)
        probe_resource = gpu('teacher_probe', teacher_command(config, admission, 'probe'), 3600, probe_bytes,
            'two non-test metadata-selected probe windows; raw RGB/PNG/request upper output estimate, no project cap')
        probe = read(HERE / 'teacher_01/teacher_probe_completion.json')
        require(probe['status'] == 'PASS_REAL_NONTEST_TEACHER_PROBE', 'real teacher observation failed')
        n = sum(len(rows(Path(config['selection_dir']) / name)) for name in ('selected_train.jsonl', 'selected_dev.jsonl'))
        unit_seconds = max(measured_window_seconds(probe), probe_resource['charged_seconds'] / len(probe['window_ids']))
        maximum = math.ceil(unit_seconds * n * 2 * 2 + 1800)
        actual_probe_bytes = directory_bytes(HERE / 'teacher_01')
        planned = math.ceil(actual_probe_bytes * n / len(probe['window_ids']) * 4 + 20_000_000)
        write(HERE / 'teacher_full_cost_registration.json', {'probe_receipt_sha256': sha(HERE / 'teacher_01/teacher_probe_completion.json'),
              'windows': n, 'two_real_teacher_passes': True, 'maximum_seconds': maximum,
              'planned_output_bytes': planned, 'probe_actual_bytes': actual_probe_bytes}, fresh=True)
        gpu('teacher_full', teacher_command(config, admission, 'all'), maximum, planned,
            'real two-window measured bytes/time scaled to fixed 160 windows and second weak semantic review')
        sc = student_config(config)
        student_args = [HERE / 'train_student.py', '--run-dir', RUN, '--labels-dir', HERE / 'teacher_01/validated',
                        '--out-dir', HERE / 'student_01', '--config', HERE / 'student_config.json']
        cpu('student_admission', student_args + ['--check-only'], 7200)
        counts = read(HERE / 'teacher_01/validated/validation_receipt.json')['eligible_by_split']
        cost = read(config['registered_B_train_report'])
        effective = cost.get('effective_backward_samples', cost.get('valid_samples', 3620))
        old_seconds = cost.get('wall_seconds', cost.get('elapsed_seconds', 18000))
        # Existing measured B training is a cost estimate, never an official quality proxy.
        maximum = math.ceil(max(1, old_seconds / max(1, effective)) * counts['train'] * 3 * 4 + counts['dev'] * 4 * 60 + 3600)
        adapter_bytes = (Path(sc['model']['initial_adapter_dir']) / 'adapter_model.safetensors').stat().st_size
        planned = adapter_bytes * 12 + (counts['train'] * 3 + counts['dev'] * 4) * 200000 + 20_000_000
        gpu('student_train', student_args, maximum, planned,
            'new validated count times original B measured training cost; 3 epoch adapters, update20 optimizer/RNG/prefix adapter, CPU reload')
        trained = read(HERE / 'student_01/student_completion.json')
        require(trained['status'] == 'PASS_TRAINED_SELECTED_STUDENT_ADAPTER' and trained['base_frozen'] is True,
                'student training/development selection failed')
        selected_pipeline('nontest')
        progress('PASS_T_NONTEST8_COMPLETE_CHAIN')
        candidate = selected_pipeline('rematch')
        result = {'status': 'PASS_AUTOPILOT_FINAL_T_ZIP_ON_LINUX', 'utc': utc(),
             'candidate': str(candidate), 'candidate_sha256': sha(candidate), 'candidate_bytes': candidate.stat().st_size,
             'videos': 426, 'selected_epoch': trained['selected_epoch'],
             'selected_adapter_sha256': trained['selected_adapter_sha256'],
             'source_lock_sha256': sha(HERE / 'source_lock.json'),
             'uploaded': False, 'automatic_return': False, 'official_score': None,
             'teacher_is_offline_only': True, 'complete_pipeline_parameters': 8782459120}
        write(HERE / 'completion.json', result, fresh=True)
        progress(result['status'], candidate=str(candidate), candidate_bytes=candidate.stat().st_size)
        return 0
    except BaseException as error:
        result = {'status': 'STOP_AUTOPILOT_PRESERVED', 'utc': utc(),
             'last_progress': read(HERE / 'progress.json') if (HERE / 'progress.json').exists() else None,
             'error_type': type(error).__name__, 'reason': str(error), 'uploaded': False, 'automatic_return': False}
        write(HERE / 'completion.json', result, fresh=True)
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
