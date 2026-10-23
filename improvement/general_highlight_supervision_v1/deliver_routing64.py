"""Receive only final two artifacts over a freshly verified direct strict SSH path."""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import subprocess
import zipfile
from direct_route64 import snapshot, direct_peer, SSH
from routing_package63_common import canonical

LOCAL = Path(__file__).resolve().parents[2]
REPORT = LOCAL / 'reports/overnight_candidates_20261022_v1'
REMOTE = '/home/inspur/aic_video_work/general_highlight_supervision_20261021_v1/routing_package63'
PROTECTED = LOCAL / 'deliveries/CONTEXT_SEMANTIC_RESIDUAL_8B_20261016/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip'
EXPECTED_SHA = 'b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def validate_archive(path, expected, history):
    if path.stat().st_size != expected['ZIP']['bytes'] or sha(path) != expected['ZIP']['sha256']:
        raise ValueError('Cross-machine final ZIP size/SHA differ')
    with zipfile.ZipFile(path) as archive:
        if archive.namelist() != ['predictions.jsonl'] or archive.testzip() is not None:
            raise ValueError('Windows final CRC or member set invalid')
        raw = archive.read('predictions.jsonl')
    if hashlib.sha256(raw).hexdigest() != expected['member']['sha256']:
        raise ValueError('Final JSONL member identity differs from Linux')
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if len(rows) != 426 or {row['video_id'] for row in rows} != {str(i) for i in range(426)}:
        raise ValueError('Final426 set differs')
    for row in rows:
        if row['targetRatioWH'] not in [[16, 9], [9, 16]] or row['model_params_b'] != 8.816809946:
            raise ValueError('Final target ratio/accounting invalid')
        frames = [item['frame'] for item in row['predictions']]
        if frames != sorted(set(frames)) or any(type(frame) is not int or frame < 0 for frame in frames):
            raise ValueError('Final native ordinal ordering invalid')
        if any(len(item['bboxes']) != 3 or not all(type(v) in (int, float) and math.isfinite(v) for v in item['bboxes'])
               for item in row['predictions']):
            raise ValueError('Final bbox scalar structure invalid')
    if sum(len(row['predictions']) for row in rows) != expected['selected_frames']:
        raise ValueError('Final selected denominator differs')
    digest = canonical(rows)
    if digest != expected['canonical_sha256'] or digest in history:
        raise ValueError('Final prediction identity differs or duplicates historical/other candidate')
    history.add(digest)


def main():
    if PROTECTED.stat().st_size != 384630 or sha(PROTECTED) != EXPECTED_SHA:
        raise ValueError('Protected40.47 is not the original accepted baseline')
    manifest_cmd = SSH + ['aic-inspur-home', 'cat ' + REMOTE + '/completion.json']
    result = subprocess.run(manifest_cmd, capture_output=True, timeout=20)
    if result.returncode or len(result.stdout) > 20000:
        raise RuntimeError('Actual short completed-package receipt unavailable')
    manifest = json.loads(result.stdout)
    if manifest['state'] != 'TWO_DISTINCT_ALL426_CPU_PACKAGES_QA_COMPLETE_WINDOWS_PENDING' or len(manifest['candidates']) != 2:
        raise ValueError('Actual two-package Linux terminal missing')
    route = snapshot()
    save(REPORT / 'direct_delivery_route64.json', dict(UTC=datetime.now(timezone.utc).isoformat(), **route))
    catalog = json.loads((Path(__file__).parent / 'historical_artifact_catalog63.json').read_text(encoding='utf8'))
    history = {row['canonical_sha256'] for row in catalog['accepted']}
    deliveries = []
    for item in manifest['candidates']:
        policy = item['policy']
        stem = {'source_rerank': 'SPORT_ROUTE_RERANK_8B', 'source_remove': 'SPORT_ROUTE_REMOVE_8B'}[policy]
        source = PurePosixPath(item['ZIP']['path'])
        if source.parent != PurePosixPath(REMOTE) / policy or source.name != 'candidate_' + stem + '.zip':
            raise ValueError('Unexpected final ZIP path; do not download')
        destination = LOCAL / 'deliveries' / (stem + '_20261022'); destination.mkdir()
        partial = destination / (source.name + '.partial')
        scp = ['scp', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=12',
               '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=2',
               'aic-inspur-home:' + str(source), str(partial)]
        transfer = subprocess.run(scp, capture_output=True, timeout=90)
        if transfer.returncode:
            raise RuntimeError('Final ZIP transfer failed; preserve partial/successful files: ' + transfer.stderr.decode(errors='replace')[:300])
        validate_archive(partial, item, history)
        final = destination / source.name; partial.rename(final)
        receipt = dict(**item, Windows_path=str(final), Windows_bytes=final.stat().st_size,
            Windows_sha256=sha(final), CRC_member_and_426_readback=True, source='Actual Linux final ZIP only',
            route_receipt=str(REPORT / 'direct_delivery_route64.json'), raw_tensor_media_transferred=False)
        save(destination / 'delivery_acceptance.json', receipt); deliveries.append(receipt)
        (destination / '说明.txt').write_text(
            '40.47原包保持。仅自动识别到固定四类竞技场景时应用此策略，其他来源逐帧保持。\n'
            + ('等覆盖重新排序，逐源选帧数量不变。\n' if policy == 'source_rerank' else '仅从原选帧中删除弱片段，不新增帧；允许合法空输出。\n')
            + '全部主辅8.816809946B。426/原生PTS/原框来源/独立11strict/ZIP及Windows一致性通过。\n'
            + '收益只在一条已曝光外部跳水样本得到支持；不能保证通用或官网提分。未自动提交。\n', encoding='utf-8')
    if sha(PROTECTED) != EXPECTED_SHA:
        raise ValueError('Protected baseline changed during delivery')
    after = direct_peer(15889, 'linux-direct-test')
    before = route['windows_peer']
    received = after['stats']['rx_bytes'] - before['stats']['rx_bytes'] if after['connection_id'] == before['connection_id'] else None
    save(REPORT / 'windows_delivery64.json', dict(state='TWO_DISTINCT_CANDIDATE_ZIPS_DELIVERED',
        UTC=datetime.now(timezone.utc).isoformat(), candidates=deliveries, baseline40_47_unchanged=True,
        baseline_SHA256=EXPECTED_SHA, new_official_submissions=0, official_score='UNKNOWN',
        current_direct_peer_after=after, actual_UDP_received_delta=received,
        automatic_experiments_after_delivery=False))
    print(json.dumps(dict(delivered=len(deliveries), paths=[r['Windows_path'] for r in deliveries],
        bytes=[r['Windows_bytes'] for r in deliveries], official_score='UNKNOWN'), ensure_ascii=False))


if __name__ == '__main__': main()
