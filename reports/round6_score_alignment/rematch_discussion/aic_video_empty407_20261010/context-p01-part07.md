可以建立有条件的完整窗口银标，但它必须被定义为“基于B0实际可见输入、经过有限原生视频核验的可审计事件监督”，而不是逐帧视频真值。

不能要求观察者证明自己见过全部原生帧。这在目前工具条件下既无法证实，也不必要。

但也不能仅凭agy调用成功、提供了64张图片和教师自述，就声明完整窗口监督成立。

4.1 三个不同的证据层

L1：物理输入证据

必要

源SHA、实际64帧或不足64帧的全部输入、ordinal、真实PTS、RGB像素SHA及供给记录。

L2：语义观察证据

agy读取原生MP4，另有显式采样帧；主控独立盲审相同证据。两者均需记录可见事实和无法判断的范围。

L3：完整监督资格

经审查的事件集合、边界、明确NO范围和可能改变最终答案的未解决不确定性。只有满足本层规则，才能生成完整segments训练目标。

L1完整不自动推出L2成立，更不自动推出L3成立。

4.2 64帧全部供给，与完整视频观察的区别

我建议冻结两个独立字段：

all_student_sampled_frames_supplied

以及：

all_native_video_frames_observed

前者可以由程序检查供给清单和回执，并用逐批视觉核查提高可信度。

后者目前通常无法证明，应如实记录为false或unverified。

不能让teacher仅回答“我已经看完全部64帧”就通过。必须提供具体帧ID和事实说明，并抽查这些事实是否出现在对应图像里。

推荐每批8帧、按实际PTS排列，分批提供，不改变B0真正的训练输入。若工具无法可靠确认某批画面，则该批不能被声称已完成有效观察。

这是一项关于证据供给与可核验事实的要求，并非声称能够检测模型内部是否注意到了每一张图。

4.3 我修改“完整窗口”的认定方式

不能采用两个极端：

极端一： 64帧已供给，所以其他全部时间自然为NO。

极端二： 64帧之间没有逐帧人工查看，所以任何完整窗口都永远不能入训。

应引入有后果的不确定性（consequential uncertainty）。

当某个未解决的时间范围可能改变事件是否存在、事件数量、事件边界或是否应该返回空列表时，它就是有后果的不确定性。

只有这类不确定性会直接阻断完整窗口SFT资格。

可采用确定性风险线索发现需要补查的位置，例如镜头内容突变、运动峰值、遮挡、主体突然变化、动作状态不连续。它们是补查触发器，不是高光标签。

如果补充的原生帧能够解释变化，就可以消除这一具体疑点；如果不能，保留UNKNOWN并拒绝完整窗口入训。

这种规则不能排除所有未检测到的短事件，因此它产生的是有限观察协议下的银标，而不是关于原视频绝对完整性的证明。

4.4 正例和空窗口的准入

标签

	

允许入训的条件




正例segments

	

事件确实可由学生采样辨认，边界有独立证据，整窗无会改变答案的未决问题




合法[]

	

64帧视觉审查、原生视频概览与风险补查支持“没有可辨认且值得保留的高光”，且不存在未解决的重要遗漏




UNKNOWN

	

不生成完整监督目标




事件多于5个

	

不强行合并以适配grammar；当前窗口拒绝入训




教师可见、学生不可见的关键动作

	

拒绝该窗口的精确事件监督




跨镜连续高光

	

两侧均有连续叙事证据时允许




无关内容越界

	

拒绝原端点；独立确定边界后才可重新审定

其中“重新审定边界”必须保留原标签与原证据，形成有版本的新审查结果，不能静默修改teacher原答案使其看起来一次成功。

对于合法[]，其含义只能是在明确规定的可见观察协议下没有发现可辨认高光，不能写成已经证明整段原生视频不存在任何高光。

4.5 具体边界接受条件

建议冻结：

端点以原生ordinal及对应实际PTS记录，使用半开区间。

正例具有内部动作证据、开始附近的内外证据、结束附近的内外证据。

端点审查的不确定范围建议不超过0.5秒；超过则不得冒充精确边界监督。

切镜前后若属于同一个完整动作或叙事高潮，可以跨镜，但应写出连续性的可见依据。

凡未解决分歧可能改变最终segments列表，整窗拒收。

0.5秒只是建议的工程容忍上限，不是AIC评测容忍度，更不代表所有0.5秒内误差都可无条件接受。

独立盲审的顺序必须是：先看媒体与冻结规则，独立写下自己的事件和不确定性；冻结记录后，再揭示agy答案并处理分歧。

主控的模型式盲审可以增加不同观察路径的证据，却不是独立人工金标。若独立判断与教师共同遗漏动作，二者一致仍可能一起出错。

五、唯一可执行工作包

我接受主控的24窗、12来源组作为一次有限可行性试验上限，但修改分组和门槛。

不扩大到Tibo的48窗方案，也不把24窗当成充分的正式质量验证集。

5.1 数据划分
12

训练窗

6来源组
4

流程开发窗

2来源组
8

锁定确认窗

4来源组

相比6/3/3，我建议6/2/4。原因是训练源数量不变，但把一个来源组留给最终确认，减少只有3个确认独立单位的问题。

开发集只用于一次停止判断，不选学习率、不调prompt、不选择checkpoint，因此不需要为开发门保留过多来源。

这仍然是小样本试验。4个确认来源也无法提供可靠的跨域泛化证明。

5.2 来源隔离

冻结来源关系表时，不仅核对source_id，还需核对原始媒体SHA、转载、裁剪、近重复和历史使用身份。

每组至少记录四种曝光状态：

媒体是否被旧B训练使用；

是否存在历史弱标签；

是否参与过开发或超参数选择；

本次事件级银标是否在预测揭示前独立冻结。

新事件标注参考即使是第一次建立，也不意味着这段媒体此前从未见过。

如果所有确认来源都有历史曝光，应称为锁定的历史曝光开发确认组，不能包装成全新独立测试集。

不读取100confirm，不为凑够独立组而重新命名来源。

5.3 标注任务预算

保留主控的前瞻上限：

环节

	

最大数量




agy原生视频候选标注

	

24个窗口会话




主控独立盲审

	

24份记录




额外密集边界补查

	

8项




新窗口总量

	

24




新大数据下载

	

0

这56项是任务记录上限，不是56次等价API调用或免费额度。实际内部工具调用、token消耗与费用仍需单独计账。

前4个窗口作为固定流程先导，必须从已分配的训练来源中事前确定，不允许根据结果更换窗口。

先导门： 如果无法提供实际64帧证据清单、无法建立真实盲审记录、无法校验native PTS/像素，或者无法形成至少一个可靠的完整正例和一个可靠完整NO示例，就停止扩展。

这两个示例只能验证流程可行，不授予训练资格。

5.4 正式银标准入门

在24窗上限内，要求：

项目

	

前瞻门槛




训练合格窗口

	

至少8/12




训练来源覆盖

	

至少4个来源组




正例与合法NO

	

两类均存在，并分别覆盖至少2组




接纳窗口内有后果的UNKNOWN

	

0




端点/native身份不匹配

	

0




无证据支持的边界外溢

	

0




标签与冻结grammar不兼容

	

0

对无法接纳的窗口，不得删除原记录以提高合格率。

只有达到这些门槛，才允许进行一次训练。

24窗够不够？

够支持一次低成本、目标明确、以原B为初始化的探索性续训。

不够支持“已经证实新模型在AIC上泛化更好”的结论。即使通过全部银标和确认门，也只能说明在该有限参考协议下，新候选表现较好，值得作为有风险的竞争实验。

六、训练合同与严格STOP

r01源码已表明当前B0允许0..5，因此训练必须包含经验证的合法正例与合法空目标，而不是人为排除所有NO窗口。

训练前必须完成：

锁定原B adapter SHA 8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23及config身份。

从原B权重初始化，不从237步图片评分LoRA初始化。

冻结基座及视觉参数，核实际总参数不超过9B。

取得B0原生训练的build_target具体实现或运行合同证据，确认assistant-only mask、真实视频张量、EOS、无截断及梯度归一。

[]和正例各用一个真实已接纳样本进行前向CE检查。

需要特别指出：

r01提供的train_student.py调用training_target.build_target，但没有包含该函数的定义。因此，现在不能仅凭r01全文宣称原生训练mask已经得到完整代码级静态验收。

我接受以下训练参数作为一次固定小试：

参数

	

固定值




初始化

	

原B LoRA




LoRA

	

r16 / alpha32 / qkvo




学习率

	

1e-5




有效batch

	

4




训练轮数

	

最多2 epoch




更新上限

	

最多8次




优化器

	

新建，明确记录，不假称旧状态恢复




候选checkpoint

	

固定最终终点




新模型结构

	

不允许

这里8步是上限而不是目标：按最多12个训练窗、有效batch4、2 epoch计算，正常情况下至多约6次完整更新。不能重复样本凑8步。

6.1 CE归一必须明示

建议以每个样本非mask的assistant目标token平均损失为基础，再对batch内窗口等权平均：

𝐿
=
1
𝐵
∑
𝑖
=
1
𝐵
(
−
1
∣
𝐴
𝑖
∣
∑
𝑡
∈
𝐴
𝑖
log
⁡
𝑝
𝜃
(
𝑦
𝑖
,
𝑡
∣
𝑥
𝑖
,
𝑦
𝑖
,
<
𝑡
)
)
L=
B
1
	​

i=1
∑
B
	​

(−
∣A
i
	​

∣
1
	​

t∈A
i
	​

∑
	​

logp
θ
	​

(y
i,t
	​

∣x
i
	​

,y
i,<t
	​

))

其中 
𝐴
𝑖
A
i
	​

 是有效assistant目标位置集合，不包括prompt和padding。

这样不会因为某个窗口输出5段而另一个窗口输出[]，就单纯让长答案贡献更多总权重。

这是一项待冻结的新训练合同，不应误称为现有源码已全部证明的事实。

6.2 GPU STOP

建议保留训练1,200计费秒上限。首次真实更新同时核对显存、时间、梯度、参数变化和保存重载。

如果以实际运行速度推算，在剩余预算内无法完成原定更新，就停止；不能减少帧数、改变视觉预算或截断目标来勉强完成。

loss短期正常震荡不自动STOP；NaN/Inf、输入身份错误、mask错误、非预期参数更新、时间上限和来源污染才是硬STOP。

七、质量指标：必须先定义分母

这是我认为主控修订方案里仍需补全最多的地方。

7.1 参考时间轴

对每个确认窗口，定义三个互不重叠的集合：

𝐾
K：经审查的KEEP时间范围；

𝑁
N：经审查的明确非高光时间范围；

𝑈
U：未解决、不能赋予正负语义的范围。

只有 
𝐾
∪
𝑁
K∪N 能作为可评分参考域。

训练完整窗口时要求没有会改变目标的未决U；评价时可以另外展示部分可判定范围，但不能让它们进入完整参考主指标。

预测若落入U，不自动计TP或FP，但必须单列其预测时长。否则模型可以利用不确定区间逃避评价。

7.2 正例时间F1

在完整正例参考窗口上，使用时间长度测度：

