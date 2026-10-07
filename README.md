# AIC 视频高光剪辑

AIC 产业命题赛「基于视频大模型的通用视频高光剪辑」的项目代码、实验方案、验收记录和提交包归档。当前复赛已确认成绩：**Linux 8B 37.63，4B 33.81，Mac 8B 33.46**。初赛最佳已确认成绩 **43.94**。初赛与复赛的视频集合不同，分数不直接比较。

本仓库是从工作项目导出的发布快照。保留核心代码原始字节和目录结构；数据集、弱标签逐样本清单、基座/adapter 权重、运行环境、缓存和原始逐帧中间结果没有随仓库分发。已评分源码及正在运行的冻结作业保持原字节；工作项目文档追加最新状态。

## 提交包与官方成绩

| 阶段 | 方案 | 官方分数 | 可下载 ZIP |
| --- | --- | ---: | --- |
| 复赛 | A：4B / P2-T2 时间模型，native PTS 与帧身份恢复 | **33.81** | [candidate_A_PTS.zip][zip-a] |
| 复赛 | B：Linux 8B 区间 JSON SFT，最终 5 轮，同 8B 空间基座 | **37.63** | [candidate_B_8B.zip][zip-b] |
| 复赛 | Mac 8B：64 帧低分辨率区间 SFT | **33.46** | [candidate_MAC_8B.zip](reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/mac8b_delivery_v2/delivery_01/candidate_MAC_8B.zip)；用户已提交，方案停止 |
| 初赛 | 未微调 Qwen3-VL 单片段基线 | 41.09 | [baseline ZIP](submissions/qwen3vl_baseline_20260910/baseline_qwen3vl_20260910.zip) |
| 初赛 | 未微调 Qwen3-VL 多片段 reader | 41.22 | [multi-reader ZIP](submissions/qwen3vl_multi_reader_20260910/aic-qwen3vl-multi-20260910.zip) |
| 初赛 | 历史 Qwen3-VL LoRA reader | 43.48 | [LoRA-reader ZIP](submissions/qwen3vl_lora_reader_20260912/aic-qwen3vl-lora-reader-20260912.zip) |
| 初赛 | P2-Final：P2-T2 时间 + 镜头内稀疏空间锚点 | **43.94** | [P2-Final ZIP](submissions/round6_p2t2_qwen_sparse_20260920/round6_p2t2_qwen_sparse_candidate.zip) |
| 初赛 | Round5 S2 temporal 候选 | 未确认新成绩 | [历史候选 ZIP](submissions/round5_s2_temporal_20260917/aic-round5-s2-temporal-20260917.zip)；上传记录为阻塞 |

每个 ZIP 仅包含 `predictions.jsonl`。完整 SHA-256、大小、成绩来源与状态见 [提交包清单](docs/SUBMISSIONS.md) 和 [机器可读清单](docs/submission_packages.json)。只有已确认结果才填官方分数；未评分候选不继承其他包的分数。复赛成绩由用户报告/截图提供，未另行核验官网。Linux 8B 截图显示 `37.63 / DONE`，裁切部分不足以确认完整时间或名次。

## 下一轮代码修复与执行（2026-10-07）

已按采纳结论建立独立 [next_round_v1](reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/next_round_v1)。145项CPU合同、真实processor逐张量一致、全空426独立strict及真实CUDA空生成/空assistant有限CE损失已通过。修复严格0..1000坐标、合法空与失败分离、原生PTS训练目标、生产一致开发输入、全源空间场和Mac离线预留。旧已评分包不变。

2026-10-07 23:38 UTC+8：全面核查后的 [v7 接续入口](reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/teacher_student_autopilot_v7/CONTINUE.md) 已单次启动。修复了真实 PTS 到学生目标的精度冲突、helper身份、开发/生产实帧合同、成本与回执等问题；94项CPU合同、10302真实端点、12原目标无损回放及两条真实视频解码通过。旧serializer拒绝11/12，新拒绝0，标签数值变化0。

真实小试12/12全部正、空例0，分布门 `STOP_PILOT_DISTRIBUTION`；第二弱复查2/12、2支持，其余仍在运行，不能宣称字段顺序校准解决质量问题。T更新0、无新T ZIP。完整诊断后保留原科学门，不造空/删样本/盲目全量重跑。详见[全链审计](reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller/COMPREHENSIVE_AUDIT_20261007.md)。

v5同样十二窗全正而STOP；独立真实诊断3支持、9拒绝/不确定，部分拒绝有可证实的时间单位误判。同教师弱复查不能视为人工真值。v6为独立工程修复准备版本、未准入启动；v7保留v5高光定义，先解释/选择状态再列片段，且明确复查两套时间，这是待验证科学校准。当前校准集已看过历史诊断，不冒充未触碰验证集。原grammar的all_provided_frames_reviewed=true为常量，不能当自主观察证明。

Z已完成426条/521窗口时间和全源CPU调度，但13:08被旧冻结51GiB额度拒绝空间阶段而STOP，旧失败与源码保留，未生成Z包。机器实际尚有约193GiB空间；新T使用真实容量运行器，不以Z成功/评分为前提。Windows旧下载、上传桥接和Z回传停止，Mac不参与。用户批准的Linux原地下载与自动标注、微调、封包授权继续有效。

T路线是32B离线教师观察128train/32dev自然窗口、生成并复查完整窗口弱标签，然后从已取得37.63的B最终LoRA以lr1e-5接续最多3epochs；第20更新做真实重载验收，每轮固定弱开发选择检查点，通过NONTEST8后做426复赛推理和strict ZIP。训练、开发、生产共用原生PTS选帧与0..5段输入合同；允许合法空，失败不转空。32B不进入比赛部署链，部署仍为8,782,459,120参数。详见[T协议](reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/teacher_student_autopilot_v7/PROTOCOL.md)和[接续状态](reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/STATUS_AUTOPILOT_20261007.md)。本轮未取得新官方分。

中间产物和最终新ZIP先留Linux，用户只取一个选定提交包，取包前说明实际大小；其他新大流量传输须先说明规模、链路及可能机场消耗并取得确认。计算不依赖Windows持续在线，Mac不参与。磁盘/RAM/VRAM没有项目人为额度，新作业按真实容量和共享任务冲突安排；已注册旧作业与失败证据保持。S仍缺合格双比例构图参考。

不需要本地复刻AIC官方总分；非测试诊断和格式/身份检查保留。正式得分来自官网每日最多5次提交，阶段最高有效分排名。内部弱教师F1不能替代官方分。[复赛通知](https://www.aicomp.cn/notice/notice-3/5307.html)

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
