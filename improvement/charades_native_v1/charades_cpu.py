"""New Charades native-clock/native64 CPU preparation; never loads a model.

One source has a complete sequential clock decode, strict author-second domain
check, then one sequential RGB decode. Each new window is processor-encoded
once. Successful clocks and all partial outputs survive later failures.
"""
from bisect import bisect_left
from fractions import Fraction as F
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import re
import socket
import sys
import time

from charades_common import (ROOT, RUN, LEGACY, read, save, sha, utc, require,
                            check_deadline, resource_snapshot)

NATIVE_FRAMES = 64
MAX_INPUT_TOKENS = 16384
HELPER_DIRECTORY = Path('/home/inspur/aic_video_work/twenty_hour_five_20261014_v1/local_boundary_v1/code')
HELPER_FILES = {
    'lb_io.py': 'c1a1c459a022c08d248aab220c72b4784158a2230e51c695996d57794f1bf614',
    'lb_contract.py': '7ddd9d2aa0439a1bd784c7fab5e2769c4668b03597e844016b7dfc0d0de57077',
}
_PROCESSOR_RUNTIME = None


class NativeEndpointError(ValueError):
    """Native source/author-second domain failure, never processor/network."""


def _canonical_sha(value):
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(',', ':'), allow_nan=False).encode()
    return hashlib.sha256(payload).hexdigest()


def _inside(path, root):
    path = Path(path).resolve()
    require(path.is_relative_to(Path(root).resolve()), 'New Charades path escaped its independent ROOT')
    return path


def _source_bindings(source, media_receipt, reference, bindings):
    source_id = source['source_id']
    require(isinstance(source_id, str) and re.fullmatch(r'[A-Za-z0-9_-]{1,80}', source_id),
            'Frozen safe Charades source ID required')
    require(isinstance(source['role'], str) and type(source['rank']) is int,
            'Frozen source role/rank required')
    require(type(media_receipt['bytes']) is int and media_receipt['bytes'] > 0,
            'Actual admitted media byte count required')
    return dict(registered_bindings=bindings,
        source=dict(source_id=source_id, role=source['role'], rank=source['rank']),
        media_receipt=dict(path=str(Path(media_receipt['path']).resolve()),
                           bytes=media_receipt['bytes'], sha256=media_receipt['sha256']),
        reference_metadata_sha256=_canonical_sha(reference),
        preparation_code_sha256=sha(Path(__file__)), tensor_cache_helper_files=HELPER_FILES)


def _measure_clock(path, source_id, receipt):
    """First complete decode: native PTS/last positive duration, no RGB."""
    import av
    points, geometry, last_duration = [], None, None
    with av.open(str(path)) as container:
        if len(container.streams.video) != 1:
            raise NativeEndpointError('Ambiguous original video stream')
        stream = container.streams.video[0]
        stream.thread_count = 1
        rate = stream.average_rate
        if stream.time_base is None or rate is None or F(rate) <= 0:
            raise NativeEndpointError('Missing exact original native time base/nominal rate')
        for frame in container.decode(stream):
            if len(points) % 64 == 0:
                check_deadline()
            if frame.pts is None or frame.time_base is None:
                raise NativeEndpointError('Original frame has no exact native PTS/time base')
            point = F(frame.pts)*F(frame.time_base)
            if point < 0 or (points and point <= points[-1]):
                raise NativeEndpointError('Original full native PTS is not strictly increasing')
            shape = (frame.width, frame.height)
            if geometry is None:
                geometry = shape
            if shape != geometry or min(shape) <= 0:
                raise NativeEndpointError('Original native frame geometry changed')
            points.append(point)
            duration = getattr(frame, 'duration', None)
            last_duration = F(duration)*F(frame.time_base) if duration is not None else None
        if not points:
            raise NativeEndpointError('Original video has no physical frames')
        origin = points[0]
        normalized = [p-origin for p in points]
        last_valid = last_duration is not None and last_duration > 0
        physical_end = normalized[-1]+last_duration if last_valid else None
        # The measured original and diagnostic normalized clocks are both kept.
        # A nonzero original origin is rejected later, never used to shift labels.
        return dict(source_id=source_id, source_name=source_id,
            source_path=str(path), source_bytes=receipt['bytes'], source_sha256=receipt['sha256'],
            original_exact_pts=list(map(str, points)), normalized_exact_pts=list(map(str, normalized)),
            first_original_pts_exact=str(origin), n_frames=len(points), native_frames=len(points),
            width=geometry[0], height=geometry[1], fps_num=F(rate).numerator, fps_den=F(rate).denominator,
            video_stream_index=stream.index, stream_time_base_exact=str(F(stream.time_base)),
            stream_start_time=stream.start_time,
            container_start_time_microseconds_diagnostic_only=container.start_time,
            container_duration_microseconds_diagnostic_only=container.duration,
            last_frame_duration_exact=str(last_duration) if last_duration is not None else None,
            physical_end_exact=str(physical_end) if physical_end is not None else None,
            original_physical_end_exact=str(points[-1]+last_duration) if last_valid else None,
            positive_last_frame_duration_verified=last_valid,
            original_zero_origin_verified=origin == 0 and stream.start_time in (0, None),
            physical_endpoint_evidence=dict(kind='LAST_NATIVE_FRAME_PTS_PLUS_POSITIVE_DURATION',
                last_normalized_pts_exact=str(normalized[-1]),
                last_frame_duration_exact=str(last_duration) if last_duration is not None else None),
            decoder_version=av.__version__, AV_thread_count=1, new_complete_clock_decodes=1,
            author_label_shift_applied=False, label_interpolation=False,
            nominal_fps_or_container_duration_used_for_end=False, audio_observed=False)


