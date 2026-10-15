# Strict positive admission v1

本目录只实现独立小试。保留旧 40.46 风格基线全部原帧；完整旧短视图 B0 + 旧 VERIFY 显式 KEEP 且存在基线外 native 帧的候选，才进行一次新提示词模型准入。候选原端点不改；新 KEEP 加入完整原候选，UNKNOWN/DROP 不新增。原候选减基线的每个 native 连通段都必须有独立正面可见证据，已有基线亮点不能替新增段背书。旧调用与旧 QA 仅绑定引用。

当前 dev 链精确采用原四源 26 B0、37 VERIFY：输出决定的十条真实新增候选，另十五条 old KEEP overlap 因 native contribution 全含于基线而数学省略。prepare 重新导出完整 37 条分母审计并与 `protocol_v2.json` 的十条登记核对，不读取参考标签。

## 最简注册

Linux 新独占根目录下保存 `registration.json`；部署所有本目录 `.py` 到 `root/code/`。所有 ref 为 `{ "path": "absolute Linux path", "sha256": "64 lowercase hex" }`。

```json
{
  "status": "REGISTERED_POSITIVE_ADMISSION_V1",
  "stage_group": "dev",
  "baseline_sha256": "86593725c6bad919dc0d342fe98ad65e489a13a6e492da5de3afd247a3226543",
  "model_parameters": 8782459120,
  "source_scope": "EXTERNAL_NONTEST_ONLY",
  "reference_available_to_inference": false,
  "optimizer_updates": 0,
  "production_admitted": false,
  "protocol_ref": { "path": "ROOT/protocol_v2.json", "sha256": "..." },
  "authorization_ref": { "path": "ROOT/USER_AUTHORIZATION.json", "sha256": "..." },
  "legacy_model_common_ref": { "path": "PRIOR/code/model_common.py", "sha256": "..." },
  "legacy_token_module_ref": { "path": "/home/inspur/aic_video_work/twenty_hour_five_20261014_v1/candidate_verify_v2/code/cv_tokens.py", "sha256": "..." },
  "proxy_metrics_ref": { "path": "PRIOR/code/evaluate_pilot.py", "sha256": "..." },
  "required_files": { "absolute code/dependency/metadata path": "sha256" },
  "adopted_source_groups": {
    "dev": [{
      "prior_root": "/home/inspur/aic_video_work/recall_expansion_verify40_46_20261014_v1",
      "prior_group": "dev",
      "source_names": ["v_vfJnUQ9Tax0", "v_8tlLBffNjf8", "v__CMIO5R_OGA", "v_voaGOm-rl9Y"],
      "old_cpu_admission": { "path": "PRIOR/cpu_acceptance_dev.json", "sha256": "..." },
      "old_b0": {
        "admission": { "path": "PRIOR/gpu_admission_dev_B0.json", "sha256": "..." },
        "gpu_completion": { "path": "PRIOR/dev/B0/gpu_01/completion.json", "sha256": "..." },
        "replay_completion": { "path": "PRIOR/dev/B0/replay_01/completion.json", "sha256": "..." }
      },
      "old_verify": {
        "admission": { "path": "PRIOR/gpu_admission_dev_VERIFY.json", "sha256": "..." },
        "gpu_completion": { "path": "PRIOR/dev/VERIFY/gpu_01/completion.json", "sha256": "..." },
        "replay_completion": { "path": "PRIOR/dev/VERIFY/replay_01/completion.json", "sha256": "..." },
        "export": { "path": "PRIOR/dev/VERIFY/verification_export.json", "sha256": "..." }
      },
      "reference_completion": { "path": "PRIOR/reference_completion_dev.json", "sha256": "actual pointer file digest" }
    }]
  },
  "gpu_budget": { "dev": {
    "max_actual_calls": 10,
    "max_seconds": 1200,
    "gpu_job_name": "unique_positive_dev10_job_name",
    "deadline": "timezone-aware ISO timestamp"
  }}
}
```

`required_files` 必须在运行前绑定全部新 `code/*.py`、协议/auth/官方回执、三个 legacy refs、cv_tokens 同目录的 cv_contract.py、`legacy.runtime_dependencies()`、`legacy.processor_assets()` 与 `legacy.CONFIG`。只枚举已有运行时代码和 processor metadata，不扫描或下载模型权重。旧媒体、RGB、processor、B0、旧 VERIFY、旧 QA 不重做。旧 source/input/proof/cache 的所用闭包由 `adopted()` 收集，admit 生成新的 `source_lock_dev_POSITIVE.json`。

参考入口可为实际 reference completion ref 或原 pointer ref，评价进程才打开其内容与标签。prepare/input QA/admit/infer 仅核 ref 文件 SHA，不读人工标签。实际 pointer 与 target SHA 必须分别从原文件核准，不能复用 inventory 中被同名字段覆盖的摘要值。

## 唯一运行入口

主线程完成真实资源核对与注册冻结后，使用现有 Python 和显式 `CUDA_VISIBLE_DEVICES=0`：

```text
PYTHON -B -u ROOT/code/positive_chain.py --root ROOT --group dev
```

链依次启动独立 CPU 子进程 prepare → input_qa → admit；使用现有唯一共享 `RUN/resource_unlimited_v1_20261007/gpu_run.py` 完成十条新调用；自然 completed/exit0 且共享 ledger 唯一一致后，再独立 CPU output-only QA → 八门 dev 评价。CPU 子进程仅屏蔽自己的 CUDA，父 CUDA0 保留。首次新 token 输入 QA 在 GPU 前以独立 partition/encode 实现逐比特比较；GPU 后不重复该 encode 或旧 vision processor，仅核实际 output token/grammar/parser/native 与首次 input proof 绑定。

所有目录以 `exist_ok=False`、文件以 exclusive create 写入。工程失败留 raw/failure/成功，不产生 UNKNOWN/EMPTY，不自动重启。链到 dev PASS 冻结或 scientific STOP 即结束，不自动取得新确认媒体、fixed40、426 或 ZIP，也不创建 Goal/心跳。

## 本地纯检查

`python -B improvement/recall_positive_admission_v1/check_pure.py` 只使用合成数据，检查 exact novel runs、零可见样本的不确定性契约、三路 canonical JSON、UNKNOWN/DROP 不加帧、原 baseline 函数一致和八门精度拒绝。它不证明真实输入/GPU/科学质量已通过。