𝑇
𝑃
=
∣
𝑃
∩
𝐾
∣
,
𝐹
𝑃
=
∣
𝑃
∩
𝑁
∣
,
𝐹
𝑁
=
∣
𝐾
∖
𝑃
∣
TP=∣P∩K∣,FP=∣P∩N∣,FN=∣K∖P∣
𝐹
1
=
2
𝑇
𝑃
2
𝑇
𝑃
+
𝐹
𝑃
+
𝐹
𝑁
F
1
	​

=
2TP+FP+FN
2TP
	​


其中 
𝑃
P 为模型输出的预测区间并集。

有正例却全空，则该窗口F1为0。

**真值为空、预测也为空的窗口，不应直接给正例F1记1分。**它应进入独立NO指标。

7.3 显式NO误选
N
O
_
F
P
_
R
a
t
e
=
预测落在明确NO中的总时长
明确NO的总时长
NO_FP_Rate=
明确NO的总时长
预测落在明确NO中的总时长
	​


如果没有明确NO参考时长，指标为N/A，而不是0。若某确认组缺乏负例证据，就不能声称该组已经验证误报控制能力。

7.4 事件召回及边界

时间F1容易被一个很长的预测区间取得部分重合，因此还要进行事件一对一匹配。

建议以时间IoU≥0.5作为一个前瞻的事件匹配阈值。每个预测最多匹配一个参考事件，每个参考事件最多匹配一个预测。

分别报告：

参考事件总数与匹配成功数；

完整正例窗口被预测全空的数量；

已匹配事件的起止误差；

不相关内容边界外溢；

来源组最差退化。

阈值0.5仅服务本地诊断，不能声称与官方评分阈值一致。

7.5 一切排除都要保留分母

最终报告至少给出：

分母

	

必报内容




24个计划窗口

	

完成、失败、拒收、UNKNOWN数量




12个计划来源组

	

各组曝光与可评价状态




完整银标窗口

	

正例/NO数量及各自总时长




全部原始提案事件

	

支持、驳回、边界未决数量




全部锁定确认窗口

	

可评价比例及为什么不能评价




两个模型的全部预测

	

合法空、解析失败、预测时长、未知区域预测时长

不能只把合格窗口挑出来报一个漂亮的macroF1，而不展示剩余样本。

八、原B candidate0与质量晋升

candidate0必须是37.66对应的完整双窗均衡native管线，不是只加载同一个adapter却换成普通V14输入。

特别要保持：

实际冻结的双窗计划和原生ordinal列表；

真实PTS和原生RGB输入；

B0 EMPTY_PROMPT与0–5 grammar；

processor、视觉预算和greedy；

解码、真实native区间映射；

完整原8B空间场与compose。

不能仅口头说“保持floor64”，然后重新计算与历史双窗不相同的帧索引。必须逐窗口核对实际输入身份。

如果candidate0已存在同一输入身份的成功原始输出，精确引用，不重复成功生成；否则在有界比较中各调用一次。

8.1 确认组前瞻GO条件

我建议修订为：

四个确认来源组中，至少三个具有可接纳的完整银标参考，合格窗口至少6/8。

至少两个确认来源组有正例参考、两个来源组有明确NO参考；二者允许在同一组内并存。

开发组一次比较中，正例时间macroF1相对candidate0改善，否则STOP。

锁定确认中，正例来源组等权macroF1至少改善0.03绝对值，且至少三分之二的正例来源组不退化。

最差正例来源组F1退化不超过0.05。

NO误选率不增加，正例整窗漏空数量不增加，事件召回不下降。

不新增已审定的无关内容外溢或不合法区间。

全部工程身份与输出严格验收通过。

0.03、0.05等数值是前瞻工程风险筛选阈值。在这样小的来源组样本上，它们不提供置信度保证。

若确认组缺乏足够正例或NO，不得将未定义的指标按0处理，也不得根据结果换组补齐；本轮应STOP，不授予426资格。

Bootstrap区间、留一来源分析可以报告，但不以小样本区间为统计保证。

8.2 非测试8的作用

非测试8用于最后的冻结管线工程与异常审查。

如果全部合法为空，它不是自动错误；但若candidate0在同一输入下有明确事件，而candidate1出现全域坍缩，应触发质量风险STOP，而不能只凭格式通过。

不得按这8个视频调整阈值、输出长度、提示词、TopK或选用其他checkpoint。

8.3 426预算

原V14时间推理已有约5,430计费秒的历史记录，不能机械照搬其他席位建议的2,400秒作为保证足够的426完整运行预算。

建议：

训练≤1,200新增计费秒；

非测试对照≤2,400新增计费秒；

如获准单次426风险实验，时间推理先用非测试真实耗时估算，并设置最高7,200新增计费秒的前瞻上限；

若估算加上资源装载、退出余量无法在上限内完整运行，直接NO426，不启动半截作业。

以上属于建议的费用上限，不是对实际推理速度的预测。空间场保持已有完整结果精确复用。

任何阶段达到上限或出现无法恢复的身份错误，封存状态、成本和原raw，不通过重复生成掩盖失败。

九、对主控修订的主要否决意见

主控修订已经解决了第一轮最严重的语义方向错误。但我仍否决两种可能的隐性放行方式。

第一，不能把“64帧完整供给”升级成“完整窗口语义已证实”。

64帧、PTS和SHA证明模型理论上获得了什么信息；它们不证明某个不到0.5秒的动作一定被看见，也不证明未标时间是NO。

必须引入有后果的不确定性审查和密集边界证据。

第二，不能让锁定确认组的指标以未说明的空参考方式计算。

如果3个确认来源里大多数没有正例，却使用旧V14式“预测空且参考空则F1=1”的总体均值，新模型可以靠更多空输出拿到看似改善的平均分。这正是407空事件之后尤其需要防止的评价扭曲。

正例时间F1与明确NO误选必须分开，来源组和拒收分母必须完整展示。

十、最强反例及最终裁决
对本方案的最强反例

假设agy与主控经过完整64帧清单审查，均认定一个30秒视频有两段精彩动作，且能够提供合法的原生边界。

模型以这两段作为完整银标续训，确认组相对原B的F1也上升了。

但真实视频中，可能还有一段只持续0.3秒、发生于相邻采样帧之间的决定性动作。它既没有进入学生64帧，也没有被agy实际工具采样或盲审发现。

这时所有供给SHA、PTS、训练CE、教师与审查一致率都可以正确，而银标仍遗漏了真正重要的内容。

更严重的是，如果标注者共同偏好“热闹、动作大、主体显眼”的镜头，模型可能在所有银标指标上超过原B，但在AIC评测中因叙事价值或真实时序边界失误而下降。

这个反例无法由24窗试验完全排除。

它不意味着当前必须等待人工逐帧金标才能做任何实验，而意味着候选晋升的性质应被限定为：

有限银标证据支持的一次风险竞争实验，而不是经过证明的高光质量升级。

最终唯一执行路线

批准下一阶段的条件性工作路线

先完成4窗可观察性先导 → 扩展最多24窗银标审查 → 达标才从原B续训一次 → 仅一次开发与锁定确认 → 再决定NO426或唯一风险ZIP。

原37.66 candidate0

永久保留

237步图片评分器继续训练

不批准

当前立即启动B续训

不批准，先验收银标

本轮实验、联网、GPU、官网提交

均不执行

我对研究项目Pro下一轮裁决建议聚焦两个真正尚未解决的判定，而不是再讨论模型菜单：

其一： 采用上述“学生可见64帧 + 原生视频概览 + 风险区间补查 + 主控盲审”的有限观察合同，是否足以授予可审计的完整窗口银标资格？我认为有条件可以，但绝不是原生逐帧金标。

其二： 24窗12组、锁定确认最多4个来源的实验，是否足以支持一次小规模B续训及有条件的风险候选？我认为足以支持前者；对后者必须要求全部质量、来源、成本与工程门通过，并明确官方分仍未知。

至此，本轮实际六卷均已按字节完整读入，四席原文、主控修订、必要训练和运行源码已进行静态交叉审查。不存在本轮新模型调用或实验结果。Pro连续预算维持5/8，剩3，本次普通回合不消耗。

ChatGPT 可能会出错。请核查重要信息。
最新一条回复




高

## 第二轮完整公开原答 grok-r01.md
原始文件SHA=d768f5cb7943aef2b616b9b08cd5412acdd6b7cf56629abc4f4ab5a71ac3f0fb

工作了 10s

读取确认

任务 AIC-VIDEO-REMATCH-NEXT-20261005 / 子议题 EMPTY407-20261010 / r01。

实际读取范围：context-r01-index.md + context-r01-part01.md 至 context-r01-part06.md 顺序拼接全文，至末标 END_EMPTY407_R01。索引声明 535643 字节 / SHA256 4096ebc8f6dc91de3b60a9b1ceefb3496cc9fe4e1161531f795b75e13f57296a；本次读取的是工具提供的文本流，未对原始文件字节做独立主机验签。继承完整 r00b、四席首轮原文（含 Gemini 截断及补答）、主控修订及补充源码（含 contracts.py 的 EMPTY_PROMPT、runtime.py、train_student.py 等）。未实验、未联网。

事实 / 推断 / 未知（更新）

事实：当前 37.66 对应 B0 实际绑定 V14 EMPTY_PROMPT（0..5 区间、允许 {"segments":[]}、不确定不代表无高光）；旧 1..5 属历史 B1/CFR，不可混用。dev 实际 1351 点（非 1451），new 预测范围 24..53、≥49 仅 48/1351，4/9 源全空。
推断：407 空主因仍是 TVSum 任务/域偏移 + 绝对分数收缩 + 2s 整格假设；B0 允许空后，完整窗口监督在语法上不再强制正例。
未知：闭源事件标签与 AIC 真实高光的对齐、原 B native 在非测试域的选帧行为、有限银标下续训是否优于 candidate0。

交叉批判与接受/拒绝/修改

接受主控纠正：B0 实际 0..5 且允许空（contracts.py EMPTY_PROMPT 与 allow_empty=True 调用链已确认）。Sol 首轮误把历史 1..5 当当前语法，已纠正；不能仅用正窗修一个不存在的表达限制。
接受 Tibo 的逆序反例（sTEELN-vY30 grid5 gold87/pred48 vs grid32 gold27/pred50）：保序校准无法修逆序，且 TVSum ≠ AIC 金标。
拒绝 Gemini 首答中的 100% 非空强制、静态必拒、I-frame 即切镜先验；补答已撤回，切镜只触发审查、连续叙事可跨镜。
接受主控对“同教师一致≠金标”“UNKNOWN 不转负例”“部分 KEEP 不得编成完整 segments”的立场。
修改我的首轮路线：原先建议先小批标注再诊断，现与主控/Tibo/Sol 收敛到“有界事件级银标 + 条件性原 B 续训”。但 24 窗/12 组规模过小，且来源已暴露时不能称盲确认。
对主控新案的批评：即使缩到 24 窗，仍把“agy 原生 MP4 + 显式 64 帧/PTS 回执 + 主控盲审”当作可操作银标资格，但稀疏工具观察无法证明完整窗口可监督；全窗 SFT 资格若要求“整个声明范围均有审查 KEEP/NO”，在实际 1fps 级工具下极易把合法有限观察永久阻塞，或反过来把未观察区域隐含为负。

