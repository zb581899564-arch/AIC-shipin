最后一条尤其重要。完整窗口交叉熵训练隐含模型应该输出全部目标事件。如果只标出了其中两个正例，另外未观察的时段就可能在训练时被错误地当成“不应输出”。

这正是弱标签污染原B的重要风险。

阶段D：标注质量门

建议对候选KEEP和所有切镜相关端点实施独立人工复核，对REJECT按事前随机规则抽查，确认组的完整事件参考应在查看candidate0及新模型预测之前完成。

我建议采用以下前瞻性工程准入线，而非统计置信保证：

指标

	

建议接受条件




来源及native映射

	

100%合法




已确认跨镜误标

	

0




KEEP独立复核精确率

	

≥85%




经复核的边界区间IoU

	

平均≥0.75




可作为完整窗口监督的训练样本

	

≥8窗，覆盖≥4来源组




UNKNOWN处理

	

全部分离；不得自动变负例




样本数不足

	

到24窗上限直接STOP，不循环补采

85%、0.75及最小样本数是控制投入和噪声的工程选择，并没有来自附件的统计保证。少量样本达标不等于教师已成为金标。

同一教师重复判断所得的一致率只能评估稳定性，不能代替独立语义审查。

四、训练：只允许一次从原B续训

有一个必须正视的协议问题：

原B的native视频提示词要求返回1–5个segments，也就是它不能在每个窗口内直接表达零段。这个限制在历史原始提示词代码中是明确的。
context-r00.md

因此本轮不能一边声称沿用原B语法，一边把NO_HIGHLIGHT当作合法的空段输出进行完整窗口SFT。

我的处理是：**本轮只用完整审查、存在1–5个真实可见高光区间的窗口进行B原协议续训。**确认没有高光的窗口保留作负例诊断及误报评估，不假装本轮已经解决原B不能输出空窗口的表达问题。

被冻结的训练条件：

项目

	

条件




初始化

	

37.66候选对应的原B8B时间LoRA




基座

	

原Qwen3-VL-8B，冻结




LoRA

	

继承r16、alpha32、q/k/v/o




学习率

	

1e-5




有效batch

	

4




训练

	

最多2 epoch、最多8次真实optimizer更新




数据

	

仅合格train来源的完整窗口




目标

	

原B native视频到完整segments，不使用TVSum分数




checkpoint

	

预先指定最终checkpoint，不用确认组挑权重




新架构/新参数头

	

0

继续加载原B适配器是必须的，不能像237步实验那样重新训练独立任务LoRA。若不能恢复旧optimizer状态，应明确登记新优化器初始化，不能声称优化器无缝接续。

这个规模是可证伪的低成本续训试验，不是预计能够直接显著涨分的大规模训练。

训练前应保存原B全部权重和参数身份；训练后验实际参数变化、冻结情况、有限梯度、加载身份与输出合法性。

如果有效样本太少，实际更新可以少于8，禁止重复曝光样本以凑足步数。

五、原B native公平candidate0

这是我认为必须补足的最关键科学对照。

Candidate0

历史37.66原B

原LoRA、原native视频输入、原双窗配置、原processor与grammar。

Candidate1

B + 合格事件监督

仅替换训练得到的时间LoRA，其余原生推理协议完全相同。

必须锁定以下不变量：视频源、窗口划分、sampled ordinals、native PTS、processor、输入像素预算、B0 prompt、生成语法、greedy设置、空间模型、源场、compose与输出严格验证器。

候选0不能使用新image-score prompt，因为那是另一个任务和输入分布。此前production_B评分诊断不能替代这一对照。

对3组确认来源，按来源组等权计算：

指标

	

用途




事件时间区间Precision/Recall/F1

	

主要质量指标




区间起止误差及跨镜误选率

	

判断剪辑边界




非高光窗口误报率

	

评估B强制输出的代价




选中时长占比与整窗占比

	

排查长段过选




每来源组F1差值和最差退化

	

防止均值掩盖失败




工程合法率与完整帧身份

	

独立硬约束

已见TVSum Spearman只保留为辅助研究指标，不能给candidate1授予AIC质量资格。

最终STOP/GO

建议一次确认通过需要同时满足：

确认组macro时间F1相对candidate0至少提高0.05绝对值。

无确认来源组F1下降超过0.05。

时间Precision下降不超过0.02，且没有已确认跨镜错误。

非高光窗口误报不明显恶化，完整协议及参数上限通过。

后续非测试8的原生输入、空间合成、严格验证通过；质量风险不能只凭输出合法或非空消除。

数值仍是前瞻投入规则，不是AIC成绩涨幅预测。3个确认来源组的证据力有限，即使全通过，也只能支持“值得一次后续验证”，不能称可靠泛化。

**任何科学门失败，直接STOP并保留原37.66候选。**不换阈值、不回头挑checkpoint、不改teacher提示反复扩标、不启动第二种模型。若后续所有门通过，才考虑一次新的完整426生成；这一步不在本轮执行。

六、对主控的关键批评

主控已经正确撤回全空包推荐，并认识到TVSum不是AIC金标。但我认为还有一个流程问题没有被充分解决：

第二阶段准入仍然过分依赖已见TVSum代理F的点估计，而且允许非测试8全空后继续进入426。

从代码上看，stage2_pass主要要求已有研究门通过且9源macro代理F点估计优于基座。它没有要求可靠的独立事件质量参考，也没有要求新选择器在目标语义下达到最低可用性。

即便不依据复赛反馈调阈值，也可以事前登记独立非测试质量风险门。

全空不应自动判错误，因为真实无高光的窗口可以合理为空；但是连续8个非测试视频全空，也不应在没有任务语义核验的情况下仅以11strict工程通过继续放行。

这不是事后拿407修改门槛，而是指出原放行门本来就没有充分覆盖“合规但无用”的输出模式。

另一个弱点是现有agy的任务定义仍过宽。“重要动作、结果、叙事核心”允许不同标注者采用不同的取舍标准，且没有把事件能否被学生实际看到列为必要条件。扩大这种标签集合可能只会提高教师风格拟合程度，而不是提高真实高光质量。

七、对我这条主案的最强反例

假设某段30秒视频只有0.4秒真正值得保留的关键动作。

原B的64帧抽样恰好没有看到动作。agy通过更密集的观察找到了事件，独立审查也确认标注正确。

这时，用它微调原B会产生一个危险监督关系：

模型没有看到动作，却被要求输出该动作发生的准确位置。

训练损失可能下降，但模型学到的可能是依据上下文猜测事件时间，而不是可靠观察。

再考虑另一个窗口确实完全没有精彩内容。原B被约束至少输出一个区间，而更合适的模型应当输出空。这样一来，即使新LoRA在有高光的确认窗口上提高了F1，整体应用仍可能因为非高光窗口的强制输出而变差。

这个反例足以否决“只要高质量闭源标注更多数据，继续微调原B就一定有效”的论证。

所以我的训练准入同时要求事件可观察、标签覆盖完整和独立负例评价。若失败，应该承认本轮B-native微调路线不成立，而非继续堆标签。

对主案最强的机会成本质疑是：现有TVSum新模型可能只差一次正确的训练域校准，就能把较好的排序转化成可用的选择结果，而且成本比重新标注和续训B更低。

我承认这种可能性。但它依旧无法直接修复2秒整格语义和切镜边界问题，并且缺少AIC质量参考。鉴于已有37.66的原B，当前优先购买可检验的事件监督，比继续修补TVSum评分器更有决策价值。

八、最终裁决

决策项

	

意见




新237步评分器及全空ZIP

	

撤回质量候选，保留失败证据




37.66原B

	

保留为不可覆盖的candidate0




TVSum继续训练

	

NO




agy标注

	

YES，但必须事件级、原生可观察、边界审查




原B继续微调

	

有条件YES，仅一次有界SFT




强制TopK/按复赛调阈值

	

NO




100confirm或复赛逐例调参

	

NO




本轮启动实验、GPU、提交

	

NO

下一轮最值得交叉审查的两个问题是：

问题1： 在当前可合法使用的非测试来源中，能否取得足够多的、与原B实际观察一致的完整窗口监督？如果教师能看见而学生不能看见，是否应该直接判本轮监督不可训练？

问题2： 原B要求1–5个区间，意味着不能表达真正的空窗口。若确认组显示这才是主要质量瓶颈，是否应结束本轮续训路线，另立带有合法空输出的独立协议实验，而不是偷偷修改candidate1的grammar？

我的最终意见：先建立可验证的原生事件监督，再进行一次原B的小规模续训；不能证明监督完整和可观察，就不启动训练。没有独立确认质量提升，就不产新的426竞争包。

本轮只完成附件核验、历史代码及结果静态审查、独立方案裁决；没有读取100confirm、调用agy、训练模型、重新生成视频或联网。Pro余额仍按原连续账本5/8、剩3处理，不因本次会诊发生消耗。

ChatGPT 可能会出错。请核查重要信息。
最新一条回复




高

## 第一轮原始完整公开回答：grok-r00.md
SHA256=dfe12f43219e03e10c1c25fb9922d19ab771a94f6c506ecb9c26d03be209562d

工作了 34s

读取确认

任务 AIC-VIDEO-REMATCH-NEXT-20261005 / 子议题 EMPTY407-20261010 / r00。

实际读取范围：附件 context-r00.md 全文 37132 行，至末标 END_EMPTY407_R00。本地计算 SHA256 = d41e34c692283252bec48c0635d5ea3a2ac1f84f3eada219f5fcea60a570fea0（与声明一致，但此为本次读取核对，不代表对原始 Linux 文件的独立主机验签）。未调用外部实验或联网。

事实 / 推断 / 未知

事实：原 B 双窗 37.66 / 102112 选中帧已由用户反馈；新 237 步独立 TVSum 图片评分 LoRA 在 426 上仅 3189 帧、407 空；非测试 8 全空；dev 上 Spearman 0.522 vs base 0.044，native proxy F 点估计改善但 95% CI 跨 0；agy 6 段 90 格 KEEP37/REJECT34/UNKNOWN19，1fps 声明无法独立证明完整观测，末格切镜导致整格过宽；阈值 49 仅 train 人工 80 分位冻结；新包已撤回质量推荐。
推断：407 空高度可能来自任务/域不匹配（TVSum 相对重要性 ≠ AIC 高光边界）+ 绝对分数校准偏移 + 2 秒整格扩展假设，而非单纯工程失败。
未知：真实 AIC 高光召回、官网分、闭源标注与任务定义的实际对齐程度、原 B native 在相同非测试域上的选帧分布。

唯一推荐主路线（有界、可执行）

以原 B native 视频 prompt / grammar / processor / 时钟作为 candidate0 保底。

有界工作包：在已有非测试来源（优先非测试 8 或开放非测试短片）上，用 Gemini 3.8 Flash（agy 终端，最高档）做小批事件级标注（先 3–5 个完整短域或等效 30–60 秒切片，覆盖不同内容类型）。

标注产出后，在同一非测试域上同时回放：

原 B native 预测；
新图片评分选择器的原始分数分布（不改阈值、不强制 TopK）。
用标注作为弱代理，量化两者与闭源事件边界的重合程度、空视频是否对应标注中的真实低光/无高光，以及分数是否系统偏低。此检查可区分校准偏移 vs 语义不匹配 vs 时序输入差异，且不扩大同配方 TVSum、不碰复赛输出、不生成新 426。

最强反例

TVSum 高 Spearman 仍可导致 AIC 崩塌：相对重要性高的“叙事中段/人物特写”在 AIC 短剪辑中可能是冗余过渡；2 秒整格 KEEP 会吞掉切镜后的非高光帧（agy 已实证末格扇舞→行人切换）；分数整体下移后 49 阈值把几乎所有视频判空，即使排序局部正确。CI 跨 0 的 proxy F 已提示该风险，却仍进入 426。

根因最小非测试判别检查

非测试 8（已全空）上：导出新选择器每格 scores_x20 原始分布 + 原 B native 实际选帧区间；同时用上述小批闭源事件标注计算区间 IoU / 覆盖率 / 空视频一致性。若分数中位数显著低于 TVSum train 分布且与标注高光区间错位，则优先校准/任务重定义；若原 B 与标注更重合，则新选择器路线可证伪。不读 100confirm、不按复赛输出调阈值。

标注格式 / 观测方法 / 质量接受条件

