# sol 第2轮完整可见意见

来源：https://chatgpt.com/c/6ac381db-4b5c-83ea-be82-bb3d86a7cc37
UTC：2026-10-05T11:23:30.986Z
5.6 sol基础型号由用户确认；高模式UI。以下为可见正文，不含私有思维链。

任务确认：AIC-VIDEO-REMATCH-NEXT-20261005｜版本 r01｜文件 context-r01.md。 我实际逐行读取了附件正文 L1–L2163，并核算文件 SHA256 为 4b67bed3fd51c0ebb55ed556d7c3abdb9191f64f46e3cbef49a85fc876b1027a，与给定值一致；读取内容包括 r00 基础包、Tibo / sol / Grok / Gemini 四席完整首轮意见、主控论文复核、r01 交叉问题及 Gemini 勘误，不把“附件存在”当作已读。当前仍只讨论，不启动 GPU、下载、复赛推理或提交。
context-r01

一、我先纠正自己的首轮

我撤回两个过强结论。第一，我首轮要求“先证明4B出现明显容量瓶颈，再准8B”，这个前置条件不合理。容量瓶颈很难被单独证明，做这种证明可能比一个匹配的小型8B探针更贵；考虑截止期和用户明确的8B倾向，8B应尽早做小探针，不需要等4B失败。但探针是在验证“这条8B实现值得继续”，不是预设8B优于4B。这与主控 r01 的修正一致。
context-r01

第二，我首轮直接把 UniVTG 的“foreground＋saliency＋boundary”三头搬进主案，监督语义越界。UniVTG §3.1 的确定义 
𝑓
𝑖
,
𝑑
𝑖
,
𝑠
𝑖
f
i
	​

,d
i
	​

,s
i
	​

，但它拥有对应监督；我们只有弱区间，没有独立连续“精彩程度”等级。其 QVHighlights Table 2 的 35.47→43.63 也只能证明该框架在其数据上有效。第一版应只有网格二分类/覆盖范围内排序；边界损失只用于边界语义确证的样本，不制造 saliency 真值。 
开放访问CVF
+1

我首轮自定的“recall +3pp、F1最多掉1pp”也撤回：它可以是讨论用的实用目标，不能冒充有依据的科学门槛。
context-r01

二、对其他席的具体批判

Grok 的论文数字必须纠正。 它写“去掉 saliency loss 后 R1@0.5
 从44.84降到25.87”，实际混了两列。Moment-DETR 主文 Table 4：完整损失 R1@0.5
=53.94、R1@0.7
=34.84；去掉 saliency 后分别是44.84、25.87，Avg mAP也由32.20降至25.05。补充材料 Table 3 更重要：仅 interval-inside/outside saliency ranking 就已有 Avg mAP 31.46，反而支持我们“不编连续精彩度、先做覆盖内二分类/排序”的简化路线。
NeurIPS 会议论文集
+1
 Grok提出“连续两个线上差值进入预设噪声带就停止”也不能成立：我们从未测过官方评分随机噪声，不能凭空制造 noise band。
context-r01

Gemini 的方向可以保留，数字不能保留。 官方 Qwen3-VL-8B 配置是36层、hidden=4096、32个attention heads、8个KV heads、head_dim=128；按 rank16 的独立 q/k/v/o LoRA 推算是 15,335,424 参数，q/v两项也只有7,667,712，不是约35M。官方公开基础总参数为8,767,123,696；再加 4096→128→1 的共享头 524,545，预估总计 8,782,983,665，仍低于9B，但最终必须以真实加载张量重新核账。
Hugging Face
+1

Gemini 的“≤38GiB、≥3fps、426条≤6小时”都是未实测假设；68.4% 是初赛 119/174 的16:9比例，不是复赛426条的已知分布；从初赛41%覆盖推一个“复赛60%覆盖候选”同样没有独立依据。这些都应删除，而不是换一个数字。它同时说“绝不微调空间”又“微调中心位移”，也自相矛盾。
context-r01

对 Tibo 我总体更接近，但仍补一个风险：B=8B区间、C=8B网格可以较好比较目标形式；A=4B、B=8B却是整包比较，不能称纯规模消融，因为8B空间基础输出也可能变化。Tibo自己的三包设计已经承认这一点。
context-r01

三、核心裁决：立即8B小探针；query-token头可行

我的唯一主案现在改为：Qwen3-VL-8B共享主干，视觉塔与基础权重冻结，文本注意力 q/k/v/o rank16 LoRA＋共享 4096→128→1 二元网格头；空间推理时关闭时间adapter和读出头。 4B/P2-T2完整链仅作后备。

