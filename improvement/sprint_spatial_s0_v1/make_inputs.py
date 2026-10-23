"""First scorer-specific inputs from accepted RGB; no JPEG or Qwen work."""
import hashlib
import json
import numpy as np
import torch
from control import ROOT, S1, read, checked, write, append, reference, geometry, signature
from preprocess import encode_image, encode_rois, verify_author_preprocessing


def main():
    contract = verify_author_preprocessing()
    protocol = read(ROOT / 'protocol.json')
    rows = [r for r in read(S1 / 'cohort.json')['rows'] if r['role'] == 'dev']
    centers = {r['item_id']: r for r in map(json.loads, checked(read(S1 / 'center_completion.json')['predictions']).read_text().splitlines())}
    geo = geometry()
    destination = ROOT / 'inputs'
    destination.mkdir()
    accepted, references = [], []
    for row in rows:
        rgb = np.load(checked(row['rgb']), allow_pickle=False)
        if list(rgb.shape) != [row['height'], row['width'], 3] or hashlib.sha256(rgb.tobytes()).hexdigest() != row['RGB_sha256']:
            raise ValueError('Accepted original RGB changed')
        center = centers[row['item_id']]['center']
        candidates = []
        for relative in protocol['relative_widths']:
            box = geo.box_for_width(row['width'], row['height'], center, relative)
            if box not in candidates:
                candidates.append(box)
        baseline = centers[row['item_id']]['baseline_box']
        if baseline not in candidates or not candidates:
            raise ValueError('Original deployed box must remain in the legal candidate set')
        image, sx, sy = encode_image(rgb)
        rois = encode_rois(candidates, sx, sy)
        target = destination / (row['item_id'].replace(':', '_') + '.pt')
        payload = dict(image=image, rois=rois)
        with target.open('xb') as stream:
            torch.save(payload, stream)
        saved = torch.load(target, map_location='cpu', weights_only=True)
        if any(not torch.equal(saved[k], value) for k, value in payload.items()):
            raise ValueError('First input save/reload changed real values')
        record = dict(item_id=row['item_id'], source_rgb=row['rgb'], input=reference(target),
            signatures={k: signature(v) for k, v in payload.items()}, candidates=candidates,
            baseline_box=baseline, source_width=row['width'], source_height=row['height'], center=center)
        append(ROOT / 'input_journal.jsonl', record)
        accepted.append(record)
        x1, y1, x2, y2 = row['original_normalized_xyxy']
        references.append(dict(item_id=row['item_id'], original_xywh=[x1 * row['width'], y1 * row['height'],
            (x2 - x1) * row['width'], (y2 - y1) * row['height']]))
    if len(accepted) != 80 or torch.cuda.is_initialized():
        raise ValueError('Registered CPU-only80 denominator')
    write(ROOT / 'inputs.json', accepted)
    write(ROOT / 'references.json', references)
    write(ROOT / 'input_acceptance.json', dict(status='PASS80_FIRST_AUTHOR_PREPROCESS_LEGAL_CANDIDATES',
        images=80, proposals=sum(len(r['candidates']) for r in accepted), preprocessing_contract=contract,
        inputs=reference(ROOT / 'inputs.json'), references=reference(ROOT / 'references.json'),
        original_media_or_Qwen_processor_repeated=False, new_Qwen_generations=0, GPU_initialized=False,
        media_and_original_sources_overlap_with_model_pretraining='UNKNOWN', all80_historical_S1_metrics_exposed=True))


if __name__ == '__main__':
    main()
