"""Once-only B2: actual trained B inference, complete non-test and 426 strict ZIP."""
from common import *
import math
import shutil
import subprocess
import time
import traceback
import zipfile


def checkpoint(stage, **extra):
    value = dict(stage=stage, pid=os.getpid(), source_lock_sha256=sha(HERE / 'source_lock.json'),
                 automatic_return=False, uploaded=False, **extra)
    progress(HERE, value)
    return value


def capacity(planned):
    module = load(RUN / 'resource_unlimited_v1_20261007/physical_capacity.py', 'b2_actual_capacity')
    return module.admit(read(ROOT / 'resource_policy.json'), disk_free_bytes=shutil.disk_usage(ROOT).free,
                        remaining_output_bytes=planned)


def gpu(script, stage, scope, out, maximum, planned):
    config = verify()
    admission = capacity(planned)
    name = 'rematch_B2_v4_' + scope + '_' + stage + '_01'
    write(HERE / (name + '.admission.json'), dict(authorized=True,
        user_request='2026-10-08完全授权自主裁决修复接续到最终一个ZIP', stage=stage, scope=scope,
        source_lock_sha256=sha(HERE / 'source_lock.json'), capacity=admission,
        max_seconds=maximum, planned_output_bytes=planned, official_upload_authorized=False))
    command = [sys.executable, '-B', config['current_runner'], '--name', name,
        '--max-seconds', str(maximum), '--planned-output-bytes', str(planned), '--capacity-reason',
        'Measured current same-8B outputs and complete source-field counts; actual capacity only, no Mac or quota',
        '--queue-seconds', '86400', '--', sys.executable, '-B', str(HERE / script), stage, scope, str(out)]
    checkpoint('RUNNING_' + scope.upper() + '_' + stage.upper(), job=name, capacity=admission)
    with (HERE / (name + '.wrapper.log')).open('x') as stream:
        result = subprocess.run(command, cwd=RUN, stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT)
    receipt = RUN / 'controller' / (name + '.resource.json')
    require(result.returncode == 0 and receipt.exists() and read(receipt)['status'] == 'completed',
            'B2 GPU phase failed: ' + name)


def cpu(stage, scope, out, timeout, planned):
    verify(); capacity(planned)
    checkpoint('RUNNING_' + scope.upper() + '_' + stage.upper())
    with (HERE / (scope + '_' + stage + '.log')).open('x') as stream:
        result = subprocess.run([sys.executable, '-B', str(HERE / 'production.py'), stage, scope, str(out)],
            cwd=RUN, stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT, timeout=timeout)
    require(result.returncode == 0, 'B2 CPU phase failed: ' + scope + ' ' + stage)


def measured_space():
    from cost_contract import measured_spatial_cost
    paths = [HERE / 'nontest_01/spatial.stage.json', RUN / 'next_round_v1/nontest_01/spatial.stage.json']
    return measured_spatial_cost([(path, read(path)) for path in paths if path.is_file()])


def final_zip(path, expected_count):
    import hashlib
    with zipfile.ZipFile(path) as archive:
        require(archive.namelist() == ['predictions.jsonl'] and archive.testzip() is None, 'ZIP member or CRC failure')
        data = archive.read('predictions.jsonl')
    records = [json.loads(line) for line in data.decode('utf-8').splitlines() if line.strip()]
    _, manifest, _ = inputs('rematch' if expected_count == 426 else 'nontest')
    ids = [row['video_id'] for row in records]
    require(len(ids) == expected_count and len(set(ids)) == expected_count and
            set(ids) == {row['video_id'] for row in manifest['records']}, 'ZIP source denominator changed')
    require(data == path.with_name('predictions.jsonl').read_bytes(), 'ZIP member differs from accepted predictions')
    return dict(zip_bytes=path.stat().st_size, zip_sha256=sha(path), crc_pass=True,
                predictions_sha256=hashlib.sha256(data).hexdigest(), archive_names=['predictions.jsonl'], videos=len(ids))


