"""Select sources by name hash only; preserve original crowd summaries."""
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.io import loadmat

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / 'reports/human_reference_iteration_20261013_v1'
MATERIAL = REPORT / 'summe_original_metadata_01'


def main():
    receipt = json.loads((MATERIAL / 'receipt.json').read_text())
    assert receipt['status'].startswith('PASS') and receipt['videos_downloaded'] == 0
    inventory = {row['name']: row for row in receipt['inventory']}
    gt = []
    for path in sorted((MATERIAL / 'GT').glob('*.mat')):
        data = loadmat(path)
        n = int(data['nFrames'].item())
        scores = data['user_score']
        assert scores.shape[0] == n and scores.ndim == 2 and scores.shape[1] >= 15
        assert np.isfinite(scores).all() and (scores >= 0).all()
        assert np.array_equal((scores > 0).mean(axis=1), data['gt_score'].reshape(-1))
        member = inventory['videos/' + path.stem + '.webm']
        gt.append(dict(source_name=path.stem, source_group='SumMe:' + path.stem,
                       order_key=hashlib.sha256(('SUMME_HUMAN_20261013_V1:' + path.stem).encode()).hexdigest(),
                       annotation_path=str(path.resolve()), annotation_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                       annotation_frames=n, annotation_fps=float(data['FPS'].item()),
                       annotation_duration=float(data['video_duration'].item()),
                       human_summary_columns=int(scores.shape[1]),
                       user_id_metadata_columns=int(data['all_userIDs'].size),
                       labels='user_score > 0, following original author evaluation; values encode segment identities',
                       member=member))
    assert len(gt) == 25
    gt.sort(key=lambda row: row['order_key'])
    selected = gt[:20]
    for index, row in enumerate(selected):
        row['role'] = 'screen' if index < 12 else 'confirm'
    result = dict(status='REGISTERED_BEFORE_MODEL_PREDICTIONS_NOT_MEDIA_OR_QUALITY_ADMISSION',
                  original_source_url=receipt['source_url'], archive_bytes=receipt['full_archive_bytes'],
                  selected_sources=20, screen_sources=12, confirm_sources=8, rows=selected,
                  reserve_sources=[row['source_name'] for row in gt[20:]],
                  exact_compressed_media_payload_bytes=sum(row['member']['compressed_bytes'] for row in selected),
                  exact_decoded_file_bytes=sum(row['member']['bytes'] for row in selected),
                  direct_official_to_linux_proposed=True,
                  video_license='Original README: non-commercial research only; no redistribution of input videos',
                  annotation_license='Original README: freely for research with GygliECCV14 citation',
                  differences_from_competition='Human subjective video summaries; not crop geometry labels or unanimous ordinary negatives',
                  annotation_values_binarized_per_author=True,
                  user_id_metadata_incomplete_not_used_to_drop_summary_columns=True,
                  native_frame_mapping='UNVERIFIED', known_source_separation='PENDING',
                  new_model_calls=0, new_optimizer_updates=0)
    with (REPORT / 'human_source_registration_01.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
    print(json.dumps({key: value for key, value in result.items() if key != 'rows'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