格式：事件级（非固定 2 秒格）。每条：KEEP / NO_HIGHLIGHT / UNKNOWN；精确 start/end（原生 PTS 或有理秒）；至少 1 个可见证据帧 ordinal；visible_evidence 文本；observation_scope 与 limitations 必填。
观测：原生 MP4 直接 view_file；对潜在切镜/快速动作提高密度（关键点多帧或短窗密集），不声称逐帧全覆盖；UNKNOWN 保留且不转负例。
接受条件：独立第二观察（不同模型或人工抽查）对边界与切镜一致性 ≥ 预定义比例；证据帧实际对应描述对象；整格过宽导致切镜覆盖的案例显式拒绝或拆分。同教师一致率不视为金标。

原 B 续训 vs 新选择器 + 公平对照

优先原 B native 作为 candidate0。仅当上述非测试判别显示原 B 与闭源事件明显更优，且标签质量验收通过后，才考虑从原 B adapter 续训（明确加载原 adapter SHA、保留 optimizer 状态、train-only 不足标签不凑负例）。新选择器仅作诊断对照，不直接晋升；公平对照必须同 native 输入域、同 grammar、非测试隔离。

数据源与隔离

仅用现有非测试 / 开放非测试来源；train/calibration/confirmation 源级隔离；9 个已见 TVSum dev 不得冒充盲测；新标注不混入旧人工评分训练目标；空间场继续精确复用原 8B 源场（本轮新空间调用 0）。

预算 / 停止条件

本轮仅小批标注 + 非测试回放诊断，无新 GPU 训练、无 426 生成。
停止：UNKNOWN 比例过高或边界验收失败；判别检查显示两者均与标注严重错位；达到预定义小批上限仍无清晰根因方向。
数值（如验收一致率）仅为前瞻工程投入规则，无统计保证。连续 Pro 已用 5/8，剩 3，本讨论不消耗。

对主控的批评（关键弱点）

研究门与 stage2_pass 以点估计 native proxy F > base 放行，同时明确记录配对 95% CI 跨 0，仍推进完整 426。这把“弱代理排序改善”直接当成可投入生产的信号，未能在非测试域提前拦截系统性空视频风险。工程 11strict 通过与质量证据被过度分离。

排序提升 ≠ AIC 高光质量；同教师一致率 ≠ 真值。禁止复赛调阈值、强制 TopK、读 100confirm、重复成功生成。本轮仅文字讨论，等待下一轮交叉审查后由研究项目 Pro 裁决。

## 第一轮原始完整公开回答：gemini-r00-partial-input-visible.md
SHA256=95a31c871627cefbdbb680bf2c1c465ca7f3ceaffef2f8ad7774c4e6401890e0

Gemini 说

本次输入已完整读取主控提供的附件材料及所声明的上下文信息。主控声明文件大小为 841249 字节 / 37132 行，主控声明 SHA256 为 d41e34c692283252bec48c0635d5ea3a2ac1f84f3eada219f5fcea60a570fea0；在此明确：该散列值仅为主控环境的单方声明值，我未在本地沙箱独立验签。当前输入流在 quality_result.json 尾部数据行处自然截断，但前序完整的故障事实、全部 8 个开发/训练/评估/标注脚本源码、前置指标表格及决策链路已完全读取，足以支撑排查与技术路线界定。   
MD
+ 3

根因诊断与事实/推断/未知边界
事实、推断与未知的边界划分

确定事实：新训练 237 步 LoRA 采用 TVSum 图像打分协议（16 图拼接，20..100 整数），冻结阈值 49 来自 39 个训练源的真值 80 分位数。在 9 个已见开发源上，new 模型在 5 个源上的选中帧率为完全全空的 0.000000（-esJrBWj2d8 为 11.2%，Yi4Ij2NM7U4 为 4.4%，cjibtmSLxQ4 为 1.5%，sTEELN-vY30 为 14.8%，EYqVtI9YWJA 为 10.1%）。非测试 8 个视频全部为空，426 个复赛视频中 407 个为空。历史原 B（双窗均衡）曾获用户反馈 37.66 分。   
MD
+ 3

工程推断：407 空并非推理硬件挂起或解码崩塌，而是“预测值收缩”与“真值绝对阈值”错位叠加“固定 2 秒整格脉冲扩展”造成的全域截断。AIC 视频画面分布与 TVSum 存在分布偏移，模型输出向均值（25~45 分）聚拢，几乎无法越过硬编码的 49 分界线。   
MD
+ 1

客观未知：AIC 官方评测真实判分脚本对“空视频”的惩罚机制（是按 F1 判 0 分，还是导致提交格式校验失败）；真实复赛视频中真实正例时长的全局先验分布；以及闭源教师模型在完整视频时序下的真实动作召回率。   
MD

四大技术维度的根因隔离

目标函数与语义任务根因（Semantic & Objective Mismatch）：
TVSum 是视频摘要（Video Summarization）任务，其人工打分反映的是镜头在整个视频中的“信息代表性与冗余度”，均值主要分布在 2~3 分区间。而 AIC 是高光检测与剪辑（Highlight Moment Detection），关注强动作爆发、核心事件与叙事高潮。用摘要代表性替代高光动作性，监督信号从源头即发生语义偏移。   
MD
+ 1

校准根因（Calibration Collapse）：
这是导致 407 空的最直接导火索。主控将训练集人工真值的第 80 百分位数（49）直接作为模型预测输出的二值化硬阈值。深度模型经过回归微调后存在方差收缩（Variance Shrinkage）和均值回归效应，预测分数的经验分布根本不等于标签分布。未经过任何保序回归（Isotonic Regression）或温度校准，直接把真值分位数套用在预测值上，导致在 9 个 dev 源中已有 5 个源全空（模型最大输出从未达到 49）。   
MD
+ 1

时序与采样根因（Temporal & Grid Extrapolation）：
将每 2 秒抽取 1 帧的中点预测分数，无条件广播覆盖这 2 秒内的所有原生帧（50~60 帧）。这种阶跃矩形扩展放大了校准失误：只要采样子帧低了 1 分，整段 2 秒瞬间归零；且 2 秒固定网格完全割裂了镜头时序连续性，破坏了动作的天然起止点。   
MD
+ 1

工程与评估根因（Evaluation Metric Blindness）：
Stage 2 放行规则仅要求 native_macro_proxy_f['new'] > base。在 9 个源中，由于模型在 Yi4Ij2NM7U4 上异常拟合打出了 0.7058 的 F 值（base 仅 0.2175），单点拉高了宏平均，掩盖了超过半数源完全全空的系统性崩溃，使伪优化通过了放行闸口。   
MD
+ 1

主控致命弱点批评与最强反例
弱点批评：形式主义伪严格与指标结构性失明（Verification Theater）

主控耗费大量算力与代码，在 SHA256 账本追踪、Fraction 纳秒对齐、BGR 转 RGB 二进制哈希校验、11 项严格格式回放上构筑了看似无懈可击的防线。然而，主控在最核心的业务质量监控上存在严重的逻辑倒错：
在 PROSPECTIVE_STAGE2.md 中预先写明“empty allowed”，从而在思想上合理化了空输出；当看到 9 个开发源中 5 个全空、非测试 8 个视频全部选出 0 帧时，主控没有将其识别为灾难性异常，反而以“独立 CPU 回放通过、11 项 strict 全部 PASS、允许空是原协议行为”为由，强行推进了 426 个全量复赛推理，最终产出 407 个空视频的废弃包。主控用完美的“流程合规”掩盖了“业务死亡”。   
MD
+ 2

最强反例（The Strongest Counterexample）

构造一个退化退火模型 M
degen
	​

：
对任意输入的 16 图序列，该模型全部预测常数 30 分（低于阈值 49），但在遇到特定背景色彩的视频（例如特定亮度的一段采访）时，对其中连续两格恒定预测 50 分。
在包含 9 个开发源的集合中，M
degen
	​

 在 8 个源上的选中帧数均为 0，对应的局部指标全为 0；唯独在第 9 个源上，这两格恰好撞上了人工高光，取得局部 F=0.8。
此时计算宏平均代理指标：
   
MD

Macro Proxy F=
9
0×8+0.8
	​

≈0.0889

对照基座的宏平均指标：

Base Macro Proxy F=0.0415[cite: 1]


因为 0.0889>0.0415，该退化模型完美通过主控现行的 Stage 2 放行门槛（stage2_pass = True）！然而该模型在全域场景下的全空率高达 88.9%。这确证了：当前主控依赖的宏平均代理 F 值，极易被单一源的极端高分绑架，对大面积全空的系统性溃败毫无防御能力。   
MD
+ 1

唯一推荐执行路线：基于原 B 骨架的高光闭源蒸馏（有界闭环）

必须坚守底线原则：

排序提升不等于 AIC 高光质量，同教师一致率不等于真值。   
MD

严禁复赛调阈值、严禁强制 TopK 兜底、严禁读取 100confirm、严禁对复赛数据做输出分布逆推。   
MD

空间场沿用原 8B 冻结源场（31295 锚点），不追加空间模型调用。   
MD

路线唯一选择：彻底废弃独立的 16 图 TVSum 图像评分选择器，回归原 B native 视频时序协议作为 Candidate 0；通过终端 agy 对非测试视频执行基于切镜与动作边界的闭环标注，在原 B adapter 权重上进行小学习率时序边界微调。   
MD

[现有非测试视频 (Train/Dev/Holdout)]
                 │
                 ▼
[Shot 切镜预分段 (PySceneDetect / I-frame 强边界)]
                 │
                 ▼
[终端 agy (Gemini 3.8 Flash high) 结构化三态标注] ──> (拒绝跨镜整格/保留 UNKNOWN 隔离)
                 │
                 ▼
[严格语义与观测验收 (通过率门禁)]
                 │
                 ▼
[以原 B Adapter 为起点，加载权重续训 (Native 视频时序微调)]
                 │
                 ▼
[非测试 8 视频最小判别门禁] ──(未超越 Candidate 0 / 出现全空)──> 触发 STOP，直接回退 37.66 保底
                 │ (严格胜出)
                 ▼
[单次 426 复赛生成与打包]

1. 非测试最小判别检查（Sanity Check Gate）

在对 426 视频启动任何推理之前，必须且仅在现有的 8 个非测试视频（nontest）上执行最小判别，不通过则严禁进入复赛：

全空一票否决（Zero-Empty Veto）：8 个非测试视频中，空视频数量必须严格为 0。

帧预算合理性区间：整体选中帧占总视频帧数比例必须处于 [12%,28%] 之间，且单视频选中率标准差不得超过 10%（严禁饥饿或泛滥）。

切镜交叠惩罚：选中的高光区间与场景切换点的重合度必须小于 5%（高光不可跨越突兀切镜）。

2. 标注格式、切镜边界与真实观测接受条件

终端 agy 标注必须从“粗暴 2 秒网格打标签”升级为“Shot 约束下的事件级三态标注”：   
MD

输入预切分：禁止送入跨切镜片段。利用基础切镜工具对长视频切分为单镜头单元（Shot），候选边界严格对齐 Shot 边界。

输出格式约束：

JSON
{
  "shot_id": 12,
  "start_pts": 145000,
  "end_pts": 235000,
  "state": "KEEP | REJECT | UNKNOWN",
  "action_description": "明确的动作核心与视觉主体",
  "observed_keyframes_pts": [150000, 180000, 220000],
  "boundary_confidence": "HIGH | MEDIUM | LOW"
}


真实观测证明与接受条件：

模型必须列出其判断所依据的具体关键帧时间戳（observed_keyframes_pts），禁止仅给结果不给观测依据。   
MD

三态逻辑隔离：KEEP 必须具备明确主体动作；REJECT 必须是观察完整且明确为静态/过渡的内容；UNKNOWN 包含视野模糊、镜头快速晃动、动作未完成等一切不确定情况。   
MD

负例规则：UNKNOWN 严格作为中性掩码剔除，绝不作为负例（not_semantic_highlight_gold = true）；仅将高置信度的 REJECT 作为时序对比负例。   
MD

单段废弃规则：若一个 Shot 内存在未观察到的切镜（如 91IHQYk1IQM 尾帧行人突变案例），该 Shot 必须直接废弃或将边界截断至切镜前，严禁整格强行赋 KEEP。单视频 UNKNOWN 比例超过 35% 则整视频隔离。   
MD

3. 数据来源隔离与多维质量指标

源级强隔离：数据切分必须以原始视频 Source ID 为单位严格隔离，禁止将同源视频的不同片段混入 Train 和 Calibration/Dev 集。   
MD

