"""One first pretrained pass per new cell; old four features are referenced."""
import time
import numpy as np
import torch

from common import ENGINEERING, ROOT, checked, read, reference, write_new
from profile_gpu import load_authorized_backbone
from runtime import extract_rgb_features, make_models


def source_features(row, backbone):
    sid = row['sid']
    target = ROOT / 'features' / sid
    target.mkdir()
    rgb = np.load(checked(row['rgb']), mmap_mode='r', allow_pickle=False)
    previous = read(ENGINEERING / 'pretrained_profile04/completion.json')
    old_ids = {r['source_id'] for r in previous['sources']}
    parts, inherited, calls = [], 0, 0
    if sid in old_ids:
        for index in range(2):
            meta = read(ENGINEERING / f'pretrained_profile04/{sid}_{index}_primary.json')
            parts.append(np.load(checked(meta['feature']), allow_pickle=False))
        inherited = 2
    for begin in range(inherited, len(rgb), 8):
        clips = torch.from_numpy(rgb[begin:begin+8].copy()).permute(0,4,1,2,3).cuda().float()/255
        clips = (clips-.45)/.225
        with torch.inference_mode():
            values = extract_rgb_features(backbone, clips).cpu().numpy()
        primary = target / f'batch_{begin:04d}.npy'
        with primary.open('xb') as out:
            np.save(out, values, allow_pickle=False)
        assert values.shape == (len(clips),2048) and np.isfinite(values).all()
        parts.append(values)
        calls += len(clips)
    merged = np.concatenate(parts)
    assert merged.shape == (len(rgb),2048)
    with (target / 'all.npy').open('xb') as out:
        np.save(out, merged, allow_pickle=False)
    result = dict(sid=sid, features=reference(target / 'all.npy'), cells=len(rgb),
                  inherited_i3d_cells=inherited, new_i3d_cells=calls)
    write_new(target / 'acceptance.json', result)
    with (ROOT / 'feature_journal.jsonl').open('a') as out:
        import json
        out.write(json.dumps(dict(sid=sid,cells=len(rgb),new_i3d_cells=calls))+'\n')
    return result


def main():
    assert torch.cuda.is_available()
    inputs = read(ROOT / 'input_acceptance.json')
    (ROOT / 'features').mkdir()
    backbone, unused_temporal, _ = make_models(ENGINEERING)
    del unused_temporal
    load_authorized_backbone(ENGINEERING, backbone)
    backbone.cuda().eval().requires_grad_(False)
    started = time.monotonic()
    rows = [source_features(row, backbone) for row in inputs['sources']]
    write_new(ROOT / 'feature_acceptance.json', dict(status='PASS_PRETRAINED_ALL_NATIVE_CELLS',
              sources=rows, new_i3d_cells=sum(r['new_i3d_cells'] for r in rows),
              inherited_i3d_cells=4, seconds=time.monotonic()-started,
              peak_allocated_bytes=torch.cuda.max_memory_allocated()))


if __name__ == '__main__':
    main()
