# 本轮实际 CPU 检查与未运行事项

本目录的 [CPU_RESULTS.json](CPU_RESULTS.json) 和 [CPU_RESULTS.log](CPU_RESULTS.log) 是最终代码闭合清单上的**实际合成 CPU 运行**；[TORCH_CPU_RESULTS.json](TORCH_CPU_RESULTS.json) 是实际尝试新 Torch 门的回执。它们不是 Linux 视频实验，也没有提供新候选的质量证据。

最终统一检查：**111项通过，0失败、0错误、0跳过，29.213066秒，退出码0**；Torch未导入。代码清单绑定26个新Python文件及配置，另逐字节绑定32个继承依赖，清单SHA256为 `d91ece392be1a59a42027fd9a61c497be002e5a618bb9deb6dc0c74bfba5301b`。独立 Torch 命令中的30项pure另通过，13项真实张量检查因本机缺依赖未执行。

## 已执行的范围

标准库与 NumPy 使用真实运算和临时文件，包括整源候选组合、Fraction 原生窗口、来源均衡 ridge 的独立解析/最小二乘对照、LOSO 留源隔离、权重实际保存重读、全部评审/来源宏评价、候选上限和独立停止条件。最终数量、用时、Python/NumPy版本与失败/跳过数以 CPU_RESULTS 为准。

关键反例包括：

- 一个来源有6对、另一个来源有1对且偏好相反，正确来源等权回归斜率为 `-75/226`；按pair数量池化会得到正斜率。
- 同时改变留出来源的特征与全部参考，其 LOSO 折拟合权重 SHA 不变；它进入最终拟合时权重会改变。标准化也只用各折训练来源。
- `2 - 10^-40` 属于 `[0,2)`，精确 `2` 不属于；不能先转float再做原生窗判定。
- 整源只能选同一slot的完整并集；逐窗口GT oracle混用不同slot得到的高分不属于候选。
- 原TIME非空、评审有选择时，新空输出记作false empty；即使保护外部代理为空也不能隐藏这个变化。
- oracle、训练拟合分、旧 DPO 的真实参数变化或胜过较弱基线，都不能替代三路各自的生成/排序/对照门。
- 已完成原 DPO 的绝对 chosen/rejected 概率可以同时下降而相对差上升；只读诊断保留原 STOP，重复16对身份不能静默去重。

正式采用测试使用完整合成426来源/522窗的实际文件 SHA 链与独立 BASE 哨兵，保留真实 JSON/EOS/合成 tokenizer 往返及 native PTS 解析，禁止模型调用。**真实 Qwen tokenizer/grammar 边界在该测试中明确 mock，不能作为 Linux 通过证据。**43原控制测试明确 mock 原采用函数，只检验一次委托、覆盖与失败传播。

renderer 测试真实运行继承的 field/PTS composer、独立 subprocess、11项严格验证、两种比例和 ZIP 往返，输入为合成426来源，测试中保护身份显式替换为合成 ZIP。它没有读取实际官方视频、权重、标签或生成新的正式提交包。缺源、FAILED、空间域排除、原生时钟漂移、过期批准和 canonical 零差异都拒绝。

driver 测试保留真实 admission/selection 接口，重依赖明确 SYNTHETIC Mock：正式资产核字节在加载模型之前；环境变更在采用/调用之前拒绝；package向renderer传完整批准文档而不是文件ref；NO_EFFECT允许新增provenance，但任何原输入字段改变都会阻止复用。正式池复用测试另核原完整pool、独立critic批准、0新模型调用和原费用不重复计算。这些测试不制造522个真实模型回答的“PASS”。

## 真实 Torch 门未在本机运行通过

当前环境没有 Torch。实际执行统一命令得到 `status=NOT_RUN`、真实 `torch_checks=0`、退出码 **77**；pure检查通过不能把它转为PASS。Linux必须运行当前闭合代码的**30项pure＋13项真实CPU Torch**，没有skip或fail，版本/代码ref一致，才允许新Qwen阶段。

13项真实张量门覆盖实际CPU signed-hash投影、完整组移位、teacher-forced全suffix概率求和、预测EOS的真实causal位置、随机状态隔离/恢复、参数无梯度/冻结、FP32 checkpoint重载、输入hidden维度以及观察像素/PTS/预算；新增观察prefix保存重载、改字节、重绑错误prefix SHA和删除文件均必须实际被拒绝。它不会装载Qwen或CUDA。

## 开发过程中保留的失败与修复

首次单独运行 `test_verification` 时共13项，其中12通过，1项因**合成测试fixture**把负例命名为已存在的 `frozen.json` 而报 `FileExistsError`。原排他写入行为是正确的，未放松；仅把负例文件改为独立的 `changed_frozen.json`，受影响测试和其余12项重新运行13/13通过（0.043秒）。这不是资产或模型小试失败，也不描述成首次整套全通过。

最终汇总时，一次把 `torch_checks.py` 误当作独立脚本路径调用，先因包导入报 `ModuleNotFoundError`、退出1，未创建张量门回执。随后采用 RUNBOOK 已规定的仓库根 `python -m improvement.content_choice_v1.torch_checks` 命令，得到实际缺 Torch 的 `NOT_RUN/77` 回执。没有修改门或安装依赖来把它转为通过；手册同时收紧了“所有入口支持绝对路径”的不准确表述。

交叉审查中修复的新实现问题：跨窗选择缺少实际PTS约束、同sid错误来源SHA可混入评价、NO_EFFECT整字典比较受新provenance影响、生产selection额外字段与renderer严格schema不符、admission ref/document传参混淆、正式新资产加载前预检不足、跨阶段runtime identity未完全绑定、观察新prefix缺少落盘重载核验。相应直接回归已纳入本目录；没有修改40.47依赖或重新解释旧实验为成功。

原 PR #1 的 `python -B tools/check_review_regressions.py` 另实际执行通过4组原有合成CPU程序。新入口也从非仓库cwd/不相关PYTHONPATH以绝对脚本路径实际执行 `--help` 成功，验证原wrapper切cwd不会把本轮入口误导向旧checkout；没有启动wrapper作业。

`python -B tools/verify_publication.py` 实际得到 `PASS_PUBLICATION`：6694个生效清单文件、3707个Python语法文件、8个原有历史归档，source hashes / ZIP CRC / 排除资产扫描 / secret pattern扫描均通过。旧 publication_manifest 原始字节不变，新字节只加入 publication_updates 覆盖层；现有文件只修改根README导航与覆盖层。

40.47保护ZIP本体不在此公开checkout或其8个归档登记内，本轮没有重新读到或计算其真实字节SHA。一次尝试在公开包登记中定位该SHA因条目不存在而未完成，随后确认了此资产缺口；上面的8个历史归档通过不能替代40.47本体校验。保护ZIP及私有复现依赖须在Linux按既定384630字节/SHA和原manifest重新核验；仓库中所有旧代码、旧根计划/手册和冻结记录与f343起点无差异。

## 未运行，不能由这些检查代替

新真实私有资产/权重/patch/参考验收、43/522原控制实际再核、新 Qwen greedy/sample/TF、25真实来源 critic 拟合、LOSO/跨数据集真实指标、观察重分配的真实输入效果、费用/峰值显存、正式426生成/复用、正式封包和官网提交，全部尚未运行。

已完成的旧 DPO 工程和 STOP 仍以 [PILOT_RESULT_20261019_01.md](../native_preference_v1/PILOT_RESULT_20261019_01.md) 为准，本次合成结果既不否定其真实执行，也不能把其科学 STOP 改成成功。
