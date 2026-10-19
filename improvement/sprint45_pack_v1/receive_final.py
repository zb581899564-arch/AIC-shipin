"""Receive only a completed final ZIP and its brief receipt; no raw exports."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(remote_receipt, label, alias='aic-inspur-home', tailscale_nc=False):
    if alias not in ('aic-inspur-home', 'aic-inspur-tailscale'):
        raise ValueError('Existing configured alias required')
    transport = ['-o', 'BatchMode=yes', '-o', 'ConnectTimeout=12']
    if tailscale_nc:
        if alias != 'aic-inspur-tailscale':
            raise ValueError('Explicit current Tailscale route only')
        transport += ['-o', 'ProxyCommand="C:/Program Files/Tailscale/tailscale.exe" nc %h %p']
    if not label.replace('_', '').isalnum():
        raise ValueError('Plain independent delivery label required')
    if not remote_receipt.startswith('/home/inspur/aic_video_work/') or "'" in remote_receipt:
        raise ValueError('Exact project receipt path required')
    code = 'import pathlib,json; p=pathlib.Path(' + repr(remote_receipt) + '); print(p.read_text())'
    query = subprocess.run(['ssh'] + transport + [alias, 'python3 -'], input=code, text=True,
                           capture_output=True, timeout=40, check=True)
    receipt = json.loads(query.stdout)
    if not receipt.get('path', '').endswith('.zip') or receipt.get('online_effect') != 'UNKNOWN':
        raise ValueError('Actual completed unknown-effect ZIP required')
    folder = Path(__file__).resolve().parents[2] / 'deliveries' / label
    folder.mkdir(exist_ok=False)
    archive = folder / Path(receipt['path']).name
    subprocess.run(['scp'] + transport + [alias + ':' + receipt['path'], str(archive)], check=True, timeout=90)
    assert archive.stat().st_size == receipt['bytes'] and digest(archive) == receipt['sha256']
    with zipfile.ZipFile(archive) as z:
        assert z.namelist() == ['predictions.jsonl'] and z.testzip() is None
        member = z.read('predictions.jsonl')
    assert hashlib.sha256(member).hexdigest() == receipt['member_sha256']
    rows = [json.loads(line) for line in member.splitlines()]
    assert len(rows) == 426 and {r['video_id'] for r in rows} == {str(i) for i in range(426)}
    assert all(isinstance(r['predictions'], list) and r['model_params_b'] <= 9 for r in rows)
    assert sum(not r['predictions'] for r in rows) == receipt.get('empty_sources', 0)
    assert all(len({p['frame'] for p in r['predictions']}) == len(r['predictions']) for r in rows)
    frames = sum(len(r['predictions']) for r in rows)
    assert frames == receipt['frames']
    (folder / 'linux_completion.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
    local = dict(path=str(archive), bytes=archive.stat().st_size, sha256=digest(archive),
                 member_sha256=hashlib.sha256(member).hexdigest(), records=426, frames=frames,
                 CRC=True, same_as_linux=True, online_effect='UNKNOWN', website_submitted=False,
                 transport_alias=alias, tailscale_userspace_nc=tailscale_nc)
    (folder / 'windows_acceptance.json').write_text(json.dumps(local, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(local, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--receipt', required=True)
    parser.add_argument('--label', required=True)
    parser.add_argument('--alias', choices=['aic-inspur-home', 'aic-inspur-tailscale'], default='aic-inspur-home')
    parser.add_argument('--tailscale-nc', action='store_true')
    args = parser.parse_args()
    main(args.receipt, args.label, args.alias, args.tailscale_nc)