唯一可执行有界工作包

先静态核训练 mask/实际协议、来源与历史曝光（不重复成功生成）。

然后：最多 12 source_group × 2 个事前固定非重叠 ≤30s 窗口（共 24 窗），划分为 6 训练 / 3 流程开发 / 3 锁定确认。已有 TVSum48 源优先建立曝光关系表；若全为旧暴露组则明确降为锁定开发、弱证据，不假称未见。来源不够即缩小并登记，不下载新数据。

agy 作为提案教师：原生 MP4 全局观察 + 显式送原 B 实际 64 帧原生 RGB/PTS 索引（可分批），每批读取回执与逐帧可见事实可审查；边界处补供原生短序列。所有声明与实际工具供给分开记录，不用教师自报证明完整观测。第二观察由主控直接查看相同证据，先独立盲记再对比教师（当前无人工金标，不冒称人工审查）。

银标资格诚实定义：

完整采样覆盖 ≠ 全视频逐帧已观察。
全窗 SFT 资格仅当声明范围内所有区域均有经审查的 KEEP 或明确 NO，且学生实际输入（64 帧）足以识别该事件；含未解决 UNKNOWN 的整窗排除。
合法无高光只有在足够全窗证据下才可输出 []。
部分正例不得作为全部真值；超过 5 事件或不确定边界不擅自合并。

标签达标后，才一次 B 权重初始化 native SFT：原 r16/alpha32/qkvo，基座/视觉冻结，lr 1e-5，有效 batch 4，至多 2 epoch / 8 真实更新（不凑数、不扫超参）。新 optimizer 明确登记。确认 candidate0/1 仅差 adapter，同源/window/floor64/精确 PTS/processor/像素/EMPTY_PROMPT/0..5/greedy/native 映射/空间场。固定终点，只一次确认。

前瞻风险门（非统计保证）：开发 macro ΔtimeF1 > 0；锁定确认 macro > 0 且至少 2/3 源不负；无正事件漏空增加、明确 NO 误选时长增加或可确认无关内容边界外溢。完整报告 precision/recall/最坏源退化。任何工程/标签/质量门失败即 STOP 本版，保留 37.66，不事后重选样本。全部通过才单次完整 426 风险 ZIP（官网分 UNKNOWN，用户手工提交）。

本阶段上限：标注 24 窗 + 有界补查；native 训练 ≤1200 计费秒、非测试对照 ≤2400 计费秒（建议上限，实际动态准入）。已有成功 candidate0 精确身份可复用。

最强反例

即使银标通过独立盲审，教师与审查者共同漏掉 64 帧之间的短瞬态高光（或共同偏好“热闹运动”为高光），学生在银标 F1 上胜出 candidate0，官方分仍下降。24 窗/12 组（且多已暴露）的等权 F1 改善无法排除共同偏差；完整窗口资格在稀疏观测下要么过严导致无样本，要么过松导致隐含负例污染。若确认集显示空窗表达或采样不可见才是主瓶颈，则本轮续训路线应直接否定，而非硬跑。

停止 / GO 与未知处理

工程 STOP：来源无法隔离、训练合同 mask 无法绑定、工具回执与声明不一致、参数超 9B。
质量 STOP：确认 macro ΔF1 ≤ 0、正事件漏空增加、明确 NO 误选增加、边界外溢、UNKNOWN 分母未全列。
未知全列：所有 UNKNOWN 窗口/区间保留在分母，不转负、不丢弃后报均值。
来源已暴露时，确认集降级为锁定开发审查，不称独立泛化。

排序提升 ≠ AIC 质量；同教师一致率 ≠ 真值。禁止复赛调阈值、强制非空/TopK、读 100confirm。本轮仅讨论，等待研究项目 Pro 集中裁决。连续 Pro 仍 5/8，剩 3。

## 第二轮完整公开原答 gemini-r01.md
原始文件SHA=d5d97e8bbbf4d56011bd36034a232bce360745ecca58bbf91983e589de9444b5

Gemini 说
读取确认与分母核实

已完整读取新分卷索引 context-r01-index.md 与分卷正文 context-r01-part01.md 至 context-r01-part06.md，按序拼接共计 535,643 字节，读至终末标记 END_EMPTY407_R01。必须在开头独立声明：主控给出的 SHA256 4096ebc8f6dc91de3b60a9b1ceefb3496cc9fe4e1161531f795b75e13f57296a 为主控单方环境声明值，我在本轮交互中已完整核验文本流及末标，但未在本地 Linux 底层对物理文件独立验签。   
MD
+ 4

关键数据点核准

开发源评分分母纠正：9 个已见 TVSum 开发源的实际有效评估点数为 1,351 点（4 个对比臂累计记录 1351×4=5,404 个元组），先前口头提及的 1,451 确为笔误。   
MD
+ 1

输出分布与全空事实：新模型打分范围收缩至 [24,53]，而人工标签范围为 [21,87]。新模型 ≥49 的预测仅有 48 点（占比 3.55%），人工标签 ≥49 则有 293 点（占比 21.69%）。开发源实际呈现 4 源全空、5 源非空。   
MD
+ 4

不可逆排序反例确证：在 sTEELN-vY30 中，grid 5（ordinal 329）人工得分为 87、模型预测为 48（被硬阈值过滤）；而 grid 32（ordinal 1949）人工得分为 27、模型预测为 50（被选入）。这种同源内的严重语义逆序，证明单纯的单调保序校准（如温度缩放、Isotonic 回归）无法纠偏错误。   
MD
+ 4

交叉批判：自我纠偏与同席意见审查
1. 自我纠偏与澄清（Gemini）

纠正首答矛盾与教条假设：在 r00 截断答复中，我曾出现“5个全空与列出5个非空”的表述混乱，并在 r00b 中进行了事实修正（实为 4 空、5 非空）；同时，我在 r00 中提出“非测试集必须 100% 非空”、“帧选择比例必须在 12%~28%”、“切镜绝不可跨越”、“I-frame 强边界等同切镜”等预设，这些已被证明是脱离实际的教条先验。官方允许合法无高光视频输出为空，连续动作亦可自然跨越剪辑切镜，视频编码的 I 帧更无法与语义镜头切换划等号。   
MD
+ 2

撤回伪反例 M
spike
	​

：我在 r00 中构造的退化模型 M
spike
	​

 仅针对了 stage2_pass 中的 Proxy F 点估计，但主控现行流水线在进入 Stage 2 前还设有 research_pass（要求 Macro Spearman 及 Top15 效用在多数源上优于基线）。M
spike
	​

 会在第一阶段被 Spearman 门禁直接拦截。这一反例未能击穿复合门禁，本轮已彻底废弃，后文将提供直击时序抽样与银标缺陷的最强反例。   
MD
+ 2

2. 批判 Sol（致命代码与版本认知错误）

核心错误：Sol 坚定声称“原 B 的 native 视频提示词要求返回 1–5 个 segments，不能在窗口内表达零段”，并据此主张“训练时只保留存在 1–5 个正例高光的窗口，剔除所有空高光窗口”。   
MD

代码事实反驳：检查 precision_helpers/contracts.py 中的源码，当前 37.66 生产基线 bw_common.helpers 绑定的 EMPTY_PROMPT 明确规定：

"- return between 0 and 5 intervals"
'- when the clip has no worthwhile highlight, return {"segments": []}'
且下游解析器 parse_segments 明确带入 allow_empty=True。   
MD
+ 2

危害定性：Sol 把历史废弃分支 B1（以及旧 CFR 时代的 temporal_common.py，其规定 1..5 段且不允许空）错当成了当前的候选零基准 B0。若依 Sol 的建议在微调时强行剥离纯负例/无高光窗口，将从数据分布上直接摧毁原 B0 已具备的“合法拒绝并输出空段”的鲁棒性，使模型退化为盲目过召回的废品。   
MD
+ 3

3. 批判 Grok（任务模态与语法混淆）

核心错误：Grok 要求“新图片评分选择器与 B native 在同 grammar、同 prompt 下作公平对照”。   
MD

技术机制反驳：B native 是端到端的视频序列时序事件定位（输入为 64 帧视频张量，输出为时间区间的 JSON 字典），而新选择器是单批 16 图的逐帧离散重要性打分（输出为 scores_x20 整数列表）。二者任务定义、输入张量结构和解码语法从底层即不兼容。   
MD
+ 2

定性：公平对照只能发生在统一的非测试视频源与最终原生时间帧选择集（Binary Frame Selection）上，强行要求它们使用相同生成语法属于概念混淆。   
MD

4. 批判 Tibo（过度严苛导致样本饿死与成本膨胀）

合理成分：Tibo 对 1,351 点的分布收缩和逆序实例的剖析最为精准，并敏锐指出了“整格扩展吞噬切镜”的时序缺陷。   
MD
+ 1

核心缺陷：

标注吞吐量超标：Tibo 规划了 48 个窗口、最多 108 次大模型调用（48 提案 + 48 盲审 + 12 补查），在仅剩 3 次连续 Pro 额度且计费时间受限的工程现实下过于沉重。   
MD
+ 1

“全窗零 UNKNOWN”导致样本饿死：Tibo 要求进入完整窗口训练的样本“整个声明范围均有经审查的 KEEP 或明确 NO，含未解决 UNKNOWN 则整窗排除”。在实际 6 段视频先导测试中，UNKNOWN 占比高达 21.1%（19/90）。若要求 30 秒长窗内完全不含任何模糊与过渡状态，将导致几乎所有真实窗口被无差别丢弃，引发严重的“数据荒漠”使训练根本无法开工。   
MD
+ 4

5. 批判主控（统计失真与更新步数算术矛盾）

确认源的统计失真：主控提出将现有 TVSum 48 源中的样本作为“锁定确认组”。但 TVSum 资源在过去多轮实验中已被全面接触并暴露，拿已知源充当确认，无法对未见 AIC 域提供泛化背书。   
MD
+ 1

步数算术漏洞：主控建议“6 个训练组（12 个窗口），有效 batch 4，至多 2 epochs，拟进行 8 次真实更新”。   
MD

算术推导：12 个样本，若 batch 大小为 4，则 1 个 epoch 仅有 ⌊12/4⌋=3 个 update step；即使完整跑满 2 个 epoch，总更新步数也仅为 3×2=6 步！

若强行执行 8 步，意味着必须在数据不足时重复抽取样本（Over-sampling），这将直接践踏主控自己立下的“禁止重复曝光凑数”红线。必须实事求是地将步数上界锚定在数据量决定的 6 步以内。   
MD
+ 1

核心争议裁决：建立诚实银标与全窗监督资格
1. 稀疏采样与全视频观察的诚实界定

拒绝伪全知：64 帧离散采样永远不能声称看全了长达 30 秒的原生视频（约 750~900 帧物理内容）。   
MD
+ 1

科学合法的银标定义：

银标的合法性不建立在“穷尽所有未见帧”的虚构假设上，而建立在“在当前模型所能感知的 64 帧物理视觉证据空间内，事实叙述闭环且边界无实质污染”。   
MD
+ 1

