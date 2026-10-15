"""One actual CPU preparation per new registered short native64 request.

Reuses accepted full clocks/media and any matching accepted old/new RGB cache.
Only the newly registered short contexts are seek-read. No full clock remeasure,
downloads, model load, or GPU launch. Encoded tensors are saved for GPU reuse.
"""
import argparse
from bisect import bisect_left
from fractions import Fraction as F
import hashlib
import os
from pathlib import Path
import resource
import time

from lb_contract import MAX_INPUT_TOKENS, NATIVE_FRAMES, normalized_clock
import lb_io as io


def frame_metadata_ordinals(request, n_frames):
    wanted = set(request['source_frame_ordinals'])
    cut = request['original_endpoint_cut_ordinal']
    wanted.update((cut-1, cut))
    for index in request['source_frame_ordinals']:
        wanted.update((index-1, index+1))
    return sorted(i for i in wanted if 0 <= i < n_frames)


def cache_pixels(request, reuse_refs, roots):
    import numpy as np
    wanted = set(request['source_frame_ordinals'])
    recovered, durations, reused = {}, {}, []
    for ref in reuse_refs:
        path = io.checked_ref(ref, roots=roots)
        meta = io.read(path)
        if meta['source_sha256'] != request['source_sha256']:
            raise ValueError('Immutable RGB reuse refers to another source')
        for ordinal, duration in meta.get('native_duration_by_ordinal', {}).items():
            if ordinal in durations and durations[ordinal] != duration:
                raise ValueError('Previously accepted contextual native duration changed')
            durations[ordinal] = duration
        pairs = [(sample, ordinal) for sample, ordinal in enumerate(meta['source_frame_ordinals'])
                 if ordinal in wanted and ordinal not in recovered]
        if not pairs:
            continue
        array_path = Path(meta['frame_array_path']).resolve()
        if not any(array_path.is_relative_to(Path(root).resolve()) for root in roots):
            raise ValueError('RGB array escaped its immutable external/new cache directory')
        if io.sha(array_path) != meta['frame_array_sha256']:
            raise ValueError('Previously accepted RGB array changed')
        with np.load(array_path, allow_pickle=False) as archive:
            arrays = archive['rgb']
        if (arrays.dtype != np.uint8 or arrays.shape != (64, request['height'], request['width'], 3) or
                [hashlib.sha256(a.tobytes()).hexdigest() for a in arrays] != meta['pixel_sha256']):
            raise ValueError('Previously accepted native64 RGB pixels changed')
        for sample, ordinal in pairs:
            image = arrays[sample].copy()
            recovered[ordinal] = image
            reused.append(dict(source_frame_ordinal=ordinal, input_path=str(path),
                               input_sha256=ref['sha256'], pixel_sha256=meta['pixel_sha256'][sample]))
        del arrays
    return recovered, durations, reused


def seek_new_context(request, clock, recovered, durations):
    """Match absolute decoder PTS to the accepted clock, never seek ordinals."""
    import av
    import numpy as np
    points, raw, origin, _ = normalized_clock(clock)
    required_metadata = frame_metadata_ordinals(request, len(points))
    missing_meta = {i for i in required_metadata if str(i) not in durations}
    missing_pixels = set(request['source_frame_ordinals'])-set(recovered)
    wanted = missing_meta | missing_pixels
    if not wanted:
        return [], 0
    positions = {p: i for i, p in enumerate(raw)}
    if len(positions) != len(raw):
        raise ValueError('Accepted complete original PTS is not unique')
    decoded_targets, metadata_seen = [], set()
    lower, upper = min(wanted), max(wanted)
    with av.open(request['source_path']) as container:
        if len(container.streams.video) != 1:
            raise ValueError('Ambiguous original source video stream')
        stream = container.streams.video[0]
        if (stream.time_base is None or stream.index != clock['video_stream_index'] or
                stream.average_rate is None or
                F(stream.average_rate) != F(request['fps_num'], request['fps_den'])):
            raise ValueError('Accepted source video stream/rate changed')
        container.seek(int(raw[lower]/F(stream.time_base)), stream=stream, backward=True, any_frame=False)
        last = None
        for frame in container.decode(stream):
            if frame.pts is None or frame.time_base is None:
                raise ValueError('New contextual frame has no native PTS/time base')
            point = F(frame.pts)*F(frame.time_base)
            if last is not None and point <= last:
                raise ValueError('New contextual seek PTS is not strictly increasing')
            last = point
            if point > raw[upper]:
                break
            if point not in positions:
                raise ValueError('Context decoder PTS is absent from accepted complete native clock')
            ordinal = positions[point]
            if ordinal not in wanted:
                continue
            if (frame.width, frame.height) != (request['width'], request['height']):
                raise ValueError('New contextual geometry differs from the accepted source')
            if ordinal in missing_meta:
                duration = getattr(frame, 'duration', None)
                duration = F(duration)*F(frame.time_base) if duration is not None else None
                durations[str(ordinal)] = str(duration) if duration is not None else None
                metadata_seen.add(ordinal)
            if ordinal in missing_pixels:
                image = frame.to_ndarray(format='rgb24')
                if image.dtype != np.uint8 or image.shape != (request['height'], request['width'], 3):
                    raise ValueError('New contextual RGB shape/dtype changed')
                recovered[ordinal] = image
                decoded_targets.append(ordinal)
    if (metadata_seen != missing_meta or
            set(recovered) != set(request['source_frame_ordinals'])):
        raise ValueError('Not every registered new target frame/metadata was recovered')
    return decoded_targets, len(metadata_seen)


