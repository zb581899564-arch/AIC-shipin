# Positive first-fresh remaining recovery v2

仅部署到原 `FRESH/recovery_v2/code/`，不覆盖 `FRESH/code/`、原注册、原失败或已经成功的 primary/RGB/clock/source-plan。原生输入定义、采样、模型、全部八质量门、预算和原截止时间保持。

唯一入口（现有 Python，父 `CUDA_VISIBLE_DEVICES=0`）：

```text
PYTHON -B -u FRESH/recovery_v2/code/fresh_chain.py --root FRESH --positive-root MAIN
```

`FRESH=MAIN/fresh_01`。新控制状态为 `FRESH/confirm/chain_02/`。从尚未执行的 `first_input_qa.py` 开始；链中没有 prepare 子调用。保留的 `prepare_inputs.py` 仅作为冻结源码快照，直接调用会立即拒绝，无法重做成功准备。

## 新注册

保存独立 `FRESH/positive_fresh_recovery_registration_v2.json`。完整复制原 `positive_fresh_registration.json` 字段，除以下列明项外不改值：

- `status`: `REGISTERED_POSITIVE_FIRST_FRESH_REMAINING_RECOVERY_V2`。
- 三个 `gpu_budget.*.gpu_job_name` 分别使用 `recall_positive_fresh4_b0_20261015_v2`、`recall_positive_fresh4_verify_20261015_v2`、`recall_positive_fresh4_admission_20261015_v2`。原 max calls `48/240/80`、max seconds `1800/2400/1200`、deadline 全保持原值。
- `required_files` 保留全部原注册文件及其原 digest，再并入全部新 12 个 `.py`、下列 refs、原 primary implementation closure 中每个文件及原 digest。禁止给同一路径替换 digest。
- `original_code_files`: 原 `FRESH/code/*.py` 的完整绝对路径到 SHA256 映射，并在 `required_files` 以相同 digest 保存。

新增 refs（每条均 `{ "path": "absolute Linux path", "sha256": "actual hex" }`）：

| 字段 | 精确位置 |
| --- | --- |
| `original_registration_ref` | `FRESH/positive_fresh_registration.json` |
| `original_chain_failure_ref` | `FRESH/confirm/chain_01/failure.json` |
| `primary_completion_ref` | `FRESH/confirm/inputs_01/completion.json` |
| `diagnosis_ref` | `FRESH/remaining_recovery_diagnosis_17.json` |
| `source_clocks_ref` | `FRESH/confirm/source_clocks.json` |
| `view_plan_ref` | `FRESH/confirm/view_plan.json` |

`required_files` 还须绑定 `FRESH/confirm/inputs_01/implementation_closure.json`（digest等于成功 primary completion 的 `implementation_closure_sha256`），以及诊断 `bindings` 中每个文件，包括原 `first_input_qa.log`。原 primary `registration_sha256` 必须仍等于 **原注册** SHA，不改成新 v2 注册 SHA。

启动前一次性核实际 first QA 输出目录、CPU acceptance/source lock、B0/VERIFY GPU/replay/admission、MAIN 的 confirmation registration/POSITIVE/comparison 均不存在，原/新 GPU jobs 均无终态；只支持已诊断的 zero-first-QA/zero-model 状态。该检查只在父链首次启动执行；之后合法成功阶段不触发隐式重启。

## 唯一顺序修复

`unique_view_plan.unique_views` 顺序为全来源 baseline 后全来源 overlap；成功 primary 原程序逐来源循环，再在各来源内筛原计划视图。v2 按以下原生产顺序校验，**不修改或排序成功 entries**：

```python
expected = [view for source in accepted_source_order
            for view in original_plan if view['source_name'] == source]
```

来源数必须恰为4，case集合完整唯一，来源顺序和每源原计划顺序都必须精确一致。新独立 QA 仍核源、case、原时钟、native64、PNG/NPZ像素、每case真实 smart_resize geometry、primary证据、实际独立 processor 与cache逐比特一致；每例首次独立 evidence 在比较前立即保留。全部28例真实首次QA完成后才能GPU。

其余 B0/conservative VERIFY/positive 串行控制和GPU后output-only QA延续v1；正面准入调用原冻结 `MAIN/code/positive_*.py`，不改原science或prompt。末尾首次四源八门比较只到待fixed40的PASS或STOP，不启动fixed40/426/ZIP/Goal/自动化。

## 本地检查

```text
python -B improvement/recall_positive_fresh_recovery_v2/check_pure.py
```

已通过实际顺序缺陷的合成复现、原正确来源分组顺序PASS、重复/缺失/源内乱序/错误case或来源拒绝、不修改原entries、恢复authority不变和QA已开始拒绝、prepare硬拒绝、原native64/sourceplan/容量数学与GPU前首次QA/GPU后output-only检查。12个Python文件AST检查通过；这些纯检查不代替Linux真实首次独立QA或模型科学验收。
