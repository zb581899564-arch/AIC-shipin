# 第五轮执行提示词：AIC 风格无查询时序微调

你是执行 Agent，负责训练机上的数据构建、基线复现、训练与评测；总控 Agent负责研究判断和最终验收。你不是唯一使用该工作区的 Agent，不得回滚、覆盖或删除其他人的文件。遇到超出本提示词的选择，不自行扩大实验，保留证据并停下报告。

## 总控已经作出的决定

1. 停止 OraRL 空间定位、跟踪和动态宽度路线；空间模块冻结为当前 Qwen3-VL `P1`。
2. 第四轮原报告需要勘误。先读取：
   - 本地 `G:\ai\AIC视频\reports\orarl_round4\SUPERVISOR_REVIEW.md`
   - 远端 `/home/inspur/aic_video_work/orarl_round4/REPORT.md`
   - 远端 `/home/inspur/aic_video_work/orarl_round4/evidence/`
3. 下一轮只解决“什么时候剪”。当前 43.4800 候选的 LoRA 来自 query-conditioned QVHighlights，但比赛推理是 query-free；新路线使用 820 条已映射的 AIC 风格 `WEAK_TEACHER` 标签训练 query-free 时序 adapter。
4. 内部弱标签指标只用于选择候选，不等于 AIC 官方分数。本轮禁止读取比赛测试视频、全量测试推理、打包或上传。

## 目录与保护边界

- 新工作目录：`/home/inspur/aic_video_work/temporal_round5`
- 原始标签：`/home/inspur/aic_video_data/labels/train.jsonl`，只读
- 映射：`/home/inspur/aic_video_work/orarl_round4/evidence/mapping_rows.jsonl`，只读
- 基座模型：`/home/inspur/aic_video_work/models/Qwen3-VL-4B-Instruct`，只读
- 当前 43.48 adapter：`/home/inspur/aic_video_work/training_round2_20260910/formal_v1/best`，只读
- 当前推理入口、旧训练、OraRL round1–4、提交包和账本均只读；不能覆盖历史结果。
- 不升级驱动，不改网络，不改其他环境，不向第三方 API 发送任何视频、帧或标签。
- GPU 必须使用现有全局锁，串行运行；本轮 GPU 硬上限 6 小时，新增磁盘上限 10 GiB，结束时不得有残留进程。

## 阶段 A：第四轮勘误与数据冻结（先 CPU）

1. 在 `temporal_round5/audit/ROUND4_ERRATA.md` 写入主管复核中的六项勘误，不能覆盖旧报告。
2. 重新核对 987 行映射：只接纳 `status=usable` 的 820 行；75 条 missing、92 条 time_uncertain 永久排除。逐行确认：
   - `source_path` 存在；
   - clip-local segment 满足 `0 <= start < end <= clip_duration`；
   - 转换后的 source 时间满足源视频范围；
   - 所有字段保留 `WEAK_TEACHER` 标记。
3. 不能把 `free_axis_travel` 称为主体运动强度。它只作为元数据保留，不用于本轮分层。
4. 按 `youtube_id` 分组，确保同一 YouTube 来源绝不跨 split。用固定 seed `20260916` 做确定性分组，冻结 80 个来源组为 holdout、80 个来源组为 dev，其余 561 个为 train。分配必须在任何模型输出之前完成。
5. 报告三份 split 的行数、来源组数、片段时长、segment 数、总高光时长比例。若 clip duration、segment 数或高光比例的任一主要分位差异明显，允许在**模型运行前**改用确定性的分箱分层分组，但必须记录原算法、修改原因和最终 manifest 哈希；不能根据模型结果换 split。
6. 不批量渲染新视频。数据加载时从源视频的 `[clip.start_sec, clip.end_sec]` 虚拟取片段，模型看到的时间必须从 0 开始。抽取 30 个来源组做 PTS/边界与首尾帧身份检查，记录实际解码时间；不能仅用 `r_frame_rate == avg_frame_rate` 宣称全部 CFR。
7. 生成并锁定：`train.jsonl`、`dev.jsonl`、`holdout.jsonl`、`data_gate.json`、`input_hashes.json`。任何门禁失败都停止，不启动 GPU。

## 阶段 B：固定开发集基线

对完整 dev split 运行以下三臂，所有臂使用相同虚拟片段、采样上限 64 帧、query-free 任务语义，并统一为多区间 JSON：`{"segments":[[start_sec,end_sec],...]}`。

