"""Fixed author splits and direct member-range acquisition, never whole archive."""
import hashlib
import io
from pathlib import Path
import struct
import subprocess
import time
import urllib.error
import urllib.request
import zlib
import numpy as np
from PIL import Image
from common import ROOT, WORK, WIDTH, TRAIN200, EXPAND, append, checked, digest, read, ref, write


def fingerprint(image):
    gray = np.asarray(image.convert('L').resize((9, 8)))
    return sum(int(v) << i for i, v in enumerate((gray[:, 1:] > gray[:, :-1]).reshape(-1)))


def acquire(member, destination):
    protocol = read(ROOT / 'protocol.json')
    start, length = member['header_offset'], member['range_bytes'] if 'range_bytes' in member else None
    # Existing eval index has exact filename/header metadata, but may not have range_bytes.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def request(offset, count, name):
        req = urllib.request.Request(protocol['origin_url'], headers={
            'Range': f'bytes={offset}-{offset + count - 1}', 'Accept-Encoding': 'identity',
            'User-Agent': 'AIC-S1-noncommercial-research'})
        time.sleep(1.25)
        with opener.open(req, timeout=60) as response:
            peer = response.fp.raw._sock.getpeername()
            route = subprocess.check_output(['ip', 'route', 'get', peer[0]], text=True).strip()
            if 'dev eno2' not in route or peer[0].startswith(('127.', '198.18.', '100.')):
                raise ValueError('Public direct source route not verified')
            if response.status != 206 or response.headers.get('Content-Range') != f'bytes {offset}-{offset + count - 1}/{protocol["archive_bytes"]}':
                raise ValueError('No full archive fallback allowed')
            raw = response.read(count + 1)
        if len(raw) != count:
            raise ValueError('Truncated exact range')
        path = destination.with_suffix('.' + name)
        with path.open('xb') as stream:
            stream.write(raw)
        append(ROOT / 'range_receipts.jsonl', dict(offset=offset, bytes=count, peer=peer, route=route,
            empty_proxy=True, output=ref(path)))
        return raw
    header = request(start, 30, 'header')
    values = struct.unpack('<4s5H3I2H', header)
    if values[0] != b'PK\x03\x04' or values[3] != member['compression']:
        raise ValueError('Original ZIP header mismatch')
    offset = start + 30 + values[-2] + values[-1]
    packed = request(offset, member['compressed_bytes'], 'packed')
    raw = zlib.decompress(packed, -15) if member['compression'] == 8 else packed
    if len(raw) != member['bytes'] or zlib.crc32(raw) & 0xffffffff != member['crc32']:
        raise ValueError('Original author JPEG CRC/size mismatch')
    with destination.open('xb') as stream:
        stream.write(raw)
    return raw


def load_rgb(path):
    with Image.open(path) as image:
        if image.getexif().get(274, 1) != 1:
            raise ValueError('Unregistered EXIF transformation')
        return image.convert('RGB').copy()


def save_rgb(image, key):
    path = ROOT / 'rgb' / f'{key}.npy'
    with path.open('xb') as stream:
        np.save(stream, np.asarray(image), allow_pickle=False)
    return ref(path)


def training_rows():
    rows = [__import__('json').loads(s) for s in (EXPAND / 'accepted_train.jsonl').read_text().splitlines() if s.strip()]
    if len(rows) != 602 or len({r['source_sha256'] for r in rows}) != 602:
        raise ValueError('Historical602 identity mismatch')
    output = []
    for row in rows:
        path = Path(row['source'])
        if digest(path) != row['source_sha256']:
            raise ValueError('Historical author JPEG changed')
        image = load_rgb(path)
        rgb_sha = hashlib.sha256(np.asarray(image).tobytes()).hexdigest()
        if rgb_sha != row['RGB_sha256']:
            raise ValueError('Retired RGB reconstruction differs from accepted original')
        restored = save_rgb(image, 'train_' + path.name)
        item = dict(item_id=row['item_id'], role='train', media=ref(path), rgb=restored, width=image.width,
            height=image.height, RGB_sha256=rgb_sha, dhash=fingerprint(image),
            original_normalized_xyxy=row['reference_original_xyxy'], historical_human_width=row['target']['width'],
            retired_RGB_tensor_recovery_explicit=True, original_source_group='UNKNOWN_BEYOND_PUBLISHER_FILE')
        output.append(item)
        append(ROOT / 'recovered_train.jsonl', item)
    return output


