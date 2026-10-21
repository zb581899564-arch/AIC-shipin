"""First I3D input profile on two existing external sources, native PTS bound."""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import time

from provenance import digest, reference, write_new

OLD_ASSETS = Path('/home/inspur/aic_video_work/native_preference_20261019_v1/assets.private.json')


def select_existing_sources():
    assets = json.loads(OLD_ASSETS.read_text())
    reg = assets['source_registration_ref']
    assert digest(reg['path']) == reg['sha256']
    rows = json.loads(Path(reg['path']).read_text())['sources']
    rows = [r for r in rows if r['group'] == 'check']
    rows.sort(key=lambda r: hashlib.sha256(('i3d_raw_profile01:' + r['sid']).encode()).hexdigest())
    assert len(rows) >= 2
    return rows[:2]


def resize_crop(frame):
    # New RGB-I3D-R50 profile: short side 256, center 224, eight samples / 64 native frames.
    w, h = frame.width, frame.height
    scale = 256 / min(w, h)
    image = frame.reformat(width=round(w * scale), height=round(h * scale), format='rgb24').to_ndarray()
    top = (image.shape[0] - 224) // 2
    left = (image.shape[1] - 224) // 2
    return image[top:top + 224, left:left + 224].copy()


def prepare_source(row, out):
    import av
    import numpy as np
    media, clock_ref = row['media'], row['clock_ref']
    assert digest(media['path']) == media['sha256']
    assert digest(clock_ref['path']) == clock_ref['sha256']
    clock = json.loads(Path(clock_ref['path']).read_text())
    assert clock['source_sha256'] == media['sha256']
    pts = [Fraction(t) for t in clock['original_exact_pts']]
    assert len(pts) > 128
    selected = list(range(0, 64, 8)) + list(range(64, 128, 8))
    pictures, exact = [], []
    start = time.monotonic()
    with av.open(media['path']) as container:
        stream = container.streams.video[0]
        # Two decode threads for this small input profile; leave the shared Java job alone.
        stream.codec_context.thread_count = 2
        for i, frame in enumerate(container.decode(stream)):
            if i >= 128:
                break
            actual = Fraction(frame.pts) * frame.time_base
            assert actual == pts[i], (row['sid'], i, str(actual), str(pts[i]))
            if i in selected:
                pictures.append(resize_crop(frame))
                exact.append(str(actual))
    assert len(pictures) == 16
    rgb = np.stack(pictures).reshape(2, 8, 224, 224, 3)
    path = out / f"{row['sid']}_rgb.npz"
    with path.open('xb') as stream:
        np.savez_compressed(stream, rgb=rgb, native_indices=np.asarray(selected).reshape(2, 8))
    with np.load(path, allow_pickle=False) as restored:
        assert np.array_equal(rgb, restored['rgb'])
        assert restored['rgb'].dtype == np.uint8
    return dict(source_id=row['sid'], media=media, clock=clock_ref, rgb=reference(path),
                shape=list(rgb.shape), exact_sample_pts=exact, native_indices=selected,
                cells=[dict(start=str(pts[0]), end=str(pts[64])),
                       dict(start=str(pts[64]), end=str(pts[128]))],
                first_profile_decode_seconds=time.monotonic() - start,
                pretrained_features_available=False, target_labels_read=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True, type=Path)
    args = parser.parse_args()
    output = args.root / 'raw_profile03'
    output.mkdir()
    rows = select_existing_sources()
    write_new(output / 'registration.json', dict(
        role='EXTERNAL_ENGINEERING_ONLY_NOT_HUMAN_HIGHLIGHT_TRAINING',
        sources=[dict(id=r['sid'], media=r['media'], clock=r['clock_ref']) for r in rows],
        bins_per_source=2, native_frames_per_bin=64, samples_per_bin=8,
        short_side=256, center_crop=224, pretrained_normalize_mean=.45,
        pretrained_normalize_std=.225, no_official_data=True,
    ))
    receipts = []
    for row in rows:
        receipt = prepare_source(row, output)
        write_new(output / f"{row['sid']}_acceptance.json", receipt)
        receipts.append(receipt)
    write_new(output / 'completion.json', dict(
        status='FIRST_RAW_RGB_NATIVE_PTS_PASS_NO_MODEL_YET', sources=receipts,
        accepted_clips=4, target_labels_read=False, model_calls=0,
    ))


if __name__ == '__main__':
    main()
