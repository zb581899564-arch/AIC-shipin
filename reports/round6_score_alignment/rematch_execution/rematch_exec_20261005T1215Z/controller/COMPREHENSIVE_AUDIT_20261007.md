# 教师→8B→提交包全链核查（2026-10-07）

本次按用户“全面核查，有问题立即解决”授权进行。审查了教师请求/实际 grammar/原 validator、标签到学生序列化、输入身份、优化器/检查点、开发与生产解码、成本准入、进程所有权和最终交付门。工程修复先在独立 v6 复现、验证；v6 不启动已知质量失败的任务。当前 v7 冻结后只运行真实十二窗配方校准。旧运行源码、原始回答和失败回执保留。

## 已证实并修复的问题

| 问题及影响 | 修复 | 验证证据 |
| --- | --- | --- |
| 教师真实 PTS 有 6–15 位小数，学生旧 serializer/grammar 只允许 4 位；12 条真实目标中 11 条被拒绝，不能进入微调 | 用 Decimal 从原值精确序列化，最多 18 位；学生生成 grammar 与严格 parser 使用同一数值合同，不对旧标签舍入 | 10302 个真实元数据端点、12 原目标回放：新拒绝 0，原数值变化 0；不可由 float parser 精确保留的候选明确拒绝 |
| 旧 common.py 的 sys.path/sys.modules 可能继续加载旧四位 helper，表面换代码而实际仍旧实现 | 显式加载并核验本版本 contracts/constrained_json/engine/training_target 文件身份 | CPU 原症状及 helper 身份检查；源锁绑定本版本文件 |
| 开发可把数值合法、却不含任何实际源帧的极短区间计为成功，生产才失败 | 顺序解码保留窗内全部 native PTS，开发/生产共用 native_segment_ranges；失败保留 raw 和拒绝区间，不转空 | 极短区间原症状、两条真实源窗 719/720 全帧 PTS；原 64 帧 pixel SHA 一致，实际正区间有帧 |
| 全量教师增量磁盘估计混入已储存 pilot，再除以两条 probe，可能误判容量 | 只按真实 probe 单窗目录估计，扣除已存标签；单独计复查请求 | 实际 pilot/probe 分离与增量成本 CPU 合同；继续只用真实容量 |
| 合法全空 NONTEST 回执没有空间模型调用成本，旧链可能做 anchors × None | 从当前 T 或同固定 8B 历史 NONTEST 真实成功调用取成本；空回执不伪装调用，无合法证据则明确停止 | 合法空回执与实际调用成本 CPU 合同；不改历史成本字节 |
| probe/all/review 共用服务器历史回执位置，后阶段可能覆盖原证据 | 服务器日志和 start/models/stop 按独立 session 保存 | 会话路径与历史回执隔离 CPU 检查 |
| fresh 重输入 probe 可能命中 done 缓存，误报新生成 | fresh 调用明确禁止已完成缓存；pilot 与两条重输入 probe 窗口不重叠 | 缓存拒绝与真实 ID 集合检查 |
| 复查模型混淆窗口秒数与源 PTS，把合法标签判成越界 | 复查请求明确两套单位，并提供计算后的本地/源时间两列表；说明跨窗内容及稀疏采样的证据边界 | 原诊断存在可直接算术复现的误判；新请求两列表 CPU 合同 |
| all_provided_frames_reviewed=true 实际为原 grammar 常量，却被文字描述成模型自主确认 | 修正当前注释/说明，保持原 schema/validator；第二复查真实可拒绝 | 三状态实际固定运行时 grammar 检查；不以常量证明完整语义观察 |
| v6 的 review_prompt_sha256 元数据仍为旧值（v6 从未启动 GPU 链） | 不回写冻结 v6；v7 绑定实际新 prompt SHA，并在 preflight 核对标注与复查 prompt | v7 全源码/模型/tool preflight PASS |
| 一次临时监控过滤字符串 python -，连 python -B 控制器也排除，进程快照不完整 | 新独立巡检按完整版本路径和父进程/PGID 关联服务器，不排除 python -B；旧错误快照保留 | 实查 controller 3086278、wrapper 3091186、pilot 3091199、所属 server 3092890；不能以 GPU 暂时 0% 判断卡死 |

