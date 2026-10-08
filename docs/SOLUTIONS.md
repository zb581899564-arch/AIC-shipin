# 方案、证据与当前状态

## 当前教师工程修复与真实接续

32B教师完整160标签与160盲第二选择已真实完成，132新复查、28原成功精确复用，工程失败0。弱支持正65、空14、UNKNOWN81；实际支持65train/14dev，全部160分母与原raw保持，同教师一致性不是人工真值。V13学生CPU准入错误拒绝原pilot24的diagnostic标记。V14在独立exact manifest下仅允许原pilot24精确成功回执跨阶段，原标记/STOP/成本不改；旧consumer失败、新完整160 consumer与11拒绝合同已真实CPU验收，不重复教师生成。当前实际阶段 `SOURCE_PREFLIGHT_CPU_PENDING_REGISTRATION`，新8B T实际更新0，没有新最终ZIP，新官网分未知。原B37.63与B2用户37.32/DONE继续绑定各自旧ZIP。见[协议](../reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/teacher_student_autopilot_v14/PROTOCOL.md)与[聚合验收](../reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/teacher_student_autopilot_v14/aggregate_stage_handoff_acceptance.json)。

<!-- END_CURRENT_V8 -->
## 当前自主B2接续

2026-10-08 09:45 UTC+8：当前路线为[B2已微调8B生产对齐](../reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/b_score_aligned_package_v4/CONTINUE.md)。保留已评分37.63的B最终LoRA，不增加训练更新；时间使用B adapter、空间同8B原生基座，总逻辑参数8,782,459,120。B2采用所有分支实际native PTS/floor64帧/顺序PyAV/16384长输入、精确端点与全源空间场，仍用B原1–5段提示与greedy。旧37.63仍绑定旧B包，B2用户回报官网37.32/DONE。

32B context v3已经完整8/8真实请求、0工程失败，三正被弱审核支持，唯一NO被拒绝；没有受支持真实空例，T更新0。审核声称overview仅到119.0189秒，实际完整源回执末PTS149.98316666666668、13帧>=120；事实性错误和语义争议同时保留，不能将拒绝改PASS或空标签当真值。旧raw/失败/科学STOP保存；不再盲试同配方，不造空或弱化原监督门。B2是保留已经训练B的可交付路线，不冒充新教师T训练。

69项CPU、434来源/529真实自然窗/33447样本端点、12原目标无损回放与实际processor/HD/8非测试源重开pixel SHA通过。571文件锁 `52363b5a6f452ac01a55474eacf6529b80e7c4e4ec3e99868f7d91162fae27db`，单次launcher历史PID `3965729`；本次快照阶段 `PASS_COMPLETE_426_B2_8B_ZIP_ON_LINUX`、实际命令进程 `0`。实际B LoRA长输入CUDA已PASS：12048token、288 adapter张量与保存值相等、全基座SHA与原训练相等，选择token分数有限；0优化器更新。Linux最终ZIP终态与NONTEST8/426全部独立strict登记已PASS。包 `/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/b_score_aligned_package_v4/rematch_01/candidate_B2_8B.zip`，实际 `317401` 字节，SHA256 `0f8c95f01222a28a053e6f80b76b3d4d7ac3dc82077f4dd533605337bc6883a3`。B2已交付，用户回报37.32/DONE。

旧Z时间实际adapter=False，521旧时间不能复用B2。非测试全源CPU/同基座空间只在输入/算法/关键SHA与完整回执一致后原样复用；复赛旧CPU域与新native源域不同，不准入复用，真实重算全源CPU/空间。后台真实B长输入CUDA→NONTEST8→426/521时间/全源空间→独立strict ZIP。最终只有真实B2 completion PASS、8/426独立strict全部true、大小/SHA/CRC/唯一JSONL/426身份验收才可提交。

最终ZIP已完整验收，本轮巡检在交付时结束。Linux后台独立运行，本地巡检需要Windows开机且Codex运行。最终只有一个选定ZIP留Linux，不自动回传或AIC上传；新大流量先许可、Mac退出，实际容量与共享GPU锁/账本/7200保持。见[B2决策](../reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller/NEXT_ACTION_B2_20261008.md)、[协议](../reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/b_score_aligned_package_v4/PROTOCOL.md)、[实时接续](../reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/STATUS_AUTOPILOT_20261007.md)。

最终实物ZIP、8/426身份与全部strict、31,295个真实锚点及GPU追加账本已独立复核，见[最终验收](../reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller/B2_v4_final_acceptance_20261008.json)。

