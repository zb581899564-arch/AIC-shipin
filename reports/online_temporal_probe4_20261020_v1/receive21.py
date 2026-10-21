"""Download one container of final ZIPs only, then verify four submission artifacts."""
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import subprocess
import zipfile

H = Path(__file__).resolve().parent
WORK = H.parents[1]
REMOTE = '/home/inspur/aic_video_work/online_temporal_probe4_20261020_v1'
PY = '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
ALIAS = 'aic-inspur-tailscale'
BASE = WORK / 'deliveries/CONTEXT_SEMANTIC_RESIDUAL_8B_20261016/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip'


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def canonical(rows):
    data = [{k: row[k] for k in ['video_id', 'targetRatioWH', 'predictions']}
            for row in sorted(rows, key=lambda x: x['video_id'])]
    return sha(json.dumps(data, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())


def save(p, data):
    with p.open('x', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


source = 'ROOT=' + repr(REMOTE) + '\n' + r'''
from pathlib import Path
import hashlib,json,zipfile
R=Path(ROOT);c=json.loads((R/'completion21.json').read_text())
assert c['status']=='FOUR_DISTINCT_RISK_ZIPS_LINUX_ACCEPTED_PENDING_WINDOWS'
assert len(c['candidates'])==4 and c['accuracy_metric_runs']==0 and c['model_calls']==0
for item in c['candidates']:
 v=json.loads(Path(item['independent_validation_ref']['path']).read_text())
 assert len(v['checks'])==11 and all(v['checks'].values()) and not v['strict_loader_issues']
p=Path(c['bundle_ref']['path']);b=p.read_bytes()
assert len(b)==c['bundle_ref']['bytes'] and hashlib.sha256(b).hexdigest()==c['bundle_ref']['sha256']
with zipfile.ZipFile(p) as z:assert z.testzip() is None
print(json.dumps(c))
'''
r = subprocess.run(['ssh', '-o', 'ConnectTimeout=15', ALIAS, PY + ' -B -'], input=source,
                   text=True, capture_output=True, timeout=55)
print(r.stderr)
r.check_returncode()
remote = json.loads(r.stdout)
save(H / 'windows_delivery_started21.json', dict(utc=datetime.now(timezone.utc).isoformat(), remote=remote))
partial = H / 'final_bundle21.zip.partial01'
assert not partial.exists()
subprocess.run(['scp', '-o', 'ConnectTimeout=15', ALIAS + ':' + remote['bundle_ref']['path'], str(partial)],
               check=True, timeout=180)
bundle = partial.read_bytes()
assert len(bundle) == remote['bundle_ref']['bytes'] and sha(bundle) == remote['bundle_ref']['sha256']
assert BASE.stat().st_size == 384630 and sha(BASE.read_bytes()) == 'b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'
with zipfile.ZipFile(BASE) as z:
    baseline = [json.loads(s) for s in z.read('predictions.jsonl').splitlines() if s.strip()]
ids = {r['video_id'] for r in baseline}
ratios = {r['video_id']: r['targetRatioWH'] for r in baseline}
history = json.loads((H / 'history_fingerprints21.json').read_text(encoding='utf-8'))
used = {v['canonical_sha256'] for v in history['packages']}
target = WORK / 'deliveries/ONLINE_TEMPORAL_PROBE4_20261020'
target.mkdir(exist_ok=False)
deliveries = []
with zipfile.ZipFile(io.BytesIO(bundle)) as outer:
    assert outer.testzip() is None
    expected = {'delivery_manifest21.json'} | {Path(x['zip_ref']['path']).name for x in remote['candidates']}
    assert set(outer.namelist()) == expected and len(outer.namelist()) == 5
    manifest = json.loads(outer.read('delivery_manifest21.json'))
    assert manifest['candidates'] == remote['candidates']
    for item in remote['candidates']:
        name = Path(item['zip_ref']['path']).name
        assert Path(name).name == name and name.endswith('.zip')
        data = outer.read(name)
        assert len(data) == item['zip_ref']['bytes'] and sha(data) == item['zip_ref']['sha256']
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            assert archive.namelist() == ['predictions.jsonl'] and archive.testzip() is None
            payload = archive.read('predictions.jsonl')
        assert len(payload) == item['member_bytes'] and sha(payload) == item['member_sha256']
        rows = [json.loads(s) for s in payload.splitlines() if s.strip()]
        assert len(rows) == 426 and {r['video_id'] for r in rows} == ids
        assert all(r['targetRatioWH'] == ratios[r['video_id']] for r in rows)
        assert all(r['model_params_b'] == item['actual_pipeline_parameters'] / 1e9 for r in rows)
        assert sum(len(r['predictions']) for r in rows) == item['frames']
        actual = canonical(rows)
        assert actual == item['canonical_sha256'] and actual not in used
        used.add(actual)
        final = target / name
        with final.open('xb') as f:
            f.write(data)
        deliveries.append(dict(index=item['index'], method=item['method'], local_zip=str(final),
            bytes=len(data), sha256=sha(data), frames=item['frames'], added_frames=item['added_frames'],
            removed_frames=item['removed_frames'], empty_sources=item['empty_sources'],
            actual_pipeline_parameters=item['actual_pipeline_parameters'], official_score='UNKNOWN',
            Linux11strict='PASS', Windows_size_SHA_CRC_member_SHA_history_distinct='PASS'))
partial.rename(H / 'received_final_bundle21.zip')
receipt = dict(status='FOUR_DISTINCT_NEW_RISK_ZIPS_WINDOWS_ACCEPTED', utc=datetime.now(timezone.utc).isoformat(),
    deliveries=deliveries, transfer_bytes=len(bundle), transfer_sha256=sha(bundle),
    protected_baseline_unchanged=True, baseline_score=40.47, local_accuracy_metric_runs=0,
    new_model_calls=0, new_training_updates=0, automatic_submission=False, remote=remote)
save(H / 'windows_delivery_completion21.json', receipt)
save(target / 'WINDOWS_DELIVERY_RECEIPT.json', receipt)
labels = ['一致补召回（原帧全保留）', '一致删选（三次都不支持才删）',
          '逐窗口视觉对比选择', '131权重内容critic（未过原本地对照，风险试分）']
text = '# 四个时序方向在线探索包\n\n40.47原包不变；本轮未运行本地F1/代理准确率，没有提分保证。\n\n'
for item, label in zip(deliveries, labels):
    text += f"{item['index']}. {label}：{Path(item['local_zip']).name}\n\n"
    text += f"   {item['frames']}帧，新增{item['added_frames']}、删除{item['removed_frames']}，空来源{item['empty_sources']}；SHA256 {item['sha256']}\n\n"
text += '顺序已固定；请按编号分别反馈官方总分。只比较完整方案，不按测试内容逐条修正。全部经过426记录/原生PTS/空间来源/参数/11项格式/CRC/成员SHA/Windows验收。完整计算证据留Linux；不自动官网提交。\n'
(target / '提交顺序与真实限制.md').write_text(text, encoding='utf-8')
(H / 'DELIVERY21.md').write_text(text, encoding='utf-8')
ack = 'VALUE=' + repr(receipt) + '\n' + r'''
from pathlib import Path
import json
p=Path('/home/inspur/aic_video_work/online_temporal_probe4_20261020_v1/windows_delivery_completion21.json')
with p.open('x') as f:json.dump(VALUE,f,ensure_ascii=False,indent=2)
print('FOUR_WINDOWS_FINAL_ZIPS_ACKNOWLEDGED')
'''
r = subprocess.run(['ssh', '-o', 'ConnectTimeout=15', ALIAS, PY + ' -B -'], input=ack,
                   text=True, encoding='utf-8', capture_output=True, timeout=45)
save(H / 'windows_delivery_ack21.json', dict(exit_code=r.returncode, stdout=r.stdout, stderr=r.stderr))
print(json.dumps(dict(status=receipt['status'], deliveries=deliveries, transfer_bytes=len(bundle))))
print(r.stdout); print(r.stderr); r.check_returncode()