def main():
    protocol = read(ROOT / 'protocol.json')
    (ROOT / 'rgb').mkdir()
    output = training_rows()
    write(ROOT / 'train_recovery_acceptance.json', dict(status='PASS602_RETIRED_RGB_RECOVERED_FROM_ORIGINAL_JPEG',
        rows=output, no_old_success_claim_rewritten=True, first_new_conditioned_pixels_not_yet_run=True))
    old_eval = read(WIDTH / 'inputs.json')
    protected = read(WIDTH / 'control/protected.json')
    denied_names = set(protected['filenames']) | {r['item_id'].split(':')[-1] for r in old_eval}
    denied_hashes = set(protected['media_sha256']) | {r['media']['sha256'] for r in output} | {r['source_sha256'] for r in old_eval}
    fingerprints = [r['dhash'] for r in output]
    for row in old_eval:
        array = np.load(WIDTH / 'rgb' / (row['key'] + '.npy'), allow_pickle=False)
        fingerprints.append(fingerprint(Image.fromarray(array)))
    index = read(WIDTH / 'control/zip_index.json')
    pools = {}
    for split, role in [('validation', 'dev'), ('test', 'confirm')]:
        pool = [r for r in read(WIDTH / 'control' / f'{split}.json') if r['filename'] not in denied_names and '16:9' in r['crop_bboxes']]
        pool.sort(key=lambda r: hashlib.sha256(f'S1_20261021:{split}:{r["filename"]}'.encode()).hexdigest())
        pools[role] = [(split, row) for row in pool[:protocol['maximum_pool_per_role']]]
    payload = sum(index[f'GNMC/{split}/{row["filename"]}']['compressed_bytes'] + 30 for pool in pools.values() for split, row in pool)
    write(ROOT / 'media_plan.json', dict(pools={k: [dict(split=s, filename=r['filename']) for s, r in v] for k, v in pools.items()},
        maximum_source_payload_bytes=payload, labels_used_for_selection=False, old_20_not_used_for_model_selection=True))
    (ROOT / 'media').mkdir()
    for role, pool in pools.items():
        accepted = 0
        for split, record in pool:
            if accepted == protocol['evaluation_per_role']:
                break
            name = record['filename']
            if Path(name).name != name:
                raise ValueError('Invalid author member path')
            target = ROOT / 'media' / f'{split}_{name}'
            acquire(index[f'GNMC/{split}/{name}'], target)
            image = load_rgb(target)
            raw_sha, fp = digest(target), fingerprint(image)
            if raw_sha in denied_hashes or any((fp ^ p).bit_count() <= 6 for p in fingerprints):
                append(ROOT / 'cohort_skipped.jsonl', dict(split=split, filename=name, reason='FIXED_IDENTITY_OR_NEAR_DUPLICATE', media=ref(target)))
                continue
            original = record['crop_bboxes']['16:9']
            width, height = image.size
            if abs((original[2] - original[0]) * width * 9 / 16 - (original[3] - original[1]) * height) > 2:
                raise ValueError('Native16 annotation pixel tolerance')
            row = dict(item_id=f'gnmc:{split}:{name}', role=role, media=ref(target), rgb=save_rgb(image, f'{split}_{name}'), width=width, height=height,
                RGB_sha256=hashlib.sha256(np.asarray(image).tobytes()).hexdigest(), dhash=fp,
                original_normalized_xyxy=original, original_source_group='UNKNOWN_BEYOND_PUBLISHER_FILE')
            output.append(row)
            append(ROOT / 'accepted_eval.jsonl', row)
            denied_hashes.add(raw_sha)
            fingerprints.append(fp)
            accepted += 1
            if accepted % 10 == 0:
                print(role, accepted, flush=True)
        if accepted != protocol['evaluation_per_role']:
            raise ValueError('Fixed eval identity pool exhausted; do not lower denominator')
    write(ROOT / 'cohort.json', dict(rows=output, train=602, dev=80, confirm=80, labels_not_encoder_inputs=True,
        original_source_independence='UNKNOWN', original_author_splits=True, old_confirm20_not_reused=True,
        license=ref(WIDTH / 'control/LICENSE.txt'), purpose=ref(WIDTH / 'purpose_reply.json')))


if __name__ == '__main__':
    main()