代码入口为 ../teacher_student_autopilot_v7：precision_helpers、native_segment_contract.py、cost_contract.py、teacher_label.py、train_student.py、production_t.py、controller.py。巡检入口 inspect_autopilot_live.py 位于本目录，未改运行中的 234 项冻结文件。

## 实际验收范围

- v7 共 94 项 CPU 合同：audit 15、teacher 10、student 16、clock 8、ffprobe 4、recipe 9、实际固定运行时 grammar 32，全部通过。v6 基础修复为 92 项。
- 160 个冻结真实元数据窗、10302 端点、12 条保留目标无损回放通过。新序列化没有补造或修改标签。
- 两条真实非测试视频完整顺序解码通过：719/720 全源 PTS，原 64 帧像素身份一致。不是仅使用合成媒体。
- update20 的同一 optimizer/RNG/调度接续与 batch 尾部归一化路径已核查；CPU 状态回放不是实际 8B CUDA 更新/完整重载。运行时第20更新真实验收仍必须执行。当前不支持未登记的任意崩溃后训练续跑。
- 不访问 100confirm，不用弱教师 F1 复刻官网分；最终必须 NONTEST8、426 独立 strict、ZIP 大小/SHA/CRC 和根 completion PASS。

## 标签质量仍未通过

v5 于 22:18 UTC+8 停止，12 条均正、零空、零工程失败，T 更新 0。独立真实诊断对原样十二条给出 3 支持、9 拒绝/不确定；同一个教师的复查不是人工真值，且若干拒绝有可证实的时间算术误判，因此不能把 9 条直接说成错误标签，更不能转为空。

v7 独立登记一项科学校准：保留 v5 高光定义和 teacher_prompt 字节，实际生成 grammar 先解释/选择状态，再列 retained_segments；复查同步明确窗口与源时间。这是待验证假设，不声称已经修好全正偏置。十二窗是主控已看过历史诊断的校准集，不冒充未触碰验证集。

v7 重新生成十二条，不复用旧配方标签。全部 eligible 都完成真实第二弱复查后才评估小试；即便分布已失败也保留完整诊断，不把任何拒绝/未知转空、不删除困难样本、不取消原质量门。小试只允许后续完整 128train/32dev，不能直接允许学生训练。完整 train/dev 各真实正空、全部 eligible 复查和20更新前缀等原门保持。

23:38 UTC+8 实查：controller/pilot/其所属32B server 存活，12/12 标注完成、0工程失败，全部关键文件 SHA 通过；12条均正、空例0，distribution=STOP_PILOT_DISTRIBUTION。第二弱复查已2/12、2支持，余项在真实计算；分布拒绝已确定，复查完成后仍须保留原STOP，不能宣称字段顺序校准解决了全正现象。T optimizer_steps=0，无新 T ZIP。最新实时快照在 monitor_aic_linux/latest.json，本文的数字是历史时点，不用来判断未来存活。

## 接续、资源与交付

当前唯一入口 ../teacher_student_autopilot_v7/CONTINUE.md，234文件锁 SHA 70fb36cd016c30dd837f134b907ee75f8582cc957c172ee57a57034d42d4f3dc；配置 SHA 8860c085404516d5912d3f17686e1599eef528a12b597f66518f6f8c3edc17e9。23:13:35 单次启动历史 PID 3086278，后续核完整实时命令，不重开 launcher，不改运行绑定源码。

通过小试及全量原门才自动从官网37.63的 B 最终 LoRA 以 lr1e-5 / 最多3epochs 接续 T，再弱开发选检查点→NONTEST8→426生产推理/空间→独立 strict ZIP。旧 B 官方37.63、4B33.81、退役Mac33.46各自绑定旧包，不能赋给 T。

全部计算和中间产物留 Linux，Mac 不参与；共享 GPU 锁、追加账本和7200秒历史偏移保持。磁盘/RAM/VRAM无项目人为额度，不抢占外部任务。没有新权重/素材下载、批量回传或官网提交。新大流量操作另行说明方向、规模、链路及可能机场成本，等待许可。

每小时静默监控 aic-linux 已改为 v7，异常定位修复，正常计算不发例行更新。最终只有根 completion 为 PASS_AUTOPILOT_FINAL_T_ZIP_ON_LINUX、426 strict 全通过及ZIP大小/SHA/CRC核验，才报告可提交并停用监控。当前旧时间预测不再适用。