替代脆弱 Proxy F 的多维指标：

事件级加权 IoU-mAP：以交并比 IoU ≥0.5 为门槛，计算高光区间的召回与精确度。

有效非空覆盖率（Non-Empty Video Coverage）：开发集视频非空率必须为 100%。

排序与边界联合增益：对有标注区间的排序相关系数改善，必须伴随帧分布方差在合理边界内。

4. 原 B Native 公平 Candidate 0

基准身份冻结：Candidate 0 明确为原始原 B adapter（权重 SHA 8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23），配合其原生视频双窗均衡 prompt 与时钟协议。   
MD

同场对照原则：所有新训练成果，必须在相同的非测试 8 视频上，与 Candidate 0 进行逐帧交并比、有效选中率及边界置信度的一对一严格对比。只有在整体边界更紧凑且覆盖合理的前提下，才构成候选升级资格。

5. 训练配方与 STOP 中止条件

训练机制：

明确继承原 B：必须显式从原 B adapter safetensors 加载权重续训，严禁从基座从头盲训。   
MD

微调参数：LoRA rank 保持原规格，冻结视觉编码器，仅微调语言注意力和时序投影层；学习率压缩至 1.5×10
−5
（采用余弦衰减），训练严格限制在 120 优化步以内，batch 保持梯度累积，防止破坏原 B 已建立的视觉语义空间。

硬性 STOP 条件（立即终止并交付 37.66 保底）：

训练过程出现 Loss 震荡不收敛或非有限值（Nonfinite Gradients）。

在非测试 8 视频执行推理后，出现任何 1 个视频全空，或选中帧比例超出 [10%,35%] 边界。

非测试集上的事件级指标未能严格胜出 Candidate 0。

算力预算消耗达到 2000 计费秒，或剩余 3 次 Pro 原簿额度面临无意义耗费时。   
MD

一旦触发任何一条 STOP 条件，严禁对 426 复赛集执行试探性推理，立刻以原字节引用历史 37.66 稳定包（SHA 07730c9e02e68d1a1ce54e7ef5a8aa616346cf8f2f8d78426ed36bc3eb481496）作为唯一交付物，终止本轮试探。   
MD




Flash
高点

Gemini 是一款 AI 工具，其回答未必正确无误。

## 第一轮原始完整公开回答：gemini-r00b.md
SHA256=2afe601ac079301ac3023dfd762c49c5657e7928442c54a5fcda827133b89dd8


读取范围确认与认知边界界定
1. 附件读取范围确认

完整读取本次上传的索引文件 context-r00b-index.md 及 4 卷分卷正文至终末标记 END_EMPTY407_R00B：   
MD
+ 1

context-r00b-index.md：2,361 字节，索引声明全文完整。   
MD

context-r00b-part01.md：104,985 字节，读取范围包含用户要求、关键事实、主控初始立场，以及自 PLAN.md 至 agy_short_clips_v2.py 前半段的所有报告与核心代码。   
MD

context-r00b-part02.md：2,487 字节，完整承接 agy_short_clips_v2.py 的执行函数及终态，平滑衔接进入 quality_result.json 的起始定义。   
MD

context-r00b-part03.md：123,573 字节，完整读取格式压缩后的 quality_result.json，无字段或数值截断。   
MD

context-r00b-part04.md：84,598 字节，完整读取 contest_results/completion.json、历史 b_sft8b_package_v3、b_score_aligned_package_v4、balanced_two_window_risk_v3、teacher_student_autopilot_v14、pro-p01.md 裁决、官方复赛通知快照及 temporal_common.py，读至 END_EMPTY407_R00B。   
MD

四卷拼接累计声明字节数为 315,643 字节，主控声明完整 SHA256 为 e436c71211d70252d24c6b5b3b1a458e959e3b26284e61b1bbeb7c9cd2cca479。必须客观声明：该散列值为主控单方声明，我在本交互会话中已逐行读毕全部文本流并核对末标，但未在本地操作系统环境对其进行底层独立验签。   
MD
+ 1

2. 客观事实、机制推断与未知边界划分
客观事实（已有日志与代码直接证明）

开发源真实分布更正：在 9 个 TVSum 已见开发源上，new 模型（237 步 LoRA，阈值 49）的实际结果为 4 个源全空、5 个源非空：   
MD
+ 1

全空源（选中帧数 = 0，占比 0.00%）：4wU_LUjG5Ic、J0nA4VgnoCo、JKpqYvAdIsw、i3wAGJaaktw。   
MD

非空源（选中帧数 > 0）：-esJrBWj2d8（11.28%）、EYqVtI9YWJA（10.07%）、Yi4Ij2NM7U4（4.44%）、cjibtmSLxQ4（1.54%）、sTEELN-vY30（14.77%）。   
MD

注：cjibtmSLxQ4 虽选出 299 帧，但选出帧的人类评分均低于 3（selected_human_below3_fraction = 1.0），导致其代理 F 值为 0.00。   
MD

全流程全空事实：非测试 8 个视频全部输出为空（8/8 空，选中 0 帧）；复赛 426 个视频输出中 407 个为空、19 个非空（仅选出 3,189 帧）。   
MD
+ 1

阈值来源：阈值 49 严格来自于 39 个训练源人工真值分数的第 80 百分位数（nearest-rank 80th percentile），并未对模型在该 prompt 下的预测分数分布做任何拟合或重校准。   
MD
+ 1

基线状态：原 B8B + 双窗均衡历史最佳成绩为用户反馈的 37.66，产生 102,112 个选中帧，ZIP SHA 为 07730c9e02e68d1a1ce54e7ef5a8aa616346cf8f2f8d78426ed36bc3eb481496。   
MD

代理指标特性：开发集上 new 模型 Macro Spearman 达到 0.5223（base 为 0.0436），但配对 native macro proxy F 改善量的 95% Bootstrap 置信区间为 [−0.001096,0.210326]，区间下界跨 0。   
MD
+ 1

机制推断（基于代码与统计特性的合理解释，非确证唯一真因）

分布收缩与硬截断错位：深度回归模型微调容易产生方差收缩与均值回归现象（预测值集中在 25~45 之间）。将人工打分的 80 分位数硬编码为预测截断线，是导致模型输出大面积跌破阈值而全空的最直接技术诱因。   
MD
+ 2

任务定义偏移：TVSum 监督的是 20 人平均的视频摘要代表性（相对重要性），而 AIC 是无 query 的短视频高光事件抽取。排序能力（Spearman）在摘要领域的提升，无法等价于 AIC 高光召回能力的成立。   
MD
+ 1

采样扩展的方差放大：将 2 秒中点采样的离散打分强行广播赋给同格全部 50~60 个原生帧，属于无边界支撑的阶跃扩展。若该采样帧的分数恰好低于 49，整段 2 秒瞬间跌落归零，放大了阈值偏置的敏感度。   
MD
+ 3

客观未知（当前材料无法证实的事项）

AIC 官方评测系统对“空视频”的真实判定惩罚逻辑（是直接判 0 分、按极低召回惩罚 F1，还是影响解包有效性）。   
MD

复赛 426 数据集中客观上“真正无高光”的真实样本比例。   
MD

闭源大模型在长时序上下文下对 AIC 真正高光事件边界的准确召回率与误报率。   
MD

根因维度的结构化排查
                        407/426 全空故障多维溯源
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         ▼                         ▼                         ▼
   【校准根因】               【目标与语义根因】        【时序与网格根因】
真值80分位数(49)硬套       TVSum摘要代表性均值       2秒中点离散采样向
模型收缩预测值，无分       ≠ AIC强动作高光提取，     整格强行广播，丢失
布重对齐与温度校准         排序提升不等于高光质量     连续动作与镜头切分


校准根因（Calibration Mismatch）：
这是最直接的数值诱因。主控脚本将训练集标签的经验 80 分位点（49）直接作为推理时的二值化判断条件。模型预测值受正则化与损失约束，其预测分布动态范围通常窄于真值分布。缺乏保序回归、Platt 缩放或在验证集上的独立经验分位数映射，直接套用硬阈值导致绝大部分视频的预测最大值无法突破 49。   
MD
+ 3

语义与目标函数根因（Semantic & Objective Divergence）：
TVSum 的监督本质是全局代表性冗余消除（Summarization）。高相关系数（Spearman 0.52）仅证明模型在辨别“哪个画面相对更具代表性”上有所学习，但不提供“某个画面是否达到 AIC 高光剪辑准入标准”的绝对度量。   
MD
+ 2

时序与采样根因（Temporal Discretization & Bin Assumption）：
每 2 秒仅取 1 个中点原生帧送入 16 图序列。在实际视频中，快速发生的突发高光动作容易被跳过；反之，若中点落在背景过渡帧，整段 2 秒即被判定剔除。这种粗粒度时间离散化与 AIC 原生高光的毫秒级/多镜头叙事要求存在粒度失配。   
MD
+ 4

评估门禁盲区（Gate Vulnerability）：
Stage 2 放行条件仅依赖 native_macro_proxy_f['new'] > base。在 9 个源中，仅因 Yi4Ij2NM7U4 单源的 F 值由 0.2176 冲高至 0.7059（净增 0.488），便将整体宏平均拉升，掩盖了 4 个源全空、1 个源有效选帧全错（cjibtmSLxQ4）的严重系统性溃缩，导致伪进展通过了放行闸口。   
MD
+ 2

主控关键弱点批评与最强反例
弱点批评：防御性工程合规替代了业务可用性底线（Verification Theater）

主控在工程底层（哈希绑定、纳秒级有理数网格、单次 BGR 到 RGB 转换核验、CPU 预测重放及 11 项 strict 检查）展现了严密的防御性设计。然而，主控在最核心的业务质量门禁上陷入了形式主义：
在 PROSPECTIVE_STAGE2.md 中写下 empty allowed，本意是尊重“合法无高光视频可以为空”的业务规律；但主控将其扭曲成了对系统性瘫痪的免责条款——在非测试 8 视频执行结果为 empty_videos = 8（100% 全空）、426 执行结果为 empty_videos = 407（95.5% 全空）时，主控依然以“符合预定协议、11-strict PASS、允许空是原协议行为”完成了全量流水线并生成最终候选包。主控预先设立了非测试验收环节，却未赋予其阻断能力，任由明显失效的策略推演至复赛全量生产。   
MD
+ 4

最强反例（The Strongest Counterexample）

构造一个极度退化的伪模型 M
spike
	​

：
该模型对所有输入的图像格无差别输出预测分 30（均低于阈值 49），仅在极少数具有特定背景（如纯色背景）的画面中恒定输出 52。

在 9 个已见开发源中，M
spike
	​

 在 8 个源上从未出现该特征，帧预测全部低于 49，8 个源的选中帧数全部为 0，对应的局部 Proxy F 均为 0。   
MD

在第 9 个源上，该背景恰好与某处高分重合，选出了部分重合帧，取得局部 Proxy F = 0.60。

计算宏平均指标：

Macro Proxy F=
9
0×8+0.60
	​

≈0.0667


基座模型 Base 的宏平均指标为 0.0415。   
MD

依据主控预先冻结的 Stage 2 规则 native_macro_f['new'] > base（0.0667>0.0415），该退化模型将完全合规地通过门禁，被推入全量 426 推理，产出近乎全域全空的废弃结果。   
MD
+ 1

结论：现行等权宏平均代理 F 指标极易被单一源的离群收益绑架，对系统性空选崩溃完全缺乏辨识力。   
MD
+ 1

唯一可执行有界路线：回归原 B 视频时序协议（Candidate 0），探索有界闭环增量

坚决恪守前提原则：

排序提升不等于 AIC 高光质量，同教师一致率不等于真值。   
MD

严禁复赛调阈值、严禁强制 TopK 兜底、严禁读取 100confirm、严禁根据复赛输出反推参数。   
MD

空间场严密复用原 8B 冻结源场（31,295 锚点），不新增空间模型调用。   
MD
+ 1

合法无高光视频可以为空；跨镜叙事可以是完整高光事件；编码 I 帧绝不等于语义切镜。   
MD
+ 1

路线唯一选择：彻底废弃独立的 16 图 TVSum 图像评分选择器架构，以原 B（双窗均衡，37.66）原生视频时序协议作为 Candidate 0，基于终端 agy 结构化标注建立有界闭环验证。   
MD
+ 1

                  ┌──────────────────────────────────────────────┐
                  │ Candidate 0: 原B8B+双窗均衡 (37.66 冻结底线)  │
                  └──────────────────────┬───────────────────────┘
                                         │ 对照基准
                                         ▼
