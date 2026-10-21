"""Strict reconstruction of the official frozen X-CLIP checkpoint."""
import sys
import torch
from common import ROOT, BASE_PARAMETERS, checked, read, ref, write


def checkpoint_state():
    weight = read(ROOT / 'download_acceptance.json')['weight']
    obj = torch.load(checked(weight), map_location='cpu', weights_only=True)
    state = obj['model'] if 'model' in obj else obj
    assert isinstance(state, dict) and all(isinstance(k, str) for k in state)
    if all(k.startswith('module.') for k in state):
        state = {k[7:]: v for k, v in state.items()}
    state = dict(state)
    for key in ['input_resolution', 'context_length', 'vocab_size']:
        state.pop(key, None)
    assert all(isinstance(v, torch.Tensor) for v in state.values())
    return state


def layer_count(state, prefix):
    indices = {int(k[len(prefix):].split('.')[0]) for k in state if k.startswith(prefix)}
    assert indices == set(range(len(indices))) and indices
    return len(indices)


def load_model():
    sys.path.insert(0, str(ROOT / 'runtime'))
    from models.xclip import XCLIP
    state = checkpoint_state()
    vision_width = state['visual.conv1.weight'].shape[0]
    patch = state['visual.conv1.weight'].shape[-1]
    grid = round((state['visual.positional_embedding'].shape[0] - 1) ** .5)
    config = dict(embed_dim=state['text_projection'].shape[1], image_resolution=patch * grid,
          vision_layers=layer_count(state, 'visual.transformer.resblocks.'),
          vision_width=vision_width, vision_patch_size=patch,
          context_length=state['positional_embedding'].shape[0],
          vocab_size=state['token_embedding.weight'].shape[0],
          transformer_width=state['ln_final.weight'].shape[0],
          transformer_heads=state['ln_final.weight'].shape[0] // 64,
          transformer_layers=layer_count(state, 'transformer.resblocks.'),
          T=state['mit.positional_embedding'].shape[1], droppath=0.,
          mit_layers=layer_count(state, 'mit.resblocks.'),
          prompts_layers=layer_count(state, 'prompts_generator.decoder.'),
          prompts_alpha=.1, use_cache=False, use_checkpoint=False)
    assert config['T'] == 8 and config['image_resolution'] == 224
    assert config['context_length'] == 77 and config['vocab_size'] == 49408
    torch.manual_seed(7321)
    model = XCLIP(**config).float().eval().requires_grad_(False)
    # No missing, unexpected, random or newly fitted parameters are tolerated.
    model.load_state_dict(state, strict=True)
    assert all(torch.equal(value, model.state_dict()[key]) for key, value in state.items())
    count = sum(p.numel() for p in model.parameters())
    assert count + BASE_PARAMETERS <= 9000000000
    return model, dict(config=config, parameters=count,
                       with_protected_baseline=count + BASE_PARAMETERS,
                       strict_checkpoint_tensor_count=len(state))


def main():
    model, identity = load_model()
    assert not any(p.requires_grad for p in model.parameters())
    write(ROOT / 'model_acceptance.json', dict(status='STRICT_FROZEN_AUTHOR_MODEL_PASS',
          **identity, weight=read(ROOT / 'download_acceptance.json')['weight'],
          real_forward_calls=0, extra_clip_in_prospective_runtime=False))


if __name__ == '__main__':
    main()
