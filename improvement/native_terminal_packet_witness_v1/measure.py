"""First fixed426 source-byte+compressed-packet CPU measurement, append-only."""
import argparse
import datetime as dt
from fractions import Fraction as F
import hashlib
import json
import os
from pathlib import Path
import resource
import socket
import stat
import sys
import time
import traceback

from packet_contract import SCHEMA, PacketUnavailable, packet_row, resolve

HOME = Path('/home/inspur/aic_video_work')
RUN = HOME/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
CAMPAIGN = HOME/'twenty_hour_five_20261014_v1'
ROOT = CAMPAIGN/'native_terminal_packet_witness_v1'
MEDIA = RUN/'baseline_a/m0_426_02/media'
PLAN = RUN/'balanced_two_window_risk_v3/input_01/rematch_plan.json'
REGISTRY = RUN/'baseline_pts_v4/scan_01/clock_registry.json'
SOURCE_BYTES = 4781857740
DEADLINE = dt.datetime.fromisoformat('2026-10-14T11:56:40+00:00')


class IdentityChanged(RuntimeError):
    pass


def need(ok, why):
    if not ok:
        raise IdentityChanged(why)


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha_stream(stream):
    h, count = hashlib.sha256(), 0
    while True:
        block = stream.read(8 << 20)
        if not block:
            break
        h.update(block)
        count += len(block)
    return h.hexdigest(), count


def sha(path):
    with Path(path).open('rb') as stream:
        return sha_stream(stream)[0]


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())


def host():
    need(socket.gethostname() == 'inspur-NP5570M5' and sys.platform == 'linux' and
         os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'Verified Linux CPU-only child required')
    need(Path(__file__).resolve() == ROOT/'code/measure.py', 'New registered code root required')


def safe_file(path, root):
    path = Path(path)
    need(path.is_absolute() and path == path.resolve(strict=True) and path.is_relative_to(root.resolve(strict=True)),
         'Source/reference path or symlink escaped its frozen root')
    need(path.is_file(), 'Frozen reference is not a regular file')
    return path


def ref(path):
    path = safe_file(path, RUN if Path(path).is_relative_to(RUN) else ROOT)
    return dict(path=str(path), bytes=path.stat().st_size, sha256=sha(path))


def snapshot(value):
    return dict(bytes=value.st_size, device=value.st_dev, inode=value.st_ino,
                mtime_ns=value.st_mtime_ns, regular=stat.S_ISREG(value.st_mode))


