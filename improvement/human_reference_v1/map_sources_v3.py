"""New mapping stage with immutable inheritance of four measured clocks."""
import os
import socket
import sys
from fractions import Fraction as F
from pathlib import Path

from map_sources_remote import BASE, MEDIA, check_download_admission, read, save, sha
from download_sources_remote import identity
from native_mapping_v3 import validate_mapping
from native_window_plan import plan_windows

OUT = BASE/'mapping_02'


def measured_clock(row, actual, container, stream, av):
    points, geometry, last_duration = [], None, None
    for frame in container.decode(stream):
        if frame.pts is None or frame.time_base is None:
            raise ValueError('Native frame lacks exact PTS/time base')
        point = F(frame.pts)*F(frame.time_base)
        if points and point <= points[-1]:
            raise ValueError('Original native PTS are not strictly increasing')
        points.append(point)
        current = (frame.width, frame.height)
        if geometry is None:
            geometry = current
        if current != geometry or min(current) <= 0:
            raise ValueError('Original frame geometry changed')
        duration = getattr(frame, 'duration', None)
        last_duration = F(duration)*F(frame.time_base) if duration is not None else None
    if not points or last_duration is None or last_duration <= 0:
        raise ValueError('Native ending lacks positive final-frame duration')
    origin = points[0]
    normalized = [p-origin for p in points]
    rate = stream.average_rate
    if rate is None or rate <= 0:
        raise ValueError('Original stream lacks declared positive average rate')
    return dict(source_name=row['source_name'], source_bytes=actual['bytes'],
        source_crc32=actual['crc32'], source_sha256=actual['sha256'], n_frames=len(points),
        normalized_exact_pts=list(map(str, normalized)), original_exact_pts=list(map(str, points)),
        first_original_pts_exact=str(origin), physical_end_exact=str(normalized[-1]+last_duration),
        width=geometry[0], height=geometry[1], source_path=str(MEDIA/(row['source_name']+'.webm')),
        fps_num=rate.numerator, fps_den=rate.denominator, decoder='PyAV', decoder_version=av.__version__,
        video_stream_index=stream.index,
        container_duration_microseconds=container.duration,
        physical_endpoint_evidence=dict(kind='LAST_NATIVE_FRAME_PTS_PLUS_POSITIVE_DURATION',
            last_normalized_pts_exact=str(normalized[-1]), last_frame_duration_exact=str(last_duration),
            duration_source='PyAV decoded final VideoFrame.duration * VideoFrame.time_base'))


