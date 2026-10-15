"""Package actual stopped experiment evidence and byte-exact existing best ZIP."""
from pathlib import Path
from fractions import Fraction
from datetime import datetime, timezone
import hashlib
import json
import shutil
import zipfile

PROJECT = Path(r'G:\ai\AIC视频')
ROOT = PROJECT/'reports/annotation_iteration_20261010/complete_reference_supplement_v1'
OUT = PROJECT/'deliveries/SILVER24_SFT_20261011'
EXPECTED_BEST = '07730c9e02e68d1a1ce54e7ef5a8aa616346cf8f2f8d78426ed36bc3eb481496'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')


def main():
    snapshot = read(OUT/'remote_final_snapshot.json')
    for entry in snapshot['files']:
        p = OUT/'evidence'/entry['local_name']
        assert p.stat().st_size == entry['bytes'] and digest(p) == entry['sha256']
    completion = read(OUT/'evidence/completion.json')
    quality = read(OUT/'evidence/independent_quality_receipt.json')
    training = read(OUT/'evidence/training_receipt.json')
    gate = quality['scientific_gate']
    assert completion['status'] == 'STOP_SCIENTIFIC_QUALITY_NO426_NO_RETUNING'
    assert completion['candidate_started'] is False and quality['quality_gate_passed'] is False
    assert quality['model_calls_reconstructed'] == 24 and training['new_optimizer_updates'] == 4
    assert snapshot['owned_processes'] == []
    original = PROJECT/'deliveries/ANNOTATION_ITERATION_20261010/SAFE_37_66/candidate_SAFE_37_66.zip'
    original_acceptance = original.parent/'acceptance.json'
    assert digest(original) == EXPECTED_BEST and original.stat().st_size == 306167
    assert read(original_acceptance)['sha256'] == EXPECTED_BEST
    target = OUT/'candidate_SAFE_BEST_37_66.zip'
    assert not target.exists()
    shutil.copyfile(original, target)
    assert digest(target) == EXPECTED_BEST
    with zipfile.ZipFile(target) as archive:
        assert archive.namelist() == ['predictions.jsonl'] and archive.testzip() is None
        data = archive.read('predictions.jsonl')
    rows = [json.loads(line) for line in data.splitlines() if line.strip()]
    assert len(rows) == 426 and len({row['video_id'] for row in rows}) == 426
    assert sum(len(row['predictions']) for row in rows) == 102112
    assert hashlib.sha256(data).hexdigest() == 'a20c5697c9060d5779154207d883c03ff38c06f57b38001da1cee2090d48a6f4'
    for name in ['dataset24_final_admission_schema_recovery_v1.json', 'denominator24_v21.json']:
        shutil.copyfile(ROOT/name, OUT/'evidence'/name)
    shutil.copyfile(original_acceptance, OUT/'evidence/historical_best_acceptance.json')
    failed = [k for k, value in gate['checks'].items() if not value]
    gain_exact = gate['locked']['positive_macro_gain']
    gain = float(Fraction(gain_exact))
    report = {
        'status': 'PASS_EVIDENCE_AND_BYTE_EXACT_EXISTING_BEST_DELIVERY_NEW_ADAPTER_NOT_PROMOTED',
        'packaged_utc': datetime.now(timezone.utc).isoformat(),
        'format_repairs': 'CLI39 final self-read and CLI40 eight duplicated Windows separators recovered by separate typed receipts; original rejected audits and raw preserved.',
        'dataset': {'total_planned': 24, 'qualified': 20, 'rejected': 4, 'pending': 0, 'train_windows': 8, 'evaluation_windows': 12, 'remaining_two_windows_completed': True},
        'training': {'actual_optimizer_updates': 4, 'examples_backward': 16, 'changed_lora_tensors': 288, 'base_and_vision_frozen': True, 'adapter': snapshot['adapter']},
        'evaluation': {'actual_model_calls': 24, 'independent_cpu_reconstructed': 24, 'quality_gate_passed': False,
            'scope': 'FINITE_OBSERVATION_SILVER_DIAGNOSTIC_NOT_GOLD_OR_OFFICIAL', 'locked_macro_f1_gain_exact': gain_exact,
            'locked_macro_f1_gain': gain, 'frozen_required_gain': 0.05, 'failed_checks': failed},
        'new_candidate': {'started': False, 'new_426_predictions': False, 'new_finetuned_submission_zip': False, 'official_score': None},
        'existing_best_submission': {'path': str(target), 'bytes': target.stat().st_size, 'sha256': digest(target),
            'records': 426, 'frames': 102112, 'historical_user_reported_score': 37.66,
            'score_independently_logged_in_this_run': False, 'new_training_output': False, 'official_upload_this_run': False,
            'verification_this_run': 'Byte SHA, CRC, unique JSONL, parsed count and identity uniqueness; prior independent strict provenance acceptance referenced, not rerun.'},
        'resource_cost': {'actual_new_gpu_runner_seconds': snapshot['total_new_charged_seconds'], 'unique_terminal_equal': True, 'historical_costs_preserved': True, 'cash': 'UNKNOWN_NOT_ZERO'},
        'completion_timestamp_note': snapshot['completion_timestamp_note'],
        'next_scientific_work_not_started': 'Use a separately frozen experiment with new training sources and normal-versus-event/boundary contrast labels. Keep this locked evaluation diagnostic exposed; never move its windows into training or retune this failed recipe against it.'
    }
    save(OUT/'delivery_acceptance.json', report)
    text = f'''本轮已完成格式恢复、剩余两窗标注、数据验收、实际微调和独立评估。

可提交文件：candidate_SAFE_BEST_37_66.zip
这是原37.66分包的逐字节副本，426视频、102112帧，306167字节。
SHA256：{EXPECTED_BEST}
37.66来自用户此前提交反馈；本轮未提交官网，也没有新的官方成绩。

本轮新微调结果：20合格窗口（8训练、12评估），4次真实optimizer更新，288个LoRA张量改变。基座和视觉权重冻结。24次评估回答全部由独立CPU重建核验。
新适配器未通过质量门，锁定来源宏平均F1提升{gain:.6f}，要求至少0.05；普通片段新增误选、部分召回不退化和UNKNOWN保守性条件也未全部通过。这是有限可观察片段的silver诊断，不是官网评分。
因此新适配器未替换生产模型，未启动新的426视频生成，本轮没有合格的新微调提交包。
新适配器保留：{snapshot['adapter']['path']}
适配器SHA256：{snapshot['adapter']['sha256']}
新增训练及评估GPU runner实际计费时长：{snapshot['total_new_charged_seconds']:.3f}秒，旧成本保留，现金单价未知。

evidence/保留原始验收、训练、评估、独立复核和唯一终态费用回执。全部本地副本与远端SHA一致。格式修复保留旧REJECT及原raw，没有补造输出或把UNKNOWN当负样本。
原completion.json的utc由控制器进入execute时写入，是报告创建时刻而非完成时刻；原文件未改。实际结束时间见费用回执和independent_quality.execution.json；采集时刻及completion文件mtime见remote_final_snapshot.json。

下一轮建议：另立冻结实验，补充新的训练来源与普通片段/事件、边界对比标注。当前锁定评估已暴露，应保留作诊断，不能挪入训练或反复对它调参。下一轮尚未启动。

提交时只选candidate_SAFE_BEST_37_66.zip。SILVER24_SFT_REVIEW_AND_SAFE_BEST.zip是交接资料包，不是赛题提交格式。
'''
    with (OUT/'README.txt').open('x', encoding='utf-8', newline='\n') as f:
        f.write(text)
    members = sorted(p for p in OUT.rglob('*') if p.is_file())
    save(OUT/'SHA256SUMS.json', {str(p.relative_to(OUT)).replace('\\', '/'): {'bytes': p.stat().st_size, 'sha256': digest(p)} for p in members})
    members = sorted(p for p in OUT.rglob('*') if p.is_file())
    bundle = OUT/'SILVER24_SFT_REVIEW_AND_SAFE_BEST.zip'
    with zipfile.ZipFile(bundle, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for p in members:
            archive.write(p, str(p.relative_to(OUT)).replace('\\', '/'))
    with zipfile.ZipFile(bundle) as archive:
        assert archive.testzip() is None and len(archive.namelist()) == len(members)
        for p in members:
            assert archive.read(str(p.relative_to(OUT)).replace('\\', '/')) == p.read_bytes()
    save(OUT/'bundle_acceptance.json', {'status': 'PASS_ARCHIVE_CRC_AND_ALL_MEMBER_BYTES_EQUAL', 'path': str(bundle), 'bytes': bundle.stat().st_size, 'sha256': digest(bundle), 'members': len(members), 'submission_archive': False})
    print(json.dumps({'status': report['status'], 'submission_zip': str(target), 'bundle': str(bundle), 'locked_macro_gain': gain, 'failed_checks': failed, 'new_adapter_promoted': False}, ensure_ascii=False))


if __name__ == '__main__':
    main()
