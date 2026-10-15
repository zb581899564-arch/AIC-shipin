# First independent fresh positive-admission confirmation

本目录部署到 `MAIN/fresh_01/code/`。原冻结 `MAIN/code/positive_*.py` 不修改。媒体模块单独先完成 `MAIN/fresh_01/reference_01/completion.json`，再注册本链；本链不下载、不重新测 clock、不创建 Goal/心跳、不自动 fixed40/426/ZIP。

唯一入口（现有 Linux Python，父进程 `CUDA_VISIBLE_DEVICES=0`）：

```text
PYTHON -B -u FRESH/code/fresh_chain.py --root FRESH --positive-root MAIN
```

`FRESH=MAIN/fresh_01`，其中 `MAIN` 为现有独立新增准入项目根目录。

## `positive_fresh_registration.json`

所有 ref 均为实际绝对 Linux path 和 SHA256。`protocol_ref` 指现有 main `protocol_v2.json`；不能把旧 consensus/failure/recovery registration 冒充本次科学准入。

```json
{
  "status": "REGISTERED_POSITIVE_FIRST_FRESH_CONFIRM_V1",
  "group": "confirm",
  "model_parameters": 8782459120,
  "optimizer_updates": 0,
  "source_scope": "EXTERNAL_NONTEST_ONLY",
  "reference_available_to_inference": false,
  "production_admitted": false,
  "protocol_ref": {"path": "MAIN/protocol_v2.json", "sha256": "..."},
  "authorization_ref": {"path": "MAIN/USER_AUTHORIZATION.json", "sha256": "..."},
  "development_registration_ref": {"path": "MAIN/registration.json", "sha256": "..."},
  "dev_selection_ref": {"path": "MAIN/dev/selection_before_confirmation.json", "sha256": "..."},
  "dev_result_ref": {"path": "MAIN/dev/comparison_01/result.json", "sha256": "..."},
  "source_registration_ref": {"path": "FRESH/media_registration.json", "sha256": "..."},
  "reference_completion_ref": {"path": "FRESH/reference_01/completion.json", "sha256": "..."},
  "frozen_positive_code_dir": "MAIN/code",
  "required_files": {"absolute code/dependency/asset path": "sha256"},
  "capacity_contract": {
    "video_size": {"shortest_edge": 0, "longest_edge": 0},
    "processor_source_path": "actual installed transformers video_processing_qwen3_vl.py",
    "processor_source_sha256": "..."
  },
  "deadline": "timezone-aware 6-hour deadline ISO timestamp",
  "gpu_budget": {
    "B0": {"max_actual_calls": 48, "max_seconds": 1800, "gpu_job_name": "recall_positive_fresh4_b0_20261015_v1"},
    "VERIFY": {"max_actual_calls": 240, "max_seconds": 2400, "gpu_job_name": "recall_positive_fresh4_verify_20261015_v1"},
    "POSITIVE": {"max_actual_calls": 80, "max_seconds": 1200, "gpu_job_name": "recall_positive_fresh4_admission_20261015_v1"}
  }
}
```

`video_size` 必须从既有 `CONFIG.video_size` 读真实值，示意零值不可运行。`required_files` 在准备前冻结全部本目录 `.py`、媒体 `.py`（若同目录）、原 main 所有已冻结 `.py`、本次协议/auth/rules/source-registration、原 dev registration/selection/result、`model_common.runtime_dependencies()`、`processor_assets()`、`CONFIG`、`RUNTIME`、`CV_CODE/{cv_contract,cv_tokens,cv_grammar}.py`、现有共享 `gpu_run.py` 及其直接依赖、安装的 processor source。禁止重新下载权重或扫描无关用户目录。

## 来源接口

`media_registration.json` 使用媒体模块的实际 schema；本链只使用：`known_exclusions_ref`、`source_candidates_ref`、`annotation_file_ref`、`prior_media_receipts`、`selection`、`ordered_engineering_reserves`。`source_candidates_ref` 中 `exclusions.all_old_conservative_plus_acquired_IDs` 保持全部旧身份排除。首四固定 NNuIaUFYGCE / pHZogKGkc9o / 5FM_xJGb-Tk / YW3mCNKVaa4；工程备选按既有顺序 1VDNFR3vQR4 / SFfB6qvT5FI。备选是否可用由原媒体准入按工程失败类别判定，本 CPU/模型链从不换源。

媒体完成回执须为：

```json
{
  "status": "PASS_POSITIVE_FRESH_MEDIA_NATIVE_SECONDS_NOT_INPUT_OR_GPU",
  "group": "confirm",
  "source_registration_ref": {"path": "FRESH/media_registration.json", "sha256": "..."},
  "dev_selection_ref": {"path": "MAIN/dev/selection_before_confirmation.json", "sha256": "..."},
  "dev_result_ref": {"path": "MAIN/dev/comparison_01/result.json", "sha256": "..."},
  "accepted": [{
    "video_id": "v_NNuIaUFYGCE", "group": "confirm",
    "media": {"video_id": "v_NNuIaUFYGCE", "group": "confirm", "path": ".../media.mp4", "bytes": 1, "sha256": "...", "known_ID_and_byte_separation": true},
    "clock_path": ".../clock.json", "clock_sha256": "...",
    "reference_path": ".../reference.json", "reference_sha256": "..."
  }]
}
```

实际 accepted 必须完整四条，clock/reference 与原 `native_profile_04` schema一致，media旁保留 `media_receipt.json`、`route.json`。CPU准备只读 clock、source metadata，并核引用文件 SHA；不会打开人工 reference 或 annotation 内容。首次人工指标只在链末调用冻结 `positive_evaluate.py --group confirm`。

## 工序和证据

1. `prepare_inputs.py` 沿用原 30 秒基线、15 秒短窗/7.5 秒步长、64 不同原生帧、唯一视图别名；每源一次 union RGB 解码，每 unique view 一次原 processor primary encode。
2. 独立进程 `first_input_qa.py` 对 PNG/NPZ/clock/native 与真实 processor 再观察一次，逐比特比较 primary/cache；所有来源所有视图完成首次输入 QA 后才 B0 GPU。保存新的 accepted proof 文件，原 primary proof不覆盖。
3. B0 唯一共享 wrapper，自然 completed/exit0/唯一 ledger，随后首次 output token/grammar/parser/native QA，引用已经完成的 first input proof，不再视觉编码。
4. 原保守 VERIFY 对完整 B0 candidate denominator prepare，独立 `verify_input_qa.py` 在其 GPU 前首次 partition/encode 新 text tokens、确认视觉 prefix不变。其 GPU后首次 output QA引用该输入proof，不再input retarget。
5. 完整 source/CPU/B0/VERIFY/QA 输出自动登记成冻结 `positive_io.adopted()` 可纯引用的 `registration_confirm.json`，其 `prior_root=FRESH` 与 `positive_root=MAIN` 不同。
6. 调用冻结正面准入 `positive_runtime.py` confirm prepare → 首次 token 输入 QA → admit → 第三个唯一共享 GPU → output-only QA → 冻结八门首次新四源评价。PASS仅待 fixed40；STOP保留全部证据，不自动生产。

完整 denominator 无候选时不造 GPU/UNKNOWN：明确数学零新增无法达到已冻结 recall +0.01 门，保存 scientific STOP 回执；已有成功 primary/QA/model不会重跑。工程错误均留 failure/raw/成功并阻断，不转 scientific UNKNOWN 或空预测。
