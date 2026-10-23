"""Load the exact author network with explicit inference-only compatibility."""
import ast
from functools import partial
from pathlib import Path
import sys
import torch
from legacy_align import LegacyAlign

ROOT = Path('/home/inspur/aic_video_work/sprint_spatial_s0_20261021_v1')


def build_model():
    upstream = ROOT / 'upstream'
    sys.path.insert(0, str(upstream))
    model_source = ROOT / 'author_runtime07/croppingModel.py'
    tree = ast.parse(model_source.read_text())
    excluded = {'roi_align.modules.roi_align', 'rod_align.modules.rod_align', 'thop', 'ShuffleNetV2'}
    tree.body = [node for node in tree.body if not (isinstance(node, ast.ImportFrom) and node.module in excluded)]
    namespace = dict(__name__='s0_exact_author_model_with_forward_compat',
        RoIAlign=partial(LegacyAlign, mode='roi'), RoDAlign=partial(LegacyAlign, mode='rod'),
        RoIAlignAvg=partial(LegacyAlign, mode='roi', average=True),
        RoDAlignAvg=partial(LegacyAlign, mode='rod', average=True))
    exec(compile(tree, str(model_source), 'exec'), namespace)
    model = namespace['build_crop_model'](scale='multi', alignsize=9, reddim=8,
        loadweight=False, model='mobilenetv2', downsample=4)
    model.eval().requires_grad_(False)
    return model


def load_model(path):
    model = build_model()
    checkpoint = torch.load(path, map_location='cpu', weights_only=True)
    if not isinstance(checkpoint, dict):
        raise ValueError('Expected author tensor state dictionary')
    incompatible = model.load_state_dict(checkpoint, strict=True)
    if incompatible.missing_keys or incompatible.unexpected_keys:
        raise ValueError('Author network/weights mismatch')
    return model