┌──────────────────────┐      ┌──────────────────────┐      ┌──────────────────────┐
│  非测试来源视频集    │ ───> │ 终端 agy (Gemini)    │ ───> │ 严格语义与观测验收   │
│ (严格按Source ID隔离)│      │ 连续时序三态结构标注 │      │ (UNKNOWN中性隔离)    │
└──────────────────────┘      └──────────────────────┘      └──────────┬───────────┘
                                                                       │ 达标放行
                                                                       ▼
                                                            ┌──────────────────────┐
                                                            │ 显式继承原B Adapter  │
                                                            │ 微步续训 (极低学习率)│
                                                            └──────────┬───────────┘
                                                                       │
                                                                       ▼
                                                            ┌──────────────────────┐
                                                            │ 非测试最小判别检查   │
                                                            │ (相对 Candidate 0)   │
                                                            └──────────┬───────────┘
                                                                       │ 未超越或病态偏离
                                          ┌────────────────────────────┴──────────────────────────┐
                                          ▼ 超越基准                                              ▼ 触发 STOP
                               ┌──────────────────────┐                                ┌──────────────────────┐
                               │ 单次 426 推理与打包  │                                │ 回退 37.66 历史保底  │
                               │ (严禁线上调参/补TopK)│                                │ (NO426 封存本轮工作) │
                               └──────────────────────┘                                └──────────────────────┘

1. 非测试最小判别检查（Sanity Check Gate）

在对 426 复赛集执行任何推理前，必须且仅在现有的非测试视频（nontest）上执行防御性判别，明确以下规则为前瞻工程管理规则，非统计保证事实：   
MD
+ 1

相对基准离群检验（Relative Anomaly Check）：新模型在非测试样本上的输出行为不得与 Candidate 0 发生病态偏离。若 Candidate 0 在某视频中给出了有效的高光召回，而新模型在相同输入下产生断崖式萎缩（如全空）或数量级暴增，直接判定模型进入病态区间，一票否决。   
MD
+ 3

语法与结构有效性：输出区间必须严格遵循 0 <= start < end <= clip_duration，解析失败及语法截断率必须为 0。   
MD

允许合法全空，拒绝系统性极值：允许单个无高光视频为空，但若模型在非测试集全部样本上均输出为空或均输出饱和全选，判定为分布坍塌。   
MD
+ 1

2. 标注格式、切镜边界与真实观测接受条件

终端 agy 标注必须从机械的 2 秒网格打标升级为具备事件边界意识的结构化标注：   
MD

切镜与叙事边界原则：

切镜识别工具：应使用基于像素内容连续性或直方图差异的算法（如 PySceneDetect），严禁将视频编码的 I 帧（Keyframe）直接等同于语义切镜。   
MD

跨镜叙事接纳：明确跨镜头的动作衔接、正反打对话或镜头组接可以是完整的高光事件。如果高光区间跨越了切镜，要求标注中提供该动作连续性的描述依据；对于单镜头内的独立高光，区间应紧贴动作起止，不应机械跨越无关镜头。   
MD
+ 1

标注输出格式约束：

JSON
{
  "segment_id": 0,
  "start_sec": 4.50,
  "end_sec": 12.20,
  "state": "KEEP | REJECT | UNKNOWN",
  "action_summary": "明确的主体、核心动作与叙事高潮说明",
  "observed_keyframes_seconds": [5.0, 8.5, 11.0],
  "spans_multiple_shots": false,
  "boundary_clarity": "HIGH | MEDIUM | LOW"
}


真实观测证明与接受条件：

强制可见依据：标注必须列出其实际观察到的采样时间点（observed_keyframes_seconds），禁止无支撑的区间推测。   
MD

三态逻辑隔离：KEEP 仅用于视觉特征明确的高光核心；REJECT 仅用于充分观察且确认冗余/平淡的片段；UNKNOWN 包含镜头模糊、动作起止模糊、快速晃动等一切不确定情形。   
MD

严格负例隔离：UNKNOWN 仅作为掩码排除，绝对不得当作负例监督；仅有充分观察的高置信度 REJECT 方可作为对比负例。   
MD

单段废弃规则：若某段高光区间在尾部被证实切入完全无关的静态路人（如 91IHQYk1IQM 案例），该区间必须被截断至切镜前，或标记为 UNKNOWN 隔离，严禁将整段全赋 KEEP。   
MD

3. 数据来源隔离与多维质量指标

来源级强隔离（Source-Level Isolation）：切分必须以原始视频 Source ID 为最小原子单位，彻底物理隔离 Train、Dev、Holdout，严禁同源视频的不同片段跨 split 渗透。   
MD
+ 1

多维评价体系（取代脆弱的单点 Proxy F）：

事件级 IoU 加权 F1：在有标注的非测试集合上，以时间交并比（IoU ≥0.5）为准绳评估边界质量。   
MD

逐源胜率（Source-Level Win Rate）：在验证集上，新模型相对 Candidate 0 表现改善的源必须占多数，且最差单源退化幅度必须受限。   
MD
+ 1

选帧分布散度监测：监控新模型与 Candidate 0 在选帧比例上的分布差异，防止阈值偏移导致整体漂移。   
MD
+ 1

4. 原 B Native 公平 Candidate 0

基线身份锁定：Candidate 0 严格为已获 37.66 的原 B adapter（权重 SHA 8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23），配合其双窗均衡提示词、原生 video 标签与时钟配置。   
MD
+ 1

公平比对原则：任何新训练或新配置，必须在同一组非测试视频、同等解码配置与完全一致的空间场下，与 Candidate 0 展开端到端的选帧重合度及事件边界一对一比对，未全面优于 Candidate 0 前不得晋升。   
MD
+ 1

5. 训练机制与硬性 STOP 终止条件

微调机制：

显式续训：严禁从原始基座从头盲训，必须显式加载原 B adapter 权重作为初始化。   
MD
+ 1

训练超参数管理建议：冻结视觉编码器与主干权重，仅微调语言 LoRA；学习率建议收敛在极小范围（如 1×10
−5
），优化步建议控制在 50 步以内或采用早停策略，防止破坏原 B 已建立的时序感知空间。   
MD
+ 1

硬性 STOP 条件（立即终止并回退 37.66 保底）：

训练初期 Loss 发生发散、震荡或出现非有限数值（NaN/Inf）。   
MD
+ 1

在非测试样本推理中，出现与 Candidate 0 的系统性偏离（如 Candidate 0 有正常选帧，而新模型出现全空，或选帧总量发生量级萎缩）。   
MD
+ 1

验证集上的事件级评测与逐源胜率未能严格击败 Candidate 0。   
MD
+ 1

连续 Pro 预算原簿累计已达 5/8（剩余 3 次），禁止为无质量突破的中间过程耗费 Pro 裁决。   
MD

一旦触发上述任何一项 STOP 条件，立即停止向复赛 426 集推演，以历史 37.66 保底包（SHA 07730c9e02e68d1a1ce54e7ef5a8aa616346cf8f2f8d78426ed36bc3eb481496）作为本轮唯一交付产物，封存所有实验产物与账本。   
MD




Flash
高点

Gemini 是一款 AI 工具，其回答未必正确无误。

## 补充原文件全文：reports/qwen8b_annotation_20261009_v1/training_v2/train_lora.py
字节=5297 SHA256=46b3ef67cbed55b29db77d29b010b16b49474d831b918dc8fb60664260169614

```py
"""Explicit preflight/train entry. Default preflight never loads model weights or CUDA."""
import argparse
import hashlib
import json
from pathlib import Path

from sft_contract import ImageSFTCollator, load_rows


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--config', required=True)
    p.add_argument('--dataset-root', required=True)
    p.add_argument('--model', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--train', action='store_true', help='Explicitly authorize this invocation to load weights and optimize')
    args = p.parse_args()
    config = json.loads(Path(args.config).read_text(encoding='utf-8'))
    root = Path(args.dataset_root).resolve(strict=True)
    from verify_bundle import verify
    verify(root)
    output = Path(args.output).resolve()
    if output.exists():
        raise ValueError('Use a new output directory; no overwrite or implicit resume')
    rows = {s: load_rows(root / config[f'{s}_file'], root) for s in ('train', 'validation')}
    if {r['source_group'] for r in rows['train']} & {r['source_group'] for r in rows['validation']}:
        raise ValueError('Train/validation source leakage')
    if any(r['task'] != config['task'] for s in rows.values() for r in s):
        raise ValueError('Do not silently mix tasks')
    from transformers import AutoProcessor
    processor = AutoProcessor.from_pretrained(args.model, local_files_only=True,
                                             min_pixels=config['min_pixels'], max_pixels=config['max_pixels'])
    model_config = Path(args.model) / 'config.json'
    expected = config.get('model_config_sha256')
    actual = hashlib.sha256(model_config.read_bytes()).hexdigest()
    if expected is None or actual != expected:
        raise ValueError('Model config identity is missing or changed')
    collator = ImageSFTCollator(processor, root, max_tokens=config['max_input_tokens'])
    # Every real row is processed before any model/optimizer operation. Refuse silent truncation.
    stats = {}
    for split, records in rows.items():
        counts, supervised = [], []
        for row_index, row in enumerate(records):
            encoded = collator.encode(row)
            counts.append(encoded['input_ids'].shape[1])
            supervised.append(int((encoded['labels'] != -100).sum()))
            if row_index % 20 == 0:
                print(json.dumps({'stage': 'PROCESSOR_PREFLIGHT', 'split': split,
                                  'done_rows': row_index + 1, 'expected_rows': len(records)}), flush=True)
        stats[split] = {'rows': len(records), 'max_tokens': max(counts), 'min_assistant_tokens': min(supervised)}
    output.mkdir(parents=True)
    receipt = {'status': 'PASS_ALL_REAL_IMAGE_ROWS_PROCESSOR_AND_MASK_PREFLIGHT', 'stats': stats,
               'model_config_sha256': actual, 'model_weights_loaded': False, 'optimizer_started': False}
    (output / 'preflight.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    if not args.train:
        print(json.dumps(receipt))
        return
    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import Qwen3VLForConditionalGeneration, Trainer, TrainingArguments
    if not torch.cuda.is_available():
        raise ValueError('Requested training has no CUDA device; no silent CPU fallback')
    model = Qwen3VLForConditionalGeneration.from_pretrained(args.model, local_files_only=True,
                torch_dtype=torch.bfloat16, attn_implementation='sdpa')
    targets = [name for name, module in model.named_modules()
               if name.endswith(tuple('.' + n for n in ('q_proj', 'k_proj', 'v_proj', 'o_proj')))
               and 'visual' not in name and 'vision' not in name and 'language_model' in name]
    if not targets:
        raise ValueError('Language-only LoRA targets not found')
    model = get_peft_model(model, LoraConfig(r=config['lora_rank'], lora_alpha=config['lora_alpha'],
                lora_dropout=config['lora_dropout'], target_modules=targets, bias='none', task_type='CAUSAL_LM'))
    model.config.use_cache = False
    training_args = TrainingArguments(output_dir=str(output / 'trainer'),
                per_device_train_batch_size=1, per_device_eval_batch_size=1,
                gradient_accumulation_steps=config['gradient_accumulation_steps'],
                learning_rate=config['learning_rate'], num_train_epochs=config['epochs'],
                warmup_ratio=0.05, weight_decay=0.01, bf16=True, gradient_checkpointing=True,
                gradient_checkpointing_kwargs={'use_reentrant': False},
                remove_unused_columns=False, dataloader_num_workers=0, report_to=[],
                eval_strategy='epoch', save_strategy='epoch', save_total_limit=2,
                logging_steps=1, seed=20261009, data_seed=20261009)
    trainer = Trainer(model=model, args=training_args, train_dataset=rows['train'],
                      eval_dataset=rows['validation'], data_collator=collator)
    result = trainer.train()
    trainer.save_model(str(output / 'adapter'))
    processor.save_pretrained(output / 'adapter')
    trainer.save_state()
    (output / 'train_metrics.json').write_text(json.dumps(result.metrics, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()

```


## 补充原文件全文：reports/qwen8b_annotation_20261009_v1/training_v2/sft_contract.py
字节=7250 SHA256=1656abf79b8ff266851c6d4b03bbda2840ed6bed8a2dfba280800489863186a2

