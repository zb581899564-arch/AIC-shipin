# relative 首次新4确认控制接口（准备代码，尚未执行）

新根固定为 `/home/inspur/aic_video_work/midnight_five_verify40_46_20261015_v1/relative_confirm`。旧 dev8 no-change STOP 与所有旧 ROLE/positive/consensus STOP 保持。只有新的 relative dev 真 PASS 才能创建候选注册并执行获取；本目录没有自动恢复或旧失败接续。

## 1. 准确来源、数量与小元数据导出

依原 ID-only hash 顺序，已排 known IDs 与原所有 protected/acquired/exposed 后，下一 4 为：

| video_id | author_duration_raw | 固定物体字节 |
|---|---:|---:|
| v_RTwa2d6Oqvo | 45.07 | 4,078,362 |
| v_Nj_fvFbf56I | 32.86 | 2,006,560 |
| v_MkouTZhtvEI | 57.54 | 28,787,217 |
| v_xAI1y9izXOM | 40.96 | 22,216,388 |

4 源合 57,088,527B；next2 reserve 为 `v_sqcJOpPrexQ`（22,864,284B）、`v_WV_MFi9EZeQ`（1,997,368B），6 池 81,950,179B。前两源为 ROLE 未使用的预留，ROLE 自身实际 4 源均已成功且没有 rejected。表中是保留作者元数据，尚未解码验证；预估 2 窗/源、总 8 窗，最终必须依实测 `physical_end_exact` 的 `ceil(T/30)`。

Windows 仅生成原 64 个候选的完整 provider 小子集（必须先由 main 建好报告目录）：

```powershell
python -B "G:/ai/AIC视频/improvement/midnight_five_reference_v1/confirm_mapping.py" export-provider-prefix --id-export "G:/ai/AIC视频/reports/recall_expansion_verify40_46_20261014_v1/new8_identity_selection_metadata_01.json" --inventory "C:/Users/33056/AppData/Local/Temp/aic_third_reference_20261013/tornadolabs_metadata.jsonl" --output "G:/ai/AIC视频/reports/midnight_five_verify40_46_20261015_v1/provider_prefix_06.json"
```

原 inventory 4,056,380B/SHA `b3849e17b6b821044c87789c2b1108009a4c50a0b08d255cd908a97255916042`。导出包括完整 available/absent 前缀，不能只提供喜欢的 6 源。上传小子集与原 ID-only export（原字节，不重序列化）至新根，不必传 4MB 原 inventory。

Linux 部署 `confirm_mapping.py/reference_common.py` 后：

```text
PY=/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python
MAIN=/home/inspur/aic_video_work/midnight_five_verify40_46_20261015_v1
$PY -B $MAIN/reference_code/confirm_mapping.py select --id-export $MAIN/relative_confirm/original_id_export.json --provider-prefix $MAIN/relative_confirm/provider_prefix.json --role-root /home/inspur/aic_video_work/recall_adapter_role_verify40_46_20261015_v1/fresh_01 --protocol $MAIN/relative_protocol_03.json --development-selection $MAIN/relative_dev_comparison_04_selection.json --output $MAIN/relative_confirm/source_candidates.json
```

`evaluate.py --output relative_dev_comparison_04.json` 实际产生的 selection 名字正是 `relative_dev_comparison_04_selection.json`。`select` 会检查实际新 dev PASS/result/protocol，采用 known 692 IDs/1149 文件 hash、旧 protected IDs、原 prior18 实际媒体 receipt 和 ROLE 实际 4 receipt（共 22），不会读参考票数/字幕/事件文字。隐藏别名、子片段、预训练重叠仍 UNKNOWN。

## 2. media_registration.json 完整接口

先按新 6 源获取 current HEAD-only routes，写 `public_routes.json`，格式延续旧 ROLE 的 routes：顶层 `windows_video_body_bytes=0`、6 个 `routes`；每项 `video_id/initial_public_url/bytes/metadata_only=true/status`，成功时含 `publisher_redirect_url/etag`；仅 normal HTTPS publisher CDN 或明确 PUBLIC_OBJECT_404。网络/版本失败不换源。

