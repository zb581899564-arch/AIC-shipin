# AIC 视频高光剪辑

## 新探索C-advisory（实际快照2026-10-08T17:52:32.875638+00:00）

同既有8B全源粗览＋原B局部全部自然窗，先NONTEST8五臂、固定24五臂，再完整104/96四臂对照；只有固定投入规则准入才一个探索ZIP。旧最佳B37.63保护。用户V14少0.03，37.60为差值推算，非独立官网读数。新分未知，原V14训练15更新但选原B事实保留。Tibo/Sol/Grok两轮实际讨论与最终完整卷宗同步；Pro研究项目连续额度3次已用，新0，Gemini无有效答复，主控独立兜底不冒充共识。当前阶段`RUNNING_CPU_NONTEST_FINISH`、粗览/局部完成{'overview': 8, 'local': 40}、失败0；实际模型回执与独立CPU回放分别计，CPU验收和启动不当新生成。闭世界教师一致性仅投入排序，真实质量/幻觉率未知，不保证超过最佳。见[固定协议](reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/context_advisory_v1/PROTOCOL.md)和[筛选聚合](reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/context_advisory_v1/aggregate_execution.json)。

<!-- END_CURRENT_C_ADVISORY -->


## V14历史交付与真实选点

32B教师推理完整160标签与160盲第二选择、真实8B微调及最终Linux ZIP均已完成独立验收。教师未微调32B；同教师一致性为弱监督，支持65train/14dev，UNKNOWN81与原160分母保留。修复了证据/边界编号、生成约束及probe/all/review、canonical键顺序、validator metadata、pilot diagnostic精确阶段移交。8B学生完成3epochs、15次真实optimizer更新、195次样本反向；4更新前缀、288adapter独立CPU重载与冻结基座通过。弱14dev的原B与epoch1同分，epoch2/3较低，按登记规则选择epoch0原B；新权重未胜出，不宣称新T提高。NONTEST8与426复赛各11项独立strict全true，完整426源/521时间窗/无效0、102470预测帧，ZIP CRC/唯一JSONL/身份/原字节通过。时间为本次真实生成，空间精确复用原B2完整源场，本候选新空间模型调用0、原成本保留。最终Linux包：`/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/teacher_student_autopilot_v14/rematch_01/candidate_T_8B.zip`，实际308278字节，SHA256 `95173d936d09cfcf84bcff5755336e50dbfff94ac5a7e4cfba2953064022f3a2`。包未自动回传或提交官网，新官网分未知。原B37.63绑定旧包SHA `86bd5301f6f6771a8451b32063781e214cdd70245ae5513f2a767eaecb9ebe54`；B2用户37.32/DONE绑定317401字节旧包SHA `0f8c95f01222a28a053e6f80b76b3d4d7ac3dc82077f4dd533605337bc6883a3`。见[协议](reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/teacher_student_autopilot_v14/PROTOCOL.md)与[最终聚合验收](reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/teacher_student_autopilot_v14/aggregate_final_acceptance.json)。

<!-- END_CURRENT_V8 -->
以下B2、context v3与Z/T/S段落保留对应日期的历史状态；当前V14训练和最终ZIP以上方终态验收为准。

AIC 产业命题赛「基于视频大模型的通用视频高光剪辑」的项目代码、实验方案、验收记录和提交包归档。当前复赛已确认成绩：**Linux 8B 37.63，4B 33.81，Mac 8B 33.46**。初赛最佳已确认成绩 **43.94**。初赛与复赛的视频集合不同，分数不直接比较。

本仓库是从工作项目导出的发布快照。保留核心代码原始字节和目录结构；数据集、弱标签逐样本清单、基座/adapter 权重、运行环境、缓存和原始逐帧中间结果没有随仓库分发。已评分源码及正在运行的冻结作业保持原字节；工作项目文档追加最新状态。

## 提交包与官方成绩

