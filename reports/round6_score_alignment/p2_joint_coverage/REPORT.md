# P2 联合覆盖修复：验收报告

- run_id：`round6_p2_freeze_20260918T1130Z`
- 执行时间：2026-09-17 16:20Z – 2026-09-18 11:15Z（本地 CPU 段 + 远端 GPU 段）
- 状态：**`READY_FOR_SUPERVISOR_REVIEW`**（是否进入比赛测试集阶段由总控决定，本报告不批准）
- 代码：`round6_score_alignment/p2_joint_coverage/`；证据：`reports/round6_score_alignment/p2_joint_coverage/`
- 本报告所有 IoU/F1 均为**弱标签稀疏诊断**，`official_status = NOT_OFFICIAL_SCORE` / `INTERNAL_WEAK_DIAGNOSTIC`，**不是官方成绩，也不可换算为官方分数**

---

## 0. 结论摘要

1. **旧框无界复用已在交付路径中被结构性禁止。** 新空间覆盖模块（`aic6/coverage.py`）对每个选中帧给出四类状态之一（`SAME_FRAME`／`SHOT_NEAREST`（须声明距离上限）／`NEEDS_INFERENCE`／`UNRESOLVABLE`）；没有声明镜头信息时任何复用都被拒绝（fail closed），解析失败不再静默变中心框，缺口帧一律显式要求新推理。第五轮 174 视频重放口径下：40,384 个选中帧中 37,184 帧有同帧来源，**3,200 帧有缺口（47 个视频）**；旧规则会把这 3,200 帧全部用最近旧框填满（2747 处距离 >30 帧，1948 处 >300 帧，单视频最远 3,930 帧）。与 P1a 独立复算的 3,200/47/3,930 完全一致。
2. **82 条冻结 dev 上的端到端联调已用真实推理跑通。** S2 时间输出固定不变，只替换空间来源做配对对照：新链路对 856 个缺口帧执行真实的未微调 Qwen3-VL `predict_focus` 推理，**863/863 帧全部合法有效、0 解析失败、0 静默回退**；旧链路同批帧中 856 帧靠最近旧框复制（最远 340 帧）。新链路旧框复用计数为 **0**。
3. **稀疏弱诊断诚实呈现为"证据不足"而非"提升/退化"。** S2 选中帧与 272 个冻结关键帧只交中 7 帧：这 7 帧新旧链路弱 IoU 均为 1.0（同帧弱 ROI，差异退化为 0）；另有 7 帧控制样本测得真实推理弱 IoU 均值 0.798（样本极小，仅说明管线可达）。**只有 7/272 关键帧可评，其余 265 帧和全部未选时间不可验证**——不能据此宣称联合质量，也不能宣称退化。
4. **部署成本可承受。** 按实测速率外推（0.63 s/帧、加载 7.6 s、S2 时间 2.59 s/clip），174 条测试视频的联合推理约 **0.69 GPU 小时、约 1.4 MB 预测文件、峰值显存约 8.5 GiB**（单卡 RTX 6000 Ada 实测 8534 MiB）。P2 实际消耗 **551.3 s ≈ 0.153 GPU 小时**（上限 2 h），项目累计 **14.596/24 h，余 9.404 h**；远端新增文件约 1.2 MB（上限 4 GiB）。
5. **全部工程验证通过**：单元/边界测试 30/30，边界用例目录 16/16（时间端点、重复帧、切镜拒绝复用、缺框、9:16/16:9 合法几何、合法空、无效保留失败），三个 CPU runner 复跑 exit 0，受保护输入哈希前后一致，弱 IoU 口径与 weak_dev_pilot 复现到机器精度（P0 均值 0.8316941516212057、P1 均值 0.9468196471490508 逐位一致）。

## 1. 交付物与复现命令

