# Complete-reference native runtime v1

此目录是新的训练/评估实现，未启动训练、decoder、processor、模型或 GPU。原 B8B、旧实验及冻结文件保持原字节。打包、远端上传、资源准入和费用账本由主控管理；本代码不启动外层 runner，也不产生官网分数。

## 入口

以下命令必须在主控完成参考与字节锁登记后，由已有 resource_runner 在已准入的 Linux 资源上执行。当前没有已解锁配置或可执行授权锁。

```text
python -B runtime/train.py --config NEW_CONFIG.json --lock NEW_SOURCE_LOCK.json --expected-lock LOCK_SHA --check-only
python -B runtime/preflight_native_inputs.py --config NEW_CONFIG.json --lock NEW_SOURCE_LOCK.json --expected-lock LOCK_SHA --output-dir NEW_CPU_PREFLIGHT_OUTPUT
python -B runtime/train.py --config NEW_CONFIG.json --lock NEW_SOURCE_LOCK.json --expected-lock LOCK_SHA --preflight-receipt NEW_CPU_PREFLIGHT_OUTPUT/receipt.json --expected-preflight-receipt PREFLIGHT_SHA

python -B runtime/evaluate.py --config NEW_CONFIG.json --lock NEW_SOURCE_LOCK.json --expected-lock LOCK_SHA --final-receipt NEW_TRAIN_OUTPUT/training_receipt.json --expected-final-receipt RECEIPT_SHA --check-only
python -B runtime/evaluate.py --config NEW_CONFIG.json --lock NEW_SOURCE_LOCK.json --expected-lock LOCK_SHA --final-receipt NEW_TRAIN_OUTPUT/training_receipt.json --expected-final-receipt RECEIPT_SHA
```

`--check-only` 完成字节、参考、分母、目标序列化与最终权重回执的静态校验，不导入 torch、PyAV、transformers 或 processor。训练输出和评估输出分别必须不存在，禁止覆盖、恢复或补考同一目录。评估只允许原 B 与唯一 `final_adapter`；没有中间 checkpoint 选择。

纯无模型测试：

```text
python -B -m unittest discover -s runtime -p test_runtime.py -v
```

## NEW_CONFIG.json

配置由主控新建，至少具有以下字段；所有路径均是当前执行主机的实际绝对路径，不能原地改写旧 Windows 参考或旧冻结输入来适配 Linux。

```json
{
  "schema": "COMPLETE_SILVER_NATIVE_RUNTIME_V1",
  "historical_run_root": "ABSOLUTE_EXISTING_REMATCH_EXEC_ROOT",
  "model_dir": "ABSOLUTE_EXISTING_QWEN3VL_8B_ROOT",
  "processor_dir": "ABSOLUTE_ACTUAL_PROCESSOR_SNAPSHOT",
  "initial_adapter_dir": "ABSOLUTE_ORIGINAL_B_ADAPTER",
  "initial_adapter_sha256": "8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23",
  "expected_base_sha256": "74bcce81cfcb0893cf4b4c25ae36ec908d6ea669583aedd0f3940063080b8b59",
  "seed": 20261010,
  "epochs": 2,
  "micro_batch": 1,
  "optimizer": {"name":"AdamW","lr":0.00001,"betas":[0.9,0.999],"eps":0.00000001,"weight_decay":0,"clip_norm":1},
  "protocol": {"path":"ABSOLUTE_FROZEN_PROTOCOL_V2", "sha256":"SHA"},
  "plan": {"path":"ABSOLUTE_24_WINDOW_PLAN", "sha256":"SHA"},
  "reference_registry": {"path":"ABSOLUTE_DENOMINATOR24_REGISTRY", "sha256":"SHA"},
  "processor_binding": {"path":"ABSOLUTE_ACTUAL_PROCESSOR_BINDING", "sha256":"SHA"},
  "quality_contract": {"path":"ABSOLUTE_ORIGINAL_QUALITY_CONTRACT", "sha256":"SHA"},
  "silver_contract": {"path":"ABSOLUTE_ORIGINAL_SILVER_CONTRACT", "sha256":"SHA"},
  "event_metrics": {"path":"ABSOLUTE_ORIGINAL_EVENT_METRICS", "sha256":"SHA"},
  "source_files": {"MEDIA_SHA": {"path":"ABSOLUTE_ALREADY_PRESENT_ALLOWED_MEDIA", "sha256":"MEDIA_SHA"}},
  "target_sidecars": {"WINDOW_ID": {"path":"ABSOLUTE_NEW_REVIEWED_TARGET_SIDECAR", "sha256":"SHA"}},
  "training_authorization": {"unlocked":false,"complete_silver_admitted":false},
  "final_only_evaluation_window_ids": ["ALL_4_PROCESS_DEV_AND_8_LOCKED_IDS_IN_SORTED_ORDER"],
  "train_output_dir": "ABSOLUTE_NEW_TRAIN_OUTPUT",
  "evaluate_output_dir": "ABSOLUTE_NEW_EVALUATION_OUTPUT"
}
```

`reference_registry` 可采用现有 `denominator24_v1.json` 的直接 ID 映射，或 `{"records":{...}}`。全部 24 行必须保留。无 reference 的状态必须明确以 `PENDING` 或 `REJECTED` 开头。每个已存在 reference 必须通过原 `silver_contract.verify_window`；训练行再通过原 `training_schedule`，8–12 窗、至少 4 源、至少 2 正源。4 个 process_dev 和 8 个 locked 行都需完整覆盖声明域的独立 reference。