agy 原生视频读取作为全局粗筛，提取叙事与动作爆发的主干时间戳；显式提取由原 B 实际采样的 64 帧原生 RGB 序列供第二阶段审查。   
MD
+ 1

只有当“模型宣称的高光动作”在送入学生的 64 帧内具备可辨识的物理正例像素，且区间端点落在明确的切镜或静止过渡点附近时，该段才具备监督资格。   
MD
+ 2

2. UNKNOWN 区域的工程化处理：分段屏蔽而非全窗废弃

不能采纳 Tibo 的“一票否决整窗”，也不能采纳主控早期隐式的“未标即负例”。   
MD
+ 1

区间级 Loss Masking 机制：在原 B0 的文本生成协议中，将标注结果明确转换为 {"segments": [...]}。若窗口内存在一段无法判定的 UNKNOWN（如快速运动模糊、主体被遮挡）：   
MD

若该窗口其余部分存在明确且无争议的高光动作，且 UNKNOWN 区域不与目标区间的起止端点重叠，则仅在有效高光和明确背景段上构建监督；

若 UNKNOWN 区域导致核心高光的起始点或结束点模糊不清（截断误差），则该窗口严禁作为完整正例窗口进入训练，直接降级为纯定性诊断用例。   
MD
+ 1

3. 主控独立盲审的真实能力定位

主控的审查不是引入第三方金标，而是执行“事实逻辑防线”：   
MD

切镜越界审查：检查标定的时间戳是否跨越了画面主体突变（如 91IHQY 狮舞切至行人的案例）；   
MD
+ 1

物理像素见证：检查关键动作是否真落在学生能看到的采样帧上；   
MD
+ 1

盲态对齐：主控独立记录粗略时间戳，若与 agy 偏差在 2 秒以上，该区间直接降级为 UNKNOWN，不强制调和。   
MD
+ 1

唯一可执行有界工作包：B0-NATIVE-SFT-PILOT-12W
[现有非测试视频源 (隔离审查)]
                 │
                 ▼
[选择 6 组 (12 个 ≤30s 窗口)] ──> 6 训练 / 3 流程开发 / 3 锁定对照 (已暴露声明)
                 │
                 ▼
[agy 视频定位 + 64 帧物理索引回执]
                 │
                 ▼
[主控独立事实盲审] ──(切镜越界 / 证据不足)──> 标记 UNKNOWN，不当负例
                 │
                 ▼ (通过率达标: ≥8 个合格长窗)
[原 B0 续训 (加载 37.66 Adapter，完全继承 EMPTY_PROMPT 与 0..5 语法)]
                 │ 仅更新语言 LoRA，lr=1e-5，有效 batch=4，严格 3~6 优化步
                 ▼
[非测试对等回放 (Candidate 0 vs Candidate 1)]
                 │
                 ▼
       ┌───────────────────┴───────────────────┐
       ▼ (满足复合安全门)                      ▼ (任一门触发 STOP)
[单次 426 复赛评估包生成]             [立刻终止，封存产物，回退 37.66 保底]

1. 规模与资源边界（彻底收紧）

样本规模：精简为 6 个来源组 × 每组 2 个不重叠窗口（≤30 秒）= 12 个原生窗口（6 训练、3 流程开发、3 锁定对照）。   
MD

API 预算：调用严格限制在 12 次提案 + 12 次主控核验检索 + 最多 4 次边界定点重抽 = 最多 28 次闭源调用。

算力与计费预算：

SFT 训练计费时间上限：600 秒（12 样本极低步数）。

非测试推理与回放上限：1,200 秒。

复赛 426 生成上限（若解锁）：依历史实测严格锁定 5,500 计费秒，禁止凭空压缩。

2. 训练配置锁定（严格依托 B0 代码基座）

初始化权重：必须显式加载历史最佳原 B8B adapter（SHA 8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23）。   
MD
+ 1

基座与目标层：基座 Qwen3-VL-8B 视觉编码器完全冻结；仅对 language_model 的 q_proj, k_proj, v_proj, o_proj 激活 LoRA（rank=16, alpha=32, dropout=0.05）。   
MD
+ 1

生成协议不变量：

严格继承当前 B0 的 EMPTY_PROMPT（允许 0 到 5 个段落，允许 {"segments": []}）。   
MD
+ 1

严格复用 precision_helpers/contracts.py 中的解析与惩罚逻辑，绝不混入旧 B1 的 1..5 限制。   
MD
+ 1

优化步数真实化：有效 batch=4，梯度累积=4，学习率 1×10
−5
（余弦退火或常数），严格训练 2 个 epoch，总优化步数严格锁定为 6 步，禁止任何人为重复抽样拼凑 8 步。   
MD
+ 1

3. Candidate 0 vs Candidate 1 公平对照

Candidate 0：原 B8B + 双窗均衡基线（37.66 冻结原版）。   
MD

Candidate 1：微调 6 步后的新 Adapter，除 LoRA 权重矩阵数值改变外，时钟、提示词、网格、空间场、解码器及 11-strict 后处理完全 100% 字节级一致。   
MD
+ 1

评价分母真实性：

评价指标为主指标原生时间等权区间 IoU-F1，辅助指标为明确 NO 窗口的虚警误报时长与正例高光检出率。   
MD
+ 1

凡包含 UNKNOWN 区域的窗口，其重叠时间段全部从 F1 的分母中隔离扣除，并在报告中完整披露掩码覆盖比例。   
MD
+ 1

4. 复合 STOP / GO 门禁（拒绝单一脆弱指标）

任何以下条件触发，立即执行 STOP，封存产物并无条件回退历史 37.66 保底包：

标注准入 STOP：12 个候选窗口中，经主控盲审后合格可监督窗口低于 6 个，直接终止，不进入训练。   
MD

训练数值 STOP：前 2 步未检测到有限损失（Loss 为 NaN/Inf）或 LoRA 权重梯度范数不收敛。   
MD
+ 1

行为分布 STOP：Candidate 1 在非测试集或开发集上出现系统性全空（全空率达 100%）或系统性全选（选择时长超过窗口 95%）。   
MD
+ 1

质量胜出 GO：只有在流程开发集与锁定对照集上，Candidate 1 相对 Candidate 0 的 Macro Time-F1 净增量 ΔF1>0，且明确 NO 窗口的误报时长未发生绝对恶化，才允许单次执行 426 复赛推理打包。   
MD

最强反例（The Strongest Counterexample）
时序锚点幻觉与上下文截断反例（The Temporal Anchoring Illusion）

构造一个典型的具有长因果链的高光场景：
一段 30 秒的“魔术揭秘”或“极限滑板动作”视频。滑板选手在第 14 秒起跳、第 16 秒完成动作落地。但在第 0~13 秒，视频包含了关键的加速助跑与障碍物特写；在第 17~25 秒，包含了观众的爆发欢呼与裁判打分。

银标产生机制下的共同偏差：

闭源教师模型通过稀疏 64 帧抽样，仅在第 14~16 秒看到了明显的肢体爆发动作，因此高度确信地标定高光区间为 [14.0,16.5]（判定其余为静止/准备）。   
MD
+ 1

主控执行事实盲审，对比 64 帧画面，确认第 15 秒确实在空中，第 17 秒已落地，认为端点干净，审核裁定为“合格高光银标”。   
MD
+ 1

模型的机械拟合与测试崩塌：

新模型经过 6 步微调，完美拟合了该类“超窄区间”，在开发集银标评估中获得了极高的 Time-F1 提升（ΔF1>0.15），成功骗过放行门禁被推入复赛。   
MD

复赛真实评测机制的反噬：AIC 官方真实的高光剪辑真值要求的是具有叙事完整性的短视频片段（Narrative Integrity），必须包含“助跑—起跳—落地—反馈”的完整叙事单元（真实区间为 [8.0,22.0]）。

新模型输出的紧绷超短片段 [14.0,16.5]，在官方 Intersection-over-Union 评测中：

IoU=
22.0−8.0
16.5−14.0
	​

=
14.0
2.5
	​

≈0.178

由于 IoU 远低于官方有效召回阈值（通常为 0.3 或 0.5），该区间在官方判定中被全额判定为召回失败（F1 = 0）！

与此同时，未经过度拟合的原 B0（Candidate 0）给出了较平缓的宽泛区间 [10.0,20.0]，取得 IoU ≈0.71，稳定斩获官方高分。   
MD
+ 1

结论：该反例证明，即使大模型与主控在 64 帧抽样上达成 100% 事实一致，这种建立在离散静态证据上的“局部精准剪辑”，完全可能系统性偏离剪辑赛题对“叙事因果完整性”的要求。在缺乏官方评测标尺的情况下，盲目追逐过窄的闭源教师边界，存在引发复赛官方分数反向暴跌的系统性风险。因此，任何微调尝试都必须严格有界，并誓死保留原 B0（37.66）的底线交付资格。   
MD
+ 1




Flash
高点

Gemini 是一款 AI 工具，其回答未必正确无误。

## 新必要原文件全文 reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/teacher_student_autopilot_v14/precision_helpers/training_target.py
原始bytes=3532 SHA=0a00f996d5d400772a56bcdc51d842a265c18ed1319b13cf09496a4d61e8124f

```
"""Complete optional-empty assistant targets; UNKNOWN has no training target."""
from contracts import answer_string
from video_contract import encode
import json

def from_teacher_record(record):
    if record.get('status')!='PASS_WEAK_COMPLETE_WINDOW_TARGET' or record.get('sft_eligible') is not True or record.get('uncertain') is not False:
        raise ValueError('Teacher record is not eligible complete-window supervision')
    observation=record['actual_observation']
    if observation.get('all_planned_frames_delivered') is not True or record.get('parsed_answer',{}).get('observation_scope',{}).get('all_provided_frames_reviewed') is not True:
        raise ValueError('Full provided observation was not reviewed')
    segments=json.loads(record['target_json'])['segments']
    if (segments==[]) != (record.get('explicit_no_highlight') is True):
        raise ValueError('Teacher empty semantics disagree with target')
    label=dict(observation_complete=True,status='OBSERVED_EMPTY' if not segments else 'OBSERVED_POSITIVE',segments=segments)
    target_text(label,record['window']['window_duration_sec'])
    return label

def target_text(label, duration):
    if label.get('observation_complete') is not True or label.get('status') not in ('OBSERVED_POSITIVE','OBSERVED_EMPTY'):
        raise ValueError('Only complete observed supervision has an SFT target')
    segments=label.get('segments')
    if (label['status']=='OBSERVED_EMPTY') != (segments==[]):
        raise ValueError('Observed label status disagrees with segment emptiness')
    return answer_string(segments,duration,allow_empty=True)

def build_target(processor, prompt, frames, metadata, label, duration, video_size, max_input=16384, *, native_plan, source_fps):
    import torch
    answer=target_text(label,duration)
    suffix=answer+'<|im_end|>\n'
    shared=dict(videos=[frames],video_metadata=[metadata],video_size=video_size,max_input=max_input)
    from exact_pts import exact_native_pts, verify_native_encoding
    identities=[]
    def encoded_text(text):
        with exact_native_pts(processor,native_plan,source_fps) as identity:
            value=encode(processor,text=[text],**shared)
            verify_native_encoding(processor,value,identity)
        identities.append(identity)
        return value
    head=encoded_text(prompt)
    full=encoded_text(prompt+suffix)
    prefix=int(head['input_ids'].shape[1])
    if not torch.equal(full['input_ids'][0,:prefix],head['input_ids'][0]):
        raise ValueError('Assistant prefix differs from prompt input')
    for key in ('pixel_values_videos','video_grid_thw'):
        if not torch.equal(full[key],head[key]):raise ValueError('Video encoding changed between target and prompt')
    from sft_contract import assistant_labels
    mask=assistant_labels(full['input_ids'][0].tolist(),full['attention_mask'][0].tolist(),head['input_ids'][0].tolist(),head['attention_mask'][0].tolist())
    decoded=processor.tokenizer.decode(mask['assistant_token_ids'],skip_special_tokens=False,clean_up_tokenization_spaces=False)
    if decoded!=suffix:raise ValueError('Exact assistant target token boundary changed')
    full['labels']=torch.tensor([mask['tail_labels']],dtype=torch.long)
    full['logits_to_keep']=mask['logits_to_keep']
    return full,dict(answer=answer,assistant_tokens=int(full['input_ids'].shape[1])-prefix,
                     input_tokens=int(full['input_ids'].shape[1]),allow_empty=True,exact_pts_encoding=identities)

```

