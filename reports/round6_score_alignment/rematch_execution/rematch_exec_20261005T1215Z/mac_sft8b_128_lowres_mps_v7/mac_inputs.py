"""128-frame PyAV sequential decoding and the frozen original processor contract."""
import ast
import math
from pathlib import Path
from types import SimpleNamespace
import json
import numpy as np

from sft_contract import require
import train_sft as original

HERE=Path(__file__).resolve().parent
ROOT=Path('/Users/choubk/codex-workspace')

def frozen_prompt(path):
    tree=ast.parse(Path(path).read_text())
    found=[ast.literal_eval(node.value) for node in tree.body if isinstance(node,ast.Assign) and
           any(isinstance(target,ast.Name) and target.id=='PROMPT' for target in node.targets)]
    require(len(found)==1 and isinstance(found[0],str),'frozen prompt identity missing')
    return SimpleNamespace(PROMPT=found[0],MAX_FRAMES=128,MAX_PIXELS=32768)

def clip_plan(row,max_frames=128):
    fps=row['fps_num']/row['fps_den'];total=row['n_frames']
    sf=max(0,min(int(math.ceil(max(0.0,row['clip_start_sec'])*fps)),total-1))
    ef=max(sf+1,min(int(math.floor(row['clip_end_sec']*fps)),total-1))
    count=ef-sf+1;samples=min(max_frames,count)
    local=[int(round(x)) for x in np.linspace(0,count-1,samples)]
    return dict(source_total_frames=total,source_fps=fps,clip_start_frame_abs=sf,clip_end_frame_abs=ef,
                n_frames_in_clip=count,n_sampled=samples,clip_local_indices=local,absolute_indices=[sf+i for i in local])

def decode_av_clip(row,tc,np,decord_unused):
    import av
    plan=clip_plan(row)
    mapping=json.loads((HERE/'source_map.json').read_text())
    source=Path(mapping[row['source_path']]);resolved=source.resolve()
    require(ROOT in resolved.parents and not source.is_symlink(),'Mac training media outside workspace')
    selected={index:None for index in plan['absolute_indices']};clocks={};origin=None;decoded=0
    with av.open(str(source)) as container:
        stream=container.streams.video[0];fps=float(stream.average_rate)
        require(abs(fps-plan['source_fps'])<=max(1e-6,fps*1e-6),'current PyAV source FPS mismatch')
        declared=int(stream.frames)
        require(declared in (0,row['n_frames']),'current PyAV declared frame count mismatch')
        for index,frame in enumerate(container.decode(stream)):
            decoded=index+1
            require(frame.pts is not None and frame.time_base is not None,'missing current PyAV PTS')
            current=float(frame.pts*frame.time_base)
            if index==0:origin=current
            if index in selected:
                selected[index]=frame.to_ndarray(format='rgb24');clocks[index]=current
            if declared and index>=plan['absolute_indices'][-1]:break
        if not declared:require(decoded==row['n_frames'],'current full sequential frame count mismatch')
    require(origin is not None and all(value is not None for value in selected.values()),'sequential selected ordinal missing')
    numeric_ids=sorted(set([0]+plan['absolute_indices']));timestamps=[origin if i==0 else clocks[i] for i in numeric_ids]
    tolerance=1/fps+1e-6
    residual=max(abs((timestamp-origin)-index/fps) for index,timestamp in zip(numeric_ids,timestamps))
    require(abs(origin)<=tolerance and residual<=tolerance and all(a<b for a,b in zip(timestamps,timestamps[1:])),
            'current selected source clock violates fixed R7 approximate CFR/origin gate')
    frames=np.stack([selected[i] for i in plan['absolute_indices']])
    require(tuple(frames.shape)==(plan['n_sampled'],row['height'],row['width'],3),'PyAV decoded geometry mismatch')
    metadata=dict(fps=fps,frames_indices=plan['clip_local_indices'],total_num_frames=plan['n_frames_in_clip'],video_backend='pyav')
    info={**plan,'current_clock_numeric_ids':numeric_ids,'current_pyav_pts_start_sec':timestamps,
          'current_source_origin_sec':origin,'max_selected_cfr_residual_sec':residual,'one_frame_tolerance_sec':tolerance,
          'clock_contract':'R7_APPROXIMATE_CFR_PYAV_SEQUENTIAL_SELECTED_FRAME_GATE',
          'old_pts_source_byte_equality_claimed':False,'exact_native_pts_binding_claimed':False,
          'PyAV_Decord_pixel_equality_claimed':False}
    return frames,metadata,info

original.decode_cfr_clip=decode_av_clip
build_example=original.build_example