这个头和语言LoRA可以共同训练。只要二分类 loss 从每个 query-token 的最终 hidden state 进入 MLP，且中间没有 detach/no_grad，梯度会经过修改后的attention回传到 q/k/v/o LoRA；MLP本身也同步得到梯度。最小证明不是理论宣称，而是一次真实 update 后同时检查“头梯度非零、LoRA梯度非零、基础/视觉参数梯度为零”。

但有三个对齐风险。所有视觉/固定提示内容必须位于查询读出之前，query位置必须由真实 tokenizer 映射而不是猜字符偏移；teacher标签、边界答案绝不能出现在模型输入。其次多个 query 在 causal decoder 中，后面的 query 能看到前面的 query——这不是标签泄漏，前提是前面的query只有时间身份而没有答案，但会造成时间格之间的顺序耦合；因此查询顺序必须冻结为时间顺序，并把这种耦合视为模型设计而非独立分类器。再次，训练和推理的网格、attention mask、PTS映射必须一致，空间调用前关闭adapter并清理cache，验证能恢复同一8B基础输出。附件主控的最小校验方向基本正确。
context-r01

四、mask到底遮什么

必须分三类：已覆盖正例可以作弱正；教师覆盖范围内且标注流程确实穷尽的背景才可以作 teacher-negative；覆盖语义之外的源时间全部 unknown、loss weight=0。部分跨边界网格优先 mask，除非事先定义有证据的软标签。

尤其不能把 QVHighlights/UniVTG 中“与 query 不相关”的 clip 当 AIC 的通用负例——一个片段对“找狗”是负例，完全可能仍是整条视频最精彩的片段。固定一个 generic prompt 也不会自动把 query-conditioned negative 变成 query-free negative。mask能避免制造假负例，却不能教模型找出弱教师漏掉的正例，所以仍需要很小的、合规非测试 query-free 桥接检查。

这也回答 Tibo/Grok 的问题：没有双比例独立真值，就不能证明8B空间是升级，只能验证工程完整和没有明显非测试退化；只有线上一个联合总分，也不存在任何可观测标量能单独证伪“覆盖不足”。4B稠密失败也不自动取消8B，但若连 query-token 对齐、梯度路径或标签语义都失败，则应直接停止这个架构族，而不是靠规模救实现错误。

五、前48小时、候选与止损

若后续另行授权执行，前48小时的可验收产物只应有一组：

冻结的 4B/P2-T2复赛基线合同与严格验证/技术报告骨架；8B逐张量参数账；query-token tokenizer→PTS映射测试；一次非测试8B训练步的梯度/冻结/adapter-off恢复报告；实测峰值显存、吞吐和磁盘，只报测量值，不设38GiB/3fps/6h之类假硬线。
后续线上最多预登记三个完整包：A=完整4B/P2-T2基线；B=主案8B网格；C仅在确有价值时为同一8B的区间输出控制。配置和哈希在首次看到线上成绩前封存。线上只允许回答“哪个完整包分更高”，不能据此反演召回、IoU、隐藏标签密度，更不能看到分数后扫阈值/覆盖率。
止损顺序：参数/身份/PTS/梯度路径/adapter隔离任一失败，先停工程；非测试匹配评估出现广泛退化则停8B主案回4B；若只是弱证据不确定，可明确标风险候选，但不改协议追分。线上比较结束后不从总分反向生成新测试假设。

最强反例仍是弱教师选择偏差。 假设教师系统性漏掉短暂高潮和转折，unknown mask只是“不惩罚漏标区”，并没有向模型提供这些漏掉正例；8B反而更精确学会教师偏好，网格头让错误边界更自信，离线弱指标改善，同时8B基础空间又比4B更差。这样“更大模型＋更合理输出头”两件看似正确的事叠加后，官方整包仍可能下降。因此我现在支持立即做8B小探针，但反对把“8B”本身当成提分证据。 

## 可见正文引用链接

- 开放访问CVF
+1: https://openaccess.thecvf.com/content/ICCV2023/papers/Lin_UniVTG_Towards_Unified_Video-Language_Temporal_Grounding_ICCV_2023_paper.pdf?utm_source=chatgpt.com
- R1@0.5: mailto:R1@0.5
- R1@0.5: mailto:R1@0.5
- R1@0.7: mailto:R1@0.7
- NeurIPS 会议论文集
+1: https://proceedings.neurips.cc/paper_files/paper/2021/file/62e0973455fd26eb03e91d5741a4a3bb-Paper.pdf?utm_source=chatgpt.com
- Hugging Face
+1: https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct/blame/main/config.json?utm_source=chatgpt.com
