"""Explicitly resume the zero-payload weight request; adopt all successful code."""
from common import ROOT, COMMIT, WEIGHT_BYTES, WEIGHT_URL, read, ref, write
from assets import BLOBS, fetch


def main():
    assert read(ROOT / 'assets_terminal.json')['exit_code'] == 1
    assert not list((ROOT / 'model').iterdir())
    write(ROOT / 'asset_remaining02_claim.json', dict(
          reason='Original author browser weight endpoint timed out before response/payload',
          successful_source_and_runtime_files_adopted=True, weight_successes_before=0,
          same_public_author_endpoint=True, direct_gate_unchanged=True, requests=1))
    originals = list(BLOBS) + ['LICENSE', 'X-CLIP/README.md', 'X-CLIP/configs/k400/32_8.yaml']
    files = [ref(ROOT / 'author' / name) for name in originals]
    ports = [dict(original=ref(ROOT / 'author' / name), inference_port=ref(ROOT / 'runtime' / name))
             for name in BLOBS]
    release = read(ROOT / 'downloads/release.json')
    item = next(a for a in release['assets'] if a['id'] == 71848091)
    assert item['size'] == WEIGHT_BYTES and item['browser_download_url'] == WEIGHT_URL
    weight = fetch(WEIGHT_URL, ROOT / 'model/k400_32_8.pth', WEIGHT_BYTES, WEIGHT_BYTES)
    write(ROOT / 'download_acceptance.json', dict(files=files, runtime=ports, weight=weight,
          author_commit=COMMIT, release_asset_id=item['id'], publisher_digest=item.get('digest'),
          publisher_sha256_available=False, no_auto_download=True,
          preserved_failure='assets_terminal.json/assets.log/failure.json',
          explicit_recovery='asset_remaining02', repeated_successful_downloads=0))


if __name__ == '__main__':
    main()
