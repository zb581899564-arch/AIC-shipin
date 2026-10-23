"""First new native64 B inputs, stored once; no model weights or GPU."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
from bisect import bisect_left
from fractions import Fraction
import hashlib
from pathlib import Path
import sys

import av
import numpy as np
import torch
from transformers import AutoProcessor

from time_control50_common import ROOT,RUN,WORK,read,ref,save,checked,runtime


def source_windows(source):
    clock=read(checked(source['clock']))
    origin=Fraction(clock['first_PTS_exact'])
    points=[Fraction(p)-origin for p in clock['PTS']]
    end=Fraction(clock['physical_end_exact'])-origin
    normalized=dict(normalized_exact_pts=[str(p) for p in points],physical_end_exact=str(end))
    sys.path.insert(0,str(WORK/'human_reference_iteration_20261013_v1/code'))
    from native_window_plan import plan_windows
    return clock,points,plan_windows(normalized)


def decode_window(source, clock, points, window, folder):
    ordinals=window['source_frame_ordinals'];origin=Fraction(clock['first_PTS_exact'])
    expected={points[i]+origin:i for i in ordinals};pictures={}
    with av.open(source['media']['path']) as container:
        stream=container.streams.video[0];stream.codec_context.thread_count=1
        container.seek(int((points[ordinals[0]]+origin)/stream.time_base),stream=stream,backward=True,any_frame=False)
        for frame in container.decode(stream):
            actual=Fraction(frame.pts)*frame.time_base
            if actual>points[ordinals[-1]]+origin:break
            if actual in expected:
                pictures[expected[actual]]=frame.to_ndarray(format='rgb24')
    if set(pictures)!=set(ordinals):raise ValueError('First native64 decode missed a registered original PTS')
    arrays=np.stack([pictures[i] for i in ordinals]);path=folder/'frames.npz'
    with path.open('xb') as out:np.savez_compressed(out,rgb=arrays)
    rate=Fraction(clock['rate_diagnostic_only'])
    meta=dict(case_id=folder.name,source_name=source['source'],source_path=source['media']['path'],
        source_sha256=source['media']['sha256'],source_bytes=source['media']['bytes'],
        source_total_frames=clock['native_frames'],width=clock['width'],height=clock['height'],
        fps_num=rate.numerator,fps_den=rate.denominator,
        all_source_exact_pts=[str(p) for p in points],original_clock_origin_exact=str(origin),
        window_start=window['start_exact'],window_end=window['end_exact'],
        source_frame_ordinals=ordinals,sample_exact_pts=window['sample_exact_pts'],
        pixel_sha256=[hashlib.sha256(image.tobytes()).hexdigest() for image in arrays],
        frame_array_path=str(path),frame_array_sha256=ref(path)['sha256'],
        reference_available_to_inference=False,audio_observed=False)
    save(folder/'input.json',meta)
    return meta


def encode_case(rt,processor,meta,folder):
    frames=rt.baseline_frames(meta)
    encoded,detail=rt.encode(processor,meta,frames,Fraction(meta['window_start']),rt.EMPTY_PROMPT)
    values={k:v.contiguous().cpu().numpy() for k,v in encoded.items() if torch.is_tensor(v)}
    non_tensor={k:v for k,v in encoded.items() if not torch.is_tensor(v)}
    path=folder/'encoded.npz'
    with path.open('xb') as out:np.savez_compressed(out,**values)
    with np.load(path,allow_pickle=False) as data:
        restored={k:torch.from_numpy(data[k].copy()) for k in data.files}
    if rt.tensor_signature(restored)!=detail['tensor_signature']:
        raise ValueError('First CPU cache roundtrip signature differs')
    grid=restored['video_grid_thw']
    if grid.shape!=(1,3) or int(grid[0,0])*2!=64:raise ValueError('Actual video temporal grid is not native64')
    if restored['input_ids'].shape[1]>16384 or detail['physical_frames']!=64:
        raise ValueError('Original native64 processor budget differs')
    if torch.cuda.is_initialized():raise ValueError('CPU input preparation initialized CUDA')
    record=dict(input=ref(folder/'input.json'),encoded=ref(path),detail=detail,
        input_tokens=int(restored['input_ids'].shape[1]),
        non_tensor_inputs=non_tensor,
        exact_native64_ordinals=meta['source_frame_ordinals'],native_sample_PTS=meta['sample_exact_pts'],
        source_start_exact=meta['window_start'],source_end_exact=meta['window_end'],
        actual_serialized_CPU_QA=True,labels_not_in_input=True)
    save(folder/'CPU_acceptance.json',record)
    return ref(folder/'CPU_acceptance.json')


def main():
    torch.set_num_threads(2)
    registration=read(ROOT/'registration.json');source=registration['source'];checked(source['media'])
    rt=runtime();config=read(RUN/'b_score_aligned_package_v4/config.json')
    processor=AutoProcessor.from_pretrained(config['model_dir'],local_files_only=True,min_pixels=131072,max_pixels=131072)
    clock,points,windows=source_windows(source)
    save(ROOT/'window_registration.json',dict(source=source,windows=windows,no_label_time_stretch=True,
        original_window_planner=ref(WORK/'human_reference_iteration_20261013_v1/code/native_window_plan.py')))
    (ROOT/'inputs').mkdir();accepted=[]
    for window in windows:
        folder=ROOT/'inputs'/f"D_W{window['index']:03d}";folder.mkdir()
        meta=decode_window(source,clock,points,window,folder)
        accepted.append(encode_case(rt,processor,meta,folder))
        print('ORIGINAL_TIME_CPU',len(accepted),len(windows),flush=True)
    save(ROOT/'CPU_completion.json',dict(state='ALL_FIRST_ORIGINAL_TIME_NATIVE64_INPUTS_PASS',accepted=accepted,
        windows=len(accepted),CPU_only=True,CUDA_initialized=False,
        runtime=ref(Path(rt.__file__)),config=ref(RUN/'b_score_aligned_package_v4/config.json')))


if __name__=='__main__':main()
