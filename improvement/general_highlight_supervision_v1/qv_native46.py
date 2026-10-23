"""One original decode per QV member: native clock and eight real samples / 2 s."""
from fractions import Fraction
from pathlib import Path
import sys

import av
import numpy as np

from common import ROOT, WORK, read, ref, save

TARGET = ROOT / 'qv_native46'
ENGINEERING = WORK / 'i3d_umt_cross_domain_20261021_v1'
sys.path.insert(0, str(ENGINEERING))
sys.path.insert(0, str(ENGINEERING / 'crossdata12/code'))
from prepare_raw import resize_crop
sys.path.insert(0, str(WORK / 'highlight_source_control_20261021_v1'))
from native_audit12 import known_isolation


def time_groups(points):
    origin = points[0]
    result = np.asarray([int((p-origin)//2) for p in points], dtype=np.int64)
    if result[0] != 0 or (np.diff(result) < 0).any():
        raise ValueError('Nonmonotone original 2-second groups')
    return result


def finalize(samples, indices, last_frame, last_index):
    missing = 8-len(samples)
    if missing:
        image = resize_crop(last_frame)
        samples.extend([image.copy() for _ in range(missing)])
        indices.extend([last_index]*missing)
    return np.stack(samples), indices


def decode(source, folder):
    points, durations, cells, native_indices = [], [], [], []
    samples, indices = [], []
    origin = None
    group = 0
    last_frame = None
    geometry = None
    with av.open(source['media']['path']) as container:
        if len(container.streams.video) != 1:
            raise ValueError('Original member video stream is ambiguous')
        stream = container.streams.video[0]
        stream.codec_context.thread_count = 1
        for ordinal, frame in enumerate(container.decode(stream)):
            if frame.pts is None or frame.time_base is None:
                raise ValueError('Original frame PTS missing')
            point = Fraction(frame.pts)*frame.time_base
            if points and point <= points[-1]:
                raise ValueError('Original presentation order nonmonotone')
            if origin is None:
                origin = point
                geometry = (frame.width, frame.height)
            if geometry != (frame.width, frame.height):
                raise ValueError('Original frame geometry varies')
            current = int((point-origin)//2)
            if current != group:
                if current != group+1 or last_frame is None:
                    raise ValueError('An entire 2-second cell has no original frames')
                images, used = finalize(samples, indices, last_frame, ordinal-1)
                cells.append(images)
                native_indices.append(used)
                samples, indices, group = [], [], current
            relative = point-origin-Fraction(2*group)
            needed = 0
            while len(samples)+needed < 8 and relative >= Fraction(2*(len(samples)+needed)+1, 8):
                needed += 1
            if needed:
                image = resize_crop(frame)
                samples.extend([image.copy() for _ in range(needed)])
                indices.extend([ordinal]*needed)
            points.append(point)
            duration = getattr(frame, 'duration', None)
            durations.append(Fraction(duration)*frame.time_base if duration else None)
            last_frame = frame
        if not points or durations[-1] is None or durations[-1] <= 0:
            raise ValueError('Original positive final-frame duration is required')
        images, used = finalize(samples, indices, last_frame, len(points)-1)
        cells.append(images)
        native_indices.append(used)
        physical_end = points[-1]+durations[-1]-origin
        clock = dict(PTS=[str(p) for p in points], first_PTS_exact=str(origin),
            physical_end_exact=str(points[-1]+durations[-1]), native_frames=len(points),
            frame_durations=[str(d) if d else None for d in durations],
            width=geometry[0],height=geometry[1],decoder=av.__version__,
            no_frame_resampling=True,no_label_padding_truncation_or_stretch=True,
            rate_diagnostic_only=str(stream.average_rate),
            container_duration_diagnostic_only=container.duration)
    groups = time_groups(points)
    save(folder/'clock.json',clock)
    indices = np.asarray(native_indices,dtype=np.int64)
    rgb = np.stack(cells)
    if not np.array_equal(groups[indices],np.arange(len(rgb))[:,None]*np.ones((1,8),dtype=np.int64)):
        raise ValueError('Sample crossed its exact native cell')
    rows = read(source['annotations']['path'])
    for row in rows:
        if any(Fraction(str(stop)) > physical_end for first,stop in row['relevant_windows']):
            raise ValueError('Original annotation exceeds actual media; no clipping permitted')
        if any(min(Fraction(i*2+2),Fraction(str(row['duration']))) > physical_end
               for i in row['relevant_clip_ids']):
            raise ValueError('Original annotated 2-second cell exceeds native media')
    with (folder/'rgb.npz').open('xb') as out:
        np.savez_compressed(out,rgb=rgb,native_indices=indices)
    with (folder/'groups.npy').open('xb') as out:
        np.save(out,groups,allow_pickle=False)
    with np.load(folder/'rgb.npz',allow_pickle=False) as restored:
        if not np.array_equal(rgb,restored['rgb']) or not np.array_equal(indices,restored['native_indices']):
            raise ValueError('First real CPU input reload differs')
    return dict(clock=ref(folder/'clock.json'),rgb=ref(folder/'rgb.npz'),
        groups=ref(folder/'groups.npy'),cells=len(rgb),native_frames=len(points),
        physical_duration_exact=str(physical_end),RGB_dtype=str(rgb.dtype),
        shape=list(rgb.shape),visual_repeat_samples=sum(8-len(set(x)) for x in indices.tolist()),
        repeated_visual_samples_not_repeated_labels=True,
        native_indices_validation=True,original_all_reviewers=3)


def main():
    TARGET.mkdir()
    source_completion=read(ROOT/'author_qv45/completion.json')
    save(TARGET/'registration.json',dict(source_completion=ref(ROOT/'author_qv45/completion.json'),
        original_two_second_cell=True,samples_per_cell=8,temporal_sample_offsets=[str(Fraction(2*i+1,8)) for i in range(8)],
        select_first_native_PTS_at_or_after_target_inside_cell=True,
        last_in_cell_visual_repeat_if_necessary=True,labels_never_padded=True,
        original_author_duration_is_diagnostic_not_time_stretch=True,
        source_roles_frozen_before_model=True,no_GPU=True))
    accepted=[];failures=[]
    for source in source_completion['accepted']:
        sid='Q'+source['source_hash'][:12]
        folder=TARGET/sid;folder.mkdir()
        try:
            if ref(source['media']['path'])!=source['media'] or ref(source['annotations']['path'])!=source['annotations']:
                raise ValueError('Accepted original member or annotation identity differs')
            isolation=known_isolation(source['media'])
            result=decode(source,folder)
            row=dict(source,sid=sid,**result,isolation=isolation)
            save(folder/'acceptance.json',row);accepted.append(ref(folder/'acceptance.json'))
            print('QV_NATIVE_ACCEPTED',sid,row['native_frames'],row['cells'],flush=True)
        except Exception as error:
            failure=dict(sid=sid,error=repr(error),traceback=__import__('traceback').format_exc(),
                whole_source_excluded_no_label_repair=True)
            save(folder/'failure.json',failure);failures.append(failure)
            print('QV_SOURCE_NATIVE_REJECTED',sid,repr(error),flush=True)
    save(TARGET/'completion.json',dict(state='FIRST_NATIVE_MEMBER_INPUTS_COMPLETE',
        accepted=accepted,whole_source_failures=failures,accepted_sources=len(accepted),
        source_roles_not_reassigned_after_exclusion=True,new_model_calls=0))


if __name__=='__main__':
    try:
        main()
    except BaseException:
        if TARGET.exists():save(TARGET/'failure.json',dict(traceback=__import__('traceback').format_exc()))
        raise
