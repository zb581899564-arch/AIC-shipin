"""Adopt qualified public media; prepare only the new I3D full-source RGB profile."""
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import shutil
import time

from common import ENGINEERING, ROOT, WORK, checked, clock, native_cells, read, reference, write_new
from prepare_raw import resize_crop


def register():
    assets_path = WORK / 'native_preference_20261019_v1/assets.private.json'
    assets = read(assets_path)
    previous = read(checked(assets['source_registration_ref']))
    compact = {s['id']: s for scope in assets['scopes'].values() for s in scope['sources']}
    sources = []
    for original in previous['sources']:
        s = {k: original[k] for k in ('sid', 'name', 'media', 'clock_ref')}
        old = compact[s['sid']]
        s['comparison_ref'] = old['supervision_ref']
        s['comparison_clock_ref'] = old['supervision_clock_ref']
        if s['sid'].startswith('S'):
            s['labels_ref'] = original['labels_ref']
            s['role'] = 'train'
        else:
            s['role'] = 'held_dataset'
        s['historical_exposure'] = True
        sources.append(s)
    summe = sorted([s for s in sources if s['role'] == 'train'], key=lambda s:
                   hashlib.sha256(('I3D_UMT_SUMME_DEV12:' + s['name']).encode()).hexdigest())
    assert len(summe) == 25 and len(sources) == 33
    for s in summe[:5]:
        s['role'] = 'dev'
    for s in sources:
        checked(s['media'])
        clock(s)
    identities = [s['media']['sha256'] for s in sources]
    assert len(set(identities)) == 33
    checked(assets['protected_baseline_ref'])
    expected = sum(((len(clock(s)[1])+63)//64)*8*224*224*3 for s in sources)
    free = shutil.disk_usage(ROOT).free
    # Derived from actual new arrays/model outputs, not a fixed resource threshold.
    assert free > expected + 120_000_000, (free, expected)
    write_new(ROOT / 'registration.json', dict(sources=sources,
              old_source_identity=assets['source_registration_ref'],
              protected_baseline=assets['protected_baseline_ref'],
              rights=assets['rights_basis_refs'], protocol=reference(ROOT / 'protocol.json'),
              historical_exposure=True, independent_unseen_claim=False,
              required_rgb_bytes=expected, observed_free_bytes=free,
              new_media_downloads=0, no_official_training_data=True))
    return sources


def adopted_rgb():
    completion = read(ENGINEERING / 'raw_profile03/completion.json')
    return {r['source_id']: r for r in completion['sources']}


def prepare_source(s, adopted):
    import av
    import numpy as np
    target = ROOT / 'inputs' / s['sid']
    target.mkdir()
    c, pts, end = clock(s)
    bounds, samples, groups = native_cells(len(pts))
    np.save(target / 'groups.npy', groups, allow_pickle=False)
    rgb = np.lib.format.open_memmap(target / 'rgb.npy', mode='w+', dtype=np.uint8,
                                   shape=(len(bounds), 8, 224, 224, 3))
    inherited = 0
    if s['sid'] in adopted:
        old = adopted[s['sid']]
        assert old['media']['sha256'] == s['media']['sha256']
        with np.load(checked(old['rgb']), allow_pickle=False) as ar:
            assert np.array_equal(samples[:2], ar['native_indices'])
            rgb[:2] = ar['rgb']
        inherited = 2
    wanted = {}
    for cell in range(inherited, len(bounds)):
        for slot, ordinal in enumerate(samples[cell]):
            wanted.setdefault(int(ordinal), []).append((cell, slot))
    seen = set()
    started = time.monotonic()
    with av.open(s['media']['path']) as container:
        stream = container.streams.video[0]
        stream.codec_context.thread_count = 2
        count = 0
        for ordinal, frame in enumerate(container.decode(stream)):
            if ordinal >= len(pts) or Fraction(frame.pts)*frame.time_base != pts[ordinal]:
                raise ValueError(f'Native clock mismatch: {s["sid"]} / {ordinal}')
            if ordinal in wanted:
                image = resize_crop(frame)
                for cell, slot in wanted[ordinal]:
                    rgb[cell, slot] = image
                seen.add(ordinal)
            count += 1
    assert count == len(pts) and seen == set(wanted)
    rgb.flush()
    del rgb
    restored = np.load(target / 'rgb.npy', mmap_mode='r', allow_pickle=False)
    assert restored.dtype == np.uint8 and restored.shape == (len(bounds), 8, 224, 224, 3)
    # Only training/development labels are opened here. Held-dataset labels stay out.
    if s['role'] != 'held_dataset':
        y = np.load(checked(s['labels_ref']), allow_pickle=False) > 0
        assert y.ndim == 2 and len(y) == len(pts)
        means = np.array([y[a:b].mean() for a, b in bounds], dtype=np.float32)
        np.save(target / 'target.npy', means, allow_pickle=False)
    result = dict(sid=s['sid'], role=s['role'], cells=len(bounds), native_frames=count,
                  rgb=reference(target / 'rgb.npy'), groups=reference(target / 'groups.npy'),
                  exact_cell_pts=[[str(pts[a]), str(pts[b] if b < len(pts) else end)] for a,b in bounds],
                  inherited_successful_rgb_cells=inherited, new_rgb_cells=len(bounds)-inherited,
                  native_frame_and_rater_padding=False, seconds=time.monotonic()-started)
    write_new(target / 'acceptance.json', result)
    with (ROOT / 'prepare_journal.jsonl').open('a') as out:
        out.write(json.dumps({k:result[k] for k in ['sid','cells','native_frames','seconds']})+'\n')
    return result


def main():
    (ROOT / 'inputs').mkdir()
    sources = register()
    adopted = adopted_rgb()
    rows = [prepare_source(s, adopted) for s in sources]
    write_new(ROOT / 'input_acceptance.json', dict(status='PASS33_NATIVE_RGB_INPUTS', sources=rows,
              cells=sum(r['cells'] for r in rows), old_rgb_adopted=4,
              new_model_calls=0, held_labels_opened=False))


if __name__ == '__main__':
    main()
