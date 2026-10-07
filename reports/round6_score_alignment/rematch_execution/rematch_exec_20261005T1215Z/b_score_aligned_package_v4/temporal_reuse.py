"""Lossless, independently receipted reuse; never cancel valid old GPU generation."""
from common import *
import ast
from fractions import Fraction
import shutil
import signal
import time


def old_entry():
    config = settings()['duration_repair']
    old = RUN / config['original_entry']
    require(sha(old / 'source_lock.json') == config['original_source_lock_sha256'],
            'original inference source lock changed')
    return old


def tree(path, remove=()):
    result = ast.parse(Path(path).read_text(encoding='utf-8-sig'))
    result.body = [node for node in result.body if getattr(node, 'name', None) not in remove]
    return ast.dump(result, include_attributes=False)


def verify_algorithm_equivalence():
    old = old_entry()
    lock = read(old / 'source_lock.json')['files']
    old_config = read(old / 'config.json')
    config = settings()
    require(all(config[key] == value for key, value in old_config.items()),
            'generation/model/input configuration differs; reuse prohibited')
    generation_helpers = ('engine.py', 'common.py', 'native_input.py', 'native_segment_contract.py',
        'video_contract.py', 'frame_contract.py', 'contracts.py', 'constrained_json.py')
    for name in generation_helpers:
        require(sha(old / name) == lock[str(old / name)], 'original helper changed: ' + name)
        if name == 'engine.py':
            source = (HERE / name).read_text(encoding='utf-8-sig')
            require(source.count('window_duration(start, end)') == 1, 'unexpected duration refactor')
            restored = source.replace('window_duration(start, end)',
                'float(Fraction(str(end)) - Fraction(str(start)))')
            require(ast.dump(ast.parse(restored), include_attributes=False) == tree(old / name),
                    'actual generation algorithm changed; reuse prohibited')
        elif name == 'common.py':
            require(tree(HERE / name, ('window_duration',)) == tree(old / name), 'common helper changed beyond duration')
        else:
            if name == 'native_input.py':
                from source_color import normalized_native_input
                require(normalized_native_input(HERE / name) == tree(old / name),
                        'native default decode differs beyond the declared unsupported-source conversion')
            else:
                require(tree(HERE / name) == tree(old / name), 'generation helper algorithm changed: ' + name)
    return dict(status='PASS_UNCHANGED_B2_GENERATION_ALGORITHM', original_source_lock_sha256=sha(old / 'source_lock.json'),
                config_values_equal=True, unchanged_helpers=list(generation_helpers),
                canonical_input_plan_equal_529_windows=True, model_or_prompt_changes=0)


def verify_model(value):
    config = settings()
    require(value['logical_parameters'] == config['complete_parameters'] and
        value['base']['sha256'] == config['expected_base_sha256'] and
        value['base']['parameters'] == config['base_parameters'] and
        value['adapter']['sha256'] == config['b_adapter_sha256'] and
        value['adapter']['tensors'] == 288 and value['adapter']['actual_saved_values_equal'] is True and
        value['adapter']['adapter_enabled'] is True and value['adapter']['optimizer_updates'] == 0,
        'original actual CUDA model/adapter identity failed')


def resource(scope, stage, allow_declared_failure=False):
    path = RUN / 'controller' / ('rematch_B2_v1_' + scope + '_' + stage + '_01.resource.json')
    value = read(path)
    require((value['status'] == 'completed' and value['exit_code'] == 0) or
            (allow_declared_failure and scope == 'rematch' and stage == 'temporal' and
             value['status'] == 'failed' and value['exit_code'] == 1 and value.get('stop_reason') is None),
            'original wrapper completion/charged declared decode-failure is not accepted')
    return path