| 阶段 | 方案 | 官方分数 | 可下载 ZIP |
| --- | --- | ---: | --- |
| 复赛 | A：4B / P2-T2 时间模型，native PTS 与帧身份恢复 | **33.81** | [candidate_A_PTS.zip][zip-a] |
| 复赛 | B：Linux 8B 区间 JSON SFT，最终 5 轮，同 8B 空间基座 | **37.63** | [candidate_B_8B.zip][zip-b] |
| 复赛 | B2：保留Linux B最终LoRA、native输入与全源空间场 | 37.32 | [代码与生成状态](reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/b_score_aligned_package_v4/CONTINUE.md)；`candidate_B2_8B.zip` 已在Linux严格验收 |
| 复赛 | Mac 8B：64 帧低分辨率区间 SFT | **33.46** | [candidate_MAC_8B.zip](reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/mac8b_delivery_v2/delivery_01/candidate_MAC_8B.zip)；用户已提交，方案停止 |
| 初赛 | 未微调 Qwen3-VL 单片段基线 | 41.09 | [baseline ZIP](submissions/qwen3vl_baseline_20260910/baseline_qwen3vl_20260910.zip) |
| 初赛 | 未微调 Qwen3-VL 多片段 reader | 41.22 | [multi-reader ZIP](submissions/qwen3vl_multi_reader_20260910/aic-qwen3vl-multi-20260910.zip) |
| 初赛 | 历史 Qwen3-VL LoRA reader | 43.48 | [LoRA-reader ZIP](submissions/qwen3vl_lora_reader_20260912/aic-qwen3vl-lora-reader-20260912.zip) |
| 初赛 | P2-Final：P2-T2 时间 + 镜头内稀疏空间锚点 | **43.94** | [P2-Final ZIP](submissions/round6_p2t2_qwen_sparse_20260920/round6_p2t2_qwen_sparse_candidate.zip) |
| 初赛 | Round5 S2 temporal 候选 | 未确认新成绩 | [历史候选 ZIP](submissions/round5_s2_temporal_20260917/aic-round5-s2-temporal-20260917.zip)；上传记录为阻塞 |

每个 ZIP 仅包含 `predictions.jsonl`。完整 SHA-256、大小、成绩来源与状态见 [提交包清单](docs/SUBMISSIONS.md) 和 [机器可读清单](docs/submission_packages.json)。只有已确认结果才填官方分数；未评分候选不继承其他包的分数。复赛成绩由用户报告/截图提供，未另行核验官网。Linux 8B 截图显示 `37.63 / DONE`，裁切部分不足以确认完整时间或名次。

## B2与前期教师诊断历史（2026-10-08上午）

已按采纳结论建立独立 [next_round_v1](reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/next_round_v1)。145项CPU合同、真实processor逐张量一致、全空426独立strict及真实CUDA空生成/空assistant有限CE损失已通过。修复严格0..1000坐标、合法空与失败分离、原生PTS训练目标、生产一致开发输入、全源空间场和Mac离线预留。旧已评分包不变。

2026-10-08 09:45 UTC+8历史：当时路线为[B2已微调8B生产对齐](reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/b_score_aligned_package_v4/CONTINUE.md)。保留已评分37.63的B最终LoRA，不增加训练更新；时间使用B adapter、空间同8B原生基座，总逻辑参数8,782,459,120。B2采用所有分支实际native PTS/floor64帧/顺序PyAV/16384长输入、精确端点与全源空间场，仍用B原1–5段提示与greedy。旧37.63仍绑定旧B包，B2用户回报官网37.32/DONE。

32B context v3已经完整8/8真实请求、0工程失败，三正被弱审核支持，唯一NO被拒绝；没有受支持真实空例，T更新0。审核声称overview仅到119.0189秒，实际完整源回执末PTS149.98316666666668、13帧>=120；事实性错误和语义争议同时保留，不能将拒绝改PASS或空标签当真值。旧raw/失败/科学STOP保存；不再盲试同配方，不造空或弱化原监督门。B2是保留已经训练B的可交付路线，不冒充新教师T训练。

69项CPU、434来源/529真实自然窗/33447样本端点、12原目标无损回放与实际processor/HD/8非测试源重开pixel SHA通过。571文件锁 `52363b5a6f452ac01a55474eacf6529b80e7c4e4ec3e99868f7d91162fae27db`，单次launcher历史PID `3965729`；本次快照阶段 `PASS_COMPLETE_426_B2_8B_ZIP_ON_LINUX`、实际命令进程 `0`。实际B LoRA长输入CUDA已PASS：12048token、288 adapter张量与保存值相等、全基座SHA与原训练相等，选择token分数有限；0优化器更新。Linux最终ZIP终态与NONTEST8/426全部独立strict登记已PASS。包 `/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/b_score_aligned_package_v4/rematch_01/candidate_B2_8B.zip`，实际 `317401` 字节，SHA256 `0f8c95f01222a28a053e6f80b76b3d4d7ac3dc82077f4dd533605337bc6883a3`。B2已交付，用户回报37.32/DONE。

旧Z时间实际adapter=False，521旧时间不能复用B2。非测试全源CPU/同基座空间只在输入/算法/关键SHA与完整回执一致后原样复用；复赛旧CPU域与新native源域不同，不准入复用，真实重算全源CPU/空间。后台真实B长输入CUDA→NONTEST8→426/521时间/全源空间→独立strict ZIP。最终只有真实B2 completion PASS、8/426独立strict全部true、大小/SHA/CRC/唯一JSONL/426身份验收才可提交。