```py
"""Portable Qwen3-VL image SFT contract; assistant-only loss and exact source pixels."""
import json
from pathlib import Path

import torch
from PIL import Image


def load_rows(path, root):
    root = Path(root).resolve(strict=True)
    rows = [json.loads(s) for s in Path(path).read_text(encoding='utf-8').splitlines()]
    if not rows or len({r['id'] for r in rows}) != len(rows):
        raise ValueError('Empty dataset or duplicate row ID')
    for row in rows:
        if [m['role'] for m in row['messages']] != ['user', 'assistant']:
            raise ValueError('Expected one user message and one assistant answer')
        if row['messages'][0]['content'].count('<image>') != len(row['images']):
            raise ValueError('Image placeholders and real images must match exactly')
        answer = json.loads(row['messages'][1]['content'])
        if row['task'] == 'spatial_pixel_crop':
            if set(answer) != {'box_xyw'} or len(answer['box_xyw']) != 3:
                raise ValueError('Wrong crop target')
            if not all(type(v) is int for v in answer['box_xyw']):
                raise ValueError('Crop coordinates must be integer pixels')
        elif row['task'] in ('temporal_tvsum_frame_importance', 'temporal_tvsum_importance_x20'):
            key = 'scores_x20' if row['task'].endswith('_x20') else 'scores'
            low, high = (20, 100) if key == 'scores_x20' else (1, 5)
            if set(answer) != {key} or len(answer[key]) != len(row['images']):
                raise ValueError('Wrong temporal target length')
            if not all(type(v) is int and low <= v <= high for v in answer[key]):
                raise ValueError('TVSum scores outside declared scale')
        else:
            raise ValueError('Unrecognized task')
        for image in row['images']:
            relative = Path(image)
            if relative.is_absolute() or '..' in relative.parts:
                raise ValueError('Only contained portable image paths are allowed')
            path = (root / relative).resolve(strict=True)
            if not path.is_relative_to(root):
                raise ValueError('Image escapes dataset root')
    return rows


def typed_messages(row, images):
    text = row['messages'][0]['content']
    parts = text.split('<image>')
    if len(parts) - 1 != len(images):
        raise ValueError('Image count mismatch')
    content = []
    for i, part in enumerate(parts):
        if part:
            content.append({'type': 'text', 'text': part})
        if i < len(images):
            content.append({'type': 'image', 'image': images[i]})
    return [{'role': 'user', 'content': content},
            {'role': 'assistant', 'content': [{'type': 'text', 'text': row['messages'][1]['content']}]}]


class ImageSFTCollator:
    def __init__(self, processor, dataset_root, max_tokens=16384, image_loader=None):
        self.processor = processor
        self.root = Path(dataset_root)
        self.max_tokens = max_tokens
        self.image_loader = image_loader

    def _images(self, row):
        if self.image_loader is not None:
            return self.image_loader(row)
        images = []
        for path in row['images']:
            with Image.open(self.root / path) as im:
                rgb = im.convert('RGB')
                rgb.load()
                images.append(rgb)
        return images

    def encode(self, row):
        images = self._images(row)
        messages = typed_messages(row, images)
        full = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        prefix = self.processor.apply_chat_template(messages[:1], tokenize=False, add_generation_prompt=True)
        encoded = self.processor(text=[full], images=images, return_tensors='pt', padding=False)
        prompt = self.processor(text=[prefix], images=images, return_tensors='pt', padding=False)
        ids = encoded['input_ids']
        n = prompt['input_ids'].shape[1]
        if ids.shape[1] > self.max_tokens:
            raise ValueError(f'No silent truncation: {ids.shape[1]} > {self.max_tokens}')
        if n >= ids.shape[1] or not torch.equal(ids[:, :n], prompt['input_ids']):
            raise ValueError('Full token sequence must have an exact user/generation prefix')
        labels = ids.clone()
        labels[:, :n] = -100
        labels[encoded['attention_mask'] == 0] = -100
        if not bool((labels != -100).any()):
            raise ValueError('No assistant target tokens')
        if 'pixel_values' not in encoded or 'image_grid_thw' not in encoded:
            raise ValueError('Real image vision tensors missing')
        if encoded['image_grid_thw'].shape[0] != len(images):
            raise ValueError('Vision grids and images disagree')
        encoded['labels'] = labels
        return encoded

    def __call__(self, rows):
        values = [self.encode(r) for r in rows]
        longest = max(v['input_ids'].shape[1] for v in values)
        pad = self.processor.tokenizer.pad_token_id
        if pad is None:
            raise ValueError('Tokenizer must define a padding token')
        batch = {}
        for key, fill in [('input_ids', pad), ('attention_mask', 0), ('labels', -100)]:
            target = values[0][key].new_full((len(values), longest), fill)
            for i, value in enumerate(values):
                n = value[key].shape[1]
                target[i, :n] = value[key][0]
            batch[key] = target
        expected = {'input_ids', 'attention_mask', 'labels', 'pixel_values', 'image_grid_thw'}
        for value in values:
            if set(value) != expected:
                raise ValueError(f'Unexpected processor tensors require explicit handling: {set(value) - expected}')
        for key in ('pixel_values', 'image_grid_thw'):
            batch[key] = torch.cat([v[key] for v in values], dim=0)
        return batch


def decode_output(text, task, image_count=None, source_size=None, ratio=None):
    """Strict JSON parsing. Never clamp, silently fall back, or infer empty as negative."""
    obj = json.loads(text)
    if task in ('temporal_tvsum_frame_importance', 'temporal_tvsum_importance_x20'):
        key = 'scores_x20' if task.endswith('_x20') else 'scores'
        low, high = (20, 100) if key == 'scores_x20' else (1, 5)
        if set(obj) != {key} or len(obj[key]) != image_count:
            raise ValueError('Temporal output count mismatch')
        if not all(type(v) is int and low <= v <= high for v in obj[key]):
            raise ValueError('Temporal output outside TVSum scale')
        return obj
    if task == 'spatial_pixel_crop':
        if set(obj) != {'box_xyw'} or len(obj['box_xyw']) != 3:
            raise ValueError('Wrong crop output')
        x, y, w = obj['box_xyw']
        if not all(type(v) is int for v in (x, y, w)):
            raise ValueError('Non-integer crop output')
        rw, rh = ratio
        if w <= 0 or w * rh % rw:
            raise ValueError('Crop height must be positive and exact integer')
        h = w * rh // rw
        iw, ih = source_size
        if x < 0 or y < 0 or x + w > iw or y + h > ih:
            raise ValueError('Crop outside source')
        return {'box_xywh': [x, y, w, h]}
    raise ValueError('Unrecognized task')

```


## 补充原文件全文：reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/balanced_two_window_risk_v3/bw_common.py
字节=11048 SHA256=a70d2b2fd9a009291fe6c17556e5875d9918fc7a1e29170f7baa486721b6c79e

```py
"""Independent balanced-two-window input and exact unchanged-success authority."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

HERE=Path(__file__).resolve().parent
RUN=HERE.parent
CAD=RUN/'context_advisory_v1'
PY='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'

def require(ok,reason):
    if not ok:raise ValueError(reason)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()

def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def utc():return datetime.now(timezone.utc).isoformat()

def save(path,value,fresh=True):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    text=json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    if fresh:
        with p.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
    else:
        tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(text,encoding='utf-8');tmp.replace(p)

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod

def helpers():
    sys.path.insert(0,str(CAD))
    rt=load(CAD/'runtime.py','bw_original_cad_runtime')
    student,old,frames,production=rt.bind_helpers()
    ex=load(CAD/'experiment.py','bw_original_cad_experiment')
    import context_contract as cc
    return rt,ex,cc,student,old,frames,production

def verify():
    lock=read(HERE/'source_lock.json')
    for p,s in lock['files'].items():require(sha(p)==s,'frozen balanced-two-window-alignment dependency changed: '+p)
    return lock

def state(stage,**kw):
    value=dict(stage=stage,utc=utc(),pid=__import__('os').getpid(),new_optimizer_updates=0,
        new_32B_calls=0,official_score=None,uploaded=False,**kw)
    save(HERE/'progress.json',value,fresh=False);print(json.dumps(value),flush=True)

def base_job(job):
    import copy
    value=copy.deepcopy(job)
    for part in value['windows']:
        part['window']=part['base_window'];part.pop('base_window',None)
    return value

def base_path(scope,job,ix,cc):
    return CAD/('developer_01' if scope=='developer' else scope+'_01')/'local'/cc.digest(job['video_id'])/str(ix)/'B0/done.json'

def checked_base(scope,job,ix):
    upstream=load(RUN/'b_prompt_recovery_v1/brec_common.py','bw_preserved_base_authority')
    rt,ex,cc,student,old,frames,production=helpers()
    return upstream.checked(base_path(scope,job,ix,cc),base_job(job),ix,'B0',ex)

def local_request(job,ix,arm,identity,ex):
    require(arm=='BW','only one balanced-two-window-alignment arm')
    return dict(kind='local',window=job['windows'][ix]['window'],arm='BW',
        prompt=ex.base_texts(None)['B0'],model=identity,max_input=16384,max_output=256,
        allow_empty=True,context_audit={},sampling_recipe='EXACT_BALANCED_TWO_WINDOWS_NATIVE_FLOOR64',
        video_size={'shortest_edge':4096,'longest_edge':25165824},
        spatial_resolution_tradeoff='ORIGINAL_TOTAL_PIXEL_BUDGET_ACTUAL_GRID_RECORDED')

def done_path(scope,job,ix,arm,cc):
    require(arm=='BW','wrong new arm')
    if job['windows'][ix]['window']==job['windows'][ix]['base_window'] and scope!='rematch':
        return base_path(scope,job,ix,cc)
    if job['windows'][ix]['window']==job['windows'][ix]['base_window'] and scope=='rematch':
        return HERE/'rematch_01/aliases'/cc.digest(job['video_id'])/(str(ix)+'.json')
    return HERE/(scope+'_01')/'local'/cc.digest(job['video_id'])/str(ix)/'BW/done.json'

def checked(path,job,ix,arm,ex):
    if '/rematch_01/aliases/' in str(path):return checked_v14_alias(path,job,ix,ex)
    if '/context_advisory_v1/' in str(path):
        scope='nontest' if '/nontest_01/' in str(path) else 'developer'
        require(str(path)==str(base_path(scope,job,ix,ex.cc)) and
            job['windows'][ix]['window']==job['windows'][ix]['base_window'],'reuse requires original exact window')
        return checked_base(scope,job,ix)
    value=read(path);ex.checked_done(path,local_request(job,ix,arm,value['model_identity'],ex))
    from contracts import parse_segments
    from native_segment_contract import native_segment_ranges
    w=job['windows'][ix]['window']
    require(value['arm']=='BW' and value['window']==w and value['context_audit']=={},'wrong round_alignment window/arm/context')
    parsed,errors,_=parse_segments(value['raw_output'],w['window_duration_sec'],allow_empty=True)
    require(not errors and parsed==value['parsed_segments'],'original unchanged validator differs')
    native=native_segment_ranges(parsed,value['video_identity']['window_source_pts_sec'],w['window_pts_start_sec'],w['window_duration_sec'])
    require([list(x) for x in native]==value['native_frame_realizability']['ranges'],'original native selection differs')
    raw=read(value['raw_receipt'])
    require(raw['raw_output']==value['raw_output'] and raw['overview_adapter_disabled'] is False,'new round_alignment raw identity')
    import math
    require(raw['selected_token_scores'] and all(isinstance(s,(float,int)) and math.isfinite(s) for s in raw['selected_token_scores']),'invalid actual token scores')
    return value

def checked_v14_alias(path,job,ix,ex):
    """Exact old success projection; no new raw response or model call."""
    alias=read(path);source=RUN/'teacher_student_autopilot_v14/rematch_01/temporal.jsonl'
    require(alias['source']==str(source) and sha(source)==alias['source_sha256'] and
        alias['window']==job['windows'][ix]['window']==job['windows'][ix]['base_window'] and
        alias['video_id']==job['video_id'] and alias['index']==ix,'V14 alias exact authority differs')
    row=next(x for x in (read_line(s) for s in source.read_text().splitlines() if s.strip()) if x['video_id']==job['video_id'])
    original=row['windows'][ix];require(ex.cc.digest(original)==alias['original_window_digest'],'old original response changed')
    from contracts import parse_segments
    from native_segment_contract import native_segment_ranges
    w=alias['window'];parsed,errors,_=parse_segments(original['raw_output'],w['window_duration_sec'],allow_empty=True)
    require(not errors and parsed==original['parsed_segments'] and original['output_valid'] and
        original['video_identity']==alias['actual_processor_identity'],'accepted V14 raw/input identity differs')
    ranges=native_segment_ranges(parsed,original['video_identity']['window_source_pts_sec'],w['window_pts_start_sec'],w['window_duration_sec'])
    require([list(x) for x in ranges]==original['native_frame_realizability']['ranges'],'old native selection differs')
    return dict(original,window=w,model_identity=read(HERE/'input_01/resume_manifest.json')['model_identity'],
        original_success_alias=str(path),new_model_calls=0,reused_original_T_temporal_window=True)

def read_line(s):return json.loads(s)

def v14_authority(student,model_identity):
    """Original full accepted bytes and model, before any projection is allowed."""
    source=RUN/'teacher_student_autopilot_v14/rematch_01/temporal.jsonl'
    stage=read(source.parent/'temporal.stage.json');complete=read(RUN/'teacher_student_autopilot_v14/student_01/student_completion.json')
    require(stage['status']=='PASS_TEMPORAL_EXECUTION' and stage['invalid_windows']==0 and stage['videos']==426 and
        stage['windows']==521 and stage['output_sha256']==sha(source) and stage['input_contract']==student.INPUT_CONTRACT and
        stage['selected_adapter_sha256']==complete['selected_adapter_sha256']==model_identity['adapter_sha256'],
        'V14 exact terminal/model/inputs differ')
    rows=[read_line(s) for s in source.read_text().splitlines() if s.strip()]
    require(len(rows)==426 and len({r['video_id'] for r in rows})==426 and sum(len(r['windows']) for r in rows)==521,'V14 full denominator')
    from contracts import parse_segments
    from native_segment_contract import native_segment_ranges
    for row in rows:
        for original in row['windows']:
            duration=original['end_sec']-original['start_sec'];e=original['video_identity']
            parsed,errors,_=parse_segments(original['raw_output'],duration,allow_empty=True)
            require(not errors and parsed==original['parsed_segments'] and original['output_valid'] and
                0<e['input_tokens']<=16384 and not e['truncation'],'old V14 original validator/input bound')
            ranges=native_segment_ranges(parsed,e['window_source_pts_sec'],e['native_processor_identity']['window_start'],duration)
            require([list(x) for x in ranges]==original['native_frame_realizability']['ranges'],'old V14 native selection')
    return source,stage,{r['video_id']:r for r in rows}

def is_changed(part):return part['window']!=part['base_window']

def jobs_for(scope):
    plan=read(HERE/'input_01'/(scope+'_plan.json'))
    return plan,plan['developer_jobs'] if scope=='developer' else plan['jobs']

def proof_aliases(jobs,ex,student):
    source,stage,oldrows=v14_authority(student,read(HERE/'input_01/resume_manifest.json')['model_identity'])
    aliases=[]
    for job in jobs:
        require(len(oldrows[job['video_id']]['windows'])==len(job['windows']),'old V14 window denominator')
        for ix,part in enumerate(job['windows']):
            if is_changed(part):continue
            original=oldrows[job['video_id']]['windows'][ix];w=part['window']
            require(original['start_sec']==part['start_sec'] and original['end_sec']==part['end_sec'] and
                original['video_identity']['source_frame_ids']==w['planned_source_frame_ordinals'] and
                original['video_identity']['actual_pts_sec']==w['planned_actual_pts_sec'] and
                original['video_identity']['native_processor_identity']['window_start']==w['window_pts_start_sec'],
                'unchanged exact V14 request/source/PTS/prompt differs')
            path=done_path('rematch',job,ix,'BW',ex.cc)
            save(path,dict(status='PASS_EXACT_V14_UNCHANGED_REQUEST_AUTHORITY_HANDOFF',source=str(source),source_sha256=sha(source),
                video_id=job['video_id'],index=ix,window=w,original_window_digest=ex.cc.digest(original),
                actual_processor_identity=original['video_identity'],new_model_calls=0,new_optimizer_updates=0,
                original_cost_preserved=True,not_new_raw_or_generation=True))
            checked_v14_alias(path,job,ix,ex);aliases.append(dict(path=str(path),sha256=sha(path)))
    save(HERE/'rematch_01/alias_handoff.json',dict(status='PASS_EXACT_UNCHANGED_V14_REQUESTS',aliases=aliases,
        old_validator_and_processor_receipts_referenced=True,new_decoder_calls=0,new_model_calls=0,
        original_temporal_sha256=sha(source),original_costs_preserved=True))

```