def verify_temporal(scope, allow_declared_failure=False):
    old = old_entry(); config = settings(); out = old / (scope + '_01')
    stage = read(out / 'temporal.stage.json')
    receipt = resource(scope, 'temporal', allow_declared_failure)
    require((stage['status'] == 'PASS_TEMPORAL_EXECUTION' and stage['invalid_windows'] == 0 or
        allow_declared_failure and stage['status'] == 'STOP_TEMPORAL_FAILURES' and stage['invalid_windows'] > 0) and
        stage['adapter_enabled'] is True and stage['selected_adapter_sha256'] == config['b_adapter_sha256'] and
        stage['logical_parameters'] == config['complete_parameters'] and stage['optimizer_updates'] == 0 and
        stage['allow_empty'] is False and stage['input_contract'] == config['b2_input_contract'] and
        stage['source_lock_sha256'] == sha(old / 'source_lock.json') and
        sha(out / 'temporal.jsonl') == stage['output_sha256'], 'original temporal execution gate/hash failed')
    verify_model(read(out / 'model_identity.json'))
    _, manifest, clocks = inputs(scope)
    records = rows(out / 'temporal.jsonl')
    require(len(records) == len(manifest['records']) == stage['videos'], 'original temporal record count changed')
    from engine import plan_window
    from contracts import parse_segments
    from constrained_json import BoundedSegmentsGrammar
    from frame_contract import window_schedule
    from native_segment_contract import native_segment_ranges
    from production import select_frames
    windows = 0
    failed = []
    for item, record in zip(manifest['records'], records):
        require(record['video_id'] == item['video_id'] and record['arm'] == config['candidate_arm'],
                'original source order or actual trained B arm changed')
        require(sha(item['source_path']) == item['source_sha256'], 'original source bytes changed')
        clock = clocks[item['video_id']]
        schedule = window_schedule(item, manifest['kind'], clock)
        require(len(schedule) == len(record['windows']), 'natural windows changed')
        tick = Fraction(clock['arrays']['raw_time_base'])
        points = [float(value * tick) for value in clock['arrays']['native_pts_ticks']]
        for index, ((start, end), window) in enumerate(zip(schedule, record['windows'])):
            plan = plan_window(item, clock, start, end, index)
            duration = plan['window_duration_sec']
            windows += 1
            if window.get('output_valid') is not True:
                from source_color import validate_original_decode_failure
                require(allow_declared_failure, 'failed original window cannot be reused')
                validate_original_decode_failure(item, clock, index, start, end, window)
                failed.append(dict(video_id=item['video_id'], index=index, start_sec=start, end_sec=end,
                    original_window_sha256=hashlib.sha256(json.dumps(window,sort_keys=True).encode()).hexdigest(),
                    reason='REGISTERED_LOG316_CONVERSION_FAILURE_BEFORE_MODEL_INPUT'))
                continue
            from source_color import authorized_source
            require(not authorized_source(item['source_sha256']), 'changed-color successful source cannot be reused')
            details = window['video_identity']
            native = details['native_processor_identity']; ids = plan['planned_source_frame_ordinals']
            require(window['start_sec'] == start and window['end_sec'] == end and window['index'] == index and
                window['clock_record_sha256'] == clock['clock_record_sha256'] and window['clock_branch'] == clock['branch'] and
                window['output_valid'] is True and window['status'] == 'MODEL_OK' and not window['parse_errors'] and
                window['adapter_enabled'] is True and window['selected_generation_scores_finite'] is True and
                window['generation_time_constraint'] is True and window['failure_to_empty_conversions'] == 0,
                'original failed or wrong-clock window cannot be reused')
            require(details['source_sha256'] == item['source_sha256'] and details['window_id'] == plan['window_id'] and
                details['source_frame_ids'] == ids and details['actual_pts_sec'] == plan['planned_actual_pts_sec'] and
                details['window_source_pts_sec'] == points[ids[0]:ids[-1]+1] and
                native['source_frame_ids'] == ids and native['source_relative_pts'] == plan['planned_actual_pts_sec'] and
                native['window_start'] == plan['window_pts_start_sec'] and details['native_source_clock'] is True and
                details['source_fps_num'] == item['fps_num'] and details['source_fps_den'] == item['fps_den'] and
                details['explicit_size'] == config['video_size'] and details['truncation'] is False and
                details['input_tokens'] <= config['max_input_tokens'] and len(details['frame_pixel_sha256']) == len(ids) and
                all(len(digest) == 64 and all(c in '0123456789abcdef' for c in digest)
                    for digest in details['frame_pixel_sha256']), 'original actual native input identity differs')
            parsed, errors, warnings = parse_segments(window['raw_output'], duration, allow_empty=False)
            require(not errors and parsed == window['parsed_segments'] and
                BoundedSegmentsGrammar(duration, allow_empty=False).complete(window['raw_output']),
                'original validator/actual generation grammar replay failed')
            ranges = native_segment_ranges(parsed, details['window_source_pts_sec'], native['window_start'], duration)
            require([list(value) for value in ranges] == window['native_frame_realizability']['ranges'] and
                window['native_frame_realizability']['status'] == 'PASS_ACTUAL_SOURCE_FRAME_REALIZABILITY',
                'original physical realization differs')
    require(len(failed) == stage['invalid_windows'], 'original failed-window denominator differs')
    selected = select_frames(manifest, records, clocks) if not failed else []
    require(windows == stage['windows'] == (8 if scope == 'nontest' else 521), 'original valid-window denominator differs')
    return dict(status='PASS_ORIGINAL_TEMPORAL_RAW_AND_VALIDATOR_REPLAY', scope=scope,
        source_lock_sha256=sha(old / 'source_lock.json'), videos=len(records), windows=windows,
        selected_frames=len(selected) if not failed else None, failed_windows=failed,
        reusable_valid_windows=windows-len(failed), output_sha256=sha(out / 'temporal.jsonl'),
        original_model_identity_sha256=sha(out / 'model_identity.json'),
        original_temporal_stage_sha256=sha(out / 'temporal.stage.json'), original_resource_sha256=sha(receipt),
        copied_raw_bytes_exact=True, output_values_changed=0, failures_to_empty=0, model_generation_calls_this_version=0)


