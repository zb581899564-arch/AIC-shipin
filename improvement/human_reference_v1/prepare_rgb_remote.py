"""Cache fixed native64 RGB windows after all original clocks and separation pass.

No model/processor/download operation is implemented here. Frame extraction is a
new stage after clock measurement; accepted window caches are never re-extracted.
"""
import hashlib
import json
import os
import socket
import sys
from fractions import Fraction as F
from pathlib import Path

from download_sources_remote import identity
from map_sources_remote import BASE, MEDIA, OUT as MAPPING, check_download_admission, read, save, sha
from native_mapping_v2 import validate_mapping
from native_window_plan import plan_windows

OUT = BASE / 'rgb_01'


def select_rgb(clock, window, frames):
    """Seek decoder frames are matched by original exact PTS, never seek ordinal."""
    import numpy as np
    original = [F(value) for value in clock['original_exact_pts']]
    ordinals = window['source_frame_ordinals']
    desired = {original[ordinal]: ordinal for ordinal in ordinals}
    if len(desired) != 64 or len(set(ordinals)) != 64:
        raise ValueError('A native64 cache must contain 64 different original frames')
    selected = {}
    last = None
    for frame in frames:
        if frame.pts is None or frame.time_base is None:
            raise ValueError('Seek decode frame has no native PTS/time base')
        point = F(frame.pts) * F(frame.time_base)
        if last is not None and point <= last:
            raise ValueError('Seek decode PTS is not strictly increasing')
        last = point
        if point > original[ordinals[-1]]:
            break
        if point in desired:
            if (frame.width, frame.height) != (clock['width'], clock['height']):
                raise ValueError('Seek decode geometry differs from the complete source clock')
            rgb = frame.to_ndarray(format='rgb24')
            if rgb.dtype != np.uint8 or rgb.shape != (clock['height'], clock['width'], 3):
                raise ValueError('Unexpected original RGB array geometry or type')
            selected[desired[point]] = rgb
    if set(selected) != set(ordinals):
        raise ValueError('Seek decoder did not recover every registered native64 source frame')
    images = [selected[ordinal] for ordinal in ordinals]
    pixels = [hashlib.sha256(image.tobytes()).hexdigest() for image in images]
    return np.stack(images), pixels


def admission(registration_path):
    registration, downloaded, _ = check_download_admission(registration_path)
    mapped = read(MAPPING/'completion.json')
    if (mapped['status'] != 'PASS_TWENTY_ORIGINAL_NATIVE_MAPPINGS_NOT_PROCESSOR_OR_SOURCE_ADMISSION' or
            mapped['sources'] != 20 or len(mapped['rows']) != 20 or
            mapped['bindings']['registration_sha256'] != sha(registration_path)):
        raise ValueError('All twenty registered native clocks must pass before RGB extraction')
    sources = {row['source_name']: row for row in mapped['rows']}
    if len(sources) != 20 or set(sources) != {row['source_name'] for row in registration['rows']}:
        raise ValueError('Native mapping source denominator changed')
    separated_path = BASE/'source_isolation_acceptance.json'
    separated = read(separated_path)
    if (separated['status'] != 'PASS_KNOWN_SOURCE_IDENTITY_AND_BYTE_SEPARATION' or
            separated['registered_sources'] != 20 or
            separated['registration_sha256'] != sha(registration_path) or
            separated['media_completion_sha256'] != sha(MEDIA/'completion.json') or
            separated['known_current_b_training_and_426_test_identities_complete'] is not True or
            separated['identity_intersections'] or separated['byte_intersections'] or
            separated['new_optimizer_updates'] != 0):
        raise ValueError('Known test/training identity and byte separation has not passed')
    snapshot_path = Path(separated['known_identity_snapshot_path'])
    if sha(snapshot_path) != separated['known_identity_snapshot_sha256']:
        raise ValueError('Accepted known source identity snapshot changed')
    # The snapshot is a provenance audit output, not evidence of semantic/re-encoding separation.
    return registration, downloaded, sources, dict(
        registration_sha256=sha(registration_path), mapping_completion_sha256=sha(MAPPING/'completion.json'),
        source_isolation_acceptance_sha256=sha(separated_path),
        script_sha256=sha(Path(__file__)))