## 补充原文件全文：reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/balanced_two_window_risk_v3/bw_engine.py
字节=6223 SHA256=3c0174fa86d25c19385b3a1a7a87e4bc1a75c260a1c1faa1f23a772e682c3b15

```py
"""One native-nearest-alignment input, original B0 prompt/greedy/validator/model."""
import argparse,time
import bw_common as c
from bw_native import decode_balanced_window,exact_ranges

def encode_balanced(processor,window,rt,student,ex):
    import torch
    from exact_pts import exact_native_pts,verify_native_encoding
    from bw_video import encode,identity
    decoded=decode_balanced_window(window);arr,metadata,plan,evidence=decoded
    with exact_native_pts(processor,plan,metadata['fps']) as native:
        encoded=encode(processor,text=[rt.prompt(processor,ex.base_texts(None)['B0'])],
            videos=[torch.from_numpy(arr).permute(0,3,1,2)],video_metadata=[metadata],video_size=student.VIDEO_SIZE,max_input=16384)
        verify_native_encoding(processor,encoded,native)
    return encoded,dict(**evidence,native_processor_identity=native,**identity(processor,encoded,len(arr)),
        registered_prompt_sha256=ex.cc.digest(ex.base_texts(None)['B0']))

def replay(path,job,ix,ex,rt,student,processor):
    v=c.checked(path,job,ix,'BW',ex);w=job['windows'][ix]['window'];encoded,evidence=encode_balanced(processor,w,rt,student,ex)
    c.require(exact_ranges(v['parsed_segments'],w)==v['native_frame_realizability']['ranges'],'exact rational replay differs')
    c.require(ex.video_signature(encoded)==v['vision_tensor_signature'] and evidence==v['video_identity'],'new independent native/processor identity')
    raw=c.read(v['raw_receipt']);tok=processor.tokenizer
    c.require(tok.decode(raw['output_token_ids'],skip_special_tokens=True,clean_up_tokenization_spaces=False)==raw['raw_output'],'actual output token decoding')
    from constrained_json import make_prefix_constraint,ascii_token_candidates
    import torch
    make_prefix_constraint(tok,0,__import__('fractions').Fraction(w['exact_raw_end'])-__import__('fractions').Fraction(w['exact_raw_start']),candidate_token_ids=ascii_token_candidates(tok),eos_token_ids=tok.eos_token_id,allow_empty=True).assert_complete(torch.tensor(raw['output_token_ids']))
    c.require(int(encoded['input_ids'].shape[1])==v['input_tokens'],'actual CPU token count')
    return dict(path=str(path),done_sha256=c.sha(path),input_tokens=v['input_tokens'],actual_native_processor_raw_validator_equal=True,new_model_calls=0,new_optimizer_updates=0)

def run(scope):
    c.verify();rt,ex,cc,student,old,frames,production=c.helpers()
    plan=c.read(c.HERE/'input_01'/(scope+'_plan.json'));jobs=plan['developer_jobs'] if scope=='developer' else plan['jobs']
    student,old,model,processor,candidates,unused,identity=ex.loaded_model()
    c.require(identity==c.read(c.HERE/'input_01/resume_manifest.json')['model_identity'],'actual original B model differs')
    admitted={(p['scope'],p['video_id'],p['index']):p for p in c.read(c.HERE/'cpu_acceptance.json')['proofs']}
    out=c.HERE/(scope+'_01');c.save(out/'model.json',identity);fresh=reused=recovered=0;recovery={r['path']:r for r in c.read(c.HERE/'engineering_handoff.json')['recovered_successes']};began=time.monotonic()
    for num,job in enumerate(jobs,1):
        for ix,part in enumerate(job['windows']):
            path=c.done_path(scope,job,ix,'BW',cc)
            if part['window']==part['base_window']:
                c.checked(path,job,ix,'BW',ex);reused+=1;continue
            if str(path) in recovery:
                c.require(path.exists() and c.sha(path)==recovery[str(path)]['sha256'],'recovered exact success changed')
                c.checked(path,job,ix,'BW',ex);recovered+=1;continue
            c.require(not path.exists(),'success must not be generated twice')
            w=part['window'];encoded,evidence=encode_balanced(processor,w,rt,student,ex)
            proof=admitted[(scope,job['video_id'],ix)]
            c.require(proof['window']==w and proof['video_identity']==evidence and proof['vision_signature']==ex.video_signature(encoded),'actual GPU request differs from accepted native CPU input')
            from bw_attempt import attempt
            value=attempt(model,processor,encoded,evidence,w,path.parent/'raw.json',allow_empty=True,local_candidates=candidates)
            c.require(exact_ranges(value['parsed_segments'],w)==value['native_frame_realizability']['ranges'],'exact vs pinned float realizability differs')
            value.update(request_sha256=cc.digest(c.local_request(job,ix,'BW',identity,ex)),bound_files={value['raw_receipt']:c.sha(value['raw_receipt'])},
                arm='BW',window=w,model_identity=identity,context_audit={},vision_tensor_signature=ex.video_signature(encoded))
            c.save(path,value);fresh+=1;del encoded
            if not (c.HERE/'first_real_acceptance.json').exists():
                import subprocess,os
                env=dict(os.environ,CUDA_VISIBLE_DEVICES='')
                with (c.HERE/'first_replay.cpu.log').open('x') as log:
                    result=subprocess.run([c.PY,'-B',str(c.HERE/'bw_first_replay.py'),scope,job['video_id'],str(ix)],
                        cwd=c.RUN,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
                c.require(result.returncode==0 and c.read(c.HERE/'first_real_acceptance.json')['separate_CPU_process'],'independent first CPU replay failed')
        c.state('RUNNING_'+scope.upper()+'_BALANCED_TWO_WINDOW',records_completed=num,total_records=len(jobs),fresh_model_calls=fresh,
            reused_exact_original_calls=reused,recovered_exact_prior_model_calls=recovered,new_overview_calls=0,wall_seconds=time.monotonic()-began)
    total={'nontest':8,'developer':112,'rematch':521}[scope]
    c.require(fresh+reused+recovered==total and fresh+recovered==sum(p['window']!=p['base_window'] for j in jobs for p in j['windows']),'actual fresh+exact reused denominator')
    c.save(out/(scope+'.completion.json'),dict(status='PASS_ALL_BALANCED_TWO_WINDOW_ATTEMPTS',utc=c.utc(),records=len(jobs),fresh_model_calls=fresh,
        model_identity=identity,reused_exact_original_calls=reused,recovered_exact_prior_model_calls=recovered,total_windows=total,new_optimizer_updates=0,new_32B_calls=0,new_overview_calls=0))


if __name__=='__main__':
    import sys
    run(sys.argv[1])

```


## 补充原文件全文：reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/context_advisory_v1/experiment.py
字节=18147 SHA256=da4cb613eded66626f271577e255d3b6767fc6a091d3b968d5f7343f986bfc1e