def _validate_reference(clock, reference):
    """Original author seconds; no epsilon, endpoint clipping or time stretching."""
    if clock['positive_last_frame_duration_verified'] is not True:
        raise NativeEndpointError('Actual positive last-frame duration is unavailable')
    if clock['original_zero_origin_verified'] is not True:
        raise NativeEndpointError('Original author-second zero origin is unverified; no guessed offset')
    points = [F(p) for p in clock['normalized_exact_pts']]
    end = F(clock['physical_end_exact'])
    if not points or points[0] != 0 or end <= points[-1]:
        raise NativeEndpointError('Actual complete zero-origin source/last-duration clock is invalid')
    actions = reference['actions']
    if not isinstance(actions, list):
        raise NativeEndpointError('Original author actions are not an explicit list')
    mapped = []
    for index, action in enumerate(actions):
        check_deadline()
        if not isinstance(action['class_id'], str) or not action['class_id']:
            raise NativeEndpointError('Original author action class ID is invalid')
        if not isinstance(action['start_exact'], str) or not isinstance(action['end_exact'], str):
            raise NativeEndpointError('Original author seconds must retain their exact source text')
        try:
            first, last = F(action['start_exact']), F(action['end_exact'])
        except (ValueError, ZeroDivisionError, TypeError) as error:
            raise NativeEndpointError('Original author action seconds are not exact finite values') from error
        if not 0 <= first < last <= end:
            raise NativeEndpointError('Original author endpoint lies outside actual native physical source: '
                                      +str(index)+' '+str(first)+'..'+str(last)+' / '+str(end))
        lo, hi = bisect_left(points, first), bisect_left(points, last)
        if not 0 <= lo < hi <= len(points):
            raise NativeEndpointError('Positive author action contains no actual native source frame')
        mapped.append(dict(action_index=index, class_id=action['class_id'],
            start_exact=str(first), end_exact=str(last), native_range=[lo, hi]))
    return dict(status='PASS_STRICT_ORIGINAL_AUTHOR_SECONDS_NATIVE_DOMAIN_NOT_HIGHLIGHT_GT',
        actions=mapped, action_count=len(actions), original_empty_actions_retained=not actions,
        author_length_raw_diagnostic_only=reference['author_length_raw'],
        actual_physical_end_exact=str(end), source_frame_count=len(points),
        seconds_shifted=False, labels_stretched=False, endpoint_clipped=False,
        epsilon_added=False, labels_used_for_sampling_or_prompt=False)