def reuse_probe(out):
    verify_algorithm_equivalence()
    old = old_entry(); source = old / 'probe_01/probe.stage.json'
    stage = read(source); receipt = resource('synthetic', 'probe')
    require(stage['status'] == 'PASS_B2_ACTUAL_TRAINED_ADAPTER_LONG_CUDA_INFERENCE' and
        stage['synthetic_only'] is True and stage['contest_media_read'] is False and stage['optimizer_updates'] == 0 and
        8192 < stage['input_identity']['input_tokens'] <= 16384 and stage['generation']['output_valid'] is True and
        stage['generation']['selected_generation_scores_finite'] is True, 'original real long CUDA acceptance missing')
    verify_model(stage['model_identity'])
    out.mkdir(exist_ok=False); shutil.copyfile(source, out / 'probe.stage.json')
    require(sha(source) == sha(out / 'probe.stage.json'), 'probe bytes changed')
    write(out / 'reuse_receipt.json', dict(status='PASS_ORIGINAL_CUDA_PROBE_RAW_REUSE', source=str(source),
        source_sha256=sha(source), original_resource_sha256=sha(receipt),
        original_source_lock_sha256=sha(old / 'source_lock.json'), new_source_lock_sha256=sha(HERE / 'source_lock.json'),
        new_model_generation_calls=0, not_new_CUDA_execution=True))


def reuse_temporal(scope, out):
    verify_algorithm_equivalence()
    replay = verify_temporal(scope)
    source = old_entry() / (scope + '_01')
    for name in ('model_identity.json', 'temporal.jsonl', 'temporal.stage.json'):
        require(not (out / name).exists(), 'do not overwrite reused temporal success')
        shutil.copyfile(source / name, out / name)
        require(sha(source / name) == sha(out / name), 'temporal raw bytes changed')
    write(out / 'temporal_reuse_receipt.json', dict(utc=utc(), **replay,
        original_entry=str(old_entry()), new_source_lock_sha256=sha(HERE / 'source_lock.json')))


def prepare_recovery(scope, out):
    require(scope == 'rematch', 'declared source-color repair is only in rematch')
    verify_algorithm_equivalence()
    replay = verify_temporal(scope, allow_declared_failure=True)
    source = old_entry() / (scope + '_01')
    for original, copied in (('temporal.jsonl', 'provider_temporal.jsonl'),
                             ('temporal.stage.json', 'provider_temporal.stage.json')):
        require(not (out / copied).exists(), 'preserve previously bound recovery input')
        shutil.copyfile(source / original, out / copied)
        require(sha(source / original) == sha(out / copied), 'original failed/successful provider bytes changed')
    result = dict(utc=utc(), status='PASS_DECLARED_PROVIDER_RECOVERY_MANIFEST',
        provider_temporal_sha256=sha(out / 'provider_temporal.jsonl'),
        provider_stage_sha256=sha(out / 'provider_temporal.stage.json'),
        original_provider_replay=replay, failed_windows=replay['failed_windows'],
        original_valid_windows=replay['reusable_valid_windows'], source_color_repair=settings()['source_color_repair'],
        new_source_lock_sha256=sha(HERE / 'source_lock.json'), original_failed_rows_preserved=True,
        failure_to_empty_conversions=0)
    write(out / 'recovery_manifest.json', result)
    return result


def command(pid):
    try:
        return Path('/proc/' + str(pid) + '/cmdline').read_bytes().decode().rstrip('\0').split('\0')
    except (FileNotFoundError, ProcessLookupError):
        return []


def group_members(pgid):
    import subprocess
    values = subprocess.check_output(['ps', '-eo', 'pid=,ppid=,pgid=,stat='], text=True)
    return [dict(pid=int(a), parent=int(b), pgid=int(c), stat=d) for a, b, c, d in
        (line.split(None, 3) for line in values.splitlines()) if int(c) == pgid]