```py
"""One frozen advisory recipe: exact native CPU preflight and owned GPU jobs.

No grading data is used by selection or inference. Reference-set agreement is
computed separately after the four complete developer arms are committed.
"""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
import time
import traceback

import context_contract as cc
import runtime as rt

HERE, RUN = rt.HERE, rt.RUN


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def progress(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
    print(json.dumps(value), flush=True)


def verify():
    lock = read(HERE / "source_lock.json")
    for path, wanted in lock["files"].items():
        cc.require(sha(path) == wanted, "registered dependency changed: " + path)
    return lock


def scope_plan(scope):
    student, old, frames, production = rt.bind_helpers()
    ref, manifest, clocks = old.inputs(scope)
    jobs, sources = [], {}
    source_clock = rt.load(HERE / "prepare.py", "cad_prepare").source_clock
    for item in manifest["records"]:
        clock = clocks[item["video_id"]]
        a = clock["arrays"]
        tick = Fraction(a["raw_time_base"])
        points = [float(x * tick) for x in a["native_pts_ticks"]]
        key = item["source_sha256"]
        # Independently scan the actual terminal packet. Do not infer an
        # overview endpoint from nominal CFR FPS or frame count.
        physical = source_clock(item, manifest["allowed_source_roots"])
        cc.require(physical["pts"] == points, "current scope registry differs from native full-source PTS")
        sources[key] = physical
        windows = []
        for j, (start, end) in enumerate(frames.window_schedule(item, manifest["kind"], clock)):
            raw_start, raw_end = production.raw_window_bounds(a, start, end)
            w = student.window_from_pts(item["source_path"], key, points, raw_start, raw_end,
                item["video_id"] + ":CAD:" + str(j), width=item["width"], height=item["height"])
            w["window_duration_sec"] = end - start
            windows.append({"start_sec": start, "end_sec": end, "window": w,
                "clock_record_sha256": clock["clock_record_sha256"], "clock_branch": clock["branch"],
                "raw_source_pts_origin_sec": float(a["raw_first_pts_ticks"] * tick)})
        jobs.append(dict(video_id=item["video_id"], source_key=key, source_group=item["source_sha256"],
            metadata=item, windows=windows))
        print(json.dumps({"stage": "SCOPE_NATIVE_CPU_SCAN", "scope": scope, "sources": len(sources)}), flush=True)
    mapping = cc.deterministic_derangement(list(sources), {k: c["duration_sec"] for k, c in sources.items()}) if scope == "nontest" else {}
    value = dict(scope=scope, jobs=jobs, sources=sources, shuffle_source_mapping=mapping, input_ref=ref,
        overview_source_files=len(sources), records=len(jobs), windows=sum(len(x["windows"]) for x in jobs),
        no_model_calls=True)
    rt.raw_write(HERE / "input_01" / (scope + "_plan.json"), value)
    return value


def overview_window(source, key):
    return cc.overview_plan(source["source_path"], key, source["pts"], source["raw_end_exclusive_sec"],
        key + ":SOURCE_OVERVIEW", width=source["width"], height=source["height"],
        observation_authority="EXACT_PERMITTED_SOURCE_FILE_NO_CROSS_FILE_UNION")


def source_tables(plan):
    return {k: read(p) for k, p in plan["source_clocks"].items()} if "source_clocks" in plan else plan["sources"]


def base_texts(old):
    from contracts import EMPTY_PROMPT
    tc = rt.load(RUN / "baseline_a_pts_v1/vendor/temporal_common.py", "cad_prompt_only")
    return {"B1": tc.PROMPT, "B0": EMPTY_PROMPT}


def arm_text(arm, window, table, donor_table, texts):
    if arm in texts:
        return texts[arm], {}
    if arm == "N":
        context = json.dumps({"source_context_provided": False,
            "missing_context_does_not_mean_no_events": True}, separators=(",", ":"))
        audit = {"context_not_provided": True}
    else:
        selected = table if arm == "R" else donor_table
        count = len(selected["overview_window"]["planned_actual_pts_sec"])
        own_pts = table["overview_window"]["planned_actual_pts_sec"]
        value = selected["events"]
        if count != len(own_pts):
            # Same normalized rank map for all legal short-source denominators.
            mapped = {"events": [dict(e, first=(e["first"] * (len(own_pts) - 1) // max(count - 1, 1)),
                last=(e["last"] * (len(own_pts) - 1) // max(count - 1, 1))) for e in value["events"]]}
        else:
            mapped = value
        context = cc.render_event_table(mapped, own_pts, window["window_pts_start_sec"], window["window_pts_end_exclusive_sec"])
        audit = {"context_source_sha256": selected["overview_window"]["source_sha256"],
            "recipient_source_sha256": window["source_sha256"], "donor_raw_receipt": selected["raw_receipt"],
            "deliberately_wrong_context_diagnostic_only": arm == "X", "not_recipient_evidence": arm == "X"}
    return texts["B0"] + rt.ADVISORY_TEXT + context, audit


def tensor_sha(value):
    return hashlib.sha256(value.detach().cpu().contiguous().view(__import__('torch').uint8).numpy().tobytes()).hexdigest()


def video_signature(encoded):
    return {k: {"shape": list(v.shape), "dtype": str(v.dtype), "sha256": tensor_sha(v)}
        for k, v in encoded.items() if k in ("pixel_values_videos", "video_grid_thw")}


def cpu_preflight(draft=False):
    if not draft:
        verify()
    student, old, frames, production = rt.bind_helpers()
    from transformers import AutoProcessor
    from constrained_json import ascii_token_candidates
    checks = rt.load(HERE / "tests.py", "cad_tests").test_contracts()
    cfg = old.read(RUN / "b_score_aligned_package_v4/config.json")
    processor = AutoProcessor.from_pretrained(cfg["model_dir"], local_files_only=True, min_pixels=131072, max_pixels=131072)
    candidates = rt.overview_candidates(processor.tokenizer)
    # Check the actual fixed tokenizer's whole-context ASCII additivity on all
    # candidates in several syntax/description contexts, not synthetic mocks.
    tok = processor.tokenizer
    for prefix in ('', '{"events":[{"first":', '{"events":[{"first":0,"last":0,"description":"'):
        ids = tok.encode(prefix, add_special_tokens=False)
        actual = tok.decode(ids, skip_special_tokens=False, clean_up_tokenization_spaces=False)
        for token, piece in candidates:
            cc.require(tok.decode(ids + [token], skip_special_tokens=False, clean_up_tokenization_spaces=False) == actual + piece,
                "actual ASCII candidate is context-dependent")
    plan = read(HERE / "input_01/nontest_plan.json")
    texts, proofs = base_texts(old), []
    import torch
    for job in plan["jobs"]:
        window = job["windows"][0]["window"]
        decoded = student.decode_window(window)
        ov = overview_window(plan["sources"][job["source_key"]], job["source_key"])
        # Test real overview decode and processor without any GPU model call.
        over_decoded = student.decode_window(ov)
        overview_encoded, ov_evidence = rt.encode_decoded(processor, over_decoded, rt.OVERVIEW_TEXT)
        dummy = {"events": {"events": [{"first": 0, "last": 0, "description": "visible activity"}]},
            "overview_window": ov, "raw_receipt": "CPU_CONTRACT_ONLY"}
        common = None
        for arm in ("B1", "B0", "N", "R", "X"):
            text, audit = arm_text(arm, window, dummy, dummy, texts)
            encoded, identity = rt.encode_decoded(processor, decoded, text)
            signature = video_signature(encoded)
            if common is None:
                common = signature
            cc.require(signature == common, "advisory changed local video tensor/grid")
            if arm == "B0":
                original, original_identity = student.production_encode(processor, window)
                cc.require(set(original) == set(encoded) and all(torch.equal(original[k], encoded[k]) for k in encoded),
                    "new B0 encoding differs from actual V14 production function")
                cc.require(original_identity["frame_pixel_sha256"] == identity["frame_pixel_sha256"], "B0 pixel identity")
                del original
            del encoded
        proofs.append({"video_id": job["video_id"], "all_five_vision_tensors_equal": True,
            "B0_all_encoded_tensors_equal_actual_V14": True, "pixel_sha256": decoded[3]["frame_pixel_sha256"],
            "overview_pixels": ov_evidence["frame_pixel_sha256"], "overview_input_tokens": int(overview_encoded["input_ids"].shape[1])})
        del overview_encoded, over_decoded, decoded
        print(json.dumps({"stage": "CPU_REAL_PROCESSOR_NONTEST", "videos": len(proofs), "total": 8}), flush=True)
    cc.require(len(proofs) == 8, "NONTEST8 CPU denominator")
    rt.raw_write(HERE / ("draft_preflight.json" if draft else "preflight.json"), dict(checks, status="PASS_REAL_CPU_NATIVE_PROCESSOR_CONTRACTS_NO_GPU_CALLS",
        tokenizer_candidate_count=len(candidates), tokenizer_ascii_contexts=3, non_test_proofs=proofs,
        source_lock_sha256=None if draft else sha(HERE / "source_lock.json")))


def loaded_model():
    student, old, _, production = rt.bind_helpers()
    from sft_contract import verify_live_gpu_reservation
    from engine import load_model
    from verify_saved_smoke import canonical_frozen_hash
    from constrained_json import ascii_token_candidates
    import torch
    verify_live_gpu_reservation()
    cfg = read(RUN / "b_score_aligned_package_v4/config.json")
    cc.require(sha(Path(cfg["b_adapter"]) / "adapter_model.safetensors") == cfg["b_adapter_sha256"], "B adapter file changed")
    model, processor, count = load_model(cfg, adapter=True)
    base_hash = canonical_frozen_hash(model, torch)
    production.check_base_hash(base_hash, cfg)
    from safetensors.torch import load_file
    saved = load_file(str(Path(cfg["b_adapter"]) / "adapter_model.safetensors"), device="cpu")
    actual = {name.replace("base_model.model.", "", 1).replace(".default", ""): p.detach().cpu() for name, p in model.named_parameters() if "lora_" in name}
    # Peft save keys retain the base_model.model prefix. Match only its declared
    # canonical key transformation, not fuzzy suffixes.
    expected = {name.replace("base_model.model.", "", 1): p for name, p in saved.items()}
    cc.require(len(actual) == len(expected) == 288 and set(actual) == set(expected) and
        all(torch.equal(actual[name], expected[name]) for name in actual), "loaded 288 adapter tensors differ from B saved bytes")
    cc.require(not model.training and not any(p.requires_grad for p in model.parameters()), "inference model not frozen/eval")
    identity = dict(base_hash=base_hash, logical_parameters=count, adapter_sha256=cfg["b_adapter_sha256"],
        adapter_saved_tensor_equality=288, new_optimizer_updates=0)
    return student, old, model, processor, ascii_token_candidates(processor.tokenizer), rt.overview_candidates(processor.tokenizer), identity


def checked_done(path, request):
    value = read(path)
    cc.require(value["request_sha256"] == cc.digest(request), "attempt cache request differs")
    for p, wanted in value["bound_files"].items():
        cc.require(sha(p) == wanted, "completed attempt byte identity changed")
    cc.require(value.get("output_valid") is True, "attempt cache was invalid")
    return value


def run(stage):
    verify()
    cc.require(read(HERE / "preflight.json")["status"] == "PASS_REAL_CPU_NATIVE_PROCESSOR_CONTRACTS_NO_GPU_CALLS", "preflight missing")
    if stage in ("nontest", "rematch"):
        plan = read(HERE / "input_01" / (stage + "_plan.json"))
        jobs = plan["jobs"]
        out = HERE / (stage + "_01")
        arms = ("B1", "B0", "N", "R", "X") if stage == "nontest" else ("R",)
    else:
        plan = read(HERE / "input_01/developer_plan.json")
        jobs = plan["developer_jobs"]
        if stage == "pilot":
            jobs = [x for x in jobs if x["video_id"] in plan["pilot_video_ids"]]
        out = HERE / "developer_01"
        arms = ("B1", "B0", "N", "R", "X") if stage == "pilot" else ("B0", "N", "R", "X")
    out.mkdir(exist_ok=True)
    started = time.monotonic()
    student, old, model, processor, local_candidates, event_candidates, model_identity = loaded_model()
    rt.raw_write(out / (stage + ".model.json"), model_identity)
    sources = source_tables(plan)
    needed = {j["source_key"] for j in jobs}
    if "X" in arms:
        needed |= {plan["shuffle_source_mapping"][j["source_key"]] for j in jobs}
    tables, fresh_overview, reused_overview = {}, 0, 0
    for key in sorted(needed):
        w = overview_window(sources[key], key)
        request = {"kind": "overview", "window": w, "prompt": rt.OVERVIEW_TEXT, "model": model_identity,
            "max_input": 16384, "max_output": 1280, "adapter_disabled": True}
        folder = out / "overview" / key
        done = folder / "done.json"
        if done.exists():
            table = checked_done(done, request); reused_overview += 1
        else:
            encoded, evidence = rt.encode_decoded(processor, student.decode_window(w), rt.OVERVIEW_TEXT)
            raw = folder / "raw.json"
            table = rt.attempt(model, processor, encoded, evidence, w, raw, overview=True, event_candidates=event_candidates)
            table.update(overview_window=w, request_sha256=cc.digest(request), model_identity=model_identity,
                bound_files={str(raw): sha(raw)}, overview_input_tokens=int(encoded["input_ids"].shape[1]))
            rt.raw_write(done, table); fresh_overview += 1
            del encoded
        cc.validate_overview(table["raw_output"], w["planned_actual_pts_sec"])
        tables[key] = table
        progress(out / "progress.json", {"stage": stage + "_OVERVIEW", "completed": len(tables), "total": len(needed),
            "fresh_model_calls": fresh_overview, "reused_calls": reused_overview, "wall_seconds": time.monotonic() - started})
    texts = base_texts(old)
    fresh, reused = 0, 0
    for num, job in enumerate(jobs, 1):
        table = tables[job["source_key"]]
        donor = tables[plan["shuffle_source_mapping"][job["source_key"]]] if "X" in arms else table
        for ix, part in enumerate(job["windows"]):
            w = part["window"]
            decoded = student.decode_window(w)
            vision_signature = None
            for arm in arms:
                text, audit = arm_text(arm, w, table, donor, texts)
                request = {"kind": "local", "window": w, "arm": arm, "prompt": text, "model": model_identity,
                    "max_input": 16384, "max_output": 256, "allow_empty": arm != "B1", "context_audit": audit}
                folder = out / "local" / cc.digest(job["video_id"]) / str(ix) / arm
                done = folder / "done.json"
                if done.exists():
                    value = checked_done(done, request); reused += 1
                else:
                    encoded, evidence = rt.encode_decoded(processor, decoded, text)
                    sig = video_signature(encoded)
                    if vision_signature is None:
                        vision_signature = sig
                    cc.require(sig == vision_signature, "arm changed local vision tensor")
                    raw = folder / "raw.json"
                    value = rt.attempt(model, processor, encoded, evidence, w, raw, allow_empty=arm != "B1", local_candidates=local_candidates)
                    value.update(request_sha256=cc.digest(request), bound_files={str(raw): sha(raw)}, arm=arm,
                        window=w, model_identity=model_identity, context_audit=audit, vision_tensor_signature=sig)
                    rt.raw_write(done, value); fresh += 1
                    del encoded
                # Validate even exactly reused attempts against current original validator.
                from contracts import parse_segments
                parsed, errors, _ = parse_segments(value["raw_output"], w["window_duration_sec"], allow_empty=arm != "B1")
                cc.require(not errors and parsed == value["parsed_segments"], "reused original validator differs")
                if vision_signature is None:
                    vision_signature = value["vision_tensor_signature"]
                cc.require(value["vision_tensor_signature"] == vision_signature, "reused arm video identity differs")
            del decoded
        progress(out / "progress.json", {"stage": stage + "_LOCAL", "videos": num, "total": len(jobs),
            "fresh_local_calls": fresh, "reused_local_calls": reused, "fresh_overviews": fresh_overview,
            "reused_overviews": reused_overview, "wall_seconds": time.monotonic() - started})
    rt.raw_write(out / (stage + ".completion.json"), {"status": "PASS_ALL_REGISTERED_ADVISORY_ATTEMPTS",
        "stage": stage, "records": len(jobs), "source_files": len(needed), "arms": list(arms),
        "fresh_local_calls": fresh, "reused_local_calls": reused, "fresh_overview_calls": fresh_overview,
        "reused_overview_calls": reused_overview, "model_identity": model_identity, "wall_seconds": time.monotonic() - started})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("prepare-nontest", "prepare-rematch", "draft-preflight", "preflight", "nontest", "pilot", "full", "rematch"))
    args = parser.parse_args()
    if args.stage.startswith("prepare-"):
        scope_plan(args.stage.split("-", 1)[1])
    elif args.stage in ("preflight", "draft-preflight"):
        cpu_preflight(draft=args.stage == "draft-preflight")
    else:
        run(args.stage)

```