部署 `confirm_media.py/reference_common.py` 至新根 `media_code/`，构造：

```python
{
  "schema": "MIDNIGHT_RELATIVE_FIRST_FRESH_MEDIA_REGISTRATION_V1",
  "status": "REGISTERED_MIDNIGHT_RELATIVE_FIRST_FRESH_MEDIA_NATIVE",
  "group": "confirm",
  "expected_accepted_sources": 4,
  "maximum_media_pool_bytes": 81950179,
  "windows_video_body_bytes": 0,
  "production_admitted": False,
  "protocol_ref": ref(MAIN/"relative_protocol_03.json"),
  "authorization_ref": ref(MAIN/"USER_AUTHORIZATION.json"),
  "development_selection_ref": ref(MAIN/"relative_dev_comparison_04_selection.json"),
  "source_candidates_ref": ref(ROOT/"source_candidates.json"),
  "public_routes_ref": ref(ROOT/"public_routes.json"),
  "media_helper_ref": ref(Path("/home/inspur/aic_video_work/recall_positive_admission_verify40_46_20261015_v1/fresh_01/media_code/positive_media.py")),
  "required_files": {absolute_path: sha256, ...}
}
```

`required_files` 冻结新 `media_code/*.py`、上述全部引用与真实 relative result、候选嵌套的 known/annotation/scope/prior22 receipts，以及旧 positive helper 和其动态 native 实现 `videoxum_reference_iteration_20261013_v1/code/native_profile_01.py`、`native_profile_04.py`。`ref` 必须为 `{path,sha256}` 且实际字节符合。独立 reg 本身完成后不可改写。

**不能原样用旧 helper.download**：其内部旧 `POOL_BYTES=49,919,698`，新六池会超过旧门。新 wrapper 的 `download_once` 保留单 GET、固定 ETag/Content-Length、不带凭据、不重定向/重试/续传的行为，使用本次新注册 81,950,179B 门；旧文件/旧模块预算不改。旧 helper 仅复用原生测量加载器、原参考 schema 提取等明确函数。新原生域检查保持原零起点、逐帧 PTS、实际末帧正 duration 与原参考端点，只检查本次 baseline 窗 native64，不引入 overlap 视窗。

实际执行入口（这里只展示）：

```text
CUDA_VISIBLE_DEVICES='' $PY -B $MAIN/relative_confirm/media_code/confirm_media.py --root $MAIN/relative_confirm
```

仅 preregistered/实际 404 或明确原生域拒绝可依序用两个 reserve；其他失败停止。成功写 `reference_01/completion.json` 和 `reference_completion_confirm.json` 指针，status 为 `PASS_MIDNIGHT_RELATIVE_FRESH_MEDIA_NATIVE_SECONDS_NOT_INPUT_OR_GPU`。下载成功不能当作 native64 输入、QA 或 GPU 准入。

## 3. CPU 原 B 输入：可与其他已准入 GPU 工作独立排程

将 `confirm_runtime/` 的全部 **12 个 py** 原字节部署至新根 `code/`。它们由已成功 ROLE fresh 的 CPU/B0/VERIFY实现复制，只替换新 `fresh_registration.py` 的注册/媒体入口、`source_plan.unique_view_plan` 为 baseline-only，以及明确的新 primary evidence origin。`model_common`、`native_helpers`、原 B0/VERIFY、首次输入 QA 与 GPU 后 output-only QA 逻辑保留；不包含旧 `fresh_chain.py` 或旧 positive 评价。

新独立输入 reg 文件仍称 `positive_fresh_registration.json` 以兼容旧阶段读取接口，内容必须是新状态：

