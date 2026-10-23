"""Exactly eight frozen PANN forwards, preserving native coarse output units."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import json
import time
import numpy as np
import torch
from common import ROOT, RUN, read, write, checked, reference
from model import load


def main():
    sys.path.insert(0, str(RUN/'temporal_sft8b_v1'))
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    model, tensors = load()
    model = model.cuda().eval()
    torch.cuda.reset_peak_memory_stats()
    output = ROOT/'event_outputs';output.mkdir()
    captured = []
    handle = model.att_block.register_forward_hook(lambda module, args, result: captured.append(result[2].detach()))
    rows, start = [], time.monotonic()
    for item in read(ROOT/'input_acceptance.json')['rows']:
        with np.load(checked(item['input_ref']), allow_pickle=False) as saved:
            values = torch.from_numpy(saved['wave'].copy())[None].cuda()
        print('BEGIN', item['uid'], flush=True)
        with torch.inference_mode():
            result = model(values)
        torch.cuda.synchronize()
        segment = captured.pop().transpose(1, 2)[0].cpu().numpy()
        framewise = result['framewise_output'][0].cpu().numpy()
        clipwise = result['clipwise_output'][0].cpu().numpy()
        target = output/(item['uid']+'.npz')
        np.savez_compressed(target, segment=segment, framewise=framewise, clipwise=clipwise)
        if captured or not np.isfinite(segment).all() or not ((segment >= 0)&(segment <= 1)).all():
            raise ValueError('Frozen event output invalid; raw retained')
        rows.append(dict(uid=item['uid'], input=item, output_ref=reference(target),
            segment_steps=len(segment), interpolated_mel_steps=len(framewise),
            coarse_stride_seconds=.32, no_dense_boundary_claim=True))
        print('ACCEPTED', item['uid'], segment.shape, flush=True)
    handle.remove()
    write(ROOT/'events_completion.json', dict(status='COMPLETE_FIRST8_FROZEN_TIMED_PANN',
        rows=rows, actual_forwards=len(rows), train_updates=0, state_tensors=tensors,
        elapsed_seconds=time.monotonic()-start,
        torch_peak_allocated_bytes=torch.cuda.max_memory_allocated(),
        actual_parameters=read(ROOT/'model_cpu_acceptance.json')['actual_parameters']))


if __name__ == '__main__':
    main()
