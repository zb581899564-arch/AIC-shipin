# Gemini 3.8 Flash 扩展 / r00

任务：AIC-VIDEO-REMATCH-NEXT-20261005
读取UTC：2026-10-05T11:09:21.283Z
来源：https://gemini.google.com/app/7df8e40a35f9c9b7?hl=zh-cn
状态：用户恢复页面后完整可见回答，aria-busy=false，出现评价/复制/重做控件，无停止回答。采用用户批准的口述例外。

一、首部确认与硬约束核验

任务 ID：AIC-VIDEO-REMATCH-NEXT-20261005

版本：r00

基础文件：context-r00.md

关键硬约束：

模型总参数量：全量实际运行主干、辅助模型及 LoRA/Adapter 总元素必须 ≤9B（共享参数仅计一次；量化不减少名义参数量）。

算力与存储：单卡 RTX 6000 Ada（约 46GiB 显存，125GiB RAM），新增磁盘占用严格受限 ≤80GiB。

测试集边界：426 个 MP4 与 426 个 JSONL 仅用于离线自动推理，严禁训练、人工标注、改动、外传第三方 API 或反向构造规则。

提交与时间：每日最多 5 次提交，以阶段最高分为准；结果截止 2026-10-23 20:00，作品截止 2026-10-25 23:59（UTC+8）。

事实、推断与未知边界：

事实：初赛 P2-Final 分数 43.9400，较 43.4800 仅微增 0.4600；预测覆盖率自 76.20% 骤降至 41.40%，共同帧空间 IoU 达 0.9384；R7 扩大训练池至 704 条后，开发集 F1（0.625101）未超过 P2-T2（0.626936）且召回率退化（0.672882 vs 0.707980），触发停机；Qwen3-VL-8B-Instruct 公开 BF16 参数量为 8,767,123,696（距 9B 上限余量仅约 232.88M）；官方复赛明确不提供训练集。   
OpenReview

推断：初赛增益受阻的主要矛盾在于时序过拟合弱教师导致的漏检（高精确、低召回），空间裁剪工程已逼近当前构图上限；弱教师区间文本 SFT 模式已遭遇结构性瓶颈。   
arXiv

未知：官方线上 Evaluator 对重复/非法帧的细粒度惩罚源码；复赛测试集的真实高光密度与画幅偏好；8B 模型在单卡 46GiB 下的长视频端到端推理吞吐与显存峰值。

二、一手论文真实检索与适用性核对

已实际联网检索并核对以下两篇一手论文之方法与实验章节：

1. Moment-DETR / QVHighlights (NeurIPS 2021)   
GitHub

来源与位置：Jie Lei et al., Detecting Moments and Highlights in Videos via Natural Language Queries, Section 3.2–3.4 及 Experiment 4.2。

核心方法：采用 Transformer 编码器-解码器架构，解码器利用 Hungarian Matching 联合预测区间坐标（L
1
	​

+L
GIoU
	​

）与前景分类，编码器输出直接通过线性层预测 Clip 级 Saliency Score，并采用 Margin-ranking Hinge Loss（margin=0.2）在正负 Clip 间建立排序约束：

L
hinge
	​

=max(0,Δ+s
neg
	​

−s
pos
	​

)

适用性：证实了密集时间打分（Dense Saliency）与多段区间联合建模的有效性，为克服离散文本 SFT 区间预测提供了理论支持。

关键不适用鸿沟：

依赖 Query：Moment-DETR 核心依赖自然语言 Query 进行跨模态注意力计算；AIC 为通用无 Query 剪辑，强套文本 Cross-Attention 会退化为无意义常数偏置。

标签粒度错位：论文依赖人工 1–5 分精细标注构建高质量的正负 Pair；AIC 仅有弱教师粗二值区间，强制构建 Pair-wise Hinge Loss 会将弱教师的时间抖动放大为系统噪声。

2. UniVTG (ICCV 2023)   
GitHub

来源与位置：Kevin Qinghong Lin et al., Towards Unified Video-Language Temporal Grounding, Section 3.1–3.2 及 Table 2/3。

核心方法：将时序定位解耦为三元组：前景指示符 f
i
	​

∈{0,1}、边界偏移 d
i
	​

=[d
i
s
	​

,d
i
e
	​

] 与显著性得分 s
i
	​

。其关键机制在于：边界回归损失（L
boundary
	​

）仅在前景片段（f
i
	​

=1）上计算，背景片段仅参与前景色分类与对比学习。

适用性：其“前景掩码隔离”与“仅在正样本上约束边界”的设计，直接启发 AIC 弱监督下的 Masked Loss——未标注源视频时段严禁作为强负例参与边界惩罚。   
arXiv

关键不适用鸿沟：

UniVTG 依赖 420 万级 CLIP 类别生成的伪文本标签进行大规模预训练，AIC 无法引入开放文本伪标签。

该文完全不涉及空间裁剪；AIC 必须同时解决时间帧选取与画幅转换（h=w×target_h/target_w）的联合 IoU 最大化，时序单点 F1 无法直接等价于 AIC 最终得分。

