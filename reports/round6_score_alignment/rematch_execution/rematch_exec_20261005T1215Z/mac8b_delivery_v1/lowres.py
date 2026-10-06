"""Frozen Mac video budget; CUDA relocation keeps the explicit video contract."""
import copy
import math
from pathlib import Path
import numpy as np

ROOT = Path('/home/inspur/aic_video_work')
MAX_FRAMES = 64
MAX_PIXELS = 32768
MAX_SEQUENCE = 6144

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def lowres_encode(processor, **kwargs):
    videos = kwargs.pop('videos')
    metadata = kwargs.pop('video_metadata')
    require(len(videos) == len(metadata) == 1, 'one video per processor call required')
    n = int(videos[0].shape[0])
    require(1 <= n <= MAX_FRAMES, 'unregistered sampled frame count')
    require(kwargs.pop('do_sample_frames', False) is False, 'implicit resampling forbidden')
    require(kwargs.pop('truncation', False) is False, 'truncation forbidden')
    padding = kwargs.pop('padding', True)
    tensors = kwargs.pop('return_tensors', 'pt')
    require(not any(k.endswith('_kwargs') for k in kwargs), 'nested processor override forbidden')
    encoded = processor(**kwargs, videos=videos,
        text_kwargs=dict(padding=padding, truncation=False),
        common_kwargs=dict(return_tensors=tensors),
        videos_kwargs=dict(video_metadata=copy.deepcopy(metadata), do_sample_frames=False,
            return_metadata=True, size=dict(shortest_edge=n*1024, longest_edge=n*MAX_PIXELS)))
    grid = encoded['video_grid_thw'][0].tolist()
    patch = processor.video_processor.patch_size
    require(int(grid[1]*grid[2]*patch*patch) <= MAX_PIXELS, 'actual processed pixel budget exceeded')
    require(encoded['input_ids'].shape[1] <= MAX_SEQUENCE, 'expanded Mac inference sequence exceeds 6144')
    return encoded

def clip_plan(row):
    fps = row['fps_num']/row['fps_den']; total = row['n_frames']
    sf = max(0, min(int(math.ceil(max(0., row['clip_start_sec'])*fps)), total-1))
    ef = max(sf+1, min(int(math.floor(row['clip_end_sec']*fps)), total-1))
    count = ef-sf+1; samples = min(MAX_FRAMES, count)
    local = [int(round(x)) for x in np.linspace(0, count-1, samples)]
    return dict(source_total_frames=total, source_fps=fps, clip_start_frame_abs=sf,
        clip_end_frame_abs=ef, n_frames_in_clip=count, n_sampled=samples,
        clip_local_indices=local, absolute_indices=[sf+i for i in local])

def decode_dev_av(row, tc, np, decord_unused):
    # Same PyAV ordinal/clock contract as Mac training; paths map to pinned Linux media.
    import av
    plan=clip_plan(row); source=Path(row['source_path']); resolved=source.resolve()
    require(ROOT in resolved.parents and not source.is_symlink(), 'dev source outside Linux workspace')
    selected={index:None for index in plan['absolute_indices']}; clocks={}; origin=None; decoded=0
    with av.open(str(source)) as container:
        stream=container.streams.video[0]; fps=float(stream.average_rate)
        require(abs(fps-plan['source_fps']) <= max(1e-6,fps*1e-6), 'PyAV FPS mismatch')
        declared=int(stream.frames); require(declared in (0,row['n_frames']), 'PyAV frame count mismatch')
        for index,frame in enumerate(container.decode(stream)):
            decoded=index+1
            require(frame.pts is not None and frame.time_base is not None, 'missing PyAV PTS')
            current=float(frame.pts*frame.time_base)
            if index==0: origin=current
            if index in selected:
                selected[index]=frame.to_ndarray(format='rgb24'); clocks[index]=current
            if declared and index>=plan['absolute_indices'][-1]: break
        if not declared: require(decoded==row['n_frames'], 'full sequential count mismatch')
    require(origin is not None and all(v is not None for v in selected.values()), 'missing selected ordinal')
    numeric_ids=sorted(set([0]+plan['absolute_indices']))
    timestamps=[origin if i==0 else clocks[i] for i in numeric_ids]; tolerance=1/fps+1e-6
    residual=max(abs((t-origin)-i/fps) for i,t in zip(numeric_ids,timestamps))
    require(abs(origin)<=tolerance and residual<=tolerance and all(a<b for a,b in zip(timestamps,timestamps[1:])),
        'selected source clock violates frozen approximate CFR gate')
    frames=np.stack([selected[i] for i in plan['absolute_indices']])
    require(tuple(frames.shape)==(plan['n_sampled'],row['height'],row['width'],3), 'decoded geometry mismatch')
    metadata=dict(fps=fps,frames_indices=plan['clip_local_indices'],total_num_frames=plan['n_frames_in_clip'],video_backend='pyav')
    info={**plan,'current_clock_numeric_ids':numeric_ids,'current_pyav_pts_start_sec':timestamps,
        'current_source_origin_sec':origin,'max_selected_cfr_residual_sec':residual,
        'one_frame_tolerance_sec':tolerance,'clock_contract':'R7_APPROXIMATE_CFR_PYAV_SEQUENTIAL_SELECTED_FRAME_GATE',
        'old_pts_source_byte_equality_claimed':False,'exact_native_pts_binding_claimed':False,
        'PyAV_Decord_pixel_equality_claimed':False}
    return frames,metadata,info

def verify_cuda_adapter(model, admission):
    import torch
    from safetensors.torch import load_file
    from train_sft import unique_parameters
    from verify_saved_smoke import canonical_frozen_hash
    import json
    report=json.loads((Path(admission['adapter']).parent/'training_evidence/train_report.json').read_text())
    require(sum(p.numel() for _,p in unique_parameters(model))==8782459120, 'logical parameter count changed')
    require(canonical_frozen_hash(model,torch)==report['freeze_evidence']['adapter_off'], 'relocated base bytes changed')
    stored=load_file(str(Path(admission['adapter'])/'adapter_model.safetensors'),device='cpu')
    actual={n.replace('.default.','.'):p for n,p in model.named_parameters() if 'lora_' in n}
    require(set(actual)==set(stored) and len(actual)==288, 'relocated LoRA key set changed')
    require(all(p.dtype==stored[n].dtype and torch.equal(p.detach().cpu(),stored[n]) for n,p in actual.items()),
        'relocated LoRA tensor bytes changed')
    targets={n.removeprefix('base_model.model.') for n,m in model.named_modules()
        if hasattr(m,'lora_A') and 'default' in m.lora_A}
    require(targets==set(report['exact_language_targets']) and len(targets)==144, 'relocated language targets changed')
    require(not any(p.requires_grad for p in model.parameters()), 'inference parameters unexpectedly trainable')
    return dict(status='PASS_MAC_ADAPTER_CUDA_RELOCATION',tensors=288,targets=144,logical_parameters=8782459120,
        byte_equal=True,base_sha256=report['freeze_evidence']['adapter_off']['sha256'])
