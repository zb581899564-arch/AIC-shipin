"""Per-source native64 preparation; inference forbidden until fresh8 actual inputs and independent admission pass."""
import argparse
import hashlib
import os
import socket
import sys
import traceback
from fractions import Fraction as F
from pathlib import Path

from native_profile_04 import (measure_original_video, native64_windows,
                               validate_original_origin, validate_reference_endpoints)
from sparse_stage_common_02 import BASE, LEGACY, RUN, check_file, read, save, sha, utc


def load_cpu_runtime():
    import torch
    import transformers
    if torch.cuda.is_initialized() or os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise ValueError('CPU-only processor child required')
    sys.path.insert(0, str(LEGACY))
    import runtime
    if Path(runtime.__file__).resolve() != (LEGACY/'runtime.py').resolve():
        raise ValueError('Unexpected original B runtime')
    modules = ('runtime', 'engine', 'contracts', 'bw_video', 'exact_pts', 'native_frames')
    files = {str(Path(sys.modules[name].__file__).resolve()): sha(sys.modules[name].__file__) for name in modules}
    config_path = RUN/'b_score_aligned_package_v4/config.json'
    model_dir = Path(read(config_path)['model_dir'])
    assets = {str(path): sha(path) for path in sorted(model_dir.iterdir())
              if path.is_file() and path.suffix in ('.json', '.txt', '.jinja')}
    if not assets:
        raise ValueError('Original processor assets missing')
    from transformers import AutoProcessor
    processor = AutoProcessor.from_pretrained(model_dir, local_files_only=True,
                                              min_pixels=131072, max_pixels=131072)
    return runtime, processor, dict(runtime_files=files, processor_assets=assets,
        original_config_sha256=sha(config_path), torch_version=torch.__version__,
        transformers_version=transformers.__version__,
        prompt_sha256=hashlib.sha256(runtime.EMPTY_PROMPT.encode()).hexdigest())


def select_rgb(clock, window, frames):
    import numpy as np
    points = [F(value) for value in clock['original_exact_pts']]
    ordinals = window['source_frame_ordinals']
    desired = {points[ordinal]: ordinal for ordinal in ordinals}
    if len(desired) != 64 or len(set(ordinals)) != 64:
        raise ValueError('Exactly64 distinct actual frames required')
    selected, last = {}, None
    for frame in frames:
        if frame.pts is None or frame.time_base is None:
            raise ValueError('Seek frame has no exact PTS')
        point = F(frame.pts) * F(frame.time_base)
        if last is not None and point <= last:
            raise ValueError('Non-monotonic seek PTS')
        last = point
        if point > points[ordinals[-1]]:
            break
        if point in desired:
            rgb = frame.to_ndarray(format='rgb24')
            if rgb.dtype != np.uint8 or rgb.shape != (clock['height'], clock['width'], 3):
                raise ValueError('Original RGB geometry changed')
            selected[desired[point]] = rgb
    if set(selected) != set(ordinals):
        raise ValueError('Registered native samples were not all recovered')
    images = [selected[index] for index in ordinals]
    return np.stack(images), [hashlib.sha256(image.tobytes()).hexdigest() for image in images]