def _windows(clock):
    points = [F(p) for p in clock['normalized_exact_pts']]
    end = F(clock['physical_end_exact'])
    count = (end.numerator+30*end.denominator-1)//(30*end.denominator)
    result = []
    for index in range(count):
        lo, hi = end*index/count, end*(index+1)/count
        first, stop = bisect_left(points, lo), bisect_left(points, hi)
        if stop-first < NATIVE_FRAMES:
            raise NativeEndpointError('Fixed <=30s equal window has fewer than 64 distinct physical frames')
        ordinals = [first+i*(stop-first-1)//63 for i in range(NATIVE_FRAMES)]
        if len(set(ordinals)) != NATIVE_FRAMES:
            raise NativeEndpointError('Integer-floor64 plan repeated an actual source frame')
        result.append(dict(index=index, start_exact=str(lo), end_exact=str(hi),
            eligible_first=first, eligible_stop=stop, source_frame_ordinals=ordinals,
            sample_exact_pts=[str(points[i]) for i in ordinals]))
    return result


def _load_cpu_runtime():
    global _PROCESSOR_RUNTIME
    if _PROCESSOR_RUNTIME is not None:
        return _PROCESSOR_RUNTIME
    require(socket.gethostname() == 'inspur-NP5570M5' and sys.platform == 'linux',
            'Real Charades CPU preparation is confined to the verified Linux host')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'This CPU process must explicitly hide CUDA')
    for filename, digest in HELPER_FILES.items():
        require(sha(HELPER_DIRECTORY/filename) == digest, 'Frozen original lossless tensor helper changed')
    sys.path.insert(0, str(HELPER_DIRECTORY))
    existing = sys.modules.get('lb_contract')
    if existing is not None:
        require(Path(existing.__file__).resolve() == (HELPER_DIRECTORY/'lb_contract.py').resolve(),
                'Frozen tensor helper contract was shadowed')
    name = '_charades_native_frozen_tensor_cache'
    spec = importlib.util.spec_from_file_location(name, HELPER_DIRECTORY/'lb_io.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    require(helper.RUN.resolve() == Path(RUN).resolve() and helper.LEGACY.resolve() == Path(LEGACY).resolve(),
            'Original trained B runtime roots differ')
    import torch
    torch.set_num_threads(1)
    if torch.get_num_interop_threads() != 1:
        torch.set_num_interop_threads(1)
    require(not torch.cuda.is_initialized(), 'CPU input preparation unexpectedly initialized CUDA')
    # New module is charades_common, so the original engine's own common import
    # remains intact. The helper verifies all original dependency file paths.
    runtime, processor, identity = helper.cpu_runtime()
    require(torch.get_num_threads() == 1 and torch.get_num_interop_threads() == 1,
            'Frozen serial torch CPU protocol changed')
    _PROCESSOR_RUNTIME = runtime, processor, helper, identity
    return _PROCESSOR_RUNTIME