def freeze():
    host()
    need(dt.datetime.now(dt.timezone.utc) < DEADLINE, 'No new stage after the campaign deadline')
    need(not (ROOT/'registration_01.json').exists() and not (ROOT/'run_01').exists(), 'This first measurement is already claimed')
    plan, registry = read(PLAN), read(REGISTRY)
    plan_ref, registry_ref = ref(PLAN), ref(REGISTRY)
    need(plan['input_ref']['registry_sha256'] == registry_ref['sha256'], 'Original plan/registry binding differs')
    records = {x['video_id']: x for x in registry['records']}
    jobs = {x['video_id']: x for x in plan['jobs']}
    need(len(records) == len(registry['records']) == len(jobs) == len(plan['jobs']) == 426 and
         set(records) == set(jobs) == {str(i) for i in range(426)}, 'Complete fixed426 source identities required')
    sources, counts = [], dict(old_explicit_native_end=0, old_CFR_nominal_only=0)
    for vid in sorted(jobs, key=int):
        meta, record = jobs[vid]['metadata'], records[vid]
        path = safe_file(meta['source_path'], MEDIA)
        info = snapshot(path.stat())
        need(info['regular'] and info['bytes'] > 0, 'Frozen source is not nonempty regular media')
        clock_ref = record['clock_arrays']
        clock_path = safe_file(clock_ref['path'], RUN)
        clock_binding = ref(clock_path)
        need(clock_binding['sha256'] == clock_ref['sha256'], 'Original clock array bytes differ')
        arrays = read(clock_path)
        arrays = arrays.get('arrays', arrays)
        need(arrays['video_id'] == vid and arrays['source_sha256'] == record['source_sha256'] == meta['source_sha256'] and
             len(arrays['native_pts_ticks']) == arrays['n_frames'] == record['n_frames'] == meta['n_frames'],
             'Original source/full-clock identity or frame denominator differs')
        ticks, tick = arrays['native_pts_ticks'], F(arrays['raw_time_base'])
        need(ticks and tick > 0 and all(type(x) is int for x in ticks) and
             all(a < b for a, b in zip(ticks, ticks[1:])) and ticks[0] == arrays['raw_first_pts_ticks'],
             'Original complete exact integer frame PTS/origin invalid')
        raw_end, ends = None, arrays['native_frame_end_pts_ticks']
        terminal = record['terminal_evidence']
        if ends is None:
            need(record['clock_branch'] == 'CFR_LEGACY' and record.get('cfr_eligible') is True and
                 terminal['kind'] == 'LEGACY_CFR_N_DIV_FPS' and terminal['native_packet_endpoint_proven'] is False,
                 'Null terminal is not explicit old CFR planning-only evidence')
            counts['old_CFR_nominal_only'] += 1
        else:
            need(isinstance(ends, list) and len(ends) == len(ticks) and type(ends[-1]) is int and
                 ends[-1] > ticks[-1] and terminal['kind'] == 'NATIVE_LAST_FRAME_PACKET_DURATION',
                 'Old explicit native endpoint evidence invalid; no fallback')
            raw_end = str(ends[-1]*tick)
            counts['old_explicit_native_end'] += 1
        for holder in (meta, record):
            if holder.get('source_bytes') is not None:
                need(holder['source_bytes'] == info['bytes'], 'Old source byte count differs')
        sources.append(dict(video_id=vid, source_path=str(path), source_sha256=meta['source_sha256'],
            source_stat=info, n_frames=len(ticks), width=meta['width'], height=meta['height'],
            clock_array_ref=clock_binding, clock_branch=record['clock_branch'],
            original_raw_time_base_exact=str(tick), original_raw_first_frame_pts_exact=str(ticks[0]*tick),
            original_raw_last_frame_pts_exact=str(ticks[-1]*tick), old_explicit_raw_end_exact=raw_end,
            old_terminal_evidence=terminal, original_clock_not_modified=True))
    need(sum(s['source_stat']['bytes'] for s in sources) == SOURCE_BYTES and
         counts == dict(old_explicit_native_end=10, old_CFR_nominal_only=416), 'Fixed source byte/terminal-branch scope differs')
    code = {p.name: ref(p) for p in sorted((ROOT/'code').glob('*.py'))}
    save(ROOT/'registration_01.json', dict(schema=SCHEMA,
        status='FROZEN_BEFORE_FIRST_SOURCE_HASH_OR_PACKET_MEASUREMENT', utc=utc(), source_count=426,
        source_bytes=SOURCE_BYTES, original_plan_ref=plan_ref, original_clock_registry_ref=registry_ref,
        code_files=code, sources=sources, terminal_branches=counts, CPU_only=True,
        main_agent_first426_packet_measurement_approved=True,
        purpose='Actual compressed-packet terminal witness only; no new full-frame clock or input qualification',
        source_order='original video_id numeric ascending; all fixed426 ordinary-format failures retained',
        source_execution='serial; does not reserve or interrupt external CPU/GPU tasks',
        budget=dict(new_sources=0, network_payload_bytes=0, source_payload_bytes=SOURCE_BYTES,
                    source_SHA_passes_per_attempt=1, AV_open_demux_passes_per_attempt=1,
                    planned_two_pass_logical_media_bytes=2*SOURCE_BYTES, GPU_seconds=0,
                    frame_decodes=0, RGB_outputs=0, processor_calls=0, model_calls=0),
        no_successful_source_remeasurement=True, no_nominal_or_container_duration_fallback=True,
        deadline_before_new_measurement_start=DEADLINE.isoformat(), old_files_not_modified=True,
        predictions_GT_labels_scores_read=False))
    return dict(status='REGISTERED_FIRST426_PACKET_WITNESS_CPU_ONLY', registration_sha256=sha(ROOT/'registration_01.json'),
                source_count=426, source_bytes=SOURCE_BYTES, terminal_branches=counts)


