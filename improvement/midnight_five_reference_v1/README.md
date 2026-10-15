# MIDNIGHT 两个删除臂：外部参考与输入映射

本目录只实现 JSON 元数据采用和 CPU 精确时间评价。没有模型、launcher、媒体下载、processor、缓存反序列化或 QA 重放入口。旧 ROLE、positive、consensus 等科学 STOP 与其协议不变。

## 已核实的开发输入

原根 `/home/inspur/aic_video_work/recall_expansion_verify40_46_20261014_v1` 的 `cpu_acceptance_dev.json` 为 26 个完整 native64 视窗（8 baseline、18 overlap），对应 26 个 B0 成功回答和 37 个 VERIFY 成功候选及首次独立 QA。删除原基线事件只需 **8 个新视窗调用、11 个基线候选**。8 个所需 `.pt.gz` 缓存现存且大小与原证明一致；新 runtime 仍须按引用 SHA 检查实际缓存。

开发四源依原顺序为 `v_vfJnUQ9Tax0`、`v_8tlLBffNjf8`、`v__CMIO5R_OGA`、`v_voaGOm-rl9Y`。全部已曝光，标签固定为 `development_previously_exposed`，不能称新盲确认。

## 映射命令

代码部署至新根 `reference_code/`、冻结新根 `protocol.json` 后执行：

```text
/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python -B /home/inspur/aic_video_work/midnight_five_verify40_46_20261015_v1/reference_code/map_existing.py --prior-root /home/inspur/aic_video_work/recall_expansion_verify40_46_20261014_v1 --group dev --protocol /home/inspur/aic_video_work/midnight_five_verify40_46_20261015_v1/protocol.json --output /home/inspur/aic_video_work/midnight_five_verify40_46_20261015_v1/dev_mapping
```

只新增输出目录，不改写旧文件。`inference_entries.json` 的 `entries` 可直接作为新 runtime requests。每项含 `case_id/source_name/source_id/source_sha256`、`input_kind=FULL_GZIP`、`cache_ref`、`original_prompt`、完整 64 项 `source_ordinals/exact_pts`、`window_exact/window_native_end_ordinal/window_native_end_exact`、`candidate_events` 和原首次 QA 引用。`source_id` 为原 `video_id`，外部开发源不伪造比赛匿名 ID。

缓存 codec 为 `TORCH_SAVE_GZIP_LOSSLESS_LEVEL1`。原 prompt 从旧 B0 实际 `request.json` 采用，并与原 done 的请求 SHA、原 CPU evidence 的 prompt SHA 绑定。新 prompt 及首次 token QA 由新 runtime 负责。

每个候选保留原 `event_id/original_interval_exact/decision`，`selected_interval_exact` 为原基线真正贡献：按原规则起点减 `3/4` 秒、终点加 `1/2` 秒、原长至少 8 秒再加 `1/4` 秒，clip 原视窗；全源原 non-DROP 候选为空时保留原 source-empty guard。新两个臂只删除指定候选，预测为所有剩余 `selected_interval_exact` 的并集。重叠由并集自然处理，没有裁端点或为凑差异修改输出。

`evaluation_manifest.json` 单独保存 clock/reference 指针与原基线并集；不要把该文件或人工参考交给模型。映射过程只检查 reference completion 的元数据，不打开标注内容。

## 固定质量门与新输出接口

新协议用 `deletion_quality_gates`（或独立协议的 `quality_gates`）固定以下值：

```json
{
  "full_group_denominator": 4,
  "macro_paired_all_rater_duration_F1_delta_min": "0",
  "macro_all_rater_precision_delta_min": "0",
  "per_source_F1_delta_min": "-1/100",
  "minimum_sources_with_real_changed_native_frames": 1,
  "maximum_invalid_decisions": 0
}
```

两个臂分别要求宏 F1 不降、宏 precision 不降、每源 F1 最多降 0.01、invalid=0、完整四源与所有原标注者分母、至少一个来源实际减少原生帧、没有新增原生帧。召回给出精确值但不设绝对不降门，这是新删除范围的预登记门，不能回写旧补召回八门。只有删了事件但重叠导致帧集合没变化时仍为 no-change，严格 FAIL。

评价输入直接使用新 runtime 的 stage `completion.json`。每条 `entries` 带原 mapping 字段及 `decision_ref/output_qa_ref`；done 有五字段的 `parsed`、`raw_ref/input_ref/first_input_qa_ref`。逐项 proof 状态要求 `PASS_FIRST_INDEPENDENT_OUTPUT_QA`、`CPU_only=true`、`new_model_calls=0`，并绑定相同 done/raw/first-input-QA/parsed。只提取 `ordinary/redundant` 两个删除列表；`action/reaction/information` 不做人工参考指标筛选。

```text
python -B reference_code/evaluate.py --manifest dev_mapping/evaluation_manifest.json --decisions dev/completion.json --output dev_deletion_comparison.json
```

输出含每臂 `PASS/gates/macro/cases`。只要一臂 PASS，另写 `dev_deletion_comparison_selection.json`，固定独立的 passed arms；这还不是全量准入。两臂均失败时 exit 5；格式、分母、QA 或引用错误直接工程失败，不能代填空或 UNKNOWN。

## 首次新确认边界

开发通过后，主链必须另登记未曝光新 4 源。选择延续原 ID-only hash 排序，不依据标签、开发效果或已曝光确认指标重排；排除 known training/test IDs 与 hashes、所有已曝光/已取得源 ID 与已知文件 hashes。原始 ID-only 候选前缀在本地 `reports/recall_expansion_verify40_46_20261014_v1/new8_identity_selection_metadata_01.json`；原 hash salt 为 `RECALL_VERIFY40_46_VIDE0XUM_SMALL8_20261014_V1`。最新 ROLE 的 `fresh_01/source_candidates.json`、`media_registration.json` 及 `reference_01/completion.json` 需用于补齐已取得 22 源的隔离集合；其剩余 reserve 未曝光不自动代表实际媒体准入成功。

本目录没有下载或生成新来源的代码。实际新 4 媒体、clock、参考与完整 CPU 输入、首次 QA 和原 baseline 构建均须先真实完成，不能把已曝光确认改称新确认。缺少来源索引或字节隔离证据时停止，不能构造真值。隐藏别名、子片段或预训练重叠仍 UNKNOWN。

`evaluate.py` 支持 `group=confirm` 的独立 manifest：必须额外提供 `fresh_admission_ref`，指向状态 `PASS_MIDNIGHT_NEW4_ID_BYTES_NATIVE_ADMISSION` 的真实接收证明，包含 `sources_unexposed_before_registration=true`、`quality_metrics_examined_before_freeze=false`、同一 `protocol_ref`、完整有序 `source_names`、实际开发的 `development_selection_ref` 与 `admitted_arms`。该证明由主链在 ID/byte/native 检查后产生，不能仅手写这些布尔量就视为核验完成。确认评价仍保留完整四源，且只有实际通过开发的臂可取得确认 PASS。

参考是事件文字引导的人类摘要时间区间代理；人工未选不是 ORDINARY 标注。指标不是密集高光真值、不是官方成绩。所有新旧失败与官方效果 UNKNOWN 保持原意。
