"""First frozen video forwards, persisted before any output acceptance."""
import time
import numpy as np
import torch
from common import ROOT, checked, read, ref, write
from model_io import load_model


def output_components(model, pixels, raw_text):
    video, patches = model.encode_video(pixels)
    base_text = raw_text.unsqueeze(0).expand(len(pixels), -1, -1)
    text = base_text + model.prompts_generator(base_text, patches.mean(dim=1))
    video = video / video.norm(dim=-1, keepdim=True)
    text = text / text.norm(dim=-1, keepdim=True)
    # Positive, globally fixed logit_scale does not affect per-query AP rankings.
    cosine = torch.einsum('bd,bkd->bk', video, text)
    return dict(video=video.cpu().numpy(), text=text.cpu().numpy(),
                scores=cosine.cpu().numpy())


def forward_source(model, raw_text, source, mean, std):
    folder = ROOT / 'outputs' / source['sid']
    folder.mkdir()
    rgb = np.load(checked(source['rgb']), mmap_mode='r', allow_pickle=False)
    rows = []
    for mode in ['real', 'reverse']:
        for start in range(0, len(rgb), 8):
            batch = np.array(rgb[start:start + 8], copy=True)
            if mode == 'reverse':
                batch = batch[:, ::-1].copy()
            pixels = torch.from_numpy(batch).to('cuda', dtype=torch.float32)
            pixels = pixels.permute(0, 1, 4, 2, 3).div_(255.)
            pixels = (pixels - mean) / std
            outputs = output_components(model, pixels, raw_text)
            path = folder / f'{mode}_{start:04}.npz'
            np.savez(path, **outputs)
            identity = ref(path)
            assert all(np.isfinite(v).all() for v in outputs.values())
            assert outputs['scores'].shape == (len(batch), 26)
            assert np.max(np.abs(outputs['scores'])) <= 1.00001
            row = dict(mode=mode, start=start, cells=len(batch), output=identity)
            rows.append(row)
            with (ROOT / 'journal.jsonl').open('a') as stream:
                import json
                stream.write(json.dumps(dict(sid=source['sid'], **row)) + '\n')
    acceptance = dict(sid=source['sid'], native_cells=len(rgb), outputs=rows)
    write(folder / 'acceptance.json', acceptance)
    return acceptance


def main():
    # The long-running parent already imported its launcher before the network
    # transfer. Recheck in this fresh child, before allocating any model on GPU.
    from resource_context06 import live_reason
    live_reason('encoder')
    assert torch.cuda.is_available()
    inputs = read(ROOT / 'input_acceptance.json')
    model, identity = load_model()
    assert identity == {k: read(ROOT / 'model_acceptance.json')[k] for k in identity}
    model = model.to('cuda').eval()
    mean = torch.tensor([.48145466, .4578275, .40821073], device='cuda').view(1, 1, 3, 1, 1)
    std = torch.tensor([.26862954, .26130258, .27577711], device='cuda').view(1, 1, 3, 1, 1)
    (ROOT / 'outputs').mkdir()
    tokens = torch.from_numpy(np.load(checked(inputs['tokens']), allow_pickle=False)).to('cuda')
    started = time.monotonic()
    with torch.inference_mode():
        raw_text = model.encode_text(tokens)
        path = ROOT / 'outputs/text_raw.npy'
        np.save(path, raw_text.cpu().numpy(), allow_pickle=False)
        assert raw_text.shape == (26, 512) and torch.isfinite(raw_text).all()
        sources = [forward_source(model, raw_text, s, mean, std) for s in inputs['sources']]
    torch.cuda.synchronize()
    assert all(not m.training for m in model.modules())
    write(ROOT / 'inference_completion.json', dict(status='ALL_FIRST_VIDEO_OUTPUTS_PERSISTED',
          sources=sources, text=ref(path), text_forward_batches=1,
          actual_video_forward_batches=sum(len(s['outputs']) for s in sources),
          video_cells_real=512, video_cells_reverse=512, original_image_views=4096,
          reverse_image_views=4096, seconds=time.monotonic() - started,
          peak_allocated_bytes=torch.cuda.max_memory_allocated(),
          targets_opened=False, gradients_or_updates=0, qwen_calls=0))


if __name__ == '__main__':
    main()
