"""Exactly four first pretrained feature calls; no fitting or production."""
import argparse
import json
from pathlib import Path
import time

from provenance import digest, reference, write_new
from runtime import extract_rgb_features, make_models, score_features

WEIGHT_BYTES = 224_733_497
WEIGHT_URL = 'https://dl.fbaipublicfiles.com/pytorchvideo/model_zoo/kinetics/I3D_8x8_R50.pyth'


def load_authorized_backbone(root, backbone):
    import torch
    authorization = json.loads((root / 'weight_authorization.json').read_text())
    assert authorization['authorized_model'] == dict(url=WEIGHT_URL, bytes=WEIGHT_BYTES)
    assert authorization['human_answer'].strip()
    receipt = json.loads((root / 'weight_acceptance.json').read_text())
    path = Path(receipt['path'])
    assert path.stat().st_size == WEIGHT_BYTES and digest(path) == receipt['sha256']
    state = torch.load(path, map_location='cpu', weights_only=True)
    backbone.load_state_dict(state['model_state'], strict=True)
    backbone.eval().requires_grad_(False)
    return receipt


def profile_source(root, source, backbone, temporal, output):
    import numpy as np
    import torch
    path = Path(source['rgb']['path'])
    assert digest(path) == source['rgb']['sha256']
    with np.load(path, allow_pickle=False) as archive:
        rgb = archive['rgb'].copy()
    clips = torch.from_numpy(rgb).permute(0, 4, 1, 2, 3).float().div_(255)
    clips.sub_(.45).div_(.225)
    features, durations = [], []
    for index, clip in enumerate(clips):
        torch.cuda.synchronize()
        start = time.monotonic()
        with torch.inference_mode():
            feat = extract_rgb_features(backbone, clip[None].cuda())
        torch.cuda.synchronize()
        elapsed = time.monotonic() - start
        saved = feat.cpu().numpy()
        # Save every first successful call before any independent checks.
        primary = output / f"{source['source_id']}_{index}_primary.npy"
        with primary.open('xb') as stream:
            np.save(stream, saved, allow_pickle=False)
        write_new(output / f"{source['source_id']}_{index}_primary.json", dict(
            feature=reference(primary), seconds=elapsed, native_cell=source['cells'][index],
            loaded_pretrained=True, generated_on_official_data=False,
        ))
        assert saved.shape == (1, 2048) and np.isfinite(saved).all()
        assert np.array_equal(saved, np.load(primary, allow_pickle=False))
        features.append(feat)
        durations.append(elapsed)
    tokens = torch.stack(features, dim=1)
    with torch.inference_mode():
        scores = score_features(temporal, tokens, torch.ones((1, 2), dtype=torch.bool, device='cuda'))
    assert scores.shape == (1, 2) and torch.isfinite(scores).all()
    result = dict(source_id=source['source_id'], first_i3d_forwards=2,
                  seconds_per_clip=durations, feature_shape=list(tokens.shape),
                  untrained_umt_scores=scores.tolist(), umt_is_untrained=True,
                  quality_claim=False, native_cells=source['cells'])
    write_new(output / f"{source['source_id']}_completion.json", result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    import torch
    root = args.root
    assert torch.cuda.is_available() and torch.cuda.device_count() > 0
    assert (root / 'cpu04_completion.json').exists()
    prepared = json.loads((root / 'raw_profile03/completion.json').read_text())
    output = root / 'pretrained_profile04'
    output.mkdir()
    write_new(output / 'claim.json', dict(scope='FOUR_I3D_FEATURES_TWO_UNTRAINED_UMT_CALLS_ONLY'))
    started = time.monotonic()
    torch.manual_seed(69)
    backbone, temporal, _ = make_models(root)
    weight = load_authorized_backbone(root, backbone)
    backbone.cuda()
    temporal.eval().requires_grad_(False).cuda()
    torch.cuda.reset_peak_memory_stats()
    results = [profile_source(root, row, backbone, temporal, output) for row in prepared['sources']]
    write_new(output / 'completion.json', dict(
        status='RAW_PRETRAINED_I3D_UMT_PTS_ENGINEERING_LOOP_PASS_NOT_QUALITY',
        sources=results, weight=weight, seconds=time.monotonic() - started,
        peak_cuda_allocated_bytes=torch.cuda.max_memory_allocated(),
        peak_cuda_reserved_bytes=torch.cuda.max_memory_reserved(),
        actual_i3d_feature_forwards=4, actual_untrained_umt_forwards=2,
        training_updates=0, native_8b_calls=0, production_allowed=False,
    ))


if __name__ == '__main__':
    main()