v4保持canonical时长修复，新加SHA绑定的97送模型前log316/errno95转换修复：临时UNSPECIFIED transfer/限定范围ITU601样本映射后恢复frame元数据，原源/YUV/range/尺寸/PTS不变，不声称恢复摄影gamma曲线。其他源默认转换保持，9转换CPU/64实际帧RGB与空间BGR完全对应、69原CPU/实际processor/8非测试pixel SHA通过；11独立所有权mock及6实际失败分类CPU通过。v1有效GPU计算不打断，v4新NONTEST8后等待完整provider和记账，所有成功原validator/输入/SHA核验原字节保留，只为登记送模型前错误真正生成一次；旧失败STOP保留，不转空/减426分母。见[显式转换与恢复](../reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller/B2_COLOR_RECOVERY_20261008.md)。

v4另修复恢复失败证据丢失：新返回原文先写独立且不可覆盖raw，再做有效性校验，异常另记failure/traceback；3项CPU验收无效原文保留/有效原文保留/重复覆盖拒绝通过。v3只停止等待controller，未开始恢复GPU，旧锁与产物保留。冻结源码不回写，生成/色彩/时间配方保持v3，不重复任何成功推理。

完整426/521时间已PASS、无效0；原425成功记录整行字节/520成功窗口相等，仅为已登记送模型前失败实际新生成1窗MODEL_OK，原失败和STOP保留。原raw与接受窗、全部分母及NONTEST8/11 strict均经独立验收；实际GPU费用单独按wrapper账本核。见[真实恢复验收](../reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller/B2_v4_recovery_acceptance_20261008.json)。

## 复赛 A：4B / 33.81

沿用已训练 P2-T2 时间 adapter，以未微调 Qwen 做空间定位。复赛共有 426 视频、521 时间窗口；CFR/native 时间戳分支保持源身份。受约束 JSON 生成恢复原解析失败；空间随机定位的 8 个身份失败以顺序解码补算，原成功对象保留。

完成 93,155 个所选帧、13,022 个空间锚点、严格 ZIP 与 Mac 跳板回传。用户报告官方 **33.81**，绑定 SHA `5b8a186eefc2d162d65f76267979b57a6fbb94ea64fd26461f13270acb66e313`。原失败 receipt 保留，不因最终恢复成功将旧运行改为 PASS。

## 复赛 B：Linux 8B / 37.63

固定 Qwen3-VL-8B-Instruct revision，r16 语言 LoRA，区间 JSON 的 assistant token 交叉熵 SFT；仅使用已知正窗口，不将 UNKNOWN 作为负类。固定 5 轮 / 3620 有效 backward / 227 更新，最终 adapter SHA `8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23`。视觉与基座冻结。

104 视频、96 来源组、112 窗口的单次固定弱开发：BASE 组宏 F1 `0.3426182206`，SFT `0.6850031671`，配对增量 `0.3423849465`，95% CI `[0.2589075960, 0.4246593239]`。BASE 有 36 解析失败，SFT 112/112 有效，两臂推理工程失败均 0。增量包含格式改善；100 confirm 未读。

v1 在容量时间戳兼容处停止。v2 NONTEST8 通过，但误将训练 8192 token 界用于比赛推理，81 个窗口在 generate 前被 guard 拒绝。独立 v3 将生产界登记为 16384，合成 64 帧 HD / 12048 token GPU 验收通过；旧 14 个成功窗口保持不变，其余按协议处理，不降帧或截断。

最终 426 视频 / 521 窗口、101,985 帧 / 13,947 锚点完整严格通过，2026-10-06 21:41 UTC+8 本机回传验收完成。用户截图显示 **37.63 / DONE**，比复赛 A 提高 **3.82**，ZIP SHA `86bd5301f6f6771a8451b32063781e214cdd70245ae5513f2a767eaecb9ebe54`。截图不完整，完整时间及名次未知；具体 ZIP 依据用户指认和对话交付记录绑定。

## Mac 独立 8B：低分辨率 64 帧 / 33.46，已停止

最初 128 帧 MPS 方案内存不足，修复后的 v7 工作集仍超过当时 live MPS 建议值，停止并保留证据。改为 64 帧、显式每帧 ≤32768 像素、6144 token 的 v8；保留 r16/lr5e-5/5epochs/704训练视频/724正窗口/602来源组。MPS 修复包括局部 FP32 DeepStack 索引加和、严格 feature/token 掩码与逐样本缓存释放。

2026-10-06 22:15 UTC+8 完成 3620 有效 backward / 227 更新及冻结、重载验收。最终 adapter SHA `1baa14a96d30d3836478295752c0b932f40f811863c28db99b56102fcfa1d5b5`。

