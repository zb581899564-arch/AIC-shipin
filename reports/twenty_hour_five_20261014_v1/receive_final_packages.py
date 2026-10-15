"""Receive only newly accepted final ZIPs and short receipts from Linux.

No raw/tensor/clock download. Existing successful deliveries are never copied
again. A partial carrier is retained for explicit diagnosis if it is corrupt.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

CAMPAIGN = '/home/inspur/aic_video_work/twenty_hour_five_20261014_v1'
REMOTE_ROOT = CAMPAIGN + '/temporal_family_native_package_v3'
WORKSPACE = Path(__file__).resolve().parents[2]
ARMS = ('START', 'END', 'BOTH', 'VERIFY', 'VERIFY_BOTH',
        'SOURCE_START', 'SOURCE_END', 'SOURCE_BOTH')


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def require(value, reason):
    if not value:
        raise ValueError(reason)


def save_new(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def receive(receipt_file):
    summary = json.loads(receipt_file.read_text(encoding='utf-8-sig'))
    require(summary['status'] == 'COMPLETE_AVAILABLE_ACTUALLY_DISTINCT_NEW_FAMILY_PACKAGES',
            'Actual remote package completion required')
    packages = summary['packages']
    require(len(packages) == summary['actual_packages'] <= 5, 'Actual package denominator')
    require(len({row['canonical_SHA256'] for row in packages}) == len(packages),
            'Packages must have genuinely distinct predictions')
    delivered = []
    for row in packages:
        arm = row['arm']
        require(arm in ARMS and row['status'] == 'PASS_ENGINEERING_NEW_TEMPORAL_EXPLICIT_RISK_ZIP_NOT_OFFICIAL_SCORE'
                and row['records'] == 426 and row['independent11strict'] is True
                and row['actual_parameters'] == 8782459120
                and row['quality_pass_claimed'] is False and row['website_submitted'] is False,
                'Only genuinely validated new engineering-risk final packages')
        expected = REMOTE_ROOT + '/package_' + arm + '/candidate_TEMPORAL_' + arm + '.zip'
        require(row['zip'] == expected and 0 < row['bytes'] <= 20_000_000,
                'Unexpected remote file or non-small final ZIP')
        out = WORKSPACE / 'deliveries' / ('AIC20H_TEMPORAL_' + arm + '_20261014')
        out.mkdir(parents=True, exist_ok=True)
        marker = out / 'delivery_receipt.json'
        target = out / ('candidate_TEMPORAL_' + arm + '.zip')
        if marker.exists():
            previous = json.loads(marker.read_text(encoding='utf-8'))
            require(previous['remote_receipt'] == row and target.is_file(),
                    'Existing successful delivery belongs to a different artifact')
            delivered.append(previous)
            continue
        require(not target.exists(), 'Unreceipted final file requires diagnosis')
        partial = target.with_suffix('.zip.partial')
        if not partial.exists():
            subprocess.run(['scp', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
                            '-o', 'StrictHostKeyChecking=yes',
                            'aic-inspur-home:' + row['zip'], str(partial)], check=True)
        require(partial.stat().st_size == row['bytes'] and digest(partial) == row['SHA256'],
                'Carrier size/SHA mismatch; retain partial and diagnose explicitly')
        with zipfile.ZipFile(partial) as archive:
            require(archive.namelist() == ['predictions.jsonl'] and archive.testzip() is None,
                    'Single-member ZIP/CRC mismatch')
            body = archive.read('predictions.jsonl')
        require(hashlib.sha256(body).hexdigest() == row['member_SHA256'], 'Exact member SHA mismatch')
        records = [json.loads(line) for line in body.splitlines() if line]
        require(len(records) == 426 and {x['video_id'] for x in records} == {str(i) for i in range(426)},
                'Windows received incomplete or duplicated source set')
        require(all(x['predictions'] and x['model_params_b'] == 8.78245912 for x in records),
                'Windows received empty source or parameter mismatch')
        require(sum(len(x['predictions']) for x in records) == row['frame_count'],
                'Windows received wrong selected-frame count')
        partial.rename(target)
        result = dict(status='PASS_WINDOWS_FINAL_ZIP_SIZE_SHA_CRC_MEMBER_SOURCESET',
                      utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                      local_zip=str(target.resolve()), remote_receipt=row,
                      raw_tensor_clock_transfers=0, website_submitted=False,
                      official_score='UNKNOWN', quality_pass_claimed=False)
        save_new(marker, result)
        delivered.append(result)
        print(json.dumps(dict(arm=arm, zip=str(target.resolve()), bytes=row['bytes'],
                              SHA256=row['SHA256'], official_score='UNKNOWN'), ensure_ascii=False), flush=True)
    print(json.dumps(dict(actual_new_deliveries=len(delivered), goal_count=5,
                          goal_complete_claimed=False), ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--receipt-file', type=Path, required=True)
    receive(parser.parse_args().receipt_file)
