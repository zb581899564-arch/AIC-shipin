# Positive fixed40 第一层 B0 上界独立审查

结论：当前 `improvement/recall_positive_fixed40_v1` 未发现剩余静态致命问题，可保留为条件性准备。原“17 个合法窗口”不足以证明完整覆盖的缺口已经修复，并通过纯合成反例检查。本审查不构成部署或运行许可，不是实际 fixed40 事实 PASS；没有取得或查看媒体，没有 SSH、解码、重测 clock、模型调用或重跑旧成功 audit。

## 充分条件及结论边界

设 O 为原完整银标的 222 个已观测 ORDINARY 原生点，P 为所有可能覆盖 O 的原完整 15 秒、7.5 秒步长窗口及精确右尾窗所产生的实际 B0 proposal 原生帧并集。冻结 positive 规则只从同端点 B0 proposal 的保守 VERIFY 显式 KEEP 中再次准入，故真正新增集合 A⊆P。若 P∩O=∅，即可充分证明 A∩O=∅，这一步不需要重推 old40 baseline30、VERIFY 或 strictpositive。

若实际 P 触 O，本层只能输出 `INCONCLUSIVE_PENDING_REGISTERED_VERIFY`，不能改成失败、空结果或事实 PASS。后续保守 VERIFY、实际基线及 strictpositive 的条件性最小范围沿 review16，必须另有明确注册；本运行器没有自动启动后续层的入口。D8 不可替代实际 VERIFY40.46 基线。

冻结 union 规则提供“实际基线不删除”的结构依据，不等于已经证明原 184 个 KEEP 全覆盖，也不是最终 426 帧/框保持验收。原 reference coverage/reference quality FAILED、2675 UNKNOWN 及其语义仍保留。

## 关键完整性缺口及修复

初读发现，仅验证 9 来源、17 窗、222 点数量及每窗合法，仍可漏掉覆盖 O 的重叠窗。例：end=30、O=10 时，[0,15) 与 [7.5,22.5) 都必须纳入；用合法 [15,30) 替换后者，数量不变仍会漏证。这是上界充分条件的关键缺口。

当前 `registration.validate_complete_covering_grid` 从绑定的原 clock、physical end 和完整 O 独立重建 zero-origin 全 grid 与 exact right-tail，按半开区间筛出全部触 O 窗，再要求 `(source SHA, clock SHA, exact start, exact end)` 集合与注册集合完全相等。不同 case ID 下的重复几何也拒绝。`metadata()` 在任何 prepare 前强制执行此校验。这是新计划的纯集合 QA，不会执行旧 source audit、clock 测量或 decoder。

实查其覆盖 end31/O20 的三个窗口 [7.5,22.5)、[15,30)、[16,31)，不会以右尾代替早先重叠窗；end30/O15 的右端半开及尾窗去重处理一致。

## 注册、调用及输出闭包

- `source_audit_plan_ref` 与 completion/code/reference refs 均必填且纳入 required_files；缺文件/SHA 不符即拒绝。当前没有现成持久 plan 可冒充已运行产物。只能在新四源实际八门 PASS 后，由主线程从原 clocks/descriptors/银标生成新的不可变 metadata snapshot，并执行上述首次纯集合 QA；不运行旧失败方向 deploy/launcher，不重测 clock。
- 注册要求当前 positive v2 的实际 dev、首次 fresh confirm 两份各四源结果、原八门全 true，并绑定实际注册、chain、模型身份、唯一调用 journal、自然 GPU 终态和首次 output QA；旧 consensus PASS 或任一 STOP/失败门不能替代。positive 实现文件与实际两阶段 required_files 精确一致，原 fixed40 零 KEEP 删除/零 ORDINARY 新增门不变。
- 全 17 窗必须按明确 NEW/ADOPT 计划闭合。ADOPT 要求同 source/clock、完整原视窗、native64、prompt/tensor/model/raw/原 QA/成功终态的精确身份；仅几何相同不足以复用。NEW 先 primary，再独立真实首次 input QA，全部通过后才新共享 GPU。GPU 后只进行 token/grammar/parser/native 的 output QA，不再 encode/retarget 输入。
- `fact_check` 要求完整唯一的实际成功输出及对应首次 QA/raw/request/native 绑定；缺失、重复、工程失败、非法 EMPTY、时域/原生点不一致均拒绝，不转 UNKNOWN 或空。只给 `B0_UPPER_BOUND_SUFFICIENT` 或未决状态，明确 production=false、next_level_started=false、complete_positive_recipe_executed=false。

## 本次实际验证与未验证项

只运行 `python -B improvement/recall_positive_fixed40_v1/check_pure.py`，PASS；其合成 9 来源/17 几何/222 点夹具覆盖合法替换、漏窗、重复几何、错 clock、精确右尾、半开边界，以及 sufficient/inconclusive/失败拒绝和 fresh PASS 权限。另以独立小夹具检查 end31/O20 三重覆盖、同数量合法替换拒绝、重复拒绝及短于 15 秒来源；PASS。9 个 Python 文件 AST 解析 PASS。没有运行真实 facts 阶段。

执行前仍需实际 fresh 八门 PASS、新完整 source plan 与全部真实依赖冻结、逐窗精确复用核对及当时资源判断。当前不能报告实际 P 避 O、事实已通过、old40 FAILED 修复或可以进入 426。