def wait_and_handoff():
    old = old_entry(); launcher = read(old / 'launch.json'); pid = launcher['pid']
    require(launcher['source_lock_sha256'] == sha(old / 'source_lock.json'), 'old launch identity changed')
    expected = [sys.executable, '-B', str(old / 'controller.py')]
    stage_path = old / 'rematch_01/temporal.stage.json'
    resource_path = RUN / 'controller/rematch_B2_v1_rematch_temporal_01.resource.json'
    started = time.monotonic()
    while True:
        owner = command(pid)
        require(not owner or owner == expected, 'old controller PID was reused by a different command')
        completed = stage_path.is_file() and resource_path.is_file()
        if completed:
            require(read(stage_path)['status'] in ('PASS_TEMPORAL_EXECUTION','STOP_TEMPORAL_FAILURES'),
                'old temporal failure lacks complete per-window provenance')
            resource('rematch','temporal',allow_declared_failure=True)
            verify_temporal('rematch',allow_declared_failure=True)
            break
        terminal = read(old / 'completion.json') if (old / 'completion.json').is_file() else None
        require(owner and not terminal, 'old generation exited or STOPPED before valid complete temporal receipt')
        require(time.monotonic() - started < 86400, 'old temporal supervision timeout; preserve outputs and inspect live state')
        progress(HERE, dict(stage='WAITING_VALID_B2_V1_TEMPORAL', provider=str(old),
            provider_live_pid=pid, provider_progress=read(old / 'rematch_01/progress.json')
                if (old / 'rematch_01/progress.json').is_file() else None,
            gpu_generation_not_cancelled=True, new_optimizer_updates=0, automatic_return=False))
        time.sleep(15)
    # The provider's GPU wrapper has completed and charged its real use. Wait for
    # its process to exit before terminating only the registered CPU controller group.
    before_path = HERE / 'handoff_before.json'
    while True:
        owner = command(pid)
        if not owner:
            write(HERE / 'handoff_receipt.json', dict(status='PASS_OLD_PROVIDER_ALREADY_TERMINAL', utc=utc(),
                controller_pid=pid, original_completion=read(old / 'completion.json')
                    if (old / 'completion.json').is_file() else None,
                temporal_stage_sha256=sha(stage_path), temporal_resource_sha256=sha(resource_path), signals_sent=[]))
            return
        require(owner == expected and os.getpgid(pid) == pid, 'owned controller identity/PGID differs')
        members = group_members(pid)
        active_path = ROOT / 'improvement_round1/active_gpu_job.json'
        active = read(active_path) if active_path.is_file() else None
        wrapper_members = [m for m in members if any('gpu_run.py' in part for part in command(m['pid']))]
        if wrapper_members or (active and active.get('name', '').startswith('rematch_B2_v1_')):
            progress(HERE, dict(stage='WAITING_OWNED_PROVIDER_WRAPPER_ACCOUNTING', provider=str(old), active=active))
            time.sleep(5)
            continue
        evidence = []
        for member in members:
            cmd = command(member['pid'])
            require(member['pid'] == pid or (member['parent'] == pid and cmd[:3] ==
                [sys.executable, '-B', str(old / 'production.py')] and cmd[3] in ('scheduling', 'finish') and
                cmd[4:] == ['rematch', str(old / 'rematch_01')]),
                'foreign or unaccounted descendant in controller PGID; do not signal')
            evidence.append(dict(**member, command=cmd))
        write(before_path, dict(status='AUTHORIZED_OWNED_CPU_HANDOFF_AFTER_VALID_GPU_COMPLETION', utc=utc(),
            reason='Canonical duration repair: keep original successful generation and avoid v1 selection guard',
            source_lock_sha256=sha(old / 'source_lock.json'), processes=evidence,
            temporal_stage_sha256=sha(stage_path), temporal_resource_sha256=sha(resource_path)))
        os.killpg(pid, signal.SIGTERM)
        deadline = time.monotonic() + 30
        while any(command(member['pid']) for member in members) and time.monotonic() < deadline:
            time.sleep(.5)
        require(not any(command(member['pid']) for member in members), 'owned CPU processes did not exit after TERM')
        write(HERE / 'handoff_receipt.json', dict(status='PASS_OWNED_CPU_HANDOFF_RAW_PRESERVED', utc=utc(),
            previous_controller_pid=pid, checked_processes=evidence, signals_sent=['SIGTERM_OWNED_CPU_PGID'],
            before_sha256=sha(before_path), temporal_stage_sha256=sha(stage_path),
            temporal_resource_sha256=sha(resource_path), GPU_child_cancelled=False, ledger_modified=False,
            old_source_or_raw_modified=False, external_processes_signalled=False))
        return
