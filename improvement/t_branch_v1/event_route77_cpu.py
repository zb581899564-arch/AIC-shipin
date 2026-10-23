"""First independent K400/expert CPU replay and native keep-mask for actual40.48."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import numpy as np
import torch
import torch.nn.functional as F

from event_route77_common import OUT, ENGINEERING, model_helpers, source_inputs, old_model_registration
from t_io import check, identity, read, save


def main():
    torch.set_num_threads(2)
    runtime, profile, _, classes = model_helpers(); old = old_model_registration()
    backbone, expert, _ = runtime.make_models(ENGINEERING)
    profile.load_authorized_backbone(ENGINEERING, backbone)
    expert.load_state_dict(torch.load(check(old['expert_checkpoint']), map_location='cpu', weights_only=True)['model'], strict=True)
    backbone.eval().requires_grad_(False); expert.eval().requires_grad_(False)
    mapping = {k.strip('"'): v for k, v in read(check(old['class_names'])).items()}
    target = {mapping[k] for k in classes}
    actual = read(OUT / 'GPU_completion.json'); inputs = source_inputs(); masks = {}
    for sid, ref in actual['outputs'].items():
        row = read(check(ref)); accepted = read(check(inputs[sid]['input']))
        values = np.load(check(row['features']), allow_pickle=False)
        probs = np.load(check(row['probabilities']), allow_pickle=False)
        with torch.inference_mode():
            replay = F.linear(torch.from_numpy(values), backbone.blocks[-1].proj.weight,
                backbone.blocks[-1].proj.bias).softmax(-1).numpy()
        if not np.allclose(replay, probs, atol=2e-6, rtol=1e-4):
            raise ValueError('First CPU original-classifier replay differs')
        category = int(probs.mean(0).argmax())
        if int(replay.mean(0).argmax()) != category or (category in target) != row['source_routed']:
            raise ValueError('Exact original source route decision differs across CPU/GPU')
        groups = np.load(check(accepted['groups']), allow_pickle=False)
        if (len(groups) != inputs[sid]['source']['native_frames']
                or not np.array_equal(groups, np.arange(len(groups)) // 64)):
            raise ValueError('Exact original native64 route grouping differs')
        mask = np.ones(len(groups), dtype=bool)
        if row['source_routed']:
            saved = np.load(check(row['expert']), allow_pickle=False)
            with torch.inference_mode():
                x = F.normalize(torch.from_numpy(values), dim=-1)[None]
                score = runtime.score_features(expert, x, torch.ones(x.shape[:2], dtype=torch.bool)).numpy()[0]
            if not np.allclose(score, saved, atol=2e-5, rtol=1e-4) or not np.array_equal(score >= .5, saved >= .5):
                raise ValueError('First CPU exact expert/binary policy replay differs')
            mask = saved[groups] >= .5
        path = OUT / (sid + '_intrinsic_route_keep.npz')
        with path.open('xb') as stream:
            np.savez_compressed(stream, keep=mask)
        masks[sid] = dict(intrinsic_keep=identity(path), source_routed=row['source_routed'],
            global_class=row['original_global_class'], native_frames=len(groups), model_output=ref,
            route_nonactivation_does_not_mean_ordinary_ground_truth=True)
    if len(masks) != 2 or torch.cuda.is_initialized():
        raise ValueError('Exactly two first route CPU source replays must complete without CUDA')
    save(OUT / 'CPU_completion.json', dict(state='PASS_FIRST_EXACT_CURRENT40_48_ROUTE_CPU',
        source_masks=masks, no_threshold_or_class_changed=True,
        original_Nobel_backbone_not_repeated=True, no_human_labels_read=True,
        all_native_masks_only_remove_not_add=True, new_model_or_confirmation_or_candidate_claim=False))


if __name__ == '__main__':
    main()
