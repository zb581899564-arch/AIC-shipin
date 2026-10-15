# 首次QA前顺序错误：仅剩余阶段恢复审查

2026-10-15。只读审查新增 `improvement/recall_positive_fresh_recovery_v2` 与主线程的小量失败诊断；未SSH、读取真实张量/媒体、执行QA/模型或部署，未改旧代码、旧协议、媒体入口或旧审查文件。

**结论：新v2恢复静态范围正确，可由主线程在实际注册闭包和无旧活动任务核验后，仅启动尚未执行的首次独立输入QA及后续链。不是实际恢复成功、确认八门或固定40通过。**

## 失败与成功边界

`fresh_plan_failure_diagnosis_17.json` 记录sources_equal=true、plans_equal=true、entry_order_equal=false、differences=[]。生产者 `prepare_inputs.py` 依accepted四来源循环，再筛选同源plan视图；`unique_view_plan` 本身却按全体baseline后全体overlap排列。因此两种列表次序不同，不代表原source、PTS、窗、采样或输入内容不同。

实际小回执 `fresh_remaining_recovery_diagnosis_17.json` 绑定原registration、primary completion、chain_01 failure、首次QA日志、source_clocks和view_plan SHA；记录完整28个primary started=returned、四源、原plan未变、逐case视图身份相符、源分组完整次序匹配。首次QA输出目录不存在、证据数0，B0 GPU目录也不存在。回执中的source_RGB_decode_completed为null，不把该字段单独解释成4次成功；新注册验证另从实际primary completion强制actual_new_RGB_decode_passes=4。

旧 `first_input_qa.main` 的错误列表相等检查位于输出mkdir、processor载入、runtime.encode之前。该位置与QA目录不存在/0证据相符，说明28个primary和4次RGB需引用，而后续28个首次独立编码仍是真正未做的必要QA，不能因为“primary成功”省掉。

## 新恢复的限定修改

- 新注册名 `positive_fresh_recovery_registration_v2.json`，状态 `REGISTERED_POSITIVE_FIRST_FRESH_REMAINING_RECOVERY_V2`，代码目录限定 `fresh_01/recovery_v2/code`。原 `positive_fresh_registration.json`、原code、primary及其implementation closure全部保留并纳入新required_files，不覆盖旧成功或旧failure。
- `validate_recovery_documents/validate_remaining_recovery` 绑定原28输入/4RGB、QA0、原失败阶段、独立诊断及其全部bindings，source_clocks/view_plan/reference completion与原primary记录逐字段相等。protocol、authorization、dev结果/selection、source登记、冻结positive代码、容量合同、deadline、实际模型/优化器、source scope和生产未准入均与原注册精确相等；三个GPU阶段预算不变，仅改为不同、未启动的新v2作业名。
- `validate_source_grouped_order` 按accepted原四源次序，在**原plan内部**保留各源原视图次序构造期望列表；严格比较case_id/source_name完整序列并查重、查完整分母。它不排序或重写旧entries、不修改旧plan。随后逐case再绑定原窗端点、source SHA、完整PTS、采样ordinal/PTS、view roles、输入路径/SHA和primary proof。
- 新 `fresh_chain` 使用 `confirm/chain_02`，先一次absence检查，要求QA、CPU acceptance、源锁、旧/新GPU产物、VERIFY及父positive确认文件均不存在；旧/新GPU自然终态也不得已存在。链直接从first_input_qa开始，没有prepare child；新prepare函数入口主动拒绝调用，防止误重做RGB/primary。实际旧父/子进程退出与共享账本/active状态由主线程部署前核实，静态文件不能代替实时核验。
- 第一次输入QA从原PNG/NPZ/primary cache独立核位并产生新的QA proof，完成28个后才B0。VERIFY及严格positive首次token QA仍在各自GPU之前；GPU后只读已完成输入QA证据及cache并检查新输出token/grammar/parser/native，不重复encode/retarget。最终仍由冻结v2 positive合同与原八门首次评价新4源。

## 最小独立验证

本审查者执行了不接触真实数据的独立comparison fixture：四源、每源baseline/overlap构造可重现role-major与source-major顺序差；正确生产者顺序通过，检查前后plan/entries不变。六类错误均拒绝：原role-major、缺entry、重复entry、源内换序、foreign case和foreign source。真实小诊断的primary28/QA0字段也与上述失败边界一致。

另独立AST检查12个新Python文件，通过；确认chain02先absence再建目录、无prepare child、prepare首语句硬拒绝、B0/VERIFY首次QA均先于GPU、两个GPU后replay无encode/retarget调用。运行器代理另报告自身纯恢复权限/预算/deadline不变与QA已启动否决检查通过；未冒称本审查重新执行其完整测试。

本审查范围内无剩余静态致命阻塞。新注册尚须实际绑定完整原证据及新源码SHA并通过；后续QA或模型实际失败须保留新失败及已成功项，不自动重试、换源、改变门或回写原终态。本文件不宣称已发生任何恢复计算，也不授权新确认之外的事实/426/封包。