最终ZIP已完整验收，本轮巡检在交付时结束。Linux后台独立运行，本地巡检需要Windows开机且Codex运行。最终只有一个选定ZIP留Linux，不自动回传或AIC上传；新大流量先许可、Mac退出，实际容量与共享GPU锁/账本/7200保持。见[B2决策](reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller/NEXT_ACTION_B2_20261008.md)、[协议](reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/b_score_aligned_package_v4/PROTOCOL.md)、[实时接续](reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/STATUS_AUTOPILOT_20261007.md)。

最终实物ZIP、8/426身份与全部strict、31,295个真实锚点及GPU追加账本已独立复核，见[最终验收](reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller/B2_v4_final_acceptance_20261008.json)。

v4保持canonical时长修复，新加SHA绑定的97送模型前log316/errno95转换修复：临时UNSPECIFIED transfer/限定范围ITU601样本映射后恢复frame元数据，原源/YUV/range/尺寸/PTS不变，不声称恢复摄影gamma曲线。其他源默认转换保持，9转换CPU/64实际帧RGB与空间BGR完全对应、69原CPU/实际processor/8非测试pixel SHA通过；11独立所有权mock及6实际失败分类CPU通过。v1有效GPU计算不打断，v4新NONTEST8后等待完整provider和记账，所有成功原validator/输入/SHA核验原字节保留，只为登记送模型前错误真正生成一次；旧失败STOP保留，不转空/减426分母。见[显式转换与恢复](reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller/B2_COLOR_RECOVERY_20261008.md)。

v4另修复恢复失败证据丢失：新返回原文先写独立且不可覆盖raw，再做有效性校验，异常另记failure/traceback；3项CPU验收无效原文保留/有效原文保留/重复覆盖拒绝通过。v3只停止等待controller，未开始恢复GPU，旧锁与产物保留。冻结源码不回写，生成/色彩/时间配方保持v3，不重复任何成功推理。

完整426/521时间已PASS、无效0；原425成功记录整行字节/520成功窗口相等，仅为已登记送模型前失败实际新生成1窗MODEL_OK，原失败和STOP保留。原raw与接受窗、全部分母及NONTEST8/11 strict均经独立验收；实际GPU费用单独按wrapper账本核。见[真实恢复验收](reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller/B2_v4_recovery_acceptance_20261008.json)。

## 资源策略已取消人为额度（2026-10-07）

用户明确授权本项目不限制磁盘、内存、显存。新作业只核机器实际容量、预计产物和共享任务冲突，不使用旧80/51GiB或Mac预留；GPU累计时间继续不限。源码中的旧额度是已登记历史，后续统一使用[物理容量运行器](reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/resource_unlimited_v1_20261007/gpu_run.py)，[新策略与接续](reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/resource_unlimited_v1_20261007/CONTINUE.md)记录实际下载/构建状态。32B仅离线标注，不进入比赛<=9B部署链，权重和暂存下载不随仓库发布。

## Mac 已退出（2026-10-07）

用户截图确认 Mac 包 **33.46 / DONE**，比 Linux 8B 低 **4.17**。按用户要求停止 Mac 训练、推理和中转；已将重要源码、训练记录及 LoRA 私有归档，逐442成员核 SHA/大小后删除我们在唯一工作根的项目、环境、模型、媒体与缓存，释放约 **26.13 GiB**，仅剩3个工作说明/启动文件约12 KiB。Linux任务继续，交付等待已改为既有SSH别名直连；未改SSH/Tailscale或他人文件。详见[清理与接续记录](reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/mac_retirement_20261007/CONTINUE_AFTER_MAC_RETIREMENT.md)。

## 当前方案

时间模型先预测 30 秒窗口中的高光区间，再按源帧与真实时间戳恢复所选帧。CPU 镜头检测限制空间框的跨帧复用；最多每 8 帧安排一个空间锚点，使用同帧 Qwen 结果在镜头内插值。最终经过完整性、合法框、同帧身份、JSONL 合同与 ZIP 验收。

Linux 8B 用 `Qwen/Qwen3-VL-8B-Instruct` 固定 revision `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b`，语言 LoRA `r=16`、学习率 `5e-5`、5 epochs，704 个训练视频 / 602 来源组 / 724 已知正窗口，3620 次有效 backward、227 次更新。基座和视觉参数冻结；UNKNOWN 未选区域不造负类。训练和固定开发输入界为 8192 token，生产推理 v3 单独登记 16384 token，保留原输入、不截断。时间 adapter 与空间无 adapter 模式共享一个 8B 基座，全链逻辑参数 **8,782,459,120**。

