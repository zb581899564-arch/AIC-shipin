from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--run-dir", type=Path, required=True)
    args = ap.parse_args()
    root, run = args.root.resolve(), args.run_dir.resolve()
    selected = run / "pilot/gnmc/selected"
    for name in ["pilot_manifest.jsonl", "dev_manifest.jsonl", "sealed_holdout_manifest.jsonl", "conversion_records.jsonl", "manifest_validation.json"]:
        shutil.copy2(selected / name, run / name)
    inventory = json.loads((run / "existing_evidence_inventory.json").read_text(encoding="utf-8"))
    nonhold = inventory["official_training"]
    leakage = json.loads((run / "leakage_audit.json").read_text(encoding="utf-8"))
    dev = [json.loads(x) for x in (run / "dev_manifest.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    holdout = [json.loads(x) for x in (run / "sealed_holdout_manifest.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    accessed = datetime.now(timezone.utc).isoformat()
    candidates = [
        {
            "candidate": "GNMC 0.0.1", "publisher": "Aneesh Vartakavi / Gracenote", "status": "ELIGIBLE_PILOT",
            "evidence_tier": "TIER_B_PUBLIC_ANNOTATION_LIMITED", "exact_target_ratios": ["16:9"], "missing_target_ratios": ["9:16"],
            "annotation": "one crop per image/aspect ratio made by an experienced editor; no second annotator or review recorded",
            "source_binding": "image filename binds publisher-provided image bytes and normalized crop coordinates",
            "license": "PolyForm-Noncommercial-1.0.0", "media_origin": "publisher archive does not include per-image origin URLs",
            "usage_gate": "eligible only for local noncommercial diagnostic in P2-R; downstream competition training/submission and commercial use remain unapproved",
            "official_sources": ["https://zenodo.org/records/6228834", "https://github.com/aneeshvartakavi/GNMC"],
            "version": "Zenodo 0.0.1; Git commit 9d52ee02a6b2bb5b411e3e13b203decd249f4518", "accessed_utc": accessed,
            "download": {"bytes": 363946070, "md5": "0f2c3e47c8cd28af6a424d3e356b052b", "sha256": "2292aa403b447a0bb1130ab64633741956668ecc7c85c568869d42d12dd9b6a3"},
        },
        {
            "candidate": "LIVE-YT VC", "publisher": "UT Austin LIVE / paper authors", "status": "METADATA_ONLY",
            "evidence_tier": "NOT_ELIGIBLE_CURRENTLY", "exact_target_ratios": ["9:16"],
            "annotation": "30 sampled frames per video labeled by human subjects; paper reports 90 subjects and 30 ratings per video",
            "source_binding": "repository documents video filenames and frameN boxes; media sampled from LSVQ and YouTube-UGC",
            "license": "NOT_AVAILABLE in inspected official repository", "usage_gate": "downloadability from Box is not a license; media not downloaded",
            "official_sources": ["https://github.com/steven413d/LIVE-YT-VideoCropping", "https://arxiv.org/abs/2604.24947"],
            "version": "Git commit 2a91e9492c092c966b10fdc9b369b057d92e8ffb", "accessed_utc": accessed,
        },
        {
            "candidate": "GAICD", "publisher": "Hui Zeng et al.", "status": "METADATA_ONLY",
            "evidence_tier": "NOT_ELIGIBLE_CURRENTLY", "exact_target_ratios": ["16:9", "9:16"],
            "annotation": "candidate crops grouped around six aspect ratios and scored 1-5; each crop rated by seven experienced subjects",
            "source_binding": "publisher dataset link exists; paper says images were crawled from Flickr",
            "license": "NOT_AVAILABLE in inspected official repository", "usage_gate": "media and labels not downloaded because use boundary is unresolved",
            "official_sources": ["https://github.com/HuiZeng/Grid-Anchor-based-Image-Cropping", "https://arxiv.org/abs/1909.08989"],
            "version": "Git commit d3262a1bc840cd998cdff4bee0c712b4ad0787b7", "accessed_utc": accessed,
        },
        {
            "candidate": "RetargetVid", "publisher": "CERTH-ITI / paper authors", "status": "NOT_ELIGIBLE",
            "exact_target_ratios": ["1:3", "3:1"], "annotation": "dense per-frame crops from six human subjects",
            "license": "MIT for repository contents; underlying DHF1K media terms separate",
            "reason": "target ratios do not match 9:16 or 16:9; containment of a 1:3 crop is not target-ratio crop truth",
            "official_sources": ["https://github.com/bmezaris/RetargetVid"], "version": "Git commit 43673dd83b279c4aedeeea22f32d03582ac45194", "accessed_utc": accessed,
        },
        {
            "candidate": "Flickr Cropping Dataset / FLMS", "publisher": "Yi-Ling Chen et al.", "status": "NOT_ELIGIBLE",
            "annotation": "photography hobbyists drew crops; AMT preference validation; source images described as Flickr Creative Commons",
            "license": "per-image Flickr Creative Commons terms", "reason": "released crop windows are not fixed to exact 9:16 and 16:9; ratio conversion would create new semantics",
            "official_sources": ["https://yiling-chen.github.io/flickr-cropping-dataset/"], "accessed_utc": accessed,
        },
        {
            "candidate": "CUHK Image Cropping Dataset", "publisher": "CUHK / Chen Change Loy", "status": "NOT_ELIGIBLE",
            "annotation": "950 images, each cropped by three expert photographers", "license": "research purposes only",
            "reason": "target aspect ratios are not fixed to exact 9:16 and 16:9; automatic ratio conversion is forbidden",
            "official_sources": ["http://personal.ie.cuhk.edu.hk/~ccloy/downloads_cuhk_crop_dataset.html"], "accessed_utc": accessed,
        },
        {
            "candidate": "CPC", "publisher": "View Proposal Network paper authors", "status": "NOT_ELIGIBLE",
            "annotation": "algorithm-generated candidate views crowd-ranked at 1:1, 3:4, 4:3 and 16:9",
            "license": "NOT_AVAILABLE in inspected first-party material", "reason": "no 9:16 and no direct human-drawn target crop; unsuitable as two-ratio reference",
            "official_sources": ["https://openaccess.thecvf.com/content_cvpr_2018/html/Wei_View_Proposal_Network_CVPR_2018_paper.html"], "accessed_utc": accessed,
        },
        {
            "candidate": "MIR-Thumb", "publisher": "CropNet paper authors", "status": "UNKNOWN",
            "annotation": "paper reports crowd-sourced fixed-ratio thumbnail boxes including 16:9 and 9:16; aesthetics are not the stated goal",
            "license": "NOT_AVAILABLE", "reason": "no canonical publisher archive and terms were located in the bounded search; identity and usage cannot be frozen",
            "official_sources": ["https://doi.org/10.1145/3240508.3240517"], "accessed_utc": accessed,
        },
        {
            "candidate": "Carousel", "publisher": "Rafe Loya et al.", "status": "NOT_ELIGIBLE",
            "annotation": "human expert multi-target composition boxes with per-image source/license metadata",
            "license": "open non-commercial licenses recorded per image", "reason": "only 2:3 and 3:2 target ratios",
            "official_sources": ["https://github.com/RafeLoya/carousel"], "accessed_utc": accessed,
        },
    ]
    dump(run / "candidate_registry.json", {"schema": "p2r_candidate_registry_v1", "search_scope": "bounded primary-source search", "candidates": candidates})
    usage = {
        "schema": "p2r_source_and_usage_audit_v1", "accessed_utc": accessed,
        "conclusion": "Only GNMC passed a limited local-diagnostic gate, and only for 16:9. No 9:16 candidate passed both semantics and use-boundary gates.",
        "sources": [
            {"name": "AIC/QVHighlights-derived official share", "tier": "TIER_W_WEAK_TEACHER", "use": "existing local weak-supervision research only", "restriction": "no redistribution; no per-video license; no external service upload"},
            {"name": "P1b media", "tier": "NOT_ELIGIBLE_REFERENCE_UNANNOTATED", "use": "local interface tests", "restriction": "all 8 are unannotated; no semantic reference"},
            {"name": "GNMC", "tier": "TIER_B_PUBLIC_ANNOTATION_LIMITED", "use": "local noncommercial diagnostic only", "restriction": "PolyForm Noncommercial; no downstream competition/training/submission approval; no per-image origin URL"},
            {"name": "LIVE-YT VC", "tier": "NOT_ELIGIBLE_CURRENTLY", "use": "metadata audit only", "restriction": "no explicit license found"},
            {"name": "GAICD", "tier": "NOT_ELIGIBLE_CURRENTLY", "use": "metadata audit only", "restriction": "no explicit license found; Flickr origins not itemized in inspected material"},
        ],
    }
    dump(run / "source_and_usage_audit.json", usage)
    visual = {
        "schema": "p2r_visual_qa_v1", "reviewed_by": "execution agent", "review_scope": "box landing, declared ratio, and media identity only; no aesthetic preference judgment",
        "contact_sheet": str((selected / "dev_visual_contact.jpg").resolve()), "contact_sha256": sha256(selected / "dev_visual_contact.jpg"),
        "reviewed_items": [r["item_id"] for r in dev], "reviewed_count": len(dev), "pilot_count": len(dev) + len(holdout), "review_rate": len(dev) / (len(dev) + len(holdout)),
        "result": "PASS_BOX_LANDING_ONLY", "observations": ["4/4 dev crops are visibly inside their source image", "red overlays match a wide 16:9 window", "identity labels correspond to the dev manifest"],
        "not_verified": ["aesthetic optimality", "agreement with a second annotator", "sealed holdout visual content"],
    }
    dump(run / "visual_qa.json", visual)
    (run / "annotation_semantics.md").write_text(f"""# P2-R 标注语义\n\n## 现有 AIC 训练标签\n\n现有 987 行标签由 `api_doubao_doubao-seed-2-1-pro-260628` 生成，空间采样频率为 1 Hz，全部目标比例为 9:16。它们继续定级为 `TIER_W_WEAK_TEACHER`，不能称人工或官方真值。既有冻结报告记录 577 条可映射且带 ROI 的记录、8,369 个教师关键帧和 90,172 个逐帧 ROI；逐帧 ROI 不是独立人工判断。由于初版结构审计误解析了 64 条弱 holdout 的标签结构，最终重算先排除这些条目，只处理 {nonhold['usable_rows_with_roi']} 条非 holdout 带 ROI 记录，其中有 {nonhold['usable_keyframe_entries']:,} 个教师关键帧和 {nonhold['usable_roi_entries']:,} 个逐帧 ROI。\n\n## GNMC 试点\n\nGNMC 为每张图像提供经验编辑者针对固定比例直接选择的单个裁剪框。本轮只取原生 16:9 标注，不派生 9:16；原始 `[x1,y1,x2,y2]` 归一化坐标无损转换为源像素浮点 `[x,y,w,h]`。每个比例只有一名编辑者，没有第二复核者和多参考，因此定级为 `TIER_B_PUBLIC_ANNOTATION_LIMITED`。\n\n## 多参考与空值\n\nloader 支持 `reference_boxes` 多框；未来若一帧有多个可接受人工裁剪，全部保留，诊断分取预测与任一参考的最大 IoU。双方均空计 1，只有一方为空计 0。当前 GNMC 图像均有一个非空参考；该规则只由手算测试验证，不是 AIC 官方 evaluator。\n\n## 稀疏覆盖\n\n图像项标为 `coverage=single_image`。视频候选若只标少数帧必须标 `coverage=sparse`，未标帧不等于空真值，也不得插值。\n""", encoding="utf-8")
    (run / "reference_protocol.md").write_text("""# P2-R 参考协议\n\n状态：`INTERNAL_DIAGNOSTIC_REFERENCE_SPEC`，不是 AIC 官方 evaluator。\n\n1. 媒体以 SHA-256 固定，来源组跨开发/封存留出不得交叉。\n2. 目标比例必须原生存在；不得把其他比例的框伸缩成 9:16/16:9 真值。\n3. 规范框为源像素浮点 `[x,y,w,h]`，必须有限、正面积、在画幅内，并在两像素容差内满足目标比例。原始坐标原样保存在转换记录。\n4. 开发与封存留出分别使用独立清单。封存清单默认不得被模型排名脚本读取。\n5. 多参考保留全部框；单帧诊断取最大 IoU。双方均空计 1、单方空计 0。稀疏视频只评已标帧。\n6. 任何重复项/帧、NaN/Infinity、越界、错误比例、缺失媒体、哈希不符或来源跨 split 均使输入为 `INVALID_INPUT`，不得自动清洗。\n7. GNMC 试点仅授权本地非商业诊断；不得据此批准训练、比赛测试、打包或提交。\n""", encoding="utf-8")
    tests = {"status": "PASS", "command": "python -m unittest discover -s round6_score_alignment/p2r_reference_gate/tests -v", "tests_run": 25, "passed": 25, "failed": 0, "errors": 0, "coverage": ["double empty", "single empty", "multiple references", "sparse coverage", "duplicate item/frame", "NaN/Infinity/bool", "out of bounds", "wrong 16:9", "valid 9:16", "missing media", "hash mismatch", "source leakage", "invalid JSON"]}
    dump(run / "loader_test_results.json", tests)
    boundary_incident = {
        "schema": "p2r_boundary_incident_v1",
        "status": "RECORDED_AND_REMOVED_FROM_FINAL_RECOMPUTATION",
        "incident": "The initial superseded structural audit parsed label JSON for all 577 usable ROI rows, including the 64 weak-split holdout rows.",
        "exposure": "label structure only; no holdout media, model output, scoring, sample selection, or quality judgment",
        "remediation": "Final audit excludes holdout row indices before JSON parsing and removes them from all per-row and interpolation recomputation outputs.",
        "consequence": "This execution cannot claim that the 64-row weak holdout remained unopened; it must not use that split as a sealed holdout. The separate GNMC sealed manifest was not visually inspected or used for model judgment.",
    }
    dump(run / "boundary_incident.json", boundary_incident)
    evidence = {
        "schema": "p2r_evidence_index_v1", "status": "REFERENCE_GATE_PARTIAL",
        "facts": [
            {"claim": "Official training spatial labels are model-teacher 9:16 weak labels", "evidence": "existing_evidence_inventory.json", "level": "L1_LOCAL_BYTES"},
            {"claim": f"{nonhold['bracketed_roi_frames_linear_within_1px']:,} of {nonhold['bracketed_roi_frames']:,} bracketed non-holdout ROI frames match linear interpolation of 1 Hz key positions within 1 px", "evidence": "existing_evidence_inventory.json", "level": "L2_RECOMPUTED_STRUCTURE", "limitation": "64 weak holdout rows are excluded; consistency does not prove unpublished generator code"},
            {"claim": "P1b has four 16:9 and four 9:16 media, all UNANNOTATED", "evidence": "existing_evidence_inventory.json + round6_score_alignment/p1b/pilot_manifest.json", "level": "L1_LOCAL_BYTES"},
            {"claim": "GNMC archive is official Zenodo 0.0.1 and matches publisher MD5", "evidence": "snapshots/gnmc_zenodo_record.json + pilot/gnmc/GNMC.zip", "level": "L1_PUBLISHER_AND_BYTES"},
            {"claim": "GNMC partial pilot contains four dev and four sealed 16:9 file-unique image items", "evidence": "pilot_manifest.jsonl + manifest_validation.json", "level": "L2_RECOMPUTED", "limitation": "source independence beyond publisher filename is UNKNOWN"},
            {"claim": "No near duplicate was found in 768 pHash comparisons against 96 frames from eight AIC non-test groups", "evidence": "leakage_audit.json", "level": "L3_BOUNDED", "limitation": "full source leakage remains UNKNOWN"},
            {"claim": "No eligible 9:16 public candidate passed both semantics and use-boundary gates", "evidence": "candidate_registry.json + source_and_usage_audit.json", "level": "L2_PRIMARY_SOURCE_AUDIT"},
            {"claim": "Initial superseded audit parsed 64 weak-holdout label payloads; final recomputation excludes them", "evidence": "boundary_incident.json", "level": "L1_EXECUTION_RECORD"},
        ],
    }
    dump(run / "evidence_index.json", evidence)
    report = f"""# P2-R 可信非测试构图参考门\n\n**唯一状态：`REFERENCE_GATE_PARTIAL`。** 本轮完成现有证据清算、一手来源候选审计、一个受限 16:9 外部参考试点、严格 loader/评分边界测试、有限泄漏检查和视觉落框检查。9:16 独立参考仍未通过使用边界与语义门，因此不满足 `PASS_PILOT` 的双比例、16 来源要求。未使用 GPU、未训练/推理、未打开 64 条弱 holdout、未读取比赛测试视频、未生成候选或提交。\n\n## 四个问题的回答\n\n### 1. 官方 9:16 标签能支持什么\n\n它们只能作为 `TIER_W_WEAK_TEACHER`。987 行均由教师模型生成；全量有 9,041 个 `crop_keyframes` 和 98,242 个逐帧 `cropRois`。在 577 条可映射且带 ROI 的记录中，本轮重算得到 8,369 个教师关键帧、90,172 个逐帧 ROI。90,166 个可由相邻关键帧夹住的 ROI 中，89,184 个（{inventory['official_training']['linear_consistency_rate']:.2%}）与 1 Hz 关键位置的线性插值在 1 像素内一致，且有 71,058 次相邻框完全重复。它强烈支持“逐帧 ROI 主要是稀疏教师轨迹的复制/插值产物”，但没有发布的生成代码，故不把统计一致性写成实现事实。36 帧既有可视抽样只证明部分媒体映射可用，不升格构图真值。\n\n### 2. 项目内是否已有可信 16:9 参考\n\n没有。P1b 有 4 条 16:9 与 4 条 9:16 非测试媒体，但 8/8 均为 `UNANNOTATED`，annotator/reviewer 都不存在，只能做接口检查。它们的底层 YouTube 媒体也没有逐视频许可证。\n\n### 3. 公开数据是否提供可用参考\n\nGNMC 0.0.1 通过了**受限**试点门：官方 Zenodo 归档 363,946,070 字节，本地 MD5 与发布记录 `0f2c3e47c8cd28af6a424d3e356b052b` 一致；经验编辑者为每张图像提供固定比例裁剪，16:9 可直接使用。限制是每比例单编辑者、无独立复核、无每图来源 URL，并采用 PolyForm Noncommercial；所以只批准 P2-R 本地非商业诊断，不能自动扩展到竞赛训练/提交。\n\nLIVE-YT VC 有人类 9:16 视频框，GAICD 同时包含 16:9/9:16 的人类评分候选，但二者官方仓库均未发现明确数据许可证；“公开下载”不等于许可，故只登记 `METADATA_ONLY`，没有下载媒体。RetargetVid、FLMS、CUHK、CPC、Carousel 因比例或标注语义不匹配被排除；MIR-Thumb 的规范下载与条款仍为 `UNKNOWN`。\n\n### 4. 是否能冻结双比例试点\n\n不能。已冻结 GNMC 16:9 的 8 个独立图像来源：4 个 dev、4 个 `sealed_holdout`，全部媒体 SHA、坐标转换和格式检查通过。9:16 合格来源为 0，故总量只有 8/16，比例只覆盖一侧。封存清单由脚本生成但未用于模型判断。\n\n## 试点验收\n\n- 严格 loader/诊断边界：25/25 通过，覆盖双空/单空、多参考、稀疏、重复帧、NaN/Infinity/bool、越界、错误比例、缺媒体、哈希不符与 split 泄漏。\n- 视觉落框：4/8（50%，全部 dev）接触图已实际查看，4/4 红框在源图内且呈 16:9；只验证落地/身份/比例，不评价构图美感，sealed holdout 未视觉打开。\n- 泄漏：GNMC 数字 ID 与 AIC `video_id/youtube_id` 无交集；8 张图与 P1b 8 个非测试来源的 96 帧完成 768 次 pHash 比较，阈值 6 下 0 匹配。GNMC 不提供原图 URL，且未全盘解码 AIC 语料，所以完整来源泄漏为 `UNKNOWN`，不能宣称全局隔离。\n- 同帧历史模型输出：不存在；按协议没有启动推理，也没有模型排名或质量分。\n\n## 产物\n\n- `candidate_registry.json`：9 个候选及资格结论。\n- `source_and_usage_audit.json`：使用边界和限制。\n- `existing_evidence_inventory.json`：官方弱标签/P1b 证据矩阵及逐行结构统计。\n- `pilot_manifest.jsonl`、`dev_manifest.jsonl`、`sealed_holdout_manifest.jsonl`、`conversion_records.jsonl`：受限 GNMC 16:9 试点。\n- `reference_protocol.md`、`annotation_semantics.md`、`loader_test_results.json`、`leakage_audit.json`、`visual_qa.json`。\n\n## 停止与交接\n\n`REFERENCE_GATE_PARTIAL` 不批准下一阶段模型对照，也不批准 GPU、训练、弱 holdout、比赛测试、打包或提交。总控可选择：取得 LIVE-YT VC/GAICD 的明确使用授权后补齐 9:16；或另找带明确许可证、媒体身份和原生 9:16 人工裁剪的第一方数据。不得把现有 9:16 弱教师框或执行Agent自画框填入独立参考。\n"""
    report = report.replace(
        "未使用 GPU、未训练/推理、未打开 64 条弱 holdout、未读取比赛测试视频、未生成候选或提交。",
        "未使用 GPU、未训练/推理、未读取比赛测试视频、未生成候选或提交。初版结构脚本越界解析了 64 条弱 holdout 的标签结构；未打开媒体、未评分或用于选样，最终重算已排除，但本执行轮不得再称该弱 holdout 保持封存，详见 `boundary_incident.json`。",
    )
    report = report.replace(
        "在 577 条可映射且带 ROI 的记录中，本轮重算得到 8,369 个教师关键帧、90,172 个逐帧 ROI。90,166 个可由相邻关键帧夹住的 ROI 中，89,184 个（98.91%）与 1 Hz 关键位置的线性插值在 1 像素内一致，且有 71,058 次相邻框完全重复。",
        f"既有冻结报告记录 577 条可映射带 ROI、8,369 个教师关键帧和 90,172 个逐帧 ROI。最终重算先排除 64 条弱 holdout，只处理 {nonhold['usable_rows_with_roi']} 条非 holdout 带 ROI 记录：{nonhold['bracketed_roi_frames']:,} 个可由相邻关键帧夹住的 ROI 中，{nonhold['bracketed_roi_frames_linear_within_1px']:,} 个（{nonhold['linear_consistency_rate']:.2%}）与 1 Hz 关键位置线性插值在 1 像素内一致，且有 {nonhold['adjacent_exact_box_repeats']:,} 次相邻框完全重复。",
    )
    stats_start = "在 577 条可映射且带 ROI 的记录中，本轮重算得到"
    stats_end = "36 帧既有可视抽样只证明部分媒体映射可用，不升格构图真值。"
    if stats_start in report:
        start_index = report.index(stats_start)
        end_index = report.index(stats_end, start_index) + len(stats_end)
        corrected_stats = (
            "既有冻结报告记录 577 条可映射带 ROI、8,369 个教师关键帧和 90,172 个逐帧 ROI。"
            f"最终重算先排除 64 条弱 holdout，只处理 {nonhold['usable_rows_with_roi']} 条非 holdout 带 ROI 记录："
            f"{nonhold['bracketed_roi_frames']:,} 个可由相邻关键帧夹住的 ROI 中，"
            f"{nonhold['bracketed_roi_frames_linear_within_1px']:,} 个（{nonhold['linear_consistency_rate']:.2%}）"
            f"与 1 Hz 关键位置线性插值在 1 像素内一致，且有 {nonhold['adjacent_exact_box_repeats']:,} 次相邻框完全重复。"
            "这强烈支持“逐帧 ROI 主要是稀疏教师轨迹的复制/插值产物”，但没有发布的生成代码，"
            "故不把统计一致性写成实现事实。36 帧既有可视抽样只证明部分媒体映射可用，不升格构图真值。"
        )
        report = report[:start_index] + corrected_stats + report[end_index:]
    report = report.replace(
        "已冻结 GNMC 16:9 的 8 个独立图像来源",
        "已冻结 GNMC 16:9 的 8 个文件级唯一图像项；因无逐图原始 URL，文件层面以外的来源独立性为 `UNKNOWN`",
    )
    report_root = run.as_posix()
    links = (
        f"报告根目录：`{report_root}`。主要交付："
        f"[候选登记]({report_root}/candidate_registry.json)、"
        f"[使用边界审计]({report_root}/source_and_usage_audit.json)、"
        f"[现有证据清单]({report_root}/existing_evidence_inventory.json)、"
        f"[参考协议]({report_root}/reference_protocol.md)、"
        f"[最终冻结]({report_root}/final_freeze.json)。"
    )
    report = report.replace("\n\n## 四个问题的回答", f"\n\n{links}\n\n## 四个问题的回答", 1)
    (run / "REPORT.md").write_text(report, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