def main(registration_path, resume=False):
    if socket.gethostname() != 'inspur-NP5570M5':
        raise ValueError('This CPU entry is confined to the existing Linux training host')
    registration, downloaded, mapped, bindings = admission(registration_path)
    if (OUT/'completion.json').exists():
        raise ValueError('Completed native RGB extraction must not be launched again')
    if resume:
        if read(OUT/'launch_claim.json')['bindings'] != bindings or (OUT/'failure.json').exists():
            raise ValueError('A failed or changed RGB extraction requires a separate recovery protocol')
    else:
        OUT.mkdir(parents=True, exist_ok=False)
        save(OUT/'launch_claim.json', dict(pid=os.getpid(), bindings=bindings,
             new_model_calls=0, new_optimizer_updates=0))
    import av
    import numpy as np
    entries = []
    current = None
    try:
        for index, row in enumerate(registration['rows'], 1):
            source = row['source_name']
            mapping = mapped[source]
            bundle_path = Path(mapping['bundle_path'])
            if not bundle_path.resolve().is_relative_to(MAPPING.resolve()):
                raise ValueError('Native mapping bundle escaped its registered stage directory')
            if sha(bundle_path) != mapping['bundle_sha256']:
                raise ValueError('Accepted original mapping bundle changed')
            bundle = read(bundle_path)
            clock = bundle['clock']
            if validate_mapping(row, clock) != bundle['mapping'] or plan_windows(clock) != bundle['windows']:
                raise ValueError('Native mapping/window evidence changed')
            path = MEDIA/(source+'.webm')
            actual = identity(path)
            if actual != downloaded[source]['identity'] or actual['sha256'] != clock['source_sha256']:
                raise ValueError('Accepted original media bytes changed')
            for window in bundle['windows']:
                current = f'H{index:02d}_W{window["index"]:03d}'
                folder = OUT/current
                meta_path = folder/'input.json'
                window_bindings = dict(**bindings, mapping_bundle_sha256=mapping['bundle_sha256'])
                if meta_path.exists():
                    meta = read(meta_path)
                    if (meta['bindings'] != window_bindings or meta['source_sha256'] != actual['sha256'] or
                            meta['source_frame_ordinals'] != window['source_frame_ordinals'] or
                            meta['sample_exact_pts'] != window['sample_exact_pts'] or
                            meta['window_start'] != window['start_exact'] or meta['window_end'] != window['end_exact'] or
                            meta['case_id'] != current or sha(meta['frame_array_path']) != meta['frame_array_sha256']):
                        raise ValueError('Accepted native64 RGB cache changed')
                    # Cached window is preserved; no successful real RGB decode is repeated.
                else:
                    folder.mkdir(exist_ok=False)
                    first_raw = F(clock['original_exact_pts'][window['source_frame_ordinals'][0]])
                    with av.open(str(path)) as container:
                        if len(container.streams.video) != 1:
                            raise ValueError('Ambiguous source video stream')
                        stream = container.streams.video[0]
                        if stream.index != clock['video_stream_index'] or stream.time_base is None:
                            raise ValueError('Native source video stream changed')
                        container.seek(int(first_raw/F(stream.time_base)), stream=stream,
                                       backward=True, any_frame=False)
                        arrays, pixels = select_rgb(clock, window, container.decode(stream))
                    array_path = folder/'frames.npz'
                    with array_path.open('xb') as destination:
                        np.savez_compressed(destination, rgb=arrays)
                    meta = dict(case_id=current, source_name=source, source_group=row['source_group'],
                        source_path=str(path), source_sha256=actual['sha256'], source_bytes=actual['bytes'],
                        source_total_frames=clock['n_frames'], width=clock['width'], height=clock['height'],
                        fps_num=clock['fps_num'], fps_den=clock['fps_den'],
                        all_source_exact_pts=clock['normalized_exact_pts'],
                        original_clock_origin_exact=clock['first_original_pts_exact'],
                        window_start=window['start_exact'], window_end=window['end_exact'],
                        source_frame_ordinals=window['source_frame_ordinals'],
                        sample_exact_pts=window['sample_exact_pts'], pixel_sha256=pixels,
                        frame_array_path=str(array_path), frame_array_sha256=sha(array_path),
                        audio_observed=False, reference_available_to_inference=False,
                        bindings=window_bindings)
                    save(meta_path, meta)
                    del arrays
                entries.append(dict(case_id=current, source_name=source,
                                    input_path=str(meta_path), input_sha256=sha(meta_path)))
                print(json.dumps(dict(case_id=current, completed_windows=len(entries)), ensure_ascii=False), flush=True)
        save(OUT/'inputs.json', entries)
        save(OUT/'completion.json', dict(status='PASS_REGISTERED_NATIVE64_RGB_CACHES_NOT_PROCESSOR_ADMISSION',
             sources=20, windows=len(entries), inputs_sha256=sha(OUT/'inputs.json'), bindings=bindings,
             new_model_calls=0, new_optimizer_updates=0, processor_inputs='UNVERIFIED'))
    except Exception as error:
        save(OUT/'failure.json', dict(status='FAILED_NATIVE64_RGB_EXTRACTION', case_id=current,
             error_type=type(error).__name__, error=str(error), successful_inputs_retained=entries,
             new_model_calls=0, new_optimizer_updates=0))
        raise


if __name__ == '__main__':
    os.environ['CUDA_VISIBLE_DEVICES'] = ''  # Only this CPU process, never a chain parent.
    main(Path(sys.argv[1]), resume='--resume' in sys.argv[2:])
