"""First missing backbone only; exact original K400 route on both development sources."""
import json
import sys

import numpy as np
import torch
import torch.nn.functional as F

from event_route77_common import OUT, GENERAL, ENGINEERING, model_helpers, source_inputs, old_model_registration
from t_io import ROOT, WORK, check, identity, read, save


def first_backbone(backbone, extractor, sid, info, folder):
    if info['existing_feature'] is not None:
        return info['existing_feature'], 0
    source = read(check(info['input']))
    array = np.load(check(source['rgb']), mmap_mode='r', allow_pickle=False)
    if array.dtype != np.uint8 or array.shape != (info['cells'], 8, 224, 224, 3):
        raise ValueError('First exact-best route RGB geometry differs')
    parts = []
    with (folder / 'backbone_journal.jsonl').open('x') as journal:
        for first in range(0, len(array), 8):
            raw = torch.from_numpy(array[first:first + 8].copy()).permute(0, 4, 1, 2, 3)
            actual = raw.cuda()
            if not torch.equal(actual.cpu(), raw):
                raise ValueError('Actual first I3D GPU uint8 pixels differ from accepted CPU')
            with torch.inference_mode():
                values = extractor(backbone, (actual.float() / 255 - .45) / .225).cpu().numpy()
            path = folder / ('batch_%04d.npy' % first)
            with path.open('xb') as stream:
                np.save(stream, values, allow_pickle=False)
            if values.shape != (len(raw), 2048) or not np.isfinite(values).all():
                raise ValueError('First new route backbone output invalid; raw retained')
            parts.append(values)
            journal.write(json.dumps(dict(first=first, actual_cells=len(values), output=identity(path))) + '\n')
            journal.flush()
    path = folder / 'features.npy'
    with path.open('xb') as stream:
        np.save(stream, np.concatenate(parts), allow_pickle=False)
    return identity(path), len(array)


def main():
    runtime, profile, fingerprint, classes = model_helpers()
    sys.path.insert(0, str(WORK / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/temporal_sft8b_v1'))
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation(); torch.set_num_threads(2)
    lock = read(OUT / 'source_input_lock.json')
    for ref in list(lock['code'].values()) + list(lock['dependencies'].values()):
        check(ref)
    old = old_model_registration()
    backbone, expert, _ = runtime.make_models(ENGINEERING)
    profile.load_authorized_backbone(ENGINEERING, backbone)
    expert.load_state_dict(torch.load(check(old['expert_checkpoint']), map_location='cpu', weights_only=True)['model'], strict=True)
    backbone.cuda().eval().requires_grad_(False); expert.cuda().eval().requires_grad_(False)
    total = 8782459120 + 98329 + 37184640 + sum(p.numel() for p in backbone.parameters()) + sum(p.numel() for p in expert.parameters())
    if total != 8853994586 or total > 9000000000:
        raise ValueError('Actual full new-best/ASR parameter budget differs')
    before = fingerprint(backbone), fingerprint(expert)
    mapping = {k.strip('"'): v for k, v in read(check(old['class_names'])).items()}
    target = {mapping[k] for k in classes}; inverse = {v: k for k, v in mapping.items()}
    folder = OUT / 'outputs'; folder.mkdir(); outputs = {}; new_cells = 0
    for sid, info in source_inputs().items():
        dest = folder / sid; dest.mkdir()
        feature, cells = first_backbone(backbone, runtime.extract_rgb_features, sid, info, dest)
        new_cells += cells
        values = np.load(check(feature), allow_pickle=False)
        if values.shape != (info['cells'], 2048):
            raise ValueError('Old/new exact route feature dimensions differ')
        tensor = torch.from_numpy(values).cuda()
        with torch.inference_mode():
            probabilities = F.linear(tensor, backbone.blocks[-1].proj.weight,
                backbone.blocks[-1].proj.bias).softmax(-1).cpu().numpy()
        path = dest / 'K400.npy'
        with path.open('xb') as stream:
            np.save(stream, probabilities, allow_pickle=False)
        category = int(probabilities.mean(0).argmax()); routed = category in target
        scores = None
        if routed:
            with torch.inference_mode():
                x = F.normalize(tensor, dim=-1)[None]
                scores = runtime.score_features(expert, x, torch.ones(x.shape[:2], device=x.device, dtype=torch.bool)).cpu().numpy()[0]
            if scores.shape != (info['cells'],) or not np.isfinite(scores).all():
                raise ValueError('First original expert output shape or values differ')
            with (dest / 'expert.npy').open('xb') as stream:
                np.save(stream, scores, allow_pickle=False)
        save(dest / 'acceptance.json', dict(source=sid, input=info['input'], features=feature,
            probabilities=identity(path), original_global_class=inverse[category], source_routed=routed,
            expert=identity(dest / 'expert.npy') if routed else None,
            new_backbone_cells=cells, old_backbone_adopted=(cells == 0)))
        outputs[sid] = identity(dest / 'acceptance.json')
        print('EVENT77_FIRST_EXACT_ROUTE', sid, cells, routed, flush=True)
    if (fingerprint(backbone), fingerprint(expert)) != before or new_cells != 277:
        raise ValueError('Frozen model values or first-only backbone denominator differs')
    save(OUT / 'GPU_completion.json', dict(state='FIRST_CURRENT40_48_ROUTE_TWO_SOURCES_NEEDS_CPU',
        outputs=outputs, new_I3D_cells=277, original_Nobel294_cells_not_repeated=True,
        new_K400_projections=2, new_expert_calls=sum(read(check(r))['source_routed'] for r in outputs.values()),
        actual_complete_parameters=total, all_frozen_weights_unchanged=True,
        peak_torch_bytes=torch.cuda.max_memory_allocated(), new8B_calls=0, new_training=0))


if __name__ == '__main__':
    main()