三、核心问题独立分析
1. 每日 5 次提交的利用策略与不可辨识性分析

评分公式：单视频 F=
N
pred
	​

+N
gt
	​

2∑
t∈matched
	​

IoU
t
	​

	​

（双空 1，单空 0），全库均值乘以 100。

数学不可辨识反例：
设某视频 N
gt
	​

=100：

候选 A（高覆盖/低 IoU）：预测 N
pred
	​

=100，命中 50 帧，单帧平均 IoU=0.8。分子为 2×40=80，分母为 200，单视频得分 0.400。

候选 B（低覆盖/高 IoU）：预测 N
pred
	​

=40，命中 30 帧，单帧平均 IoU=0.95。分子为 2×28.5=57，分母为 140，单视频得分 0.407。

两候选总分几乎相同（0.400 vs 0.407），但前者时间召回率高达 50%、后者仅 30%；一个标量总分根本无法解耦时间召回、时间精确率与空间框吻合度。若在线盲测阈值，极易将“大幅删帧导致分母偶然收缩”误判为“模型性能提升”，进而诱发灾难性过拟合。

反向探测边界：利用微小扰动探针反推测试集标签明文违反赛事“反向构造规则”底线；但在工程上预登记有限单变量消融完全合法。

提交策略与停止条件：每日至多使用 1–2 次，严禁为用满 5 次盲目刷榜。制定如下预登记候选矩阵：

包 0（基线锚点）：P2-Final 复赛移植包（验证评测链路一致性）。

包 1（时间高召回消融）：调整时序滑动窗口打分阈值（覆盖率由 41% 恢复至 ~60%）。

包 2（8B 架构探索）：8B 共享主干下的初版推理包。

停止条件：若提交包离线格式校验存在任一警告，绝对不提交；若连续 2 次提交线上总分波动 <0.2 且无法在离线诊断中定位归因，立即冻结线上探索，退回本地离线审计。

2. 唯一优先模型架构与训练机制

模型选型：Qwen3-VL-8B-Instruct（BF16 参数 8,767,123,696），坚决采用时空共享主干，禁止叠加独立 4B/8B 空间模型。

参数硬约束核验：
基座距离 9B 仅剩 232,876,304（约 232.88M）参数。全参微调在单张 46GiB 显卡上必将发生 OOM，且无法保留通用构图先验。

训练机制：

时序模块：冻结 ViT 视觉塔与 LLM 主干大部分层，仅在 LLM 注意力层注入轻量 LoRA（rank=16,α=32，目标张量 q_proj, v_proj，参数量约 35M），并在顶层接入 1 个 3 层轻量 MLP 时序打分头（输出固定 PTS 网格的置信度，参数量 <5M）。增量参数总量 ≤40M，严格符合 ≤9B 规则。

空间模块与 Adapter 隔离：时序微调严禁破坏预训练模型的通用空间定位能力。在执行空间裁剪定位时，显式禁用时序 LoRA 与打分头（Adapter Scale 归零），复用纯净的未微调 8B 视觉定位能力；结合 CPU 镜头门控与关键帧锚点插值，杜绝逐帧高负载前向传播。

单卡验证入口：
必须在 M0 阶段建立非测试验证脚本：在单卡 RTX 6000 Ada 上实测 BF16、FlashAttention-2 下 8B 主干抽取 30 秒视频特征的显存峰值（阈值：≤38GiB）与吞吐量（阈值：≥3.0 fps），确认 426 个测试视频总推理时长在可控预算内（≤6 小时）。

3. 数据监督机制与去偏方案

Query-free 任务适配：剔除所有复杂的自然语言指令诱导，固定极简通用 Prompt（如：“Identify video highlight segments and main subject positions”），消除文本生成的多样性漂移。

未标注时段 Mask 机制：将 908 条审计后的标签区间视为弱正例；视频内部、未被弱标签覆盖的时段标记为 UNKNOWN_MASK，在损失计算中权重置零（不计入交叉熵反向传播），仅在确认的背景切片中计算有限负样本损失，彻底阻断对有偏弱教师“假负例”的盲目拟合。   
arXiv

合法空与多段事件支持：保留整视频全空样本通道；时序打分头输出 PTS 稠密置信曲线，通过自适应水线阈值与非极大值抑制（NMS）自动聚合出 1 至 5 段完整事件，破除初赛“固定单窗强制选取”的人工偏差。

跨画幅空间风险控制：弱空间标签全为 9:16（固定 169×300），而测试集 68.4% 为 16:9。绝对禁止在弱空间标签上微调 8B 空间坐标（初赛空间 LoRA 退化已成铁证）；空间裁剪保持最大合法宽度裁剪（Max Legal Crop），仅微调中心点位移预测，严格锁定长宽比几何换算。

4. 分段实施计划（10月5日 – 10月23日）

前 48 小时极速交付（10月5日 – 10月6日）：

合同固化：只读解析 426 个 JSONL 基础元数据，锁定输入输出合同与本地严格校验器。   
arXiv

参数审计脚本：交付自动化脚本，逐张量求和验证主干+LoRA+打分头 ≤9B。