`NEW_SOURCE_LOCK.json` 格式为 `{"files":{"ABSOLUTE_PATH":"SHA256"}}`。锁必须包括本目录全部 `.py`、NEW_CONFIG、protocol、plan、registry、每份 reference/target sidecar、所有允许的 source media、三份原科学 contract、实际 processor 全文件、原 adapter 两文件、模型 config/generation_config/weight index/全部 safetensors，以及 common.py 的 `dependency_names` 所列历史 runtime 依赖。reference 自身的 evidence 路径/SHA仍逐一核验。不得将可变训练日志加入静态锁。

## 独立已审 target sidecar

原 Fraction reference 不改写。原 grammar 仅接受 <=18 位有限小数且必须由原 float parser 保持 numeric identity；非终止 Fraction 没有 sidecar 时静态拒绝。sidecar 必须逐边界登记审阅范围，声明这些序列化点不是实测 cut：

```json
{
  "window_id":"WINDOW_ID",
  "reference_sha256":"EXACT_REFERENCE_SHA",
  "reviewed":true,
  "not_measured_cut":true,
  "exact_target_local":[["0","720619/30000"]],
  "serialized_decimal_as_str":[["0","24.020633333333333"]],
  "reviewed_boundary_ranges_local_exact":[[["0","0"],["REVIEWED_LOW","REVIEWED_HIGH"]]]
}
```

此示例不是自动批准 W01 的实际完整 target；sidecar 的所有分段必须与该 reference 的完整 KEEP列表相同。运行时以 Decimal→Fraction 精确比较，不使用 epsilon；要求映射在登记审阅范围内，且 native64 以及完整 eligible 原生帧 KEEP集合都不改变。范围或成员不相等时停止，不修改 reference、不补帧、不自动舍入。

完整 Linux 输入投影和媒体 SHA 已实际验收后，可用 `python -B runtime/freeze_inputs.py --config NEW_CONFIG.json --output NEW_SOURCE_LOCK.json` 新建字节锁。该入口从当前 `common.py` 的实际依赖清单收集历史依赖、当前全部运行源码、参考与证据、媒体、processor、base 和原 B adapter，不导入历史 launcher 或模型。锁生成后仍必须通过 `train.py --check-only` 和实际 CPU preflight，才能进入 GPU 训练。

## 工程与科学验收

训练维持原 B0 prompt、顺序 PyAV native PTS、floor64、原 source97 色彩白名单和固定 total-video 像素预算。编码要求与已审 `student_processor` 回执的 64 原始 RGB SHA、normalized tensor SHA、grid 和 input tokens 一致。训练完整序列 <=16384 tokens，assistant suffix <=256；只监督 assistant JSON、`<|im_end|>` 与其末尾换行，并保留一个 causal predecessor logit。没有 scores_x20 或逐帧 importance loss。

源权重 `N/(G*n_s)` 与原 schedule 的 `ceil(N/4)/N` 系数只乘一次。实际固定两轮随机窗序，每窗每轮恰好一次，4/6 updates；源均衡是该精确目标函数，不重新更换随机顺序。首步非零 finite 梯度、每步 finite CE/真实权重变化、实际 update/source 顺序写入新目录。最终检查冻结 base/vision 全字节、唯一 checkpoint，以及 288 张 LoRA tensor 保存后重载的 dtype/值身份。loss 下降不构成质量通过。

评估保留原 grammar/greedy 与 parser，并以精确 Fraction 独立核验分段和 half-open 原生帧集合。raw 在任何解析校验之前独占保存；失败不会成为空窗。源级 exact 时间集合 F1、precision/recall、最大一对一 tIoU=0.5 event recall、NO FP、已知正例空窗、UNKNOWN conservative gates 和原 locked 0.05 增益门全部执行。新选取的 confirmed-NO 时间，即使总 FP 时长不增加，也视为新 unrelated spill。仅 UNKNOWN 而无 confirmed KEEP 的源，只有完全相同的预测可证明 conservative 零增益；改变预测时该门 fail-closed。科学失败返回 5，明确 NO426/不改配方补考。

## 当前验证与限制

主控追加了 `preflight_native_inputs.py`：静态准入后，用实际 CPU 顺序解码与原 processor 完整核对训练窗和12评估窗的有效张量、输入、native PTS及assistant目标，模型调用和CUDA初始化均为0。每窗输出和最终回执单独绑定 SHA。真实训练 CLI 还必须提供 `--preflight-receipt` 和 `--expected-preflight-receipt`；只有当前锁/配置对应的实际 CPU 接受回执才可进入模型加载。`--check-only` 不要求尚未生成的 CPU 回执。新增入口只验证过 CLI help，实际 CPU 执行仍待完整数据准入和Linux部署，不把代码实现当作实际接受。

2026-10-10：11 个 stdlib-only 数学 oracle 测试通过；8 个 Python 文件 AST 解析通过。未创建真实解锁配置、source_lock、训练回执或评估回执。未实际加载 decoder、processor、LoRA/base、GPU或运行新优化器；真实模型损失接口、native 像素/输入一致性、288 tensor 保存重载和科学质量仍须在主控解锁后实测。完整参考与 sidecar 若不满足上面的静态门，程序不会进入模型加载。