def continuity(request, clock, durations):
    points, raw, origin, physical_end = normalized_clock(clock)

    def adjacent_after(ordinal):
        value = durations.get(str(ordinal))
        if value is None:
            return False
        duration = F(value)
        next_pts = raw[ordinal+1] if ordinal+1 < len(raw) else physical_end+origin
        return duration > 0 and raw[ordinal]+duration == next_pts

    result = {}
    for sample, ordinal in enumerate(request['source_frame_ordinals']):
        before = ordinal-1 if request['side'] == 'start' else ordinal
        result[str(sample)] = before >= 0 and adjacent_after(before)
    cut = request['original_endpoint_cut_ordinal']
    pivot = F(request['original_endpoint_exact'])
    verified = (0 < cut < len(points) and points[cut-1] < pivot <= points[cut] and
                adjacent_after(cut-1))
    return result, verified


def main(base):
    io.host(cpu=True)
    base = io.base_path(base)
    plan = base/'plan_01'
    complete = io.read(plan/'completion.json')
    if (complete['status'] != 'PASS_FROZEN_LOCAL_BOUNDARY_PLAN_NOT_CPU_ADMISSION' or
            complete['requests_sha256'] != io.sha(plan/'requests.json') or
            complete['events_sha256'] != io.sha(plan/'events.json') or
            complete['own_code_files'] != io.own_code_files()):
        raise ValueError('Main-agent frozen plan/code changed before actual CPU preparation')
    reg = io.read(complete['registration_path'])
    if io.sha(complete['registration_path']) != complete['registration_sha256']:
        raise ValueError('Frozen registration changed')
    io.checked_required(reg, base)
    requests = io.read(plan/'requests.json')
    if len(requests) != complete['requests'] or len(requests) != reg['actual_model_call_budget']:
        raise ValueError('Registered actual request denominator changed')
    out = base/'cpu_01'
    out.mkdir(exist_ok=False)
    bindings = dict(registration_sha256=complete['registration_sha256'],
        plan_completion_sha256=io.sha(plan/'completion.json'), own_code_files=io.own_code_files())
    io.save(out/'launch_claim.json', dict(pid=os.getpid(), utc=io.utc(), bindings=bindings,
        new_model_calls=0, new_optimizer_updates=0, CPU_only=True))
    current, proofs, checked_sources = None, [], set()
    new_reuse = {}
    try:
        import torch
        import numpy as np
        runtime, processor, runtime_identity = io.cpu_runtime()
        bindings['original_b_processor_runtime'] = runtime_identity
        for original in requests:
            request_started = time.monotonic()
            request = dict(original)
            current = request['request_id']
            source = request['source_sha256']
            if source not in checked_sources:
                path = io.checked_ref(dict(path=request['source_path'], sha256=source))
                if path.stat().st_size != request['source_bytes']:
                    raise ValueError('Accepted original media byte size changed')
                checked_sources.add(source)
            clock = io.extract_clock(io.read(io.checked_ref(request['original_evidence']['clock'])),
                                     request['clock_object_keys'])
            if normalized_clock(clock)[0] != [F(p) for p in request['all_source_exact_pts']]:
                raise ValueError('Frozen complete native clock differs from request plan')
            folder = out/current
            folder.mkdir(exist_ok=False)
            reused_refs = request['reuse_rgb_inputs']+new_reuse.get(source, [])
            roots = (*io.EXTERNAL_ROOTS, out)
            recovered, durations, reused = cache_pixels(request, reused_refs, roots)
            new_ordinals, metadata_count = seek_new_context(request, clock, recovered, durations)
            arrays = np.stack([recovered[i] for i in request['source_frame_ordinals']])
            pixels = [hashlib.sha256(a.tobytes()).hexdigest() for a in arrays]
            request['continuity_by_sample'], request['original_endpoint_continuity_verified'] = continuity(
                request, clock, durations)
            array_path = folder/'frames.npz'
            with array_path.open('xb') as destination:
                np.savez_compressed(destination, rgb=arrays)
            meta = dict(request, case_id=current, pixel_sha256=pixels,
                frame_array_path=str(array_path), frame_array_sha256=io.sha(array_path),
                new_pixel_target_ordinals=new_ordinals, immutable_reused_pixels=reused,
                native_duration_by_ordinal=durations, new_contextual_metadata_frames=metadata_count,
                new_complete_clock_decodes=0, bindings=bindings)
            meta_path = folder/'input.json'
            io.save(meta_path, meta)
            frames = arrays, request['source_frame_ordinals'], request['sample_exact_pts']
            processor_started = time.monotonic()
            encoded, evidence = runtime.encode(processor, meta, frames, F(meta['window_start']), meta['prompt'])
            processor_seconds = time.monotonic()-processor_started
            tokens = int(encoded['input_ids'].shape[1])
            if (tokens > MAX_INPUT_TOKENS or evidence['physical_frames'] != NATIVE_FRAMES or
                    any(value.device.type != 'cpu' for value in encoded.values() if hasattr(value, 'device'))):
                raise ValueError('Actual native64/token/CPU-only input budget failed')
            tensor_path = folder/'encoded_tensors.pt.gz'
            compression_started = time.monotonic()
            io.save_tensor_cache(tensor_path, encoded)
            compression_seconds = time.monotonic()-compression_started
            if torch.cuda.is_initialized():
                raise ValueError('Actual CPU preparation initialized CUDA')
            proof_path = folder/'cpu_input.json'
            io.save(proof_path, dict(status='PASS_CPU_LOCAL_BOUNDARY_NATIVE64_PROCESSOR_INPUT',
                request_id=current, event_id=meta['event_id'], side=meta['side'], bindings=bindings,
                input_path=str(meta_path), input_sha256=io.sha(meta_path), input_evidence=evidence,
                input_tokens=tokens, encoded_tensor_path=str(tensor_path),
                encoded_tensor_sha256=io.sha(tensor_path),
                encoded_tensor_format=io.TENSOR_CACHE_FORMAT,
                encoded_tensor_compression_level=1, encoded_tensor_file_bytes=tensor_path.stat().st_size,
                logical_tensor_payload_bytes=sum(value.numel()*value.element_size() for value in encoded.values()),
                rgb_npz_file_bytes=array_path.stat().st_size,
                processor_seconds=processor_seconds, tensor_compression_seconds=compression_seconds,
                request_wall_seconds=time.monotonic()-request_started,
                process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                CPU_only=True,
                CUDA_initialized=False, new_model_calls=0, new_optimizer_updates=0))
            proofs.append(dict(request_id=current, event_id=meta['event_id'], side=meta['side'],
                proof_path=str(proof_path), proof_sha256=io.sha(proof_path),
                input_path=str(meta_path), input_sha256=io.sha(meta_path), input_tokens=tokens))
            new_reuse.setdefault(source, []).append(dict(path=str(meta_path), sha256=io.sha(meta_path)))
            print(__import__('json').dumps(dict(request_id=current, accepted_inputs=len(proofs),
                total_inputs=len(requests), new_pixel_targets=len(new_ordinals))), flush=True)
            del encoded, arrays, recovered, frames
        io.save(out/'completion.json', dict(status='PASS_ALL_NEW_LOCAL_BOUNDARY_CPU_INPUTS_NOT_GPU_ADMISSION',
            requests=len(proofs), events=complete['events'], proofs=proofs, bindings=bindings,
            CPU_only=True, CUDA_initialized=False, actual_new_processor_encodes=len(proofs),
            new_model_calls=0, new_optimizer_updates=0, new_media_downloads=0,
            new_complete_clock_decodes=0, GPU_launch_admitted=False))
    except BaseException as error:
        io.save(out/'failure.json', dict(status='FAILED_NEW_CPU_INPUT_KEEP_ALL_SUCCESSFUL_EVIDENCE',
            request_id=current, successful_proofs=proofs, error=repr(error),
            new_model_calls=0, new_optimizer_updates=0))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', required=True)
    args = parser.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    main(args.base)