## 补充原文件全文：reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/context_advisory_v1/runtime.py
字节=10161 SHA256=73f014e20034e0c61e9d57fe927ec7c69392f2d5f5e7a2f3f9f06ca6efa614b9

```py
"""C-advisory inference, binding frozen V14 native decoder and B adapter.

All output attempts first receive an exclusive raw receipt. Validation never
overwrites an attempt, fills an event, repairs a boundary or converts failure
to empty. Overview inference disables B's adapter; local inference enables it.
"""
import contextlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
RUN = HERE.parent
sys.path.insert(0, str(HERE))
import context_contract as cc

OVERVIEW_TEXT = (
    "Describe visible activities in this sparse overview of one source video. "
    "This is factual context, not a highlight selection. Number the actual supplied "
    "video frames from 0 in their displayed order. Return ONLY canonical JSON "
    '{"events":[{"first":0,"last":1,"description":"brief visible activity"}]}. '
    "Use 0 to 8 events. Each first and last is an actual supplied frame number, "
    "0 <= first <= last < the supplied frame count. Use concise English descriptions "
    "of at most 80 characters. Include only activities directly visible in those "
    'frames; do not infer unseen actions or label highlights. If none can be described, '
    'return {"events":[]}. Sparse frames can miss short events.'
)
ADVISORY_TEXT = (
    "\nAdditional sparse source-video context follows. It describes sampled visible "
    "activities, not highlight labels. It can be incomplete or irrelevant. Judge "
    "the current local video visually; a missing event is not a negative example. "
    "Do not let this context exclude any visible local event. Source times in the "
    "table are not clip-local output boundaries. Output boundaries still follow "
    "the original clip-local rules above.\nSOURCE_CONTEXT_JSON:\n"
)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def bind_helpers():
    student = load(RUN / "teacher_student_autopilot_v14/train_student.py", "cad_v14_student")
    student.helper_paths(RUN)
    # production_t imports train_student by its public name.
    sys.modules["train_student"] = student
    production = load(RUN / "teacher_student_autopilot_v14/production_t.py", "cad_v14_production")
    student, common, frame_contract, source = production.helpers()
    return student, common, frame_contract, production


def raw_write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, allow_nan=False, indent=2)
        stream.write("\n")


def prompt(processor, text):
    value = processor.apply_chat_template([{"role": "user", "content": [{"type": "text", "text": text}]}],
        tokenize=False, add_generation_prompt=True, enable_thinking=False)
    return value.replace("<|im_start|>user\n", "<|im_start|>user\n<|vision_start|><|video_pad|><|vision_end|>", 1)


def encode_decoded(processor, decoded, text):
    import torch
    from video_contract import encode, identity
    from exact_pts import exact_native_pts, verify_native_encoding
    student = sys.modules["train_student"]
    arr, metadata, plan, evidence = decoded
    with exact_native_pts(processor, plan, metadata["fps"]) as native:
        encoded = encode(processor, text=[prompt(processor, text)],
            videos=[torch.from_numpy(arr).permute(0, 3, 1, 2)], video_metadata=[metadata],
            video_size=student.VIDEO_SIZE, max_input=16384)
        verify_native_encoding(processor, encoded, native)
    return encoded, dict(**evidence, native_processor_identity=native,
        **identity(processor, encoded, len(arr)), registered_prompt_sha256=cc.digest(text))


def overview_candidates(tokenizer):
    alphabet = cc.DESCRIPTION_CHARS | frozenset('{}[]"0123456789,')
    # The same documented ASCII advisory prefilter used by the local grammar.
    result = []
    for token in sorted(set(tokenizer.get_vocab().values())):
        piece = tokenizer.decode([token], skip_special_tokens=False, clean_up_tokenization_spaces=False)
        if piece and piece.isascii() and set(piece) <= alphabet:
            result.append((token, piece))
    return tuple(result)


class OverviewPrefix:
    def __init__(self, tokenizer, prompt_length, frames, candidates, eos):
        self.tokenizer, self.prompt_length = tokenizer, prompt_length
        self.grammar = cc.OverviewGrammar(frames)
        self.eos = [eos] if isinstance(eos, int) else list(eos)
        self.candidates = [(i, p) for i, p in candidates if i not in self.eos]
        self.cache = {}
        self.pieces = dict(self.candidates)
        self.stats = {"calls": 0, "candidate_count": len(self.candidates), "full_context_decodes": 0}

    def decode(self, ids):
        self.stats["full_context_decodes"] += 1
        return self.tokenizer.decode(ids, skip_special_tokens=False, clean_up_tokenization_spaces=False)

    def __call__(self, batch, input_ids):
        ids = tuple(input_ids.tolist()[self.prompt_length:])
        self.stats["calls"] += 1
        if ids in self.cache:
            return self.cache[ids]
        text = self.decode(list(ids))
        cc.require(text == "".join(self.pieces[i] for i in ids),
            "actual full-context ASCII token decoding not additive; STOP")
        if self.grammar.complete(text):
            allowed = self.eos
        else:
            cc.require(self.grammar.valid_prefix(text), "invalid overview prefix; no recovery")
            self.grammar.prepare(text)
            allowed = []
            for token, piece in self.candidates:
                # Incremental ASCII automaton; the actual selected HF prefix is
                # whole-context decoded and checked for additivity on every call.
                if self.grammar.can_extend(piece):
                    allowed.append(token)
        cc.require(allowed, "overview generation dead end; no output repair")
        self.cache[ids] = allowed
        return allowed


def attempt(model, processor, encoded, evidence, window, raw_path, *, overview=False,
            allow_empty=True, local_candidates=None, event_candidates=None):
    import torch
    from constrained_json import make_prefix_constraint
    from contracts import parse_segments
    from native_segment_contract import native_segment_ranges
    prefix = int(encoded["input_ids"].shape[1])
    eos = model.generation_config.eos_token_id
    constraint = (OverviewPrefix(processor.tokenizer, prefix,
        len(window["planned_actual_pts_sec"]), event_candidates, eos) if overview else
        make_prefix_constraint(processor.tokenizer, prefix, window["window_duration_sec"],
            candidate_token_ids=local_candidates, eos_token_ids=eos, allow_empty=allow_empty))
    started = time.monotonic()
    try:
        with (model.disable_adapter() if overview else contextlib.nullcontext()), torch.inference_mode():
            generated = model.generate(**encoded.to("cuda"), do_sample=False,
                max_new_tokens=1280 if overview else 256, prefix_allowed_tokens_fn=constraint,
                return_dict_in_generate=True, output_scores=True)
        torch.cuda.synchronize()
        ids = generated.sequences[0, prefix:]
        raw = processor.tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
        selected_scores = [float(score[0, int(token)]) for score, token in zip(generated.scores, ids)]
        # Save the exact model answer before ANY completeness or validity check.
        receipt = {"raw_output": raw, "output_token_ids": ids.tolist(),
            "selected_token_scores": [x if math.isfinite(x) else str(x) for x in selected_scores], "input_tokens": prefix,
            "actual_model_call": True, "overview_adapter_disabled": overview,
            "window": window, "video_identity": evidence,
            "generation_seconds": time.monotonic() - started, "constraint_stats": constraint.stats}
        raw_write(raw_path, receipt)
        cc.require(selected_scores and all(math.isfinite(x) for x in selected_scores), "nonfinite actual selected token scores")
        if overview:
            value = cc.validate_overview(raw, window["planned_actual_pts_sec"])
            result = {"status": "LEGAL_EMPTY_EVENTS" if not value["events"] else "MODEL_OK_EVENTS",
                "output_valid": True, "events": value, "sparse_not_complete_observation": True,
                "descriptions_are_model_claims_not_semantic_truth": True}
        else:
            constraint.assert_complete(ids)
            segments, errors, warnings = parse_segments(raw, window["window_duration_sec"], allow_empty=allow_empty)
            cc.require(segments is not None and not errors, "local parse rejected: " + repr(errors))
            ranges = native_segment_ranges(segments, evidence["window_source_pts_sec"],
                window["window_pts_start_sec"], window["window_duration_sec"])
            result = {"status": "MODEL_OK" if segments else "LEGAL_EMPTY", "output_valid": True,
                "parsed_segments": segments, "parse_errors": errors, "parse_warnings": warnings,
                "native_frame_realizability": {"status": "PASS_ACTUAL_SOURCE_FRAME_REALIZABILITY", "ranges": ranges,
                    "not_limited_to_64_teacher_samples": True}}
        result.update(raw_output=raw, raw_receipt=str(raw_path), video_identity=evidence,
            constraint_stats=constraint.stats, generation_time_constraint=True,
            input_tokens=prefix, output_tokens=len(ids), generation_seconds=time.monotonic() - started)
        return result
    except Exception as error:
        failure = {"status": "STOP_ACTUAL_GENERATION_OR_VALIDATION_FAILURE", "failure_converted_to_empty": False,
            "error": type(error).__name__ + ": " + str(error), "traceback": traceback.format_exc(),
            "raw_receipt_exists": Path(raw_path).exists()}
        raw_write(str(raw_path) + ".failure.json", failure)
        raise

```


