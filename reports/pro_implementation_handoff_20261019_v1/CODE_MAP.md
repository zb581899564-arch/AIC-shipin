# 从机制到真实入口

以下路径相对仓库根。历史脚本包含Linux绝对路径和过期deadline；仅阅读，不直接运行。资产并未包含在GitHub。

## 保护基线40.47

- `improvement/score_residual_runtime_v1/semantic09.py`：语义头训练/外部OOF。
- `improvement/score_residual_runtime_v1/features.py`、`prepare.py`：原表示与映射。
- `improvement/score_residual_runtime_v1/production_semantic10.py`、`production_semantic_apply10.py`、`production_semantic_package10.py`：正式特征、受控补选与封包。
- `improvement/score_residual_runtime_v1/semantic_head_controller09.py`、`semantic_chain09.py`、`production_semantic_chain10.py`：阶段连接。
- 原TIME训练及空间基础在 `reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/` 相关历史代码中；不能仅看小头就宣称原8B没训练过。

## BCE / soft-F1失败时序头

- `improvement/temporal_selector_v1/features.py`、`mapping.py`、`head.py`、`train.py`。
- `recovery_02/train_v2.py`、`recovery_05/train_resume_v3.py` 为后续实际工程版本，`package_04/package_v4.py`为对应打包。
- `reports/temporal_selector_20261018_v1/POSTMORTEM_9_74_9_31.md` 是完整方案失败，不应再把相同头/损失称作新方向。

## 10月19日整源SFT与纠偏

共同目录 `improvement/bottleneck_24h_v1/`：

- `summary_contract.py`、`summary_context_pixels.py`：真实Overview/Excerpt patch组合、video grid/时间组/文本。
- `target_contract_feasibility_v3.py`：原人工逐评审目标的native可表达性；不是模型能力。
- `prepare_summary.py`、`summary_runtime.py`：缓存绑定、真实label mask与causal shift。
- `summary_gpu.py` → `summary_gpu_remaining11.py`：4步工程pilot后接remaining555，原序列CE。
- `summary_generate.py`、`summary_grammar6.py`、`summary_output.py`、`summary_output_qa.py`：同合同生成、约束、拒重复键/NaN、输出复核。
- `evaluate_summary.py`：原生帧、重叠去重、逐源/全评审时间代理与覆盖对照。
- `objective20/summary_gpu.py`：唯一固定token normalizer损失对照；其余同目录为真正绑定的复制版本，不能和父目录任意混用。
- `objective20/final_training_qa.py`、`objective20/run_after_training21.py`：完成后的首次核查与比较，不是当前任务。
- `prepare_summary_formal.py`、`summary_formal_generate.py`、`package_summary_formal.py`、`run_summary_formal.py`：原失败训练路线的**未准入条件生产代码**，文件存在不代表曾执行或仍允许执行。

## 精确诊断28–40

同一 `bottleneck_24h_v1/`：

|问题|源码|
|---|---|
|目标/grammar实际路径|`diagnose_underselection28.py`|
|相同输入、两个adapter规范路线概率|`probe_decision29.py`、`review_probability29.py`|
|完整损失与分支梯度|`decision_gradient32.py`、`review_gradient33.py`|
|逐评审完整文本的模态|`modal_target_audit34.py`|
|step559保存动量局部方向|`adam_direction35.py`|
|同g/v/step保留与清零m的一步对照|`one_step_momentum37.py`|
|候选概率、自由输出和首次复核|`evaluate_one_step38.py`、`review_one_step39.py`|

诊断未证明唯一因果；不要只看到`adam_direction35.py`就再次跑已经失败的一步修复。

## 音频

- `bottleneck_24h_v1/audio_hypothesis22.py`：已有DSP诊断；非音频语义模型。
- `audio_semantic23.py`、`audio_visual23.py`：固定Tiny下载/转录/新用途输入。
- `run_audio23_remaining24.py`：仅恢复文件名404的剩余控制，不重下已成功对象。
- `run_audio_visual25.py`：固定4新ASR文字调用与原视觉采用。

## 最新正式1044回答及五包

`improvement/five_summary_sprint_v41/`：

- `base_pilot41.py`：43回答后末尾flags失败的冻结原实现；保留此失败代码，不包装为成功版。
- `review_pilot_remaining42.py`：只采用43 raw的首次CPU开发诊断；原GPUfailed状态保持。
- `prepare_formal41.py`：426/522首真实CPU输入。
- `generate_formal41.py`：原TIME和关闭adapter的BASE两角色；每次实际Qwen forward核144层角色flags，退出PEFT显式恢复冻结flags，核原TIME288矩阵及BASE末hash。
- `qa_outputs41.py`：1044首次独立token/grammar/parser/native输出复核。
- `package_five41.py`：五个冻结集合策略、原生域/旧空间场交集、真实模型计数、独立格式与历史差异检查。
- `run_formal_chain41.py`、`complete_packages43.py`：有限链及封包连接。
- `finish_windows_remaining45.py`：只接剩余最终ZIP，不往返raw。

`register_start_formal41.py`中96CPU为当时描述笔误；实核32逻辑CPU，注册线程4没有改变。新协议应按当前机器实测判断，不沿用固定资源准入线。

## 其他已完成历史

`diagnostic_score_goal_v1/`含实际排名、ROI、direct box、trust region及原作者query接口研究；先读阶段结果142，再找相应源码。`source_consensus_event_v1/`、`relative_precision_event_v1/`、`meaningful_event_residual_v1/`为此前残差/双向视觉/音画过滤，不能因名称不同重复。

## 已有审查修复仍保留

- `improvement/midnight_five_package_v1/package_math.py` 与 `check_pure.py`：媒体身份绑定。
- `improvement/midnight_production_unique_v3/mf_common.py` 与 `check_pure.py`：真实路径边界。
- `tools/verify_publication.py`、`check_publication_updates.py`：冻结快照与增量清单。
- `python -B tools/check_review_regressions.py`：四组隔离CPU回归，不依赖GPU或媒体。

新增方案宜新建独立目录和显式配置，不再自动寻找“最新vN”，不改旧代码/输入锁来冒充新结果。