| 产物 | 路径 |
|---|---|
| 冻结记录（代码/输入/证据哈希） | `reports/round6_score_alignment/p2_joint_coverage/round6_p2_freeze_20260918T1130Z.json` |
| 里程碑1：174 视频四类状态审计 | 同目录 `round6_p2_m1_20260918T1000Z.json` |
| 里程碑2a：dev 模拟预测 CPU 测试 | 同目录 `round6_p2_m2a_20260918T0735Z.json`（+`.sim_predictions.jsonl`） |
| 里程碑2b：边界用例目录 | 同目录 `round6_p2_m2b_20260918T0755Z.json` |
| 里程碑3：新旧链路配对对照 | 同目录 `round6_p2_m3_20260918T0955Z.json` |
| 真实推理原始输出 | 同目录 `gap_predictions.jsonl`（SHA-256 `730b12da…92a9926f`）+ `gap_predictions.run.json` + `infer_gaps.log` |
| 推理请求清单 | 同目录 `p2_infer_requests.jsonl`（SHA-256 `300b972d…450cb8701`） |
| 新模块与测试 | `round6_score_alignment/p2_joint_coverage/`（`aic6/coverage.py` 为核心新模块；`tests/`；`run_m1_coverage_audit.py`、`run_m2a_sim_cpu.py`、`run_m2b_boundary.py`、`run_m3_paired.py`、`remote_infer_gaps.py`、`run_freeze.py`） |

复现（仓库根目录）：

```bash
python round6_score_alignment/p2_joint_coverage/run_m1_coverage_audit.py
python round6_score_alignment/p2_joint_coverage/run_m2a_sim_cpu.py
python round6_score_alignment/p2_joint_coverage/run_m2b_boundary.py
python -B -m unittest discover -s round6_score_alignment/p2_joint_coverage/tests -t round6_score_alignment/p2_joint_coverage
# 远端（训练机，需 aic_video_work 环境）：
# .../env/qwen3vl_isolated_20260910/bin/python remote_infer_gaps.py p2_infer_requests.jsonl gap_predictions.jsonl
python round6_score_alignment/p2_joint_coverage/run_m3_paired.py      # 依赖 gap_predictions.jsonl
python round6_score_alignment/p2_joint_coverage/run_freeze.py
```

## 2. 里程碑逐项证据

### 里程碑1 修复空间覆盖（完成）

- 新模块 `coverage.py`：四类状态 + `CoverageGate`（有界复用必须显式声明 `max_reuse_gap_frames`，非 bool 正整数，NaN/Infinity/float/bool 全部拒绝）+ `legacy_copy_profile`（旧规则对照，只统计不产出框）。
- 174 视频审计（`round6_p2_m1_20260918T1000Z.json`）：`SAME_FRAME` 37,184 / `SHOT_NEAREST` 0（未声明镜头时禁用）/ `NEEDS_INFERENCE` 3,200 / `UNRESOLVABLE` 0；声明"整视频单镜头+30 帧上限"的变体下 160/174 视频可完全解决。缺口最集中：vid 19（1,716）、62（427）、0（142）、100（122）、105（105），与 P1a 一致。
- 第五轮原代码、提交包、历史报告只读未动（受保护输入 5+5 项哈希前后一致）。

### 里程碑2 训练集上的可部署对照（完成）

- 模拟预测 CPU 测试（m2a）：82 条 dev 的 S2 选择共 863 帧（新策略；旧 round+闭区间为 904 帧），模拟链路产出官方格式 JSONL 并经严格校验 0 问题；863 个框的 16:9 镜像几何检验 0 非法。
- 边界用例（m2b）16/16，全部手算期望值。
- 真实推理（远端，隔离环境 `qwen3vl_isolated_20260910`——与第五轮生产同一环境）：856 缺口帧 + 7 控制帧全部有效；逐帧均值 0.63 s，总 551.32 s，峰值 8534 MiB。
- **现有标签全部 9:16**；16:9 仅验证了几何、覆盖与成本，未做也做不了质量主张。

### 里程碑3 联调时间与空间（完成）

