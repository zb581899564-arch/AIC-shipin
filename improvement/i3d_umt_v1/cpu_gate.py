"""Actual model inventory and focused tensor contracts; no pretrained inference."""
import argparse
import copy
from pathlib import Path
import time

from provenance import write_new
from runtime import make_models, score_features

PROTECTED_PARAMETERS = 8_782_557_449


def check_temporal(temporal):
    import torch
    torch.manual_seed(69)
    temporal.eval()
    features = torch.randn(1, 6, 2048)
    valid = torch.tensor([[True, True, True, True, False, False]])
    with torch.inference_mode():
        first = score_features(temporal, features, valid)
        second = score_features(temporal, features.clone(), valid.clone())
    assert first.shape == valid.shape and torch.equal(first, second)
    assert (first[~valid] == 0).all() and torch.isfinite(first).all()
    clone = copy.deepcopy(temporal)
    clone.load_state_dict(temporal.state_dict(), strict=True)
    with torch.inference_mode():
        assert torch.equal(first, score_features(clone, features, valid))
    temporal.train()
    labels = torch.tensor([[0., 1., .5, 0., -1., -1.]])
    output = temporal(dict(video=features, audio=None, saliency=labels), mode="train")
    losses = [v for k, v in output.items() if k.endswith("loss")]
    assert losses and all(torch.isfinite(v).all() for v in losses)
    sum(losses).backward()
    assert any(p.grad is not None and p.grad.abs().sum() > 0 for p in temporal.parameters())
    return ["INFERENCE_NO_LABEL_INPUT", "PADDING_MASK", "DETERMINISTIC_RELOAD", "FINITE_TRAINING_GRADIENT"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--attempt", default="cpu_gate")
    args = parser.parse_args()
    if not args.attempt.replace("_", "").isalnum():
        raise ValueError("Invalid attempt name")
    import torch
    torch.set_num_threads(2)
    started = time.monotonic()
    write_new(args.root / f"{args.attempt}_claim.json", dict(stage="CPU_RANDOM_INITIALIZATION_ONLY"))
    backbone, temporal, config = make_models(args.root)
    backbone_n = sum(p.numel() for p in backbone.parameters())
    temporal_n = sum(p.numel() for p in temporal.parameters())
    actual = PROTECTED_PARAMETERS + backbone_n + temporal_n
    assert actual <= 9_000_000_000
    checks = check_temporal(temporal)
    write_new(args.root / f"{args.attempt}_completion.json", dict(
        status="CPU_CONTRACTS_PASS_NOT_PRETRAINED_QUALITY", checks=checks,
        protected_parameters=PROTECTED_PARAMETERS, rgb_i3d_r50_parameters=backbone_n,
        umt_visual_only_parameters=temporal_n, pipeline_parameters=actual,
        remaining_parameters=9_000_000_000 - actual, configuration=config,
        seconds=time.monotonic() - started, pretrained_weights_downloaded=False,
        new_8b_calls=0, new_real_video_model_calls=0, optimizer_updates=0,
    ))


if __name__ == "__main__":
    main()
