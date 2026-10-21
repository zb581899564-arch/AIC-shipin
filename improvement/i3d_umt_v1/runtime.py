"""Use upstream model definitions; inference masks depend only on real inputs."""
from pathlib import Path
import sys


def activate(root):
    root = Path(root)
    for p in [root / "dependencies", root / "sources/pytorchvideo", root / "sources/UMT"]:
        sys.path.insert(0, str(p))


def make_models(root):
    activate(root)
    from pytorchvideo.models.hub.resnet import i3d_r50
    import models  # UMT registry registration, in a fresh pilot process only.
    from nncore.nn import build_model

    # RGB I3D-R50 is a declared new feature profile, not the original UMT cached I3D.
    backbone = i3d_r50(pretrained=False)
    config = dict(
        type="UMT",
        video_enc=dict(type="UniModalEncoder", dims=[2048, 256],
                       pos_cfg=dict(type="PositionalEncoding"),
                       enc_cfg=dict(type="TransformerEncoderLayer"), norm_cfg=dict(type="LN")),
        query_gen=dict(type="QueryGenerator", p=0),
        query_dec=dict(type="QueryDecoder", dims=256,
                       pos_cfg=dict(type="PositionalEncoding"),
                       dec_cfg=dict(type="TransformerDecoderLayer"), norm_cfg=dict(type="LN")),
        pred_head=dict(type="SaliencyHead", dims=[256, 1]),
    )
    temporal = build_model(config)
    return backbone, temporal, config


def score_features(temporal, features, valid):
    import torch
    if features.ndim != 3 or valid.shape != features.shape[:2]:
        raise ValueError("Feature/mask dimensions disagree")
    if not torch.isfinite(features[valid]).all() or not valid.any(dim=1).all():
        raise ValueError("Nonfinite or empty input")
    # Upstream calls this field 'saliency'. Here it is exclusively a padding mask.
    mask_only = torch.where(valid, features.new_zeros(()), features.new_full((), -1))
    inputs = dict(video=features, audio=None, saliency=mask_only)
    return temporal(inputs, mode="test")["_out"]["saliency"]


def extract_rgb_features(backbone, clips):
    """Keep the loaded 400-class head for checkpoint identity; bypass it for features."""
    x = clips
    for block in backbone.blocks[:-1]:
        x = block(x)
    return x.mean(dim=(2, 3, 4))
