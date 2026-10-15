"""Local review bundle, separate from the unchanged competition submission ZIP."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,zipfile
base=Path(__file__).resolve().parent
root=base/'slot6_silver24_v1'
discussion=base.parent/'round6_score_alignment/rematch_discussion/aic_video_empty407_20261010'
delivery=base.parent.parent/'deliveries/ANNOTATION_ITERATION_20261010'
decision=root/'pilot_final_adjudication_v1.json'
if not decision.exists():raise SystemExit('FINAL_ADJUDICATION_NOT_CREATED')
decision_data=json.loads(decision.read_text(encoding='utf-8'))
dest=delivery/'SLOT6_QUALITY_REVIEW';dest.mkdir(exist_ok=True)
paths=[decision,root/'source_window_plan.json',root/'frozen_protocol_v2_explicit_empty_gate.json',
       root/'pilot_execution_receipt_v1.json',root/'cpu_preparation_completion.json',
       root/'source_audio_presence_only.json',root/'blind_initial_geometry_acceptance_v1.json',
       root/'quality_contract.py',root/'silver_contract.py',root/'event_metrics.py']
jobs=json.loads((root/'observations/jobs.json').read_text())['jobs'][:4]
for folder in map(Path,jobs):
    attempt=folder/'teacher_attempt01_http1'
    paths += [folder/'manifest.json',folder/'student_views/receipt.json',
              attempt/'proposal.json',attempt/'audit.json',attempt/'terminal.json']
    correction=attempt/'main_metadata_correction_v1.json'
    if correction.exists():paths.append(correction)
paths += sorted((root/'blind_reviews/initial').glob('*.json'))
paths += sorted((root/'blind_reviews/initial').glob('*.md'))
paths += sorted(root.glob('main_factual*.md'))
paths += [discussion/'final-pilot-decision.md']
paths += [discussion/f'{s}-r03.md' for s in ('tibo','sol','grok','gemini')]
paths += [discussion/'gemini-r03-completion.md',discussion/'gemini-r03-input-status.json',
          discussion/'context-final-pilot-v1-receipt.json',discussion/'final-pilot-ui-receipt.json']
paths += [discussion/'context-final-pilot-v1.md',discussion/'context-final-pilot-v1-index.md']
paths += sorted(discussion.glob('*final-pilot-ack*.md'))
paths += [root/'actual_processor_binding.json',root/'student_views_cpu_receipt.json',
          root/'remaining_student_views_cpu_receipt.json',root/'observations/jobs.json']
paths=list(dict.fromkeys(paths))
inventory=[]
for p in paths:
    raw=p.read_bytes()
    name=('labels/'+str(p.relative_to(root)).replace('\\','/')) if p.is_relative_to(root) else ('discussion/'+p.name)
    inventory.append(dict(archive_path=name,source=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
readme='''# 标注质量复核包（不能直接用于训练或官网提交）

这是四窗真实Gemini提案、独立初审/学生有效视图审阅、实际工具用量及主控最终裁定的审计资料。
原始提案不是人工金标，存在的UNKNOWN不能改成负例。具体准入/拒收状态见pilot_final_adjudication_v1.json。
包内没有模型权重、视频、PNG、私有思维链或新训练数据完成声明。
公开答复/审阅者一致不能证明真实高光质量；源历史曝光、音频缺失、有限采样和补查暴露均保留。

比赛提交请使用另一个SAFE_37_66目录中的candidate_SAFE_37_66.zip，历史用户反馈37.66。
该比赛包未改写，本质量复核包绝不能上传到比赛预测接口。
'''
zip_path=dest/'SLOT6_annotation_quality_evidence.zip'
with zipfile.ZipFile(zip_path,'x',compression=zipfile.ZIP_DEFLATED) as z:
    z.writestr('README.md',readme)
    z.writestr('inventory.json',json.dumps(inventory,ensure_ascii=False,indent=2))
    for p,row in zip(paths,inventory):z.write(p,row['archive_path'])
with zipfile.ZipFile(zip_path) as z:
    assert z.testzip() is None
    assert len(z.namelist())==len(set(z.namelist()))
    for row in inventory:assert hashlib.sha256(z.read(row['archive_path'])).hexdigest()==row['sha256']
safe=delivery/'SAFE_37_66/candidate_SAFE_37_66.zip'
raw=safe.read_bytes();safe_sha=hashlib.sha256(raw).hexdigest()
assert len(raw)==306167 and safe_sha=='07730c9e02e68d1a1ce54e7ef5a8aa616346cf8f2f8d78426ed36bc3eb481496'
with zipfile.ZipFile(safe) as z:
    assert z.testzip() is None and z.namelist()==['predictions.jsonl']
    rows=[json.loads(line) for line in z.read('predictions.jsonl').splitlines()]
    assert len(rows)==426
receipt=dict(utc=datetime.now(timezone.utc).isoformat(),review_zip=str(zip_path),review_bytes=zip_path.stat().st_size,
             review_sha256=hashlib.sha256(zip_path.read_bytes()).hexdigest(),review_inventory_sha_roundtrip=True,
             review_not_training_ready=True,review_not_submission=True,pilot_status=decision_data['status'],
             submission_zip=str(safe),submission_bytes=len(raw),submission_sha256=safe_sha,
             submission_crc=True,submission_records=426,new_optimizer_updates=0,new_student_temporal_calls=0,
             official_score_source='HISTORICAL_USER_FEEDBACK_NOT_CURRENT_PORTAL_VERIFICATION')
(dest/'delivery_receipt.json').open('x',encoding='utf-8').write(json.dumps(receipt,ensure_ascii=False,indent=2))
print(json.dumps(receipt,ensure_ascii=False,indent=2))