def _check_capacity(clock, processor, remaining_windows):
    snapshot = resource_snapshot()
    rgb_bytes = NATIVE_FRAMES*clock['height']*clock['width']*3
    explicit_size = processor.video_processor.size
    require(set(explicit_size) == {'shortest_edge', 'longest_edge'}, 'Original explicit processor video size changed')
    tensor_upper = explicit_size['longest_edge']*3*4
    # Derived byte estimates, not a fixed GiB/resource threshold. Original dtype
    # is float32 here; no reduced precision is introduced to make capacity fit.
    memory_estimate = 2*rgb_bytes+2*tensor_upper
    disk_estimate = remaining_windows*(rgb_bytes+tensor_upper+(rgb_bytes+tensor_upper)//1000+65536)
    require(snapshot['mem_available_bytes'] > memory_estimate,
            'Current available memory cannot cover the upcoming native64 CPU allocations')
    require(snapshot['disk_available_bytes'] > disk_estimate,
            'Current available disk cannot cover conservative remaining native64 outputs')
    return dict(snapshot=snapshot, upcoming_memory_bytes_estimate=memory_estimate,
                remaining_output_bytes_estimate=disk_estimate,
                estimates_derive_from_actual_geometry_and_original_processor_budget=True)


def _write_window(source, receipt, clock, window, arrays, folder, bindings,
                  runtime, processor, helper, runtime_identity, capacity):
    import numpy as np
    import torch
    started = time.monotonic()
    folder.mkdir(exist_ok=False)
    case_id = 'CH_'+source['source_id']+'_W'+str(window['index']).zfill(3)
    pixels = [hashlib.sha256(a.tobytes()).hexdigest() for a in arrays]
    array_path = folder/'frames.npz'
    with array_path.open('xb') as destination:
        np.savez_compressed(destination, rgb=arrays)
    meta_path = folder/'input.json'
    meta = dict(case_id=case_id, source_name=source['source_id'], source_id=source['source_id'],
        source_group='Charades:'+source['source_id'], source_role=source['role'], source_rank=source['rank'],
        source_path=str(Path(receipt['path']).resolve()), source_sha256=receipt['sha256'], source_bytes=receipt['bytes'],
        source_total_frames=clock['n_frames'], width=clock['width'], height=clock['height'],
        fps_num=clock['fps_num'], fps_den=clock['fps_den'],
        all_source_exact_pts=clock['normalized_exact_pts'],
        original_clock_origin_exact=clock['first_original_pts_exact'],
        window_start=window['start_exact'], window_end=window['end_exact'],
        source_frame_ordinals=window['source_frame_ordinals'], sample_exact_pts=window['sample_exact_pts'],
        pixel_sha256=pixels, frame_array_path=str(array_path), frame_array_sha256=sha(array_path),
        native_clock_path=bindings['native_clock_path'], native_clock_sha256=bindings['native_clock_sha256'],
        audio_observed=False, reference_available_to_inference=False,
        reference_labels_used_for_sampling=False, bindings=bindings)
    save(meta_path, meta)
    frames = arrays, meta['source_frame_ordinals'], meta['sample_exact_pts']
    encoding_started = time.monotonic()
    encoded, evidence = runtime.encode(processor, meta, frames, F(meta['window_start']), runtime.EMPTY_PROMPT)
    processor_seconds = time.monotonic()-encoding_started
    tokens = int(encoded['input_ids'].shape[1])
    require(tokens <= MAX_INPUT_TOKENS and evidence['physical_frames'] == NATIVE_FRAMES,
            'Actual original B native64/token budget failed; no truncation/padding fallback')
    require(all(isinstance(t, torch.Tensor) and t.device.type == 'cpu' for t in encoded.values()),
            'Actual original processor input was not a CPU tensor dict')
    tensor_path = folder/'encoded_tensors.pt.gz'
    compression_started = time.monotonic()
    helper.save_tensor_cache(tensor_path, encoded)
    compression_seconds = time.monotonic()-compression_started
    decode_started = time.monotonic()
    restored = helper.load_tensor_cache(tensor_path)
    decompression_seconds = time.monotonic()-decode_started
    require(runtime.tensor_signature(restored) == evidence['tensor_signature'],
            'Lossless gzip cache did not preserve the actual CPU input tensor signature')
    require(not torch.cuda.is_initialized(), 'CPU encode/cache unexpectedly initialized CUDA')
    proof_path = folder/'cpu_input.json'
    proof = dict(status='PASS_CPU_ORIGINAL_B_NATIVE64_PROCESSOR_INPUT', case_id=case_id,
        source_name=source['source_id'], input_path=str(meta_path), input_sha256=sha(meta_path),
        input_evidence=evidence, input_tokens=tokens,
        encoded_tensor_path=str(tensor_path), encoded_tensor_sha256=sha(tensor_path),
        encoded_tensor_format=helper.TENSOR_CACHE_FORMAT, encoded_tensor_compression_level=1,
        encoded_tensor_file_bytes=tensor_path.stat().st_size, rgb_npz_file_bytes=array_path.stat().st_size,
        logical_tensor_payload_bytes=sum(t.numel()*t.element_size() for t in encoded.values()),
        processor_seconds=processor_seconds, tensor_compression_seconds=compression_seconds,
        tensor_decompression_check_seconds=decompression_seconds,
        window_write_encode_seconds=time.monotonic()-started,
        process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        CPU_only=True, CUDA_initialized=False, actual_new_processor_encodes=1,
        new_model_calls=0, new_optimizer_updates=0, bindings=bindings,
        original_b_processor_runtime=runtime_identity, dynamic_capacity_receipt=capacity)
    save(proof_path, proof)
    del restored, encoded, frames
    return dict(case_id=case_id, source_name=source['source_id'],
        input_path=str(meta_path), input_sha256=sha(meta_path),
        proof_path=str(proof_path), proof_sha256=sha(proof_path), input_tokens=tokens,
        encoded_tensor_path=str(tensor_path), encoded_tensor_sha256=proof['encoded_tensor_sha256'],
        encoded_tensor_format=helper.TENSOR_CACHE_FORMAT,
        encoded_tensor_file_bytes=proof['encoded_tensor_file_bytes'], rgb_npz_file_bytes=proof['rgb_npz_file_bytes'],
        process_peak_rss_kib=proof['process_peak_rss_kib'],
        processor_seconds=processor_seconds, tensor_compression_seconds=compression_seconds)


def _decode_rgb_once(source, receipt, clock, windows, source_out, bindings, proofs):
    """Second decode is sequential and verifies every original PTS again."""
    import av
    import numpy as np
    runtime, processor, helper, identity = _load_cpu_runtime()
    original = [F(p) for p in clock['original_exact_pts']]
    index, images, cursor = 0, [], 0
    capacities = []
    capacity = _check_capacity(clock, processor, len(windows))
    capacities.append(capacity)
    with av.open(receipt['path']) as container:
        require(len(container.streams.video) == 1, 'Original source stream changed after clock measurement')
        stream = container.streams.video[0]
        stream.thread_count = 1
        require(stream.index == clock['video_stream_index'] and stream.time_base is not None and
                str(F(stream.time_base)) == clock['stream_time_base_exact'] and stream.average_rate is not None and
                F(stream.average_rate) == F(clock['fps_num'], clock['fps_den']),
                'Original native stream/time base/rate changed after complete clock')
        for ordinal, frame in enumerate(container.decode(stream)):
            if ordinal % 64 == 0:
                check_deadline()
            require(ordinal < len(original) and frame.pts is not None and frame.time_base is not None,
                    'Second sequential decode native-frame denominator changed')
            require(F(frame.pts)*F(frame.time_base) == original[ordinal] and
                    (frame.width, frame.height) == (clock['width'], clock['height']),
                    'Second sequential RGB decode differs from accepted complete original clock')
            cursor += 1
            if index >= len(windows) or ordinal not in windows[index]['source_frame_ordinals']:
                continue
            image = frame.to_ndarray(format='rgb24')
            require(image.dtype == np.uint8 and image.shape == (clock['height'], clock['width'], 3),
                    'Actual original RGB dtype/geometry changed')
            images.append(image)
            if ordinal == windows[index]['source_frame_ordinals'][-1]:
                require(len(images) == NATIVE_FRAMES, 'Registered native64 source frame was not recovered')
                arrays = np.stack(images)
                folder = source_out/('W'+str(index).zfill(3))
                entry = _write_window(source, receipt, clock, windows[index], arrays, folder, bindings,
                                      runtime, processor, helper, identity, capacity)
                proofs.append(entry)
                print(json.dumps(dict(source_id=source['source_id'], accepted_windows=len(proofs),
                    source_windows=len(windows), input_tokens=entry['input_tokens'])), flush=True)
                del arrays, images
                images = []
                index += 1
                if index < len(windows):
                    capacity = _check_capacity(clock, processor, len(windows)-index)
                    capacities.append(capacity)
    require(cursor == len(original) and index == len(windows) and not images,
            'Complete sequential RGB/source input denominator failed')
    return identity, capacities


def prepare_source(source, media_receipt, reference, source_out, bindings):
    """Return one source's immutable completion; preserve every old success."""
    require(socket.gethostname() == 'inspur-NP5570M5' and sys.platform == 'linux',
            'Charades real media/CPU preparation must stay on the Linux host')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU preparation child must hide CUDA only for itself')
    check_deadline()
    source_out = _inside(source_out, ROOT)
    path = _inside(media_receipt['path'], ROOT)
    require(path.is_file() and path.stat().st_size == media_receipt['bytes'] and sha(path) == media_receipt['sha256'],
            'New admitted original media identity changed before CPU preparation')
    stage_bindings = _source_bindings(source, media_receipt, reference, bindings)
    completion_path = source_out/'completion.json'
    if completion_path.exists():
        completed = read(completion_path)
        require(completed['status'] == 'PASS_CHARADES_SOURCE_NATIVE64_CPU_INPUTS_NOT_GPU_ADMISSION' and
                completed['bindings'] == stage_bindings,
                'Previously successful Charades CPU source binding changed')
        require(sha(completed['native_clock_path']) == completed['native_clock_sha256'],
                'Previously successful complete original clock changed')
        for entry in completed['proofs']:
            require(sha(entry['proof_path']) == entry['proof_sha256'] and
                    sha(entry['input_path']) == entry['input_sha256'] and
                    sha(entry['encoded_tensor_path']) == entry['encoded_tensor_sha256'],
                    'Previously successful actual CPU proof/input/cache changed')
            old_meta = read(entry['input_path'])
            require(sha(_inside(old_meta['frame_array_path'], ROOT)) == old_meta['frame_array_sha256'],
                    'Previously successful native RGB cache changed')
        return completed
    source_out.mkdir(parents=True, exist_ok=True)
    require(not (source_out/'cpu_launch.json').exists() and not (source_out/'failure.json').exists(),
            'An existing failed/interrupted CPU source requires explicit independent recovery')
    started = time.monotonic()
    save(source_out/'cpu_launch.json', dict(pid=os.getpid(), utc=utc(), bindings=stage_bindings,
        CPU_only=True, new_model_calls=0, new_optimizer_updates=0, resource_snapshot=resource_snapshot()))
    proofs, clock_path, clock_saved, stage = [], source_out/'native_clock.json', False, 'CLOCK'
    try:
        require(not clock_path.exists(), 'A prior successful clock must be reused by explicit recovery, not decoded again')
        clock = _measure_clock(path, source['source_id'], media_receipt)
        save(clock_path, dict(status='COMPLETE_ORIGINAL_NATIVE_CLOCK_MEASURED_BEFORE_DOMAIN_ADMISSION',
            clock=clock, bindings=stage_bindings, CPU_only=True, new_model_calls=0, new_optimizer_updates=0))
        clock_saved = True
        stage = 'AUTHOR_NATIVE_DOMAIN'
        domain = _validate_reference(clock, reference)
        domain_path = source_out/'reference_validation.json'
        save(domain_path, dict(domain, bindings=stage_bindings, native_clock_sha256=sha(clock_path)))
        stage = 'NATIVE64_WINDOW_PLAN'
        windows = _windows(clock)
        plan_path = source_out/'windows.json'
        save(plan_path, dict(status='PASS_FIXED_NATIVE64_WINDOWS_NOT_PROCESSOR_ADMISSION', windows=windows,
            native_clock_sha256=sha(clock_path), reference_labels_used_for_windows=False, bindings=stage_bindings))
        actual_bindings = dict(stage_bindings, native_clock_path=str(clock_path), native_clock_sha256=sha(clock_path),
            reference_validation_sha256=sha(domain_path), window_plan_sha256=sha(plan_path))
        stage = 'SEQUENTIAL_RGB_AND_ACTUAL_CPU_PROCESSOR'
        identity, capacities = _decode_rgb_once(source, media_receipt, clock, windows, source_out, actual_bindings, proofs)
        stage = 'COMPLETE_SOURCE_ADMISSION'
        require(path.stat().st_size == media_receipt['bytes'], 'Original media size changed during CPU preparation')
        completed = dict(status='PASS_CHARADES_SOURCE_NATIVE64_CPU_INPUTS_NOT_GPU_ADMISSION',
            source_id=source['source_id'], role=source['role'], rank=source['rank'], bindings=stage_bindings,
            native_clock_path=str(clock_path), native_clock_sha256=sha(clock_path),
            reference_validation_path=str(domain_path), reference_validation_sha256=sha(domain_path),
            window_plan_path=str(plan_path), window_plan_sha256=sha(plan_path), proofs=proofs,
            accepted_windows=len(proofs), actual_new_processor_encodes=len(proofs),
            original_b_processor_runtime=identity, CPU_only=True, CUDA_initialized=False,
            AV_thread_count=1, torch_thread_count=1, torch_interop_thread_count=1,
            full_native_clock_decodes=1, sequential_rgb_decodes=1,
            author_empty_actions_retained=not reference['actions'],
            new_model_calls=0, new_optimizer_updates=0, GPU_launch_admitted=False,
            source_wall_seconds=time.monotonic()-started,
            process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            output_file_bytes=sum(p.stat().st_size for p in source_out.rglob('*') if p.is_file()),
            capacity_receipts=capacities, utc=utc())
        save(completion_path, completed)
        return completed
    except BaseException as error:
        save(source_out/'failure.json', dict(status='FAILED_CHARADES_SOURCE_KEEP_CLOCK_AND_SUCCESSFUL_INPUTS',
            source_id=source['source_id'], stage=stage, bindings=stage_bindings,
            error_type=type(error).__name__, error=str(error),
            engineering_native_endpoint_failure=isinstance(error, NativeEndpointError),
            complete_clock_preserved=clock_saved, native_clock_path=str(clock_path) if clock_saved else None,
            native_clock_sha256=sha(clock_path) if clock_saved else None, successful_proofs=proofs,
            new_model_calls=0, new_optimizer_updates=0, CPU_only=True, utc=utc()))
        raise