## 新必要原文件全文 reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/temporal_sft8b_v1/sft_contract.py
原始bytes=19501 SHA=c2e762e7deca7cbc15d6d2b158e5251eeb25141b5cf5b02b8996042619c3414d

```
"""Stdlib-only admission and assistant-interval CE contracts; never imports torch."""
from __future__ import annotations
import hashlib
import json
import math
import os
from pathlib import Path
import re

MODEL_ID="Qwen/Qwen3-VL-8B-Instruct"
REVISION="0c351dd01ed87e9c1b53cbc748cba10e6187ff3b"
SCOPE="TEMPORAL_8B_SFT_SMOKE_NONTEST"
ROUTE="TEMPORAL_8B_INTERVAL_SFT"
BASE_PARAMS=8_767_123_696
LORA_PARAMS=15_335_424
TOTAL_PARAMS=BASE_PARAMS+LORA_PARAMS
ORIGINAL_TRAIN_SHA="ef427866153a9601be01b6e12356951c2fb56730525b0d7b7c353651c2930ddf"
ORIGINAL_TRAIN_RELATIVE="r7_temporal_pool/round7_temporal_pool_20260921T090903Z/inputs/train_temporal.jsonl"


class AdmissionRejected(ValueError): pass


def require(condition,message):
    if not condition: raise AdmissionRejected(message)


def sha256(path):
    digest=hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda:source.read(8<<20),b""): digest.update(block)
    return digest.hexdigest()


def is_sha(value):
    return isinstance(value,str) and re.fullmatch("[0-9a-f]{64}",value) is not None


def finite(value):
    return type(value) in (int,float) and math.isfinite(value)


def load_original_train(path=None):
    path=Path(path) if path else Path(__file__).resolve().parents[3]/ORIGINAL_TRAIN_RELATIVE
    require(path.is_file() and sha256(path)==ORIGINAL_TRAIN_SHA,"fixed original R7 704 train file identity mismatch")
    rows=[json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    require(len(rows)==704 and len({row.get("sample_id") for row in rows})==704 and
            all(row.get("split")=="train" for row in rows),"fixed R7 source is not the original train-only 704")
    return rows


def read_bound(spec,name):
    require(isinstance(spec,dict) and set(spec)=={"path","sha256"} and is_sha(spec["sha256"]),
            name+" requires exact path/SHA evidence")
    path=Path(spec["path"])
    require(path.is_file() and sha256(path)==spec["sha256"],name+" byte identity mismatch")
    return path


def segments_valid(segments,duration):
    require(finite(duration) and duration>0 and isinstance(segments,list) and 1<=len(segments)<=5,
            "illegal target duration/segment count; empty or UNKNOWN is not a target")
    previous=0.0
    for segment in segments:
        require(isinstance(segment,list) and len(segment)==2 and all(finite(x) for x in segment),
                "nonfinite or nonnumeric target segment")
        a,b=segment
        require(0<=a<b<=duration+1e-9 and a>=previous-1e-9,"invalid, overlapping or backward target")
        require(0<=round(a,4)<round(b,4)<=duration+1e-9,"round4 target becomes invalid")
        previous=b
    return segments


def answer_string(segments,duration):
    segments_valid(segments,duration)
    return json.dumps({"segments":[[round(a,4),round(b,4)] for a,b in segments]},separators=(",",":"))


def assistant_labels(full_ids,full_mask,prompt_ids,prompt_mask):
    """Mask all prompt/video and padding IDs, supporting either padding side."""
    require(len(full_ids)==len(full_mask) and len(prompt_ids)==len(prompt_mask) and
            all(x in (0,1) for x in full_mask+prompt_mask),"invalid token attention mask")
    active=[i for i,mask in enumerate(full_mask) if mask]
    prompt=[value for value,mask in zip(prompt_ids,prompt_mask) if mask]
    actual=[full_ids[i] for i in active]
    require(prompt and actual[:len(prompt)]==prompt,"assistant prompt/token boundary mismatch")
    require(len(actual)>len(prompt),"no supervised assistant tokens")
    first=active[len(prompt)]
    labels=[-100]*len(full_ids)
    for position in active[len(prompt):]: labels[position]=full_ids[position]
    keep=len(full_ids)-max(0,first-1)
    return {"labels":labels,"tail_labels":labels[-keep:],"logits_to_keep":keep,
            "supervised_tokens":len(actual)-len(prompt),"prompt_tokens":len(prompt),
            "first_supervised_position":first,"assistant_token_ids":actual[len(prompt):]}


def language_target_names(module_names,layer_count):
    require(type(layer_count) is int and layer_count>0,"invalid language layer count")
    pattern=re.compile(r"^model\.language_model\.layers\.(\d+)\.self_attn\.(q_proj|k_proj|v_proj|o_proj)$")
    selected=[name for name in module_names if pattern.fullmatch(name)]
    expected={f"model.language_model.layers.{i}.self_attn.{projection}"
              for i in range(layer_count) for projection in ("q_proj","k_proj","v_proj","o_proj")}
    require(set(selected)==expected and len(selected)==len(expected),"language q/k/v/o target inventory mismatch")
    return selected


def validate_trainable_names(names):
    require(names and all("lora_" in name and "visual" not in name and "modules_to_save" not in name
                          and re.search(r"language_model\.layers\.\d+\.self_attn\.(q_proj|k_proj|v_proj|o_proj)\.",name)
                          for name in names),"unexpected trainable base/vision/head/LoRA target")


class EffectiveAccumulation:
    """Only successful supervised backward calls count; no partial update."""
    def __init__(self,grad_accum,updates):
        require(type(grad_accum) is int and grad_accum>0 and type(updates) is int and updates>0,
                "positive explicit update/accumulation counts required")
        self.grad_accum,self.updates=grad_accum,updates
        self.pending=self.completed=self.effective_batches=0
    def record_backward(self,has_loss,loss_finite=True):
        if not has_loss: return False
        require(loss_finite,"nonfinite loss cannot count as an effective batch")
        require(self.completed<self.updates,"extra batch after fixed updates")
        self.pending+=1; self.effective_batches+=1
        return self.pending==self.grad_accum
    def record_step(self):
        require(self.pending==self.grad_accum,"partial or empty accumulation cannot step")
        self.completed+=1; self.pending=0
    def finish(self):
        require(self.completed==self.updates and self.pending==0 and
                self.effective_batches==self.updates*self.grad_accum,"incomplete fixed effective update count")


def legacy_clip_plan(row):
    fps=row["fps_num"]/row["fps_den"]; total=row["n_frames"]
    sf=int(math.ceil(max(0.0,row["clip_start_sec"])*fps))
    ef=int(math.floor(row["clip_end_sec"]*fps))
    sf=max(0,min(sf,total-1)); ef=max(sf+1,min(ef,total-1))
    count=ef-sf+1; samples=min(64,count)
    indices=[0] if samples==1 else [int(round(i*((count-1)/(samples-1)))) for i in range(samples)]
    if samples>1: indices[-1]=count-1
    return {"source_total_frames":total,"source_fps":fps,"clip_start_frame_abs":sf,
            "clip_end_frame_abs":ef,"n_frames_in_clip":count,"n_sampled":samples,
            "clip_local_indices":indices,"absolute_indices":[sf+i for i in indices]}


FIXED={"schema":"aic_temporal_sft8b_config_v1","model_id":MODEL_ID,"revision":REVISION,
       "max_frames":64,"max_pixels":131072,"window_seconds":30,"precision":"bf16",
       "attn_implementation":"sdpa","lora_rank":16,"lora_alpha":32,"lora_dropout":0.05,
       "modules_to_save":None,"gradient_checkpointing_use_reentrant":False,
       "loss":"ASSISTANT_INTERVAL_JSON_CE","optimizer":"AdamW","weight_decay":0.0,"grad_clip_norm":1.0,
       "adamw_betas":[0.9,0.999],"adamw_eps":1e-8}
EXTRA={"model_dir","model_receipt","train_manifest","r7_train_registry","temporal_common","r7_core",
       "out_dir","updates","grad_accum","lr","seed","max_sequence_length","max_wall_seconds"}


def verify_model_receipt(model_dir,receipt):
    controller="completed" in receipt
    require((receipt.get("repo") if controller else receipt.get("repo_id"))==MODEL_ID and
            receipt.get("revision")==REVISION,"wrong fixed 8B model receipt")
    if controller:
        require(receipt.get("status")=="COMPLETE_HASH_VERIFIED" and
                Path(receipt.get("model_path","")).resolve()==model_dir.resolve(),"8B receipt incomplete/path mismatch")
    entries=receipt.get("completed") if controller else receipt.get("files")
    require(isinstance(entries,list) and entries,"8B model receipt files missing")
    declared=set()
    for entry in entries:
        name=entry.get("name") if controller else entry.get("path")
        require(isinstance(name,str) and Path(name).name==name and name not in declared,"unsafe/duplicate model file")
        declared.add(name); source=model_dir/name
        size=entry.get("bytes") if controller else entry.get("size_bytes")
        require(type(size) is int and size>=0 and source.is_file() and source.stat().st_size==size and
                is_sha(entry.get("sha256")) and sha256(source)==entry["sha256"],"fixed model file byte mismatch")
    required={"config.json","tokenizer.json","tokenizer_config.json","preprocessor_config.json",
              "video_preprocessor_config.json","model.safetensors.index.json"}
    required.update(p.name for p in model_dir.iterdir() if p.is_file() and p.suffix in
                    (".json",".safetensors",".jinja",".txt",".model"))
    require(required<=declared and any(name.endswith(".safetensors") for name in declared),"unbound model/config/tokenizer file")
    architecture=json.loads((model_dir/"config.json").read_text())
    require(architecture.get("model_type")=="qwen3_vl" and architecture.get("text_config",{}).get("hidden_size")==4096,
            "model architecture is not pinned Qwen3-VL-8B")
    index=json.loads((model_dir/"model.safetensors.index.json").read_text())
    require(isinstance(index.get("weight_map"),dict) and index["weight_map"] and
            set(index["weight_map"].values())<=declared,"unbound model shard index")


def admit(config_path,admission_path,here=None):
    """All authority, code, model and source byte checks precede runtime imports."""
    here=Path(here or Path(__file__).parent).resolve()
    admission=json.loads(Path(admission_path).read_text(encoding="utf-8"))
    require(admission.get("schema")=="aic_temporal_sft8b_admission_v1" and admission.get("scope")==SCOPE and
            admission.get("authorized") is True and admission.get("registered_route")==ROUTE and
            admission.get("training_authorized_by_user") is True and
            admission.get("formal_c_bce_admitted") is False,"SFT smoke route not registered/authorized; C STOP remains")
    route_path=read_bound(admission.get("training_authorization_evidence"),"user training request and main B registration")
    choice=json.loads(route_path.read_text(encoding="utf-8"))
    require(choice.get("authorized") is True and choice.get("route")==ROUTE and choice.get("scope")==SCOPE and
            choice.get("authority_kind")=="USER_TRAINING_REQUEST_MAIN_REGISTERED_B_ROUTE" and
            choice.get("user_request_quote")=="然后推理打包开训。" and choice.get("explicit_user_route_choice") is False and
            choice.get("authorization_inferred_from_nonresponse") is False and choice.get("formal_c_bce_admitted") is False and
            choice.get("full_training_admitted") is False,
            "broader user training request/main B protocol evidence does not authorize this smoke")
    require(admission.get("config_sha256")==sha256(config_path),"SFT config not bound to admission")
    config=json.loads(Path(config_path).read_text(encoding="utf-8"))
    require(set(config)==set(FIXED)|EXTRA,"unknown/missing SFT recipe field")
    for key,value in FIXED.items():
        require(config[key]==value and type(config[key]) is type(value),"fixed SFT recipe changed: "+key)
    for key in ("updates","grad_accum","seed","max_sequence_length"):
        require(type(config[key]) is int and config[key]>0,"invalid explicit SFT "+key)
    for key in ("lr","max_wall_seconds"):
        require(finite(config[key]) and config[key]>0,"invalid explicit SFT "+key)
    require(all(admission.get(key) is True for key in ("resource_preflight_pass","shared_gpu_queue_approved",
                "disk_peak_within_80gib","budget_runner_required")),"SFT resources/queue not registered")
    code=admission.get("source_code_sha256")
    require(isinstance(code,dict) and set(code)=={"sft_contract.py","train_sft.py"} and
            all(is_sha(digest) and sha256(here/name)==digest for name,digest in code.items()),"SFT source code identity mismatch")
    bound={name:read_bound(config[name],name) for name in
           ("model_receipt","train_manifest","r7_train_registry","temporal_common","r7_core")}
    for key in ("model_receipt","train_manifest","r7_train_registry"):
        require(admission.get(key+"_sha256")==config[key]["sha256"],"admission does not bind "+key)
    output=Path(config["out_dir"]).resolve()
    require(here in output.parents and (not output.exists() or not any(output.iterdir())),"unsafe/nonempty SFT smoke output")
    # Verify borrowed helpers before importing them, including fixed prompt/IO.
    common=bound["temporal_common"].read_text(encoding="utf-8")
    require("MAX_FRAMES = 64" in common and "MAX_PIXELS = 128 * 32 * 32" in common,
            "R7 temporal preprocessing identity changed")
    model_dir=Path(config["model_dir"])
    require(model_dir.is_dir(),"8B model directory missing")
    verify_model_receipt(model_dir,json.loads(bound["model_receipt"].read_text(encoding="utf-8")))
    registry=json.loads(bound["r7_train_registry"].read_text(encoding="utf-8"))
    rows=[json.loads(line) for line in bound["train_manifest"].read_text(encoding="utf-8").splitlines() if line.strip()]
    original=load_original_train(bound["r7_core"].parent.parent/"inputs/train_temporal.jsonl")
    sources=validate_training_rows(registry,rows,original)
    for source,digest in sources.items():
        require(Path(source).is_file() and sha256(source)==digest,"training source bytes changed before runtime imports")
    return {"config":config,"admission":admission,"rows":rows,"sources":sources,"bound":bound,
            "config_sha256":sha256(config_path),"admission_sha256":sha256(admission_path),
            "origin_train_manifest_sha256":registry["origin_train_manifest_sha256"]}


def validate_training_rows(registry,rows,original_rows=None):
    """Train-only metadata/target join, independent of machine-local paths."""
    parents=registry.get("records")
    require(registry.get("schema")=="aic_sft8b_r7_train_registry_v1" and registry.get("expected_parent_count")==704
            and registry.get("origin_train_manifest_sha256")==ORIGINAL_TRAIN_SHA and isinstance(parents,list) and len(parents)==704,
            "not the frozen original 704 train parent registry")
    lookup={r.get("parent_sample_id"):r for r in parents}
    require(len(lookup)==704 and None not in lookup and all(isinstance(key,str) and key for key in lookup),"duplicate/missing 704 parent ID")
    original={r["sample_id"]:r for r in (load_original_train() if original_rows is None else original_rows)}
    require(set(lookup)==set(original) and len(original)==704,"registry replaced original 704 parent set")
    old_identity=("video_id","source_group","youtube_id","source_path","clip_start_sec","clip_end_sec")
    for parent in parents:
        old=original[parent["parent_sample_id"]]
        require(all(parent.get(key)==old.get(key) for key in old_identity),
                "registry parent differs from fixed original train source/window")
        require(parent.get("split")=="train" and parent.get("label_status")=="WEAK_TEACHER" and
                parent.get("pts_audit_status")=="PASS","dev/confirm/unapproved PTS parent forbidden")
        old_fps=old.get("source_avg_fps")
        require(old.get("split")=="train" and old.get("label_status")=="WEAK_TEACHER" and old.get("pts_audit_status")=="PASS" and
                finite(old_fps) and old_fps>0 and finite(old.get("pts_frame_interval_sec")) and old["pts_frame_interval_sec"]>0 and
                finite(old.get("pts_max_residual_sec")) and 0<=old["pts_max_residual_sec"]<=1/old_fps+1e-6,
                "fixed R7 parent lacks its historical approximate CFR evidence")
        require(parent.get("n_frames")==old.get("decoded_source_frames") and
                type(parent.get("fps_num")) is int and parent["fps_num"]>0 and
                type(parent.get("fps_den")) is int and parent["fps_den"]>0 and
                abs(parent["fps_num"]/parent["fps_den"]-old_fps)<=max(1e-6,old_fps*1e-6),
                "new source count/FPS differs from original R7 metadata; old byte equality is unproven")
    require(len({r.get("youtube_id") for r in parents})==602,"frozen 602 original R7 train source groups changed")
    require(rows and len({r.get("window_id") for r in rows})==len(rows),"empty/duplicate SFT window manifest")
    identity=("video_id","youtube_id","source_group","source_path","source_sha256","n_frames","fps_num","fps_den","width","height",
              "source_bytes","source_mtime_ns")
    sources={}
    for row in rows:
        require(row.get("parent_sample_id") in lookup,"SFT sample outside original 704 train")
        parent=lookup[row["parent_sample_id"]]
        require(row.get("sample_id")==row["parent_sample_id"] and all(row.get(key)==parent.get(key) for key in identity),
                "SFT window parent/source identity mismatch")
        require(row.get("split")=="train" and row.get("label_status")=="WEAK_TEACHER" and row.get("pts_audit_status")=="PASS",
                "SFT train-only weak/CFR status missing")
        require(all(type(row.get(key)) is int and row[key]>0 for key in ("n_frames","fps_num","fps_den","width","height"))
                and row["n_frames"]>=2 and is_sha(row.get("source_sha256")),"invalid source metadata/byte identity")
        start,end=row.get("clip_start_sec"),row.get("clip_end_sec")
        require(finite(start) and finite(end) and 0<=start<end<=row["n_frames"]*row["fps_den"]/row["fps_num"]+1e-6
                and end-start<=30+1e-9,"SFT window violates registered CFR 30s source contract")
        require(parent["clip_start_sec"]<=start<end<=parent["clip_end_sec"]+1e-9,"SFT window exceeds original parent clip")
        windows=parent.get("registered_windows",[])
        registered=[w for w in windows if w.get("window_id")==row["window_id"]]
        require(len(registered)==1,"window not uniquely registered under its 704 parent")
        window=registered[0]
        require(window.get("parent_sample_id",row["parent_sample_id"])==row["parent_sample_id"] and
                all(window.get(key)==row.get(key) for key in ("clip_start_sec","clip_end_sec","segments_clip_local")),
                "registered window geometry/canonical target mismatch")
        segments_valid(row.get("segments_clip_local"),end-start)
        require(row["source_path"] not in sources or sources[row["source_path"]]==row["source_sha256"],"contradictory source byte bindings")
        sources[row["source_path"]]=row["source_sha256"]
    return sources


def verify_live_gpu_reservation():
    require(os.name=="posix","SFT execution requires main's Linux shared GPU wrapper")
    path=Path("/home/inspur/aic_video_work/improvement_round1/active_gpu_job.json")
    require(path.is_file(),"shared GPU reservation missing")
    active=json.loads(path.read_text()); ancestors=set(); pid=os.getpid()
    for _ in range(32):
        ancestors.add(pid)
        if pid<=1: break
        pid=int(Path(f"/proc/{pid}/stat").read_text().rsplit(")",1)[1].split()[1])
    require(active.get("child_pid") in ancestors and active.get("runner_pid") in ancestors,
            "SFT reservation belongs to another process")

```