def main():
    require(not (HERE / 'registration.json').exists(), 'controller already registered')
    write(HERE / 'registration.json', dict(pid=os.getpid(), utc=utc(), source_lock_sha256=sha(HERE / 'source_lock.json'),
        route='PRESERVED_TRAINED_B_8B_NATIVE_PTS_SOURCE_FIELD_B2', new_optimizer_updates=0,
        automatic_return=False, uploaded=False))
    try:
        verify()
        from temporal_reuse import reuse_probe, reuse_temporal, wait_and_handoff, prepare_recovery
        reuse_probe(HERE / 'probe_01')
        require(read(HERE / 'probe_01/probe.stage.json')['status'] ==
                'PASS_B2_ACTUAL_TRAINED_ADAPTER_LONG_CUDA_INFERENCE', 'actual B2 CUDA acceptance missing')
        for scope in ('nontest', 'rematch'):
            out = HERE / (scope + '_01'); out.mkdir(exist_ok=False)
            if scope == 'rematch':
                require(read(HERE / 'nontest_01/package.stage.json')['status'] ==
                        'PASS_COMPLETE_B2_8B_PACKAGE_ON_LINUX', 'full non-test gate required before rematch')
                measurement = read(HERE / 'nontest_01/temporal.stage.json')
                seconds = measurement['wall_seconds'] / measurement['windows']
                maximum = max(3600, math.ceil(521 * seconds * 2 + 1200))
                planned = max(60_000_000, math.ceil((HERE / 'nontest_01/temporal.jsonl').stat().st_size / 8 * 426 * 2))
            else:
                maximum, planned = 3600, 60_000_000
            if scope == 'rematch':
                checkpoint('WAITING_VALID_B2_V1_TEMPORAL')
                wait_and_handoff()
            if scope == 'rematch':
                plan = prepare_recovery(scope, out)
                if plan['failed_windows']:
                    gpu('recovery.py', 'recover', scope, out, 3600, max(planned, 60_000_000))
                else:
                    reuse_temporal(scope, out)
            else:
                reuse_temporal(scope, out)
            cpu('scheduling', scope, out, 14400, 2_000_000_000 if scope == 'rematch' else 100_000_000)
            schedule = read(out / 'schedule.stage.json')
            anchors, selected = schedule['anchors'], schedule['selected_frames']
            cost_path, seconds = measured_space()
            maximum = max(3600, math.ceil(anchors * seconds * 2 + 1200))
            planned = anchors * 6000 + selected * 2500 + 20_000_000
            write(HERE / (scope + '_spatial_registration.json'), dict(anchors=anchors,
                field_frames=schedule['field_frames'], selected_frames=selected,
                measured_nontest_receipt=cost_path, measured_seconds_per_anchor=seconds,
                maximum_seconds=maximum, planned_output_bytes=planned))
            if not (out / 'spatial.stage.json').exists():
                if anchors:
                    gpu('production.py', 'spatial', scope, out, maximum, planned)
                else:
                    cpu('spatial', scope, out, 600, 100_000)
            cpu('finish', scope, out, 3600, planned)
            report = read(out / 'package.stage.json')
            independent = read(out / 'independent_validation.json')
            require(report['video_records'] == (8 if scope == 'nontest' else 426) and report['issues'] == [] and
                    independent['status'] == 'PASS_INDEPENDENT_STRICT_VALIDATION' and
                    all(independent['checks'].values()), 'B2 full strict source validation failed')
            result = final_zip(out / 'candidate_B2_8B.zip', 8 if scope == 'nontest' else 426)
            if scope == 'nontest':
                checkpoint('PASS_B2_NONTEST8_COMPLETE', **result)
        candidate = HERE / 'rematch_01/candidate_B2_8B.zip'
        result = checkpoint('PASS_COMPLETE_426_B2_8B_ZIP_ON_LINUX', candidate=str(candidate),
            **final_zip(candidate, 426), official_score=None, temporal_adapter_sha256=settings()['b_adapter_sha256'],
            actual_training='PRESERVED_ALREADY_TRAINED_B_5_EPOCHS_227_UPDATES', new_optimizer_updates=0,
            new_T_training_started=False, teacher_quality_stop_preserved=True,
            nontest_package_receipt_sha256=sha(HERE / 'nontest_01/package.stage.json'),
            independent_validation_sha256=sha(HERE / 'rematch_01/independent_validation.json'))
    except Exception as error:
        result = checkpoint('STOP_B2_PACKAGE_V4', failure_type=type(error).__name__, failure=str(error), traceback=traceback.format_exc())
    write(HERE / 'completion.json', dict(utc=utc(), **result))
    return 0 if result['stage'] == 'PASS_COMPLETE_426_B2_8B_ZIP_ON_LINUX' else 1


if __name__ == '__main__':
    raise SystemExit(main())
