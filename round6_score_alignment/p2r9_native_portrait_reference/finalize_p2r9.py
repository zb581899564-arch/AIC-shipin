from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "round6_p2r9_20260920T040552Z"
FINAL_STATUS = "P2R9_PERMISSION_REQUIRED"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def local_link(path: Path) -> str:
    return path.resolve().as_posix()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    run = args.run_dir.resolve()
    snapshots = run / "snapshots"
    code = root / "round6_score_alignment/p2r9_native_portrait_reference"
    now = datetime.now(timezone.utc).isoformat()

    candidates = [
        {
            "candidate_id": "LIVE_YT_VC",
            "priority": 1,
            "publisher": "LIVE / University of Texas at Austin authors with Google collaborators",
            "version": "repository commit 2a91e9492c092c966b10fdc9b369b057d92e8ffb; arXiv:2604.24947v1",
            "official_urls": [
                "https://github.com/steven413d/LIVE-YT-VideoCropping",
                "https://arxiv.org/abs/2604.24947",
                "https://utexas.app.box.com/s/hylumfu8akjhdgdd4teynsyc6ickwv1j/folder/407721578256",
            ],
            "qualification_status": "PERMISSION_REQUIRED",
            "native_9_16": "PASS_ON_PRIMARY_DOCUMENTATION",
            "human_composition": "PASS_FOR_ORIGINAL_SPARSE_LABELS_ONLY",
            "byte_bound_identity": "APPARENT_PASS_NOT_BYTE_VERIFIED: README binds video filename to frameN dictionaries; no candidate media or CSV was downloaded",
            "use_boundary": "FAIL_PENDING_WRITTEN_PERMISSION: repository has no LICENSE/data card/releases; Box page supplies access but no dataset-specific license",
            "source_groupable": "PASS_BY_ORIGINAL_VIDEO_FILENAME",
            "aic_overlap": "UNKNOWN_BEYOND_METADATA; no candidate media or index was opened for fingerprinting",
            "annotation_detail": "1800 six-second videos; original study samples 30 frames per video and each sampled frame is labeled by one human; 90 subjects total; 9:16; post-filtered VC++ is not treated as direct human ground truth",
            "underlying_media": "YouTube-UGC official page states CC BY 4.0; LSVQ official page grants broad use/copy/modify/distribute with notice. The LIVE-YT derived clip/annotation package still needs its own written boundary and per-item attribution mapping.",
            "download_state": "STOPPED_BEFORE_LABEL_OR_MEDIA_DOWNLOAD",
            "evidence_snapshots": ["live_yt_readme.md", "live_yt_repo.json", "live_yt_contents.json", "live_yt_releases.json", "live_yt_box_page.md", "live_yt_arxiv_2604.24947.pdf", "youtube_ugc_official.md", "lsvq_official.md"],
        },
        {
            "candidate_id": "GAICD",
            "priority": 2,
            "publisher": "Hui Zeng et al.",
            "version": "repository commit d3262a1bc840cd998cdff4bee0c712b4ad0787b7; arXiv:1909.08989",
            "official_urls": ["https://github.com/HuiZeng/Grid-Anchor-based-Image-Cropping", "https://arxiv.org/abs/1909.08989"],
            "qualification_status": "METADATA_ONLY",
            "native_9_16": "PRESENT_AS_GRID_ANCHOR_RATIO",
            "human_composition": "LIMITED: algorithmically enumerated grid crops scored 1-5 by seven experienced subjects; must remain a scored multi-candidate set, not a unique hand-drawn crop",
            "byte_bound_identity": "DATASET_INTERNAL_BINDING_DESCRIBED; original Flickr IDs/URLs and per-image licenses are not preserved in the reviewed first-party release evidence",
            "use_boundary": "NOT_AVAILABLE: repository license is null and no data/annotation/media terms were found",
            "source_groupable": "ONE_IMAGE_ONE_GROUP_WITHIN_RELEASE; upstream publisher/source grouping unavailable",
            "aic_overlap": "UNKNOWN; no eligible media download",
            "download_state": "STOPPED_BEFORE_DATASET_DOWNLOAD",
            "evidence_snapshots": ["gaicd_readme.md", "gaicd_repo.json", "gaicd_tree.json", "gaicd_arxiv.xml"],
        },
        {
            "candidate_id": "MIR_THUMB",
            "priority": 3,
            "publisher": "CropNet paper authors / ACM",
            "version": "DOI 10.1145/3240508.3240517",
            "official_urls": ["https://doi.org/10.1145/3240508.3240517"],
            "qualification_status": "METADATA_ONLY",
            "native_9_16": "REPORTED_BY_LATER_PAPER_BUT_NOT_VERIFIED_IN_FIRST_PARTY_ARCHIVE",
            "human_composition": "CROWD_THUMBNAIL_ANNOTATION_REPORTED; composition/aesthetics scope limited",
            "byte_bound_identity": "NOT_AVAILABLE",
            "use_boundary": "NOT_AVAILABLE",
            "source_groupable": "UNKNOWN",
            "aic_overlap": "NOT_COMPUTABLE",
            "download_state": "NO_FIRST_PARTY_ARCHIVE_FOUND",
            "evidence_snapshots": ["mir_thumb_cropnet_crossref.json", "mir_thumb_cropnet_acm.md"],
        },
        {
            "candidate_id": "GENCROP_PORTRAIT1K",
            "priority": 4,
            "publisher": "GenCrop paper authors",
            "version": "repository commit 763da99334ec8c2ec10466af538d81878b7c7a2f; arXiv:2312.12080",
            "official_urls": ["https://github.com/jhong93/gencrop", "https://arxiv.org/abs/2312.12080"],
            "qualification_status": "NOT_ELIGIBLE",
            "native_9_16": "FAIL: aggregate audit of the official 1000-image portrait evaluation index found 0 exact 9:16 among 2260 crop_xywh boxes",
            "human_composition": "PASS: one photography-domain expert, average 2.3 acceptable crops per image",
            "byte_bound_identity": "HASHED Unsplash image IDs; media requires Unsplash dataset access",
            "use_boundary": "Code BSD-3; annotation-specific license not stated; Unsplash media has separate terms/access",
            "source_groupable": "ONE_UNSPLASH_IMAGE_ONE_GROUP",
            "aic_overlap": "NOT_RUN_BECAUSE_RATIO_GATE_FAILED",
            "download_state": "ONLY_2.0_MIB_OFFICIAL_COMPRESSED_ANNOTATION_INDEX_DOWNLOADED; NO_MEDIA",
            "aggregate_audit": {"images": 1000, "crop_boxes": 2260, "exact_9_16_boxes": 0},
            "evidence_snapshots": ["gencrop_readme.md", "gencrop_license.md", "gencrop_arxiv.xml", "gencrop_portrait_testeval_sha256.json.gz", "unsplash_license.md", "unsplash_data.md"],
        },
        {
            "candidate_id": "UGCROP5K",
            "priority": 5,
            "publisher": "S2CNet paper authors",
            "version": "repository commit 6c92712c85e73c2c22b7cbcb17338485b0dc56dd; arXiv:2401.08086",
            "official_urls": ["https://github.com/suyukun666/S2CNet", "https://arxiv.org/abs/2401.08086"],
            "qualification_status": "METADATA_ONLY",
            "native_9_16": "NOT_AVAILABLE_IN_RELEASE EVIDENCE",
            "human_composition": "algorithmically predefined anchors scored by at least five of 20 annotators; not direct-drawn crops",
            "byte_bound_identity": "DATASET NOT RELEASED IN REVIEWED REPOSITORY",
            "use_boundary": "NOT_AVAILABLE; repository has no license",
            "source_groupable": "UNKNOWN",
            "aic_overlap": "NOT_COMPUTABLE",
            "download_state": "NO_DATASET_MEDIA_OR_ANNOTATIONS AVAILABLE",
            "evidence_snapshots": ["s2cnet_readme.md", "s2cnet_repo.json", "s2cnet_arxiv.xml"],
        },
        {
            "candidate_id": "H2V_142K",
            "priority": 6,
            "publisher": "Horizontal-to-Vertical Video Conversion paper authors",
            "version": "arXiv:2101.04051",
            "official_urls": ["https://arxiv.org/abs/2101.04051"],
            "qualification_status": "NOT_ELIGIBLE",
            "native_9_16": "GEOMETRIC_9_16_PRESENT",
            "human_composition": "FAIL: humans label primary face/torso subject boxes; the 9:16 crop is a maximum rectangle mechanically centered on the subject box",
            "byte_bound_identity": "NOT_REVIEWED_AFTER_SEMANTIC_GATE_FAILURE",
            "use_boundary": "NOT_REVIEWED_AFTER_SEMANTIC_GATE_FAILURE",
            "source_groupable": "VIDEO_ID IN PAPER",
            "aic_overlap": "NOT_RUN_BECAUSE_SEMANTIC_GATE_FAILED",
            "download_state": "NO_DOWNLOAD",
            "evidence_snapshots": ["h2v_arxiv.xml"],
        },
    ]
    write_json(run / "targeted_candidate_registry.json", {
        "schema": "p2r9_targeted_candidate_registry_v1",
        "run_id": RUN_ID,
        "created_utc": now,
        "search_order_preserved": True,
        "bounded_search_closed": True,
        "candidates": candidates,
        "counts": {
            "ELIGIBLE_DEV_PILOT": 0,
            "ELIGIBLE_PROCESS_SEALED_PILOT": 0,
            "PERMISSION_REQUIRED": 1,
            "METADATA_ONLY": 3,
            "NOT_ELIGIBLE": 2,
            "UNKNOWN": 0,
        },
    })

    license_rows = [
        {
            "candidate_id": c["candidate_id"],
            "qualification_status": c["qualification_status"],
            "data_terms": c["use_boundary"],
            "annotation_terms": "NOT_AVAILABLE" if c["candidate_id"] in {"LIVE_YT_VC", "GAICD", "MIR_THUMB", "UGCROP5K"} else c["use_boundary"],
            "underlying_media_terms": c.get("underlying_media", c["use_boundary"]),
            "local_noncommercial_diagnostic": "NOT_AUTHORIZED" if c["qualification_status"] in {"PERMISSION_REQUIRED", "METADATA_ONLY"} else "INELIGIBLE_BY_NONLICENSE_GATE",
            "training": "NOT_AUTHORIZED",
            "competition_submission": "NOT_AUTHORIZED",
            "code_license_not_substituted": True,
            "evidence_snapshots": c["evidence_snapshots"],
        }
        for c in candidates
    ]
    write_json(run / "license_evidence_matrix.json", {
        "schema": "p2r9_license_evidence_matrix_v1",
        "created_utc": now,
        "rows": license_rows,
    })

    semantic_rows = [
        {
            "candidate_id": c["candidate_id"],
            "native_9_16": c["native_9_16"],
            "human_semantics": c["human_composition"],
            "media_binding": c["byte_bound_identity"],
            "source_grouping": c["source_groupable"],
            "multi_reference_policy": (
                "retain original sparse human boxes by sampled frame; do not use VC++ smoothing as direct-human truth"
                if c["candidate_id"] == "LIVE_YT_VC" else
                "retain every grid candidate and human score; do not collapse to a fabricated unique ground truth"
                if c["candidate_id"] == "GAICD" else
                "retain every expert crop; no exact 9:16 item exists"
                if c["candidate_id"] == "GENCROP_PORTRAIT1K" else
                "NOT_APPLICABLE_OR_NOT_VERIFIED"
            ),
            "iou_diagnostic_support": (
                "TECHNICALLY_SUPPORTED_FOR_ORIGINAL_SPARSE_LABELS_AFTER_PERMISSION_AND_BYTE_VERIFICATION"
                if c["candidate_id"] == "LIVE_YT_VC" else
                "ONLY_AS_SCORE_AWARE_MULTI_CANDIDATE_DIAGNOSTIC_AFTER LICENSE/IDENTITY RESOLUTION"
                if c["candidate_id"] == "GAICD" else
                "NO"
            ),
            "qualification_status": c["qualification_status"],
        }
        for c in candidates
    ]
    write_json(run / "annotation_semantics_matrix.json", {
        "schema": "p2r9_annotation_semantics_matrix_v1",
        "created_utc": now,
        "rows": semantic_rows,
    })

    write_json(run / "qualification_decision.json", {
        "schema": "p2r9_qualification_decision_v1",
        "run_id": RUN_ID,
        "status": FINAL_STATUS,
        "eligible_dev_pilot_candidates": [],
        "eligible_process_sealed_pilot_candidates": [],
        "permission_required_candidate": "LIVE_YT_VC",
        "decision": "LIVE-YT original sparse labels are technically aligned but the derived dataset/annotation package lacks explicit first-party reuse terms. No label or media download is allowed before written permission.",
        "bounded_search_closed": True,
        "no_real_holdout_created": True,
    })

    permission_draft = f"""# LIVE-YT VC 使用边界询问稿（未发送）

状态：`DRAFT_ONLY_NOT_SENT`。本文件不构成授权，也未通过邮件、issue、表单或私信发送。

## 拟询问对象与公开来源

- 对象：Cheng-Han Lee 及 LIVE-YT VC 作者/维护者团队。
- 公开来源：论文作者列表 `arXiv:2604.24947v1`，以及第一方仓库 <https://github.com/steven413d/LIVE-YT-VideoCropping>（维护账户 `steven413d`）。
- 如用户后续明确授权联系，应由用户选择实际渠道；本轮不代发。

## English draft

Subject: Permission clarification for limited local research evaluation using LIVE-YT VC

Dear LIVE-YT VC authors and maintainers,

We are conducting a local, non-commercial research evaluation for a video highlight and reframing competition project. We would like to use a strictly limited subset of the original LIVE-YT VC data only as an offline diagnostic reference. At this stage we would use at least eight source videos, keep source videos as independent groups, and evaluate only the original sparse human 9:16 annotations. We would not redistribute the videos or labels, upload them to an external API, or include them in a submission package.

Could you please confirm each of the following separately?

1. May we download and locally retain the LIVE-YT VC `study_videos` and `video_bbox_labels.csv` for non-commercial research evaluation in a competition-related project?
2. Does that permission cover both the dataset's derived six-second video clips and the original sparse human bounding-box annotations, rather than only the repository code?
3. Are the selected study videos individually traceable to YouTube-UGC or LSVQ, with the attribution or notice required by the underlying source included in the release? If so, where is that per-video mapping recorded?
4. May we compute and privately retain aggregate IoU-style diagnostic results and hashes without publishing per-video labels or coordinates?
5. Is model training or fine-tuning on these videos/annotations permitted? We will treat this as **not permitted** unless you explicitly answer yes.
6. Is using a model evaluated or trained with this dataset in a competition submission permitted? We will treat this as **not permitted** unless you explicitly answer yes.
7. May a trained model or other non-reconstructive derivative be published? We will treat this as **not permitted** unless you explicitly answer yes.
8. What citation, copyright notice, attribution, deletion/update obligation, or redistribution restriction must we follow?
9. Do the same terms apply to LIVE-YT VC++? We currently intend to treat VC++ as post-processed labels, not direct human ground truth.

If helpful, we can limit the request to evaluation-only use of eight videos and the original sparse labels, with no training, redistribution, public release, or competition packaging.

Sincerely,
[Name / affiliation to be supplied by the user]
"""
    (run / "permission_request_draft.md").write_text(permission_draft, encoding="utf-8")

    protocol = f"""# P2-R9 `PROCESS_SEALED` 聚合评分协议

## 当前可用性

入口代码已实现并通过纯合成测试，但**没有绑定真实候选**。当前状态为 `SYNTHETIC_PROTOCOL_ONLY / REAL_HOLDOUT_NOT_BOUND`，原因是没有候选通过书面资格门。它不是密码学盲测，也不是操作系统权限隔离；共享工作区无法证明执行Agent绝对不能读取底层文件。

## 文件分离

- 公开 commitment 只允许数据集版本、项目 ID、来源组、媒体 SHA-256、目标比例、固定选样规则/种子、标签文件 SHA-256、项目数、评测代码哈希和保护注册表哈希。
- 私有参考文件由评分入口内部读取；真实绑定时不得复制到普通报告、普通 manifest、接触图或 stdout。
- 预测文件包含同一项目/来源组/媒体哈希/比例、`OK|FAILED` 状态和预测框。失败项必须空框，并以 0 分留在分母。
- `holdout_access_log.jsonl` 只追加调用时间、执行者、代码/预测/commitment 哈希、聚合是否生成及错误码，不记录项目 ID、框或逐项分数。

## 坐标与评分

- 框格式为源像素浮点 `[x,y,w,h]`，四个值必须有限、非 bool、面积为正、在源图边界内，并以 `1e-6` 容差满足目标比例。
- 空参考与空预测计 1；只有一方为空计 0。
- 多参考保留全部标注，单帧得分取预测框与全部可接受参考中的最大 IoU；不得按模型结果预先选择参考。
- 稀疏标签只评发布者标注的稀疏帧，不插值。
- 先按项目计算，再给项目宏均值；同一来源组内先平均，再对来源组做宏平均。失败项保持在各自来源组和总体分母。

## 硬拒绝

缺失/多余/重复项目、非法 JSON、NaN/Infinity/bool、越界、错误比例、媒体哈希不符、来源跨 split、评测代码哈希变化、原始标签哈希变化、保护注册表哈希变化、公开 commitment 含坐标/轨迹/逐项分数，以及 64 条弱 holdout、4 条 GNMC exposed sealed 或旧 88 条历史 holdout 的任何命中都拒绝运行。异常只输出稳定错误码，不输出参考 payload 或栈。

## 入口

`{local_link(code / 'evaluate_process_sealed.py')}`

真实数据只有在总控确认候选为 `ELIGIBLE_PROCESS_SEALED_PILOT` 后才能生成 `BOUND` commitment。本轮的模板故意为 `NOT_BOUND_NO_ELIGIBLE_CANDIDATE`，因此入口会拒绝真实运行。
"""
    (run / "process_sealed_protocol.md").write_text(protocol, encoding="utf-8")

    registry_path = run / "protected_input_registry.json"
    commitment_template = {
        "schema": "p2r9_holdout_commitment_v1",
        "status": "NOT_BOUND_NO_ELIGIBLE_CANDIDATE",
        "dataset_version": "NOT_AVAILABLE",
        "source_dataset_sha256": "NOT_AVAILABLE",
        "selection_rule": "NOT_RUN_BECAUSE_QUALIFICATION_GATE_FAILED",
        "selection_seed": 20260920,
        "item_count": 0,
        "items": [],
        "dev_source_group_sha256": [],
        "reference_labels_sha256": "NOT_AVAILABLE",
        "evaluator_sha256": sha256_file(code / "evaluate_process_sealed.py"),
        "engine_sha256": sha256_file(code / "sealed_evaluator.py"),
        "protected_registry_sha256": sha256_file(registry_path),
        "note": "template only; contains no real holdout and is intentionally rejected by the evaluator",
    }
    write_json(run / "holdout_commitment_template.json", commitment_template)
    (run / "holdout_access_log.jsonl").touch(exist_ok=True)

    write_json(run / "pilot_decision.json", {
        "schema": "p2r9_pilot_decision_v1",
        "qualification_gate_passed": False,
        "real_dev_manifest_created": False,
        "real_process_sealed_holdout_created": False,
        "candidate_label_files_downloaded": 0,
        "candidate_media_files_downloaded": 0,
        "reason": "LIVE-YT data/annotation package permission is not explicit; all other candidates fail ratio, semantic, identity, release, or permission gates.",
    })

    snapshot_index = json.loads((run / "source_snapshot_index.json").read_text(encoding="utf-8"))
    snapshot_bytes = sum(row.get("bytes", 0) for row in snapshot_index["snapshots"] if row["status"].startswith("CAPTURED"))
    write_json(run / "resource_usage.json", {
        "schema": "p2r9_resource_usage_v1",
        "created_utc": now,
        "gpu_seconds": 0,
        "models_loaded": 0,
        "training_runs": 0,
        "inference_runs": 0,
        "competition_test_media_opened": 0,
        "weak_holdout_reference_payloads_parsed_for_quality": 0,
        "gnmc_exposed_reference_payloads_parsed_for_scoring": 0,
        "candidate_media_download_bytes": 0,
        "candidate_label_download_bytes": 2047240,
        "source_snapshot_bytes": snapshot_bytes,
        "largest_candidate_metadata_download_bytes": max(row.get("bytes", 0) for row in snapshot_index["snapshots"]),
        "metadata_per_candidate_limit_bytes": 100 * 1024 * 1024,
        "total_new_disk_limit_bytes": 3 * 1024**3,
        "single_media_limit_bytes": 500 * 1024**2,
        "cpu_heavy_wall_seconds": 0.9,
        "cpu_heavy_limit_seconds": 90 * 60,
        "ssh_used": False,
        "external_messages_sent": 0,
        "packages_or_uploads_created": 0,
        "limits_respected": True,
        "note": "Network research and light hashing are not counted as CPU-heavy work. The 33.4 MB arXiv PDF and 2.0 MB compressed Portrait1K annotation index are metadata/evidence snapshots, not candidate media.",
    })

    report = f"""# P2-R9 原生 9:16 参考与流程封存门报告

**唯一最终状态：`{FINAL_STATUS}`。**

有界一手来源检索已结束，不再扩展候选清单。LIVE-YT VC 的原始稀疏标签在比例、人工构图语义和文件/帧绑定设计上是唯一技术上接近合格的首选；YouTube-UGC 与 LSVQ 的底层媒体各有第一方使用声明，但 LIVE-YT 派生的六秒视频和标注包本身没有 LICENSE、数据卡或明确研究/竞赛使用条款。因此本轮在下载真实标签或媒体前停止，并生成未发送的精确询问稿。其余候选没有通过比例、人工语义、第一方归档、媒体身份或许可门。

## 五个问题的闭环答案

1. **LIVE-YT / GAICD / MIR-Thumb 的遗漏证据。** LIVE-YT 仓库在固定 commit 下只有 README、无 release、无 LICENSE；但底层 YouTube-UGC 明示 CC BY 4.0，LSVQ 明示可使用/复制/修改/分发并要求完整通知与引用。这补全了底层媒体边界，却不能替代 LIVE-YT 派生包许可。GAICD 仍无仓库许可证，且 Flickr 原图逐项 ID/URL/许可未在审计证据中保留。MIR-Thumb 仍未找到第一方数据归档、版本或许可。
2. **其他公开原生 9:16 人工参考。** 未找到可落地的新来源。Portrait1K 是真实专家裁剪，但官方 1000 图索引的 2260 个框中精确 9:16 为 0；H2V 的 9:16 是围绕人工主体框机械生成；UGCrop5K 是算法网格候选后人工评分且数据未在官方仓库发布。
3. **8 个来源组试点。** 未执行。没有候选通过书面资格门，因而没有下载真实媒体/标签、没有建立 4 dev + 4 process-sealed，也没有用同源复制凑数。
4. **`PROCESS_SEALED` 入口。** 代码和纯合成门禁已经实现，30 项测试覆盖不泄漏、严格格式、多参考、稀疏、空值、宏平均、失败留在分母、哈希锁定、来源隔离和三类保护输入拒绝。真实 commitment 故意保持 `NOT_BOUND`；这只是流程封存，不是密码学盲测。
5. **路线切换。** 公开空间参考的继续搜索正式停止。最小外部动作只有一次明确的 LIVE-YT 书面许可确认；在许可到来前不再下载或扩展空间参考。若用户不授权联系或许可未获得，建议总控冻结当前未微调 Qwen 空间基线，另行制定 P2-T 高光时间误差、端点与召回路线；本轮没有启动 P2-T。

## 事实

- 保护注册表封禁 64 条弱 holdout、4 条 GNMC exposed sealed，以及旧 88 条历史 holdout 的固定数据集哈希/来源命名空间；未读取这些材料的参考框做评分或选样。
- 输入和工作区在在线候选检索前冻结；固定搜索优先级和停止条件未因下载便利调整。
- 一手证据快照 24/24 成功。只有网页、论文、仓库元数据和 2.0 MiB 的 Portrait1K 压缩标注索引；候选媒体下载为 0。
- GPU、模型加载、训练、推理、比赛测试视频读取、外发消息、打包和上传均为 0。
- 评测入口正常 stdout 只含聚合值和哈希；拒绝路径只含稳定错误码。测试使用的坐标完全是运行时临时合成数据，不是候选或历史留出答案。

## 推断

- LIVE-YT 的原始 30 个采样帧标签适合未来做稀疏 9:16 独立诊断；VC++ 是时间滤波后的派生标签，不能冒充每帧直接人工真值。
- LIVE-YT 最可能只需一轮作者确认即可进入最小试点，但在得到书面回答和实际字节哈希前，`BYTE_BOUND_IDENTITY` 只能写“设计上可绑定、尚未字节核验”。
- GAICD 即使取得许可，也应保留所有候选与人评分，不能挑最高分后称唯一人工框；它不是当前首选。

## 未知与限制

- LIVE-YT Box 目录未提供数据专属许可、每项底层来源/归属映射和文件大小清单；这些必须由维护方确认或在获准下载后核验。
- 没有候选媒体，因此没有做 pHash/帧指纹；AIC 交集只能写 `UNKNOWN_BEYOND_METADATA`。
- 共享工作区不提供真正的权限隔离，`PROCESS_SEALED` 只能约束正常入口和普通产物，不证明底层文件绝对不可读。
- 本轮没有独立 9:16 分数，更没有 AIC 官方联合分或官方提分证据。

## 关键交付

- [候选登记]({local_link(run / 'targeted_candidate_registry.json')})
- [许可证据矩阵]({local_link(run / 'license_evidence_matrix.json')})
- [标注语义矩阵]({local_link(run / 'annotation_semantics_matrix.json')})
- [保护注册表]({local_link(run / 'protected_input_registry.json')})
- [流程封存协议]({local_link(run / 'process_sealed_protocol.md')})
- [未绑定 commitment 模板]({local_link(run / 'holdout_commitment_template.json')})
- [未发送授权询问稿]({local_link(run / 'permission_request_draft.md')})
- [一手来源快照索引]({local_link(run / 'source_snapshot_index.json')})
- [资源记录]({local_link(run / 'resource_usage.json')})

## 停止边界

本阶段到此停止，等待总控Agent验收。该状态不批准 P2-Q、P2-T、P3、GPU、训练、比赛测试推理、真实留出调用、候选打包、上传或提交。
"""
    (run / "REPORT.md").write_text(report, encoding="utf-8")

    evidence_items = []
    for path in sorted(run.rglob("*")):
        if not path.is_file() or path.name in {"final_freeze.json", "final_freeze.sha256.txt", "freeze_verification.json", "evidence_index.json", "file_hashes.json"}:
            continue
        evidence_items.append({
            "path": path.relative_to(root).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    write_json(run / "evidence_index.json", {
        "schema": "p2r9_evidence_index_v1",
        "run_id": RUN_ID,
        "status": FINAL_STATUS,
        "created_utc": now,
        "files": evidence_items,
    })
    print(json.dumps({"status": FINAL_STATUS, "candidates": len(candidates), "evidence_files": len(evidence_items)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