def measure_source(source):
    import av
    path = safe_file(source['source_path'], MEDIA)
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
    fd = os.open(path, flags)
    with os.fdopen(fd, 'rb', closefd=True) as stream:
        need(snapshot(os.fstat(stream.fileno())) == source['source_stat'], 'Source stat changed before its first read')
        actual_sha, bytes_read = sha_stream(stream)
        need(actual_sha == source['source_sha256'] and bytes_read == source['source_stat']['bytes'], 'Source SHA/bytes changed; stop ALL remaining sources')
        need(snapshot(os.fstat(stream.fileno())) == source['source_stat'], 'Source changed while hashing')
        stream.seek(0)
        matches, max_pts, counted, no_pts, payload_bytes = [], None, 0, 0, 0
        with av.open(stream, mode='r') as container:
            video = list(container.streams.video)
            if len(video) != 1:
                raise PacketUnavailable('Exactly one video stream required; no stream fallback')
            selected = video[0]
            stream_meta = dict(index=selected.index, type=selected.type, time_base_exact=str(selected.time_base),
                codec_name=selected.codec_context.name, width=selected.codec_context.width,
                height=selected.codec_context.height)
            if [stream_meta['width'], stream_meta['height']] != [source['width'], source['height']]:
                raise IdentityChanged('Actual video stream geometry differs from the original source metadata')
            for packet in container.demux(selected):
                counted += 1
                payload_bytes += packet.size
                if packet.pts is None:
                    no_pts += 1
                    continue
                if packet.time_base is None:
                    raise PacketUnavailable('Display packet has no actual time base')
                point = F(packet.pts)*F(packet.time_base)
                max_pts = point if max_pts is None else max(max_pts, point)
                if point == F(source['original_raw_last_frame_pts_exact']):
                    compressed = bytes(packet)
                    if len(compressed) != packet.size:
                        raise PacketUnavailable('Matching packet payload size differs')
                    matches.append(packet_row(packet.pts, packet.duration, str(packet.time_base), packet.size,
                                              packet.stream.index, hashlib.sha256(compressed).hexdigest()))
        need(snapshot(os.fstat(stream.fileno())) == source['source_stat'] and
             snapshot(path.stat()) == source['source_stat'], 'Source identity changed during packet demux')
    evidence = dict(actual_source_sha256=actual_sha, source_SHA_read_bytes=bytes_read,
                    video_stream=stream_meta, AV_open_calls=1, demux_calls=1, video_packets_observed=counted,
                    packets_without_display_pts=no_pts, compressed_video_payload_bytes_observed=payload_bytes,
                    matching_packets=matches, max_display_packet_pts_exact=str(max_pts) if max_pts is not None else None,
                    actual_frame_decode_calls=0, PyAV_version=av.__version__)
    try:
        value = resolve(matches, max_pts, source['original_raw_last_frame_pts_exact'],
                        source['original_raw_first_frame_pts_exact'], source['old_explicit_raw_end_exact'])
    except (PacketUnavailable, TypeError) as error:
        return dict(status='FAIL_PACKET_TERMINAL_WITNESS_NO_FALLBACK', error=str(error), observations=evidence)
    value.update(video_id=source['video_id'], source_path=source['source_path'], source_sha256=actual_sha,
                 source_bytes=bytes_read, clock_array_ref=source['clock_array_ref'],
                 original_clock_branch=source['clock_branch'], observations=evidence)
    return value


