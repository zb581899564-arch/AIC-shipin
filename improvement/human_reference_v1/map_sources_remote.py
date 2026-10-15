"""CPU-only full native clock mapping after authorized media completion.

Successful source bundles are reused on an explicit resume. This entry does not
load processors/models, accept GPU inputs, evaluate labels, or download files.
"""
import hashlib
import json
import os
import socket
import sys
from fractions import Fraction as F
from pathlib import Path

from download_sources_remote import identity
from native_mapping_v2 import validate_mapping
from native_window_plan import plan_windows

BASE = Path('/home/inspur/aic_video_work/human_reference_iteration_20261013_v1')
MEDIA = BASE / 'media_01'
OUT = BASE / 'mapping_01'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())


def progress(value):
    temporary = OUT / 'progress.json.pending'
    with temporary.open('w', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(OUT / 'progress.json')


def clock_from_frames(row, media_identity, frames):
    """Measure the decode sequence; never infer points/end from average FPS."""
    points = []
    geometry = None
    last_duration = None
    for frame in frames:
        if frame.pts is None or frame.time_base is None:
            raise ValueError('Decoded source frame has no native PTS/time base')
        point = F(frame.pts) * F(frame.time_base)
        if points and point <= points[-1]:
            raise ValueError('Decoded source PTS is not strictly increasing')
        points.append(point)
        current = (frame.width, frame.height)
        if geometry is None:
            geometry = current
        if current != geometry or min(current) <= 0:
            raise ValueError('Decoded source geometry changed or is invalid')
        duration = getattr(frame, 'duration', None)
        last_duration = F(duration) * F(frame.time_base) if duration is not None else None
    if not points:
        raise ValueError('No native decoded video frames')
    if last_duration is None or last_duration <= 0:
        raise ValueError('No positive native final-frame duration; no FPS/container-ending fallback')
    origin = points[0]
    normalized = [value-origin for value in points]
    clock = dict(source_name=row['source_name'], source_bytes=media_identity['bytes'],
                 source_crc32=media_identity['crc32'], source_sha256=media_identity['sha256'],
                 n_frames=len(points), normalized_exact_pts=list(map(str, normalized)),
                 original_exact_pts=list(map(str, points)), first_original_pts_exact=str(origin),
                 physical_end_exact=str(normalized[-1]+last_duration),
                 width=geometry[0], height=geometry[1],
                 physical_endpoint_evidence=dict(kind='LAST_NATIVE_FRAME_PTS_PLUS_POSITIVE_DURATION',
                     last_normalized_pts_exact=str(normalized[-1]),
                     last_frame_duration_exact=str(last_duration),
                     duration_source='PyAV decoded final VideoFrame.duration * VideoFrame.time_base'))
    return clock, validate_mapping(row, clock)


def check_download_admission(registration_path):
    registration = read(registration_path)
    rows = registration['rows']
    if len(rows) != 20 or len({row['source_name'] for row in rows}) != 20:
        raise ValueError('The complete fixed twenty-source registration is required')
    canonical = hashlib.sha256(json.dumps(registration, sort_keys=True, ensure_ascii=False,
                                         separators=(',', ':')).encode()).hexdigest()
    claim = read(MEDIA / 'launch_claim.json')
    authorization = claim['authorization']
    if (authorization['approved'] is not True or
            authorization['registration_canonical_sha256'] != canonical or
            authorization['registration_sha256'] != sha(registration_path) or
            claim['registration_sha256'] != sha(registration_path) or
            authorization['route'] != 'ETH_ORIGINAL_ORIGIN_TO_LINUX_DIRECT' or
            authorization['compressed_media_bytes'] != 861654036):
        raise ValueError('Missing bound human approval for the original media transfer')
    completion = read(MEDIA / 'completion.json')
    if (completion['status'] != 'PASS_TWENTY_AUTHORIZED_ORIGINAL_MEDIA_TRANSFERS_NOT_INPUT_ADMISSION' or
            completion['sources'] != 20 or len(completion['rows']) != 20 or
            completion['total_media_file_bytes'] != 871679467):
        raise ValueError('All original media transfers must complete before native mapping')
    downloaded = {row['source_name']: row for row in completion['rows']}
    if len(downloaded) != 20 or set(downloaded) != {row['source_name'] for row in rows}:
        raise ValueError('Download source denominator differs from the registration')
    for row in rows:
        proof = downloaded[row['source_name']]
        if (proof['status'] != 'PASS_ORIGINAL_ZIP_MEMBER_CRC_SHA' or
                proof['source_group'] != row['source_group'] or
                proof['original_member'] != row['member']['name'] or
                proof['identity']['bytes'] != row['member']['bytes'] or
                proof['identity']['crc32'] != row['member']['crc32']):
            raise ValueError('Downloaded member binding changed')
    return registration, downloaded, claim


def main(registration_path, contract_path, resume=False):
    if socket.gethostname() != 'inspur-NP5570M5':
        raise ValueError('This CPU entry is confined to the existing Linux training host')
    registration, downloaded, media_claim = check_download_admission(registration_path)
    if Path(contract_path).name != 'NATIVE_MAPPING_CONTRACT_V2.md':
        raise ValueError('The corrected pre-media mapping contract is required')
    bindings = dict(registration_sha256=sha(registration_path),
                    mapping_contract_sha256=sha(contract_path), mapper_sha256=sha(Path(__file__)),
                    mapping_validator_sha256=sha(Path(__file__).with_name('native_mapping_v2.py')),
                    window_planner_sha256=sha(Path(__file__).with_name('native_window_plan.py')),
                    media_completion_sha256=sha(MEDIA/'completion.json'),
                    media_launch_claim_sha256=sha(MEDIA/'launch_claim.json'))
    if (OUT/'completion.json').exists():
        raise ValueError('Completed native mapping must not be launched or replayed again')
    if resume:
        if read(OUT/'launch_claim.json')['bindings'] != bindings:
            raise ValueError('Explicit mapping resume differs from its frozen inputs/code')
        if (OUT/'failure.json').exists():
            raise ValueError('Actual failed mapping requires a separate reviewed recovery version')
    else:
        OUT.mkdir(parents=True, exist_ok=False)
        save(OUT/'launch_claim.json', dict(pid=os.getpid(), bindings=bindings,
             authorization=media_claim['authorization'], new_model_calls=0, new_optimizer_updates=0))
    # Imported only after completed-media/approval gates and the unique launch claim.
    import av
    accepted = []
    current_source = None
    try:
        for row in registration['rows']:
            current_source = row['source_name']
            if '/' in current_source or '\\' in current_source or '..' in current_source:
                raise ValueError('Unexpected registered source path')
            path = MEDIA / (current_source+'.webm')
            proof = downloaded[current_source]
            if Path(proof['path']).resolve() != path.resolve() or not path.resolve().is_relative_to(MEDIA.resolve()):
                raise ValueError('Media path does not bind the original download location')
            actual = identity(path)
            if actual != proof['identity']:
                raise ValueError('Accepted original media bytes changed')
            bundle_path = OUT/(current_source+'.mapping_bundle.json')
            if bundle_path.exists():
                bundle = read(bundle_path)
                if (bundle['status'] != 'PASS_ONE_ORIGINAL_NATIVE_MAPPING_AND_WINDOW_PLAN' or
                        bundle['bindings'] != bindings or bundle['clock']['source_sha256'] != actual['sha256'] or
                        validate_mapping(row, bundle['clock']) != bundle['mapping'] or
                        plan_windows(bundle['clock']) != bundle['windows']):
                    raise ValueError('Successful native mapping bundle changed')
                # Completed decode is reused; only pure bindings are checked.
            else:
                with av.open(str(path)) as container:
                    if len(container.streams.video) != 1:
                        raise ValueError('Ambiguous source video stream')
                    stream = container.streams.video[0]
                    rate = stream.average_rate
                    if rate is None or rate <= 0:
                        raise ValueError('Actual source has no positive declared average rate')
                    clock, mapped = clock_from_frames(row, actual, container.decode(stream))
                    clock.update(source_path=str(path), fps_num=rate.numerator, fps_den=rate.denominator,
                                 decoder='PyAV', decoder_version=av.__version__, video_stream_index=stream.index)
                bundle = dict(status='PASS_ONE_ORIGINAL_NATIVE_MAPPING_AND_WINDOW_PLAN',
                              bindings=bindings, clock=clock, mapping=mapped, windows=plan_windows(clock),
                              new_model_calls=0, new_optimizer_updates=0)
                save(bundle_path, bundle)
            accepted.append(dict(source_name=current_source, source_group=row['source_group'],
                                 bundle_path=str(bundle_path), bundle_sha256=sha(bundle_path),
                                 native_frames=bundle['clock']['n_frames'], windows=len(bundle['windows'])))
            progress(dict(completed_sources=len(accepted), registered_sources=20, last_source=current_source,
                          new_model_calls=0))
            print(json.dumps(accepted[-1], ensure_ascii=False), flush=True)
        save(OUT/'completion.json', dict(status='PASS_TWENTY_ORIGINAL_NATIVE_MAPPINGS_NOT_PROCESSOR_OR_SOURCE_ADMISSION',
             sources=20, rows=accepted, bindings=bindings, new_model_calls=0, new_optimizer_updates=0,
             known_source_separation='UNVERIFIED', processor_inputs='UNVERIFIED'))
    except Exception as error:
        save(OUT/'failure.json', dict(status='FAILED_NATIVE_MAPPING_OR_WINDOW_PLAN', source_name=current_source,
             error_type=type(error).__name__, error=str(error), completed_sources=len(accepted),
             registered_sources=20, successful_bundles_retained=accepted,
             new_model_calls=0, new_optimizer_updates=0))
        raise


if __name__ == '__main__':
    os.environ['CUDA_VISIBLE_DEVICES'] = ''  # Only this CPU process; no chain/GPU launch.
    main(Path(sys.argv[1]), Path(sys.argv[2]), resume='--resume' in sys.argv[3:])