- 配对设计：S2 时间输出固定，只换空间来源（新链路=覆盖门控+真实推理；旧链路=最近旧框复制），配对单位为 clip/来源组，bootstrap 种子 20260918、10,000 次。
- 可计算项：稀疏关键帧诊断（7 帧可评，新旧均 1.0，差 0.0）；控制样本 7 帧真实推理弱 IoU 均值 0.798。
- 不可计算项（明确记录）：完整联合弱诊断（272 关键帧仅 7 帧被选中，时间维度无真值）；旧预测不能当真值；内部评分器非官方 evaluator。
- 旧框缺口确证被解决：新链路 `legacy_copy=0`，全部 856 缺口帧来自真实新推理。
- 174 测试视频部署估算：**≈0.69 GPU 小时**（空间 0.56 + 时间 0.13），无需下载新模型；未读取任何测试视频画面、未运行测试集推理。

## 3. 哪些结论成立 / 哪些仍是弱标签推断

**成立（工程事实，可复现）：**
- 四类状态分类与有界复用门控行为符合规范（45 项测试/用例）；
- 新链路在 82 条 dev 上端到端合法（863/863 有效、0 静默回退、0 跨镜头/无界复制）；
- 旧链路的 3,200 帧缺口与无界复制行为（174 视频口径）；
- 实测成本与资源账本；
- 受保护输入未被修改。

**弱标签推断（不可升级为官方结论）：**
- 7 帧上的弱 IoU 一致性（含 0.798 控制样本）——样本极小、全部 9:16 弱教师标签、媒体身份未官方认证；
- "新链路质量与旧链路相当/更好"——**当前证据不足以支持任何方向的质量结论**；
- 0.69 GPU 小时外推值——基于 82 条 dev 的速率，测试视频分布可能不同。

## 4. 进入测试集阶段前仍缺什么

1. 总控对候选实现与证据的审查验收（本报告仅为 `READY_FOR_SUPERVISOR_REVIEW`）；
2. 测试集自动推理的明确授权与运行窗口（估算 ≤0.7 GPU h + 解码/打包余量）；
3. 时间端点约定（`TIMESTAMP_HALFOPEN` vs 旧约定）的最终选择——两者在 174 视频上仅 vid 107 相差 1 帧，但属于内部策略选择，官方语义未知；
4. 镜头检测（当前只有"整视频单镜头"可声明；3,200 缺口帧全部按新推理处理，未依赖镜头信息）；
5. 官方 evaluator 或其对非法提交/稀疏标注处置的确认；
6. 若总控要求质量证据：需先建立 16:9/9:16 可靠空间诊断数据，弱标签稀疏诊断不足以证明提分。

## 5. 预算与边界遵守

- GPU：P2 实际 551.32 s ≈ 0.153 h（上限 2 h）；项目累计 14.596/24 h。作业串行，前后核对 `nvidia-smi` 与 `active_gpu_job.json`（作业结束后已清除）。
- 磁盘：远端新增 ~1.2 MB（上限 4 GiB）；本地报告 ~1 MB。
- 未下载模型/视频，未要求用户补标，未调用外部标注 API，未运行完整训练，未操作浏览器，未生成或上传比赛测试集候选包，未读取测试视频内容。
- 中途 SSH 中断约 8.5 小时（连接超时），远端状态在恢复后按 UNKNOWN→重查处理：GPU 空闲、无活动作业、无残留进程，随后才启动推理；失败的首个作业（`ModuleNotFoundError`，错误环境）留有 `infer_gaps.log` 前身记录并在重试前清理，未伪造任何状态。

## 6. 局限与不得主张

- 内部弱 IoU 口径与 weak_dev_pilot 完全一致并已复现，但**不是官方 evaluator**；
- `SPARSE_DIAGNOSTIC` 语义为内部口径；
- 本报告不批准测试集推理、不构成提分预测；官方 50 分目标不受本报告影响。