def main(registration_path):
    if socket.gethostname() != 'inspur-NP5570M5' or os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise ValueError('Registered CPU-only Linux preparation required')
    reg_path = Path(registration_path)
    reg = read(reg_path)
    for name, digest in reg['required_files'].items():
        check_file(BASE/name, digest)
    download = read(check_file(BASE/reg['media_directory']/'completion.json', reg['media_completion_sha256']))
    if download['status'] != 'PASS_FRESH_CONFIRM_MEMBER_BATCH_BYTES_AND_IDENTITY_NOT_NATIVE_ADMISSION':
        raise ValueError('Actual member download acceptance required')
    selection = read(BASE/reg['selection_path'])['selection']
    selected = {row['video_id']: (index+1, row) for index, row in enumerate(selection)}
    refs = {row['video_id']: row for row in read(BASE/reg['reference_path'])}
    out = BASE/reg['output_directory']
    out.mkdir(exist_ok=False)
    bindings = dict(registration_sha256=sha(reg_path), required_files=reg['required_files'],
                    media_completion_sha256=reg['media_completion_sha256'])
    save(out/'launch_claim.json', dict(pid=os.getpid(), utc=utc(), bindings=bindings, new_model_calls=0))
    accepted, current = [], None
    runtime = processor = runtime_identity = None
    try:
        import av
        import numpy as np
        for media in download['members']:
            vid = current = media['video_id']
            index, row = selected[vid]
            path = check_file(media['path'], media['sha256'], media['bytes'])
            source_out = out/vid
            source_out.mkdir(exist_ok=False)
            clock = measure_original_video(path, av)
            clock.update(source_sha256=media['sha256'], source_bytes=media['bytes'])
            # Retain the successful complete measurement even if manual endpoint admission fails.
            save(source_out/'clock.json', clock)
            validate_original_origin(clock)
            endpoint = validate_reference_endpoints(clock, refs[vid]['annotator_intervals_exact_seconds'])
            windows = native64_windows(clock)
            import shutil
            raw_window_bytes = 64 * clock['width'] * clock['height'] * 3
            meminfo = {line.split(':')[0]: int(line.split(':')[1].split()[0]) * 1024
                       for line in Path('/proc/meminfo').read_text().splitlines() if ':' in line}
            if 3 * raw_window_bytes > meminfo['MemAvailable']:
                raise ValueError('Actual native RGB array/stack/compression capacity unavailable')
            if 2 * raw_window_bytes * len(windows) > shutil.disk_usage(out).free:
                raise ValueError('Actual native RGB cache capacity unavailable')
            save(source_out/'mapping.json', dict(status='PASS_UNMODIFIED_REFERENCE_SECONDS_IN_NATIVE_DOMAIN',
                 video_id=vid, clock_sha256=sha(source_out/'clock.json'), windows=windows,
                 endpoint=endpoint, author_nominal_duration_diagnostic_only=refs[vid]['author_duration_raw'],
                 author_1fps_grid_used_as_native_GT=False, reference_text_available_to_model=False,
                 independent_author_media_byte_identity_verified=False))
            for window in windows:
                case = current = f'{vid}_W{window["index"]:03d}'
                folder = source_out/case
                folder.mkdir(exist_ok=False)
                with av.open(str(path)) as container:
                    stream = container.streams.video[0]
                    if stream.index != clock['video_stream_index'] or F(stream.time_base) != F(clock['stream_time_base_exact']):
                        raise ValueError('Native stream identity changed')
                    first = F(window['sample_exact_pts'][0])
                    container.seek(int(first/F(stream.time_base)), stream=stream, backward=True, any_frame=False)
                    arrays, pixels = select_rgb(clock, window, container.decode(stream))
                array_path = folder/'frames.npz'
                with array_path.open('xb') as destination:
                    np.savez_compressed(destination, rgb=arrays)
                del arrays
                meta = dict(case_id=case, source_name=vid, source_group=row['group'],
                    source_path=str(path), source_sha256=media['sha256'], source_bytes=media['bytes'],
                    source_total_frames=clock['native_frames'], width=clock['width'], height=clock['height'],
                    fps_num=clock['fps_num'], fps_den=clock['fps_den'],
                    all_source_exact_pts=clock['original_exact_pts'], original_clock_origin_exact='0',
                    window_start=window['start_exact'], window_end=window['end_exact'],
                    source_frame_ordinals=window['source_frame_ordinals'], sample_exact_pts=window['sample_exact_pts'],
                    pixel_sha256=pixels, frame_array_path=str(array_path), frame_array_sha256=sha(array_path),
                    audio_observed=False, reference_available_to_inference=False,
                    bindings=dict(**bindings, mapping_sha256=sha(source_out/'mapping.json')))
                meta_path = folder/'input.json'
                save(meta_path, meta)
                if runtime is None:
                    runtime, processor, runtime_identity = load_cpu_runtime()
                    save(out/'processor_runtime_identity.json', runtime_identity)
                frames = runtime.baseline_frames(meta)
                encoded, detail = runtime.encode(processor, meta, frames, F(meta['window_start']), runtime.EMPTY_PROMPT)
                tokens = int(encoded['input_ids'].shape[1])
                if tokens > 16384 or detail['physical_frames'] != 64:
                    raise ValueError('Actual original-B native64/token budget exceeded')
                if any(value.device.type != 'cpu' for value in encoded.values() if hasattr(value, 'device')):
                    raise ValueError('Processor created GPU tensors')
                proof = dict(status='PASS_CPU_ORIGINAL_B_NATIVE64_PROCESSOR_INPUT', case_id=case,
                    source_name=vid, input_path=str(meta_path), input_sha256=sha(meta_path), input_evidence=detail,
                    input_tokens=tokens, bindings=bindings, runtime_identity_sha256=sha(out/'processor_runtime_identity.json'),
                    CPU_only=True, new_model_calls=0, new_optimizer_updates=0)
                proof_path = folder/'cpu_input.json'
                save(proof_path, proof)
                accepted.append(dict(case_id=case, video_id=vid, group=row['group'],
                    input_path=str(meta_path), input_sha256=sha(meta_path),
                    proof_path=str(proof_path), proof_sha256=sha(proof_path), input_tokens=tokens))
                del encoded, frames
                print('Accepted CPU input '+case, flush=True)
        import torch
        if torch.cuda.is_initialized():
            raise ValueError('CPU preparation initialized CUDA')
        save(out/'completion.json', dict(status='PASS_FRESH_CONFIRM_BATCH_NATIVE64_CPU_INPUTS_NOT_GPU_ADMISSION',
            utc=utc(), sources=len(download['members']), windows=len(accepted), proofs=accepted,
            bindings=bindings, new_model_calls=0, new_optimizer_updates=0, GPU_launch_admitted=False))
    except BaseException:
        save(out/'failure.json', dict(status='FAILED_BATCH_CPU_KEEP_COMPLETE_CLOCKS_RGB_AND_PROOFS',
            utc=utc(), case_or_source=current, accepted_windows=accepted,
            traceback=traceback.format_exc(), new_model_calls=0))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('registration')
    main(parser.parse_args().registration)
