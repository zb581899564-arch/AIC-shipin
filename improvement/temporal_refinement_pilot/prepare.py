"""New six-source visual-only development diagnostic; never a training launcher."""
import hashlib
import json
import sys
from bisect import bisect_left
from fractions import Fraction
from pathlib import Path

ROOT = Path('/home/inspur/aic_video_work')
HERE = ROOT / 'temporal_refinement_pilot_20261011/dev_01'
IDS = ['qvh_8056', 'qvh_6992', 'qvh_10050', 'qvh_8737', 'qvh_5488', 'qvh_8154']


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)


def main():
    import av
    import numpy as np
    from PIL import Image, ImageDraw
    HERE.mkdir(parents=True, exist_ok=False)
    data = ROOT / 'data_qvh_confirmed_20260910/dev.jsonl'
    rows = {r['video_id']: r for r in map(json.loads, data.read_text().splitlines())}
    selection = [rows[i] for i in IDS]
    if len({r['source_group'] for r in selection}) != 6:
        raise ValueError('six independent original-source groups required')
    train_groups = {r['source_group'] for r in map(json.loads, (data.parent/'train.jsonl').read_text().splitlines())}
    if train_groups.intersection(r['source_group'] for r in selection):
        raise ValueError('development source intersects this approved training split')
    save(HERE/'selection_audit.json', dict(rows=selection, selection_basis='six physical-action dev sources chosen before model output',
        qvh_labels_used_only_to_find_sources=True, qvh_relevance_not_generic_highlight_truth=True,
        previously_evaluated_development_split=True, fresh_holdout=False,
        source_attestation_sha256=sha(data.parent/'source_attestation.json'),
        development_sha256=sha(data), training_sha256=sha(data.parent/'train.jsonl')))
    inputs = []
    for case, r in enumerate(selection, 1):
        key = f'T{case:02d}'
        folder = HERE/key
        folder.mkdir()
        path = Path(r['video_path'])
        if sha(path) != r['video_sha256']:
            raise ValueError('source identity changed')
        points = []
        with av.open(str(path)) as c:
            if len(c.streams.video) != 1:
                raise ValueError('ambiguous source stream')
            st = c.streams.video[0]
            rate = st.average_rate
            if rate is None or rate <= 0:
                raise ValueError('missing actual rate')
            width, height = st.width, st.height
            for f in c.decode(st):
                if f.pts is None or f.time_base is None:
                    raise ValueError('missing native PTS')
                points.append(str(Fraction(f.pts)*f.time_base))
        exact = [Fraction(x) for x in points]
        if not exact or any(a >= b for a, b in zip(exact, exact[1:])):
            raise ValueError('native clock is not strictly increasing')
        # QVH timestamps are only a deterministic source-selection anchor.
        a, b = r['relevant_windows'][0]
        start = max(0, min((a+b)/2-15, r['duration_sec']-30))
        lo, hi = Fraction(str(start)), Fraction(str(start))+30
        first, stop = bisect_left(exact, lo), bisect_left(exact, hi)
        n = stop-first
        if n < 64:
            raise ValueError('short source cannot meet fixed64 diagnostic')
        ordinals = [first+i*(n-1)//63 for i in range(64)]
        wanted = set(ordinals)
        images = []
        pixels = []
        with av.open(str(path)) as c:
            for ordinal, f in enumerate(c.decode(c.streams.video[0])):
                if ordinal in wanted:
                    if str(Fraction(f.pts)*f.time_base) != points[ordinal]:
                        raise ValueError('second decode clock differs')
                    arr = f.to_ndarray(format='rgb24')
                    if arr.shape != (height, width, 3):
                        raise ValueError('RGB geometry changed')
                    images.append(arr)
                    pixels.append(hashlib.sha256(arr.tobytes()).hexdigest())
                if ordinal >= ordinals[-1]:
                    break
        if len(images) != 64:
            raise ValueError('missing selected native frame')
        np.savez_compressed(folder/'frames.npz', rgb=np.stack(images))
        # Every delivered observation is visible; thumbnails preserve full frame.
        tile_w, tile_h = 300, 194
        sheet = Image.new('RGB', (tile_w*8, tile_h*8), '#101010')
        draw = ImageDraw.Draw(sheet)
        for i, arr in enumerate(images):
            im = Image.fromarray(arr)
            im.thumbnail((296, 168), Image.Resampling.LANCZOS)
            x, y = (i%8)*tile_w, (i//8)*tile_h
            sheet.paste(im, (x+(tile_w-im.width)//2, y+24+(168-im.height)//2))
            draw.text((x+4, y+4), f'{key} ID {i:02d}  PTS {float(exact[ordinals[i]]):.3f}', fill='white')
        sheet.save(folder/'contact.jpg', quality=90)
        meta = dict(case_id=key, source_path=str(path), source_sha256=r['video_sha256'],
            source_group=r['source_group'], source_total_frames=len(points), width=width, height=height,
            fps_num=rate.numerator, fps_den=rate.denominator, window_start=str(lo), window_end=str(hi),
            eligible_first=first, eligible_stop=stop, all_source_exact_pts=points,
            source_frame_ordinals=ordinals, sample_exact_pts=[points[i] for i in ordinals], pixel_sha256=pixels,
            frame_array_path=str(folder/'frames.npz'), frame_array_sha256=sha(folder/'frames.npz'),
            contact_sha256=sha(folder/'contact.jpg'), source_bytes=path.stat().st_size,
            audio_observed=False, reference_available_to_inference=False)
        save(folder/'input.json', meta)
        inputs.append(dict(case_id=key, input_path=str(folder/'input.json'), input_sha256=sha(folder/'input.json')))
        print(json.dumps(dict(case_id=key, frames=64, contact_bytes=(folder/'contact.jpg').stat().st_size)), flush=True)
    save(HERE/'inputs.json', inputs)
    save(HERE/'preparation.json', dict(status='PASS_SIX_SOURCE_NATIVE64_PREPARATION_NOT_REFERENCE_QUALITY',
        sources=6, frames=384, source_groups=6, split='EXPOSED_DEVELOPMENT_NOT_BLIND_HOLDOUT',
        new_model_calls=0, new_optimizer_updates=0, qvh_gt_not_used_as_generic_highlight_reference=True,
        prepared_bytes=sum(p.stat().st_size for p in HERE.rglob('*') if p.is_file()),
        contacts=[dict(case_id=i['case_id'], bytes=(HERE/i['case_id']/'contact.jpg').stat().st_size,
            sha256=sha(HERE/i['case_id']/'contact.jpg')) for i in inputs]))


if __name__ == '__main__':
    main()