复赛基线提交：将初赛冻结的 4B+P2-T2+未微调空间工程链路直接在复赛 426 样本上运行并严格打包，完成第 1 次官方基线提交，锁定复赛初始基线分。

材料同步：初始化技术报告骨架、代码仓库版本标签与环境 Dockerfile。

M2/M3 主干与时序探索（10月7日 – 10月13日）：

跑通 8B 显存/吞吐验证；

基于 908 条数据池，训练 8B 共享主干 + Masked LoRA + 稠密时序打分头；

交付基于离线 5 折来源组交叉验证的对比报告。

M4 决策与全量冻结（10月14日 – 10月18日）：

执行预登记的线上消融（最多 3 次提交）；

若 8B 在离线验证与线上锚点均有稳健正向增益，锁定 8B；若退化，立即回滚至 4B+高召回时序分支。

收尾与合规交付（10月19日 – 10月23日）：

10月20日前完成最终预测结果提交；

10月21日–23日完成代码可复现性回归、环境依赖冻结及技术报告终稿归档。

门禁原则：工程必过门（0 非法框、0 越界、参数 ≤9B、哈希校验一致）为一票否决；研究证据门（离线验证指标）作为候选选择依据，允许在工程合规前提下提交带有新假设的探索包。

5. 最强反例、回滚、成本与尖锐质询

最强反例：
R7 实验已经证明：盲目扩大弱监督数据池，模型不仅未能提升，反而因弱教师固有的保守偏差导致召回率直接下降 3.5 个百分点。8B 模型的更大容量极可能“更完美地拟合了有偏弱教师的假精确”；加之 8B 前向计算耗时激增，若引发空间锚点提取超时，系统将被迫降级，导致线上崩盘。

唯一优先方案：基于 Qwen3-VL-8B-Instruct 的共享主干方案（时序端采用 Masked 稠密时序打分 LoRA，空间端冻结主干并隔离 LoRA，沿用镜头门与关键帧插值）。

唯一后备方案：Qwen3-VL-4B + 高召回时序打分微调 + 冻结空间链路（若 8B 显存超标或吞吐无法满足 6 小时内完成测试集，立即触发全量回滚）。

向其他参与者提出的 2 个尖锐质询：

关于总分黑盒：若每日 5 次提交仅返回一个标量 F 值，当某次实验总分微升 0.3 分时，在数学上如何排除“这只是因为测试集短视频比例偏高导致的分母偶然偏小”，而非真实时空泛化能力的提升？

关于 8B 部署可行性：Qwen3-VL-8B-Instruct 原始参数已占 8.767B，在规则明确禁止通过量化降低统计参数量的前提下，单卡 46GiB 显存如何保证在长视频多帧特征提取时不发生 OOM，并确保 426 个测试视频的端到端时序+空间推理在截止日前稳定跑完？   
arXiv

## UI公式源码属性（同一可见公式）

- `\le 9\text{B}`
- `\le 80\text{GiB}`
- `L_1 + L_{\text{GIoU}}`
- `\text{margin}=0.2`
- `\mathcal{L}_{\text{hinge}} = \max(0, \Delta + s_{\text{neg}} - s_{\text{pos}})`
- `f_i \in \{0, 1\}`
- `d_i = [d_i^s, d_i^e]`
- `s_i`
- `\mathcal{L}_{\text{boundary}}`
- `f_i=1`
- `h = w \times \text{target\_h} / \text{target\_w}`
- `F = \frac{2 \sum_{t \in \text{matched}} \text{IoU}_t}{N_{\text{pred}} + N_{\text{gt}}}`
- `N_{\text{gt}} = 100`
- `N_{\text{pred}} = 100`
- `\text{IoU} = 0.8`
- `2 \times 40 = 80`
- `N_{\text{pred}} = 40`
- `\text{IoU} = 0.95`
- `2 \times 28.5 = 57`
- `<0.2`
- `\text{rank}=16, \alpha=32`
- `<5\text{M}`
- `\le 40\text{M}`
- `\le 9\text{B}`
- `\le 38\text{GiB}`
- `\ge 3.0\text{ fps}`
- `\le 6\text{ 小时}`
- `169 \times 300`
- `\le 9\text{B}`
- `\le 9\text{B}`
- `F`

## 可见链接



## 引用弹层可见来源

- [ GitHub  jayleicn/moment_detr: [NeurIPS 2021] Moment-DETR code ... - GitHub “GitHub - jayleicn/moment_detr: [NeurIPS 2021] Moment-DETR code and QVHighlights dataset · GitHub ... saliency loss (by setting the corresponding loss weight to ...”](https://github.com/jayleicn/moment_detr)
- [ GitHub  [ICCV 2023] UniVTG: Towards Unified Video-Language ... - GitHub “UniVTG (ICCV'23) [arXiv] TL; DR: The first video temporal grounding pretraining model, unifying diverse temporal annotations to power moment retrieval (interval...”](https://github.com/showlab/UniVTG#:~:text=UniVTG%20(ICCV'23)%20%5BarXiv%5D%20TL%3B%20DR%3A%20The%20first,Create%20the%20Huggingface%20space%20demo!%20*%20%5B2023.7.)
