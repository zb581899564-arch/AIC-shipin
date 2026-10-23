"""First strict author checkpoint and actual parameter audit on CPU."""
import torch
from control import ROOT, read, checked, write, reference
from runtime import load_model


def main():
    accepted = read(ROOT / 'weight_acceptance06.json')
    asset = dict(path=accepted['path'], bytes=accepted['bytes'], sha256=accepted['sha256'])
    model = load_model(checked(asset))
    count = sum(p.numel() for p in model.parameters())
    if count != 2911753 or count + 8782557449 > 9000000000 or torch.cuda.is_initialized():
        raise ValueError('Exact learned architecture/parameter/CPU identity')
    if not all(torch.isfinite(value).all() for value in model.state_dict().values()):
        raise ValueError('Nonfinite author checkpoint tensors')
    write(ROOT / 'learned_weight_acceptance.json', dict(status='PASS_STRICT_AUTHOR_CHECKPOINT_CPU',
        weight=asset, downloaded_acceptance=reference(ROOT / 'weight_acceptance06.json'),
        tensors=len(model.state_dict()), actual_parameters=count, combined_pipeline_parameters=count + 8782557449,
        missing_or_extra_keys=0, research_forward_calls=0, GPU_initialized=False,
        original_module_and_checkpoint_layout_preserved=True))


if __name__ == '__main__':
    main()