def run():
    host()
    reg_path = ROOT/'registration_01.json'
    reg = read(reg_path)
    need(reg['schema'] == SCHEMA and reg['main_agent_first426_packet_measurement_approved'] is True and
         reg['CPU_only'] is True and dt.datetime.now(dt.timezone.utc) < DEADLINE, 'First CPU measurement scope/deadline not accepted')
    for binding in [reg['original_plan_ref'], reg['original_clock_registry_ref'], *reg['code_files'].values()]:
        need(sha(binding['path']) == binding['sha256'], 'Frozen code/reference bytes changed')
    check = read(ROOT/'pure_check_01.json')
    need(check['status'].startswith('PASS_NEW_EXACT_PACKET_') and check['code_files'] == reg['code_files'], 'First pure packet check not bound to exact code')
    out = ROOT/'run_01'
    out.mkdir(exist_ok=False)
    started = time.monotonic()
    save(out/'launch_claim.json', dict(status='FIRST_FIXED426_PACKET_MEASUREMENT_CLAIM', pid=os.getpid(), parent_pid=os.getppid(),
        argv=sys.argv, registration_sha256=sha(reg_path), utc=utc(), CPU_only=True, source_serial=True,
        frame_decodes=0, processor_calls=0, model_calls=0))
    refs, failures, measured = {}, {}, 0
    fatal = None
    try:
        for source in reg['sources']:
            vid = source['video_id']
            folder = out/'sources'/vid
            folder.mkdir(parents=True, exist_ok=False)
            save(folder/'launch.json', dict(video_id=vid, utc=utc(), source=source, pid=os.getpid(), first_attempt=True))
            step = time.monotonic()
            try:
                binding = source['clock_array_ref']
                need(sha(binding['path']) == binding['sha256'], 'Original source clock array changed')
                result = measure_source(source)
            except IdentityChanged:
                raise
            except Exception as error:
                result = dict(status='FAIL_PACKET_TERMINAL_MEASUREMENT_ERROR_NO_FALLBACK', error=repr(error),
                              traceback=traceback.format_exc(), video_id=vid, frame_decode_calls=0)
            result.update(CPU_wall_seconds=time.monotonic()-step, utc=utc(), original_files_modified=False)
            save(folder/'terminal.json', result)
            measured += 1
            binding = dict(path=str(folder/'terminal.json'), sha256=sha(folder/'terminal.json'))
            (refs if result['status'].startswith('PASS_') else failures)[vid] = binding
            if measured % 25 == 0 or measured == 426:
                print(json.dumps(dict(progress=measured, success=len(refs), failure=len(failures)), sort_keys=True), flush=True)
    except BaseException as error:
        fatal = dict(error=repr(error), traceback=traceback.format_exc(), utc=utc(), active_source=source['video_id'])
        if not (folder/'terminal.json').exists():
            save(folder/'terminal.json', dict(status='FATAL_SOURCE_IDENTITY_CHANGED_ALL_STOP', **fatal,
                CPU_wall_seconds=time.monotonic()-step, old_source_not_modified=True))
        save(out/'failure.json', dict(status='STOP_ALL_REMAINING_PRESERVE_EVERY_SUCCESS', **fatal, successes=refs,
            ordinary_failures=failures, measured_sources=measured, successful_source_attempts_must_not_repeat=True))
    complete = dict(schema=SCHEMA,
        status='COMPLETE_FIRST426_PACKET_WITNESS_AGGREGATE_NOT_FULL_FRAME_DECODE' if fatal is None else 'STOP_SOURCE_IDENTITY_OR_UNEXPECTED_FATAL',
        registered_sources=426, attempted_source_terminal_count=measured+(1 if fatal is not None else 0),
        successful_sources=len(refs), ordinary_failed_sources=len(failures), remaining_unattempted_sources=426-measured-(1 if fatal else 0),
        success_terminal_refs=refs, failure_terminal_refs=failures, fatal=fatal,
        registration_ref=dict(path=str(reg_path), sha256=sha(reg_path)), pure_check_ref=dict(path=str(ROOT/'pure_check_01.json'),sha256=sha(ROOT/'pure_check_01.json')),
        CPU_wall_seconds=time.monotonic()-started, process_CPU_seconds=time.process_time(), peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        frame_decode_calls=0, RGB_outputs=0, processor_calls=0, model_calls=0, GPU_seconds=0,
        new_full_frame_PTS_claim=False, old_clocks_modified=False, successes_must_not_repeat=True,
        future_independent_frame_PTS_and_duration_equality_required=True, utc=utc())
    save(out/'completion.json', complete)
    print(json.dumps({k:complete[k] for k in ('status','successful_sources','ordinary_failed_sources','remaining_unattempted_sources','CPU_wall_seconds')}, sort_keys=True), flush=True)
    return 0 if fatal is None else 2


def pure():
    host()
    from check_packet_contract_01 import main
    value = main()
    value['code_files'] = {p.name: ref(p) for p in sorted((ROOT/'code').glob('*.py'))}
    save(ROOT/'pure_check_01.json', value)
    print(json.dumps(dict(status=value['status'], pure_check_sha256=sha(ROOT/'pure_check_01.json')), sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=('pure','freeze','run'))
    args = parser.parse_args()
    if args.operation == 'freeze':
        print(json.dumps(freeze(), sort_keys=True))
    elif args.operation == 'pure':
        pure()
    else:
        sys.exit(run())