def main():
    if socket.gethostname() != 'inspur-NP5570M5':
        raise ValueError('Unexpected host')
    reg_path = BASE/'human_source_registration_01.json'
    registration, downloaded, _ = check_download_admission(reg_path)
    recovery_path = BASE/'native_mapping_recovery_02.json'
    recovery = read(recovery_path)
    for path, digest in recovery['frozen_files'].items():
        if sha(path) != digest:
            raise ValueError('Frozen recovery input/code changed: '+path)
    audit = read(BASE/'annotation_ordinal_clock_audit_01.json')
    if (audit['status'] != 'AUTHOR_ORIGINAL_ORDINAL_VECTOR_AUDIT_NOT_NATIVE_ADMISSION' or
            audit['registration_sha256'] != sha(reg_path) or audit['sources'] != 20 or
            audit['original_annotations_changed'] or audit['labels_resampled']):
        raise ValueError('Original author ordinal audit is missing or changed')
    if (recovery['registration_sha256'] != sha(reg_path) or
            read(BASE/'mapping_01/failure.json')['completed_sources'] != 3):
        raise ValueError('Recovery does not bind the actual v2 failure')
    bindings = dict(registration_sha256=sha(reg_path),
        mapping_contract_sha256=sha(BASE/'NATIVE_MAPPING_CONTRACT_V3.md'),
        recovery_registration_sha256=sha(recovery_path),
        author_ordinal_audit_sha256=sha(BASE/'annotation_ordinal_clock_audit_01.json'),
        mapper_sha256=sha(__file__), mapping_validator_sha256=sha(Path(__file__).with_name('native_mapping_v3.py')),
        window_planner_sha256=sha(Path(__file__).with_name('native_window_plan.py')),
        media_completion_sha256=sha(MEDIA/'completion.json'))
    OUT.mkdir(exist_ok=False)
    save(OUT/'launch_claim.json', dict(bindings=bindings, pid=os.getpid(), new_model_calls=0))
    import av
    inheritance = {entry['source_name']: entry for entry in recovery['inherited_clocks']}
    accepted, source = [], None
    try:
        for row in registration['rows']:
            source = row['source_name']
            actual = identity(MEDIA/(source+'.webm'))
            if actual != downloaded[source]['identity']:
                raise ValueError('Accepted original media changed')
            inherited = inheritance.get(source)
            if inherited:
                original_path = Path(inherited['path'])
                if sha(original_path) != inherited['sha256']:
                    raise ValueError('Inherited measured clock changed')
                original = read(original_path)
                clock = original['clock'] if inherited['kind'] == 'V2_SUCCESS_BUNDLE' else original
                provenance = dict(kind=inherited['kind'], path=str(original_path), sha256=sha(original_path),
                                  new_decode=False)
            else:
                with av.open(str(MEDIA/(source+'.webm'))) as container:
                    if len(container.streams.video) != 1:
                        raise ValueError('Ambiguous original video stream')
                    clock = measured_clock(row, actual, container, container.streams.video[0], av)
                clock_path = OUT/(source+'.observed_clock.json')
                save(clock_path, clock)  # Measurement survives even a later admission failure.
                provenance = dict(kind='NEW_ORIGINAL_COMPLETE_DECODE', path=str(clock_path),
                                  sha256=sha(clock_path), new_decode=True)
            if clock['source_sha256'] != actual['sha256']:
                raise ValueError('Clock original-byte identity changed')
            mapped = validate_mapping(row, clock)
            windows = plan_windows(clock)
            if inherited and inherited['kind'] == 'V2_SUCCESS_BUNDLE' and windows != original['windows']:
                raise ValueError('Inherited successful native window plan changed')
            bundle_path = OUT/(source+'.mapping_bundle.json')
            save(bundle_path, dict(status='PASS_ONE_ORIGINAL_NATIVE_MAPPING_AND_WINDOW_PLAN',
                bindings=bindings, clock=clock, mapping=mapped, windows=windows,
                decode_provenance=provenance, new_model_calls=0, new_optimizer_updates=0))
            accepted.append(dict(source_name=source, source_group=row['source_group'],
                bundle_path=str(bundle_path), bundle_sha256=sha(bundle_path),
                native_frames=clock['n_frames'], windows=len(windows), new_decode=provenance['new_decode']))
            temp = OUT/'progress.json.pending'
            temp.write_text(__import__('json').dumps(dict(completed_sources=len(accepted),
                registered_sources=20, last_source=source)), encoding='utf-8')
            temp.replace(OUT/'progress.json')
            print(__import__('json').dumps(accepted[-1]), flush=True)
        save(OUT/'completion.json', dict(status='PASS_TWENTY_ORIGINAL_NATIVE_MAPPINGS_NOT_PROCESSOR_OR_SOURCE_ADMISSION',
            sources=20, rows=accepted, bindings=bindings,
            new_complete_decodes=sum(row['new_decode'] for row in accepted),
            inherited_complete_clocks=4, original_v2_failure_preserved=True,
            new_model_calls=0, new_optimizer_updates=0))
    except BaseException as error:
        save(OUT/'failure.json', dict(status='FAILED_V3_NATIVE_MAPPING_KEEP_MEASUREMENTS', source_name=source,
            error=repr(error), successful_bundles_retained=accepted, new_model_calls=0))
        raise


if __name__ == '__main__':
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    main()
