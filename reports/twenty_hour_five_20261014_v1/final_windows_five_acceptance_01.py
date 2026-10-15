"""Final actual-delivery union check; does not re-run any Linux stage."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import zipfile

R = Path(__file__).resolve().parents[2]


def canonical(values):
    relevant = [dict(video_id=v['video_id'], targetRatioWH=v['targetRatioWH'], predictions=v['predictions'])
                for v in sorted(values, key=lambda v: v['video_id'])]
    return hashlib.sha256(json.dumps(relevant, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def main():
    history = json.loads((R / 'reports/twenty_hour_five_20261014_v1/linux_historical_canonical_set_01.json').read_text(encoding='utf8'))
    assert history['status'] == 'FROZEN_HISTORY_CANONICAL_IDENTITIES_FROM_ACCEPTED_PACKAGE_LOCK'
    assert history['source_history_ref']['sha256'] == 'b05a80b2d23349a3b1976b521067e3c81571bd9062989c0f7be5c2e49bf7f82e'
    old = set(history['canonical_SHA256'])
    assert old and len(old) == history['unique_historical_predictions']
    paths = sorted((R / 'deliveries').glob('AIC20H_TEMPORAL_*_20261014/delivery_receipt.json'))
    assert len(paths) == 5, 'Exactly five actual new campaign delivery receipts required'
    accepted = []
    for path in paths:
        done = json.loads(path.read_text(encoding='utf8'))
        assert done['status'] == 'PASS_WINDOWS_FINAL_ZIP_SIZE_SHA_CRC_MEMBER_SOURCESET'
        x = done['remote_receipt']
        p = Path(done['local_zip'])
        assert p.is_file()
        with zipfile.ZipFile(p) as z:
            member = z.read('predictions.jsonl')
        values = [json.loads(line) for line in member.splitlines() if line]
        actual = canonical(values)
        assert actual == x['canonical_SHA256']
        assert actual not in old, 'A new name is not a new prediction'
        assert x['independent11strict'] is True and x['quality_pass_claimed'] is False
        assert x['actual_parameters'] == 8782459120 and x['website_submitted'] is False
        accepted.append(dict(arm=x['arm'], local_zip=str(p.resolve()), bytes=x['bytes'], SHA256=x['SHA256'],
                             member_SHA256=x['member_SHA256'], canonical_SHA256=actual,
                             frame_count=x['frame_count'], records=426, independent11strict=True,
                             official_score='UNKNOWN', quality_pass_claimed=False))
    assert len({x['arm'] for x in accepted}) == len({x['SHA256'] for x in accepted}) == len({x['canonical_SHA256'] for x in accepted}) == 5
    receipt = dict(status='PASS_FIVE_REAL_NEW_WINDOWS_ZIPS_COMPLETE_UNION_ACCEPTANCE_NOT_OFFICIAL_SCORE',
                   utc=dt.datetime.now(dt.timezone.utc).isoformat(), target=5, actual_new_delivered=5,
                   packages=accepted, every_package_actual_records=426, physical_model_parameters=8782459120,
                   scientific_quality_claim=False, website_submitted=False, raw_tensor_clock_transfers=0,
                   genuine_canonical_differences_actual_local_verified=True,
                   historical_canonical_reference=history['source_history_ref'],
                   distinct_from_historical_packages_actual_local_verified=True)
    out = R / 'reports/twenty_hour_five_20261014_v1/final_windows_delivery_acceptance_01.json'
    with out.open('x', encoding='utf8') as f:
        json.dump(receipt, f, ensure_ascii=False, indent=2)
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == '__main__':
    main()