最终 adapter 转移到 Linux CUDA 评测/推理。交付 v1 因 Linux 目录误检查导致两臂均在解码和 generate 前失败，实际开发生成为 0；保留 STOP。独立 v2 修复目录检查，新旧输入合同 SHA 相同。

2026-10-07 00:07 UTC+8 查询：固定开发 PASS，BASE 组宏 F1 `0.3031034002`，SFT `0.6499916173`，配对增量 `0.3468882171`，95% CI `[0.2608539784, 0.4331386393]`。SFT 112/112 有效，BASE 44 解析失败，推理工程失败 0。NONTEST8 已通过 8 视频 / 629 帧完整独立严格门。此前为复赛时间推理阶段。2026-10-07 10:27 UTC+8 再次核验：完整426包已在03:12完成、03:14回传独立验收；101880帧/14007锚点，SHA `7f49ff90b5a21fd71a6036d8da0a1b78f3ab9c1d900ab2f81bc1f319e9d4533d`。大小、SHA、CRC、426记录与11项独立strict全部通过；当时尚无官方分数。随后用户截图确认 **33.46 / DONE**；比4B低0.35、比Linux8B低4.17，包SHA不变。用户要求停用Mac，工作根26.13GiB占用已在重要资产核验备份后删除；只保留12KiB说明/启动文件，Mac不再参与计算或传输。

两种 8B 的开发输入不同，不能依据上述 F1 对它们直接排名；硬件、像素预算、解码后端同时改变，不作单因素结论。它们都使用同一 8B 共享基座，全链逻辑参数 `8,782,459,120`，没有叠加独立 4B。

## C：稠密二元头 / STOP

计划优先探索稠密时间分数，但教师材料缺 prompt、完整观察范围与原始响应证据。未选范围是 UNKNOWN，不能直接标成 0，因此正式 BCE 未准入。三次合成更新与成本探针只证明工程连通，不是正式训练或高光质量结果。当前不能用同监督 4B 头或伪负例绕过此门。

## 初赛历史

- 未微调单片段和多片段 reader 官方 41.09、41.22。
- 历史 LoRA reader 官方 43.48，用户报告；完整对应 ZIP 已归档。
- P2-T 首轮弱开发不通过；P2-T2 固定 5 epochs 后通过一次弱开发，成为 P2-Final 时间组件。
- P2-Final 官方 43.94，用户截图显示名次 30；比 43.48 增加 0.46。
- R7 时间池最终开发门不通过，停止，保留 P2-T2，未生成可提交 R7 官方结果。
- 空间 LoRA 小试弱 IoU 下降，停止完整空间训练；后续空间链冻结未微调 Qwen。

详见原始 `ROADMAP.md`、各版本 `PROTOCOL.md`、`decision.json` 和报告。目标 50/55+ 是项目目标，尚未达到，不是收益承诺。

## 下一轮Z/T/S（2026-10-07）

独立next_round_v1已修坐标单位、合法空、空目标/原生PTS、统一生产输入、完整源空间场及离线Mac容量。145主合同与19选择器合同通过；真实processor旧默认逐张量一致、全空426独立strict和实际CUDA有限空CE通过。Z为原生8B、保留B的时间提示与受约束解码，但空间实现同步修复，因此官网比较是整套配方比较。一次性Linux接续已通过B/Z同输入工程开发及NONTEST8完整门，11:22 UTC+8实查处于426条时间推理；新独立直连交付等待替代Mac桥接，运行源码/配额不修改。当前Z无已交付包/官方分。

T模板从既有B adapter续训、lr1e-5、最多3epochs，但首批完整窗口无真实标签，32B权重需19.52GiB。此前合计容量不足；Mac清理后未来容量投影通过。用户随后明确取消所有项目磁盘、RAM、VRAM人为额度，有效策略ACTUAL_CAPACITY_ONLY已生效；新作业不再继承旧80/51GiB配额。教师固定权重已开始Windows暂存下载，Linux项目内CMake修复配置PASS、CUDA运行时编译中，新桥接自动在资产/Z完成后直连上传并全SHA复核。教师仍未实际加载、新标签未生成、T尚未训练。supervision_v2独立一次CPU已验收选择128/32，修复无新PTS的duration-only尾格并保留其证据。S无已绑定双比例构图参考，继续STOP。所有旧包/成绩保持。

详见next_round_v1/PROTOCOL.md、EXECUTION_STATUS.md；官网每日5次、取最高有效分，内部弱F1仅机制诊断，不复刻官方总分。