- `T0_BASE`：未微调 Qwen3-VL。
- `T1_QVH_LORA`：当前 43.48 adapter；这是主要对照。
- `T2_ORARL_TEMPORAL`：现有 Video-ORA-4B 的 temporal grounding，只测试一次固定的通用表达“the moments most worth retaining in a short highlight edit”。使用作者支持的时序协议；解析后再转成统一 JSON。不得搜索提示词。

训练和推理使用同一条 query-free Qwen 提示：识别片段中所有值得保留到短高光中的时间区间，只返回 clip-local 秒的 JSON。不得输入 QVHighlights query、teacher summary、cropRois 或测试集信息。

逐行保存原始输出、解析状态、区间、耗时和峰值显存。评测使用区间并集的 precision、recall、F1，非法输出计 0 且保留在分母；另报有效率、空预测率、预测时长比例、片段时长分层结果，以及按 `youtube_id` 配对 bootstrap。此处只称 `WEAK_TEACHER temporal F1`。

## 阶段 C：训练流程测试与两种初始化

仅在阶段 A、B 完整通过后继续。

1. 训练目标只包含 query-free 提示和弱标签 `segments`；loss 只覆盖 assistant 答案 token。
2. 冻结视觉模块与原始语言模型权重，只训练语言注意力 `q_proj/k_proj/v_proj/o_proj` 的 LoRA。使用 BF16、rank 16、alpha 32、dropout 0.05、batch 1、梯度累积 16；固定随机种子并记录依赖版本。
3. 建立两臂：
   - `S1_FRESH`：从基座新建 LoRA，学习率 `5e-5`；
   - `S2_WARM`：从 43.48 adapter 继续训练，学习率 `2e-5`，保持其 rank、target modules 与其余配置。
4. 两臂各先跑 16 条样本、最多 20 个 optimizer steps。验证 checkpoint 可重新加载、训练 loss 有限、推理 JSON 合法、视觉权重与基座权重未被修改。任一项失败即停。
5. smoke 通过后，两臂各训练 1 epoch，并在完整 dev 上比较。只允许选择 dev `WEAK_TEACHER F1` 较高的一臂继续；平分时选择预测时长比例更接近标签且有效率更高的一臂。不能改 split、提示词、解析器或指标。
6. 选中臂最多训练到总计 3 epochs；每个 epoch 后评 dev，按预先固定的 dev F1 选择 checkpoint。单臂累计训练到 4 GPU 小时或总轮次 3，先到即停。

## 阶段 D：唯一一次留出评测

选定唯一 checkpoint 后，才运行一次完整 holdout。与 `T1_QVH_LORA` 在同一 holdout 上配对比较。全部满足才记为 `PASS_INTERNAL_GATE`：

1. 100% 输出可解析、区间有序、不重叠、不越界；
2. dev 平均 F1 相对 T1 提升至少 3.0 个百分点；
3. holdout 平均 F1 相对 T1 提升至少 2.0 个百分点；
4. holdout 来源组配对 bootstrap 95% 区间下界不小于 0；
5. 在 clip duration 四分位层中，任何一层相对 T1 的退化不超过 2.0 个百分点；
6. adapter 能在离线环境重新加载并复现固定 3 条 dev、3 条 holdout 的完全相同区间输出。

未过门槛就保留 43.48 adapter，不用 holdout 调参，不启动新的训练尝试。通过门槛也只冻结内部候选，本轮仍禁止比赛测试集推理、打包和上传，等待总控验收。

## 交付与停止条件

交付至少包括：

- `/home/inspur/aic_video_work/temporal_round5/REPORT.md`
- `audit/ROUND4_ERRATA.md`
- 数据 manifest、split 与哈希
- 三个基线臂的原始输出和指标
- 两个 smoke 结果、训练配置、GPU/磁盘账本
- 选中 adapter 或明确的失败原因
- dev/holdout 配对对照、bootstrap、分层表
- 结束时 GPU、进程和磁盘状态

把最终报告和小型证据文件复制到本地 `G:\ai\AIC视频\reports\temporal_round5\`，逐文件核对 SHA-256。不要复制模型权重到本地。汇报时严格区分：格式通过、弱标签内部收益、官方成绩；没有官方提交就写 `OFFICIAL_SCORE=NOT_AVAILABLE`。