```python
{
  "status": "REGISTERED_MIDNIGHT_RELATIVE_FIRST_FRESH_INPUTS_V1",
  "group": "confirm", "model_parameters": 8782459120, "optimizer_updates": 0,
  "source_scope": "EXTERNAL_NONTEST_ONLY", "reference_available_to_inference": False,
  "production_admitted": False,
  "protocol_ref": ref(MAIN/"relative_protocol_03.json"),
  "authorization_ref": ref(MAIN/"USER_AUTHORIZATION.json"),
  "dev_selection_ref": ref(MAIN/"relative_dev_comparison_04_selection.json"),
  "dev_result_ref": ref(MAIN/"relative_dev_comparison_04.json"),
  "source_registration_ref": ref(ROOT/"media_registration.json"),
  "source_candidates_ref": ref(ROOT/"source_candidates.json"),
  "reference_completion_ref": ref(ROOT/"reference_01/completion.json"),
  "required_files": {absolute_path: sha256, ...},
  "capacity_contract": ORIGINAL_ROLE_FRESH_INPUT_REG["capacity_contract"],
  "deadline": "2026-10-15T16:00:00Z",
  "gpu_budget": {
    "B0": {"max_actual_calls": ACTUAL_BASELINE_PLAN_COUNT, "max_seconds": 1200, "gpu_job_name": "UNIQUE_NEW_NAME"},
    "VERIFY": {"max_actual_calls": 5*ACTUAL_BASELINE_PLAN_COUNT, "max_seconds": 1800, "gpu_job_name": "ANOTHER_UNIQUE_NEW_NAME"}
  }
}
```

`capacity_contract` 来自 `/home/inspur/aic_video_work/recall_adapter_role_verify40_46_20261015_v1/fresh_01/positive_fresh_registration.json` 的实际已验原 smart_resize/installed processor contract，复制该字段原值并冻结其 `processor_source_path/SHA`。新 reg 的 `required_files` 除 12 新 py 与全部引用外，包含 `model_common.runtime_dependencies()`、`model_common.processor_assets()`、`CONFIG/RUNTIME` 与原 CV contract/token/grammar helper 及 capacity processor 源。先据实际新 clock 用纯 `source_document` + `baseline_only_plan` 得到分母再固定 budget，不能凭表中作者时长假装已测 8。

```text
CUDA_VISIBLE_DEVICES='' $PY -B $MAIN/relative_confirm/code/prepare_inputs.py --root $MAIN/relative_confirm
CUDA_VISIBLE_DEVICES='' $PY -B $MAIN/relative_confirm/code/first_input_qa.py --root $MAIN/relative_confirm
```

第一步只新 4 次单源 RGB 解码与预计 8 次 primary encode/cache；第二步是独立进程首次 8 次 vision input QA，均不启动 GPU。stage 不可重跑；失败保留成功与缓存，任何剩余恢复须明确另登记。4 来源下预计 8 B0、最多 40 原 VERIFY（实际候选数在 B0 后固定）、最后最多 8 个新的 BASE relative classifier 视窗；没有 overlap B0 或旧成功重算。

新 GPU 仍须主链生成实际 CPU/QA/source lock 后的独立 B0/VERIFY admission，用唯一共享 `gpu_run.py` 和自然终态账本；没有提供可绕过准入的 launcher。B0/VERIFY 原 TIME 角色和所有 8,782,459,120 驻留参数保持，最终 relative classifier 才在生成内禁用 TIME。

## 4. 新分类映射与首次确认评价

主链完成新 B0/VERIFY 及首次 output QA 后，将外层 `map_existing.py/map_confirm_completed.py/reference_common.py` 部署同一新 reference code 目录：

```text
$PY -B $MAIN/reference_code/map_confirm_completed.py --root $MAIN/relative_confirm --output $MAIN/relative_confirm/rank_mapping_01
```

生成 `inference_entries.json`、实际 ID/byte/native/B0/VERIFY/first-QA 绑定的 `fresh_admission.json` 和 `first_fresh_evaluation_manifest.json`。只用新成功输入，不跑旧比较或重放 QA。主分类器用 inference entries 产生新的首次输入/输出 QA 后：

```text
$PY -B $MAIN/reference_code/evaluate.py --manifest $MAIN/relative_confirm/rank_mapping_01/first_fresh_evaluation_manifest.json --decisions NEW_RELATIVE_CLASSIFIER_STAGE/completion.json --output $MAIN/relative_confirm/fresh_comparison.json
```

完整新 4 源首次确认，只有实际 relative dev PASS 的臂可获确认 PASS；失败臂不因另一臂新源表现获得恢复。人工摘要未选仍不是 ORDINARY 真值，官方提分效果 UNKNOWN。
