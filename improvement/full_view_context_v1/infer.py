"""Save all first image embeddings before QA; reuse existing text outputs."""
import sys
import numpy as np
import torch
from common import ROOT, CLIP, MEAN, STD, checked, read, ref, write, save_array


def main():
    inputs = read(ROOT / 'input_acceptance.json')
    assert inputs['status'] == 'PASS56_SAME_NATIVE_RGB_TWO_VIEWS'
    sys.path.insert(0, str(CLIP / 'vendor'))
    import clip
    model, _ = clip.load(str(checked(inputs['weight'])), device='cuda', jit=False)
    model.eval().requires_grad_(False)
    parameters = sum(p.numel() for p in model.parameters())
    assert parameters == 151277313 and parameters + 8782557449 == 8933834762
    images = np.load(checked(inputs['pixels']), allow_pickle=False)
    assert images.shape == (112, 224, 224, 3) and images.dtype == np.uint8
    mean = torch.tensor(MEAN, device='cuda')[None, :, None, None]
    std = torch.tensor(STD, device='cuda')[None, :, None, None]
    (ROOT / 'outputs').mkdir()
    files = []
    for begin in range(0, len(images), 32):
        pixels = torch.from_numpy(images[begin:begin + 32].copy()).permute(0, 3, 1, 2).cuda().float() / 255
        with torch.inference_mode():
            raw = model.encode_image((pixels - mean) / std).cpu().numpy()
        path = ROOT / 'outputs' / f'images_{begin:03d}.npy'
        save_array(path, raw)
        write(ROOT / 'outputs' / f'batch_{begin:03d}.json', dict(begin=begin, output=ref(path)))
        assert raw.shape == (len(pixels), 512) and np.isfinite(raw).all()
        files.append(ref(path))
    write(ROOT / 'inference_completion.json', dict(status='PASS112_FIRST_CLIP_IMAGE_OUTPUTS', files=files,
          image_forward_batches=len(files), image_embeddings=112, text_forward_batches=0, training_updates=0,
          original_8B_calls=0, peak_allocated_bytes=torch.cuda.max_memory_allocated(),
          parameters=parameters, combined_with_baseline=parameters + 8782557449, target_labels_opened=False))


if __name__ == '__main__':
    main()
