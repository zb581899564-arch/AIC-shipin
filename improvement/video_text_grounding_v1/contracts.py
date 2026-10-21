"""A targeted real-Torch check of cached text versus the author forward."""
import sys
import torch
from common import ROOT, write
from infer import output_components


def main():
    sys.path.insert(0, str(ROOT / 'runtime'))
    from models.xclip import XCLIP
    torch.manual_seed(7321)
    # Synthetic reduced-width graph only; no real video or downloaded checkpoint.
    model = XCLIP(embed_dim=64, image_resolution=64, vision_layers=1,
          vision_width=64, vision_patch_size=32, context_length=10, vocab_size=64,
          transformer_width=64, transformer_heads=1, transformer_layers=1,
          T=8, mit_layers=1, prompts_layers=1, use_cache=False).eval()
    pixels = torch.rand(2, 8, 3, 64, 64)
    tokens = torch.randint(1, 63, (3, 10))
    tokens[:, -1] = 63
    with torch.inference_mode():
        original = model(pixels, tokens) / model.logit_scale.exp()
        components = output_components(model, pixels, model.encode_text(tokens))
    assert torch.allclose(original, torch.from_numpy(components['scores']), atol=1e-6)
    assert torch.equal(pixels.flip(1).flip(1), pixels)
    assert all(not m.training for m in model.modules())
    write(ROOT / 'torch_contracts.json', dict(status='PASS_SCOPED_AUTHOR_FORWARD_EQUIVALENCE',
          checks=3, synthetic_only=True, real_video_model_calls=0,
          initialization_only_import_port=True))


if __name__ == '__main__':
    main()