Mac 版本保留相同监督、r16、学习率和训练曝光量，改为最多 64 帧、显式每帧 ≤32768 像素、6144 token 与 PyAV/MPS 训练；最终 adapter 在 Linux CUDA 做开发和生产推理。它同时包含输入与后端差异，不能单独把差异归因于硬件或某个参数。

固定 104 视频 / 96 来源组开发中，Linux 8B 的来源组宏 F1 为 0.685003，Mac 最终模型为 0.649992；二者输入协议不同，不能直接排名。指标是弱教师一致性，且与基座的增量包含格式解析改善，不能代替官方分数。[方案详情与失败版本](docs/SOLUTIONS.md)记录了停止原因及当前边界。

## 核心代码导航

| 内容 | 入口 |
| --- | --- |
| Linux 8B 正式训练、梯度与冻结检查 | [temporal_sft8b_full_v1][full-code]，训练函数 `train_full.py`；公共例子构建与 LoRA 合同在同级 `temporal_sft8b_v1` |
| 固定开发比较 | [temporal_sft8b_dev_v1][dev-code] |
| Linux 8B 推理、阶段调度、严格封包 | [b_sft8b_package_v3][b-code]：`runtime.py`、`production.py`、`controller.py`、`verify_delivery.py` |
| Mac 低内存训练与 MPS 修复 | [mac_sft8b_64_lowres_v8][mac-train]：`train_mac.py`、`mac_inputs.py`、`mps_deepstack.py` |
| Mac 最终 adapter 的 CUDA 开发与提交包 | [mac8b_delivery_v2][mac-delivery]：`lowres.py`、`runtime.py`、`dev/evaluate.py`、`production.py` |
| PTS 合同、顺序帧解码、CPU 镜头与空间锚点 | [baseline_a_pts_v1][pts-code]；JSON 约束在同级 `baseline_a_format_recovery_v1` |
| B2已训练B生产对齐 | [b_score_aligned_package_v4](reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/b_score_aligned_package_v4)：`engine.py`、`native_input.py`、`source_color.py`、`temporal_reuse.py`、`recovery.py`、`production.py`、`controller.py` |
| 新教师/8B全链与审计修复 | [v7源码](reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/teacher_student_autopilot_v7)：`teacher_label.py`、`train_student.py`、`precision_helpers`、`production_t.py`、`controller.py` |
| 共享 GPU 作业锁、资源证据与追加账本 | [controller/gpu_run.py][gpu-run] |
| Qwen 原生基线实现 | [inference/baseline_qwen3vl.py](inference/baseline_qwen3vl.py) |
| 初赛 P2-T2 / P2-Final | [时间训练代码](round6_score_alignment/p2t_temporal_improvement)、[最终空间与恢复代码](round6_score_alignment/p2final_test_candidate) |
| 帧标注工具、严格 loader 与合同测试 | [round6_score_alignment/p1a](round6_score_alignment/p1a)、[p1b](round6_score_alignment/p1b) |

[复赛讨论最终裁决](reports/round6_score_alignment/rematch_discussion/aic_video_rematch_20261005T1044Z/final-decision.md)、[历史路线](ROADMAP.md)、[初赛 43.94 归因报告](reports/round6_score_alignment/PROJECT_CONTEXT_AND_ATTRIBUTION_20260921.md)以及原始验收报告均保留。历史文档中的 PID、预算和“未开始”是当时快照；当前入口以本 README 和各版本日期为准。

## 阅读与复现

先读 [运行和资产说明](docs/REPRODUCTION.md)。这是带有实验路径、SHA 锁和一次性作业注册的研究工程；完整训练/推理需要恢复获授权媒体、弱标签清单、固定模型与环境，仓库克隆本身不代表具备全部运行资产。已有 `launch*.json` 为历史证据，不应用旧 launcher 重开同名实验。

在不加载数据、不运行 GPU 的情况下，可以验证发布文件及归档包：

```bash
python tools/verify_publication.py
```

[发布范围与文件哈希](docs/PUBLICATION.md)、[源文件清单](docs/publication_manifest.json)、[第三方依赖说明](docs/THIRD_PARTY.md)。本次未额外授予数据、模型或第三方代码许可；各自许可与比赛规则继续适用。

[zip-a]: reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/delivery_A_SPATIAL_IDENTITY_01/recover_01/candidate_A_PTS.zip
[zip-b]: reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/b_sft8b_package_v3/delivery_01/candidate_B_8B.zip
[full-code]: reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/temporal_sft8b_full_v1
[dev-code]: reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/temporal_sft8b_dev_v1
[b-code]: reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/b_sft8b_package_v3
[mac-train]: reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/mac_sft8b_64_lowres_v8
[mac-delivery]: reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/mac8b_delivery_v2
[pts-code]: reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/baseline_a_pts_v1
[gpu-run]: reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller/gpu_run.py
