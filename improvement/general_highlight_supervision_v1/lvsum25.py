"""First original-media native mapping and real I3D RGB preparation, no model calls."""
from fractions import Fraction
import os
from pathlib import Path
import shutil
import sys
import time
import traceback

os.environ['CUDA_VISIBLE_DEVICES']=''

import numpy as np

from common import ROOT, WORK, read, ref, save

OLD_CODE=WORK/'highlight_source_admission_20261021_v1/matched_hl_pilot16/code'
sys.path.insert(0,str(OLD_CODE))
sys.path.append(str(WORK/'highlight_source_control_20261021_v1'))
sys.path.append(str(WORK/'i3d_umt_cross_domain_20261021_v1/crossdata12/code'))
from native_audit12 import native_clock, known_isolation
from prepare_raw import resize_crop

TARGET=ROOT/'native25'


def render(media,clock,path):
    import av
    pts=[Fraction(x) for x in clock['PTS']];count=len(pts)
    cells=(count+63)//64
    rgb=np.lib.format.open_memmap(path/'rgb.npy',mode='w+',dtype=np.uint8,shape=(cells,8,224,224,3))
    wanted={}
    for group,start in enumerate(range(0,count,64)):
        for slot in range(8):wanted.setdefault(min(start+8*slot,count-1),[]).append((group,slot))
    observed=set();decoded=0
    with av.open(media['path']) as container:
        stream=container.streams.video[0];stream.codec_context.thread_count=1
        for ordinal,frame in enumerate(container.decode(stream)):
            if ordinal>=count or Fraction(frame.pts)*frame.time_base!=pts[ordinal]:
                raise ValueError('First I3D render differs from original native clock')
            if ordinal in wanted:
                image=resize_crop(frame)
                for group,slot in wanted[ordinal]:rgb[group,slot]=image
                observed.add(ordinal)
            decoded+=1
    if decoded!=count or observed!=set(wanted):raise ValueError('Missing first real RGB input')
    rgb.flush();del rgb
    array=np.load(path/'rgb.npy',mmap_mode='r',allow_pickle=False)
    if array.shape!=(cells,8,224,224,3) or array.dtype!=np.uint8:raise ValueError('Input serialization differs')
    np.save(path/'groups.npy',np.arange(count,dtype=np.int64)//64,allow_pickle=False)
    save(path/'input_acceptance.json',dict(rgb=ref(path/'rgb.npy'),groups=ref(path/'groups.npy'),
        cells=cells,native_frames=count,all_sample_native_ordinals=sorted(wanted),
        native_clock=ref(path/'clock.json'),real_decode_count=decoded,short_final_pixels_only_repeated=True,
        labels_never_padded_or_truncated=True,first_render=True))


def admit(row,registration,annotations):
    path=TARGET/row['sid'];path.mkdir()
    media=row['media'];isolation=known_isolation(media)
    clock=native_clock(Path(media['path']));save(path/'clock.json',clock)
    start=Fraction(clock['first_PTS_exact']);end=Fraction(clock['physical_end_exact'])-start
    source_annotations=[a for a in annotations if a['video_path']==row['source']['url']]
    if len(source_annotations)!=row['source']['annotators']:raise ValueError('Original reviewer rows differ')
    if len({a['annotator_id'] for a in source_annotations})!=len(source_annotations):
        raise ValueError('Repeated original annotator ID is not an independent reviewer')
    for a in source_annotations:
        for s in a['summary_timestamps']:
            if not 0<=Fraction(str(s['start_time']))/1000<Fraction(str(s['end_time']))/1000<=end:
                raise ValueError('Original annotation endpoint outside original media; no repair or clipping')
    # Preserve each entire author's original row; no rounded timestamps or reviewer selection.
    save(path/'original_annotations.json',source_annotations)
    pixels=((clock['native_frames']+63)//64)*8*224*224*3
    if shutil.disk_usage(ROOT).free<pixels+2*24857564:
        raise ValueError('Measured native RGB footprint exceeds current capacity')
    render(media,clock,path)
    result=dict(sid=row['sid'],media=media,clock=ref(path/'clock.json'),
        annotations=ref(path/'original_annotations.json'),input=ref(path/'input_acceptance.json'),
        role=registration['roles'][row['source']['source_hash']],isolation=isolation,
        publisher=row['source']['host'],original_source=row['source'],
        native_frames=clock['native_frames'],duration_seconds=float(end),
        raw_PTS_origin=str(start),all_reviewers=len(source_annotations),
        summary_preference_not_explicit_ordinary=True,original_ms_without_quantization=True)
    save(path/'acceptance.json',result)
    print('NATIVE_INPUT_ACCEPTED',row['sid'],result['native_frames'],result['all_reviewers'],flush=True)
    return ref(path/'acceptance.json')


def main():
    TARGET.mkdir()
    save(TARGET/'registration.json',dict(scope='First native clocks/labels/real RGB for new8 non-sport recordings',
        author_annotation=ref(ROOT/'lvsum20/annotations__lvsum_72_dataset.json'),
        helpers={name:ref(path) for name,path in {
            'native_clock_and_known_isolation':WORK/'highlight_source_control_20261021_v1/native_audit12.py',
            'original_resize':WORK/'i3d_umt_cross_domain_20261021_v1/crossdata12/code/prepare_raw.py'}.items()},
        no_GPU=True,no_repeat_old_decode_or_model=True,malformed_whole_source_exclusion_only=True))
    started=time.monotonic()
    registration=read(ROOT/'media24/registration.json')
    annotations=read(ROOT/'lvsum20/annotations__lvsum_72_dataset.json')
    accepted=[];failed=[]
    for route in registration['selected']:
        sid='L'+route['source']['source_hash'][:12]
        media_acceptance=ROOT/'media24'/(sid+'_acceptance.json')
        media_failure=ROOT/'media24'/(sid+'_failure.json')
        while not media_acceptance.exists() and not media_failure.exists():
            if time.monotonic()-started>1800:raise TimeoutError('Bounded first media stage elapsed')
            time.sleep(2)
        if media_failure.exists():
            failed.append(dict(sid=sid,reason='Original media stage failed; no repeated download'))
            continue
        row=read(media_acceptance)
        try:accepted.append(admit(row,registration,annotations))
        except Exception as error:
            failure=dict(sid=row['sid'],error=repr(error),traceback=traceback.format_exc(),
                whole_source_excluded_before_training=True,no_automatic_repeat=True)
            failed.append(failure);save(TARGET/(row['sid']+'_failure.json'),failure)
            print('NATIVE_INPUT_FAILED',row['sid'],repr(error),flush=True)
    save(TARGET/'completion.json',dict(state='NEW_NATIVE_INPUT_ADMISSION_TERMINAL',
        accepted=accepted,failed=failed,accepted_sources=len(accepted),
        model_calls=0,original_labels_unchanged=True,all_failures_preserved=True))


if __name__=='__main__':main()
