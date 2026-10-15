"""Charades v2 partial references and immutable native/CPU success reuse.

Inherited clocks are referenced without decoding. Complete old CPU sources are
referenced without RGB/processor/cache rewrites. New native64 windows retain the
original B prompt; author annotations never select windows or enter inference.
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

from charades_v2_common import (ROOT, V1ROOT, RUN, LEGACY, read, save, sha, utc,
                               require, check_deadline, resource_snapshot)

NATIVE_FRAMES = 64
MAX_INPUT_TOKENS = 16384
HELPER_DIRECTORY = Path('/home/inspur/aic_video_work/twenty_hour_five_20261014_v1/local_boundary_v1/code')
HELPER_FILES = {
    'lb_io.py': 'c1a1c459a022c08d248aab220c72b4784158a2230e51c695996d57794f1bf614',
    'lb_contract.py': '7ddd9d2aa0439a1bd784c7fab5e2769c4668b03597e844016b7dfc0d0de57077',
}
_PROCESSOR_RUNTIME = None
COMPLETION_STATUS = 'PASS_CHARADES_V2_SOURCE_NATIVE64_CPU_INPUTS_PARTIAL_REFERENCE_NOT_GPU_ADMISSION'
OLD_COMPLETION_STATUS = 'PASS_CHARADES_SOURCE_NATIVE64_CPU_INPUTS_NOT_GPU_ADMISSION'


class NativeEndpointError(ValueError):
    """Physical native clock/native64 failure, never annotation or processor."""


def _canonical_sha(value):
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(',', ':'), allow_nan=False).encode()
    return hashlib.sha256(payload).hexdigest()


def _inside(path, root):
    path = Path(path).resolve()
    require(path.is_relative_to(Path(root).resolve()), 'Charades path escaped its explicitly bound ROOT')
    return path


def _source_media_path(source, receipt):
    """Only explicit inherited media may refer to the frozen v1 source root."""
    inherited = 'existing_native_clock_path' in receipt
    root = V1ROOT if inherited else ROOT
    return _inside(receipt['path'], root/'media_01'/source['source_id'])


def _bound_file(path, digest, root):
    path = _inside(path, root)
    require(path.is_file() and sha(path) == digest, 'Frozen inherited artifact identity changed: '+str(path))
    return path


def _source_bindings(source, media_receipt, reference, bindings):
    source_id = source['source_id']
    require(isinstance(source_id, str) and re.fullmatch(r'[A-Za-z0-9_-]{1,80}', source_id),
            'Frozen safe Charades source ID required')
    require(isinstance(source['role'], str) and type(source['rank']) is int,
            'Frozen source role/rank required')
    require(type(media_receipt['bytes']) is int and media_receipt['bytes'] > 0,
            'Actual admitted media byte count required')
    inherited = {}
    for name in ('native_clock', 'CPU_completion'):
        path_key, sha_key = 'existing_'+name+'_path', 'existing_'+name+'_sha256'
        require((path_key in media_receipt) == (sha_key in media_receipt),
                'Inherited artifact path/SHA must be present as a pair')
        if path_key in media_receipt:
            inherited[path_key] = str(Path(media_receipt[path_key]).resolve())
            inherited[sha_key] = media_receipt[sha_key]
    require('existing_CPU_completion_path' not in inherited or 'existing_native_clock_path' in inherited,
            'Old CPU completion requires its complete immutable native clock')
    return dict(registered_bindings=bindings,
        source=dict(source_id=source_id, role=source['role'], rank=source['rank']),
        media_receipt=dict(path=str(Path(media_receipt['path']).resolve()),
                           bytes=media_receipt['bytes'], sha256=media_receipt['sha256']),
        reference_metadata_sha256=_canonical_sha(reference),
        preparation_code_sha256=sha(Path(__file__)), tensor_cache_helper_files=HELPER_FILES,
        inherited_artifacts=inherited, reference_policy='PARTIAL_AUTHOR_ACTION_NATIVE_ELIGIBILITY_V2')


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


def _validate_clock(clock):
    """Physical clock validity remains strict independently of author labels."""
    if clock['positive_last_frame_duration_verified'] is not True:
        raise NativeEndpointError('Actual positive last-frame duration is unavailable')
    if clock['original_zero_origin_verified'] is not True:
        raise NativeEndpointError('Original author-second zero origin is unverified; no guessed offset')
    points = [F(p) for p in clock['normalized_exact_pts']]
    end = F(clock['physical_end_exact'])
    original = [F(p) for p in clock['original_exact_pts']]
    duration = F(clock['last_frame_duration_exact'])
    origin = F(clock['first_original_pts_exact'])
    if (not points or points[0] != 0 or origin != 0 or duration <= 0 or
            end != points[-1]+duration or original != [p+origin for p in points] or
            len(points) != clock['n_frames'] or clock['native_frames'] != len(points) or
            any(a >= b for a, b in zip(points, points[1:]))):
        raise NativeEndpointError('Actual complete zero-origin source/last-duration clock is invalid')
    return points, end


def _validate_reference(clock, reference):
    """Preserve all author text; classify partial eligibility without clipping."""
    points, end = _validate_clock(clock)
    actions = reference['actions']
    require(isinstance(actions, list), 'Original author actions are not an explicit list')
    mapped, eligible = [], 0
    for index, action in enumerate(actions):
        check_deadline()
        require(isinstance(action, dict) and isinstance(action['class_id'], str) and action['class_id'],
                'Original author action class ID is invalid; STOP metadata, do not replace source')
        require(isinstance(action['start_exact'], str) and isinstance(action['end_exact'], str),
                'Original author seconds must retain exact source text; STOP metadata, do not replace source')
        row = dict(action_index=index, class_id=action['class_id'],
            start_exact=action['start_exact'], end_exact=action['end_exact'],
            original_action=dict(action), eligibility='CENSORED_UNKNOWN', scored=False,
            native_range=None, contains_native_frame=None, ordinary=False,
            official_ongoing_definition_assumed=False)
        try:
            first, last = F(action['start_exact']), F(action['end_exact'])
        except (ValueError, ZeroDivisionError, TypeError):
            row['censor_reason'] = 'AUTHOR_ENDPOINT_TEXT_NOT_EXACT_FINITE_SECONDS'
        else:
            if not 0 <= first < last <= end:
                row['censor_reason'] = 'AUTHOR_INTERVAL_NOT_FULLY_IN_PHYSICAL_NATIVE_DOMAIN'
            else:
                lo, hi = bisect_left(points, first), bisect_left(points, last)
                # This registered proxy compares original author-second
                # endpoints. Empty native-frame membership is a diagnostic,
                # never an extra eligibility gate or visible-highlight core.
                row.update(eligibility='FULLY_IN_DOMAIN', scored=True, native_range=[lo, hi],
                           contains_native_frame=lo < hi, censor_reason=None)
                eligible += 1
        mapped.append(row)
    return dict(status='PASS_PARTIAL_AUTHOR_ACTION_ELIGIBILITY_NOT_COMPLETE_HIGHLIGHT_GT',
        actions=mapped, action_count=len(actions), all_action_count=len(actions),
        eligible_action_count=eligible, censored_action_count=len(actions)-eligible,
        fully_in_domain_without_native_frame_count=sum(
            row['eligibility'] == 'FULLY_IN_DOMAIN' and row['contains_native_frame'] is False for row in mapped),
        eligibility_counts=dict(FULLY_IN_DOMAIN=eligible, CENSORED_UNKNOWN=len(actions)-eligible),
        original_empty_actions_retained=not actions, zero_in_domain_source_retained=eligible == 0,
        author_length_raw_diagnostic_only=reference['author_length_raw'],
        actual_physical_end_exact=str(end), source_frame_count=len(points),
        seconds_shifted=False, labels_stretched=False, endpoint_clipped=False,
        epsilon_added=False, labels_used_for_sampling_or_prompt=False,
        original_author_reference_sha256=_canonical_sha(reference),
        whole_source_GT_complete=False, fully_in_domain_union_is_complete_GT=False,
        whole_source_precision_recall_F1_admitted=False, censored_is_ordinary=False,
        censored_is_official_ongoing=False, input_validity_is_model_quality=False,
        eligibility_basis='STRICT_AUTHOR_SECONDS_PHYSICAL_DOMAIN_ONLY',
        endpoint_proxy_is_dense_native_frame_GT=False,
        no_native_frame_action_is_visible_highlight_core=False)


def _inherited_clock(source, receipt, reference):
    """Read a hash-bound full v1 wrapper; no decoder is called."""
    folder = V1ROOT/'native_01'/source['source_id']
    path = _bound_file(receipt['existing_native_clock_path'], receipt['existing_native_clock_sha256'], folder)
    require(path == (folder/'native_clock.json').resolve(), 'Expected exact complete v1 clock wrapper path')
    wrapper = read(path)
    require(wrapper['status'] == 'COMPLETE_ORIGINAL_NATIVE_CLOCK_MEASURED_BEFORE_DOMAIN_ADMISSION',
            'Only a complete immutable v1 measured native clock can be inherited')
    clock = wrapper['clock']
    require(wrapper['bindings']['source'] == dict(source_id=source['source_id'], role=source['role'], rank=source['rank']) and
            wrapper['bindings']['reference_metadata_sha256'] == _canonical_sha(reference) and
            wrapper['bindings']['media_receipt'] == dict(path=str(Path(receipt['path']).resolve()),
                bytes=receipt['bytes'], sha256=receipt['sha256']),
            'Inherited source/media/original author metadata binding differs')
    require(clock['source_id'] == source['source_id'] and clock['source_name'] == source['source_id'] and
            clock['source_sha256'] == receipt['sha256'] and clock['source_bytes'] == receipt['bytes'] and
            Path(clock['source_path']).resolve() == Path(receipt['path']).resolve(),
            'Inherited complete clock/media/source identity differs')
    _validate_clock(clock)
    return clock, path


def _windows(clock):
    points, end = _validate_clock(clock)
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


def _checked_cpu_proofs(source, receipt, clock, clock_path, windows, completed, root):
    """Verify immutable proof/cache bytes and identity without CPU re-encoding."""
    folder = Path(root)/'native_01'/source['source_id']
    require(completed['source_id'] == source['source_id'] and completed['role'] == source['role'] and
            completed['rank'] == source['rank'] and completed['native_clock_path'] == str(clock_path) and
            completed['native_clock_sha256'] == sha(clock_path) and completed['CPU_only'] is True and
            completed['CUDA_initialized'] is False and completed['new_model_calls'] == 0 and
            completed['new_optimizer_updates'] == 0 and completed['GPU_launch_admitted'] is False,
            'Previously successful source/native/CPU identity changed')
    entries = completed['proofs']
    require(len(entries) == len(windows) == completed['accepted_windows'],
            'Previously successful CPU source window denominator changed')
    artifacts = []
    for entry, window in zip(entries, windows):
        check_deadline()
        expected_case = 'CH_'+source['source_id']+'_W'+str(window['index']).zfill(3)
        expected_folder = folder/('W'+str(window['index']).zfill(3))
        require(entry['case_id'] == expected_case and entry['source_name'] == source['source_id'],
                'Previously successful CPU case/source identity changed')
        proof_path = _bound_file(entry['proof_path'], entry['proof_sha256'], expected_folder)
        input_path = _bound_file(entry['input_path'], entry['input_sha256'], expected_folder)
        tensor_path = _bound_file(entry['encoded_tensor_path'], entry['encoded_tensor_sha256'], expected_folder)
        require(proof_path.name == 'cpu_input.json' and input_path.name == 'input.json' and
                tensor_path.name == 'encoded_tensors.pt.gz', 'Unexpected frozen successful CPU artifact paths')
        proof, meta = read(proof_path), read(input_path)
        for key in ('case_id', 'source_name', 'input_path', 'input_sha256', 'input_tokens',
                    'encoded_tensor_path', 'encoded_tensor_sha256', 'encoded_tensor_format'):
            require(proof[key] == entry[key], 'Proof/manifest artifact binding differs: '+key)
        require(proof['status'] == 'PASS_CPU_ORIGINAL_B_NATIVE64_PROCESSOR_INPUT' and
                proof['CPU_only'] is True and proof['CUDA_initialized'] is False and
                proof['actual_new_processor_encodes'] == 1 and proof['new_model_calls'] == 0 and
                proof['new_optimizer_updates'] == 0 and
                proof['encoded_tensor_format'] == 'TORCH_SAVE_GZIP_LOSSLESS_LEVEL1' and
                proof['encoded_tensor_compression_level'] == 1 and
                tensor_path.stat().st_size == entry['encoded_tensor_file_bytes'] and
                proof['original_b_processor_runtime'] == completed['original_b_processor_runtime'],
                'Old successful CPU processor/lossless cache evidence changed')
        require(proof['input_evidence']['physical_frames'] == NATIVE_FRAMES and
                bool(proof['input_evidence']['tensor_signature']) and
                0 < entry['input_tokens'] <= MAX_INPUT_TOKENS,
                'Actual successful native64/token/signature evidence is missing')
        require(meta['case_id'] == expected_case and meta['source_id'] == source['source_id'] and
                meta['source_name'] == source['source_id'] and meta['source_role'] == source['role'] and
                meta['source_rank'] == source['rank'] and meta['source_sha256'] == receipt['sha256'] and
                meta['source_bytes'] == receipt['bytes'] and meta['source_path'] == str(Path(receipt['path']).resolve()) and
                meta['source_total_frames'] == clock['n_frames'] and
                meta['all_source_exact_pts'] == clock['normalized_exact_pts'] and
                meta['original_clock_origin_exact'] == clock['first_original_pts_exact'] and
                meta['window_start'] == window['start_exact'] and meta['window_end'] == window['end_exact'] and
                meta['source_frame_ordinals'] == window['source_frame_ordinals'] and
                meta['sample_exact_pts'] == window['sample_exact_pts'] and
                meta['native_clock_path'] == str(clock_path) and meta['native_clock_sha256'] == sha(clock_path) and
                meta['reference_available_to_inference'] is False and
                meta['reference_labels_used_for_sampling'] is False and meta['audio_observed'] is False and
                len(meta['pixel_sha256']) == NATIVE_FRAMES,
                'Old complete native64 window/frame/no-reference identity changed')
        rgb_path = _bound_file(meta['frame_array_path'], meta['frame_array_sha256'], expected_folder)
        require(rgb_path.name == 'frames.npz' and rgb_path.stat().st_size == entry['rgb_npz_file_bytes'],
                'Previously successful native RGB artifact identity changed')
        for path, digest in ((proof_path, entry['proof_sha256']), (input_path, entry['input_sha256']),
                             (tensor_path, entry['encoded_tensor_sha256']), (rgb_path, meta['frame_array_sha256'])):
            artifacts.append(dict(path=str(path), sha256=digest, bytes=path.stat().st_size))
    return entries, artifacts


def _reuse_cpu_completion(source, receipt, reference, clock, clock_path, windows):
    folder = V1ROOT/'native_01'/source['source_id']
    path = _bound_file(receipt['existing_CPU_completion_path'], receipt['existing_CPU_completion_sha256'], folder)
    require(path == (folder/'completion.json').resolve(), 'Expected exact original CPU completion path')
    completed = read(path)
    require(completed['status'] == OLD_COMPLETION_STATUS and
            completed['bindings']['tensor_cache_helper_files'] == HELPER_FILES and
            completed['bindings']['reference_metadata_sha256'] == _canonical_sha(reference) and
            completed['bindings']['source'] == dict(source_id=source['source_id'], role=source['role'], rank=source['rank']) and
            completed['bindings']['media_receipt'] == dict(path=str(Path(receipt['path']).resolve()),
                bytes=receipt['bytes'], sha256=receipt['sha256']),
            'Only exact successful original B v1 source/CPU/helper identity can be inherited')
    entries, artifacts = _checked_cpu_proofs(source, receipt, clock, clock_path, windows, completed, V1ROOT)
    artifacts.insert(0, dict(path=str(path), sha256=receipt['existing_CPU_completion_sha256'], bytes=path.stat().st_size))
    for path_key, digest_key in (('window_plan_path', 'window_plan_sha256'),
                                 ('reference_validation_path', 'reference_validation_sha256')):
        artifact = _bound_file(completed[path_key], completed[digest_key], folder)
        artifacts.append(dict(path=str(artifact), sha256=completed[digest_key], bytes=artifact.stat().st_size))
    old_plan = read(completed['window_plan_path'])
    require(old_plan['windows'] == windows and old_plan['native_clock_sha256'] == sha(clock_path) and
            old_plan['reference_labels_used_for_windows'] is False,
            'Complete original CPU window plan is not the frozen native-only plan')
    return entries, completed['original_b_processor_runtime'], artifacts


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
    name = '_charades_v2_native_frozen_tensor_cache'
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
    # New module is charades_v2_common, so the original engine's own common import
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
    """Prepare only previously unprepared work; cite every old successful byte."""
    require(socket.gethostname() == 'inspur-NP5570M5' and sys.platform == 'linux',
            'Charades real media/CPU preparation must stay on the Linux host')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU preparation child must hide CUDA only for itself')
    check_deadline()
    stage_bindings = _source_bindings(source, media_receipt, reference, bindings)
    source_out = _inside(source_out, ROOT/'native_01'/source['source_id'])
    require(source_out == (ROOT/'native_01'/source['source_id']).resolve(), 'Exact independent v2 source output required')
    path = _source_media_path(source, media_receipt)
    require(path.is_file() and path.stat().st_size == media_receipt['bytes'] and sha(path) == media_receipt['sha256'],
            'Admitted original media identity changed before CPU preparation')
    inherited_clock = 'existing_native_clock_path' in media_receipt
    inherited_CPU = 'existing_CPU_completion_path' in media_receipt
    completion_path = source_out/'completion.json'
    if completion_path.exists():
        completed = read(completion_path)
        require(completed['status'] == COMPLETION_STATUS and
                completed['bindings'] == stage_bindings,
                'Previously successful Charades v2 CPU source binding changed')
        clock_path = _bound_file(completed['native_clock_path'], completed['native_clock_sha256'],
                                (V1ROOT if inherited_clock else ROOT)/'native_01'/source['source_id'])
        clock = read(clock_path)['clock']
        windows = _windows(clock)
        for path_key, digest_key in (('window_plan_path', 'window_plan_sha256'),
                                     ('reference_validation_path', 'reference_validation_sha256')):
            _bound_file(completed[path_key], completed[digest_key], source_out)
        require(read(completed['window_plan_path'])['windows'] == windows,
                'Previously successful v2 native-only window plan changed')
        _checked_cpu_proofs(source, media_receipt, clock, clock_path, windows, completed,
                            V1ROOT if inherited_CPU else ROOT)
        for artifact in completed['inherited_CPU_artifacts']:
            _bound_file(artifact['path'], artifact['sha256'], V1ROOT/'native_01'/source['source_id'])
        return completed
    source_out.mkdir(parents=True, exist_ok=True)
    require(not (source_out/'cpu_launch.json').exists() and not (source_out/'failure.json').exists(),
            'An existing failed/interrupted CPU source requires explicit independent recovery')
    started = time.monotonic()
    save(source_out/'cpu_launch.json', dict(pid=os.getpid(), utc=utc(), bindings=stage_bindings,
        CPU_only=True, new_model_calls=0, new_optimizer_updates=0, resource_snapshot=resource_snapshot()))
    proofs, clock_path, clock_saved, stage = [], source_out/'native_clock.json', False, 'CLOCK'
    new_clock_decodes, new_RGB_decodes, new_encodes = 0, 0, 0
    try:
        if inherited_clock:
            stage = 'INHERITED_COMPLETE_NATIVE_CLOCK_IDENTITY'
            clock, clock_path = _inherited_clock(source, media_receipt, reference)
            clock_saved = True
            save(source_out/'native_clock_reuse.json', dict(status='REFERENCE_COMPLETE_V1_NATIVE_CLOCK_NO_DECODE',
                native_clock_path=str(clock_path), native_clock_sha256=sha(clock_path),
                bindings=stage_bindings, new_clock_decodes=0, new_model_calls=0, CPU_only=True))
        else:
            require(not clock_path.exists(), 'A prior successful clock must be explicitly reused, not decoded again')
            new_clock_decodes = 1
            clock = _measure_clock(path, source['source_id'], media_receipt)
            save(clock_path, dict(status='COMPLETE_ORIGINAL_NATIVE_CLOCK_MEASURED_BEFORE_DOMAIN_ADMISSION',
                clock=clock, bindings=stage_bindings, CPU_only=True, new_model_calls=0, new_optimizer_updates=0))
            clock_saved = True
        stage = 'PARTIAL_AUTHOR_ACTION_NATIVE_ELIGIBILITY'
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
        inherited_artifacts, capacities = [], []
        if inherited_CPU:
            stage = 'INHERITED_COMPLETE_CPU_INPUT_IDENTITIES_NO_REENCODE'
            proofs, identity, inherited_artifacts = _reuse_cpu_completion(source, media_receipt, reference, clock, clock_path, windows)
        else:
            stage = 'FIRST_SEQUENTIAL_RGB_AND_ACTUAL_CPU_PROCESSOR'
            new_RGB_decodes = 1
            identity, capacities = _decode_rgb_once(source, media_receipt, clock, windows, source_out, actual_bindings, proofs)
            new_encodes = len(proofs)
        stage = 'COMPLETE_SOURCE_ADMISSION'
        require(path.stat().st_size == media_receipt['bytes'], 'Original media size changed during CPU preparation')
        completed = dict(status=COMPLETION_STATUS,
            source_id=source['source_id'], role=source['role'], rank=source['rank'], bindings=stage_bindings,
            native_clock_path=str(clock_path), native_clock_sha256=sha(clock_path),
            reference_validation_path=str(domain_path), reference_validation_sha256=sha(domain_path),
            window_plan_path=str(plan_path), window_plan_sha256=sha(plan_path), proofs=proofs,
            accepted_windows=len(proofs), actual_new_processor_encodes=new_encodes,
            inherited_CPU_inputs=len(proofs) if inherited_CPU else 0,
            inherited_CPU_artifacts=inherited_artifacts,
            existing_CPU_completion_path=media_receipt.get('existing_CPU_completion_path'),
            existing_CPU_completion_sha256=media_receipt.get('existing_CPU_completion_sha256'),
            original_b_processor_runtime=identity, CPU_only=True, CUDA_initialized=False,
            AV_thread_count=1, torch_thread_count=1, torch_interop_thread_count=1,
            full_native_clock_decodes=new_clock_decodes, sequential_rgb_decodes=new_RGB_decodes,
            new_clock_decodes=new_clock_decodes, new_complete_clock_decodes=new_clock_decodes,
            new_RGB_decodes=new_RGB_decodes,
            author_empty_actions_retained=not reference['actions'],
            reference_eligibility_counts=domain['eligibility_counts'],
            whole_source_GT_complete=False, whole_source_precision_recall_F1_admitted=False,
            input_validity_is_model_quality=False, reference_labels_used_for_windows_or_prompt=False,
            new_model_calls=0, new_optimizer_updates=0, GPU_launch_admitted=False,
            source_wall_seconds=time.monotonic()-started,
            process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            output_file_bytes=sum(p.stat().st_size for p in source_out.rglob('*') if p.is_file()),
            capacity_receipts=capacities, utc=utc())
        save(completion_path, completed)
        return completed
    except BaseException as error:
        save(source_out/'failure.json', dict(status='FAILED_CHARADES_V2_SOURCE_KEEP_CLOCK_AND_SUCCESSFUL_INPUTS',
            source_id=source['source_id'], stage=stage, bindings=stage_bindings,
            error_type=type(error).__name__, error=str(error),
            engineering_native_endpoint_failure=isinstance(error, NativeEndpointError),
            complete_clock_preserved=clock_saved, native_clock_path=str(clock_path) if clock_saved else None,
            native_clock_sha256=sha(clock_path) if clock_saved else None, successful_proofs=proofs,
            new_clock_decodes=new_clock_decodes, new_RGB_decodes=new_RGB_decodes,
            actual_new_processor_encodes=len(proofs) if not inherited_CPU else 0,
            annotation_failure_never_source_replacement=True,
            new_model_calls=0, new_optimizer_updates=0, CPU_only=True, utc=utc()))
        raise
