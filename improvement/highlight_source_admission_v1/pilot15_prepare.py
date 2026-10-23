"""First I3D RGB inputs, audited against already accepted exact native clocks."""
from fractions import Fraction
import json
from pathlib import Path
import shutil
import time

from pilot15_common import ADMISSION, ROOT, ENGINEERING, checked, read, ref, save, native_cells


def render(source):
    import av
    import numpy as np
    from prepare_raw import resize_crop
    stem=source['source'];target=ROOT/'inputs'/stem;target.mkdir()
    clock=read(checked(source['clock']));pts=[Fraction(x) for x in clock['PTS']]
    bounds,samples,groups=native_cells(len(pts))
    np.save(target/'groups.npy',groups,allow_pickle=False)
    rgb=np.lib.format.open_memmap(target/'rgb.npy',mode='w+',dtype=np.uint8,
        shape=(len(bounds),8,224,224,3))
    wanted={}
    for group,indices in enumerate(samples):
        for slot,ordinal in enumerate(indices):wanted.setdefault(int(ordinal),[]).append((group,slot))
    seen=set();count=0;start=time.monotonic()
    with av.open(str(checked(source['media']))) as container:
        stream=container.streams.video[0];stream.codec_context.thread_count=1
        for ordinal,frame in enumerate(container.decode(stream)):
            if ordinal>=len(pts) or Fraction(frame.pts)*frame.time_base!=pts[ordinal]:
                raise ValueError('First I3D pixel render differs from accepted native clock')
            if ordinal in wanted:
                image=resize_crop(frame)
                for group,slot in wanted[ordinal]:rgb[group,slot]=image
                seen.add(ordinal)
            count+=1
    if count!=len(pts) or seen!=set(wanted):raise ValueError('Missing first real I3D inputs')
    rgb.flush();del rgb
    # First serialization validation, not another decoder/processor call.
    array=np.load(target/'rgb.npy',mmap_mode='r',allow_pickle=False)
    if array.dtype!=np.uint8 or array.shape!=(len(bounds),8,224,224,3):
        raise ValueError('First serialized RGB geometry failed')
    save(target/'acceptance.json',dict(source=stem,rgb=ref(target/'rgb.npy'),
        groups=ref(target/'groups.npy'),cells=len(bounds),native_frames=count,
        exact_pts_sample=[[str(pts[i]) for i in indices] for indices in samples],
        first_real_I3D_RGB_render=True,accepted_clock_adopted=source['clock'],
        short_final_bin_pixel_repeats_only=True,no_label_padding=True,seconds=time.monotonic()-start))
    print('INPUT_ACCEPTED',stem,len(bounds),flush=True)
    return ref(target/'acceptance.json')


def main():
    protocol=read(ROOT/'protocol.json')
    completion=read(ADMISSION/'native_remaining14_completion.json')
    sources=[read(checked(value)) for value in completion['sources']]
    for source in sources:
        source['role']=completion['source_roles'][source['source']]
    expected=sum(((source['native_frames']+63)//64)*8*224*224*3 for source in sources)
    free=shutil.disk_usage(ROOT).free
    if free<expected+24856937*2+100_000_000:raise ValueError('Actual first RGB/output footprint exceeds capacity')
    baseline=Path('/home/inspur/aic_video_work/semantic_context_production_20261016_v1/package/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip')
    baseline_ref=ref(baseline)
    if baseline_ref['bytes']!=384630 or baseline_ref['sha256']!=protocol['protected_baseline_sha256']:
        raise ValueError('Protected40.47 binding changed')
    control=read(ENGINEERING/'crossdata12/frozen_final.json')['checkpoint'];checked(control)
    save(ROOT/'registration.json',dict(sources=sources,protected_baseline=baseline_ref,
        control_checkpoint=control,expected_RGB_bytes=expected,actual_disk_free_bytes=free,
        old_STOP_unchanged=True,old_control_not_40_47_exact_prediction=True,
        research_only_pilot_not_T_main_cohort=True))
    (ROOT/'inputs').mkdir()
    outputs=[render(source) for source in sources]
    save(ROOT/'input_acceptance.json',dict(state='PASS4_FIRST_REAL_I3D_INPUTS',sources=outputs,
        no_new_model_calls=True,held_labels_not_loaded_into_model_or_loss=True))


if __name__=='__main__':main()