## 新必要原文件全文 reports/round6_score_alignment/rematch_discussion/aic_video_empty407_20261010/source_exposure_audit.json
原始bytes=42623 SHA=da7fc191afdba994c280274575ee70120f3ff2a61ee5f34027e7961a11ca9606

```
{
  "utc": "2026-10-10T04:55:15.431817+00:00",
  "status": "PASS_EXISTING_MEDIA_BYTES_AND_HISTORICAL_AUDIT_BINDING",
  "sources": 50,
  "human_alignment_eligible": 48,
  "all_sources_previously_exposed": true,
  "source_rows": [
    {
      "source_id": "-esJrBWj2d8",
      "source_group": "youtube:-esJrBWj2d8",
      "category": "DS",
      "prior_split": "validation",
      "media_sha256": "811186cdec40ef58049f0cc951c07a9f6f7d2b5cb27511e01094b829bbd10a9e",
      "media_bytes": 12547350,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\-esJrBWj2d8\\-esJrBWj2d8.mp4",
      "native_frames": 6912,
      "duration": 230.4,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "0tmA_C6XwfM",
      "source_group": "youtube:0tmA_C6XwfM",
      "category": "GA",
      "prior_split": "train",
      "media_sha256": "63a2f711416d2a911a4f00166fedb7ce01e2eaab18946c0222071322111b961b",
      "media_bytes": 7573592,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\0tmA_C6XwfM\\0tmA_C6XwfM.mp4",
      "native_frames": 3532,
      "duration": 141.28,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "37rzWOQsNIw",
      "source_group": "youtube:37rzWOQsNIw",
      "category": "MS",
      "prior_split": "train",
      "media_sha256": "c4fb034705c03a890fed5cc46ff79d1e9aef5cd9edec1d22dfe7cc653b5fd98a",
      "media_bytes": 10156252,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\37rzWOQsNIw\\37rzWOQsNIw.mp4",
      "native_frames": 5742,
      "duration": 191.5914,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "3eYKfiOEJNs",
      "source_group": "youtube:3eYKfiOEJNs",
      "category": "GA",
      "prior_split": "train",
      "media_sha256": "d8c2669fbd08e8b2f35ebce82dfe5aa6cbf7e8fbee56df9e971ca12b7dd9e322",
      "media_bytes": 10488602,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\3eYKfiOEJNs\\3eYKfiOEJNs.mp4",
      "native_frames": 4853,
      "duration": 194.12,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "4wU_LUjG5Ic",
      "source_group": "youtube:4wU_LUjG5Ic",
      "category": "PR",
      "prior_split": "validation",
      "media_sha256": "2779762f2c332931c9fb4e61783b81df6e34b487dc3a94c882781c981e6c4869",
      "media_bytes": 8815620,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\4wU_LUjG5Ic\\4wU_LUjG5Ic.mp4",
      "native_frames": 4005,
      "duration": 167.041875,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "91IHQYk1IQM",
      "source_group": "youtube:91IHQYk1IQM",
      "category": "PR",
      "prior_split": "train",
      "media_sha256": "327f8cd1ff27ecec1de291e396ac7c40521253fa208f2e3c477c5b1e84964f05",
      "media_bytes": 5830349,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\91IHQYk1IQM\\91IHQYk1IQM.mp4",
      "native_frames": 3312,
      "duration": 110.5104,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "98MoyGZKHXc",
      "source_group": "youtube:98MoyGZKHXc",
      "category": "VT",
      "prior_split": "train",
      "media_sha256": "e293ceb35a8f1ec514707c579ab9b78e678a0c686f895d25945b9a50432c000c",
      "media_bytes": 9817234,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\98MoyGZKHXc\\98MoyGZKHXc.mp4",
      "native_frames": 4688,
      "duration": 187.52,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "_xMr-HKMfVA",
      "source_group": "youtube:_xMr-HKMfVA",
      "category": "FM",
      "prior_split": "train",
      "media_sha256": "1d9cd42e19931934ea362f7509bf69f0e98a13da801414998d58296fca4bcbbe",
      "media_bytes": 8040777,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\_xMr-HKMfVA\\_xMr-HKMfVA.mp4",
      "native_frames": 4463,
      "duration": 148.91543333333334,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "akI8YFjEmUw",
      "source_group": "youtube:akI8YFjEmUw",
      "category": "VU",
      "prior_split": "train",
      "media_sha256": "28f8d4d89a14b30f9066ad5146e8b219c67d45291b9a1588af6d1f6c455acffe",
      "media_bytes": 7222459,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\akI8YFjEmUw\\akI8YFjEmUw.mp4",
      "native_frames": 3995,
      "duration": 133.29983333333334,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "AwmHb44_ouw",
      "source_group": "youtube:AwmHb44_ouw",
      "category": "VT",
      "prior_split": "train",
      "media_sha256": "82ecca1de0363253060bb3c19e2f5dbd4080bfc0cd790db23c3e73ffd76a602f",
      "media_bytes": 19246027,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\AwmHb44_ouw\\AwmHb44_ouw.mp4",
      "native_frames": 10597,
      "duration": 353.58656666666667,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "b626MiF1ew4",
      "source_group": "youtube:b626MiF1ew4",
      "category": "PK",
      "prior_split": "train",
      "media_sha256": "66d6dc7720db2ae750c9c85a7f6a0d55416a9a23ce6ca7d151969501d8606e1c",
      "media_bytes": 12624955,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\b626MiF1ew4\\b626MiF1ew4.mp4",
      "native_frames": 5661,
      "duration": 235.875,
      "human_ordinal_alignment": "NOT_RECORDED",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "Bhxk-O1Y7Ho",
      "source_group": "youtube:Bhxk-O1Y7Ho",
      "category": "GA",
      "prior_split": "train",
      "media_sha256": "a66202fe5943daee0a0984fd708ff3126168ded35750c099a54ae67705e1ff3f",
      "media_bytes": 24536587,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\Bhxk-O1Y7Ho\\Bhxk-O1Y7Ho.mp4",
      "native_frames": 13511,
      "duration": 450.8170333333333,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "byxOvuiIJV0",
      "source_group": "youtube:byxOvuiIJV0",
      "category": "FM",
      "prior_split": "train",
      "media_sha256": "b94f772069a7479b54c27b50650bccdfb0b75bb573abf8bda27dba1a5af75abd",
      "media_bytes": 8234183,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\byxOvuiIJV0\\byxOvuiIJV0.mp4",
      "native_frames": 3705,
      "duration": 154.529375,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "cjibtmSLxQ4",
      "source_group": "youtube:cjibtmSLxQ4",
      "category": "PK",
      "prior_split": "validation",
      "media_sha256": "43183ef7f35bfcbc39c122be797fdee5031103862c7c7da3b9ab74d222c79c9d",
      "media_bytes": 35194393,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\cjibtmSLxQ4\\cjibtmSLxQ4.mp4",
      "native_frames": 19406,
      "duration": 647.5135333333334,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "E11zDS9XGzg",
      "source_group": "youtube:E11zDS9XGzg",
      "category": "DS",
      "prior_split": "train",
      "media_sha256": "f4370b8fd985c3b41bf5590988669b18794ea64fea3921a8109962a91c324986",
      "media_bytes": 27524696,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\E11zDS9XGzg\\E11zDS9XGzg.mp4",
      "native_frames": 15307,
      "duration": 510.23333333333335,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "EE-bNr36nyA",
      "source_group": "youtube:EE-bNr36nyA",
      "category": "BK",
      "prior_split": "train",
      "media_sha256": "0e11bb5bb60ac4842b2ee500c9cf985395a083ae92c3f498f1e91f12aa8e1691",
      "media_bytes": 5274150,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\EE-bNr36nyA\\EE-bNr36nyA.mp4",
      "native_frames": 2941,
      "duration": 98.13136666666666,
      "human_ordinal_alignment": "NOT_RECORDED",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "eQu1rNs0an0",
      "source_group": "youtube:eQu1rNs0an0",
      "category": "BT",
      "prior_split": "train",
      "media_sha256": "7a3daec4c22feace99c4e193ce72e4a3e17bbedd4f0c6feb39e3e9030e6fb05f",
      "media_bytes": 8817667,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\eQu1rNs0an0\\eQu1rNs0an0.mp4",
      "native_frames": 4931,
      "duration": 164.53103333333334,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "EYqVtI9YWJA",
      "source_group": "youtube:EYqVtI9YWJA",
      "category": "BT",
      "prior_split": "validation",
      "media_sha256": "6ffcc966ab00a6096d7b256cffd09408efa7db376df7732644f875b8ff27f390",
      "media_bytes": 10713251,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\EYqVtI9YWJA\\EYqVtI9YWJA.mp4",
      "native_frames": 5939,
      "duration": 198.16463333333334,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "fWutDQy1nnY",
      "source_group": "youtube:fWutDQy1nnY",
      "category": "PR",
      "prior_split": "train",
      "media_sha256": "d50d740e77517611ea231e844d409ebdf51e05037ef8cd17a22cd983d2464fc3",
      "media_bytes": 31792596,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\fWutDQy1nnY\\fWutDQy1nnY.mp4",
      "native_frames": 17527,
      "duration": 585.8541966106227,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "GsAD1KT1xo8",
      "source_group": "youtube:GsAD1KT1xo8",
      "category": "PK",
      "prior_split": "train",
      "media_sha256": "a195fc9d8e5330ee55c62dfc0a99eb5d130bf0444bb412992d1204eecd8f3a86",
      "media_bytes": 7794439,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\GsAD1KT1xo8\\GsAD1KT1xo8.mp4",
      "native_frames": 4356,
      "duration": 145.3452,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "gzDbaEs1Rlg",
      "source_group": "youtube:gzDbaEs1Rlg",
      "category": "VT",
      "prior_split": "train",
      "media_sha256": "6682bdee7edc1d697a1807bb3f84f50e3cacd98266fc93d1deb38adbb8d125c2",
      "media_bytes": 15419041,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\gzDbaEs1Rlg\\gzDbaEs1Rlg.mp4",
      "native_frames": 7210,
      "duration": 288.4,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "Hl-__g2gn_A",
      "source_group": "youtube:Hl-__g2gn_A",
      "category": "MS",
      "prior_split": "train",
      "media_sha256": "9386d64a62463f36213a043e6e74c76faf5eff746d7ef53035146c7bead40bd1",
      "media_bytes": 13134659,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\Hl-__g2gn_A\\Hl-__g2gn_A.mp4",
      "native_frames": 5846,
      "duration": 243.82691666666668,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "HT5vyqe0Xaw",
      "source_group": "youtube:HT5vyqe0Xaw",
      "category": "VU",
      "prior_split": "train",
      "media_sha256": "85fdd93e61fb670b5437666c9eb90aa1798889edbe07394749c00ca0d044c886",
      "media_bytes": 17564055,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\HT5vyqe0Xaw\\HT5vyqe0Xaw.mp4",
      "native_frames": 9671,
      "duration": 322.6890333333333,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "i3wAGJaaktw",
      "source_group": "youtube:i3wAGJaaktw",
      "category": "GA",
      "prior_split": "validation",
      "media_sha256": "7a8cc3f5415702ce254200db00650cb42981ba0c0fa5b5ef4a910f7c66c69c21",
      "media_bytes": 8413810,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\i3wAGJaaktw\\i3wAGJaaktw.mp4",
      "native_frames": 4700,
      "duration": 156.82333333333332,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "iVt07TCkFM0",
      "source_group": "youtube:iVt07TCkFM0",
      "category": "BT",
      "prior_split": "train",
      "media_sha256": "7c34621e37ff0cc6d7f8838e8c6468e67eea934484e3c7ecf8eca7409c35e3f7",
      "media_bytes": 5538282,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\iVt07TCkFM0\\iVt07TCkFM0.mp4",
      "native_frames": 2500,
      "duration": 104.27083333333333,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "J0nA4VgnoCo",
      "source_group": "youtube:J0nA4VgnoCo",
      "category": "VT",
      "prior_split": "validation",
      "media_sha256": "65c9490a2166d17736c38ed077f250290c548b1da8f1801f10ff53fad8e84a5b",
      "media_bytes": 31626560,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\J0nA4VgnoCo\\J0nA4VgnoCo.mp4",
      "native_frames": 14019,
      "duration": 584.709125,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "jcoYJXDG9sw",
      "source_group": "youtube:jcoYJXDG9sw",
      "category": "DS",
      "prior_split": "train",
      "media_sha256": "3354cee170c1b9ace768883f058150869874ed27c2b60cf08b9f2272b5aa1db9",
      "media_bytes": 14753114,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\jcoYJXDG9sw\\jcoYJXDG9sw.mp4",
      "native_frames": 5971,
      "duration": 199.23236666666668,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "JgHubY5Vw3Y",
      "source_group": "youtube:JgHubY5Vw3Y",
      "category": "BT",
      "prior_split": "train",
      "media_sha256": "dff35488cc8dfd1b4962d82d8a96f475a051f163ed7dea4be8a0d10456e5b7c5",
      "media_bytes": 7682265,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\JgHubY5Vw3Y\\JgHubY5Vw3Y.mp4",
      "native_frames": 4304,
      "duration": 143.61013333333332,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "JKpqYvAdIsw",
      "source_group": "youtube:JKpqYvAdIsw",
      "category": "FM",
      "prior_split": "validation",
      "media_sha256": "da63a55d05c49f042699b366f3026ba77c8695208b40eb40b506867604caf905",
      "media_bytes": 8201511,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\JKpqYvAdIsw\\JKpqYvAdIsw.mp4",
      "native_frames": 3802,
      "duration": 152.08,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "kLxoNp-UchI",
      "source_group": "youtube:kLxoNp-UchI",
      "category": "DS",
      "prior_split": "train",
      "media_sha256": "0c91bfa880e3af0e1716e7456ada0a304a97911eef76b1cd4fdce5066a52e8f7",
      "media_bytes": 6970411,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\kLxoNp-UchI\\kLxoNp-UchI.mp4",
      "native_frames": 3896,
      "duration": 129.99653333333333,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "LRw_obCPUt0",
      "source_group": "youtube:LRw_obCPUt0",
      "category": "MS",
      "prior_split": "train",
      "media_sha256": "ce57a731477468ddf799c29cfcbd11469e30cb96eb844c372a8447a90e1db858",
      "media_bytes": 13697882,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\LRw_obCPUt0\\LRw_obCPUt0.mp4",
      "native_frames": 6241,
      "duration": 260.30170833333335,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "NyBmCxDoHJU",
      "source_group": "youtube:NyBmCxDoHJU",
      "category": "DS",
      "prior_split": "train",
      "media_sha256": "6960e8850f04eae077a85e3befddaed36ce1196ac84d9efd8f8560ac90e557b7",
      "media_bytes": 10213204,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\NyBmCxDoHJU\\NyBmCxDoHJU.mp4",
      "native_frames": 4740,
      "duration": 189.6,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "oDXZc0tZe04",
      "source_group": "youtube:oDXZc0tZe04",
      "category": "BK",
      "prior_split": "train",
      "media_sha256": "dd2cddeaeb6bc44dea976337af5c8b79b0030abbe2438ed8549fe9304621efd2",
      "media_bytes": 20654776,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\oDXZc0tZe04\\oDXZc0tZe04.mp4",
      "native_frames": 11414,
      "duration": 380.8471333333333,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "PJrm840pAUI",
      "source_group": "youtube:PJrm840pAUI",
      "category": "PK",
      "prior_split": "train",
      "media_sha256": "790c560f5132928d456803ca5e23b03ca38b1eb8d3383b619afbed60dd5be86f",
      "media_bytes": 14766069,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\PJrm840pAUI\\PJrm840pAUI.mp4",
      "native_frames": 6580,
      "duration": 274.1666666666667,
      "human_ordinal_alignment": "NOT_RECORDED",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "qqR6AEXwxoQ",
      "source_group": "youtube:qqR6AEXwxoQ",
      "category": "BT",
      "prior_split": "train",
      "media_sha256": "77987b565d016441183ec928ef985f1a1d805b4c36c833a0b0b2705fff6a092d",
      "media_bytes": 14617342,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\qqR6AEXwxoQ\\qqR6AEXwxoQ.mp4",
      "native_frames": 8073,
      "duration": 269.3691,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "RBCABdttQmI",
      "source_group": "youtube:RBCABdttQmI",
      "category": "PR",
      "prior_split": "train",
      "media_sha256": "2411ac74f1e8a049072063bd579b4aa034e5c01a388c67cdcc7959763562b36b",
      "media_bytes": 19590609,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\RBCABdttQmI\\RBCABdttQmI.mp4",
      "native_frames": 10917,
      "duration": 364.2639,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "Se3oxnaPsz0",
      "source_group": "youtube:Se3oxnaPsz0",
      "category": "BK",
      "prior_split": "validation",
      "media_sha256": "87bf58a787009bce2add1a743bca81b98b33e7bb8edee80c1ff7c7070ae368e6",
      "media_bytes": 7584394,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\Se3oxnaPsz0\\Se3oxnaPsz0.mp4",
      "native_frames": 4166,
      "duration": 138.86666666666667,
      "human_ordinal_alignment": "UNRESOLVED_COUNT_DIFFERENCE_NOT_PADDED",
      "excluded_human_vector_alignment": true,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "sTEELN-vY30",
      "source_group": "youtube:sTEELN-vY30",
      "category": "VU",
      "prior_split": "validation",
      "media_sha256": "b6767caf3ddb2a1750672427315fe61c63a854de26ca707f5e5041bf45557d48",
      "media_bytes": 8065363,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\sTEELN-vY30\\sTEELN-vY30.mp4",
      "native_frames": 4468,
      "duration": 148.93333333333334,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "uGu_10sucQo",
      "source_group": "youtube:uGu_10sucQo",
      "category": "BK",
      "prior_split": "train",
      "media_sha256": "302cfeab45f174688d2a709cc4528087a5ba17d4fb9880ceac8fe8db87007b51",
      "media_bytes": 8256585,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\uGu_10sucQo\\uGu_10sucQo.mp4",
      "native_frames": 4009,
      "duration": 167.04166666666666,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "vdmoEJ5YbrQ",
      "source_group": "youtube:vdmoEJ5YbrQ",
      "category": "VU",
      "prior_split": "train",
      "media_sha256": "77f719f5de3ca948691dd34e7dac5ed5783d1b98814fea035aa7cce6d21edb72",
      "media_bytes": 17926114,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\vdmoEJ5YbrQ\\vdmoEJ5YbrQ.mp4",
      "native_frames": 9870,
      "duration": 329.329,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "VuWGsYPqAX8",
      "source_group": "youtube:VuWGsYPqAX8",
      "category": "FM",
      "prior_split": "train",
      "media_sha256": "9476a6d8bc6fdcff909fa2885ba82ba7696b3d05fca2f070e313139e434eabe3",
      "media_bytes": 11537377,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\VuWGsYPqAX8\\VuWGsYPqAX8.mp4",
      "native_frames": 5412,
      "duration": 216.48,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "WG0MBPpPC6I",
      "source_group": "youtube:WG0MBPpPC6I",
      "category": "MS",
      "prior_split": "train",
      "media_sha256": "0d68d94612da8efd687419dc030a485d61419c30290865d9ec1f9ed1062040f9",
      "media_bytes": 21473331,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\WG0MBPpPC6I\\WG0MBPpPC6I.mp4",
      "native_frames": 9535,
      "duration": 397.68895833333335,
      "human_ordinal_alignment": "UNRESOLVED_COUNT_DIFFERENCE_NOT_PADDED",
      "excluded_human_vector_alignment": true,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "WxtbjNsCQ8A",
      "source_group": "youtube:WxtbjNsCQ8A",
      "category": "BK",
      "prior_split": "train",
      "media_sha256": "b6c658e4d5258fcba10207b8c49ed624cabfe951ed9c9a96aa4ed6fada96d388",
      "media_bytes": 14014038,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\WxtbjNsCQ8A\\WxtbjNsCQ8A.mp4",
      "native_frames": 7959,
      "duration": 265.5653,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "XkqCExn6_Us",
      "source_group": "youtube:XkqCExn6_Us",
      "category": "PK",
      "prior_split": "train",
      "media_sha256": "ee3e102d0cda34b30c8eadaa162157616c398213dc88d0198ff4cc6476dd5fc9",
      "media_bytes": 10210795,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\XkqCExn6_Us\\XkqCExn6_Us.mp4",
      "native_frames": 5631,
      "duration": 187.8877,
      "human_ordinal_alignment": "NOT_RECORDED",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "xmEERLqJ2kU",
      "source_group": "youtube:xmEERLqJ2kU",
      "category": "FM",
      "prior_split": "train",
      "media_sha256": "14184d35578cc9e672428f693ae74328ecb54b003d85857ff2afbf8354a90081",
      "media_bytes": 24129938,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\xmEERLqJ2kU\\xmEERLqJ2kU.mp4",
      "native_frames": 13365,
      "duration": 445.9455,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "xwqBXPGE9pQ",
      "source_group": "youtube:xwqBXPGE9pQ",
      "category": "VU",
      "prior_split": "train",
      "media_sha256": "71bb39923112962e30006918c9e3a9dbcd248786f275568447e8a29ebdb380ff",
      "media_bytes": 12666392,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\xwqBXPGE9pQ\\xwqBXPGE9pQ.mp4",
      "native_frames": 7010,
      "duration": 233.90033333333332,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "xxdtq8mxegs",
      "source_group": "youtube:xxdtq8mxegs",
      "category": "GA",
      "prior_split": "train",
      "media_sha256": "fe3200fd13dfbf74f5c02d73ec9acd7bd0c1f68eb876968bc74230549320c327",
      "media_bytes": 7367068,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\xxdtq8mxegs\\xxdtq8mxegs.mp4",
      "native_frames": 4324,
      "duration": 144.13333333333333,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "XzYM3PfTM4w",
      "source_group": "youtube:XzYM3PfTM4w",
      "category": "VT",
      "prior_split": "train",
      "media_sha256": "c758df53e237aadc9e893a4389078b25f58000a782d3c69b8490195aae30dac0",
      "media_bytes": 6010860,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\XzYM3PfTM4w\\XzYM3PfTM4w.mp4",
      "native_frames": 3327,
      "duration": 111.0109,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "Yi4Ij2NM7U4",
      "source_group": "youtube:Yi4Ij2NM7U4",
      "category": "MS",
      "prior_split": "validation",
      "media_sha256": "26ec9f71ea771e5601a1f5c963fa425681ae2f86b3dfca483a64d58b5a65feb9",
      "media_bytes": 21884159,
      "media_path": "G:\\ai\\AIC视频\\reports\\qwen8b_annotation_20261009_v1\\input\\Yi4Ij2NM7U4\\Yi4Ij2NM7U4.mp4",
      "native_frames": 9731,
      "duration": 405.4583333333333,
      "human_ordinal_alignment": "COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF",
      "excluded_human_vector_alignment": false,
      "exposure": "PRIOR_IMAGE_ANNOTATION_AND_MODEL_EXPERIMENTS; NOT_BLIND",
      "current_B_native_training_exposure": "NOT_PROVEN_FROM_THIS_MANIFEST",
      "license_history": "UNRESOLVED_BUNDLED_WEBSCOPE_NOTICE_VS_CURRENT_AUTHOR_README"
    },
    {
      "source_id": "z_6gVvQb2d0",
      "source_group": "youtube:z_6gVvQb2d0",
      "category": "PR",
      "prior_split": "train",
      "media_sha256": "fe77605cdf8c234219ce423a90a93e44e003e55567bdb9bb87a3fb5fec0063cd",
