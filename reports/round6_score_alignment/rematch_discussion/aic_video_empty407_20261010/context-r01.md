# EMPTY407 第二轮完整交叉审查 r01

连续任务AIC-VIDEO-REMATCH-NEXT-20261005。普通第一轮四席公开答复均完成；Gemini原r00截断答复保留，补传r00b完整四卷后修订答复也保留。不是多数票证明质量。原所有事实/源码/历史Pro与异议全文随后继承。本版末标END_EMPTY407_R01。Pro仍5/8，剩3，本轮不消耗。

## 主控第一轮后的修订、接受与拒绝
接受：图片评分架构的阈值/校准与事件目标存在明显风险；撤回237步新包质量推荐，保留失败原件。主控过去放行门只比较弱基座及已见TVSum代理，非测试8全空也没触发语义审查，不能把完整工程验收当业务可用性。SHA/PTS/像素保护仍必要，但不能代替高光质量。
接受：优先原37.66对应B8B native管线，标注原生事件并验证学生可见证据、完整窗口和边界；部分KEEP+未知区域不能编成完整segments，因为停止输出会隐含遗漏监督。未知不转负例；同教师一致不是金标；独立盲审先看媒体/规则后看答案。
纠正关键版本错误：Sol把旧历史1..5提示当成当前37.66语法，事实不成立。当前bw_common.helpers -> context_advisory.runtime.bind_helpers -> V14.helper_paths明确绑定V14 precision_helpers/contracts.py；experiment.base_texts()['B0']=该模块EMPTY_PROMPT，内容return between 0 and 5 intervals且允许[]、不把不确定当无高光。bw_engine/local_request实际allow_empty=True。下附完整必要代码。旧1..5提示属于历史B1/原CFR，保留不能混作当前B0。不能仅训练正窗以修一个不存在的表达限制。
纠正主控口头分母笔误：新9dev actual score/gold共有1351点，不是1451。new范围24..53，gold21..87，>=49 new48/1351，gold293/1351；4/9全空，5非空。Tibo的逆序反例应复核：sTEELN-vY30 grid5 gold87/pred48 vs grid32 gold27/pred50；保序标量校准无法修这种逆序，且TVSum重要性仍非AIC金标。Tibo所报5404是4臂×1351。
拒绝：Gemini首答100%非空/强制选帧比例/静态必拒/I-frame即切镜先验；补答已撤回这些。切镜只触发审查，连续叙事允许跨镜；模型新版本不应事后改写原标签端点制造通过。训练早期有限loss也可正常波动，不能把任意震荡都说成失败。Gemini“单尖峰M_spike可过完整门”只检验stage2额外proxyF，忽略stage2还要求研究Spearman/top15多数源改善，因此不是完整门反例；门仍不足以证明AIC质量，这点成立。
拒绝：Grok要求新图片评分器与B native同grammar作公平比较；不同任务的诊断必须各自原prompt/grammar，只统一媒体源/参考域并比较最终选择，不能改B到图片prompt。B续训candidate0/1则确实必须同原native输入和生成协议。旧optimizer状态未核，不要求凭空恢复；继承B权重、明确新建optimizer不等于恢复旧优化轨迹。
保留异议：仅有6–12个来源组的银标门不能证明官方涨分。此前旧32B弱标签15步没有胜过B，不能反复同配方；新计划必须购买不同的实际观察及目标一致证据。不预设降阈值一定无价值，也不把它开成第二条426路线。

## 主控建议唯一有界工作包，供严格批判
先静态核训练mask/实际协议、来源与历史曝光，不重复已有成功生成。首次小试4窗，流程可审计后扩到最多12 source_group×2个事前确定非重叠<=30s窗口，共24窗：6训练/3流程开发/3锁定确认。已有TVSum48源优先，先建立历史曝光关系再定组；不假称确认未见，若都是旧暴露组则明确锁定开发性质和弱证据。来源不够缩小并登记，不擅自下载。
agy终端为提案教师，原生MP4提供全局观察，再显式送原B实际64帧原生RGB/PTS索引(可分批)，每批读取回执与逐帧可见事实可审查；边界补供原生短序列。所有声明和实际工具供给分开，不用teacher自报证明完整观测。第二观察由主控直接查看相同证据且先独立盲记，再对比教师；当前没有人工金标，不冒称人工审查。全窗SFT资格究竟能否在64帧完整供给+原生MP4稀疏工具下成立需重点裁决：不能把所有采样帧已读等同整个视频逐帧已观察，也不能把稀疏之间每一小段一律UNKNOWN而把合法有限观察学习永久阻塞。请给科学上诚实可操作的银标资格，或明确否定本轮全窗续训。
候选事件事实/高光理由/内部与内外边界证据、原生ordinal/PTS、可观察性、未解决范围都保留。超过5事件/不确定边界不擅自合并凑grammar。合法无高光只有足够全窗证据才可[]；部分正例不得作为全部真值。
最多24提案+24盲审记录+8新边界补查=56项观察任务(主控审查不是闭源调用)，已有6片原成功raw只引用不重跑。前瞻工程上限非统计保证。至少8合格训练窗/4组；完整参考先冻结再揭示candidate0/1。主要source等权原生时间F1，事件匹配/边界误差/正事件漏空/明确NO误选另报；UNKNOWN分母全列。小样本不能据此宣称官网涨分。
标签达标才一次B权重初始化native SFT；初拟原r16/alpha32/qkvo，基座/视觉冻结，lr1e-5，有效batch4，至多2epoch/8真实更新(不凑数、不扫超参/挑确认checkpoint)，新optimizer明确登记。逐样本assistant-only CE归一公式须冻结，不能沿用评分训练器假称native视频训练。确认候选0/1只差adapter，使用相同源/window/floor64/精确PTS/processor/像素/EMPTY_PROMPT/0..5/greedy/native映射/空间场。新权重固定终点，只一次确认。
建议前瞻风险门：开发macroΔtimeF1>0；锁定确认macro>0且至少2/3源不负，无正事件漏空增加、明确NO误选时长增加或可确认无关内容边界外溢。要求precision/recall/最坏源退化完整报告，由Pro选择数值门或否定其证据力。不用teacher一致或选帧密度作真值。若必须更大确认才科学充分，请区分统计证明和用户明确接受的有限实验风险。
本阶段上限标注24窗/有界补查，native训练1200计费秒、非测试对照2400计费秒建议；实际资源动态准入，CPU准备不计作模型0成本、资源加载退出时间真实记账。426新推理预算须实测非测试后估算、保留拆卸余量，不能照搬Tibo2400秒(原V14仅时间5430.028秒)。已有成功candidate0精确身份可复用，不重复模型/CPU验收。任何工程/标签/质量门失败STOP这版，保留37.66，不事后重选样本配方。全部通过才单次完整426风险ZIP，官网分UNKNOWN，用户手工提交；不自动生产替换。

请交叉批判全部原文与主控改案，直接回答：当前B0版本、完整监督可观察性资格、银标审查的真实能力与来源/曝光隔离、主控缩减预算能否支撑一次可信小试、质量指标具体分母/未知处理、若拒绝训练是否有仍可购买新信息的可执行下一步。不得把“要求完整观察”无限升级为无可达到的金标证明，但不能虚构资格。仅讨论，不联网/实验/训练；下一步才研究项目Pro集中裁决。
# AIC 视频复赛：407个空视频后的重新决策

任务ID AIC-VIDEO-REMATCH-NEXT-20261005；子议题 EMPTY407-20261010；r00b完整业务包；数值JSON仅压缩空白，所有值和代码完整保留。
这份包提供本次决策所需的事实、原报告、必要代码和前次Pro裁决。不是把整个仓库或无关用户对话外传。每个原文件都有本地主控实际读取的字节与SHA；外部模型不应把声明SHA说成自己已独立验签。末尾标志END_EMPTY407_R00B。

## 用户原始要求及持续授权
用户：“你妹的407个视频是空是什么鬼，你赶紧用一锅炖那个技能去讨论讨论下一步怎么办吧，可以继续微调我们最佳包，也可以继续让强闭源模型去标注很好的数据集，你自己看着弄”。此前要求自主调研、讨论、检查修复并迭代到质量可用ZIP，优先终端调用agy做高光视频标注。用户说明官方允许闭源辅助标注，不再重复询问标注许可。今天已明确允许Gemini 3.8 Flash网页最高档（实际UI高点/超级详尽）参加本次讨论。
讨论后的训练和标注在用户授权内；公开发布、官网提交、生产模型替换和新大流量下载/传输没有新增授权。原B最佳包、未提交工作、原raw、失败、STOP、费用全部保留。禁止读100confirm、手看复赛内容调参、按复赛输出选择阈值或补TopK。复赛407空是公开报告的失败症状，可评估风险；不据此反推测试配方。

## 当前关键事实与局限
1. 历史最佳原B8B+双窗均衡已由用户反馈37.66/DONE，426记录102112选中帧，ZIP306167字节，SHA07730c9e02e68d1a1ce54e7ef5a8aa616346cf8f2f8d78426ed36bc3eb481496。未独立登录官网验证。双窗改变不是新训练，原B adapter SHA8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23保留。
2. 新237步独立TVSum图片评分LoRA不是从原B续训。39train源314行、9个已见dev源89行；16有序图片/row、2秒取中点、20人均值乘20。输出语法20..100，但importance标签是TVSum相对重要性，不是AIC语义高光边界。阈值49来自train人工标签80分位，与模型输出分布校准未获证明，2秒整格扩展是假设。
3. 新实验426仅3189选中帧，407空、19非空；非测试8全部空。510真实生成与实际4439张采样图片独立CPU回放都通过，工程11strict通过；这不证明质量。新ZIP12384字节，SHA01969ab4c8221b279dfa58fe1c9f3c5c47cd01fe8cd7dea312bde93cdb3d6325，官网分UNKNOWN，未提交。主控撤回推荐它作为质量可用包，保留失败产物。
4. 四组89条开发比较中new Spearman .522329/base .043629，但native proxyF改善95CI[-.001096,.210326]跨0；9dev已暴露，不盲。production_B是在新image评分prompt下的诊断，根本不是原B native视频生产公平比较。工程gate只要求点估计大于base且研究排序改善，未能识别AIC域崩塌。
5. agy终端Gemini3.8Flash-high读取6段30s原生MP4，90格KEEP37/REJECT34/UNKNOWN19。工具声称1fps/30images，实际完整观测无法导出证明；20稀疏原生锚点与PTS映射核过，其中最后28-30s格镜头切换暴露整格过宽。teacher入训0、UNKNOWN未当负例。这不代表不能标注，而代表需要任务定义/边界与质量验收。
6. 旧32B160窗+盲复查仅65train/14dev弱支持，其余81UNKNOWN；旧微调15步后选回原B。成功、失败和弱一致性限制保留；同模型复查不是金标。旧空间LoRA合法0/148、旧TVSum时间20步也未胜基座，不能重开旧失败假称新进展。
7. 最佳空间源场31295锚点/原18723.876秒成本保留。本次新选择器新空间调用0，只精确复用完整场后过滤。模型最终实际主辅总参数必须<=9B；闭源可用于非测试训练标注，不能拿闭源直接推理复赛提交。
8. 本轮8新GPU作业自然完成/exit0、独立唯一终态账本4598.561109152623计费秒；不是GPU忙碌积分。无当前活跃本轮作业，历史费用不归零。
9. 现有TVSum48完整人工native映射源、开发104/96组及原开放非测试数据可查；不能凭空称有未暴露任务金标或所有全球数据不存在。新大数据需专项方向/大小/代理流量许可；先用现有数据。
10. 连续Pro预算原簿累计5/8，剩3。前次Pro G0/NO426与用户随后接受风险的双窗实验历史均保留，今日不是重置预算。

## 主控独立初始立场（先于外部意见）
撤回新评分ZIP推荐。407空是严重部署质量风险，但仅此无法确证真实高光召回或唯一原因。先区分语义任务不匹配、全局阈值/输出校准、视频时序输入差异、训练输出偏置/工程语义问题，而不是立刻扩大同配方TVSum训练或测试降阈值。
优先以原B37.66的native视频prompt/grammar/processor/时钟作为candidate0。构建现有非测试来源的目标一致高质量闭源标注，小批先验证再扩大，保留未知与证据不足；使用事件级KEEP/NO/UNKNOWN及原生证据帧和精确边界，独立审查切镜/快速动作，不能要求模型假称全帧看到。标注审查应比较实际可见视觉事实和任务定义，不能把同教师一致率当独立金标。
选择器校准实验只有非测试train/calibration/confirmation source级隔离、事前指标/目标预算和原B native公平对照成立时才值得做。TVSum排序任务可以辅助但不应取代高光边界监督。如果原B续训，则明确加载原B adapter、保留candidate0和实际optimizer变化，train-only不够的标签不凑负例。空间暂保持原8B源场；一轮一条可证伪主路线，质量验收先于426。用户希望推进，请给可执行的有界工作包，别无限等完美真值或无限模型菜单。

## 请每位普通参与者回答
先确认任务/版本/附件/实际读取范围及末标，区分事实、推断、未知。给唯一推荐主路线、最强反例、根因的最小非测试判别检查、具体标注格式/观察方法/质量接受条件、从原B续训还是新选择器及公平对照、数据源和隔离、预算/停止条件。数值阈值若只是前瞻工程投入规则需说明依据，不假称统计保证。批评主控至少一项关键弱点。只讨论材料，不调用外部实验；下一轮将完整共享所有人的原文再交叉批判，后才向Chrome研究Pro问一次。


## 原文件全文：reports/annotation_iteration_20261010/PLAN.md
字节=3996；SHA256=876c650aa73767aa4c6ac9445d003ad2b35dda6b86fdffc0b51b7be9aa69db56

```md
# 主控接替Pro后的执行协议

用户授权：自行深度调研、与专门子agent讨论、修复、迭代至可提交ZIP，优先终端agy高光标注。网页Pro因电脑操作工具URL安全检查失败未发送，0次；本方案为主控裁决，非Pro意见。

现有最佳已由用户反馈37.66；保留原B权重、全部冻结历史/失败/raw/费用。已有TVSum pilot真实crop12/time20步，但空间合法0/148；时间matched61rows903frames MAE新.54297/base.54175/常数.48817，均不能作为晋升理由。

先不下载新数据：TVSum已有48源native帧与20人人工评分一致，39训练源/9验证源；9源已暴露，只叫development，不能冒充盲测。600旧Gemini候选语义边界未经验收，全部继续排除监督。

## 已冻结的第一阶段

独立TVSum image-score selector，保持scores_x20(20..100)、固定2秒输入网格、16有序images/row。新rank8、alpha16、lr1e-4、3epochs、batch1/acc4，语言qkvo LoRA、视觉冻结，maxpixels65536；全真实输入assistant-only mask，无截断，独立输出。仅一个预先指定最终checkpoint，不依据本轮dev调学习率/阈值或挑checkpoint。原pilot与基座在相同固定长度整数JSON grammar、相同真实输入全89row比较。grammar只保证格式，不证明质量。

主要报告source macro Spearman（常数为0并单列）与每源固定top15%帧的人类重要性效用、全分母合法率、MAE/基座/常数。top15%仅TVSum诊断预算，不自动移植到AIC。预定晋升研究门：全部89row合法、所有目标帧都参与；相对基座macroSpearman和top15%效用均严格改善，且至少5/9源Spearman改善。另做固定train-only视觉依赖对照（真图/置换图），不据dev结果换对照。门只决定下一阶段投入，非AIC金标/官方分保证。

agy先3个已指定train源，每源2个30秒短native MP4，保存顺序原生ordinal/PTS与片内时钟→源时钟映射；固定2秒候选格KEEP/REJECT/UNKNOWN，可见视觉证据和观察限制，不自由生成秒数、不称全帧看过。首/中/末原生帧独立视觉检查；出现实质错位拒该段，不平移修标签，不扩到50源。未观察不生成负例。这批teacher弱标签不进入本轮人工评分训练。

第二阶段取决于首阶段真实结果：如研究门失败，停止本版配方并保留失败，新训练不替换生产；交付本地37.66保底包并透明记录没有新候选。如通过，独立冻结与训练输入一致的时间选择器、train-only阈值（允许空），先非测试，再完整426；原空间源场按精确来源重用，不能把adapter接原B0视频prompt。质量为TVSum代理证据，AIC分仍未知；用户接受风险的新候选必须与保底明显区分。

所有GPU通过现有共享runner和唯一追加账本；实时资源/外部冲突决定准入，无固定资源阈值。新小量控制文件经在线Mac ProxyJump上传；新数据/模型/大ZIP传输仍需要专项流量许可。本轮不需要新大传输。没有官网提交、公开发布、生产替换授权。

最终交付ZIP必须唯一predictions.jsonl、完整426身份/比例、源native合法帧号、整数合法框、无重复遗漏、CRC/解压字节/SHA、独立核验；如保底则原字节引用并标识历史37.66，不伪称本轮新训练结果。

## 资料

Qwen官方微调框架明确区分image/video tags及实际输入，冻结vision的混合图像视频训练建议不能证明本项目配方有效：https://github.com/QwenLM/Qwen3-VL/blob/main/qwen-vl-finetune/README.md

TVSum作者数据说明是50个视频/每源20人人工重要性，摘要预算是一种研究协议，不是AIC高光金标：https://github.com/yalesong/tvsum/blob/master/README.md

独立agent最强反例：TVSum相对重要不等于AIC应提交高光；强制topk会把空高光视频变正例；16images与原native video/B0/segment协议三重迁移不能混套；同源多帧不是独立证据。

```


## 原文件全文：reports/annotation_iteration_20261010/RESEARCH.md
字节=3537；SHA256=72079e7918753c742b8a1a815eb1a1c4127b4eba484d4cc9a57fe14fc3d80a71

```md
# 调研与独立讨论结论

本轮用户明确让主控接替网页Pro，并开一个专门讨论子agent。Pro实际0次。主控和独立agent往返审查，未把agent意见当实验成功证据。

## 当前问题与优先次序

1. 时间身份和输出协议先于更多弱标签：600旧Gemini自由报秒候选中已有37rz内容错位，输入工具成功不等于事件时间准确。
2. 先使用已有人工评分，而不是新收低质weaklabels：48源完整native/人工向量对齐证据比当前自动标注更可靠；新agy短视频只做标注流程检验和未来弱监督准备。
3. 原pilot仅20优化步、lr1e-5，不能据此宣布8B不能学，但必须先完整比较基座/常数/源排序，不能只看loss。新的3epochs/lr1e-4是主控预先指定的一次实验配方，不声称Qwen官方保证这一学习率。
4. 学生train/infer保持同16images/scores_x20任务，禁止把它直接加载到原B0 native-video segment提示。空间crop本轮不同时换。

## 官方和论文资料

- Qwen官方微调入口区分image/video媒体标签、真实输入对应关系，并提供grounding格式示例和vision冻结配置；所用imagecollator和实际输入检查符合这一原则，但本项目脚本与官方整套框架不同：https://github.com/QwenLM/Qwen3-VL/blob/main/qwen-vl-finetune/README.md
- TVSum作者说明50视频及每源20人人工重要性，摘要的固定预算是研究协议；不能认为这些主观重要性等于AIC高光动作金标：https://github.com/yalesong/tvsum/blob/master/README.md
- Otani et al., CVPR2019, Rethinking the Evaluation of Video Summaries：作者发现旧摘要指标很受分段影响，并建议直接检查重要性相关性。我们因此按source macro排序、人类效用和native扩段效果一起报告，避免只优化常数可获益的MAE：https://openaccess.thecvf.com/content_CVPR_2019/html/Otani_Rethinking_the_Evaluation_of_Video_Summaries_CVPR_2019_paper.html
- QVHighlights原论文是query-conditioned moments+saliency，与不带query的AIC裁剪高光不是同一任务；适合作后续明确query任务的数据候选，本轮不盲目下载大型新包：https://arxiv.org/abs/2107.09609

## 独立agent质疑与主控采纳

最强反例：常数重要性降低MAE而排序为0；固定15%把无高光视频变正例；2秒中点不代表整个2秒动作；换image-score adapter回原B0构成输入、任务、解码三重迁移。主控接受：不造TVSum0分负例、不每视频强制topk、不换crop、不把弱标注当gold。

研究门完整89行全分母、按源macro Spearman/固定top15%效用，常数源记0，固定nativeordinal tie-break；至少5/9源排序改善且两macro正改善。另12个train-only hash预选16图行跨来源交换图，比较原目标NLL，正常图整体和多数更低才能视为有输入依赖。仅输入有影响不能证明高光质量。

source bootstrap CI和最差源退化完整报告，可能改善极小而CI跨0；不声称统计确定性。第二阶段阈值49只由训练评分q80决定，可空，并用完整human native向量对扩段选择评估，不凭排序门直接推426。

agy3train源6短clip，固定2s candidate ID且native PTS精确映射、无音频、声明有损视频派生，模型工具报告1fps不能当独立全域覆盖证明。首中末原生PNG人工式视觉检查仅是稀疏观察，绝不升级成逐帧全通过。若实质错位则拒该段、不平移修标签；本轮不把新weaklabels加入人工训练目标。

```


## 原文件全文：reports/annotation_iteration_20261010/DISCUSSION.md
字节=2683；SHA256=b2a8d16267da811807e35d4ee2a5beb4a8b7d3cf0adc2b3ced6f49d4ef771c0e

```md
# 专门子agent的独立审查与主控答复

用户明确要求“你自己去开个子agent专门和自己讨论去”，因此仅开一个只读讨论agent independent_plan_review，主控负责修改/执行/验收。

## 第一轮独立意见

TVSum bins0..5和更多训练步不自动证明AIC改善。常数评分可能更低MAE却排序0；相对重要不一定应该提交，2s中点不是动作边界。新16images adapter接原B native视频/B0/segment协议有输入、任务、decoder三重迁移。应先训练only协议/视觉依赖小门；9验证源已经暴露，不能称真正untouched。426只替换时间且复用完整空间源场；合法率只是工程门，没有独立AIC gold则不能称官方质量通过。

优先native短clip、固定候选格KEEP/REJECT/UNKNOWN与可见锚点映射；工具DONE不证明观看全域。先3train源，不把未观察记负，实质错位拒该段。不要把TVSum1..5映射0=无高光，不强制每video topk。若image-score独立替换必须train/infer同序列和processor，在同native域比较选帧。

## 主控答复

接受任务/输入迁移批评，保持scores_x20，不造0。一次3epochs/lr1e-4/acc4/rank8实验；9源仅development，所有89行全分母、固定grammar，同输入base/new/pilot/oldadapter比较。预先三条件、视觉依赖小门和train-only阈值；agy只6trainclip弱标签，不混本轮人工监督；研究门失败保留原配方结果，交付透明历史37.66保底，不伪称新模型成果。

## 第二轮最终审查（原结论）

接受先执行一次独立scores_x20评分器实验；冻结门只能支持继续研究，不能证明AIC提分。保持原B和37.66包作为保底，不合并crop。

完整89行、常数Spearman0、逐source变化/最差退化/bootstrap CI；top15效用按source宏平均，平分按nativeordinal。12train完整16图row正常与跨源互换，优先teacher-forced NLL；全体生成向量不变是塌缩，发生变化只证明依赖。

最终阈值与native映射只train-only冻结；9源实际选中率/空源/低重要误选/完整native效用。2s中点不能自动赋整段，要用既有完整human向量验证扩段。没有AIC gold，non-test工程检查不是质量保证。

最强反例：排序略升，但阈值选出更多低收益帧，或扩段造成误报，连续IoU加权F最终下降。新包只能是用户接受风险的竞争试验，不能标“质量通过”。

本轮agent仅只读研究、审查与讨论，未修改/调用模型/启动GPU或传输。

## 追加代码审查

主控已再次交付本轮实际代码供独立agent检查，后续发现和修复另存，不回写先前意见。

```


## 原文件全文：reports/annotation_iteration_20261010/INDEPENDENT_REVIEW.md
字节=3003；SHA256=c659a7ac11faff9976a7f3341da9e90329dde8ded414063f19abeb7c18736b33

```md
# 独立讨论与代码复核

用户明确要求专门子agent与主控讨论；independent_plan_review只读检查，不改代码、调用模型或启动GPU。主控综合意见裁决，不代表网页版Pro意见。

独立复核未发现score grammar、实际生成或assistant-only图片交换NLL的致命问题。发现原evaluate_iteration.py只把第一阶段研究门写入PASS，未将已冻结的第二阶段native macro proxy F严格大于base纳入放行。主控保留原脚本，新建evaluate_iteration_v2.py，分别记录research_pass/stage2_pass；只有后者允许继续本版426。

完整时间域审查发现实际数据无漏格或重叠，但原验收缺少可执行约束。新增audit_native_domains.py，实际CPU通过9源首0/连续/末=native_frames=human_vector_length、media/PTS身份、20人分数和、89行对所有grid一对一覆盖。SHA与独立agent自行计算一致；不重跑训练或已成功生成。

原B adapter在新image-score prompt下仅是诊断，不宣称击败原B视频生产管线。视觉依赖仅证明输入敏感性。agy首中末图片仅支持稀疏内容抽查；1fps工具返回不证明完整观察，弱标签不纳入本轮训练。

独立agent复核v2放行逻辑通过：完整域断言先执行，research_pass保留原门，stage2_pass额外要求等权native代理F改善，bootstrap/常数MAE仅作诊断。后续实际输入方案另审三点：OrdinalReader为BGR，必须显式一次转RGB并分别记像素签名；精确Fraction时间格连续覆盖scope，每16图实长尾块不填充，超长或空格拒绝；完整旧空间场先验身份与全部anchor，禁止预筛或通过补框/删选帧绕过缺口。原B配置只能提供已冻结数据/decoder/空间场，不能沿用原时间模型身份。

selector_contract.py的CPU验收实际通过9源全部native grid和89行user prompt精确相等。这是迁移工程准备，不代表新的质量证据或模型调用。

完整新dev结果实际通过预定门：macro Spearman .522329相对base .043629、8/9改善；native代理F .130418相对.041489，但配对95区间跨0，不保证AIC分数。后续contest_engine子agent主体审查通过：RGB/精确grid/实际token与visiontensor CPU回放/全空间场compose/11strict。发现只冻结adapter权重而未冻结配置的身份缺口，主控在启动前加入配置SHA dcd134aecf4573d0f462d70adcf96b8beeba6bd76e62ec6c5bf57593fe79a8e1和实际active adapter/rank/alpha/targets/参数回执，非测试8真实8call成功证明实际身份符合。子agent曾担心sft_contract import来源，随后实核common注入和远端函数SHA c2e762e7deca7cbc15d6d2b158e5251eeb25141b5cf5b02b8996042619c3414d与旧source_lock一致并撤回该疑点，没有为错误疑点改版或重复生成。

非测试8独立CPU回放与11strict全部通过；实际选择全空，不能作为质量改善证据，阈值未因此调整。仅作为实际管线工程验收，继续已冻结的单次426实验生成。

```


## 原文件全文：reports/annotation_iteration_20261010/QUALITY_REPORT.md
字节=2679；SHA256=371d066dabc0911167bd3bd355fd7ca4bdf37cb4bf527a06ae4506724201945b

```md
# 通过冻结的研究与第二阶段投入门

本轮真实LoRA训练237步；最终adapter SHA `1f39afb662f77661f008bc6000a054b9d838b988558ef0b762e2d98975d94933`。6个GPU作业自然completed、exit0、终态账本一一对应，累计新增计费运行时间2985.891秒。训练与权重留Linux，原生产未替换。

研究门=True，第二阶段门=True；所有4组各89行合法，完整9源原生域覆盖通过。9源是已见development，不是盲测；TVSum代理指标不是AIC官方分。

| 同图片评分协议 | macro Spearman | top15人工效用 | macro MAE | native代理F |
|---|---:|---:|---:|---:|
| new | 0.522329 | 2.421738 | 0.413941 | 0.130418 |
| base | 0.043629 | 1.996554 | 0.555512 | 0.041489 |
| pilot | 0.091523 | 1.928498 | 0.560734 | 0.041489 |
| production_B | 0.044226 | 1.904736 | 0.622093 | 0.050574 |

production_B仅在新image-score prompt下诊断，不等于原B native视频管线被比较。top15%只作排序诊断，实际选择阈值49只由train冻结，允许空；2秒域扩展是插值假设。

| 源 | Spearman new | base | native F new | base | 新选中原生帧占比 |
|---|---:|---:|---:|---:|---:|
| -esJrBWj2d8 | 0.481794 | -0.068359 | 0.100000 | 0.001961 | 0.112847 |
| 4wU_LUjG5Ic | 0.521919 | -0.355677 | 0.000000 | 0.000000 | 0.000000 |
| EYqVtI9YWJA | 0.745954 | 0.276619 | 0.117878 | 0.153846 | 0.100690 |
| J0nA4VgnoCo | 0.529518 | -0.049685 | 0.000000 | 0.000000 | 0.000000 |
| JKpqYvAdIsw | 0.124814 | 0.193680 | 0.000000 | 0.000000 | 0.000000 |
| Yi4Ij2NM7U4 | 0.765361 | 0.161156 | 0.705882 | 0.217593 | 0.044394 |
| cjibtmSLxQ4 | 0.397881 | 0.234930 | 0.000000 | 0.000000 | 0.015408 |
| i3wAGJaaktw | 0.448332 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| sTEELN-vY30 | 0.685391 | 0.000000 | 0.250000 | 0.000000 | 0.147717 |

Spearman改善源=8/9；最差逐源变化=-0.068865。
配对源bootstrap95区间：`{"macro_spearman": [0.2954748974839695, 0.6400322592634471], "macro_top15_utility": [0.1529160912940675, 0.7167301024095378], "native_macro_proxy_f": [-0.0010960742498937347, 0.21032592871357847]}`。若跨0，证据不足支持可靠泛化或官网提分。
训练域图片交换：正常图片更好10/12，平均swap-normal NLL=0.070607，输入依赖门=True。此检查不等于高光质量。

agy另完成6段、90格：KEEP37/REJECT34/UNKNOWN19，20个稀疏原生锚点已查看；观察与整段边界仍有缺口。新teacher训练入选0，UNKNOWN未转负例。

未依据本轮dev修改学习率、阈值或选checkpoint。原raw/失败/成功生成保留；验收工程v2独立修正了第一阶段PASS误当第二阶段PASS的错误。

```


## 原文件全文：reports/annotation_iteration_20261010/DELIVERY.md
字节=3691；SHA256=5985ffc8495f27e9ef7669abde311b2b36d1b55d722381039b4075499118989d

```md
# 2026-10-10 本轮交付

已完成独立子agent讨论、数据域核验、真实237步LoRA训练、4组各89条开发集比较、agy视频标注试验及完整426视频实验包。两个ZIP均已在本地通过验收；没有代用户提交官网，没有替换原生产模型。

| 本地ZIP | 身份 | 大小 | 实际结果 |
|---|---|---:|---|
| [candidate_IMAGE_SCORE_237STEP_8B.zip](../../deliveries/ANNOTATION_ITERATION_20261010/NEW_237STEP_EXPERIMENTAL/candidate_IMAGE_SCORE_237STEP_8B.zip) | 新237步微调实验 | 12,384字节 | 426视频，3,189选中帧，407视频为空；官网分未知 |
| [candidate_SAFE_37_66.zip](../../deliveries/ANNOTATION_ITERATION_20261010/SAFE_37_66/candidate_SAFE_37_66.zip) | 历史最佳原字节副本 | 306,167字节 | 426视频，102,112选中帧；此前用户反馈37.66分 |

新包SHA256：`01969ab4c8221b279dfa58fe1c9f3c5c47cd01fe8cd7dea312bde93cdb3d6325`。
历史包SHA256：`07730c9e02e68d1a1ce54e7ef5a8aa616346cf8f2f8d78426ed36bc3eb481496`。

新实验包适合尝试回传分数，但当前稳妥选择仍是已知37.66历史包。新选择器只有19个视频非空，明显偏保守；通过格式验收不能证明高光质量合格或超过旧最佳。没有在看到复赛输出后修改冻结阈值、强行补高光或选择其他checkpoint。

## 实际训练与验证

本轮使用TVSum完整人工分数训练独立图片重要性评分选择器：39训练源314行，9个已见开发源89行；q/k/v/o LoRA rank8，237次真实optimizer更新，完整参数8,774,791,408。adapter SHA `1f39afb662f77661f008bc6000a054b9d838b988558ef0b762e2d98975d94933`；权重留Linux独立目录，原B8B生产保持。

在同一图片评分协议下，开发源宏平均Spearman新模型0.522329、base0.043629，8/9源改善。native代理F新模型0.130418、base0.041489，但配对95%区间跨0；这些是已见TVSum开发代理指标，不能代替AIC官方分。原production_B也只在这个新prompt下作诊断，未证明击败其原视频管线。详见[质量报告](QUALITY_REPORT.md)与[独立审查](INDEPENDENT_REVIEW.md)。

426视频510次真实生成全部完成，实际输入4439张原生采样图片；所有输入像素、token、prompt、输出解析均经过独立CPU回放。原完整空间源场先组合再过滤，空间模型新增调用0，原31,295锚点及费用保留。远端11项严格验收全部通过，本地另核ZIP单文件CRC、426精确源身份、比例、帧序与范围、框几何、JSONL字节SHA和远端报告一致。允许空视频是原协议行为。

## agy标注结果

优先通过终端调用agy，6段原生视频完成90个2秒候选格：37 KEEP、34 REJECT、19 UNKNOWN。逐源时间映射与20个原生图像锚点已核对；工具仅回报1fps观察，完整边界观察未获证明，末格也存在镜头切换。因此新teacher标签入训0；UNKNOWN未当负例，原始输出与标注待复核保留。详见[标注发现](ANNOTATION_FINDINGS.md)。

## 完成状态与费用

所有本轮拥有的远端controller/engine作业在收集时为0；8个GPU作业均自然完成、exit0，唯一终态回执与原追加账本相符。前6个训练/诊断作业2985.891315707937秒，最终两次推理1612.6697934446856秒，本轮8个GPU作业合计4598.561109152623秒（约1.277小时计费运行时间；不是GPU忙碌度积分）。全部历史费用、失败、raw、原最佳包及旧生产权重保留。

新ZIP与17个小量聚合文件共30,111字节，实时确认Mac在线后经Mac ProxyJump取回；没有下载新大数据或回传模型权重，没有公开push。此前Pro调用0次，后由用户指定主控与独立子agent代替讨论。

```


## 原文件全文：reports/annotation_iteration_20261010/ANNOTATION_FINDINGS.md
字节=1370；SHA256=829c23f1a74869ccb6c171a59843e01220354b2474af94b4f0f2956edc7720d6

```md
# 本次agy扩标裁决

3个训练源、每源2段30秒原生MP4，6次真实agy命令调用自然完成。90个固定候选格：KEEP37、REJECT34、UNKNOWN19。新标签/原stream/全PTS映射/clip SHA保留，UNKNOWN不当作负例。

20个本地原生锚点复核支持多个观察点对象对应，但不能证明全率观察或全格事件边界。末段28/29秒确有扇舞，尾帧已切到行人，说明离散观察覆盖不足能直接导致高光区间过长，不能只验JSON就入训。

另对6段全部native mapping与原20人人工重要性求交，记录TVSum代理均值。0tm第二段KEEP均值2.258、REJECT2.299；37rz第二段KEEP1.647、REJECT1.648，弱标签正负在此代理下未分开。其他段出现正向分离。TVSum相对重要性与本次语义KEEP定义并不相同，故这些数字不是teacher准确率，也不是AIC分数。

裁决：本次不把teacher标签加入已冻结人工评分训练，也不直接扩成50源；已有人工监督的完整训练和对照先完成。下一轮若扩teacher，应先让目标定义明确并对切镜/快速动作提高观察密度，建立独立边界参考，再以视频源为单位验收，保留未观察UNKNOWN。当前模型显示具备读本地短MP4并输出带观察限制标签的能力；“原生读视频”等于内部什么采样，仍以实际工具证据为限。

```


## 原文件全文：reports/annotation_iteration_20261010/ANNOTATION_ANCHOR_AUDIT.md
字节=2311；SHA256=8591355103b31fcdc1e17821046a0ba6d45276897156fa462348f962e9b6f5d1

```md
# 短视频稀疏锚点核验

主控实际查看源原生帧首、中、末PNG；这些PNG是本地审查证据，不作为本次agy输入。agy通过view_file原生读取短MP4。片内时间映射由全部原生PTS逐项验收。

0tmA_C6XwfM_00：首帧男子与大型犬在沙发边；中帧男子扶犬身体/腿部；末帧男子托持小犬前爪。与相邻固定格对象和大类动作相符，尚不证明每格高光价值或剪切微动作。

0tmA_C6XwfM_01：首、中帧均为手托犬爪、指甲剪贴近；末帧小白犬面向镜头张嘴。对应标签对象一致。单个锚点不能证明确已闭合剪切；teacher关于动作发生的细节仍为待检弱证据。

37rzWOQsNIw_00：首帧熟食店柜台，中帧打开三明治展示馅料，末帧男子持咬过的三明治并触碰嘴边。对象及粗略段落对应，没有发现旧整视频标注的明显秒数错位。

37rzWOQsNIw_01：首帧地面鸽子，中帧手持透明杯分层甜品，末帧手在杯上方持勺。对象对应；单帧不能判定连续搅拌是否高光。

91IHQYk1IQM_00：首帧铁栏后儿童，中帧Cathay Bank前红色盛装巡游并有气球/人头遮挡，末帧近景红色布料与人头遮挡。对应REJECT/KEEP/UNKNOWN的描述对象。是否应取高光仍需人工语义参考。

91IHQYk1IQM_01：已实际查看首帧红色狮头与黄色气球遮挡、中帧街道倒立表演者、末帧近处穿浅色外套行人。该段teacher最终返回尚待核对。

这是18个稀疏原生锚点检查，不是90格逐帧精标验收。工具声称1fps观察，但stream不导出实际输入帧/时间点，完整观察不可独立证明；全部新teacher标签继续排除本轮训练。

最终91IHQYk1IQM_01返回后发现尾帧行人与candidate14“28/29秒扇舞”表面不一致。主控没有立即判幻觉，而是按已冻结原生映射提取实际28/29秒：两帧确有红衣人物持蓝白扇子，teacher关于观察点的对象描述成立；29.96秒尾帧则已切到近处行人。证明1fps点观察可以对应，但把28..30秒整格赋KEEP会覆盖未观察切镜，不能据此声称整格精确高光。新增2帧证据与observation_audit.json保留，原标签未改或平移。6段全部审查结束，总20个稀疏锚点、0个teacher训练入选。

```


## 原文件全文：reports/annotation_iteration_20261010/annotation_summary.json
字节=30546；SHA256=f82fc95023c266b570b21c5522dd2f3d1e55b13bfe3359d5272902e36182af78

```json
{"status":"SIX_SHORT_CLIPS_COMPLETE_WEAK_LABELS_QUARANTINED","clips":[{"clip":"0tmA_C6XwfM_00","samples":[{"candidate_id":0,"state":"REJECT","native_frames":50,"human_proxy_mean":1.4049999999999998,"teacher_claimed_observation_instants":[0,1],"not_semantic_highlight_gold":true},{"candidate_id":1,"state":"REJECT","native_frames":50,"human_proxy_mean":1.7919999999999985,"teacher_claimed_observation_instants":[2,3],"not_semantic_highlight_gold":true},{"candidate_id":2,"state":"REJECT","native_frames":50,"human_proxy_mean":1.506,"teacher_claimed_observation_instants":[4,5],"not_semantic_highlight_gold":true},{"candidate_id":3,"state":"UNKNOWN","native_frames":50,"human_proxy_mean":1.6960000000000017,"teacher_claimed_observation_instants":[6,7],"not_semantic_highlight_gold":true},{"candidate_id":4,"state":"KEEP","native_frames":50,"human_proxy_mean":2.8760000000000026,"teacher_claimed_observation_instants":[8,9],"not_semantic_highlight_gold":true},{"candidate_id":5,"state":"REJECT","native_frames":50,"human_proxy_mean":2.360999999999998,"teacher_claimed_observation_instants":[10,11],"not_semantic_highlight_gold":true},{"candidate_id":6,"state":"KEEP","native_frames":50,"human_proxy_mean":1.517,"teacher_claimed_observation_instants":[12,13],"not_semantic_highlight_gold":true},{"candidate_id":7,"state":"REJECT","native_frames":50,"human_proxy_mean":2.332999999999998,"teacher_claimed_observation_instants":[14,15],"not_semantic_highlight_gold":true},{"candidate_id":8,"state":"REJECT","native_frames":50,"human_proxy_mean":2.4480000000000017,"teacher_claimed_observation_instants":[16,17],"not_semantic_highlight_gold":true},{"candidate_id":9,"state":"REJECT","native_frames":50,"human_proxy_mean":1.4700000000000015,"teacher_claimed_observation_instants":[18,19],"not_semantic_highlight_gold":true},{"candidate_id":10,"state":"REJECT","native_frames":50,"human_proxy_mean":1.5969999999999995,"teacher_claimed_observation_instants":[20,21],"not_semantic_highlight_gold":true},{"candidate_id":11,"state":"REJECT","native_frames":50,"human_proxy_mean":1.7469999999999999,"teacher_claimed_observation_instants":[22,23],"not_semantic_highlight_gold":true},{"candidate_id":12,"state":"REJECT","native_frames":50,"human_proxy_mean":1.5539999999999987,"teacher_claimed_observation_instants":[24,25],"not_semantic_highlight_gold":true},{"candidate_id":13,"state":"KEEP","native_frames":50,"human_proxy_mean":1.8930000000000013,"teacher_claimed_observation_instants":[26,27],"not_semantic_highlight_gold":true},{"candidate_id":14,"state":"KEEP","native_frames":50,"human_proxy_mean":2.0469999999999984,"teacher_claimed_observation_instants":[28,29],"not_semantic_highlight_gold":true}],"labels_sha256":"5dee51ad458d8f86f17ccf18a2bd6567b178b6ba92e0a50df09b06c505dc0056","manifest_sha256":"3e7aac05ae83497103b4c5f6ce7d7486c454126f15b883a00ed2898e800e21eb","mean_human_proxy_by_state":{"REJECT":1.8212999999999997,"UNKNOWN":1.6960000000000017,"KEEP":2.0832500000000005}},{"clip":"0tmA_C6XwfM_01","samples":[{"candidate_id":0,"state":"REJECT","native_frames":50,"human_proxy_mean":2.7979999999999996,"teacher_claimed_observation_instants":[0,1],"not_semantic_highlight_gold":true},{"candidate_id":1,"state":"KEEP","native_frames":50,"human_proxy_mean":2.9960000000000004,"teacher_claimed_observation_instants":[2,3],"not_semantic_highlight_gold":true},{"candidate_id":2,"state":"KEEP","native_frames":50,"human_proxy_mean":2.7060000000000013,"teacher_claimed_observation_instants":[4,5],"not_semantic_highlight_gold":true},{"candidate_id":3,"state":"REJECT","native_frames":50,"human_proxy_mean":2.7979999999999996,"teacher_claimed_observation_instants":[6,7],"not_semantic_highlight_gold":true},{"candidate_id":4,"state":"KEEP","native_frames":50,"human_proxy_mean":2.506,"teacher_claimed_observation_instants":[8,9],"not_semantic_highlight_gold":true},{"candidate_id":5,"state":"KEEP","native_frames":50,"human_proxy_mean":2.4020000000000024,"teacher_claimed_observation_instants":[10,11],"not_semantic_highlight_gold":true},{"candidate_id":6,"state":"REJECT","native_frames":50,"human_proxy_mean":2.4490000000000016,"teacher_claimed_observation_instants":[12,13],"not_semantic_highlight_gold":true},{"candidate_id":7,"state":"KEEP","native_frames":50,"human_proxy_mean":2.450000000000002,"teacher_claimed_observation_instants":[14,15],"not_semantic_highlight_gold":true},{"candidate_id":8,"state":"KEEP","native_frames":50,"human_proxy_mean":2.302999999999998,"teacher_claimed_observation_instants":[16,17],"not_semantic_highlight_gold":true},{"candidate_id":9,"state":"UNKNOWN","native_frames":50,"human_proxy_mean":2.006,"teacher_claimed_observation_instants":[18,19],"not_semantic_highlight_gold":true},{"candidate_id":10,"state":"KEEP","native_frames":50,"human_proxy_mean":1.8529999999999989,"teacher_claimed_observation_instants":[20,21],"not_semantic_highlight_gold":true},{"candidate_id":11,"state":"REJECT","native_frames":50,"human_proxy_mean":1.8009999999999986,"teacher_claimed_observation_instants":[22,23],"not_semantic_highlight_gold":true},{"candidate_id":12,"state":"KEEP","native_frames":50,"human_proxy_mean":1.506,"teacher_claimed_observation_instants":[24,25],"not_semantic_highlight_gold":true},{"candidate_id":13,"state":"REJECT","native_frames":50,"human_proxy_mean":1.6470000000000005,"teacher_claimed_observation_instants":[26,27],"not_semantic_highlight_gold":true},{"candidate_id":14,"state":"KEEP","native_frames":50,"human_proxy_mean":1.6009999999999998,"teacher_claimed_observation_instants":[28,29],"not_semantic_highlight_gold":true}],"labels_sha256":"903c2bad5e6eccff337f4d5774c0f23eea9d096dc5a69ae7da1d377a361af7e7","manifest_sha256":"e135b041b6f8976f9ccf37d5894f6386d04d2bb66a24642a6de4c42bfa317aca","mean_human_proxy_by_state":{"REJECT":2.2986,"UNKNOWN":2.006,"KEEP":2.258111111111111}},{"clip":"37rzWOQsNIw_00","samples":[{"candidate_id":0,"state":"KEEP","native_frames":60,"human_proxy_mean":2.949999999999998,"teacher_claimed_observation_instants":[0,1],"not_semantic_highlight_gold":true},{"candidate_id":1,"state":"REJECT","native_frames":60,"human_proxy_mean":1.900000000000002,"teacher_claimed_observation_instants":[2,3],"not_semantic_highlight_gold":true},{"candidate_id":2,"state":"REJECT","native_frames":60,"human_proxy_mean":2.2000000000000015,"teacher_claimed_observation_instants":[4,5],"not_semantic_highlight_gold":true},{"candidate_id":3,"state":"REJECT","native_frames":60,"human_proxy_mean":2.0999999999999974,"teacher_claimed_observation_instants":[6,7],"not_semantic_highlight_gold":true},{"candidate_id":4,"state":"REJECT","native_frames":60,"human_proxy_mean":2.0,"teacher_claimed_observation_instants":[8,9],"not_semantic_highlight_gold":true},{"candidate_id":5,"state":"KEEP","native_frames":60,"human_proxy_mean":2.4500000000000006,"teacher_claimed_observation_instants":[10,11],"not_semantic_highlight_gold":true},{"candidate_id":6,"state":"KEEP","native_frames":60,"human_proxy_mean":2.0466666666666646,"teacher_claimed_observation_instants":[12,13],"not_semantic_highlight_gold":true},{"candidate_id":7,"state":"KEEP","native_frames":60,"human_proxy_mean":1.8508333333333316,"teacher_claimed_observation_instants":[14,15],"not_semantic_highlight_gold":true},{"candidate_id":8,"state":"REJECT","native_frames":60,"human_proxy_mean":1.9083333333333352,"teacher_claimed_observation_instants":[16,17],"not_semantic_highlight_gold":true},{"candidate_id":9,"state":"REJECT","native_frames":60,"human_proxy_mean":2.3858333333333364,"teacher_claimed_observation_instants":[18,19],"not_semantic_highlight_gold":true},{"candidate_id":10,"state":"REJECT","native_frames":60,"human_proxy_mean":1.5499999999999983,"teacher_claimed_observation_instants":[20,21],"not_semantic_highlight_gold":true},{"candidate_id":11,"state":"REJECT","native_frames":60,"human_proxy_mean":1.559166666666665,"teacher_claimed_observation_instants":[22,23],"not_semantic_highlight_gold":true},{"candidate_id":12,"state":"KEEP","native_frames":60,"human_proxy_mean":2.1016666666666644,"teacher_claimed_observation_instants":[24,25],"not_semantic_highlight_gold":true},{"candidate_id":13,"state":"KEEP","native_frames":60,"human_proxy_mean":2.193333333333335,"teacher_claimed_observation_instants":[26,27],"not_semantic_highlight_gold":true},{"candidate_id":14,"state":"KEEP","native_frames":59,"human_proxy_mean":1.799999999999998,"teacher_claimed_observation_instants":[28,29],"not_semantic_highlight_gold":true}],"labels_sha256":"8ca81f3d6a6e27b7db7bd125b060c292a689b22992dfd35f182e9788ae3a56b3","manifest_sha256":"c97ba2cdfe2818e4e81b4a1fef061305326b5a697f7de23d2617e9477586f0db","mean_human_proxy_by_state":{"REJECT":1.950416666666667,"KEEP":2.1989285714285707}},{"clip":"37rzWOQsNIw_01","samples":[{"candidate_id":0,"state":"REJECT","native_frames":60,"human_proxy_mean":1.3500000000000014,"teacher_claimed_observation_instants":[0,1],"not_semantic_highlight_gold":true},{"candidate_id":1,"state":"REJECT","native_frames":60,"human_proxy_mean":1.2499999999999987,"teacher_claimed_observation_instants":[2,3],"not_semantic_highlight_gold":true},{"candidate_id":2,"state":"UNKNOWN","native_frames":60,"human_proxy_mean":1.500000000000001,"teacher_claimed_observation_instants":[4,5],"not_semantic_highlight_gold":true},{"candidate_id":3,"state":"KEEP","native_frames":60,"human_proxy_mean":1.7774999999999983,"teacher_claimed_observation_instants":[6,7],"not_semantic_highlight_gold":true},{"candidate_id":4,"state":"KEEP","native_frames":60,"human_proxy_mean":1.8241666666666658,"teacher_claimed_observation_instants":[8,9],"not_semantic_highlight_gold":true},{"candidate_id":5,"state":"REJECT","native_frames":60,"human_proxy_mean":1.6966666666666643,"teacher_claimed_observation_instants":[10,11],"not_semantic_highlight_gold":true},{"candidate_id":6,"state":"UNKNOWN","native_frames":60,"human_proxy_mean":1.5483333333333336,"teacher_claimed_observation_instants":[12,13],"not_semantic_highlight_gold":true},{"candidate_id":7,"state":"KEEP","native_frames":60,"human_proxy_mean":1.6808333333333318,"teacher_claimed_observation_instants":[14,15],"not_semantic_highlight_gold":true},{"candidate_id":8,"state":"UNKNOWN","native_frames":60,"human_proxy_mean":1.7725000000000017,"teacher_claimed_observation_instants":[16,17],"not_semantic_highlight_gold":true},{"candidate_id":9,"state":"UNKNOWN","native_frames":60,"human_proxy_mean":1.9325000000000023,"teacher_claimed_observation_instants":[18,19],"not_semantic_highlight_gold":true},{"candidate_id":10,"state":"REJECT","native_frames":60,"human_proxy_mean":2.0724999999999993,"teacher_claimed_observation_instants":[20,21],"not_semantic_highlight_gold":true},{"candidate_id":11,"state":"REJECT","native_frames":60,"human_proxy_mean":1.8708333333333333,"teacher_claimed_observation_instants":[22,23],"not_semantic_highlight_gold":true},{"candidate_id":12,"state":"UNKNOWN","native_frames":60,"human_proxy_mean":1.5691666666666684,"teacher_claimed_observation_instants":[24,25],"not_semantic_highlight_gold":true},{"candidate_id":13,"state":"KEEP","native_frames":60,"human_proxy_mean":1.4774999999999983,"teacher_claimed_observation_instants":[26,27],"not_semantic_highlight_gold":true},{"candidate_id":14,"state":"KEEP","native_frames":59,"human_proxy_mean":1.473728813559323,"teacher_claimed_observation_instants":[28,29],"not_semantic_highlight_gold":true}],"labels_sha256":"684b78e6aa619aef2c1cf757acb3aa78c6debe62c824bba5c16ed2654f3780d7","manifest_sha256":"c2caa6306803bc256cd9c1e0adc439af48f9563136b34cf5810c32311332b08a","mean_human_proxy_by_state":{"REJECT":1.6479999999999992,"UNKNOWN":1.6645000000000014,"KEEP":1.6467457627118633}},{"clip":"91IHQYk1IQM_00","samples":[{"candidate_id":0,"state":"REJECT","native_frames":60,"human_proxy_mean":1.5499999999999983,"teacher_claimed_observation_instants":[0,1],"not_semantic_highlight_gold":true},{"candidate_id":1,"state":"REJECT","native_frames":60,"human_proxy_mean":1.799999999999998,"teacher_claimed_observation_instants":[2,3],"not_semantic_highlight_gold":true},{"candidate_id":2,"state":"REJECT","native_frames":60,"human_proxy_mean":1.7000000000000017,"teacher_claimed_observation_instants":[4,5],"not_semantic_highlight_gold":true},{"candidate_id":3,"state":"REJECT","native_frames":60,"human_proxy_mean":1.75,"teacher_claimed_observation_instants":[6,7],"not_semantic_highlight_gold":true},{"candidate_id":4,"state":"UNKNOWN","native_frames":60,"human_proxy_mean":2.0999999999999974,"teacher_claimed_observation_instants":[8,9],"not_semantic_highlight_gold":true},{"candidate_id":5,"state":"KEEP","native_frames":60,"human_proxy_mean":2.049999999999998,"teacher_claimed_observation_instants":[10,11],"not_semantic_highlight_gold":true},{"candidate_id":6,"state":"UNKNOWN","native_frames":60,"human_proxy_mean":1.8041666666666647,"teacher_claimed_observation_instants":[12,13],"not_semantic_highlight_gold":true},{"candidate_id":7,"state":"KEEP","native_frames":60,"human_proxy_mean":2.056666666666665,"teacher_claimed_observation_instants":[14,15],"not_semantic_highlight_gold":true},{"candidate_id":8,"state":"KEEP","native_frames":60,"human_proxy_mean":2.455833333333334,"teacher_claimed_observation_instants":[16,17],"not_semantic_highlight_gold":true},{"candidate_id":9,"state":"UNKNOWN","native_frames":60,"human_proxy_mean":2.786666666666668,"teacher_claimed_observation_instants":[18,19],"not_semantic_highlight_gold":true},{"candidate_id":10,"state":"KEEP","native_frames":60,"human_proxy_mean":2.024166666666667,"teacher_claimed_observation_instants":[20,21],"not_semantic_highlight_gold":true},{"candidate_id":11,"state":"KEEP","native_frames":60,"human_proxy_mean":3.4399999999999973,"teacher_claimed_observation_instants":[22,23],"not_semantic_highlight_gold":true},{"candidate_id":12,"state":"KEEP","native_frames":60,"human_proxy_mean":2.8433333333333306,"teacher_claimed_observation_instants":[24,25],"not_semantic_highlight_gold":true},{"candidate_id":13,"state":"KEEP","native_frames":60,"human_proxy_mean":2.438333333333334,"teacher_claimed_observation_instants":[26,27],"not_semantic_highlight_gold":true},{"candidate_id":14,"state":"UNKNOWN","native_frames":59,"human_proxy_mean":1.75,"teacher_claimed_observation_instants":[28,29],"not_semantic_highlight_gold":true}],"labels_sha256":"18f349dff717e4de1d91b5b8df735a431ea19e05d4b08d5ddb119c99ccd21762","manifest_sha256":"dd140b668fdb6b24a4ab7660a8c559188eeaaa088ad6e01b87cecd8726b491c6","mean_human_proxy_by_state":{"REJECT":1.6999999999999995,"UNKNOWN":2.1102083333333326,"KEEP":2.472619047619046}},{"clip":"91IHQYk1IQM_01","samples":[{"candidate_id":0,"state":"UNKNOWN","native_frames":60,"human_proxy_mean":2.1000000000000005,"teacher_claimed_observation_instants":[],"not_semantic_highlight_gold":true},{"candidate_id":1,"state":"KEEP","native_frames":60,"human_proxy_mean":1.9750000000000014,"teacher_claimed_observation_instants":[2,3],"not_semantic_highlight_gold":true},{"candidate_id":2,"state":"UNKNOWN","native_frames":60,"human_proxy_mean":2.050000000000003,"teacher_claimed_observation_instants":[],"not_semantic_highlight_gold":true},{"candidate_id":3,"state":"UNKNOWN","native_frames":60,"human_proxy_mean":2.3249999999999997,"teacher_claimed_observation_instants":[],"not_semantic_highlight_gold":true},{"candidate_id":4,"state":"UNKNOWN","native_frames":60,"human_proxy_mean":2.7249999999999988,"teacher_claimed_observation_instants":[],"not_semantic_highlight_gold":true},{"candidate_id":5,"state":"UNKNOWN","native_frames":60,"human_proxy_mean":2.600000000000001,"teacher_claimed_observation_instants":[],"not_semantic_highlight_gold":true},{"candidate_id":6,"state":"UNKNOWN","native_frames":60,"human_proxy_mean":2.25,"teacher_claimed_observation_instants":[],"not_semantic_highlight_gold":true},{"candidate_id":7,"state":"KEEP","native_frames":60,"human_proxy_mean":2.0950000000000015,"teacher_claimed_observation_instants":[14,15],"not_semantic_highlight_gold":true},{"candidate_id":8,"state":"REJECT","native_frames":60,"human_proxy_mean":1.8208333333333353,"teacher_claimed_observation_instants":[16,17],"not_semantic_highlight_gold":true},{"candidate_id":9,"state":"REJECT","native_frames":60,"human_proxy_mean":1.9325000000000023,"teacher_claimed_observation_instants":[18,19],"not_semantic_highlight_gold":true},{"candidate_id":10,"state":"KEEP","native_frames":60,"human_proxy_mean":2.0208333333333357,"teacher_claimed_observation_instants":[20,21],"not_semantic_highlight_gold":true},{"candidate_id":11,"state":"UNKNOWN","native_frames":60,"human_proxy_mean":1.8483333333333316,"teacher_claimed_observation_instants":[],"not_semantic_highlight_gold":true},{"candidate_id":12,"state":"UNKNOWN","native_frames":60,"human_proxy_mean":1.6708333333333314,"teacher_claimed_observation_instants":[],"not_semantic_highlight_gold":true},{"candidate_id":13,"state":"KEEP","native_frames":60,"human_proxy_mean":2.4283333333333332,"teacher_claimed_observation_instants":[26,27],"not_semantic_highlight_gold":true},{"candidate_id":14,"state":"KEEP","native_frames":59,"human_proxy_mean":2.5889830508474563,"teacher_claimed_observation_instants":[28,29],"not_semantic_highlight_gold":true}],"labels_sha256":"efb8e804be493deb445b3b9f971ccbba6cf590134f5c90ff637c2f83b3acb129","manifest_sha256":"f6f1d0730280d64f35bb85b89b700f678f0910fef6f3eee588f85e099ca73f82","mean_human_proxy_by_state":{"REJECT":1.8766666666666687,"UNKNOWN":2.1961458333333335,"KEEP":2.2216299435028257}}],"states":{"REJECT":34,"UNKNOWN":19,"KEEP":37},"training_admitted":0,"actual_clips":6,"candidate_bins":90,"source_groups":3,"full_observation_proven":false,"human_reference_sha256":"28cc5e693e07161f2c4c7fcefb9b2d3312443f0d04535f1398b407e52fe0dd19","proxy_only_not_teacher_accuracy":true,"UNKNOWN_never_negative":true}
```


## 原文件全文：reports/annotation_iteration_20261010/observed_train.py
字节=7036；SHA256=3de0fc3e24b1748ebd839907ebd534b264884a3d635e8ac42445b79eb15dac19

```py
"""Observe the unchanged selected training entry; do not cache validation logits."""
import argparse
import hashlib
import json
import math
import runpy
import sys
from datetime import datetime, timezone
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--dataset-root',required=True)
    p.add_argument('--config',required=True)
    p.add_argument('--model',required=True)
    p.add_argument('--output',required=True)
    a=p.parse_args()
    output=Path(a.output)
    root=Path(a.dataset_root)
    assert not output.exists()
    import torch
    import transformers
    from transformers import TrainerCallback
    def emit(value):
        value={'utc':datetime.now(timezone.utc).isoformat(),**value}
        print(json.dumps(value),flush=True)
        with (output/'optimizer_observations.jsonl').open('a') as f:
            f.write(json.dumps(value)+'\n')
    def signature(model):
        h=hashlib.sha256();count=0
        for name,param in sorted(model.named_parameters()):
            if param.requires_grad:
                assert 'lora_' in name and 'visual' not in name and 'vision' not in name
                h.update(name.encode());h.update(param.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes())
                count+=param.numel()
        assert count>0
        return h.hexdigest(),count
    class Observe(TrainerCallback):
        def on_train_begin(self,args,state,control,model=None,**kwargs):
            self.initial,self.count=signature(model)
            torch.cuda.reset_peak_memory_stats()
            emit({'stage':'REAL_TRAIN_BEGIN','trainable_parameters':self.count,
                  'initial_lora_sha256':self.initial,'steps_planned':state.max_steps,
                  'prediction_loss_only':args.prediction_loss_only})
        def on_pre_optimizer_step(self,args,state,control,model=None,**kwargs):
            self.actual_step_lr=kwargs['optimizer'].param_groups[0]['lr']
            if state.global_step==0:
                total=0.0;nonzero=0
                for name,param in model.named_parameters():
                    if param.requires_grad and param.grad is not None:
                        assert bool(torch.isfinite(param.grad).all()),'Nonfinite first-step gradients'
                        norm=float(param.grad.float().norm().item())
                        total+=norm*norm;nonzero+=norm>0
                assert total>0 and nonzero>0
                emit({'stage':'FIRST_REAL_GRADIENTS','norm':math.sqrt(total),'nonzero_gradient_tensors':nonzero})
        def on_step_end(self,args,state,control,model=None,**kwargs):
            row={'stage':'REAL_OPTIMIZER_STEP','global_step':state.global_step,
                 'peak_allocated_bytes':torch.cuda.max_memory_allocated(),
                 'peak_reserved_bytes':torch.cuda.max_memory_reserved()}
            if state.global_step<=2:
                now,count=signature(model)
                assert count==self.count
                if self.actual_step_lr>0:
                    assert now!=self.initial,'Positive-LR optimizer step did not change LoRA weights'
                row.update({'lora_changed':now!=self.initial,'actual_step_learning_rate':self.actual_step_lr,'lora_sha256':now})
            emit(row)
        def on_log(self,args,state,control,logs=None,**kwargs):
            if logs:emit({'stage':'TRAINER_LOG','global_step':state.global_step,'metrics':logs})
        def on_train_end(self,args,state,control,model=None,**kwargs):
            final,count=signature(model)
            assert final!=self.initial and state.global_step>0
            emit({'stage':'REAL_TRAIN_END','global_step':state.global_step,'final_lora_sha256':final,
                  'initial_lora_sha256':self.initial,'trainable_parameters':count,
                  'peak_allocated_bytes':torch.cuda.max_memory_allocated(),
                  'peak_reserved_bytes':torch.cuda.max_memory_reserved()})
    # accelerate 1.2.1 lacks keep_torch_compile; no compiled model is used here.
    import inspect
    from accelerate import Accelerator
    from accelerate.utils.other import is_compiled_module
    unwrap=Accelerator.unwrap_model
    if 'keep_torch_compile' not in inspect.signature(unwrap).parameters:
        def compatible_unwrap(self,model,*values,keep_torch_compile=True,**options):
            assert type(keep_torch_compile) is bool and not is_compiled_module(model)
            return unwrap(self,model,*values,**options)
        Accelerator.unwrap_model=compatible_unwrap
    original=transformers.Trainer
    class ObservedTrainer(original):
        def __init__(self,*args,**kwargs):
            kwargs['args'].prediction_loss_only=True
            emit({'stage':'OBSERVED_TRAINER_ATTACHED','validation_loss_only':True})
            callbacks=list(kwargs.pop('callbacks',[]) or [])+[Observe()]
            super().__init__(*args,callbacks=callbacks,**kwargs)
        def compute_loss(self,model,inputs,return_outputs=False,**kwargs):
            result=super().compute_loss(model,inputs,return_outputs=return_outputs,**kwargs)
            loss=result[0] if return_outputs else result
            assert bool(torch.isfinite(loss).all()),'Nonfinite model loss'
            return result
    transformers.Trainer=ObservedTrainer
    sys.path.insert(0,str(root/'training_v2'))
    sys.argv=[str(root/'training_v2/train_lora.py'),'--config',a.config,'--dataset-root',a.dataset_root,
              '--model',a.model,'--output',a.output,'--train']
    source=Path(sys.argv[0]).read_text()
    old='    from transformers import Qwen3VLForConditionalGeneration, Trainer, TrainingArguments'
    new='    from transformers import Qwen3VLForConditionalGeneration, TrainingArguments\n    Trainer = __observed_trainer'
    assert source.count(old)==1
    source=source.replace(old,new)
    exec(compile(source,sys.argv[0],'exec'),{'__name__':'__main__','__file__':sys.argv[0],'__observed_trainer':ObservedTrainer})
    assert (output/'adapter/adapter_model.safetensors').exists()
    assert (output/'train_metrics.json').exists()
    observations=[json.loads(s) for s in (output/'optimizer_observations.jsonl').read_text().splitlines()]
    assert any(x.get('stage')=='FIRST_REAL_GRADIENTS' for x in observations)
    assert any(x.get('lora_changed') is True for x in observations)
    ending=[x for x in observations if x.get('stage')=='REAL_TRAIN_END']
    assert len(ending)==1
    receipt={'status':'PASS_REAL_LORA_TRAINING_FINITE_LOSS_GRADIENTS_AND_WEIGHT_CHANGES',
             'utc':datetime.now(timezone.utc).isoformat(),'result':ending[0],
             'train_metrics':json.loads((output/'train_metrics.json').read_text()),
             'validation_loss_only':True,'production_adapter_replaced':False}
    with (output/'training_acceptance.json').open('x') as f:json.dump(receipt,f,indent=2)
    print(json.dumps(receipt),flush=True)

if __name__=='__main__':main()

```


## 原文件全文：reports/annotation_iteration_20261010/predict_scores.py
字节=2894；SHA256=5116d516120fb54080bac593809efd5199be54c602fee862d5f3d5efd808861e

```py
"""One exact full-scope generation, same images/protocol for all model arms."""
import argparse,hashlib,json,sys,time
from pathlib import Path
from PIL import Image
from score_grammar import Constraint,candidates

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--model',required=True)
    p.add_argument('--data',required=True);p.add_argument('--adapter');p.add_argument('--output',required=True)
    p.add_argument('--swap',action='store_true');a=p.parse_args();root=Path(a.root)
    sys.path.insert(0,str(root/'training_v2'))
    from sft_contract import load_rows,typed_messages,decode_output
    import torch
    from transformers import AutoProcessor,Qwen3VLForConditionalGeneration
    assert torch.cuda.is_available();rows=load_rows(a.data,root);out=Path(a.output);assert not out.exists()
    processor=AutoProcessor.from_pretrained(a.model,local_files_only=True,min_pixels=4096,max_pixels=65536)
    model=Qwen3VLForConditionalGeneration.from_pretrained(a.model,local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='sdpa')
    if a.adapter:
        from peft import PeftModel
        model=PeftModel.from_pretrained(model,a.adapter,local_files_only=True)
    model=model.to('cuda').eval();ids=candidates(processor.tokenizer);torch.cuda.reset_peak_memory_stats()
    with out.open('x',encoding='utf-8') as f:
        for index,row in enumerate(rows):
            images=[]
            for path in row['images']:
                with Image.open(root/path) as im:images.append(im.convert('RGB'))
            if a.swap:images=images[1:]+images[:1]
            messages=typed_messages(row,images)[:1]
            text=processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
            encoded=processor(text=[text],images=images,return_tensors='pt').to('cuda')
            n=encoded['input_ids'].shape[1];assert n<=16384 and encoded['image_grid_thw'].shape[0]==len(images)
            constraint=Constraint(processor.tokenizer,n,len(images),ids)
            with torch.inference_mode():output=model.generate(**encoded,do_sample=False,max_new_tokens=256,prefix_allowed_tokens_fn=constraint)
            token_ids=output[0,n:].tolist();answer,obj=constraint.finish(token_ids)
            decode_output(answer,row['task'],image_count=len(images))
            record={'id':row['id'],'source_group':row['source_group'],'answer':answer,'output_token_ids':token_ids,
                    'input_tokens':n,'valid':True,'gold_in_input':False,'swapped_images':a.swap,
                    'prompt_sha256':hashlib.sha256(text.encode()).hexdigest()}
            f.write(json.dumps(record)+'\n');f.flush()
            print(json.dumps({'stage':'ACTUAL_CONSTRAINED_GENERATION','rows_done':index+1,'rows_total':len(rows),'peak_bytes':torch.cuda.max_memory_allocated()}),flush=True)
if __name__=='__main__':main()

```


## 原文件全文：reports/annotation_iteration_20261010/selector_contract.py
字节=3270；SHA256=90cb71baf6ea84d7ed812ac2e11193a751254db713da721a86fb1c178a126b0b

```py
"""Exact native sampling domains and unchanged training prompt; no inference."""
from bisect import bisect_left
from fractions import Fraction
def grid(points,start,end):
    assert all(isinstance(p,Fraction) for p in points)
    start,end=Fraction(start),Fraction(end)
    assert 0<=start<end and all(b>a for a,b in zip(points,points[1:]))
    first,stop=bisect_left(points,start),bisect_left(points,end)
    assert 0<=first<stop<=len(points)
    cursor=first;edge=start;result=[]
    while cursor<stop:
        right=min(edge+2,end);a=cursor
        while cursor<stop and points[cursor]<right:cursor+=1
        assert cursor>a,'empty sampling bin; no silent skip'
        ordinal=(a+cursor-1)//2
        result.append({'grid_index':len(result),'first_native_ordinal':a,'end_native_ordinal_exclusive':cursor,
          'sample_native_ordinal':ordinal,'sample_seconds':float(points[ordinal]),
          'start_exact':str(edge),'end_exact':str(right)})
        edge+=2
    assert result[0]['first_native_ordinal']==first and result[-1]['end_native_ordinal_exclusive']==stop
    assert all(a['end_native_ordinal_exclusive']==b['first_native_ordinal'] for a,b in zip(result,result[1:]))
    return result
def prompt(sequence):
    assert 1<=len(sequence)<=16
    descriptors='\n'.join(f'Frame {i}: native ordinal {s["sample_native_ordinal"]}, time {s["sample_seconds"]:.6f} s.' for i,s in enumerate(sequence))
    return ('Rate the visual importance of each shown frame within this ordered video sequence. '
      'Use TVSum average importance: 1 low, 3 medium, 5 high. '
      'Encode the average multiplied by 20 as an integer 20..100, preserving 0.05-point precision. '
      'Return ONLY JSON {"scores_x20":[...]} with exactly one integer per shown frame in the same order. '
      'Divide each output by 20 to recover average importance. '
      'This is sampled-frame importance, not semantic event start/end detection.\n'+descriptors)
def selftest():
    import json,numpy as np
    from pathlib import Path
    h=Path(__file__).resolve().parent;old=h.parent/'qwen8b_annotation_20261009_v1/training_v2'
    original=[json.loads(s) for s in (old/'fixed_grid_samples.jsonl').read_text().splitlines()]
    targets=[json.loads(s) for s in (old/'data/temporal_fixed_validation.jsonl').read_text().splitlines()]
    for sid in sorted({r['source_id'] for r in targets}):
        root=old.parent/'input'/sid;m=json.loads((root/'manifest.json').read_text());tb=Fraction(*m['native_time_base'])
        pts=np.load(root/'native_pts.npz')['pts'];points=[(int(p)-int(pts[0]))*tb for p in pts]
        actual=grid(points,0,Fraction(str(m['source_duration_seconds'])))
        expected=[r for r in original if r['source_id']==sid]
        assert len(actual)==len(expected)
        for a,b in zip(actual,expected):
            assert all(a[k]==b[k] for k in ('grid_index','first_native_ordinal','end_native_ordinal_exclusive','sample_native_ordinal','sample_seconds'))
        for t in (r for r in targets if r['source_id']==sid):
            seq=[actual[i] for i in t['grid_indices']]
            assert '<image>\n'*len(seq)+prompt(seq)==t['messages'][0]['content']
    print('PASS nine-source exact training-grid and all 89 prompt identities')
if __name__=='__main__':selftest()

```


## 原文件全文：reports/annotation_iteration_20261010/score_grammar.py
字节=3583；SHA256=31cbf0c2c19426ffaf953ab0d0a3d8322f7c1dbc6ee01011433fd172f71a38fd

```py
"""Finite scores grammar; exact length, integers 20..100, no output repair."""
import json

class ScoresGrammar:
    opening='{"scores_x20":['
    values=tuple(str(i) for i in range(20,101))
    def __init__(self,n):
        if type(n) is not int or not 1<=n<=16:raise ValueError('bad count')
        self.n=n
    def scan(self,text):
        if len(text)<=len(self.opening):return self.opening.startswith(text),False
        if not text.startswith(self.opening):return False,False
        count=0;number='';state='number'
        for ch in text[len(self.opening):]:
            if state=='number':
                if ch.isascii() and ch.isdigit():
                    number+=ch
                    if not any(v.startswith(number) for v in self.values):return False,False
                elif ch in ',]' and number in self.values:
                    count+=1;number=''
                    if ch==',' and count<self.n:continue
                    if ch==']' and count==self.n:state='close';continue
                    return False,False
                else:return False,False
            elif state=='close':
                if ch!='}':return False,False
                state='done'
            else:return False,False
        return True,state=='done'
    def valid_prefix(self,t):return self.scan(t)[0]
    def complete(self,t):return self.scan(t)[1]

def candidates(tokenizer):
    chars=set('{}[]":,scores_x2013456789')
    out=[]
    for i in sorted(set(tokenizer.get_vocab().values())):
        t=tokenizer.decode([i],skip_special_tokens=False,clean_up_tokenization_spaces=False)
        if t and t.isascii() and set(t)<=chars:out.append(i)
    return tuple(out)

class Constraint:
    def __init__(self,tok,prompt,n,ids):
        self.tok=tok;self.prompt=prompt;self.g=ScoresGrammar(n);self.ids=ids;self.cache={}
        eos=tok.eos_token_id;self.eos=[eos] if type(eos) is int else list(eos)
    def __call__(self,batch,seq):
        ids=tuple(seq.tolist()[self.prompt:])
        if ids in self.cache:return self.cache[ids]
        text=self.tok.decode(ids,skip_special_tokens=False,clean_up_tokenization_spaces=False)
        if self.g.complete(text):out=self.eos
        elif self.g.valid_prefix(text):
            out=[]
            for i in self.ids:
                t=self.tok.decode((*ids,i),skip_special_tokens=False,clean_up_tokenization_spaces=False)
                if t.startswith(text) and len(t)>len(text) and self.g.valid_prefix(t):out.append(i)
        else:out=[]
        if not out:raise ValueError('constrained dead end; no fallback')
        self.cache[ids]=out;return out
    def finish(self,ids):
        ids=list(ids)
        if ids and ids[-1] in self.eos:ids.pop()
        if any(i in self.eos for i in ids):raise ValueError('early EOS')
        text=self.tok.decode(ids,skip_special_tokens=False,clean_up_tokenization_spaces=False)
        if not self.g.complete(text):raise ValueError('incomplete output')
        return text,json.loads(text)

def selftest():
    for n in range(1,17):
        g=ScoresGrammar(n)
        for value in (20,21,99,100):
            s=json.dumps({'scores_x20':[value]*n},separators=(',',':'))
            assert g.complete(s) and all(g.valid_prefix(s[:i]) for i in range(len(s)+1))
        for bad in (19,101,True,20.0):
            assert not g.complete(json.dumps({'scores_x20':[bad]*n},separators=(',',':')))
        for count in (0,n+1):assert not g.complete(json.dumps({'scores_x20':[20]*count},separators=(',',':')))
    print('PASS exact count/range/all canonical prefixes')
if __name__=='__main__':selftest()

```


## 原文件全文：reports/annotation_iteration_20261010/selector_threshold.json
字节=336；SHA256=b42137063a73cc710bbfab3c54a77f2570452728bdefd1b7fa6e63c93347651e

```json
{
  "threshold_x20": 49,
  "rule": "TRAIN_HUMAN_FIXED_GRID_NEAREST_RANK_80TH_PERCENTILE; scores>=threshold; empty allowed",
  "train_file_sha256": "3eb93e2585679f0c24d71b5d13ece101b79aea53b15671948362581d116db62f",
  "fixed_bin_extension": "Entire label-independent 2-second ordinal domain; assumption not semantic boundary gold"
}
```


## 原文件全文：reports/annotation_iteration_20261010/temporal_config.json
字节=560；SHA256=ea5fc869a3498739283257214ceb012d3c48b4b590a5c315bb7062d377546b15

```json
{
  "model_config_sha256": "5cd452860dc1e9c29dd71cc3cef7f39b338b7a40793f7a260655c2d3568f3661",
  "min_pixels": 4096,
  "max_input_tokens": 16384,
  "lora_rank": 8,
  "lora_alpha": 16,
  "lora_dropout": 0.05,
  "gradient_accumulation_steps": 4,
  "learning_rate": 0.0001,
  "epochs": 3,
  "status": "FROZEN_ONE_SUFFICIENT_OPTIMIZATION_RECIPE",
  "task": "temporal_tvsum_importance_x20",
  "max_pixels": 65536,
  "train_file": "training_v2/data/temporal_fixed_train.jsonl",
  "validation_file": "training_v2/data/temporal_fixed_validation.jsonl"
}
```


## 原文件全文：reports/annotation_iteration_20261010/evaluate_iteration_v2.py
字节=8808；SHA256=813b8430755cba49e8debf455f99cfdbe61a235e084e31b0b60c751f3c248b9e

```py
"""Independent full-denominator source-paired quality and native interval audit."""
import collections,hashlib,json,math
from pathlib import Path
import numpy as np
from audit_native_domains import audit
H=Path(__file__).resolve().parent;OLD=H.parent/'qwen8b_annotation_20261009_v1/training_v2'
def rows(p):return [json.loads(s) for s in p.read_text(encoding='utf-8-sig').splitlines() if s.strip()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rank(v):
    values=np.array(v);order=np.argsort(values,kind='stable');out=np.empty(len(v));first=0
    while first<len(v):
        end=first+1
        while end<len(v) and values[order[end]]==values[order[first]]:end+=1
        out[order[first:end]]=(first+end-1)/2;first=end
    return out
def rho(a,b):
    if len(set(a))<2 or len(set(b))<2:return 0.0,True
    return float(np.corrcoef(rank(a),rank(b))[0,1]),False
def main():
    protocol=json.loads((H/'cpu_quality_acceptance_protocol.json').read_text())
    assert all(sha(H/name)==digest for name,digest in protocol['code_sha256'].items())
    native_domain_audit=audit(OLD)
    targets=rows(OLD/'data/temporal_fixed_validation.jsonl');assert len(targets)==89
    train=rows(OLD/'data/temporal_fixed_train.jsonl')
    train_scores=sorted(v for r in train for v in json.loads(r['messages'][1]['content'])['scores_x20'])
    train_mean=sum(train_scores)/len(train_scores)
    cutoff=train_scores[math.ceil(.8*len(train_scores))-1]
    threshold_file=H/'selector_threshold.json'
    frozen={'threshold_x20':cutoff,'rule':'TRAIN_HUMAN_FIXED_GRID_NEAREST_RANK_80TH_PERCENTILE; scores>=threshold; empty allowed',
            'train_file_sha256':sha(OLD/'data/temporal_fixed_train.jsonl'),'fixed_bin_extension':'Entire label-independent 2-second ordinal domain; assumption not semantic boundary gold'}
    if threshold_file.exists():assert json.loads(threshold_file.read_text())==frozen
    else:
        with threshold_file.open('x') as f:json.dump(frozen,f,indent=2)
    arms={};ids={r['id'] for r in targets};gold_by_source=collections.defaultdict(list)
    for t in targets:
        values=json.loads(t['messages'][1]['content'])['scores_x20']
        for ordinal,g,value in zip(t['native_ordinals'],t['grid_indices'],values):gold_by_source[t['source_id']].append((ordinal,g,value))
    for source in gold_by_source:gold_by_source[source].sort()
    for name in ('new','base','pilot','production_B'):
        data=rows(H/'results'/f'{name}_predictions.jsonl');lookup={r['id']:r for r in data}
        assert len(data)==len(lookup)==89 and set(lookup)==ids
        source_values=collections.defaultdict(list)
        for t in targets:
            p=lookup[t['id']];answer=json.loads(p['answer'])
            assert p['source_group']==t['source_group'] and p['swapped_images'] is False and p['valid'] is True
            assert set(answer)=={'scores_x20'} and len(answer['scores_x20'])==len(t['images']) and p['gold_in_input'] is False
            assert all(type(v) is int and 20<=v<=100 for v in answer['scores_x20'])
            for ordinal,g,pred,gold in zip(t['native_ordinals'],t['grid_indices'],answer['scores_x20'],json.loads(t['messages'][1]['content'])['scores_x20']):
                source_values[t['source_id']].append((ordinal,g,pred,gold))
        metrics={}
        for source,values in source_values.items():
            values.sort();n=len(values);assert n==len(gold_by_source[source]);pred=[v[2] for v in values];gold=[v[3] for v in values]
            corr,constant=rho(pred,gold);k=math.ceil(.15*n)
            indices=sorted(range(n),key=lambda i:(-pred[i],values[i][0]))[:k]
            selected=[v for v in values if v[2]>=cutoff]
            metrics[source]={'frames':n,'spearman':corr,'constant_ranking':constant,'top15_count':k,
              'top15_human_mean':sum(gold[i] for i in indices)/k/20,'mae':sum(abs(a-b) for a,b in zip(pred,gold))/n/20,
              'train_mean_constant_mae':sum(abs(train_mean-v) for v in gold)/n/20,
              'threshold_selected_fraction':len(selected)/n,'threshold_selected_human_mean':sum(v[3] for v in selected)/len(selected)/20 if selected else None,
              'threshold_low_human_fraction':sum(v[3]<60 for v in selected)/len(selected) if selected else None,
              'predictions':values}
        arms[name]={'rows':89,'all_outputs_valid':True,'source_metrics':metrics,
                    'macro_spearman':sum(v['spearman'] for v in metrics.values())/9,
                    'macro_top15_human_mean':sum(v['top15_human_mean'] for v in metrics.values())/9,
                    'macro_mae':sum(v['mae'] for v in metrics.values())/9,
                    'production_B_scope':'Same adapter under new image-score prompt; NOT original B native-video pipeline comparison' if name=='production_B' else None}
    sources=sorted(gold_by_source);delta_rho=[arms['new']['source_metrics'][s]['spearman']-arms['base']['source_metrics'][s]['spearman'] for s in sources]
    delta_utility=[arms['new']['source_metrics'][s]['top15_human_mean']-arms['base']['source_metrics'][s]['top15_human_mean'] for s in sources]
    rng=np.random.default_rng(20261010);draw=rng.integers(0,9,size=(10000,9))
    bootstrap={name:np.quantile(np.asarray(v)[draw].mean(axis=1),[.025,.975]).tolist() for name,v in [('macro_spearman',delta_rho),('macro_top15_utility',delta_utility)]}
    gate=sum(delta_rho)/9>0 and sum(delta_utility)/9>0 and sum(v>0 for v in delta_rho)>=5
    vision=json.loads((H/'results/vision_dependency.json').read_text());gate=gate and vision['visual_dependency_gate']
    native_blocks=rows(OLD/'human_native_blocks.jsonl');grid=rows(OLD/'fixed_grid_samples.jsonl')
    bins={ (s['source_id'],s['grid_index']):s for s in grid if s['split']=='validation'}
    native={}
    for arm,values in arms.items():
        aggregate={}
        for source,m in values['source_metrics'].items():
            intervals=[(bins[(source,v[1])]['first_native_ordinal'],bins[(source,v[1])]['end_native_ordinal_exclusive']) for v in m['predictions'] if v[2]>=cutoff]
            blocks=[b for b in native_blocks if b['source_id']==source];total=sum(b['end_native_ordinal_exclusive']-b['first_native_ordinal'] for b in blocks)
            selected=gold_sum=low=0;high_total=high_selected=0
            for b in blocks:
                a,z=b['first_native_ordinal'],b['end_native_ordinal_exclusive'];human=b['worker_score_sum']/20
                count=sum(max(0,min(z,stop)-max(a,start)) for start,stop in intervals)
                assert 0<=count<=z-a
                selected+=count;gold_sum+=count*human;low+=count if human<3 else 0
                if human>=3:high_total+=z-a;high_selected+=count
            aggregate[source]={'native_frames':total,'selected_frames':selected,'selected_fraction':selected/total,
                'selected_human_mean':gold_sum/selected if selected else None,'selected_human_below3_fraction':low/selected if selected else None,
                'threshold3_human_proxy_precision':high_selected/selected if selected else 0,'threshold3_human_proxy_recall':high_selected/high_total if high_total else None,
                'threshold3_human_proxy_f':2*high_selected/(selected+high_total) if selected+high_total else 1,
                'AIC_score':False,'bin_expansion_is_assumption':True}
        native[arm]=aggregate
    native_macro_f={arm:sum(m['threshold3_human_proxy_f'] for m in metrics.values())/9 for arm,metrics in native.items()}
    delta_f=[native['new'][s]['threshold3_human_proxy_f']-native['base'][s]['threshold3_human_proxy_f'] for s in sources]
    bootstrap['native_macro_proxy_f']=np.quantile(np.asarray(delta_f)[draw].mean(axis=1),[.025,.975]).tolist()
    stage2_pass=bool(gate and native_macro_f['new']>native_macro_f['base'])
    report={'status':'PASS_FROZEN_STAGE2_GATE' if stage2_pass else 'FAIL_FROZEN_STAGE2_GATE_KEEP_PRODUCTION',
      'research_pass':bool(gate),'stage2_pass':stage2_pass,'native_macro_proxy_f':native_macro_f,
      'native_domain_audit':native_domain_audit,
      'cpu_quality_protocol_sha256':sha(H/'cpu_quality_acceptance_protocol.json'),
      'native_proxy_f_deltas':dict(zip(sources,delta_f)),
      'arms':arms,'source_deltas':dict(zip(sources,zip(delta_rho,delta_utility))),'source_bootstrap95':bootstrap,
      'worst_spearman_delta':min(delta_rho),'positive_sources':sum(x>0 for x in delta_rho),
      'visual_dependency':vision,'native_selector_analysis':native,'selector_threshold':frozen,
      'development_seen_before':True,'independent_AIC_quality_reference':None,'no_validation_based_recipe_retry':True}
    with (H/'quality_result.json').open('x') as f:json.dump(report,f,indent=2)
    print(json.dumps({k:v for k,v in report.items() if k not in ('arms','native_selector_analysis','visual_dependency')},indent=2))
if __name__=='__main__':main()

```


## 原文件全文：reports/annotation_iteration_20261010/cpu_quality_acceptance_protocol.json
字节=756；SHA256=feaf6d912651663811892919b7e142ae02ff9140b7d54acbb4738490d8775057

```json
{
  "utc": "2026-10-09T17:26:44.807072+00:00",
  "new_dev_answers_read": false,
  "code_sha256": {
    "evaluate_iteration_v2.py": "813b8430755cba49e8debf455f99cfdbe61a235e084e31b0b60c751f3c248b9e",
    "audit_native_domains.py": "465498e1ecad980064c583a56bf0f8ccb0f697e7373829bb2c79fbf64e72f0c5",
    "selector_contract.py": "90cb71baf6ea84d7ed812ac2e11193a751254db713da721a86fb1c178a126b0b",
    "PROSPECTIVE_STAGE2.md": "cf883128f91d33d406b46c37fd1194379c463d834e5bc0c8424644e3e7c88ab3",
    "selector_threshold.json": "b42137063a73cc710bbfab3c54a77f2570452728bdefd1b7fa6e63c93347651e"
  },
  "stage2_rule": "research_pass AND exact native partitions AND 9-source equal macro proxy F new > base",
  "threshold_fixed_before_predictions": 49
}
```


## 原文件全文：reports/annotation_iteration_20261010/PROSPECTIVE_STAGE2.md
字节=1537；SHA256=cf883128f91d33d406b46c37fd1194379c463d834e5bc0c8424644e3e7c88ab3

```md
# 研究门之后的实际选择器投入门

新增门仅用于第二阶段投入，第一阶段原三条件和训练配方不改。此文件写入时尚未产生本轮新89行dev预测，也未读取任何新dev结果。

阈值已只从训练39源固定网格human scores的nearest-rank80分位冻结：scores_x20>=49，允许空。绝非每视频topk。15%只用于排序诊断。固定将每个2秒中点预测赋给同格全部native ordinals，这是插值假设，不称真实事件边界。

在完整9源原人类向量下，按human mean>=3定义明确标明的TVSum代理二元参考（不是AIC金标），评价扩段后的macro F、低分误选、空源和选中率，逐源报告。

仅第一阶段研究门和视觉依赖门均通过，且实际选择器macro代理F严格优于同输入同grammar基座、所有human native域完整、全dev合法，才投入非测试8实际pipeline。任何失败保留，不依据dev改阈值或换checkpoint，不冒称旧B native pipeline已被打败。

bootstrap可能跨0，要说明弱证据；源数9不足可靠官方提分推断。non-test8只验证实际输入/native时间/合法空/裁剪源场衔接，不能充当无标签质量金标。完整426只作为用户接受风险的竞争试验，在本轮授权下仅一次。

原B adapter在新imagescore prompt下的诊断结果不等于原B production pipeline成绩。最终候选如生成则明确新image score selector、原空间8B场、共享base计一次、实际新adapter参数、无旧timeadapter被加载。

```


## 原文件全文：reports/annotation_iteration_20261010/CONTEST_PROTOCOL.md
字节=1916；SHA256=ebcd8132a8742c79d02b587d18b6a6a782bcf6fb81b4f7c5acb0058d2084b556

```md
# 本版实际候选协议

第一/第二阶段冻结门真实通过，全部4×89回答接受，vision10/12且NLL delta>0。TVSum已见dev排序提升不是AIC分；native proxy F的95区间跨0，候选仅实验试交，保留历史37.66保底和原B生产。

本版不再训练或调阈值。实际新rank8 adapter SHA1f39afb662f77661f008bc6000a054b9d838b988558ef0b762e2d98975d94933，237步训练，实际8,774,791,408总参数、共享base一次。只使用这个time adapter，原时间B不加载；空间沿原base8B完整、time-independent源场。

原注册decoder/source97色彩白名单/源SHA/native Fraction PTS/geometry保持，OrdinalReader的BGR显式一次转RGB，分别绑定BGR/RGB/PNG/实际pixel_tensor/input_ids签名。2秒格从注册scope首起，Fraction精确域中原生序号中点，16有序images块及实际尾块，与TVSum训练原prompt/processor(4096..65536pixels)/grammar/greedy/256output/16384input完全一致。阈值49从train冻结，允许空，不强制topk；整格选取为插值假设，非语义边界真值。精确分区与原source-field合法域有差异则停止，不加epsilon或裁帧。

非测试8先prepare→真实GPU→独立CPU实际PNG/processor/token/raw/parser回放→完整旧源场compose→11strict/ZIP。仅其通过后完整426同一路线一次。新输入CPU采样和原生像素核验是本版新准备，不重启任何旧成功模型任务。所有旧空间anchor完整校验后过滤新selected，所有426视频含合法空皆保留；缺口/不合法/模型失败停止，不能转空、补框或删选帧。

所有GPU经现有唯一共享runner/账本，动态资源与冲突准入。新控制小量文件经在线Mac跳板到既有Linux项目；不传新视频/模型，不公开，不官网上传、不替换生产。最终完整ZIP验收后只经Mac取回小量候选及回执，真实字节/SHA和旧37.66保底分别标识。

```


## 原文件全文：reports/annotation_iteration_20261010/contest_engine.py
字节=16252；SHA256=2d016f19bd2d4b7ed5925e02ef1cca144675b2e3c79d2d13ac0b8da7611389ba

```py
"""New image-score time selector; immutable original source/crop field, strict ZIP."""
import argparse,hashlib,json,subprocess,sys,time
from bisect import bisect_left
from fractions import Fraction
from pathlib import Path
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent
RUN=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
B4=RUN/'b_score_aligned_package_v4';sys.path.insert(0,str(B4))
import common as c
import selector_contract as sc
from score_grammar import Constraint,candidates
MODEL=RUN/'models/Qwen3-VL-8B-Instruct';ADAPTER=H/'train/adapter'
ADAPTER_SHA='1f39afb662f77661f008bc6000a054b9d838b988558ef0b762e2d98975d94933'
ADAPTER_CONFIG_SHA='dcd134aecf4573d0f462d70adcf96b8beeba6bd76e62ec6c5bf57593fe79a8e1'
EXPECTED={
 'nontest':dict(zip(('field_frames.jsonl','field_shots.jsonl','anchor_requests.jsonl','anchor_output.jsonl'),(
 'c4b53cb7d95442ecaa4c8fa6b82b027fd5779370230a2b97f8c8796526386aed','cf4a873053bd2baf24343043eb36f835a5853ce232b409489915329f161c0375',
 'f630e725ddff54c590a4062c39b98c1b7233773b8c0a391f271378ac157283a7','1ffd45d72c723ec71f973d6b24f5e72d052ddf3f6e3b51150a2e68bacfc1532d'))),
 'rematch':dict(zip(('field_frames.jsonl','field_shots.jsonl','anchor_requests.jsonl','anchor_output.jsonl'),(
 '17ba37aadc4cf705e1ff95a78a58d8befcab9e34f7132ef0775f1ed1df0d8bca','8e81df10c685527145069cd9c65316ab6341c9da7d6e39bb282ed6c60ce12f1e',
 '9cb7c4e36597dc8ae723ac3b686b2c3b1f04d5982503478fdf19ee72b18c4798','8f83cd967d7d1f95243ac4ae3cddc7fdb78abb3d4842a78f81f6b187fb1562ab')))}
def sha(p):return c.sha(p)
def user(sequence,images):
    text='<image>\n'*len(images)+sc.prompt(sequence);parts=text.split('<image>');content=[]
    for i,part in enumerate(parts):
        if part:content.append({'type':'text','text':part})
        if i<len(images):content.append({'type':'image','image':images[i]})
    return [{'role':'user','content':content}]
def out(scope):return H/'contest_v1'/(scope+'_01')
def data(scope):
    c.verify();item,manifest,clocks=c.inputs(scope)
    assert sha(ADAPTER/'adapter_model.safetensors')==ADAPTER_SHA
    assert sha(ADAPTER/'adapter_config.json')==ADAPTER_CONFIG_SHA
    cache=B4/(scope+'_01');assert all(sha(cache/name)==digest for name,digest in EXPECTED[scope].items())
    schedule=c.read(cache/'schedule.stage.json');spatial=c.read(cache/'spatial.stage.json')
    assert schedule['status']=='PASS_TIME_INDEPENDENT_SOURCE_FIELD' and schedule['max_gap']==8 and schedule['temporal_selection_used_for_boundaries'] is False
    assert spatial['status']=='PASS_STRICT_SOURCE_FIELD_SPATIAL' and spatial['invalid']==0 and spatial['time_adapter_enabled'] is False
    assert spatial['logical_parameters']==8767123696
    return item,manifest,clocks,cache
def binding(scope):
    b=c.read(out(scope)/'prepared.json')
    assert all(sha(H/name)==digest for name,digest in b['code_sha256'].items())
    assert sha(out(scope)/'blocks.jsonl')==b['blocks_sha256'] and sha(out(scope)/'samples.jsonl')==b['samples_sha256']
    assert sha(H/'quality_result.json')==b['quality_sha256'] and c.read(H/'quality_result.json')['stage2_pass'] is True
    return b
def prepare(scope):
    import production
    from field_contract import build_field_requests
    from frame_contract import legacy_manifest
    from package_contract import keyset
    item,manifest,clocks,cache=data(scope);dest=out(scope);assert not dest.exists();dest.mkdir(parents=True)
    assert c.read(H/'quality_result.json')['stage2_pass'] is True
    domain=production.field_frames(manifest,clocks);cached=c.rows(cache/'field_frames.jsonl')
    assert len(domain)==len(keyset(domain)) and len(cached)==len(keyset(cached))
    assert {(r['video_id'],r['source_frame']):r for r in domain}=={(r['video_id'],r['source_frame']):r for r in cached}
    shots=c.rows(cache/'field_shots.jsonl');requests=c.rows(cache/'anchor_requests.jsonl');outputs=c.rows(cache/'anchor_output.jsonl')
    assert build_field_requests(cached,shots,8)==requests and len(outputs)==len(requests)==spatial_rows(cache)
    assert keyset(shots)==keyset(domain)
    for request,answer in zip(requests,outputs):
        assert answer['status']=='MODEL_OK' and answer['used_fallback'] is False and request['anchor_request_sha256']==answer['anchor_request_sha256']
        assert request['expected_pixel_sha256']==answer['decoded_pixel_sha256']
    pixel_lookup={(s['video_id'],s['source_frame']):s['decoded_pixel_sha256'] for s in shots}
    del cached,shots,requests,outputs
    samples=[];blocks=[]
    for record in sorted(manifest['records'],key=lambda r:r['video_id']):
        vid=record['video_id'];clock=clocks[vid];assert sha(record['source_path'])==record['source_sha256']
        start=Fraction(str(record['scope_start_sec']));end=clock['duration'] if scope=='rematch' else Fraction(str(record['scope_end_sec']))
        g=sc.grid(clock['pts'],start,end)
        lo=bisect_left([float(p) for p in clock['pts']],record['scope_start_sec'])
        hi=bisect_left([float(p) for p in clock['pts']],record['scope_end_sec'])
        assert g[0]['first_native_ordinal']==lo and g[-1]['end_native_ordinal_exclusive']==hi
        reader=production.OrdinalReader(record,clock);folder=dest/'frames'/vid;folder.mkdir(parents=True)
        try:
            for s in g:
                ordinal=s['sample_native_ordinal'];bgr,pixel=reader.get(ordinal)
                assert pixel==pixel_lookup[(vid,ordinal)] and bgr.shape==(record['height'],record['width'],3)
                rgb=np.ascontiguousarray(bgr[:,:,::-1]);assert np.array_equal(rgb[:,:,::-1],bgr)
                path=folder/(str(ordinal)+'.png');Image.fromarray(rgb).save(path)
                with Image.open(path) as im:assert np.array_equal(np.asarray(im.convert('RGB')),rgb)
                s.update(video_id=vid,source_sha256=record['source_sha256'],clock_record_sha256=clock['clock_record_sha256'],
                  image=str(path.relative_to(H)),image_sha256=sha(path),bgr_pixel_sha256=pixel,
                  rgb_pixel_sha256=hashlib.sha256(rgb.tobytes()).hexdigest(),color_operation='ONE_EXPLICIT_BGR_TO_RGB_AFTER_REGISTERED_DECODER')
        finally:reader.close()
        samples.extend(g)
        for first in range(0,len(g),16):
            seq=g[first:first+16];blocks.append({'id':vid+':score:'+str(first//16),'video_id':vid,'samples':seq,'prompt':sc.prompt(seq)})
        c.progress(dest,dict(stage='PREPARE_EXACT_IMAGE_SELECTOR',videos_done=len({s['video_id'] for s in samples}),videos_total=len(manifest['records']),samples=len(samples)))
    c.write_rows(dest/'samples.jsonl',samples);c.write_rows(dest/'blocks.jsonl',blocks)
    c.write(dest/'prepared.json',dict(status='PASS_EXACT_SOURCE_FIELD_PIXELS_RGB_GRID_AND_BLOCKS',videos=len(manifest['records']),samples=len(samples),blocks=len(blocks),
      code_sha256={name:sha(H/name) for name in ('contest_engine.py','selector_contract.py','score_grammar.py')},
      blocks_sha256=sha(dest/'blocks.jsonl'),samples_sha256=sha(dest/'samples.jsonl'),quality_sha256=sha(H/'quality_result.json'),
      manifest_sha256=item['manifest_sha256'],registry_sha256=item['registry_sha256'],source_field_sha256=EXPECTED[scope],
      adapter_sha256=ADAPTER_SHA,adapter_config_sha256=ADAPTER_CONFIG_SHA,threshold_x20=49,scope=scope,spatial_model_calls=0,old_spatial_costs_preserved=True))
def spatial_rows(cache):return c.read(cache/'spatial.stage.json')['rows']
def processor():
    from transformers import AutoProcessor
    return AutoProcessor.from_pretrained(MODEL,local_files_only=True,min_pixels=4096,max_pixels=65536)
def encode(p,block):
    images=[]
    for s in block['samples']:
        path=H/s['image'];assert sha(path)==s['image_sha256']
        with Image.open(path) as im:rgb=im.convert('RGB');rgb.load()
        assert hashlib.sha256(np.asarray(rgb).tobytes()).hexdigest()==s['rgb_pixel_sha256'];images.append(rgb)
    assert block['prompt']==sc.prompt(block['samples'])
    messages=user(block['samples'],images);text=p.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
    e=p(text=[text],images=images,return_tensors='pt');n=e['input_ids'].shape[1]
    assert n<=16384 and e['image_grid_thw'].shape[0]==len(images)
    signature=hashlib.sha256(e['pixel_values'].contiguous().numpy().tobytes()).hexdigest()
    return e,{'input_tokens':n,'prompt_sha256':hashlib.sha256(text.encode()).hexdigest(),'pixel_tensor_sha256':signature,
      'image_grid_thw':e['image_grid_thw'].tolist(),'input_ids_sha256':hashlib.sha256(e['input_ids'].contiguous().numpy().tobytes()).hexdigest()}
def generate(scope):
    import torch
    from transformers import Qwen3VLForConditionalGeneration
    from peft import PeftModel
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation();data(scope);b=binding(scope);dest=out(scope);assert not (dest/'raw.jsonl').exists()
    p=processor();ids=candidates(p.tokenizer)
    model=PeftModel.from_pretrained(Qwen3VLForConditionalGeneration.from_pretrained(MODEL,local_files_only=True,
      torch_dtype=torch.bfloat16,attn_implementation='sdpa'),ADAPTER,local_files_only=True).to('cuda').eval()
    total=sum(x.numel() for x in model.parameters());assert total==8774791408
    assert list(model.peft_config)==['default'] and model.active_adapters==['default']
    pc=model.peft_config['default'];assert pc.r==8 and pc.lora_alpha==16 and set(pc.target_modules)=={'q_proj','k_proj','v_proj','o_proj'}
    actual_adapter={'active_adapters':model.active_adapters,'rank':pc.r,'alpha':pc.lora_alpha,'target_modules':sorted(pc.target_modules),
      'parameter_count':sum(x.numel() for name,x in model.named_parameters() if 'lora_' in name)}
    assert actual_adapter['parameter_count']==7667712
    for parameter in model.parameters():parameter.requires_grad_(False)
    planned=c.rows(dest/'blocks.jsonl');assert len(planned)==b['blocks']
    with (dest/'raw.jsonl').open('x',encoding='utf-8') as f:
        for i,block in enumerate(planned):
            e,sig=encode(p,block);constraint=Constraint(p.tokenizer,sig['input_tokens'],len(block['samples']),ids)
            with torch.inference_mode():answer=model.generate(**e.to('cuda'),do_sample=False,max_new_tokens=256,prefix_allowed_tokens_fn=constraint)
            tokens=answer[0,sig['input_tokens']:].tolist();text,obj=constraint.finish(tokens)
            row={'id':block['id'],'video_id':block['video_id'],'answer':text,'output_token_ids':tokens,**sig}
            f.write(json.dumps(row)+'\n');f.flush()
            c.progress(dest,dict(stage='ACTUAL_NEW_SELECTOR_GENERATION',done=i+1,total=len(planned)))
    c.write(dest/'generation.json',dict(status='PASS_ALL_NEW_SELECTOR_BLOCKS',model_calls=len(planned),adapter_sha256=ADAPTER_SHA,
      logical_parameters=total,shared_base_counted_once=True,new_optimizer_updates_this_inference=0,training_optimizer_steps=237,
      old_B_time_adapter_used=False,adapter_config_sha256=ADAPTER_CONFIG_SHA,actual_adapter=actual_adapter,
      raw_sha256=sha(dest/'raw.jsonl'),prepared_sha256=sha(dest/'prepared.json')))
def replay(scope):
    import torch
    data(scope);b=binding(scope);dest=out(scope);g=c.read(dest/'generation.json')
    assert g['raw_sha256']==sha(dest/'raw.jsonl') and g['prepared_sha256']==sha(dest/'prepared.json')
    p=processor();ids=candidates(p.tokenizer);raw=c.rows(dest/'raw.jsonl');planned=c.rows(dest/'blocks.jsonl')
    assert len(raw)==len(planned)==b['blocks'] and [r['id'] for r in raw]==[r['id'] for r in planned]
    for block,row in zip(planned,raw):
        e,sig=encode(p,block);assert all(row[k]==v for k,v in sig.items()) and row['video_id']==block['video_id']
        text,obj=Constraint(p.tokenizer,sig['input_tokens'],len(block['samples']),ids).finish(row['output_token_ids'])
        assert text==row['answer'] and set(obj)=={'scores_x20'} and len(obj['scores_x20'])==len(block['samples'])
        assert all(type(v) is int and 20<=v<=100 for v in obj['scores_x20'])
    assert not torch.cuda.is_initialized()
    c.write(dest/'cpu_replay.json',dict(status='PASS_ALL_ACTUAL_PROCESSOR_PIXELS_TOKENS_RAW_PARSER_CPU',blocks=len(raw),raw_sha256=sha(dest/'raw.jsonl'),new_model_calls=0,CUDA_initialized=False))
def finish(scope):
    from production import field_frames
    from field_contract import compose_from_field
    from frame_contract import legacy_manifest
    from package_contract import keyset,validate_predictions,package
    item,manifest,clocks,cache=data(scope);b=binding(scope);dest=out(scope)
    replayed=c.read(dest/'cpu_replay.json');assert replayed['raw_sha256']==sha(dest/'raw.jsonl')
    samples=c.rows(dest/'samples.jsonl');blocks=c.rows(dest/'blocks.jsonl');raw=c.rows(dest/'raw.jsonl')
    assert len(blocks)==len(raw)==b['blocks'] and [(s['video_id'],s['grid_index']) for r in blocks for s in r['samples']]==[(s['video_id'],s['grid_index']) for s in samples]
    chosen=set();scored=[]
    for block,row in zip(blocks,raw):
        assert block['id']==row['id'];scores=json.loads(row['answer'])['scores_x20'];assert len(scores)==len(block['samples'])
        for s,score in zip(block['samples'],scores):
            assert type(score) is int and 20<=score<=100
            scored.append(dict(video_id=s['video_id'],grid_index=s['grid_index'],score_x20=score,selected=score>=49,
              first_native_ordinal=s['first_native_ordinal'],end_native_ordinal_exclusive=s['end_native_ordinal_exclusive']))
            if score>=49:chosen.update((s['video_id'],ordinal) for ordinal in range(s['first_native_ordinal'],s['end_native_ordinal_exclusive']))
    domain=field_frames(manifest,clocks);assert chosen<=keyset(domain);selected=[r for r in domain if (r['video_id'],r['source_frame']) in chosen]
    assert len(selected)==len(chosen)
    for record in manifest['records']:assert sha(record['source_path'])==record['source_sha256']
    pred,provenance=compose_from_field(legacy_manifest(manifest),selected,c.rows(cache/'field_shots.jsonl'),c.rows(cache/'anchor_requests.jsonl'),c.rows(cache/'anchor_output.jsonl'))
    c.write_rows(dest/'selected.jsonl',selected);c.write_rows(dest/'scored_bins.jsonl',scored)
    c.write_rows(dest/'predictions.jsonl',pred);c.write_rows(dest/'provenance.jsonl',provenance)
    c.write(dest/'metadata.json',dict(records=manifest['records'],errors=[]))
    checks=validate_predictions(legacy_manifest(manifest),pred,keyset(selected),provenance)
    pending=dest/'candidate_IMAGE_SCORE_237STEP_8B.PENDING.zip';checks.update(package(dest/'predictions.jsonl',pending))
    subprocess.run([sys.executable,'-B',str(RUN/'baseline_a_pts_v1/vendor/independent_validate.py'),
      '--strict-loader-root',str(RUN/'baseline_a_pts_v1/vendor/frozen_strict_loader'),'--metadata',str(dest/'metadata.json'),
      '--selected',str(dest/'selected.jsonl'),'--predictions',str(dest/'predictions.jsonl'),'--provenance',str(dest/'provenance.jsonl'),
      '--zip',str(pending),'--report',str(dest/'independent_validation.json')],check=True)
    report=c.read(dest/'independent_validation.json');assert report['status']=='PASS_INDEPENDENT_STRICT_VALIDATION' and len(report['checks'])==11 and all(report['checks'].values())
    candidate=dest/'candidate_IMAGE_SCORE_237STEP_8B.zip';pending.rename(candidate)
    c.write(dest/'package_receipt.json',dict(status='PASS_COMPLETE_IMAGE_SCORE_237STEP_8B_EXPERIMENTAL_ZIP',scope=scope,
      candidate=str(candidate),zip_bytes=candidate.stat().st_size,zip_sha256=sha(candidate),videos=len(pred),selected_frames=len(selected),
      empty_videos=sum(not r['predictions'] for r in pred),samples=len(samples),blocks=len(blocks),adapter_sha256=ADAPTER_SHA,
      logical_parameters=8774791408,training_optimizer_steps=237,old_spatial_source_field=EXPECTED[scope],spatial_model_calls=0,
      official_score=None,uploaded=False,production_replaced=False,independent_validation_sha256=sha(dest/'independent_validation.json'),
      quality_evidence='SEEN_TVSUM_DEVELOPMENT_PROXY_ONLY; NATIVE_PROXY_F_CI_CROSSES_ZERO; AIC_GENERALIZATION_UNKNOWN'))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','generate','replay','finish']);p.add_argument('scope',choices=['nontest','rematch']);a=p.parse_args()
    globals()[a.mode](a.scope)

```


## 原文件全文：reports/annotation_iteration_20261010/agy_short_clips_v2.py
字节=9437；SHA256=a8d7dda1dd3f67a7c7aa3a309ecb737b9980d5adf02eaa36553b0b867bf86d61

```py
"""Six fixed 30-second teacher checks, native PTS mapping, no guessed times."""
import av,hashlib,json,subprocess
from pathlib import Path
from fractions import Fraction
from datetime import datetime,timezone
H=Path(__file__).resolve().parent;OLD=H.parent/'qwen8b_annotation_20261009_v1'
AGY=Path('C:/Users/33056/AppData/Local/agy/bin/agy.exe');MODEL='gemini-3.8-flash-high'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def prepare():
    manifests=[json.loads(p.read_text()) for p in sorted((OLD/'input').glob('*/manifest.json'))]
    selected=[m for m in manifests if m['source_id'] in ('37rzWOQsNIw','0tmA_C6XwfM')]
    categories={m['category'] for m in selected}
    extra=next(m for m in manifests if m['split']=='train' and m['category'] not in categories and m['source_duration_seconds']>80)
    selected.append(extra);assert len(selected)==3 and all(m['split']=='train' for m in selected)
    jobs=[]
    for m in selected:
        sid=m['source_id'];src=OLD/'input'/sid/m['media_file'];assert sha(src)==m['media_sha256']
        # Fixed time domains are selected without teacher labels or human scores.
        domains=[(20,50),(max(50,int(m['source_duration_seconds']/2)),max(50,int(m['source_duration_seconds']/2))+30)]
        for j,(start,end) in enumerate(domains):
            folder=H/'agy_v2'/f'{sid}_{j:02d}';folder.mkdir(parents=True,exist_ok=False)
            dest=folder/'clip.mp4';mapping=[];original=[]
            with av.open(str(src)) as inp,av.open(str(dest),'w') as out:
                source=inp.streams.video[0];rate=source.average_rate;base=source.time_base;first=source.start_time or 0
                stream=out.add_stream('libx264',rate=source.average_rate)
                stream.width=source.codec_context.width;stream.height=source.codec_context.height
                stream.pix_fmt='yuv420p';stream.options={'crf':'18','preset':'fast'}
                stream.time_base=base;stream.codec_context.time_base=base
                offset=None
                for ordinal,frame in enumerate(inp.decode(source)):
                    source_time=Fraction(frame.pts-first)*base
                    if source_time<start:continue
                    if source_time>=end:break
                    if offset is None:offset=frame.pts
                    rel=Fraction(frame.pts-offset)*base
                    rgb=frame.to_image();original.append((ordinal,frame.pts,source_time,rgb))
                    new=av.VideoFrame.from_image(rgb);new.pts=frame.pts-offset;new.time_base=base
                    for packet in stream.encode(new):out.mux(packet)
                    mapping.append({'ordinal':ordinal,'source_pts':frame.pts,'global_seconds_exact':str(source_time),
                                    'local_seconds_exact':str(rel)})
                for packet in stream.encode():out.mux(packet)
            assert mapping
            with av.open(str(dest)) as check:
                decoded=[Fraction(f.pts)*f.time_base for f in check.decode(video=0)]
            assert len(decoded)==len(mapping)
            assert all(t==Fraction(r['local_seconds_exact']) for t,r in zip(decoded,mapping))
            anchors=[]
            for k in (0,len(original)//2,len(original)-1):
                ordinal,pts,t,rgb=original[k];p=folder/f'original_anchor_{k:04d}.png';rgb.save(p)
                anchors.append({'ordinal':ordinal,'global_seconds_exact':str(t),'local_seconds_exact':mapping[k]['local_seconds_exact'],
                                'file':str(p),'sha256':sha(p)})
            actual_duration=Fraction(mapping[-1]['local_seconds_exact'])+Fraction(1,1)/rate
            bins=[]
            for k in range(15):
                members=[r for r in mapping if 2*k<=Fraction(r['local_seconds_exact'])<min(2*k+2,actual_duration)]
                assert members
                bins.append({'candidate_id':k,'local_start':2*k,'local_end_exclusive':min(2*k+2,float(actual_duration)),
                             'first_native_ordinal':members[0]['ordinal'],'last_native_ordinal':members[-1]['ordinal']})
            manifest={'source_id':sid,'source_group':m['source_group'],'split':'train','source_sha256':m['media_sha256'],
                      'clip_file':str(dest),'clip_sha256':sha(dest),'source_mapping':mapping,'candidates':bins,'anchors':anchors,
                      'duration_seconds':float(actual_duration),'no_audio':True,'derived_video_encoding':'libx264 crf18 yuv420p; all sequential source frames; unchanged geometry; native PTS exact; lossy pixels declared'}
            save(folder/'manifest.json',manifest);jobs.append(str(folder))
    save(H/'agy_v2/jobs.json',{'jobs':jobs,'expected':6,'train_only':True,'selected_without_labels':True})
def run():
    if not (H/'agy_v2/jobs.json').exists():prepare()
    jobs=json.loads((H/'agy_v2/jobs.json').read_text())['jobs'];receipts=[]
    for path in jobs:
        folder=Path(path);m=json.loads((folder/'manifest.json').read_text());out=folder/'labels.json'
        if (folder/'acceptance.json').exists():
            r=json.loads((folder/'acceptance.json').read_text());assert sha(out)==r['raw_sha256'];receipts.append(r);continue
        assert not out.exists() and not (folder/'stream.jsonl').exists(),'Partial attempt preserved; no automatic replay'
        task=f'''用户明确授权高光标注。只处理{m['source_id']}的这一个30秒派生短视频。先view_file原生读取{(folder/'manifest.json').as_posix()}，再view_file原生直接读{(folder/'clip.mp4').as_posix()}。
禁止终端/代码/外部API/浏览器/联网/其他模型或子代理；不要读取原人类评分、旧标签、PNG或其他视频。视频无音频。
这次只做固定候选格分类，不自由报起止秒。顶层source_id、input_sha256(clip的sha)、native_video_accepted、actual_tool_name、observation_scope、limitations、candidates。
必须按manifest的15个candidate_id依序逐条返回candidate_id、state(KEEP/REJECT/UNKNOWN)、visible_evidence、actually_observed_local_seconds(精确不了就空列表)、confidence(LOW/MEDIUM/HIGH)。KEEP意味着实际可见的重要动作、结果或叙事核心；REJECT仅用于实际观察到且明确冗余/过渡的格，不是把未观察当低分。抽样未覆盖、动作不清或边界无法定位就UNKNOWN。不要声称逐帧/完整连续观看。若工具只给概览而不能准确归属时间格，应全部UNKNOWN且解释，不能编造时间。
仅write_to_file写{out.as_posix()}，已存在不能覆盖。工具失败写{(folder/'failure.json').as_posix()}后停止。'''
        (folder/'prompt.txt').write_text(task,encoding='utf-8')
        cmd=[str(AGY),'--model',MODEL,'--mode','accept-edits','--sandbox','--output-format','stream-json','--log-file',str(folder/'agy.log'),'-p',task]
        with (folder/'stream.jsonl').open('xb') as stdout,(folder/'stderr.txt').open('xb') as stderr:
            r=subprocess.run(cmd,cwd=H,stdout=stdout,stderr=stderr)
        save(folder/'terminal.json',{'exit_code':r.returncode,'utc':datetime.now(timezone.utc).isoformat()})
        assert r.returncode==0 and out.exists()
        events=[json.loads(s) for s in (folder/'stream.jsonl').read_text(encoding='utf-8-sig').splitlines() if s.strip()]
        init=next(e['init'] for e in events if e.get('event')=='init');assert init['model']==MODEL
        result=next(e['result'] for e in reversed(events) if e.get('event')=='result');assert result['status']=='SUCCESS'
        calls=[e['step_update'] for e in events if e.get('step_update',{}).get('state')=='DONE' and e['step_update'].get('tool_name')=='view_file'
               and e['step_update'].get('tool_info',{}).get('parameters',{}).get('AbsolutePath','').replace('\\','/').endswith('/clip.mp4')]
        assert calls
        doc=json.loads(out.read_text(encoding='utf-8-sig'));assert doc['source_id']==m['source_id'] and doc['input_sha256']==m['clip_sha256']
        assert doc['native_video_accepted'] is True and doc['actual_tool_name']=='view_file'
        assert [x['candidate_id'] for x in doc['candidates']]==list(range(15))
        for x in doc['candidates']:
            assert x['state'] in ('KEEP','REJECT','UNKNOWN') and x['visible_evidence']
            for t in x['actually_observed_local_seconds']:assert type(t) in (int,float) and 0<=t<m['duration_seconds']
        receipt={'status':'NATIVE_CLIP_AND_SCHEMA_PASS_SEMANTIC_REVIEW_PENDING','source_id':m['source_id'],'folder':str(folder),
                 'raw_sha256':sha(out),'stream_sha256':sha(folder/'stream.jsonl'),'states':{s:sum(x['state']==s for x in doc['candidates']) for s in ('KEEP','REJECT','UNKNOWN')},
                 'full_observation_proven':False,'training_admitted':False,'conversation_id':result['conversation_id']}
        save(folder/'acceptance.json',receipt);receipts.append(receipt)
        (H/'agy_v2/progress.json').write_text(json.dumps({'done':len(receipts),'expected':6,'receipts':receipts},indent=2),encoding='utf-8')
        print(json.dumps(receipt),flush=True)
    save(H/'agy_v2/completion.json',{'status':'SIX_NATIVE_CLIP_TEACHER_RESPONSES_SEMANTIC_REVIEW_PENDING','receipts':receipts,'training_admitted':False})
if __name__=='__main__':run()

```


## 原文件全文：reports/annotation_iteration_20261010/quality_result.json
字节=635982；SHA256=33d2bed1dc542741ceb324ec036ba021e8aefc77e646c5773258baacdb55bbfb

```json
{"status":"PASS_FROZEN_STAGE2_GATE","research_pass":true,"stage2_pass":true,"native_macro_proxy_f":{"new":0.13041783838617307,"base":0.041488836750274656,"pilot":0.041488836750274656,"production_B":0.05057355290021679},"native_domain_audit":{"status":"PASS_EXACT_NATIVE_PARTITIONS_AND_TARGET_GRID_COVERAGE","sources":{"-esJrBWj2d8":{"native_frames":6912,"human_blocks":115,"grid_bins":116,"complete_partition":true,"exact_target_coverage":true,"media_sha256":"811186cdec40ef58049f0cc951c07a9f6f7d2b5cb27511e01094b829bbd10a9e"},"4wU_LUjG5Ic":{"native_frames":4005,"human_blocks":83,"grid_bins":84,"complete_partition":true,"exact_target_coverage":true,"media_sha256":"2779762f2c332931c9fb4e61783b81df6e34b487dc3a94c882781c981e6c4869"},"EYqVtI9YWJA":{"native_frames":5939,"human_blocks":97,"grid_bins":100,"complete_partition":true,"exact_target_coverage":true,"media_sha256":"6ffcc966ab00a6096d7b256cffd09408efa7db376df7732644f875b8ff27f390"},"J0nA4VgnoCo":{"native_frames":14019,"human_blocks":284,"grid_bins":293,"complete_partition":true,"exact_target_coverage":true,"media_sha256":"65c9490a2166d17736c38ed077f250290c548b1da8f1801f10ff53fad8e84a5b"},"JKpqYvAdIsw":{"native_frames":3802,"human_blocks":76,"grid_bins":77,"complete_partition":true,"exact_target_coverage":true,"media_sha256":"da63a55d05c49f042699b366f3026ba77c8695208b40eb40b506867604caf905"},"Yi4Ij2NM7U4":{"native_frames":9731,"human_blocks":202,"grid_bins":203,"complete_partition":true,"exact_target_coverage":true,"media_sha256":"26ec9f71ea771e5601a1f5c963fa425681ae2f86b3dfca483a64d58b5a65feb9"},"cjibtmSLxQ4":{"native_frames":19406,"human_blocks":314,"grid_bins":324,"complete_partition":true,"exact_target_coverage":true,"media_sha256":"43183ef7f35bfcbc39c122be797fdee5031103862c7c7da3b9ab74d222c79c9d"},"i3wAGJaaktw":{"native_frames":4700,"human_blocks":76,"grid_bins":79,"complete_partition":true,"exact_target_coverage":true,"media_sha256":"7a8cc3f5415702ce254200db00650cb42981ba0c0fa5b5ef4a910f7c66c69c21"},"sTEELN-vY30":{"native_frames":4468,"human_blocks":73,"grid_bins":75,"complete_partition":true,"exact_target_coverage":true,"media_sha256":"b6767caf3ddb2a1750672427315fe61c63a854de26ca707f5e5041bf45557d48"}},"file_sha256":{"human_native_blocks.jsonl":"28cc5e693e07161f2c4c7fcefb9b2d3312443f0d04535f1398b407e52fe0dd19","fixed_grid_samples.jsonl":"3d1cd6ea55dc009940bec3c89428d5dfece33df6b0317c5b4f4b8a96bcf92c1b","temporal_fixed_validation.jsonl":"fdcbfb1abda89ed29e016fa3973aeef4cedd16348248e57c97bcbde202c1b76a"}},"cpu_quality_protocol_sha256":"feaf6d912651663811892919b7e142ae02ff9140b7d54acbb4738490d8775057","native_proxy_f_deltas":{"-esJrBWj2d8":0.09803921568627452,"4wU_LUjG5Ic":0.0,"EYqVtI9YWJA":-0.03596796131177271,"J0nA4VgnoCo":0.0,"JKpqYvAdIsw":0.0,"Yi4Ij2NM7U4":0.48828976034858396,"cjibtmSLxQ4":0.0,"i3wAGJaaktw":0.0,"sTEELN-vY30":0.25},"arms":{"new":{"rows":89,"all_outputs_valid":true,"source_metrics":{"-esJrBWj2d8":{"frames":116,"spearman":0.48179393831832923,"constant_ranking":false,"top15_count":18,"top15_human_mean":2.213888888888889,"mae":0.42672413793103453,"train_mean_constant_mae":0.39834066410151,"threshold_selected_fraction":0.11206896551724138,"threshold_selected_human_mean":2.2346153846153847,"threshold_low_human_fraction":0.9230769230769231,"predictions":[[29,0,32,39],[89,1,32,40],[149,2,32,48],[209,3,32,37],[269,4,32,36],[329,5,32,28],[389,6,32,29],[449,7,32,42],[509,8,32,42],[569,9,32,51],[629,10,32,36],[689,11,32,36],[749,12,32,38],[809,13,32,41],[869,14,32,28],[929,15,32,33],[989,16,32,38],[1049,17,32,40],[1109,18,32,45],[1169,19,32,43],[1229,20,32,41],[1289,21,32,56],[1349,22,32,59],[1409,23,32,50],[1469,24,32,60],[1529,25,32,54],[1589,26,32,51],[1649,27,32,48],[1709,28,32,53],[1769,29,32,46],[1829,30,32,42],[1889,31,32,46],[1949,32,32,49],[2009,33,30,57],[2069,34,30,67],[2129,35,30,62],[2189,36,30,62],[2249,37,30,62],[2309,38,30,61],[2369,39,32,49],[2429,40,32,39],[2489,41,32,35],[2549,42,32,39],[2609,43,32,33],[2669,44,32,45],[2729,45,32,34],[2789,46,32,39],[2849,47,32,36],[2909,48,50,37],[2969,49,50,36],[3029,50,50,39],[3089,51,50,42],[3149,52,50,36],[3209,53,50,39],[3269,54,50,46],[3329,55,50,49],[3389,56,50,61],[3449,57,50,48],[3509,58,50,54],[3569,59,50,48],[3629,60,50,46],[3689,61,40,43],[3749,62,37,42],[3809,63,37,52],[3869,64,30,33],[3929,65,30,28],[3989,66,30,31],[4049,67,30,31],[4109,68,30,30],[4169,69,30,33],[4229,70,30,34],[4289,71,30,31],[4349,72,30,31],[4409,73,30,40],[4469,74,30,29],[4529,75,30,31],[4589,76,30,32],[4649,77,30,32],[4709,78,30,41],[4769,79,30,41],[4829,80,30,26],[4889,81,30,27],[4949,82,30,28],[5009,83,30,30],[5069,84,30,29],[5129,85,30,29],[5189,86,30,26],[5249,87,30,30],[5309,88,30,31],[5369,89,30,26],[5429,90,30,29],[5489,91,30,25],[5549,92,30,27],[5609,93,30,32],[5669,94,30,34],[5729,95,30,26],[5789,96,32,28],[5849,97,32,34],[5909,98,32,32],[5969,99,32,34],[6029,100,32,43],[6089,101,32,40],[6149,102,32,42],[6209,103,32,45],[6269,104,32,41],[6329,105,32,43],[6389,106,32,42],[6449,107,32,48],[6509,108,32,41],[6569,109,32,35],[6629,110,32,29],[6689,111,32,28],[6749,112,26,30],[6809,113,25,29],[6869,114,26,30],[6905,115,25,30]]},"4wU_LUjG5Ic":{"frames":84,"spearman":0.5219194739656956,"constant_ranking":false,"top15_count":13,"top15_human_mean":2.523076923076923,"mae":0.4130952380952381,"train_mean_constant_mae":0.4194405573132151,"threshold_selected_fraction":0.0,"threshold_selected_human_mean":null,"threshold_low_human_fraction":null,"predictions":[[23,0,24,39],[71,1,26,28],[119,2,24,32],[167,3,26,44],[215,4,30,57],[263,5,30,60],[311,6,30,52],[359,7,30,46],[407,8,30,53],[455,9,30,50],[503,10,30,50],[551,11,30,43],[599,12,30,43],[647,13,30,41],[695,14,30,36],[743,15,30,38],[791,16,27,38],[839,17,26,35],[887,18,47,44],[935,19,47,41],[983,20,46,40],[1030,21,26,34],[1078,22,26,37],[1126,23,26,37],[1174,24,37,45],[1222,25,37,49],[1270,26,42,68],[1318,27,42,58],[1366,28,42,41],[1414,29,42,50],[1462,30,42,43],[1510,31,32,28],[1558,32,30,24],[1606,33,30,22],[1654,34,30,23],[1702,35,37,35],[1750,36,37,30],[1798,37,27,27],[1846,38,27,26],[1894,39,27,31],[1942,40,27,28],[1990,41,27,29],[2037,42,27,28],[2085,43,27,29],[2133,44,27,27],[2181,45,32,41],[2229,46,32,38],[2277,47,32,43],[2325,48,36,44],[2373,49,34,47],[2421,50,32,37],[2469,51,43,58],[2517,52,43,66],[2565,53,43,61],[2613,54,43,47],[2661,55,30,30],[2709,56,30,27],[2757,57,30,28],[2805,58,30,26],[2853,59,30,28],[2901,60,30,27],[2949,61,30,37],[2997,62,30,40],[3044,63,30,45],[3092,64,42,48],[3140,65,40,44],[3188,66,30,33],[3236,67,43,46],[3284,68,42,47],[3332,69,37,50],[3380,70,35,48],[3428,71,43,36],[3476,72,42,37],[3524,73,42,38],[3572,74,42,41],[3620,75,42,39],[3668,76,42,40],[3716,77,42,27],[3764,78,30,41],[3812,79,30,30],[3860,80,26,31],[3908,81,26,28],[3956,82,25,25],[3992,83,25,25]]},"cjibtmSLxQ4":{"frames":324,"spearman":0.3978810297066022,"constant_ranking":false,"top15_count":49,"top15_human_mean":2.3428571428571425,"mae":0.4492283950617284,"train_mean_constant_mae":0.5084463136475473,"threshold_selected_fraction":0.015432098765432098,"threshold_selected_human_mean":2.08,"threshold_low_human_fraction":1.0,"predictions":[[29,0,32,41],[89,1,31,31],[149,2,30,39],[209,3,30,29],[269,4,30,71],[329,5,30,41],[389,6,30,42],[449,7,30,41],[509,8,30,45],[569,9,30,38],[629,10,30,48],[689,11,30,46],[749,12,30,37],[809,13,30,50],[869,14,30,42],[929,15,30,54],[989,16,32,43],[1048,17,32,28],[1108,18,30,39],[1168,19,32,53],[1228,20,32,51],[1288,21,32,66],[1348,22,32,67],[1408,23,32,36],[1468,24,32,46],[1528,25,32,42],[1588,26,32,43],[1648,27,32,36],[1708,28,32,44],[1768,29,32,34],[1828,30,32,63],[1888,31,32,61],[1948,32,50,39],[2008,33,50,29],[2067,34,30,33],[2127,35,30,34],[2187,36,30,30],[2247,37,47,68],[2307,38,47,33],[2367,39,47,57],[2427,40,47,54],[2487,41,47,70],[2547,42,30,42],[2607,43,30,32],[2667,44,30,33],[2727,45,30,34],[2787,46,30,35],[2847,47,30,40],[2907,48,46,42],[2967,49,42,46],[3027,50,43,49],[3086,51,40,50],[3146,52,40,44],[3206,53,36,27],[3266,54,36,27],[3326,55,36,26],[3386,56,36,25],[3446,57,36,27],[3506,58,36,27],[3566,59,36,27],[3626,60,36,31],[3686,61,36,65],[3746,62,36,71],[3806,63,36,29],[3866,64,27,39],[3926,65,26,41],[3986,66,26,40],[4045,67,26,39],[4105,68,38,39],[4165,69,38,29],[4225,70,37,30],[4285,71,37,45],[4345,72,33,42],[4405,73,42,56],[4465,74,37,39],[4525,75,37,56],[4585,76,34,44],[4645,77,34,45],[4705,78,35,38],[4765,79,34,42],[4825,80,31,38],[4885,81,30,41],[4945,82,30,42],[5005,83,30,41],[5064,84,30,28],[5124,85,30,48],[5184,86,30,51],[5244,87,30,61],[5304,88,30,63],[5364,89,30,62],[5424,90,30,45],[5484,91,30,57],[5544,92,30,46],[5604,93,30,43],[5664,94,30,50],[5724,95,30,61],[5784,96,50,46],[5844,97,50,49],[5904,98,50,45],[5964,99,48,54],[6024,100,47,53],[6083,101,40,45],[6143,102,40,50],[6203,103,40,50],[6263,104,38,35],[6323,105,38,33],[6383,106,38,34],[6443,107,38,31],[6503,108,36,34],[6563,109,36,39],[6623,110,35,43],[6683,111,35,33],[6743,112,36,31],[6803,113,35,36],[6863,114,34,31],[6923,115,35,44],[6983,116,46,50],[7042,117,30,28],[7102,118,30,41],[7162,119,30,40],[7222,120,30,41],[7282,121,30,24],[7342,122,30,27],[7402,123,30,28],[7462,124,30,26],[7522,125,43,45],[7582,126,30,21],[7642,127,30,21],[7702,128,32,33],[7762,129,36,53],[7822,130,40,53],[7882,131,37,52],[7942,132,33,50],[8002,133,32,48],[8061,134,32,24],[8121,135,32,41],[8181,136,33,52],[8241,137,32,52],[8301,138,32,46],[8361,139,32,28],[8421,140,32,24],[8481,141,32,23],[8541,142,32,22],[8601,143,32,22],[8661,144,30,26],[8721,145,30,25],[8781,146,32,34],[8841,147,30,41],[8901,148,30,42],[8961,149,30,29],[9021,150,29,22],[9080,151,29,27],[9140,152,29,37],[9200,153,30,46],[9260,154,30,47],[9320,155,30,35],[9380,156,30,44],[9440,157,30,45],[9500,158,30,42],[9560,159,30,45],[9620,160,32,34],[9680,161,30,51],[9740,162,30,22],[9800,163,30,21],[9860,164,30,31],[9920,165,30,28],[9980,166,30,27],[10039,167,30,23],[10099,168,30,28],[10159,169,30,28],[10219,170,30,24],[10279,171,30,23],[10339,172,30,27],[10399,173,30,23],[10459,174,30,23],[10519,175,30,28],[10579,176,32,32],[10639,177,30,31],[10699,178,30,22],[10759,179,30,23],[10819,180,30,32],[10879,181,30,42],[10939,182,30,28],[10999,183,30,25],[11058,184,30,26],[11118,185,30,27],[11178,186,30,26],[11238,187,30,28],[11298,188,30,38],[11358,189,30,35],[11418,190,30,63],[11478,191,30,46],[11538,192,37,59],[11598,193,36,73],[11658,194,34,53],[11718,195,33,33],[11778,196,30,29],[11838,197,32,35],[11898,198,30,31],[11958,199,30,32],[12018,200,30,33],[12077,201,30,32],[12137,202,30,40],[12197,203,30,36],[12257,204,30,30],[12317,205,30,21],[12377,206,30,22],[12437,207,30,22],[12497,208,32,21],[12557,209,31,21],[12617,210,30,23],[12677,211,30,22],[12737,212,30,21],[12797,213,30,24],[12857,214,30,31],[12917,215,30,27],[12977,216,30,26],[13036,217,30,28],[13096,218,30,30],[13156,219,30,29],[13216,220,30,29],[13276,221,30,29],[13336,222,30,26],[13396,223,30,25],[13456,224,32,29],[13516,225,30,24],[13576,226,29,24],[13636,227,32,27],[13696,228,36,29],[13756,229,36,36],[13816,230,40,36],[13876,231,42,32],[13936,232,42,32],[13996,233,40,33],[14055,234,37,32],[14115,235,36,32],[14175,236,32,30],[14235,237,32,34],[14295,238,32,29],[14355,239,33,29],[14415,240,32,27],[14475,241,33,31],[14535,242,32,32],[14595,243,27,29],[14655,244,27,28],[14715,245,27,28],[14775,246,27,28],[14835,247,30,29],[14895,248,30,29],[14955,249,30,27],[15015,250,27,28],[15074,251,27,27],[15134,252,27,28],[15194,253,30,34],[15254,254,27,32],[15314,255,27,29],[15374,256,32,30],[15434,257,33,29],[15494,258,33,34],[15554,259,27,71],[15614,260,47,57],[15674,261,43,49],[15734,262,43,75],[15794,263,33,36],[15854,264,42,59],[15914,265,33,68],[15974,266,33,36],[16033,267,33,65],[16093,268,33,73],[16153,269,33,28],[16213,270,33,37],[16273,271,33,34],[16333,272,48,46],[16393,273,43,40],[16453,274,40,37],[16513,275,40,45],[16573,276,40,47],[16633,277,43,48],[16693,278,40,47],[16753,279,37,28],[16813,280,33,28],[16873,281,30,26],[16933,282,30,33],[16993,283,30,32],[17052,284,30,34],[17112,285,30,32],[17172,286,30,36],[17232,287,30,32],[17292,288,32,34],[17352,289,33,51],[17412,290,37,55],[17472,291,37,31],[17532,292,37,51],[17592,293,37,50],[17652,294,42,60],[17712,295,40,64],[17772,296,40,56],[17832,297,27,30],[17892,298,27,28],[17952,299,27,29],[18012,300,27,27],[18071,301,27,26],[18131,302,27,27],[18191,303,40,55],[18251,304,32,32],[18311,305,32,44],[18371,306,32,46],[18431,307,32,31],[18491,308,32,48],[18551,309,32,51],[18611,310,32,54],[18671,311,32,40],[18731,312,32,39],[18791,313,32,50],[18851,314,32,53],[18911,315,32,47],[18971,316,32,46],[19030,317,32,45],[19090,318,32,36],[19150,319,32,27],[19210,320,30,29],[19270,321,30,27],[19330,322,30,30],[19383,323,30,30]]},"EYqVtI9YWJA":{"frames":100,"spearman":0.7459540968737468,"constant_ranking":false,"top15_count":15,"top15_human_mean":2.5033333333333334,"mae":0.32599999999999996,"train_mean_constant_mae":0.5319150340715502,"threshold_selected_fraction":0.1,"threshold_selected_human_mean":2.625,"threshold_low_human_fraction":0.9,"predictions":[[29,0,36,36],[89,1,33,32],[149,2,33,33],[209,3,33,43],[269,4,32,23],[329,5,32,28],[389,6,32,25],[449,7,32,26],[509,8,32,39],[569,9,42,51],[629,10,43,54],[689,11,43,46],[749,12,43,54],[809,13,32,23],[869,14,32,25],[929,15,32,39],[989,16,50,47],[1048,17,50,54],[1108,18,50,46],[1168,19,30,24],[1228,20,30,25],[1288,21,46,42],[1348,22,46,36],[1408,23,46,52],[1468,24,30,31],[1528,25,30,29],[1588,26,30,29],[1648,27,30,29],[1708,28,30,44],[1768,29,30,38],[1828,30,30,42],[1888,31,30,40],[1948,32,32,26],[2008,33,32,31],[2067,34,32,32],[2127,35,32,28],[2187,36,32,29],[2247,37,32,34],[2307,38,32,44],[2367,39,32,39],[2427,40,32,38],[2487,41,32,34],[2547,42,32,42],[2607,43,32,47],[2667,44,32,23],[2727,45,32,26],[2787,46,32,25],[2847,47,32,23],[2907,48,32,34],[2967,49,40,66],[3027,50,42,49],[3086,51,40,43],[3146,52,40,41],[3206,53,40,42],[3266,54,40,41],[3326,55,40,48],[3386,56,40,48],[3446,57,40,60],[3506,58,27,25],[3566,59,27,26],[3626,60,27,31],[3686,61,27,27],[3746,62,27,27],[3806,63,27,27],[3866,64,30,28],[3926,65,30,28],[3986,66,52,53],[4045,67,52,54],[4105,68,52,52],[4165,69,52,55],[4225,70,52,47],[4285,71,52,47],[4345,72,52,70],[4405,73,47,37],[4465,74,28,23],[4525,75,28,23],[4585,76,28,22],[4645,77,28,31],[4705,78,28,28],[4765,79,28,53],[4825,80,46,59],[4885,81,46,55],[4945,82,44,58],[5005,83,45,57],[5064,84,44,57],[5124,85,43,61],[5184,86,43,55],[5244,87,37,40],[5304,88,43,67],[5364,89,43,63],[5424,90,43,61],[5484,91,43,40],[5544,92,43,44],[5604,93,43,46],[5664,94,43,55],[5724,95,43,44],[5784,96,30,36],[5844,97,28,27],[5904,98,27,28],[5936,99,27,28]]},"i3wAGJaaktw":{"frames":79,"spearman":0.44833238118557756,"constant_ranking":false,"top15_count":12,"top15_human_mean":2.05,"mae":0.5360759493670886,"train_mean_constant_mae":0.5376996042956035,"threshold_selected_fraction":0.0,"threshold_selected_human_mean":null,"threshold_low_human_fraction":null,"predictions":[[29,0,32,31],[89,1,30,31],[149,2,37,64],[209,3,36,55],[269,4,34,48],[329,5,34,58],[389,6,32,41],[449,7,32,40],[509,8,32,41],[569,9,32,44],[629,10,32,39],[689,11,32,36],[749,12,32,37],[809,13,32,37],[869,14,32,55],[929,15,32,55],[989,16,32,52],[1048,17,32,52],[1108,18,32,50],[1168,19,32,50],[1228,20,32,45],[1288,21,32,50],[1348,22,32,47],[1408,23,32,43],[1468,24,32,43],[1528,25,32,49],[1588,26,32,48],[1648,27,32,52],[1708,28,32,64],[1768,29,32,44],[1828,30,32,44],[1888,31,32,54],[1948,32,37,56],[2008,33,36,38],[2067,34,36,33],[2127,35,36,35],[2187,36,36,34],[2247,37,36,36],[2307,38,36,40],[2367,39,36,37],[2427,40,36,37],[2487,41,36,36],[2547,42,36,35],[2607,43,36,38],[2667,44,36,66],[2727,45,36,58],[2787,46,36,72],[2847,47,36,67],[2907,48,42,59],[2967,49,42,67],[3027,50,27,22],[3086,51,26,22],[3146,52,26,21],[3206,53,26,23],[3266,54,26,21],[3326,55,26,24],[3386,56,42,32],[3446,57,42,33],[3506,58,42,32],[3566,59,42,31],[3626,60,42,31],[3686,61,42,36],[3746,62,42,28],[3806,63,42,23],[3866,64,27,22],[3926,65,26,21],[3986,66,26,25],[4045,67,26,23],[4105,68,26,22],[4165,69,26,23],[4225,70,26,30],[4285,71,26,26],[4345,72,26,22],[4405,73,26,22],[4465,74,27,36],[4525,75,27,31],[4585,76,27,39],[4645,77,27,33],[4687,78,27,33]]},"J0nA4VgnoCo":{"frames":293,"spearman":0.5295177158066975,"constant_ranking":false,"top15_count":44,"top15_human_mean":2.6522727272727273,"mae":0.4590443686006826,"train_mean_constant_mae":0.5519635838503165,"threshold_selected_fraction":0.0,"threshold_selected_human_mean":null,"threshold_low_human_fraction":null,"predictions":[[23,0,30,27],[71,1,30,30],[119,2,29,25],[167,3,29,30],[215,4,29,25],[263,5,29,27],[311,6,29,25],[359,7,29,27],[407,8,29,26],[455,9,29,25],[503,10,29,29],[551,11,30,31],[599,12,30,51],[647,13,30,53],[695,14,30,46],[743,15,30,53],[791,16,32,48],[839,17,31,47],[887,18,30,41],[935,19,30,25],[983,20,30,25],[1030,21,27,31],[1078,22,27,29],[1126,23,27,36],[1174,24,27,26],[1222,25,27,25],[1270,26,27,26],[1318,27,27,26],[1366,28,27,27],[1414,29,27,30],[1462,30,27,33],[1510,31,27,38],[1558,32,32,30],[1606,33,32,47],[1654,34,32,38],[1702,35,30,30],[1750,36,30,30],[1798,37,30,29],[1846,38,30,25],[1894,39,30,29],[1942,40,30,29],[1990,41,30,30],[2037,42,30,27],[2085,43,30,32],[2133,44,30,29],[2181,45,30,26],[2229,46,30,31],[2277,47,30,68],[2325,48,37,68],[2373,49,36,65],[2421,50,34,26],[2469,51,32,29],[2517,52,27,27],[2565,53,26,28],[2613,54,32,33],[2661,55,32,54],[2709,56,26,33],[2757,57,25,35],[2805,58,26,26],[2853,59,26,27],[2901,60,26,28],[2949,61,26,29],[2997,62,27,28],[3044,63,27,28],[3092,64,38,35],[3140,65,37,29],[3188,66,32,25],[3236,67,30,26],[3284,68,30,25],[3332,69,30,27],[3380,70,30,26],[3428,71,30,26],[3476,72,30,26],[3524,73,30,25],[3572,74,30,26],[3620,75,30,26],[3668,76,30,27],[3716,77,30,26],[3764,78,27,27],[3812,79,27,27],[3860,80,30,28],[3908,81,28,30],[3956,82,28,42],[4004,83,28,33],[4051,84,28,41],[4099,85,28,39],[4147,86,28,47],[4195,87,28,34],[4243,88,28,43],[4291,89,28,36],[4339,90,28,40],[4387,91,28,36],[4435,92,28,35],[4483,93,28,36],[4531,94,28,35],[4579,95,28,44],[4627,96,32,35],[4675,97,32,45],[4723,98,32,44],[4771,99,32,43],[4819,100,32,45],[4867,101,32,47],[4915,102,32,46],[4963,103,32,40],[5011,104,32,48],[5058,105,32,42],[5106,106,32,41],[5154,107,32,42],[5202,108,32,43],[5250,109,32,41],[5298,110,32,39],[5346,111,32,41],[5394,112,32,44],[5442,113,30,34],[5490,114,27,30],[5538,115,27,33],[5586,116,28,36],[5634,117,30,48],[5682,118,30,33],[5730,119,30,51],[5778,120,32,54],[5826,121,30,59],[5874,122,30,56],[5922,123,30,53],[5970,124,30,56],[6018,125,30,54],[6065,126,30,53],[6113,127,30,28],[6161,128,30,28],[6209,129,30,30],[6257,130,30,30],[6305,131,30,30],[6353,132,30,39],[6401,133,30,62],[6449,134,30,54],[6497,135,30,55],[6545,136,30,74],[6593,137,30,70],[6641,138,30,52],[6689,139,30,38],[6737,140,30,38],[6785,141,30,38],[6833,142,30,35],[6881,143,30,41],[6929,144,32,42],[6977,145,32,57],[7024,146,30,59],[7072,147,30,56],[7120,148,32,56],[7168,149,32,58],[7216,150,32,63],[7264,151,32,57],[7312,152,32,58],[7360,153,32,56],[7408,154,32,53],[7456,155,32,51],[7504,156,32,47],[7552,157,32,52],[7600,158,32,48],[7648,159,32,52],[7696,160,42,75],[7744,161,42,71],[7792,162,42,59],[7840,163,42,57],[7888,164,42,59],[7936,165,42,63],[7984,166,42,55],[8031,167,42,53],[8079,168,42,66],[8127,169,42,68],[8175,170,42,70],[8223,171,42,57],[8271,172,42,51],[8319,173,42,55],[8367,174,42,57],[8415,175,42,53],[8463,176,48,57],[8511,177,47,56],[8559,178,45,53],[8607,179,43,46],[8655,180,43,44],[8703,181,43,49],[8751,182,43,59],[8799,183,43,59],[8847,184,43,57],[8895,185,37,46],[8943,186,43,44],[8991,187,43,59],[9038,188,43,46],[9086,189,43,43],[9134,190,43,36],[9182,191,43,48],[9230,192,37,45],[9278,193,37,49],[9326,194,36,47],[9374,195,36,46],[9422,196,36,45],[9470,197,36,44],[9518,198,36,46],[9566,199,36,44],[9614,200,36,47],[9662,201,36,43],[9710,202,36,44],[9758,203,36,46],[9806,204,36,44],[9854,205,36,63],[9902,206,36,56],[9950,207,36,30],[9998,208,30,32],[10045,209,30,32],[10093,210,29,31],[10141,211,29,30],[10189,212,29,30],[10237,213,28,34],[10285,214,28,29],[10333,215,28,32],[10381,216,28,34],[10429,217,28,34],[10477,218,28,32],[10525,219,28,29],[10573,220,28,26],[10621,221,28,27],[10669,222,28,28],[10717,223,28,27],[10765,224,30,29],[10813,225,30,50],[10861,226,30,51],[10909,227,30,49],[10957,228,30,51],[11005,229,30,48],[11052,230,30,48],[11100,231,30,48],[11148,232,30,51],[11196,233,30,50],[11244,234,30,48],[11292,235,30,44],[11340,236,30,50],[11388,237,28,30],[11436,238,28,35],[11484,239,28,33],[11532,240,36,30],[11580,241,34,32],[11628,242,33,33],[11676,243,33,34],[11724,244,33,27],[11772,245,33,28],[11820,246,33,26],[11868,247,33,27],[11916,248,33,26],[11964,249,33,25],[12012,250,33,25],[12059,251,30,33],[12107,252,30,30],[12155,253,29,25],[12203,254,29,27],[12251,255,29,26],[12299,256,30,25],[12347,257,30,28],[12395,258,30,25],[12443,259,30,25],[12491,260,30,28],[12539,261,30,27],[12587,262,30,27],[12635,263,30,29],[12683,264,30,26],[12731,265,30,27],[12779,266,30,24],[12827,267,30,24],[12875,268,30,25],[12923,269,30,25],[12971,270,30,24],[13019,271,30,26],[13066,272,32,26],[13114,273,30,28],[13162,274,27,30],[13210,275,27,23],[13258,276,27,26],[13306,277,27,28],[13354,278,27,29],[13402,279,27,28],[13450,280,27,29],[13498,281,27,25],[13546,282,27,23],[13594,283,27,25],[13642,284,27,24],[13690,285,27,26],[13738,286,27,25],[13786,287,27,24],[13834,288,32,30],[13882,289,31,30],[13930,290,32,30],[13978,291,30,29],[14010,292,30,29]]},"JKpqYvAdIsw":{"frames":77,"spearman":0.12481409289763393,"constant_ranking":false,"top15_count":12,"top15_human_mean":2.229166666666667,"mae":0.4337662337662338,"train_mean_constant_mae":0.37971097258788916,"threshold_selected_fraction":0.0,"threshold_selected_human_mean":null,"threshold_low_human_fraction":null,"predictions":[[24,0,30,47],[74,1,30,45],[124,2,30,47],[174,3,30,25],[224,4,30,36],[274,5,30,40],[324,6,30,29],[374,7,30,35],[424,8,30,49],[474,9,30,54],[524,10,30,40],[574,11,30,38],[624,12,30,43],[674,13,30,36],[724,14,30,29],[774,15,30,32],[824,16,46,24],[874,17,46,47],[924,18,46,39],[974,19,46,34],[1024,20,46,50],[1074,21,46,48],[1124,22,46,37],[1174,23,30,49],[1224,24,30,58],[1274,25,46,29],[1324,26,46,55],[1374,27,46,58],[1424,28,46,53],[1474,29,46,61],[1524,30,46,40],[1574,31,46,35],[1624,32,32,35],[1674,33,30,41],[1724,34,37,37],[1774,35,37,41],[1824,36,37,44],[1874,37,37,46],[1924,38,37,46],[1974,39,32,33],[2024,40,37,40],[2074,41,37,43],[2124,42,32,34],[2174,43,32,35],[2224,44,37,39],[2274,45,37,49],[2324,46,37,33],[2374,47,37,38],[2424,48,42,32],[2474,49,42,30],[2524,50,38,33],[2574,51,32,25],[2624,52,37,33],[2674,53,37,37],[2724,54,37,52],[2774,55,37,49],[2824,56,37,45],[2874,57,37,28],[2924,58,37,47],[2974,59,37,42],[3024,60,37,28],[3074,61,37,48],[3124,62,37,52],[3174,63,37,26],[3224,64,46,59],[3274,65,45,56],[3324,66,42,39],[3374,67,42,34],[3424,68,42,30],[3474,69,42,32],[3524,70,33,50],[3574,71,44,42],[3624,72,44,40],[3674,73,44,40],[3724,74,44,42],[3774,75,40,23],[3800,76,28,23]]},"sTEELN-vY30":{"frames":75,"spearman":0.6853906699845506,"constant_ranking":false,"top15_count":12,"top15_human_mean":2.6375,"mae":0.37266666666666665,"train_mean_constant_mae":0.5893703861442365,"threshold_selected_fraction":0.14666666666666667,"threshold_selected_human_mean":2.6136363636363638,"threshold_low_human_fraction":0.8181818181818182,"predictions":[[29,0,48,58],[89,1,48,57],[149,2,48,58],[209,3,48,55],[269,4,48,59],[329,5,48,87],[389,6,36,80],[449,7,36,38],[509,8,36,43],[569,9,36,36],[629,10,36,36],[689,11,36,45],[749,12,36,23],[809,13,36,24],[869,14,36,25],[929,15,36,28],[989,16,32,23],[1049,17,31,26],[1109,18,30,30],[1169,19,30,32],[1229,20,30,33],[1289,21,30,30],[1349,22,48,52],[1409,23,48,49],[1469,24,48,50],[1529,25,30,36],[1589,26,30,25],[1649,27,30,42],[1709,28,30,45],[1769,29,30,31],[1829,30,30,30],[1889,31,30,30],[1949,32,50,27],[2009,33,52,55],[2069,34,52,60],[2129,35,52,69],[2189,36,52,58],[2249,37,52,46],[2309,38,52,51],[2369,39,52,52],[2429,40,42,31],[2489,41,42,31],[2549,42,42,29],[2609,43,36,26],[2669,44,36,26],[2729,45,36,24],[2789,46,36,25],[2849,47,36,31],[2909,48,48,30],[2969,49,46,30],[3029,50,50,45],[3089,51,38,37],[3149,52,42,34],[3209,53,46,42],[3269,54,42,40],[3329,55,42,40],[3389,56,42,39],[3449,57,40,31],[3509,58,38,29],[3569,59,53,55],[3629,60,52,57],[3689,61,38,25],[3749,62,37,25],[3809,63,37,34],[3869,64,38,38],[3929,65,48,65],[3989,66,48,46],[4049,67,32,38],[4109,68,27,26],[4169,69,27,22],[4229,70,27,24],[4289,71,27,25],[4349,72,27,26],[4409,73,27,24],[4453,74,27,24]]},"Yi4Ij2NM7U4":{"frames":203,"spearman":0.7653612974081682,"constant_ranking":false,"top15_count":31,"top15_human_mean":2.643548387096774,"mae":0.30886699507389165,"train_mean_constant_mae":0.49573796166531,"threshold_selected_fraction":0.04433497536945813,"threshold_selected_human_mean":3.011111111111111,"threshold_low_human_fraction":0.3333333333333333,"predictions":[[23,0,30,28],[71,1,30,25],[119,2,30,26],[167,3,30,28],[215,4,30,25],[263,5,30,26],[311,6,30,30],[359,7,30,29],[407,8,30,29],[455,9,30,26],[503,10,30,27],[551,11,30,29],[599,12,30,27],[647,13,30,30],[695,14,30,30],[743,15,30,24],[791,16,30,29],[839,17,28,28],[887,18,27,26],[935,19,27,26],[983,20,27,26],[1031,21,27,27],[1079,22,27,27],[1127,23,27,27],[1175,24,27,24],[1223,25,27,36],[1271,26,42,49],[1319,27,42,47],[1367,28,42,45],[1415,29,42,58],[1463,30,42,53],[1511,31,30,30],[1559,32,30,26],[1607,33,30,32],[1655,34,28,28],[1703,35,27,24],[1751,36,27,28],[1799,37,27,30],[1847,38,27,23],[1895,39,27,27],[1943,40,27,31],[1991,41,27,28],[2039,42,30,37],[2087,43,30,35],[2135,44,30,40],[2183,45,30,42],[2231,46,30,44],[2279,47,30,45],[2327,48,36,46],[2375,49,33,43],[2423,50,33,39],[2471,51,33,35],[2519,52,33,39],[2567,53,33,36],[2615,54,28,28],[2663,55,28,24],[2711,56,28,28],[2759,57,28,24],[2807,58,28,26],[2855,59,33,42],[2903,60,33,50],[2951,61,33,48],[2999,62,33,51],[3047,63,33,45],[3095,64,48,50],[3143,65,47,51],[3191,66,47,48],[3239,67,47,51],[3287,68,47,55],[3335,69,47,51],[3383,70,47,44],[3431,71,47,51],[3479,72,47,44],[3527,73,47,49],[3575,74,47,42],[3623,75,47,45],[3671,76,47,43],[3719,77,47,43],[3767,78,47,52],[3815,79,47,57],[3863,80,42,51],[3911,81,42,48],[3959,82,42,50],[4007,83,42,52],[4055,84,42,56],[4103,85,42,53],[4151,86,42,55],[4199,87,42,52],[4247,88,42,50],[4295,89,42,49],[4343,90,30,27],[4391,91,30,38],[4439,92,30,25],[4487,93,30,40],[4535,94,30,40],[4583,95,30,26],[4631,96,30,25],[4679,97,30,29],[4727,98,29,27],[4775,99,30,34],[4823,100,30,41],[4871,101,30,37],[4919,102,30,41],[4967,103,30,36],[5015,104,29,25],[5063,105,29,28],[5111,106,29,27],[5159,107,29,29],[5207,108,30,31],[5255,109,30,30],[5303,110,30,29],[5351,111,30,36],[5399,112,30,32],[5447,113,30,36],[5495,114,30,33],[5543,115,29,34],[5591,116,29,40],[5639,117,30,37],[5687,118,36,53],[5735,119,36,45],[5783,120,36,52],[5831,121,36,47],[5879,122,36,47],[5927,123,36,45],[5975,124,36,46],[6023,125,36,47],[6071,126,36,47],[6119,127,36,61],[6167,128,50,65],[6215,129,50,60],[6263,130,50,68],[6311,131,50,61],[6359,132,50,60],[6407,133,50,59],[6455,134,50,63],[6503,135,26,37],[6551,136,26,26],[6599,137,26,24],[6647,138,26,27],[6695,139,26,26],[6743,140,26,27],[6791,141,26,28],[6839,142,26,26],[6887,143,26,29],[6935,144,32,30],[6983,145,32,36],[7031,146,50,49],[7079,147,50,57],[7127,148,48,51],[7175,149,48,58],[7223,150,48,51],[7271,151,48,55],[7319,152,48,50],[7367,153,48,56],[7415,154,30,29],[7463,155,30,28],[7511,156,30,24],[7559,157,30,23],[7607,158,30,25],[7655,159,30,24],[7703,160,30,31],[7751,161,28,27],[7799,162,28,41],[7847,163,28,29],[7895,164,28,33],[7943,165,28,38],[7991,166,28,36],[8039,167,37,55],[8087,168,28,38],[8135,169,28,40],[8183,170,28,34],[8231,171,28,41],[8279,172,28,40],[8327,173,28,38],[8375,174,28,44],[8423,175,28,36],[8471,176,26,39],[8519,177,26,27],[8567,178,26,30],[8615,179,26,32],[8663,180,26,30],[8711,181,26,33],[8759,182,26,33],[8807,183,26,27],[8855,184,37,50],[8903,185,37,56],[8951,186,37,66],[8999,187,37,59],[9047,188,37,52],[9095,189,37,48],[9143,190,37,47],[9191,191,37,35],[9239,192,30,35],[9287,193,28,28],[9335,194,28,26],[9383,195,28,26],[9431,196,28,27],[9479,197,28,32],[9527,198,28,30],[9575,199,28,33],[9623,200,30,34],[9671,201,30,36],[9713,202,30,36]]}},"macro_spearman":0.5223294106830001,"macro_top15_human_mean":2.421738229910273,"macro_mae":0.4139408871736182,"production_B_scope":null},"base":{"rows":89,"all_outputs_valid":true,"source_metrics":{"-esJrBWj2d8":{"frames":116,"spearman":-0.06835905801648398,"constant_ranking":false,"top15_count":18,"top15_human_mean":1.8833333333333333,"mae":0.5991379310344828,"train_mean_constant_mae":0.39834066410151,"threshold_selected_fraction":0.08620689655172414,"threshold_selected_human_mean":1.895,"threshold_low_human_fraction":1.0,"predictions":[[29,0,40,39],[89,1,40,40],[149,2,40,48],[209,3,40,37],[269,4,40,36],[329,5,40,28],[389,6,40,29],[449,7,40,42],[509,8,40,42],[569,9,40,51],[629,10,40,36],[689,11,40,36],[749,12,40,38],[809,13,40,41],[869,14,40,28],[929,15,40,33],[989,16,20,38],[1049,17,20,40],[1109,18,20,45],[1169,19,20,43],[1229,20,20,41],[1289,21,20,56],[1349,22,20,59],[1409,23,20,50],[1469,24,20,60],[1529,25,20,54],[1589,26,20,51],[1649,27,20,48],[1709,28,20,53],[1769,29,20,46],[1829,30,20,42],[1889,31,20,46],[1949,32,40,49],[2009,33,40,57],[2069,34,40,67],[2129,35,40,62],[2189,36,40,62],[2249,37,40,62],[2309,38,40,61],[2369,39,60,49],[2429,40,60,39],[2489,41,60,35],[2549,42,60,39],[2609,43,60,33],[2669,44,60,45],[2729,45,60,34],[2789,46,60,39],[2849,47,60,36],[2909,48,40,37],[2969,49,40,36],[3029,50,40,39],[3089,51,40,42],[3149,52,40,36],[3209,53,40,39],[3269,54,40,46],[3329,55,40,49],[3389,56,40,61],[3449,57,40,48],[3509,58,40,54],[3569,59,40,48],[3629,60,40,46],[3689,61,40,43],[3749,62,40,42],[3809,63,40,52],[3869,64,40,33],[3929,65,40,28],[3989,66,40,31],[4049,67,40,31],[4109,68,40,30],[4169,69,40,33],[4229,70,40,34],[4289,71,40,31],[4349,72,40,31],[4409,73,40,40],[4469,74,40,29],[4529,75,40,31],[4589,76,40,32],[4649,77,40,32],[4709,78,40,41],[4769,79,40,41],[4829,80,20,26],[4889,81,20,27],[4949,82,20,28],[5009,83,20,30],[5069,84,20,29],[5129,85,20,29],[5189,86,20,26],[5249,87,20,30],[5309,88,20,31],[5369,89,40,26],[5429,90,40,29],[5489,91,40,25],[5549,92,40,27],[5609,93,40,32],[5669,94,40,34],[5729,95,40,26],[5789,96,40,28],[5849,97,40,34],[5909,98,40,32],[5969,99,40,34],[6029,100,40,43],[6089,101,40,40],[6149,102,40,42],[6209,103,40,45],[6269,104,40,41],[6329,105,40,43],[6389,106,40,42],[6449,107,40,48],[6509,108,40,41],[6569,109,40,35],[6629,110,40,29],[6689,111,40,28],[6749,112,40,30],[6809,113,40,29],[6869,114,60,30],[6905,115,40,30]]},"4wU_LUjG5Ic":{"frames":84,"spearman":-0.35567717066389043,"constant_ranking":false,"top15_count":13,"top15_human_mean":1.7692307692307694,"mae":0.7220238095238095,"train_mean_constant_mae":0.4194405573132151,"threshold_selected_fraction":0.047619047619047616,"threshold_selected_human_mean":1.3625,"threshold_low_human_fraction":1.0,"predictions":[[23,0,20,39],[71,1,20,28],[119,2,20,32],[167,3,20,44],[215,4,20,57],[263,5,20,60],[311,6,20,52],[359,7,20,46],[407,8,20,53],[455,9,20,50],[503,10,20,50],[551,11,20,43],[599,12,20,43],[647,13,20,41],[695,14,20,36],[743,15,20,38],[791,16,40,38],[839,17,40,35],[887,18,40,44],[935,19,40,41],[983,20,40,40],[1030,21,40,34],[1078,22,40,37],[1126,23,40,37],[1174,24,40,45],[1222,25,40,49],[1270,26,40,68],[1318,27,40,58],[1366,28,40,41],[1414,29,40,50],[1462,30,40,43],[1510,31,40,28],[1558,32,40,24],[1606,33,40,22],[1654,34,40,23],[1702,35,40,35],[1750,36,40,30],[1798,37,40,27],[1846,38,40,26],[1894,39,40,31],[1942,40,40,28],[1990,41,40,29],[2037,42,40,28],[2085,43,40,29],[2133,44,40,27],[2181,45,40,41],[2229,46,40,38],[2277,47,40,43],[2325,48,40,44],[2373,49,40,47],[2421,50,40,37],[2469,51,40,58],[2517,52,40,66],[2565,53,40,61],[2613,54,40,47],[2661,55,40,30],[2709,56,40,27],[2757,57,40,28],[2805,58,40,26],[2853,59,40,28],[2901,60,40,27],[2949,61,40,37],[2997,62,40,40],[3044,63,40,45],[3092,64,40,48],[3140,65,40,44],[3188,66,40,33],[3236,67,40,46],[3284,68,40,47],[3332,69,40,50],[3380,70,40,48],[3428,71,40,36],[3476,72,40,37],[3524,73,40,38],[3572,74,40,41],[3620,75,40,39],[3668,76,40,40],[3716,77,40,27],[3764,78,40,41],[3812,79,40,30],[3860,80,100,31],[3908,81,100,28],[3956,82,100,25],[3992,83,100,25]]},"cjibtmSLxQ4":{"frames":324,"spearman":0.23493014592196065,"constant_ranking":false,"top15_count":49,"top15_human_mean":2.1959183673469385,"mae":0.49398148148148147,"train_mean_constant_mae":0.5084463136475473,"threshold_selected_fraction":0.0,"threshold_selected_human_mean":null,"threshold_low_human_fraction":null,"predictions":[[29,0,40,41],[89,1,40,31],[149,2,40,39],[209,3,40,29],[269,4,40,71],[329,5,40,41],[389,6,40,42],[449,7,40,41],[509,8,40,45],[569,9,40,38],[629,10,40,48],[689,11,40,46],[749,12,40,37],[809,13,40,50],[869,14,40,42],[929,15,40,54],[989,16,40,43],[1048,17,40,28],[1108,18,40,39],[1168,19,40,53],[1228,20,40,51],[1288,21,40,66],[1348,22,40,67],[1408,23,40,36],[1468,24,40,46],[1528,25,40,42],[1588,26,40,43],[1648,27,40,36],[1708,28,40,44],[1768,29,40,34],[1828,30,40,63],[1888,31,40,61],[1948,32,40,39],[2008,33,40,29],[2067,34,40,33],[2127,35,40,34],[2187,36,40,30],[2247,37,40,68],[2307,38,40,33],[2367,39,40,57],[2427,40,40,54],[2487,41,40,70],[2547,42,40,42],[2607,43,40,32],[2667,44,40,33],[2727,45,40,34],[2787,46,40,35],[2847,47,40,40],[2907,48,40,42],[2967,49,40,46],[3027,50,40,49],[3086,51,40,50],[3146,52,40,44],[3206,53,40,27],[3266,54,40,27],[3326,55,40,26],[3386,56,40,25],[3446,57,40,27],[3506,58,40,27],[3566,59,40,27],[3626,60,40,31],[3686,61,40,65],[3746,62,40,71],[3806,63,40,29],[3866,64,40,39],[3926,65,40,41],[3986,66,40,40],[4045,67,40,39],[4105,68,40,39],[4165,69,40,29],[4225,70,40,30],[4285,71,40,45],[4345,72,40,42],[4405,73,40,56],[4465,74,40,39],[4525,75,40,56],[4585,76,40,44],[4645,77,40,45],[4705,78,40,38],[4765,79,40,42],[4825,80,40,38],[4885,81,40,41],[4945,82,40,42],[5005,83,40,41],[5064,84,40,28],[5124,85,40,48],[5184,86,40,51],[5244,87,40,61],[5304,88,40,63],[5364,89,40,62],[5424,90,40,45],[5484,91,40,57],[5544,92,40,46],[5604,93,40,43],[5664,94,40,50],[5724,95,40,61],[5784,96,40,46],[5844,97,40,49],[5904,98,40,45],[5964,99,40,54],[6024,100,40,53],[6083,101,40,45],[6143,102,40,50],[6203,103,40,50],[6263,104,40,35],[6323,105,40,33],[6383,106,40,34],[6443,107,40,31],[6503,108,40,34],[6563,109,40,39],[6623,110,40,43],[6683,111,40,33],[6743,112,40,31],[6803,113,40,36],[6863,114,40,31],[6923,115,40,44],[6983,116,40,50],[7042,117,40,28],[7102,118,40,41],[7162,119,40,40],[7222,120,40,41],[7282,121,40,24],[7342,122,40,27],[7402,123,40,28],[7462,124,40,26],[7522,125,40,45],[7582,126,40,21],[7642,127,40,21],[7702,128,40,33],[7762,129,40,53],[7822,130,40,53],[7882,131,40,52],[7942,132,40,50],[8002,133,40,48],[8061,134,40,24],[8121,135,40,41],[8181,136,40,52],[8241,137,40,52],[8301,138,40,46],[8361,139,40,28],[8421,140,40,24],[8481,141,40,23],[8541,142,40,22],[8601,143,40,22],[8661,144,40,26],[8721,145,40,25],[8781,146,40,34],[8841,147,40,41],[8901,148,40,42],[8961,149,40,29],[9021,150,40,22],[9080,151,40,27],[9140,152,40,37],[9200,153,40,46],[9260,154,40,47],[9320,155,40,35],[9380,156,40,44],[9440,157,40,45],[9500,158,40,42],[9560,159,40,45],[9620,160,30,34],[9680,161,30,51],[9740,162,30,22],[9800,163,30,21],[9860,164,30,31],[9920,165,30,28],[9980,166,30,27],[10039,167,30,23],[10099,168,30,28],[10159,169,30,28],[10219,170,30,24],[10279,171,30,23],[10339,172,30,27],[10399,173,30,23],[10459,174,30,23],[10519,175,30,28],[10579,176,40,32],[10639,177,40,31],[10699,178,40,22],[10759,179,40,23],[10819,180,40,32],[10879,181,40,42],[10939,182,40,28],[10999,183,40,25],[11058,184,40,26],[11118,185,40,27],[11178,186,40,26],[11238,187,40,28],[11298,188,40,38],[11358,189,40,35],[11418,190,40,63],[11478,191,40,46],[11538,192,40,59],[11598,193,40,73],[11658,194,40,53],[11718,195,40,33],[11778,196,40,29],[11838,197,40,35],[11898,198,40,31],[11958,199,40,32],[12018,200,40,33],[12077,201,40,32],[12137,202,40,40],[12197,203,40,36],[12257,204,40,30],[12317,205,40,21],[12377,206,40,22],[12437,207,40,22],[12497,208,40,21],[12557,209,40,21],[12617,210,40,23],[12677,211,40,22],[12737,212,40,21],[12797,213,40,24],[12857,214,40,31],[12917,215,40,27],[12977,216,40,26],[13036,217,40,28],[13096,218,40,30],[13156,219,40,29],[13216,220,40,29],[13276,221,40,29],[13336,222,40,26],[13396,223,40,25],[13456,224,40,29],[13516,225,40,24],[13576,226,40,24],[13636,227,40,27],[13696,228,40,29],[13756,229,40,36],[13816,230,40,36],[13876,231,40,32],[13936,232,40,32],[13996,233,40,33],[14055,234,40,32],[14115,235,40,32],[14175,236,40,30],[14235,237,40,34],[14295,238,40,29],[14355,239,40,29],[14415,240,40,27],[14475,241,40,31],[14535,242,40,32],[14595,243,40,29],[14655,244,40,28],[14715,245,40,28],[14775,246,40,28],[14835,247,40,29],[14895,248,40,29],[14955,249,40,27],[15015,250,40,28],[15074,251,40,27],[15134,252,40,28],[15194,253,40,34],[15254,254,40,32],[15314,255,40,29],[15374,256,40,30],[15434,257,40,29],[15494,258,40,34],[15554,259,40,71],[15614,260,40,57],[15674,261,40,49],[15734,262,40,75],[15794,263,40,36],[15854,264,40,59],[15914,265,40,68],[15974,266,40,36],[16033,267,40,65],[16093,268,40,73],[16153,269,40,28],[16213,270,40,37],[16273,271,40,34],[16333,272,40,46],[16393,273,40,40],[16453,274,40,37],[16513,275,40,45],[16573,276,40,47],[16633,277,40,48],[16693,278,40,47],[16753,279,40,28],[16813,280,40,28],[16873,281,40,26],[16933,282,40,33],[16993,283,40,32],[17052,284,40,34],[17112,285,40,32],[17172,286,40,36],[17232,287,40,32],[17292,288,40,34],[17352,289,40,51],[17412,290,40,55],[17472,291,40,31],[17532,292,40,51],[17592,293,40,50],[17652,294,40,60],[17712,295,40,64],[17772,296,40,56],[17832,297,40,30],[17892,298,40,28],[17952,299,40,29],[18012,300,40,27],[18071,301,40,26],[18131,302,40,27],[18191,303,40,55],[18251,304,40,32],[18311,305,40,44],[18371,306,40,46],[18431,307,40,31],[18491,308,40,48],[18551,309,40,51],[18611,310,40,54],[18671,311,40,40],[18731,312,40,39],[18791,313,40,50],[18851,314,40,53],[18911,315,40,47],[18971,316,40,46],[19030,317,40,45],[19090,318,40,36],[19150,319,40,27],[19210,320,40,29],[19270,321,40,27],[19330,322,40,30],[19383,323,40,30]]},"EYqVtI9YWJA":{"frames":100,"spearman":0.27661893269306503,"constant_ranking":false,"top15_count":15,"top15_human_mean":2.033333333333333,"mae":0.5085,"train_mean_constant_mae":0.5319150340715502,"threshold_selected_fraction":0.06,"threshold_selected_human_mean":2.708333333333333,"threshold_low_human_fraction":0.8333333333333334,"predictions":[[29,0,40,36],[89,1,40,32],[149,2,40,33],[209,3,40,43],[269,4,40,23],[329,5,40,28],[389,6,40,25],[449,7,40,26],[509,8,40,39],[569,9,40,51],[629,10,40,54],[689,11,40,46],[749,12,40,54],[809,13,40,23],[869,14,40,25],[929,15,40,39],[989,16,40,47],[1048,17,40,54],[1108,18,40,46],[1168,19,40,24],[1228,20,40,25],[1288,21,40,42],[1348,22,40,36],[1408,23,40,52],[1468,24,40,31],[1528,25,40,29],[1588,26,40,29],[1648,27,40,29],[1708,28,40,44],[1768,29,40,38],[1828,30,40,42],[1888,31,40,40],[1948,32,40,26],[2008,33,40,31],[2067,34,40,32],[2127,35,40,28],[2187,36,40,29],[2247,37,40,34],[2307,38,40,44],[2367,39,40,39],[2427,40,40,38],[2487,41,40,34],[2547,42,40,42],[2607,43,40,47],[2667,44,40,23],[2727,45,40,26],[2787,46,40,25],[2847,47,40,23],[2907,48,40,34],[2967,49,40,66],[3027,50,40,49],[3086,51,40,43],[3146,52,40,41],[3206,53,40,42],[3266,54,40,41],[3326,55,40,48],[3386,56,40,48],[3446,57,40,60],[3506,58,40,25],[3566,59,40,26],[3626,60,40,31],[3686,61,40,27],[3746,62,40,27],[3806,63,40,27],[3866,64,40,28],[3926,65,40,28],[3986,66,40,53],[4045,67,50,54],[4105,68,50,52],[4165,69,50,55],[4225,70,50,47],[4285,71,50,47],[4345,72,50,70],[4405,73,40,37],[4465,74,40,23],[4525,75,40,23],[4585,76,40,22],[4645,77,40,31],[4705,78,40,28],[4765,79,40,53],[4825,80,40,59],[4885,81,40,55],[4945,82,40,58],[5005,83,40,57],[5064,84,40,57],[5124,85,40,61],[5184,86,40,55],[5244,87,40,40],[5304,88,40,67],[5364,89,40,63],[5424,90,40,61],[5484,91,40,40],[5544,92,40,44],[5604,93,40,46],[5664,94,40,55],[5724,95,40,44],[5784,96,40,36],[5844,97,40,27],[5904,98,40,28],[5936,99,40,28]]},"i3wAGJaaktw":{"frames":79,"spearman":0.0,"constant_ranking":true,"top15_count":12,"top15_human_mean":2.2,"mae":0.5417721518987342,"train_mean_constant_mae":0.5376996042956035,"threshold_selected_fraction":0.0,"threshold_selected_human_mean":null,"threshold_low_human_fraction":null,"predictions":[[29,0,40,31],[89,1,40,31],[149,2,40,64],[209,3,40,55],[269,4,40,48],[329,5,40,58],[389,6,40,41],[449,7,40,40],[509,8,40,41],[569,9,40,44],[629,10,40,39],[689,11,40,36],[749,12,40,37],[809,13,40,37],[869,14,40,55],[929,15,40,55],[989,16,40,52],[1048,17,40,52],[1108,18,40,50],[1168,19,40,50],[1228,20,40,45],[1288,21,40,50],[1348,22,40,47],[1408,23,40,43],[1468,24,40,43],[1528,25,40,49],[1588,26,40,48],[1648,27,40,52],[1708,28,40,64],[1768,29,40,44],[1828,30,40,44],[1888,31,40,54],[1948,32,40,56],[2008,33,40,38],[2067,34,40,33],[2127,35,40,35],[2187,36,40,34],[2247,37,40,36],[2307,38,40,40],[2367,39,40,37],[2427,40,40,37],[2487,41,40,36],[2547,42,40,35],[2607,43,40,38],[2667,44,40,66],[2727,45,40,58],[2787,46,40,72],[2847,47,40,67],[2907,48,40,59],[2967,49,40,67],[3027,50,40,22],[3086,51,40,22],[3146,52,40,21],[3206,53,40,23],[3266,54,40,21],[3326,55,40,24],[3386,56,40,32],[3446,57,40,33],[3506,58,40,32],[3566,59,40,31],[3626,60,40,31],[3686,61,40,36],[3746,62,40,28],[3806,63,40,23],[3866,64,40,22],[3926,65,40,21],[3986,66,40,25],[4045,67,40,23],[4105,68,40,22],[4165,69,40,23],[4225,70,40,30],[4285,71,40,26],[4345,72,40,22],[4405,73,40,22],[4465,74,40,36],[4525,75,40,31],[4585,76,40,39],[4645,77,40,33],[4687,78,40,33]]},"J0nA4VgnoCo":{"frames":293,"spearman":-0.0496852555021848,"constant_ranking":false,"top15_count":44,"top15_human_mean":1.5738636363636362,"mae":0.6627986348122866,"train_mean_constant_mae":0.5519635838503165,"threshold_selected_fraction":0.04778156996587031,"threshold_selected_human_mean":1.4535714285714287,"threshold_low_human_fraction":1.0,"predictions":[[23,0,20,27],[71,1,40,30],[119,2,40,25],[167,3,40,30],[215,4,40,25],[263,5,40,27],[311,6,40,25],[359,7,40,27],[407,8,40,26],[455,9,40,25],[503,10,40,29],[551,11,40,31],[599,12,40,51],[647,13,40,53],[695,14,40,46],[743,15,40,53],[791,16,40,48],[839,17,40,47],[887,18,40,41],[935,19,40,25],[983,20,40,25],[1030,21,40,31],[1078,22,40,29],[1126,23,40,36],[1174,24,40,26],[1222,25,40,25],[1270,26,40,26],[1318,27,40,26],[1366,28,40,27],[1414,29,40,30],[1462,30,40,33],[1510,31,40,38],[1558,32,40,30],[1606,33,40,47],[1654,34,40,38],[1702,35,40,30],[1750,36,40,30],[1798,37,40,29],[1846,38,40,25],[1894,39,40,29],[1942,40,40,29],[1990,41,40,30],[2037,42,40,27],[2085,43,40,32],[2133,44,40,29],[2181,45,40,26],[2229,46,40,31],[2277,47,40,68],[2325,48,40,68],[2373,49,40,65],[2421,50,40,26],[2469,51,40,29],[2517,52,40,27],[2565,53,40,28],[2613,54,40,33],[2661,55,40,54],[2709,56,40,33],[2757,57,40,35],[2805,58,40,26],[2853,59,40,27],[2901,60,40,28],[2949,61,40,29],[2997,62,40,28],[3044,63,40,28],[3092,64,40,35],[3140,65,40,29],[3188,66,40,25],[3236,67,40,26],[3284,68,40,25],[3332,69,40,27],[3380,70,40,26],[3428,71,40,26],[3476,72,40,26],[3524,73,40,25],[3572,74,40,26],[3620,75,40,26],[3668,76,40,27],[3716,77,40,26],[3764,78,40,27],[3812,79,40,27],[3860,80,20,28],[3908,81,20,30],[3956,82,20,42],[4004,83,20,33],[4051,84,20,41],[4099,85,20,39],[4147,86,20,47],[4195,87,20,34],[4243,88,20,43],[4291,89,20,36],[4339,90,20,40],[4387,91,20,36],[4435,92,20,35],[4483,93,20,36],[4531,94,20,35],[4579,95,20,44],[4627,96,40,35],[4675,97,40,45],[4723,98,40,44],[4771,99,40,43],[4819,100,40,45],[4867,101,40,47],[4915,102,40,46],[4963,103,40,40],[5011,104,40,48],[5058,105,40,42],[5106,106,40,41],[5154,107,40,42],[5202,108,40,43],[5250,109,40,41],[5298,110,40,39],[5346,111,40,41],[5394,112,40,44],[5442,113,40,34],[5490,114,40,30],[5538,115,40,33],[5586,116,40,36],[5634,117,40,48],[5682,118,40,33],[5730,119,40,51],[5778,120,40,54],[5826,121,40,59],[5874,122,40,56],[5922,123,40,53],[5970,124,40,56],[6018,125,40,54],[6065,126,40,53],[6113,127,40,28],[6161,128,20,28],[6209,129,20,30],[6257,130,20,30],[6305,131,20,30],[6353,132,20,39],[6401,133,20,62],[6449,134,20,54],[6497,135,20,55],[6545,136,20,74],[6593,137,20,70],[6641,138,20,52],[6689,139,20,38],[6737,140,20,38],[6785,141,20,38],[6833,142,20,35],[6881,143,20,41],[6929,144,40,42],[6977,145,40,57],[7024,146,40,59],[7072,147,40,56],[7120,148,40,56],[7168,149,40,58],[7216,150,40,63],[7264,151,40,57],[7312,152,40,58],[7360,153,40,56],[7408,154,40,53],[7456,155,40,51],[7504,156,40,47],[7552,157,40,52],[7600,158,40,48],[7648,159,40,52],[7696,160,40,75],[7744,161,40,71],[7792,162,40,59],[7840,163,40,57],[7888,164,40,59],[7936,165,40,63],[7984,166,40,55],[8031,167,40,53],[8079,168,40,66],[8127,169,40,68],[8175,170,40,70],[8223,171,40,57],[8271,172,40,51],[8319,173,40,55],[8367,174,40,57],[8415,175,40,53],[8463,176,40,57],[8511,177,40,56],[8559,178,40,53],[8607,179,40,46],[8655,180,40,44],[8703,181,40,49],[8751,182,40,59],[8799,183,40,59],[8847,184,40,57],[8895,185,40,46],[8943,186,40,44],[8991,187,40,59],[9038,188,40,46],[9086,189,40,43],[9134,190,40,36],[9182,191,40,48],[9230,192,40,45],[9278,193,40,49],[9326,194,40,47],[9374,195,40,46],[9422,196,40,45],[9470,197,40,44],[9518,198,40,46],[9566,199,40,44],[9614,200,60,47],[9662,201,60,43],[9710,202,40,44],[9758,203,40,46],[9806,204,40,44],[9854,205,40,63],[9902,206,40,56],[9950,207,40,30],[9998,208,20,32],[10045,209,40,32],[10093,210,40,31],[10141,211,40,30],[10189,212,40,30],[10237,213,40,34],[10285,214,40,29],[10333,215,40,32],[10381,216,40,34],[10429,217,40,34],[10477,218,40,32],[10525,219,40,29],[10573,220,40,26],[10621,221,40,27],[10669,222,40,28],[10717,223,40,27],[10765,224,40,29],[10813,225,40,50],[10861,226,40,51],[10909,227,40,49],[10957,228,40,51],[11005,229,40,48],[11052,230,40,48],[11100,231,40,48],[11148,232,40,51],[11196,233,40,50],[11244,234,40,48],[11292,235,40,44],[11340,236,40,50],[11388,237,40,30],[11436,238,40,35],[11484,239,40,33],[11532,240,20,30],[11580,241,20,32],[11628,242,20,33],[11676,243,20,34],[11724,244,20,27],[11772,245,20,28],[11820,246,20,26],[11868,247,20,27],[11916,248,20,26],[11964,249,20,25],[12012,250,20,25],[12059,251,20,33],[12107,252,20,30],[12155,253,20,25],[12203,254,20,27],[12251,255,20,26],[12299,256,40,25],[12347,257,40,28],[12395,258,40,25],[12443,259,40,25],[12491,260,40,28],[12539,261,40,27],[12587,262,40,27],[12635,263,40,29],[12683,264,40,26],[12731,265,40,27],[12779,266,40,24],[12827,267,40,24],[12875,268,40,25],[12923,269,40,25],[12971,270,40,24],[13019,271,40,26],[13066,272,40,26],[13114,273,40,28],[13162,274,20,30],[13210,275,40,23],[13258,276,40,26],[13306,277,40,28],[13354,278,40,29],[13402,279,60,28],[13450,280,60,29],[13498,281,60,25],[13546,282,60,23],[13594,283,60,25],[13642,284,60,24],[13690,285,60,26],[13738,286,60,25],[13786,287,60,24],[13834,288,40,30],[13882,289,40,30],[13930,290,60,30],[13978,291,60,29],[14010,292,60,29]]},"JKpqYvAdIsw":{"frames":77,"spearman":0.1936795547464208,"constant_ranking":false,"top15_count":12,"top15_human_mean":2.020833333333333,"mae":0.36948051948051946,"train_mean_constant_mae":0.37971097258788916,"threshold_selected_fraction":0.0,"threshold_selected_human_mean":null,"threshold_low_human_fraction":null,"predictions":[[24,0,40,47],[74,1,40,45],[124,2,40,47],[174,3,40,25],[224,4,40,36],[274,5,40,40],[324,6,40,29],[374,7,40,35],[424,8,40,49],[474,9,40,54],[524,10,40,40],[574,11,40,38],[624,12,40,43],[674,13,40,36],[724,14,40,29],[774,15,40,32],[824,16,40,24],[874,17,40,47],[924,18,40,39],[974,19,40,34],[1024,20,40,50],[1074,21,40,48],[1124,22,40,37],[1174,23,40,49],[1224,24,40,58],[1274,25,40,29],[1324,26,40,55],[1374,27,40,58],[1424,28,40,53],[1474,29,40,61],[1524,30,40,40],[1574,31,40,35],[1624,32,40,35],[1674,33,40,41],[1724,34,40,37],[1774,35,40,41],[1824,36,40,44],[1874,37,40,46],[1924,38,40,46],[1974,39,40,33],[2024,40,40,40],[2074,41,40,43],[2124,42,40,34],[2174,43,40,35],[2224,44,40,39],[2274,45,40,49],[2324,46,40,33],[2374,47,40,38],[2424,48,40,32],[2474,49,40,30],[2524,50,40,33],[2574,51,40,25],[2624,52,40,33],[2674,53,40,37],[2724,54,40,52],[2774,55,40,49],[2824,56,40,45],[2874,57,40,28],[2924,58,40,47],[2974,59,40,42],[3024,60,40,28],[3074,61,40,48],[3124,62,40,52],[3174,63,40,26],[3224,64,40,59],[3274,65,40,56],[3324,66,40,39],[3374,67,40,34],[3424,68,40,30],[3474,69,40,32],[3524,70,40,50],[3574,71,40,42],[3624,72,40,40],[3674,73,40,40],[3724,74,40,42],[3774,75,40,23],[3800,76,20,23]]},"sTEELN-vY30":{"frames":75,"spearman":0.0,"constant_ranking":true,"top15_count":12,"top15_human_mean":2.716666666666667,"mae":0.596,"train_mean_constant_mae":0.5893703861442365,"threshold_selected_fraction":0.0,"threshold_selected_human_mean":null,"threshold_low_human_fraction":null,"predictions":[[29,0,40,58],[89,1,40,57],[149,2,40,58],[209,3,40,55],[269,4,40,59],[329,5,40,87],[389,6,40,80],[449,7,40,38],[509,8,40,43],[569,9,40,36],[629,10,40,36],[689,11,40,45],[749,12,40,23],[809,13,40,24],[869,14,40,25],[929,15,40,28],[989,16,40,23],[1049,17,40,26],[1109,18,40,30],[1169,19,40,32],[1229,20,40,33],[1289,21,40,30],[1349,22,40,52],[1409,23,40,49],[1469,24,40,50],[1529,25,40,36],[1589,26,40,25],[1649,27,40,42],[1709,28,40,45],[1769,29,40,31],[1829,30,40,30],[1889,31,40,30],[1949,32,40,27],[2009,33,40,55],[2069,34,40,60],[2129,35,40,69],[2189,36,40,58],[2249,37,40,46],[2309,38,40,51],[2369,39,40,52],[2429,40,40,31],[2489,41,40,31],[2549,42,40,29],[2609,43,40,26],[2669,44,40,26],[2729,45,40,24],[2789,46,40,25],[2849,47,40,31],[2909,48,40,30],[2969,49,40,30],[3029,50,40,45],[3089,51,40,37],[3149,52,40,34],[3209,53,40,42],[3269,54,40,40],[3329,55,40,40],[3389,56,40,39],[3449,57,40,31],[3509,58,40,29],[3569,59,40,55],[3629,60,40,57],[3689,61,40,25],[3749,62,40,25],[3809,63,40,34],[3869,64,40,38],[3929,65,40,65],[3989,66,40,46],[4049,67,40,38],[4109,68,40,26],[4169,69,40,22],[4229,70,40,24],[4289,71,40,25],[4349,72,40,26],[4409,73,40,24],[4453,74,40,24]]},"Yi4Ij2NM7U4":{"frames":203,"spearman":0.16115616489932774,"constant_ranking":false,"top15_count":31,"top15_human_mean":1.5758064516129031,"mae":0.5059113300492611,"train_mean_constant_mae":0.49573796166531,"threshold_selected_fraction":0.0049261083743842365,"threshold_selected_human_mean":3.15,"threshold_low_human_fraction":0.0,"predictions":[[23,0,40,28],[71,1,40,25],[119,2,40,26],[167,3,40,28],[215,4,40,25],[263,5,40,26],[311,6,40,30],[359,7,40,29],[407,8,40,29],[455,9,40,26],[503,10,40,27],[551,11,40,29],[599,12,40,27],[647,13,40,30],[695,14,40,30],[743,15,40,24],[791,16,40,29],[839,17,40,28],[887,18,40,26],[935,19,40,26],[983,20,40,26],[1031,21,40,27],[1079,22,40,27],[1127,23,40,27],[1175,24,40,24],[1223,25,40,36],[1271,26,40,49],[1319,27,40,47],[1367,28,40,45],[1415,29,40,58],[1463,30,40,53],[1511,31,40,30],[1559,32,40,26],[1607,33,40,32],[1655,34,40,28],[1703,35,40,24],[1751,36,40,28],[1799,37,40,30],[1847,38,40,23],[1895,39,40,27],[1943,40,40,31],[1991,41,40,28],[2039,42,40,37],[2087,43,40,35],[2135,44,40,40],[2183,45,40,42],[2231,46,40,44],[2279,47,40,45],[2327,48,40,46],[2375,49,40,43],[2423,50,40,39],[2471,51,40,35],[2519,52,40,39],[2567,53,40,36],[2615,54,40,28],[2663,55,40,24],[2711,56,40,28],[2759,57,40,24],[2807,58,40,26],[2855,59,40,42],[2903,60,40,50],[2951,61,40,48],[2999,62,40,51],[3047,63,40,45],[3095,64,40,50],[3143,65,40,51],[3191,66,40,48],[3239,67,40,51],[3287,68,40,55],[3335,69,40,51],[3383,70,40,44],[3431,71,40,51],[3479,72,40,44],[3527,73,40,49],[3575,74,40,42],[3623,75,40,45],[3671,76,40,43],[3719,77,40,43],[3767,78,40,52],[3815,79,40,57],[3863,80,40,51],[3911,81,40,48],[3959,82,40,50],[4007,83,40,52],[4055,84,40,56],[4103,85,40,53],[4151,86,40,55],[4199,87,40,52],[4247,88,40,50],[4295,89,40,49],[4343,90,40,27],[4391,91,40,38],[4439,92,40,25],[4487,93,40,40],[4535,94,40,40],[4583,95,40,26],[4631,96,40,25],[4679,97,40,29],[4727,98,40,27],[4775,99,40,34],[4823,100,40,41],[4871,101,40,37],[4919,102,40,41],[4967,103,40,36],[5015,104,40,25],[5063,105,40,28],[5111,106,40,27],[5159,107,40,29],[5207,108,40,31],[5255,109,40,30],[5303,110,40,29],[5351,111,40,36],[5399,112,20,32],[5447,113,20,36],[5495,114,20,33],[5543,115,20,34],[5591,116,20,40],[5639,117,20,37],[5687,118,40,53],[5735,119,40,45],[5783,120,40,52],[5831,121,40,47],[5879,122,40,47],[5927,123,40,45],[5975,124,40,46],[6023,125,40,47],[6071,126,40,47],[6119,127,40,61],[6167,128,40,65],[6215,129,40,60],[6263,130,40,68],[6311,131,40,61],[6359,132,40,60],[6407,133,40,59],[6455,134,60,63],[6503,135,20,37],[6551,136,40,26],[6599,137,40,24],[6647,138,40,27],[6695,139,40,26],[6743,140,40,27],[6791,141,40,28],[6839,142,40,26],[6887,143,40,29],[6935,144,40,30],[6983,145,40,36],[7031,146,40,49],[7079,147,40,57],[7127,148,40,51],[7175,149,40,58],[7223,150,40,51],[7271,151,40,55],[7319,152,40,50],[7367,153,40,56],[7415,154,40,29],[7463,155,40,28],[7511,156,40,24],[7559,157,40,23],[7607,158,40,25],[7655,159,40,24],[7703,160,40,31],[7751,161,40,27],[7799,162,40,41],[7847,163,40,29],[7895,164,40,33],[7943,165,40,38],[7991,166,40,36],[8039,167,40,55],[8087,168,40,38],[8135,169,40,40],[8183,170,40,34],[8231,171,40,41],[8279,172,40,40],[8327,173,40,38],[8375,174,40,44],[8423,175,40,36],[8471,176,20,39],[8519,177,20,27],[8567,178,20,30],[8615,179,20,32],[8663,180,20,30],[8711,181,20,33],[8759,182,20,33],[8807,183,20,27],[8855,184,40,50],[8903,185,40,56],[8951,186,40,66],[8999,187,40,59],[9047,188,40,52],[9095,189,40,48],[9143,190,40,47],[9191,191,40,35],[9239,192,30,35],[9287,193,30,28],[9335,194,30,26],[9383,195,30,26],[9431,196,30,27],[9479,197,30,32],[9527,198,30,30],[9575,199,30,33],[9623,200,30,34],[9671,201,30,36],[9713,202,30,36]]}},"macro_spearman":0.04362925711980167,"macro_top15_human_mean":1.9965539879134349,"macro_mae":0.555511762031175,"production_B_scope":null},"pilot":{"rows":89,"all_outputs_valid":true,"source_metrics":{"-esJrBWj2d8":{"frames":116,"spearman":-0.06835905801648398,"constant_ranking":false,"top15_count":18,"top15_human_mean":1.8833333333333333,"mae":0.5991379310344828,"train_mean_constant_mae":0.39834066410151,"threshold_selected_fraction":0.08620689655172414,"threshold_selected_human_mean":1.895,"threshold_low_human_fraction":1.0,"predictions":[[29,0,40,39],[89,1,40,40],[149,2,40,48],[209,3,40,37],[269,4,40,36],[329,5,40,28],[389,6,40,29],[449,7,40,42],[509,8,40,42],[569,9,40,51],[629,10,40,36],[689,11,40,36],[749,12,40,38],[809,13,40,41],[869,14,40,28],[929,15,40,33],[989,16,20,38],[1049,17,20,40],[1109,18,20,45],[1169,19,20,43],[1229,20,20,41],[1289,21,20,56],[1349,22,20,59],[1409,23,20,50],[1469,24,20,60],[1529,25,20,54],[1589,26,20,51],[1649,27,20,48],[1709,28,20,53],[1769,29,20,46],[1829,30,20,42],[1889,31,20,46],[1949,32,40,49],[2009,33,40,57],[2069,34,40,67],[2129,35,40,62],[2189,36,40,62],[2249,37,40,62],[2309,38,40,61],[2369,39,60,49],[2429,40,60,39],[2489,41,60,35],[2549,42,60,39],[2609,43,60,33],[2669,44,60,45],[2729,45,60,34],[2789,46,60,39],[2849,47,60,36],[2909,48,40,37],[2969,49,40,36],[3029,50,40,39],[3089,51,40,42],[3149,52,40,36],[3209,53,40,39],[3269,54,40,46],[3329,55,40,49],[3389,56,40,61],[3449,57,40,48],[3509,58,40,54],[3569,59,40,48],[3629,60,40,46],[3689,61,40,43],[3749,62,40,42],[3809,63,40,52],[3869,64,40,33],[3929,65,40,28],[3989,66,40,31],[4049,67,40,31],[4109,68,40,30],[4169,69,40,33],[4229,70,40,34],[4289,71,40,31],[4349,72,40,31],[4409,73,40,40],[4469,74,40,29],[4529,75,40,31],[4589,76,40,32],[4649,77,40,32],[4709,78,40,41],[4769,79,40,41],[4829,80,20,26],[4889,81,20,27],[4949,82,20,28],[5009,83,20,30],[5069,84,20,29],[5129,85,20,29],[5189,86,20,26],[5249,87,20,30],[5309,88,20,31],[5369,89,40,26],[5429,90,40,29],[5489,91,40,25],[5549,92,40,27],[5609,93,40,32],[5669,94,40,34],[5729,95,40,26],[5789,96,40,28],[5849,97,40,34],[5909,98,40,32],[5969,99,40,34],[6029,100,40,43],[6089,101,40,40],[6149,102,40,42],[6209,103,40,45],[6269,104,40,41],[6329,105,40,43],[6389,106,40,42],[6449,107,40,48],[6509,108,40,41],[6569,109,40,35],[6629,110,40,29],[6689,111,40,28],[6749,112,40,30],[6809,113,40,29],[6869,114,60,30],[6905,115,40,30]]},"4wU_LUjG5Ic":{"frames":84,"spearman":-0.35567717066389043,"constant_ranking":false,"top15_count":13,"top15_human_mean":1.7692307692307694,"mae":0.7220238095238095,"train_mean_constant_mae":0.4194405573132151,"threshold_selected_fraction":0.047619047619047616,"threshold_selected_human_mean":1.3625,"threshold_low_human_fraction":1.0,"predictions":[[23,0,20,39],[71,1,20,28],[119,2,20,32],[167,3,20,44],[215,4,20,57],[263,5,20,60],[311,6,20,52],[359,7,20,46],[407,8,20,53],[455,9,20,50],[503,10,20,50],[551,11,20,43],[599,12,20,43],[647,13,20,41],[695,14,20,36],[743,15,20,38],[791,16,40,38],[839,17,40,35],[887,18,40,44],[935,19,40,41],[983,20,40,40],[1030,21,40,34],[1078,22,40,37],[1126,23,40,37],[1174,24,40,45],[1222,25,40,49],[1270,26,40,68],[1318,27,40,58],[1366,28,40,41],[1414,29,40,50],[1462,30,40,43],[1510,31,40,28],[1558,32,40,24],[1606,33,40,22],[1654,34,40,23],[1702,35,40,35],[1750,36,40,30],[1798,37,40,27],[1846,38,40,26],[1894,39,40,31],[1942,40,40,28],[1990,41,40,29],[2037,42,40,28],[2085,43,40,29],[2133,44,40,27],[2181,45,40,41],[2229,46,40,38],[2277,47,40,43],[2325,48,40,44],[2373,49,40,47],[2421,50,40,37],[2469,51,40,58],[2517,52,40,66],[2565,53,40,61],[2613,54,40,47],[2661,55,40,30],[2709,56,40,27],[2757,57,40,28],[2805,58,40,26],[2853,59,40,28],[2901,60,40,27],[2949,61,40,37],[2997,62,40,40],[3044,63,40,45],[3092,64,40,48],[3140,65,40,44],[3188,66,40,33],[3236,67,40,46],[3284,68,40,47],[3332,69,40,50],[3380,70,40,48],[3428,71,40,36],[3476,72,40,37],[3524,73,40,38],[3572,74,40,41],[3620,75,40,39],[3668,76,40,40],[3716,77,40,27],[3764,78,40,41],[3812,79,40,30],[3860,80,100,31],[3908,81,100,28],[3956,82,100,25],[3992,83,100,25]]},"cjibtmSLxQ4":{"frames":324,"spearman":0.37051259149066484,"constant_ranking":false,"top15_count":49,"top15_human_mean":2.1959183673469385,"mae":0.4729938271604938,"train_mean_constant_mae":0.5084463136475473,"threshold_selected_fraction":0.0,"threshold_selected_human_mean":null,"threshold_low_human_fraction":null,"predictions":[[29,0,40,41],[89,1,40,31],[149,2,40,39],[209,3,40,29],[269,4,40,71],[329,5,40,41],[389,6,40,42],[449,7,40,41],[509,8,40,45],[569,9,40,38],[629,10,40,48],[689,11,40,46],[749,12,40,37],[809,13,40,50],[869,14,40,42],[929,15,40,54],[989,16,40,43],[1048,17,40,28],[1108,18,40,39],[1168,19,40,53],[1228,20,40,51],[1288,21,40,66],[1348,22,40,67],[1408,23,40,36],[1468,24,40,46],[1528,25,40,42],[1588,26,40,43],[1648,27,40,36],[1708,28,40,44],[1768,29,40,34],[1828,30,40,63],[1888,31,40,61],[1948,32,40,39],[2008,33,40,29],[2067,34,40,33],[2127,35,40,34],[2187,36,40,30],[2247,37,40,68],[2307,38,40,33],[2367,39,40,57],[2427,40,40,54],[2487,41,40,70],[2547,42,40,42],[2607,43,40,32],[2667,44,40,33],[2727,45,40,34],[2787,46,40,35],[2847,47,40,40],[2907,48,40,42],[2967,49,40,46],[3027,50,40,49],[3086,51,40,50],[3146,52,40,44],[3206,53,40,27],[3266,54,40,27],[3326,55,40,26],[3386,56,40,25],[3446,57,40,27],[3506,58,40,27],[3566,59,40,27],[3626,60,40,31],[3686,61,40,65],[3746,62,40,71],[3806,63,40,29],[3866,64,40,39],[3926,65,40,41],[3986,66,40,40],[4045,67,40,39],[4105,68,40,39],[4165,69,40,29],[4225,70,40,30],[4285,71,40,45],[4345,72,40,42],[4405,73,40,56],[4465,74,40,39],[4525,75,40,56],[4585,76,40,44],[4645,77,40,45],[4705,78,40,38],[4765,79,40,42],[4825,80,40,38],[4885,81,40,41],[4945,82,40,42],[5005,83,40,41],[5064,84,40,28],[5124,85,40,48],[5184,86,40,51],[5244,87,40,61],[5304,88,40,63],[5364,89,40,62],[5424,90,40,45],[5484,91,40,57],[5544,92,40,46],[5604,93,40,43],[5664,94,40,50],[5724,95,40,61],[5784,96,40,46],[5844,97,40,49],[5904,98,40,45],[5964,99,40,54],[6024,100,40,53],[6083,101,40,45],[6143,102,40,50],[6203,103,40,50],[6263,104,40,35],[6323,105,40,33],[6383,106,40,34],[6443,107,40,31],[6503,108,40,34],[6563,109,40,39],[6623,110,40,43],[6683,111,40,33],[6743,112,40,31],[6803,113,40,36],[6863,114,40,31],[6923,115,40,44],[6983,116,40,50],[7042,117,40,28],[7102,118,40,41],[7162,119,40,40],[7222,120,40,41],[7282,121,40,24],[7342,122,40,27],[7402,123,40,28],[7462,124,40,26],[7522,125,40,45],[7582,126,40,21],[7642,127,40,21],[7702,128,40,33],[7762,129,40,53],[7822,130,40,53],[7882,131,40,52],[7942,132,40,50],[8002,133,40,48],[8061,134,40,24],[8121,135,40,41],[8181,136,40,52],[8241,137,40,52],[8301,138,40,46],[8361,139,40,28],[8421,140,40,24],[8481,141,40,23],[8541,142,40,22],[8601,143,40,22],[8661,144,40,26],[8721,145,40,25],[8781,146,40,34],[8841,147,40,41],[8901,148,40,42],[8961,149,40,29],[9021,150,40,22],[9080,151,40,27],[9140,152,40,37],[9200,153,40,46],[9260,154,40,47],[9320,155,40,35],[9380,156,40,44],[9440,157,40,45],[9500,158,40,42],[9560,159,40,45],[9620,160,30,34],[9680,161,30,51],[9740,162,30,22],[9800,163,30,21],[9860,164,30,31],[9920,165,30,28],[9980,166,30,27],[10039,167,30,23],[10099,168,30,28],[10159,169,30,28],[10219,170,30,24],[10279,171,30,23],[10339,172,30,27],[10399,173,30,23],[10459,174,30,23],[10519,175,30,28],[10579,176,40,32],[10639,177,40,31],[10699,178,40,22],[10759,179,40,23],[10819,180,40,32],[10879,181,40,42],[10939,182,40,28],[10999,183,40,25],[11058,184,40,26],[11118,185,40,27],[11178,186,40,26],[11238,187,40,28],[11298,188,40,38],[11358,189,40,35],[11418,190,40,63],[11478,191,40,46],[11538,192,40,59],[11598,193,40,73],[11658,194,40,53],[11718,195,40,33],[11778,196,40,29],[11838,197,40,35],[11898,198,40,31],[11958,199,40,32],[12018,200,40,33],[12077,201,40,32],[12137,202,40,40],[12197,203,40,36],[12257,204,40,30],[12317,205,40,21],[12377,206,40,22],[12437,207,40,22],[12497,208,20,21],[12557,209,20,21],[12617,210,20,23],[12677,211,20,22],[12737,212,20,21],[12797,213,20,24],[12857,214,20,31],[12917,215,20,27],[12977,216,20,26],[13036,217,20,28],[13096,218,20,30],[13156,219,20,29],[13216,220,20,29],[13276,221,20,29],[13336,222,20,26],[13396,223,20,25],[13456,224,40,29],[13516,225,40,24],[13576,226,40,24],[13636,227,40,27],[13696,228,40,29],[13756,229,40,36],[13816,230,40,36],[13876,231,40,32],[13936,232,40,32],[13996,233,40,33],[14055,234,40,32],[14115,235,40,32],[14175,236,40,30],[14235,237,40,34],[14295,238,40,29],[14355,239,40,29],[14415,240,40,27],[14475,241,40,31],[14535,242,40,32],[14595,243,40,29],[14655,244,40,28],[14715,245,40,28],[14775,246,40,28],[14835,247,40,29],[14895,248,40,29],[14955,249,40,27],[15015,250,40,28],[15074,251,40,27],[15134,252,40,28],[15194,253,40,34],[15254,254,40,32],[15314,255,40,29],[15374,256,40,30],[15434,257,40,29],[15494,258,40,34],[15554,259,40,71],[15614,260,40,57],[15674,261,40,49],[15734,262,40,75],[15794,263,40,36],[15854,264,40,59],[15914,265,40,68],[15974,266,40,36],[16033,267,40,65],[16093,268,40,73],[16153,269,40,28],[16213,270,40,37],[16273,271,40,34],[16333,272,40,46],[16393,273,40,40],[16453,274,40,37],[16513,275,40,45],[16573,276,40,47],[16633,277,40,48],[16693,278,40,47],[16753,279,40,28],[16813,280,40,28],[16873,281,40,26],[16933,282,40,33],[16993,283,40,32],[17052,284,40,34],[17112,285,40,32],[17172,286,40,36],[17232,287,40,32],[17292,288,40,34],[17352,289,40,51],[17412,290,40,55],[17472,291,40,31],[17532,292,40,51],[17592,293,40,50],[17652,294,40,60],[17712,295,40,64],[17772,296,40,56],[17832,297,40,30],[17892,298,40,28],[17952,299,40,29],[18012,300,40,27],[18071,301,40,26],[18131,302,40,27],[18191,303,40,55],[18251,304,40,32],[18311,305,40,44],[18371,306,40,46],[18431,307,40,31],[18491,308,40,48],[18551,309,40,51],[18611,310,40,54],[18671,311,40,40],[18731,312,40,39],[18791,313,40,50],[18851,314,40,53],[18911,315,40,47],[18971,316,40,46],[19030,317,40,45],[19090,318,40,36],[19150,319,40,27],[19210,320,40,29],[19270,321,40,27],[19330,322,40,30],[19383,323,40,30]]},"EYqVtI9YWJA":{"frames":100,"spearman":0.27661893269306503,"constant_ranking":false,"top15_count":15,"top15_human_mean":2.033333333333333,"mae":0.5085,"train_mean_constant_mae":0.5319150340715502,"threshold_selected_fraction":0.06,"threshold_selected_human_mean":2.708333333333333,"threshold_low_human_fraction":0.8333333333333334,"predictions":[[29,0,40,36],[89,1,40,32],[149,2,40,33],[209,3,40,43],[269,4,40,23],[329,5,40,28],[389,6,40,25],[449,7,40,26],[509,8,40,39],[569,9,40,51],[629,10,40,54],[689,11,40,46],[749,12,40,54],[809,13,40,23],[869,14,40,25],[929,15,40,39],[989,16,40,47],[1048,17,40,54],[1108,18,40,46],[1168,19,40,24],[1228,20,40,25],[1288,21,40,42],[1348,22,40,36],[1408,23,40,52],[1468,24,40,31],[1528,25,40,29],[1588,26,40,29],[1648,27,40,29],[1708,28,40,44],[1768,29,40,38],[1828,30,40,42],[1888,31,40,40],[1948,32,40,26],[2008,33,40,31],[2067,34,40,32],[2127,35,40,28],[2187,36,40,29],[2247,37,40,34],[2307,38,40,44],[2367,39,40,39],[2427,40,40,38],[2487,41,40,34],[2547,42,40,42],[2607,43,40,47],[2667,44,40,23],[2727,45,40,26],[2787,46,40,25],[2847,47,40,23],[2907,48,40,34],[2967,49,40,66],[3027,50,40,49],[3086,51,40,43],[3146,52,40,41],[3206,53,40,42],[3266,54,40,41],[3326,55,40,48],[3386,56,40,48],[3446,57,40,60],[3506,58,40,25],[3566,59,40,26],[3626,60,40,31],[3686,61,40,27],[3746,62,40,27],[3806,63,40,27],[3866,64,40,28],[3926,65,40,28],[3986,66,40,53],[4045,67,50,54],[4105,68,50,52],[4165,69,50,55],[4225,70,50,47],[4285,71,50,47],[4345,72,50,70],[4405,73,40,37],[4465,74,40,23],[4525,75,40,23],[4585,76,40,22],[4645,77,40,31],[4705,78,40,28],[4765,79,40,53],[4825,80,40,59],[4885,81,40,55],[4945,82,40,58],[5005,83,40,57],[5064,84,40,57],[5124,85,40,61],[5184,86,40,55],[5244,87,40,40],[5304,88,40,67],[5364,89,40,63],[5424,90,40,61],[5484,91,40,40],[5544,92,40,44],[5604,93,40,46],[5664,94,40,55],[5724,95,40,44],[5784,96,40,36],[5844,97,40,27],[5904,98,40,28],[5936,99,40,28]]},"i3wAGJaaktw":{"frames":79,"spearman":0.0,"constant_ranking":true,"top15_count":12,"top15_human_mean":2.2,"mae":0.5417721518987342,"train_mean_constant_mae":0.5376996042956035,"threshold_selected_fraction":0.0,"threshold_selected_human_mean":null,"threshold_low_human_fraction":null,"predictions":[[29,0,40,31],[89,1,40,31],[149,2,40,64],[209,3,40,55],[269,4,40,48],[329,5,40,58],[389,6,40,41],[449,7,40,40],[509,8,40,41],[569,9,40,44],[629,10,40,39],[689,11,40,36],[749,12,40,37],[809,13,40,37],[869,14,40,55],[929,15,40,55],[989,16,40,52],[1048,17,40,52],[1108,18,40,50],[1168,19,40,50],[1228,20,40,45],[1288,21,40,50],[1348,22,40,47],[1408,23,40,43],[1468,24,40,43],[1528,25,40,49],[1588,26,40,48],[1648,27,40,52],[1708,28,40,64],[1768,29,40,44],[1828,30,40,44],[1888,31,40,54],[1948,32,40,56],[2008,33,40,38],[2067,34,40,33],[2127,35,40,35],[2187,36,40,34],[2247,37,40,36],[2307,38,40,40],[2367,39,40,37],[2427,40,40,37],[2487,41,40,36],[2547,42,40,35],[2607,43,40,38],[2667,44,40,66],[2727,45,40,58],[2787,46,40,72],[2847,47,40,67],[2907,48,40,59],[2967,49,40,67],[3027,50,40,22],[3086,51,40,22],[3146,52,40,21],[3206,53,40,23],[3266,54,40,21],[3326,55,40,24],[3386,56,40,32],[3446,57,40,33],[3506,58,40,32],[3566,59,40,31],[3626,60,40,31],[3686,61,40,36],[3746,62,40,28],[3806,63,40,23],[3866,64,40,22],[3926,65,40,21],[3986,66,40,25],[4045,67,40,23],[4105,68,40,22],[4165,69,40,23],[4225,70,40,30],[4285,71,40,26],[4345,72,40,22],[4405,73,40,22],[4465,74,40,36],[4525,75,40,31],[4585,76,40,39],[4645,77,40,33],[4687,78,40,33]]},"J0nA4VgnoCo":{"frames":293,"spearman":0.1831938755167186,"constant_ranking":false,"top15_count":44,"top15_human_mean":1.5738636363636362,"mae":0.648122866894198,"train_mean_constant_mae":0.5519635838503165,"threshold_selected_fraction":0.04778156996587031,"threshold_selected_human_mean":1.4535714285714287,"threshold_low_human_fraction":1.0,"predictions":[[23,0,20,27],[71,1,40,30],[119,2,40,25],[167,3,40,30],[215,4,40,25],[263,5,40,27],[311,6,40,25],[359,7,40,27],[407,8,40,26],[455,9,40,25],[503,10,40,29],[551,11,40,31],[599,12,40,51],[647,13,40,53],[695,14,40,46],[743,15,40,53],[791,16,40,48],[839,17,40,47],[887,18,40,41],[935,19,40,25],[983,20,40,25],[1030,21,40,31],[1078,22,40,29],[1126,23,40,36],[1174,24,40,26],[1222,25,40,25],[1270,26,40,26],[1318,27,40,26],[1366,28,40,27],[1414,29,40,30],[1462,30,40,33],[1510,31,40,38],[1558,32,40,30],[1606,33,40,47],[1654,34,40,38],[1702,35,40,30],[1750,36,40,30],[1798,37,40,29],[1846,38,40,25],[1894,39,40,29],[1942,40,40,29],[1990,41,40,30],[2037,42,40,27],[2085,43,40,32],[2133,44,40,29],[2181,45,40,26],[2229,46,40,31],[2277,47,40,68],[2325,48,20,68],[2373,49,20,65],[2421,50,20,26],[2469,51,20,29],[2517,52,20,27],[2565,53,20,28],[2613,54,20,33],[2661,55,20,54],[2709,56,20,33],[2757,57,20,35],[2805,58,20,26],[2853,59,20,27],[2901,60,20,28],[2949,61,20,29],[2997,62,20,28],[3044,63,20,28],[3092,64,40,35],[3140,65,40,29],[3188,66,40,25],[3236,67,40,26],[3284,68,40,25],[3332,69,40,27],[3380,70,40,26],[3428,71,40,26],[3476,72,40,26],[3524,73,40,25],[3572,74,40,26],[3620,75,40,26],[3668,76,40,27],[3716,77,40,26],[3764,78,40,27],[3812,79,40,27],[3860,80,20,28],[3908,81,20,30],[3956,82,20,42],[4004,83,20,33],[4051,84,20,41],[4099,85,20,39],[4147,86,20,47],[4195,87,20,34],[4243,88,20,43],[4291,89,20,36],[4339,90,20,40],[4387,91,20,36],[4435,92,20,35],[4483,93,20,36],[4531,94,20,35],[4579,95,20,44],[4627,96,40,35],[4675,97,40,45],[4723,98,40,44],[4771,99,40,43],[4819,100,40,45],[4867,101,40,47],[4915,102,40,46],[4963,103,40,40],[5011,104,40,48],[5058,105,40,42],[5106,106,40,41],[5154,107,40,42],[5202,108,40,43],[5250,109,40,41],[5298,110,40,39],[5346,111,40,41],[5394,112,40,44],[5442,113,40,34],[5490,114,40,30],[5538,115,40,33],[5586,116,40,36],[5634,117,40,48],[5682,118,40,33],[5730,119,40,51],[5778,120,40,54],[5826,121,40,59],[5874,122,40,56],[5922,123,40,53],[5970,124,40,56],[6018,125,40,54],[6065,126,40,53],[6113,127,40,28],[6161,128,20,28],[6209,129,20,30],[6257,130,20,30],[6305,131,20,30],[6353,132,20,39],[6401,133,20,62],[6449,134,20,54],[6497,135,20,55],[6545,136,20,74],[6593,137,20,70],[6641,138,20,52],[6689,139,20,38],[6737,140,20,38],[6785,141,20,38],[6833,142,20,35],[6881,143,20,41],[6929,144,40,42],[6977,145,40,57],[7024,146,40,59],[7072,147,40,56],[7120,148,40,56],[7168,149,40,58],[7216,150,40,63],[7264,151,40,57],[7312,152,40,58],[7360,153,40,56],[7408,154,40,53],[7456,155,40,51],[7504,156,40,47],[7552,157,40,52],[7600,158,40,48],[7648,159,40,52],[7696,160,40,75],[7744,161,40,71],[7792,162,40,59],[7840,163,40,57],[7888,164,40,59],[7936,165,40,63],[7984,166,40,55],[8031,167,40,53],[8079,168,40,66],[8127,169,40,68],[8175,170,40,70],[8223,171,40,57],[8271,172,40,51],[8319,173,40,55],[8367,174,40,57],[8415,175,40,53],[8463,176,40,57],[8511,177,40,56],[8559,178,40,53],[8607,179,40,46],[8655,180,40,44],[8703,181,40,49],[8751,182,40,59],[8799,183,40,59],[8847,184,40,57],[8895,185,40,46],[8943,186,40,44],[8991,187,40,59],[9038,188,40,46],[9086,189,40,43],[9134,190,40,36],[9182,191,40,48],[9230,192,40,45],[9278,193,40,49],[9326,194,40,47],[9374,195,40,46],[9422,196,40,45],[9470,197,40,44],[9518,198,40,46],[9566,199,40,44],[9614,200,60,47],[9662,201,60,43],[9710,202,40,44],[9758,203,40,46],[9806,204,40,44],[9854,205,40,63],[9902,206,40,56],[9950,207,40,30],[9998,208,20,32],[10045,209,20,32],[10093,210,20,31],[10141,211,20,30],[10189,212,20,30],[10237,213,20,34],[10285,214,20,29],[10333,215,20,32],[10381,216,20,34],[10429,217,20,34],[10477,218,20,32],[10525,219,20,29],[10573,220,20,26],[10621,221,20,27],[10669,222,20,28],[10717,223,20,27],[10765,224,40,29],[10813,225,40,50],[10861,226,40,51],[10909,227,40,49],[10957,228,40,51],[11005,229,40,48],[11052,230,40,48],[11100,231,40,48],[11148,232,40,51],[11196,233,40,50],[11244,234,40,48],[11292,235,40,44],[11340,236,40,50],[11388,237,40,30],[11436,238,40,35],[11484,239,40,33],[11532,240,20,30],[11580,241,20,32],[11628,242,20,33],[11676,243,20,34],[11724,244,20,27],[11772,245,20,28],[11820,246,20,26],[11868,247,20,27],[11916,248,20,26],[11964,249,20,25],[12012,250,20,25],[12059,251,20,33],[12107,252,20,30],[12155,253,20,25],[12203,254,20,27],[12251,255,20,26],[12299,256,20,25],[12347,257,20,28],[12395,258,20,25],[12443,259,20,25],[12491,260,20,28],[12539,261,20,27],[12587,262,20,27],[12635,263,20,29],[12683,264,20,26],[12731,265,20,27],[12779,266,20,24],[12827,267,20,24],[12875,268,20,25],[12923,269,20,25],[12971,270,20,24],[13019,271,20,26],[13066,272,40,26],[13114,273,40,28],[13162,274,20,30],[13210,275,40,23],[13258,276,40,26],[13306,277,40,28],[13354,278,40,29],[13402,279,60,28],[13450,280,60,29],[13498,281,60,25],[13546,282,60,23],[13594,283,60,25],[13642,284,60,24],[13690,285,60,26],[13738,286,60,25],[13786,287,60,24],[13834,288,40,30],[13882,289,40,30],[13930,290,60,30],[13978,291,60,29],[14010,292,60,29]]},"JKpqYvAdIsw":{"frames":77,"spearman":0.1936795547464208,"constant_ranking":false,"top15_count":12,"top15_human_mean":2.020833333333333,"mae":0.36948051948051946,"train_mean_constant_mae":0.37971097258788916,"threshold_selected_fraction":0.0,"threshold_selected_human_mean":null,"threshold_low_human_fraction":null,"predictions":[[24,0,40,47],[74,1,40,45],[124,2,40,47],[174,3,40,25],[224,4,40,36],[274,5,40,40],[324,6,40,29],[374,7,40,35],[424,8,40,49],[474,9,40,54],[524,10,40,40],[574,11,40,38],[624,12,40,43],[674,13,40,36],[724,14,40,29],[774,15,40,32],[824,16,40,24],[874,17,40,47],[924,18,40,39],[974,19,40,34],[1024,20,40,50],[1074,21,40,48],[1124,22,40,37],[1174,23,40,49],[1224,24,40,58],[1274,25,40,29],[1324,26,40,55],[1374,27,40,58],[1424,28,40,53],[1474,29,40,61],[1524,30,40,40],[1574,31,40,35],[1624,32,40,35],[1674,33,40,41],[1724,34,40,37],[1774,35,40,41],[1824,36,40,44],[1874,37,40,46],[1924,38,40,46],[1974,39,40,33],[2024,40,40,40],[2074,41,40,43],[2124,42,40,34],[2174,43,40,35],[2224,44,40,39],[2274,45,40,49],[2324,46,40,33],[2374,47,40,38],[2424,48,40,32],[2474,49,40,30],[2524,50,40,33],[2574,51,40,25],[2624,52,40,33],[2674,53,40,37],[2724,54,40,52],[2774,55,40,49],[2824,56,40,45],[2874,57,40,28],[2924,58,40,47],[2974,59,40,42],[3024,60,40,28],[3074,61,40,48],[3124,62,40,52],[3174,63,40,26],[3224,64,40,59],[3274,65,40,56],[3324,66,40,39],[3374,67,40,34],[3424,68,40,30],[3474,69,40,32],[3524,70,40,50],[3574,71,40,42],[3624,72,40,40],[3674,73,40,40],[3724,74,40,42],[3774,75,40,23],[3800,76,20,23]]},"sTEELN-vY30":{"frames":75,"spearman":0.06257761021169796,"constant_ranking":false,"top15_count":12,"top15_human_mean":2.104166666666667,"mae":0.6786666666666668,"train_mean_constant_mae":0.5893703861442365,"threshold_selected_fraction":0.13333333333333333,"threshold_selected_human_mean":1.95,"threshold_low_human_fraction":1.0,"predictions":[[29,0,40,58],[89,1,40,57],[149,2,40,58],[209,3,40,55],[269,4,40,59],[329,5,40,87],[389,6,40,80],[449,7,40,38],[509,8,40,43],[569,9,40,36],[629,10,40,36],[689,11,40,45],[749,12,40,23],[809,13,40,24],[869,14,40,25],[929,15,40,28],[989,16,40,23],[1049,17,40,26],[1109,18,40,30],[1169,19,40,32],[1229,20,40,33],[1289,21,40,30],[1349,22,60,52],[1409,23,60,49],[1469,24,60,50],[1529,25,60,36],[1589,26,60,25],[1649,27,60,42],[1709,28,60,45],[1769,29,60,31],[1829,30,60,30],[1889,31,60,30],[1949,32,40,27],[2009,33,40,55],[2069,34,40,60],[2129,35,40,69],[2189,36,40,58],[2249,37,40,46],[2309,38,40,51],[2369,39,40,52],[2429,40,40,31],[2489,41,40,31],[2549,42,40,29],[2609,43,40,26],[2669,44,40,26],[2729,45,40,24],[2789,46,40,25],[2849,47,40,31],[2909,48,40,30],[2969,49,40,30],[3029,50,40,45],[3089,51,40,37],[3149,52,40,34],[3209,53,40,42],[3269,54,40,40],[3329,55,40,40],[3389,56,40,39],[3449,57,40,31],[3509,58,40,29],[3569,59,40,55],[3629,60,40,57],[3689,61,40,25],[3749,62,40,25],[3809,63,40,34],[3869,64,40,38],[3929,65,40,65],[3989,66,40,46],[4049,67,40,38],[4109,68,40,26],[4169,69,40,22],[4229,70,40,24],[4289,71,40,25],[4349,72,40,26],[4409,73,40,24],[4453,74,40,24]]},"Yi4Ij2NM7U4":{"frames":203,"spearman":0.16115616489932774,"constant_ranking":false,"top15_count":31,"top15_human_mean":1.5758064516129031,"mae":0.5059113300492611,"train_mean_constant_mae":0.49573796166531,"threshold_selected_fraction":0.0049261083743842365,"threshold_selected_human_mean":3.15,"threshold_low_human_fraction":0.0,"predictions":[[23,0,40,28],[71,1,40,25],[119,2,40,26],[167,3,40,28],[215,4,40,25],[263,5,40,26],[311,6,40,30],[359,7,40,29],[407,8,40,29],[455,9,40,26],[503,10,40,27],[551,11,40,29],[599,12,40,27],[647,13,40,30],[695,14,40,30],[743,15,40,24],[791,16,40,29],[839,17,40,28],[887,18,40,26],[935,19,40,26],[983,20,40,26],[1031,21,40,27],[1079,22,40,27],[1127,23,40,27],[1175,24,40,24],[1223,25,40,36],[1271,26,40,49],[1319,27,40,47],[1367,28,40,45],[1415,29,40,58],[1463,30,40,53],[1511,31,40,30],[1559,32,40,26],[1607,33,40,32],[1655,34,40,28],[1703,35,40,24],[1751,36,40,28],[1799,37,40,30],[1847,38,40,23],[1895,39,40,27],[1943,40,40,31],[1991,41,40,28],[2039,42,40,37],[2087,43,40,35],[2135,44,40,40],[2183,45,40,42],[2231,46,40,44],[2279,47,40,45],[2327,48,40,46],[2375,49,40,43],[2423,50,40,39],[2471,51,40,35],[2519,52,40,39],[2567,53,40,36],[2615,54,40,28],[2663,55,40,24],[2711,56,40,28],[2759,57,40,24],[2807,58,40,26],[2855,59,40,42],[2903,60,40,50],[2951,61,40,48],[2999,62,40,51],[3047,63,40,45],[3095,64,40,50],[3143,65,40,51],[3191,66,40,48],[3239,67,40,51],[3287,68,40,55],[3335,69,40,51],[3383,70,40,44],[3431,71,40,51],[3479,72,40,44],[3527,73,40,49],[3575,74,40,42],[3623,75,40,45],[3671,76,40,43],[3719,77,40,43],[3767,78,40,52],[3815,79,40,57],[3863,80,40,51],[3911,81,40,48],[3959,82,40,50],[4007,83,40,52],[4055,84,40,56],[4103,85,40,53],[4151,86,40,55],[4199,87,40,52],[4247,88,40,50],[4295,89,40,49],[4343,90,40,27],[4391,91,40,38],[4439,92,40,25],[4487,93,40,40],[4535,94,40,40],[4583,95,40,26],[4631,96,40,25],[4679,97,40,29],[4727,98,40,27],[4775,99,40,34],[4823,100,40,41],[4871,101,40,37],[4919,102,40,41],[4967,103,40,36],[5015,104,40,25],[5063,105,40,28],[5111,106,40,27],[5159,107,40,29],[5207,108,40,31],[5255,109,40,30],[5303,110,40,29],[5351,111,40,36],[5399,112,20,32],[5447,113,20,36],[5495,114,20,33],[5543,115,20,34],[5591,116,20,40],[5639,117,20,37],[5687,118,40,53],[5735,119,40,45],[5783,120,40,52],[5831,121,40,47],[5879,122,40,47],[5927,123,40,45],[5975,124,40,46],[6023,125,40,47],[6071,126,40,47],[6119,127,40,61],[6167,128,40,65],[6215,129,40,60],[6263,130,40,68],[6311,131,40,61],[6359,132,40,60],[6407,133,40,59],[6455,134,60,63],[6503,135,20,37],[6551,136,40,26],[6599,137,40,24],[6647,138,40,27],[6695,139,40,26],[6743,140,40,27],[6791,141,40,28],[6839,142,40,26],[6887,143,40,29],[6935,144,40,30],[6983,145,40,36],[7031,146,40,49],[7079,147,40,57],[7127,148,40,51],[7175,149,40,58],[7223,150,40,51],[7271,151,40,55],[7319,152,40,50],[7367,153,40,56],[7415,154,40,29],[7463,155,40,28],[7511,156,40,24],[7559,157,40,23],[7607,158,40,25],[7655,159,40,24],[7703,160,40,31],[7751,161,40,27],[7799,162,40,41],[7847,163,40,29],[7895,164,40,33],[7943,165,40,38],[7991,166,40,36],[8039,167,40,55],[8087,168,40,38],[8135,169,40,40],[8183,170,40,34],[8231,171,40,41],[8279,172,40,40],[8327,173,40,38],[8375,174,40,44],[8423,175,40,36],[8471,176,20,39],[8519,177,20,27],[8567,178,20,30],[8615,179,20,32],[8663,180,20,30],[8711,181,20,33],[8759,182,20,33],[8807,183,20,27],[8855,184,40,50],[8903,185,40,56],[8951,186,40,66],[8999,187,40,59],[9047,188,40,52],[9095,189,40,48],[9143,190,40,47],[9191,191,40,35],[9239,192,30,35],[9287,193,30,28],[9335,194,30,26],[9383,195,30,26],[9431,196,30,27],[9479,197,30,32],[9527,198,30,30],[9575,199,30,33],[9623,200,30,34],[9671,201,30,36],[9713,202,30,36]]}},"macro_spearman":0.09152250009750229,"macro_top15_human_mean":1.9284984323578793,"macro_mae":0.5607343447453518,"production_B_scope":null},"production_B":{"rows":89,"all_outputs_valid":true,"source_metrics":{"-esJrBWj2d8":{"frames":116,"spearman":0.43858326737165554,"constant_ranking":false,"top15_count":18,"top15_human_mean":2.363888888888889,"mae":0.39224137931034486,"train_mean_constant_mae":0.39834066410151,"threshold_selected_fraction":0.008620689655172414,"threshold_selected_human_mean":1.5,"threshold_low_human_fraction":1.0,"predictions":[[29,0,30,39],[89,1,30,40],[149,2,30,48],[209,3,30,37],[269,4,30,36],[329,5,30,28],[389,6,30,29],[449,7,30,42],[509,8,30,42],[569,9,30,51],[629,10,30,36],[689,11,30,36],[749,12,30,38],[809,13,30,41],[869,14,30,28],[929,15,30,33],[989,16,40,38],[1049,17,40,40],[1109,18,40,45],[1169,19,40,43],[1229,20,40,41],[1289,21,40,56],[1349,22,40,59],[1409,23,40,50],[1469,24,40,60],[1529,25,40,54],[1589,26,40,51],[1649,27,40,48],[1709,28,40,53],[1769,29,40,46],[1829,30,40,42],[1889,31,40,46],[1949,32,40,49],[2009,33,40,57],[2069,34,40,67],[2129,35,40,62],[2189,36,40,62],[2249,37,40,62],[2309,38,40,61],[2369,39,40,49],[2429,40,40,39],[2489,41,40,35],[2549,42,40,39],[2609,43,40,33],[2669,44,40,45],[2729,45,40,34],[2789,46,40,39],[2849,47,40,36],[2909,48,40,37],[2969,49,40,36],[3029,50,40,39],[3089,51,40,42],[3149,52,40,36],[3209,53,40,39],[3269,54,40,46],[3329,55,40,49],[3389,56,40,61],[3449,57,40,48],[3509,58,40,54],[3569,59,40,48],[3629,60,40,46],[3689,61,40,43],[3749,62,40,42],[3809,63,40,52],[3869,64,30,33],[3929,65,30,28],[3989,66,30,31],[4049,67,30,31],[4109,68,30,30],[4169,69,30,33],[4229,70,30,34],[4289,71,30,31],[4349,72,30,31],[4409,73,30,40],[4469,74,30,29],[4529,75,30,31],[4589,76,30,32],[4649,77,30,32],[4709,78,30,41],[4769,79,30,41],[4829,80,20,26],[4889,81,20,27],[4949,82,20,28],[5009,83,20,30],[5069,84,20,29],[5129,85,20,29],[5189,86,20,26],[5249,87,20,30],[5309,88,20,31],[5369,89,40,26],[5429,90,40,29],[5489,91,40,25],[5549,92,40,27],[5609,93,40,32],[5669,94,40,34],[5729,95,40,26],[5789,96,40,28],[5849,97,40,34],[5909,98,40,32],[5969,99,40,34],[6029,100,40,43],[6089,101,40,40],[6149,102,40,42],[6209,103,40,45],[6269,104,40,41],[6329,105,40,43],[6389,106,40,42],[6449,107,40,48],[6509,108,40,41],[6569,109,40,35],[6629,110,40,29],[6689,111,40,28],[6749,112,40,30],[6809,113,40,29],[6869,114,60,30],[6905,115,40,30]]},"4wU_LUjG5Ic":{"frames":84,"spearman":-0.13281564009356517,"constant_ranking":false,"top15_count":13,"top15_human_mean":2.0,"mae":0.5803571428571429,"train_mean_constant_mae":0.4194405573132151,"threshold_selected_fraction":0.047619047619047616,"threshold_selected_human_mean":1.3625,"threshold_low_human_fraction":1.0,"predictions":[[23,0,40,39],[71,1,40,28],[119,2,40,32],[167,3,40,44],[215,4,40,57],[263,5,40,60],[311,6,40,52],[359,7,40,46],[407,8,40,53],[455,9,40,50],[503,10,40,50],[551,11,40,43],[599,12,40,43],[647,13,40,41],[695,14,40,36],[743,15,40,38],[791,16,40,38],[839,17,40,35],[887,18,40,44],[935,19,40,41],[983,20,40,40],[1030,21,40,34],[1078,22,40,37],[1126,23,40,37],[1174,24,40,45],[1222,25,40,49],[1270,26,40,68],[1318,27,40,58],[1366,28,40,41],[1414,29,40,50],[1462,30,40,43],[1510,31,40,28],[1558,32,40,24],[1606,33,40,22],[1654,34,40,23],[1702,35,40,35],[1750,36,40,30],[1798,37,40,27],[1846,38,40,26],[1894,39,40,31],[1942,40,40,28],[1990,41,40,29],[2037,42,40,28],[2085,43,40,29],[2133,44,40,27],[2181,45,40,41],[2229,46,40,38],[2277,47,40,43],[2325,48,30,44],[2373,49,30,47],[2421,50,30,37],[2469,51,30,58],[2517,52,30,66],[2565,53,30,61],[2613,54,30,47],[2661,55,30,30],[2709,56,30,27],[2757,57,30,28],[2805,58,30,26],[2853,59,30,28],[2901,60,30,27],[2949,61,30,37],[2997,62,30,40],[3044,63,30,45],[3092,64,40,48],[3140,65,40,44],[3188,66,40,33],[3236,67,40,46],[3284,68,40,47],[3332,69,40,50],[3380,70,40,48],[3428,71,40,36],[3476,72,40,37],[3524,73,40,38],[3572,74,40,41],[3620,75,40,39],[3668,76,40,40],[3716,77,40,27],[3764,78,40,41],[3812,79,40,30],[3860,80,100,31],[3908,81,100,28],[3956,82,100,25],[3992,83,100,25]]},"cjibtmSLxQ4":{"frames":324,"spearman":0.17707919086243049,"constant_ranking":false,"top15_count":49,"top15_human_mean":2.113265306122449,"mae":0.5662037037037038,"train_mean_constant_mae":0.5084463136475473,"threshold_selected_fraction":0.09876543209876543,"threshold_selected_human_mean":2.0890625,"threshold_low_human_fraction":0.9375,"predictions":[[29,0,40,41],[89,1,40,31],[149,2,40,39],[209,3,40,29],[269,4,40,71],[329,5,40,41],[389,6,40,42],[449,7,40,41],[509,8,40,45],[569,9,40,38],[629,10,40,48],[689,11,40,46],[749,12,40,37],[809,13,40,50],[869,14,40,42],[929,15,40,54],[989,16,30,43],[1048,17,30,28],[1108,18,30,39],[1168,19,30,53],[1228,20,30,51],[1288,21,30,66],[1348,22,30,67],[1408,23,30,36],[1468,24,30,46],[1528,25,30,42],[1588,26,30,43],[1648,27,30,36],[1708,28,30,44],[1768,29,30,34],[1828,30,30,63],[1888,31,30,61],[1948,32,50,39],[2008,33,50,29],[2067,34,50,33],[2127,35,50,34],[2187,36,50,30],[2247,37,50,68],[2307,38,50,33],[2367,39,50,57],[2427,40,50,54],[2487,41,50,70],[2547,42,50,42],[2607,43,50,32],[2667,44,50,33],[2727,45,50,34],[2787,46,50,35],[2847,47,50,40],[2907,48,30,42],[2967,49,30,46],[3027,50,30,49],[3086,51,30,50],[3146,52,30,44],[3206,53,30,27],[3266,54,30,27],[3326,55,30,26],[3386,56,30,25],[3446,57,30,27],[3506,58,30,27],[3566,59,30,27],[3626,60,30,31],[3686,61,30,65],[3746,62,30,71],[3806,63,30,29],[3866,64,40,39],[3926,65,40,41],[3986,66,40,40],[4045,67,40,39],[4105,68,40,39],[4165,69,40,29],[4225,70,40,30],[4285,71,40,45],[4345,72,40,42],[4405,73,40,56],[4465,74,40,39],[4525,75,40,56],[4585,76,40,44],[4645,77,40,45],[4705,78,40,38],[4765,79,40,42],[4825,80,30,38],[4885,81,30,41],[4945,82,30,42],[5005,83,30,41],[5064,84,30,28],[5124,85,30,48],[5184,86,30,51],[5244,87,30,61],[5304,88,30,63],[5364,89,30,62],[5424,90,30,45],[5484,91,30,57],[5544,92,30,46],[5604,93,30,43],[5664,94,30,50],[5724,95,30,61],[5784,96,50,46],[5844,97,50,49],[5904,98,50,45],[5964,99,50,54],[6024,100,50,53],[6083,101,50,45],[6143,102,50,50],[6203,103,50,50],[6263,104,50,35],[6323,105,50,33],[6383,106,50,34],[6443,107,50,31],[6503,108,50,34],[6563,109,50,39],[6623,110,50,43],[6683,111,50,33],[6743,112,40,31],[6803,113,40,36],[6863,114,40,31],[6923,115,40,44],[6983,116,40,50],[7042,117,40,28],[7102,118,40,41],[7162,119,40,40],[7222,120,40,41],[7282,121,40,24],[7342,122,40,27],[7402,123,40,28],[7462,124,40,26],[7522,125,40,45],[7582,126,40,21],[7642,127,40,21],[7702,128,30,33],[7762,129,30,53],[7822,130,30,53],[7882,131,30,52],[7942,132,30,50],[8002,133,30,48],[8061,134,30,24],[8121,135,30,41],[8181,136,30,52],[8241,137,30,52],[8301,138,30,46],[8361,139,30,28],[8421,140,30,24],[8481,141,30,23],[8541,142,30,22],[8601,143,30,22],[8661,144,30,26],[8721,145,30,25],[8781,146,30,34],[8841,147,30,41],[8901,148,30,42],[8961,149,30,29],[9021,150,30,22],[9080,151,30,27],[9140,152,30,37],[9200,153,30,46],[9260,154,30,47],[9320,155,30,35],[9380,156,30,44],[9440,157,30,45],[9500,158,30,42],[9560,159,30,45],[9620,160,20,34],[9680,161,20,51],[9740,162,20,22],[9800,163,20,21],[9860,164,20,31],[9920,165,20,28],[9980,166,20,27],[10039,167,20,23],[10099,168,20,28],[10159,169,20,28],[10219,170,20,24],[10279,171,20,23],[10339,172,20,27],[10399,173,20,23],[10459,174,20,23],[10519,175,20,28],[10579,176,30,32],[10639,177,30,31],[10699,178,30,22],[10759,179,30,23],[10819,180,30,32],[10879,181,30,42],[10939,182,30,28],[10999,183,30,25],[11058,184,30,26],[11118,185,30,27],[11178,186,30,26],[11238,187,30,28],[11298,188,30,38],[11358,189,30,35],[11418,190,30,63],[11478,191,30,46],[11538,192,40,59],[11598,193,40,73],[11658,194,40,53],[11718,195,40,33],[11778,196,40,29],[11838,197,40,35],[11898,198,40,31],[11958,199,40,32],[12018,200,40,33],[12077,201,40,32],[12137,202,40,40],[12197,203,40,36],[12257,204,40,30],[12317,205,40,21],[12377,206,40,22],[12437,207,40,22],[12497,208,20,21],[12557,209,20,21],[12617,210,20,23],[12677,211,20,22],[12737,212,20,21],[12797,213,20,24],[12857,214,20,31],[12917,215,20,27],[12977,216,20,26],[13036,217,20,28],[13096,218,20,30],[13156,219,20,29],[13216,220,20,29],[13276,221,20,29],[13336,222,20,26],[13396,223,20,25],[13456,224,40,29],[13516,225,40,24],[13576,226,40,24],[13636,227,40,27],[13696,228,40,29],[13756,229,40,36],[13816,230,40,36],[13876,231,40,32],[13936,232,40,32],[13996,233,40,33],[14055,234,40,32],[14115,235,40,32],[14175,236,40,30],[14235,237,40,34],[14295,238,40,29],[14355,239,40,29],[14415,240,30,27],[14475,241,30,31],[14535,242,30,32],[14595,243,30,29],[14655,244,30,28],[14715,245,30,28],[14775,246,30,28],[14835,247,30,29],[14895,248,30,29],[14955,249,30,27],[15015,250,30,28],[15074,251,30,27],[15134,252,30,28],[15194,253,30,34],[15254,254,30,32],[15314,255,30,29],[15374,256,40,30],[15434,257,40,29],[15494,258,40,34],[15554,259,40,71],[15614,260,40,57],[15674,261,40,49],[15734,262,40,75],[15794,263,40,36],[15854,264,40,59],[15914,265,40,68],[15974,266,40,36],[16033,267,40,65],[16093,268,40,73],[16153,269,40,28],[16213,270,40,37],[16273,271,40,34],[16333,272,40,46],[16393,273,40,40],[16453,274,40,37],[16513,275,40,45],[16573,276,40,47],[16633,277,40,48],[16693,278,40,47],[16753,279,40,28],[16813,280,40,28],[16873,281,40,26],[16933,282,40,33],[16993,283,40,32],[17052,284,40,34],[17112,285,40,32],[17172,286,40,36],[17232,287,40,32],[17292,288,20,34],[17352,289,20,51],[17412,290,20,55],[17472,291,20,31],[17532,292,20,51],[17592,293,20,50],[17652,294,20,60],[17712,295,20,64],[17772,296,20,56],[17832,297,20,30],[17892,298,20,28],[17952,299,20,29],[18012,300,20,27],[18071,301,20,26],[18131,302,20,27],[18191,303,20,55],[18251,304,20,32],[18311,305,20,44],[18371,306,20,46],[18431,307,20,31],[18491,308,20,48],[18551,309,20,51],[18611,310,20,54],[18671,311,20,40],[18731,312,20,39],[18791,313,20,50],[18851,314,20,53],[18911,315,20,47],[18971,316,20,46],[19030,317,20,45],[19090,318,20,36],[19150,319,20,27],[19210,320,40,29],[19270,321,40,27],[19330,322,40,30],[19383,323,40,30]]},"EYqVtI9YWJA":{"frames":100,"spearman":-0.12759755308901727,"constant_ranking":false,"top15_count":15,"top15_human_mean":1.6600000000000001,"mae":0.662,"train_mean_constant_mae":0.5319150340715502,"threshold_selected_fraction":0.21,"threshold_selected_human_mean":1.8476190476190475,"threshold_low_human_fraction":1.0,"predictions":[[29,0,40,36],[89,1,40,32],[149,2,40,33],[209,3,40,43],[269,4,40,23],[329,5,40,28],[389,6,40,25],[449,7,40,26],[509,8,40,39],[569,9,40,51],[629,10,40,54],[689,11,40,46],[749,12,40,54],[809,13,40,23],[869,14,40,25],[929,15,40,39],[989,16,40,47],[1048,17,40,54],[1108,18,40,46],[1168,19,40,24],[1228,20,40,25],[1288,21,40,42],[1348,22,40,36],[1408,23,40,52],[1468,24,40,31],[1528,25,40,29],[1588,26,40,29],[1648,27,40,29],[1708,28,40,44],[1768,29,40,38],[1828,30,40,42],[1888,31,40,40],[1948,32,60,26],[2008,33,60,31],[2067,34,60,32],[2127,35,60,28],[2187,36,60,29],[2247,37,60,34],[2307,38,60,44],[2367,39,60,39],[2427,40,60,38],[2487,41,60,34],[2547,42,60,42],[2607,43,60,47],[2667,44,60,23],[2727,45,60,26],[2787,46,60,25],[2847,47,60,23],[2907,48,40,34],[2967,49,40,66],[3027,50,40,49],[3086,51,40,43],[3146,52,40,41],[3206,53,40,42],[3266,54,40,41],[3326,55,40,48],[3386,56,40,48],[3446,57,40,60],[3506,58,40,25],[3566,59,40,26],[3626,60,40,31],[3686,61,40,27],[3746,62,40,27],[3806,63,40,27],[3866,64,40,28],[3926,65,40,28],[3986,66,40,53],[4045,67,55,54],[4105,68,55,52],[4165,69,55,55],[4225,70,55,47],[4285,71,55,47],[4345,72,40,70],[4405,73,40,37],[4465,74,40,23],[4525,75,40,23],[4585,76,40,22],[4645,77,40,31],[4705,78,40,28],[4765,79,40,53],[4825,80,40,59],[4885,81,40,55],[4945,82,40,58],[5005,83,40,57],[5064,84,40,57],[5124,85,40,61],[5184,86,40,55],[5244,87,40,40],[5304,88,40,67],[5364,89,40,63],[5424,90,40,61],[5484,91,40,40],[5544,92,40,44],[5604,93,40,46],[5664,94,40,55],[5724,95,40,44],[5784,96,40,36],[5844,97,40,27],[5904,98,40,28],[5936,99,40,28]]},"i3wAGJaaktw":{"frames":79,"spearman":0.12564417184883483,"constant_ranking":false,"top15_count":12,"top15_human_mean":1.8958333333333333,"mae":0.6784810126582278,"train_mean_constant_mae":0.5376996042956035,"threshold_selected_fraction":0.20253164556962025,"threshold_selected_human_mean":2.24375,"threshold_low_human_fraction":0.8125,"predictions":[[29,0,20,31],[89,1,20,31],[149,2,20,64],[209,3,20,55],[269,4,20,48],[329,5,20,58],[389,6,20,41],[449,7,20,40],[509,8,20,41],[569,9,20,44],[629,10,20,39],[689,11,20,36],[749,12,20,37],[809,13,20,37],[869,14,20,55],[929,15,20,55],[989,16,40,52],[1048,17,40,52],[1108,18,40,50],[1168,19,40,50],[1228,20,40,45],[1288,21,40,50],[1348,22,40,47],[1408,23,40,43],[1468,24,40,43],[1528,25,40,49],[1588,26,40,48],[1648,27,40,52],[1708,28,40,64],[1768,29,40,44],[1828,30,40,44],[1888,31,40,54],[1948,32,50,56],[2008,33,50,38],[2067,34,50,33],[2127,35,50,35],[2187,36,50,34],[2247,37,50,36],[2307,38,50,40],[2367,39,50,37],[2427,40,50,37],[2487,41,50,36],[2547,42,50,35],[2607,43,50,38],[2667,44,50,66],[2727,45,50,58],[2787,46,50,72],[2847,47,50,67],[2907,48,40,59],[2967,49,40,67],[3027,50,40,22],[3086,51,40,22],[3146,52,40,21],[3206,53,40,23],[3266,54,40,21],[3326,55,40,24],[3386,56,40,32],[3446,57,40,33],[3506,58,40,32],[3566,59,40,31],[3626,60,40,31],[3686,61,40,36],[3746,62,40,28],[3806,63,40,23],[3866,64,30,22],[3926,65,30,21],[3986,66,30,25],[4045,67,30,23],[4105,68,30,22],[4165,69,30,23],[4225,70,30,30],[4285,71,30,26],[4345,72,30,22],[4405,73,30,22],[4465,74,30,36],[4525,75,30,31],[4585,76,30,39],[4645,77,30,33],[4687,78,30,33]]},"J0nA4VgnoCo":{"frames":293,"spearman":-0.12741292325209128,"constant_ranking":false,"top15_count":44,"top15_human_mean":1.6068181818181817,"mae":0.8935153583617748,"train_mean_constant_mae":0.5519635838503165,"threshold_selected_fraction":0.12627986348122866,"threshold_selected_human_mean":1.65,"threshold_low_human_fraction":1.0,"predictions":[[23,0,100,27],[71,1,100,30],[119,2,100,25],[167,3,100,30],[215,4,100,25],[263,5,100,27],[311,6,100,25],[359,7,100,27],[407,8,100,26],[455,9,100,25],[503,10,100,29],[551,11,100,31],[599,12,100,51],[647,13,100,53],[695,14,100,46],[743,15,100,53],[791,16,60,48],[839,17,60,47],[887,18,60,41],[935,19,60,25],[983,20,60,25],[1030,21,60,31],[1078,22,60,29],[1126,23,60,36],[1174,24,60,26],[1222,25,60,25],[1270,26,60,26],[1318,27,60,26],[1366,28,60,27],[1414,29,60,30],[1462,30,60,33],[1510,31,60,38],[1558,32,30,30],[1606,33,30,47],[1654,34,30,38],[1702,35,30,30],[1750,36,30,30],[1798,37,30,29],[1846,38,30,25],[1894,39,30,29],[1942,40,30,29],[1990,41,30,30],[2037,42,30,27],[2085,43,30,32],[2133,44,30,29],[2181,45,30,26],[2229,46,30,31],[2277,47,30,68],[2325,48,20,68],[2373,49,20,65],[2421,50,20,26],[2469,51,20,29],[2517,52,20,27],[2565,53,20,28],[2613,54,20,33],[2661,55,20,54],[2709,56,20,33],[2757,57,20,35],[2805,58,20,26],[2853,59,20,27],[2901,60,20,28],[2949,61,20,29],[2997,62,20,28],[3044,63,20,28],[3092,64,40,35],[3140,65,40,29],[3188,66,40,25],[3236,67,40,26],[3284,68,40,25],[3332,69,40,27],[3380,70,40,26],[3428,71,40,26],[3476,72,40,26],[3524,73,40,25],[3572,74,40,26],[3620,75,40,26],[3668,76,40,27],[3716,77,40,26],[3764,78,40,27],[3812,79,40,27],[3860,80,20,28],[3908,81,20,30],[3956,82,20,42],[4004,83,20,33],[4051,84,20,41],[4099,85,20,39],[4147,86,20,47],[4195,87,20,34],[4243,88,20,43],[4291,89,20,36],[4339,90,20,40],[4387,91,20,36],[4435,92,20,35],[4483,93,20,36],[4531,94,20,35],[4579,95,20,44],[4627,96,40,35],[4675,97,40,45],[4723,98,40,44],[4771,99,40,43],[4819,100,40,45],[4867,101,40,47],[4915,102,40,46],[4963,103,40,40],[5011,104,40,48],[5058,105,40,42],[5106,106,40,41],[5154,107,40,42],[5202,108,40,43],[5250,109,40,41],[5298,110,40,39],[5346,111,40,41],[5394,112,20,44],[5442,113,20,34],[5490,114,20,30],[5538,115,20,33],[5586,116,20,36],[5634,117,20,48],[5682,118,20,33],[5730,119,20,51],[5778,120,20,54],[5826,121,20,59],[5874,122,20,56],[5922,123,20,53],[5970,124,20,56],[6018,125,20,54],[6065,126,20,53],[6113,127,20,28],[6161,128,20,28],[6209,129,20,30],[6257,130,20,30],[6305,131,20,30],[6353,132,20,39],[6401,133,20,62],[6449,134,20,54],[6497,135,20,55],[6545,136,20,74],[6593,137,20,70],[6641,138,20,52],[6689,139,20,38],[6737,140,20,38],[6785,141,20,38],[6833,142,20,35],[6881,143,20,41],[6929,144,20,42],[6977,145,20,57],[7024,146,20,59],[7072,147,20,56],[7120,148,20,56],[7168,149,20,58],[7216,150,20,63],[7264,151,20,57],[7312,152,20,58],[7360,153,20,56],[7408,154,20,53],[7456,155,20,51],[7504,156,20,47],[7552,157,20,52],[7600,158,20,48],[7648,159,20,52],[7696,160,40,75],[7744,161,40,71],[7792,162,40,59],[7840,163,40,57],[7888,164,40,59],[7936,165,40,63],[7984,166,40,55],[8031,167,40,53],[8079,168,40,66],[8127,169,40,68],[8175,170,40,70],[8223,171,40,57],[8271,172,40,51],[8319,173,40,55],[8367,174,40,57],[8415,175,40,53],[8463,176,40,57],[8511,177,40,56],[8559,178,40,53],[8607,179,40,46],[8655,180,40,44],[8703,181,40,49],[8751,182,40,59],[8799,183,40,59],[8847,184,40,57],[8895,185,40,46],[8943,186,40,44],[8991,187,40,59],[9038,188,40,46],[9086,189,40,43],[9134,190,40,36],[9182,191,40,48],[9230,192,40,45],[9278,193,40,49],[9326,194,40,47],[9374,195,40,46],[9422,196,40,45],[9470,197,40,44],[9518,198,40,46],[9566,199,40,44],[9614,200,60,47],[9662,201,60,43],[9710,202,40,44],[9758,203,40,46],[9806,204,40,44],[9854,205,40,63],[9902,206,40,56],[9950,207,40,30],[9998,208,20,32],[10045,209,40,32],[10093,210,40,31],[10141,211,40,30],[10189,212,40,30],[10237,213,40,34],[10285,214,40,29],[10333,215,40,32],[10381,216,40,34],[10429,217,40,34],[10477,218,40,32],[10525,219,40,29],[10573,220,40,26],[10621,221,40,27],[10669,222,40,28],[10717,223,40,27],[10765,224,35,29],[10813,225,35,50],[10861,226,35,51],[10909,227,35,49],[10957,228,35,51],[11005,229,35,48],[11052,230,35,48],[11100,231,35,48],[11148,232,35,51],[11196,233,35,50],[11244,234,35,48],[11292,235,35,44],[11340,236,35,50],[11388,237,35,30],[11436,238,35,35],[11484,239,35,33],[11532,240,20,30],[11580,241,20,32],[11628,242,20,33],[11676,243,20,34],[11724,244,20,27],[11772,245,20,28],[11820,246,20,26],[11868,247,20,27],[11916,248,20,26],[11964,249,20,25],[12012,250,20,25],[12059,251,20,33],[12107,252,20,30],[12155,253,20,25],[12203,254,20,27],[12251,255,20,26],[12299,256,40,25],[12347,257,40,28],[12395,258,40,25],[12443,259,40,25],[12491,260,40,28],[12539,261,40,27],[12587,262,40,27],[12635,263,40,29],[12683,264,40,26],[12731,265,40,27],[12779,266,40,24],[12827,267,40,24],[12875,268,40,25],[12923,269,40,25],[12971,270,40,24],[13019,271,40,26],[13066,272,30,26],[13114,273,30,28],[13162,274,30,30],[13210,275,30,23],[13258,276,30,26],[13306,277,30,28],[13354,278,30,29],[13402,279,30,28],[13450,280,30,29],[13498,281,30,25],[13546,282,30,23],[13594,283,30,25],[13642,284,30,24],[13690,285,30,26],[13738,286,30,25],[13786,287,30,24],[13834,288,40,30],[13882,289,40,30],[13930,290,60,30],[13978,291,60,29],[14010,292,60,29]]},"JKpqYvAdIsw":{"frames":77,"spearman":0.095304677271993,"constant_ranking":false,"top15_count":12,"top15_human_mean":2.029166666666667,"mae":0.462987012987013,"train_mean_constant_mae":0.37971097258788916,"threshold_selected_fraction":0.18181818181818182,"threshold_selected_human_mean":1.9928571428571427,"threshold_low_human_fraction":1.0,"predictions":[[24,0,40,47],[74,1,40,45],[124,2,40,47],[174,3,40,25],[224,4,40,36],[274,5,40,40],[324,6,40,29],[374,7,40,35],[424,8,40,49],[474,9,40,54],[524,10,40,40],[574,11,40,38],[624,12,40,43],[674,13,40,36],[724,14,40,29],[774,15,40,32],[824,16,40,24],[874,17,40,47],[924,18,40,39],[974,19,40,34],[1024,20,40,50],[1074,21,40,48],[1124,22,40,37],[1174,23,40,49],[1224,24,40,58],[1274,25,40,29],[1324,26,40,55],[1374,27,40,58],[1424,28,40,53],[1474,29,40,61],[1524,30,40,40],[1574,31,40,35],[1624,32,30,35],[1674,33,30,41],[1724,34,50,37],[1774,35,50,41],[1824,36,50,44],[1874,37,50,46],[1924,38,50,46],[1974,39,50,33],[2024,40,50,40],[2074,41,50,43],[2124,42,50,34],[2174,43,50,35],[2224,44,50,39],[2274,45,50,49],[2324,46,50,33],[2374,47,50,38],[2424,48,40,32],[2474,49,40,30],[2524,50,40,33],[2574,51,40,25],[2624,52,40,33],[2674,53,40,37],[2724,54,40,52],[2774,55,40,49],[2824,56,40,45],[2874,57,40,28],[2924,58,40,47],[2974,59,40,42],[3024,60,40,28],[3074,61,40,48],[3124,62,40,52],[3174,63,40,26],[3224,64,40,59],[3274,65,40,56],[3324,66,20,39],[3374,67,20,34],[3424,68,20,30],[3474,69,40,32],[3524,70,20,50],[3574,71,40,42],[3624,72,40,40],[3674,73,40,40],[3724,74,20,42],[3774,75,20,23],[3800,76,20,23]]},"sTEELN-vY30":{"frames":75,"spearman":-0.04258993484300389,"constant_ranking":false,"top15_count":12,"top15_human_mean":1.7833333333333332,"mae":0.7773333333333333,"train_mean_constant_mae":0.5893703861442365,"threshold_selected_fraction":0.4266666666666667,"threshold_selected_human_mean":1.8828125,"threshold_low_human_fraction":0.9375,"predictions":[[29,0,40,58],[89,1,40,57],[149,2,40,58],[209,3,40,55],[269,4,40,59],[329,5,40,87],[389,6,40,80],[449,7,40,38],[509,8,40,43],[569,9,40,36],[629,10,40,36],[689,11,40,45],[749,12,40,23],[809,13,40,24],[869,14,40,25],[929,15,40,28],[989,16,60,23],[1049,17,60,26],[1109,18,60,30],[1169,19,60,32],[1229,20,60,33],[1289,21,60,30],[1349,22,60,52],[1409,23,60,49],[1469,24,60,50],[1529,25,60,36],[1589,26,60,25],[1649,27,60,42],[1709,28,60,45],[1769,29,60,31],[1829,30,60,30],[1889,31,60,30],[1949,32,50,27],[2009,33,50,55],[2069,34,50,60],[2129,35,50,69],[2189,36,50,58],[2249,37,50,46],[2309,38,50,51],[2369,39,50,52],[2429,40,50,31],[2489,41,50,31],[2549,42,50,29],[2609,43,50,26],[2669,44,50,26],[2729,45,50,24],[2789,46,50,25],[2849,47,50,31],[2909,48,40,30],[2969,49,40,30],[3029,50,40,45],[3089,51,40,37],[3149,52,40,34],[3209,53,40,42],[3269,54,40,40],[3329,55,40,40],[3389,56,40,39],[3449,57,40,31],[3509,58,40,29],[3569,59,40,55],[3629,60,40,57],[3689,61,40,25],[3749,62,40,25],[3809,63,40,34],[3869,64,40,38],[3929,65,40,65],[3989,66,40,46],[4049,67,40,38],[4109,68,40,26],[4169,69,40,22],[4229,70,40,24],[4289,71,40,25],[4349,72,40,26],[4409,73,40,24],[4453,74,40,24]]},"Yi4Ij2NM7U4":{"frames":203,"spearman":-0.008162873908860203,"constant_ranking":false,"top15_count":31,"top15_human_mean":1.6903225806451612,"mae":0.5857142857142856,"train_mean_constant_mae":0.49573796166531,"threshold_selected_fraction":0.06896551724137931,"threshold_selected_human_mean":2.0714285714285716,"threshold_low_human_fraction":1.0,"predictions":[[23,0,40,28],[71,1,40,25],[119,2,40,26],[167,3,40,28],[215,4,40,25],[263,5,40,26],[311,6,40,30],[359,7,40,29],[407,8,40,29],[455,9,40,26],[503,10,40,27],[551,11,40,29],[599,12,40,27],[647,13,40,30],[695,14,40,30],[743,15,40,24],[791,16,40,29],[839,17,40,28],[887,18,40,26],[935,19,40,26],[983,20,40,26],[1031,21,40,27],[1079,22,40,27],[1127,23,40,27],[1175,24,40,24],[1223,25,40,36],[1271,26,40,49],[1319,27,40,47],[1367,28,40,45],[1415,29,40,58],[1463,30,40,53],[1511,31,40,30],[1559,32,30,26],[1607,33,30,32],[1655,34,30,28],[1703,35,30,24],[1751,36,30,28],[1799,37,30,30],[1847,38,30,23],[1895,39,30,27],[1943,40,30,31],[1991,41,30,28],[2039,42,30,37],[2087,43,30,35],[2135,44,30,40],[2183,45,30,42],[2231,46,30,44],[2279,47,30,45],[2327,48,40,46],[2375,49,40,43],[2423,50,40,39],[2471,51,40,35],[2519,52,40,39],[2567,53,40,36],[2615,54,40,28],[2663,55,40,24],[2711,56,40,28],[2759,57,40,24],[2807,58,40,26],[2855,59,40,42],[2903,60,40,50],[2951,61,40,48],[2999,62,40,51],[3047,63,40,45],[3095,64,40,50],[3143,65,40,51],[3191,66,40,48],[3239,67,40,51],[3287,68,40,55],[3335,69,40,51],[3383,70,40,44],[3431,71,40,51],[3479,72,40,44],[3527,73,40,49],[3575,74,40,42],[3623,75,40,45],[3671,76,40,43],[3719,77,40,43],[3767,78,40,52],[3815,79,40,57],[3863,80,30,51],[3911,81,30,48],[3959,82,30,50],[4007,83,30,52],[4055,84,30,56],[4103,85,30,53],[4151,86,30,55],[4199,87,30,52],[4247,88,30,50],[4295,89,30,49],[4343,90,30,27],[4391,91,30,38],[4439,92,30,25],[4487,93,30,40],[4535,94,30,40],[4583,95,30,26],[4631,96,30,25],[4679,97,30,29],[4727,98,30,27],[4775,99,30,34],[4823,100,30,41],[4871,101,30,37],[4919,102,30,41],[4967,103,30,36],[5015,104,30,25],[5063,105,30,28],[5111,106,30,27],[5159,107,30,29],[5207,108,30,31],[5255,109,30,30],[5303,110,30,29],[5351,111,30,36],[5399,112,20,32],[5447,113,20,36],[5495,114,20,33],[5543,115,20,34],[5591,116,20,40],[5639,117,20,37],[5687,118,20,53],[5735,119,20,45],[5783,120,20,52],[5831,121,20,47],[5879,122,20,47],[5927,123,20,45],[5975,124,20,46],[6023,125,20,47],[6071,126,20,47],[6119,127,20,61],[6167,128,40,65],[6215,129,40,60],[6263,130,40,68],[6311,131,40,61],[6359,132,40,60],[6407,133,40,59],[6455,134,40,63],[6503,135,20,37],[6551,136,40,26],[6599,137,40,24],[6647,138,40,27],[6695,139,40,26],[6743,140,40,27],[6791,141,40,28],[6839,142,40,26],[6887,143,40,29],[6935,144,40,30],[6983,145,40,36],[7031,146,60,49],[7079,147,60,57],[7127,148,60,51],[7175,149,60,58],[7223,150,60,51],[7271,151,60,55],[7319,152,60,50],[7367,153,60,56],[7415,154,60,29],[7463,155,60,28],[7511,156,60,24],[7559,157,60,23],[7607,158,60,25],[7655,159,60,24],[7703,160,40,31],[7751,161,40,27],[7799,162,40,41],[7847,163,40,29],[7895,164,40,33],[7943,165,40,38],[7991,166,40,36],[8039,167,40,55],[8087,168,40,38],[8135,169,40,40],[8183,170,40,34],[8231,171,40,41],[8279,172,40,40],[8327,173,40,38],[8375,174,40,44],[8423,175,40,36],[8471,176,20,39],[8519,177,20,27],[8567,178,20,30],[8615,179,20,32],[8663,180,20,30],[8711,181,20,33],[8759,182,20,33],[8807,183,40,27],[8855,184,40,50],[8903,185,40,56],[8951,186,40,66],[8999,187,40,59],[9047,188,40,52],[9095,189,40,48],[9143,190,40,47],[9191,191,40,35],[9239,192,40,35],[9287,193,40,28],[9335,194,40,26],[9383,195,40,26],[9431,196,40,27],[9479,197,40,32],[9527,198,40,30],[9575,199,40,33],[9623,200,40,34],[9671,201,40,36],[9713,202,40,36]]}},"macro_spearman":0.04422582024093067,"macro_top15_human_mean":1.9047364767564463,"macro_mae":0.6220925809917585,"production_B_scope":"Same adapter under new image-score prompt; NOT original B native-video pipeline comparison"}},"source_deltas":{"-esJrBWj2d8":[0.5501529963348132,0.3305555555555557],"4wU_LUjG5Ic":[0.877596644629586,0.7538461538461536],"EYqVtI9YWJA":[0.4693351641806818,0.4700000000000002],"J0nA4VgnoCo":[0.5792029713088823,1.078409090909091],"JKpqYvAdIsw":[-0.06886546184878686,0.20833333333333393],"Yi4Ij2NM7U4":[0.6042051325088404,1.067741935483871],"cjibtmSLxQ4":[0.16295088378464156,0.14693877551020407],"i3wAGJaaktw":[0.44833238118557756,-0.15000000000000036],"sTEELN-vY30":[0.6853906699845506,-0.07916666666666661]},"source_bootstrap95":{"macro_spearman":[0.2954748974839695,0.6400322592634471],"macro_top15_utility":[0.1529160912940675,0.7167301024095378],"native_macro_proxy_f":[-0.0010960742498937347,0.21032592871357847]},"worst_spearman_delta":-0.06886546184878686,"positive_sources":8,"visual_dependency":{"rows":[{"id":"3eYKfiOEJNs:fixedgrid:0001","swap_source":"youtube:0tmA_C6XwfM","conditions":[{"mode":"normal","assistant_nll":0.8200708627700806,"pixel_tensor_sha256":"0dc1c0606dc0f50932caaed7b56ca64b7d362641e803537a5d4c874033d98b03"},{"mode":"cross_source_swap","assistant_nll":0.8710305094718933,"pixel_tensor_sha256":"078564d38973dbeae498b19190d2132f57e4581bfee83d820c536090aee95411"}],"swap_minus_normal":0.050959646701812744},{"id":"gzDbaEs1Rlg:fixedgrid:0000","swap_source":"youtube:HT5vyqe0Xaw","conditions":[{"mode":"normal","assistant_nll":0.7899965047836304,"pixel_tensor_sha256":"08ed78a91395c60b3c8c00ce875016d0cedd94a9d3df78dabcb907b13705950a"},{"mode":"cross_source_swap","assistant_nll":0.7763553261756897,"pixel_tensor_sha256":"8d4b6ea63271e3055ec3dba366e98fe5e9d1620735b49109cbf931a2895147df"}],"swap_minus_normal":-0.013641178607940674},{"id":"RBCABdttQmI:fixedgrid:0001","swap_source":"youtube:E11zDS9XGzg","conditions":[{"mode":"normal","assistant_nll":0.9889384508132935,"pixel_tensor_sha256":"2049f49c20bbd036c574df3ab40014691867a337b76f05133b4b23cfd029d1ea"},{"mode":"cross_source_swap","assistant_nll":1.0257600545883179,"pixel_tensor_sha256":"36b3ccbbb695796c644084754d83083af0ca5828764c2bb7fe6783a9db7fbdd5"}],"swap_minus_normal":0.036821603775024414},{"id":"xmEERLqJ2kU:fixedgrid:0006","swap_source":"youtube:qqR6AEXwxoQ","conditions":[{"mode":"normal","assistant_nll":0.8494411110877991,"pixel_tensor_sha256":"29ab0ce5cbfe66f478518900d78292618c59e8dcdc1f7d3ec5f610baf99e932d"},{"mode":"cross_source_swap","assistant_nll":0.8756667971611023,"pixel_tensor_sha256":"b16bbbd9b4d9c69d1e119e09bb68ace8c5d1064bbfa629960c533f1592b68e92"}],"swap_minus_normal":0.026225686073303223},{"id":"z_6gVvQb2d0:fixedgrid:0003","swap_source":"youtube:oDXZc0tZe04","conditions":[{"mode":"normal","assistant_nll":0.8537896871566772,"pixel_tensor_sha256":"f5bbc9c0b5307c801db1b933ec8c8853d75d60e6f21378a6b03ad47c21730a97"},{"mode":"cross_source_swap","assistant_nll":0.9818277359008789,"pixel_tensor_sha256":"8e338a48897b63661a81d973b5596aa37de475c177bf47b24e08592f70760e34"}],"swap_minus_normal":0.12803804874420166},{"id":"fWutDQy1nnY:fixedgrid:0003","swap_source":"youtube:VuWGsYPqAX8","conditions":[{"mode":"normal","assistant_nll":0.840081512928009,"pixel_tensor_sha256":"3763b2bc6f26415888678fdd07c3761a8aad3f7a241593d3bc0c25f3a8516376"},{"mode":"cross_source_swap","assistant_nll":1.0011471509933472,"pixel_tensor_sha256":"201756c0c17e17fbdc77fca6431a6a3e32341c091a95aa2ee8b1a7f98017dae2"}],"swap_minus_normal":0.16106563806533813},{"id":"0tmA_C6XwfM:fixedgrid:0000","swap_source":"youtube:3eYKfiOEJNs","conditions":[{"mode":"normal","assistant_nll":0.9011664390563965,"pixel_tensor_sha256":"078564d38973dbeae498b19190d2132f57e4581bfee83d820c536090aee95411"},{"mode":"cross_source_swap","assistant_nll":0.9298934936523438,"pixel_tensor_sha256":"0dc1c0606dc0f50932caaed7b56ca64b7d362641e803537a5d4c874033d98b03"}],"swap_minus_normal":0.028727054595947266},{"id":"HT5vyqe0Xaw:fixedgrid:0000","swap_source":"youtube:gzDbaEs1Rlg","conditions":[{"mode":"normal","assistant_nll":0.8942046761512756,"pixel_tensor_sha256":"8d4b6ea63271e3055ec3dba366e98fe5e9d1620735b49109cbf931a2895147df"},{"mode":"cross_source_swap","assistant_nll":0.9364846348762512,"pixel_tensor_sha256":"08ed78a91395c60b3c8c00ce875016d0cedd94a9d3df78dabcb907b13705950a"}],"swap_minus_normal":0.042279958724975586},{"id":"E11zDS9XGzg:fixedgrid:0012","swap_source":"youtube:RBCABdttQmI","conditions":[{"mode":"normal","assistant_nll":0.8409370183944702,"pixel_tensor_sha256":"36b3ccbbb695796c644084754d83083af0ca5828764c2bb7fe6783a9db7fbdd5"},{"mode":"cross_source_swap","assistant_nll":0.9492754936218262,"pixel_tensor_sha256":"2049f49c20bbd036c574df3ab40014691867a337b76f05133b4b23cfd029d1ea"}],"swap_minus_normal":0.10833847522735596},{"id":"qqR6AEXwxoQ:fixedgrid:0004","swap_source":"youtube:xmEERLqJ2kU","conditions":[{"mode":"normal","assistant_nll":0.9859880805015564,"pixel_tensor_sha256":"b16bbbd9b4d9c69d1e119e09bb68ace8c5d1064bbfa629960c533f1592b68e92"},{"mode":"cross_source_swap","assistant_nll":1.1765576601028442,"pixel_tensor_sha256":"29ab0ce5cbfe66f478518900d78292618c59e8dcdc1f7d3ec5f610baf99e932d"}],"swap_minus_normal":0.19056957960128784},{"id":"oDXZc0tZe04:fixedgrid:0005","swap_source":"youtube:z_6gVvQb2d0","conditions":[{"mode":"normal","assistant_nll":0.8130439519882202,"pixel_tensor_sha256":"8e338a48897b63661a81d973b5596aa37de475c177bf47b24e08592f70760e34"},{"mode":"cross_source_swap","assistant_nll":0.7810807824134827,"pixel_tensor_sha256":"f5bbc9c0b5307c801db1b933ec8c8853d75d60e6f21378a6b03ad47c21730a97"}],"swap_minus_normal":-0.03196316957473755},{"id":"VuWGsYPqAX8:fixedgrid:0000","swap_source":"youtube:fWutDQy1nnY","conditions":[{"mode":"normal","assistant_nll":0.9086798429489136,"pixel_tensor_sha256":"201756c0c17e17fbdc77fca6431a6a3e32341c091a95aa2ee8b1a7f98017dae2"},{"mode":"cross_source_swap","assistant_nll":1.0285454988479614,"pixel_tensor_sha256":"3763b2bc6f26415888678fdd07c3761a8aad3f7a241593d3bc0c25f3a8516376"}],"swap_minus_normal":0.11986565589904785}],"mean_swap_minus_normal":0.07060724993546803,"normal_better_rows":10,"visual_dependency_gate":true,"source":"TRAIN_ONLY_FIXED_HASH_12_FULL_ROWS","not_highlight_quality":true},"native_selector_analysis":{"new":{"-esJrBWj2d8":{"native_frames":6912,"selected_frames":780,"selected_fraction":0.11284722222222222,"selected_human_mean":2.233974358974359,"selected_human_below3_fraction":0.9230769230769231,"threshold3_human_proxy_precision":0.07692307692307693,"threshold3_human_proxy_recall":0.14285714285714285,"threshold3_human_proxy_f":0.1,"AIC_score":false,"bin_expansion_is_assumption":true},"4wU_LUjG5Ic":{"native_frames":4005,"selected_frames":0,"selected_fraction":0.0,"selected_human_mean":null,"selected_human_below3_fraction":null,"threshold3_human_proxy_precision":0,"threshold3_human_proxy_recall":0.0,"threshold3_human_proxy_f":0.0,"AIC_score":false,"bin_expansion_is_assumption":true},"cjibtmSLxQ4":{"native_frames":19406,"selected_frames":299,"selected_fraction":0.015407605895083994,"selected_human_mean":2.082107023411371,"selected_human_below3_fraction":1.0,"threshold3_human_proxy_precision":0.0,"threshold3_human_proxy_recall":0.0,"threshold3_human_proxy_f":0.0,"AIC_score":false,"bin_expansion_is_assumption":true},"EYqVtI9YWJA":{"native_frames":5939,"selected_frames":598,"selected_fraction":0.10069035191109614,"selected_human_mean":2.6254180602006687,"selected_human_below3_fraction":0.8996655518394648,"threshold3_human_proxy_precision":0.10033444816053512,"threshold3_human_proxy_recall":0.14285714285714285,"threshold3_human_proxy_f":0.11787819253438114,"AIC_score":false,"bin_expansion_is_assumption":true},"i3wAGJaaktw":{"native_frames":4700,"selected_frames":0,"selected_fraction":0.0,"selected_human_mean":null,"selected_human_below3_fraction":null,"threshold3_human_proxy_precision":0,"threshold3_human_proxy_recall":0.0,"threshold3_human_proxy_f":0.0,"AIC_score":false,"bin_expansion_is_assumption":true},"J0nA4VgnoCo":{"native_frames":14019,"selected_frames":0,"selected_fraction":0.0,"selected_human_mean":null,"selected_human_below3_fraction":null,"threshold3_human_proxy_precision":0,"threshold3_human_proxy_recall":0.0,"threshold3_human_proxy_f":0.0,"AIC_score":false,"bin_expansion_is_assumption":true},"JKpqYvAdIsw":{"native_frames":3802,"selected_frames":0,"selected_fraction":0.0,"selected_human_mean":null,"selected_human_below3_fraction":null,"threshold3_human_proxy_precision":0,"threshold3_human_proxy_recall":0.0,"threshold3_human_proxy_f":0.0,"AIC_score":false,"bin_expansion_is_assumption":true},"sTEELN-vY30":{"native_frames":4468,"selected_frames":660,"selected_fraction":0.1477170993733214,"selected_human_mean":2.6087121212121214,"selected_human_below3_fraction":0.8181818181818182,"threshold3_human_proxy_precision":0.18181818181818182,"threshold3_human_proxy_recall":0.4,"threshold3_human_proxy_f":0.25,"AIC_score":false,"bin_expansion_is_assumption":true},"Yi4Ij2NM7U4":{"native_frames":9731,"selected_frames":432,"selected_fraction":0.04439420409002158,"selected_human_mean":3.0084490740740737,"selected_human_below3_fraction":0.3333333333333333,"threshold3_human_proxy_precision":0.6666666666666666,"threshold3_human_proxy_recall":0.75,"threshold3_human_proxy_f":0.7058823529411765,"AIC_score":false,"bin_expansion_is_assumption":true}},"base":{"-esJrBWj2d8":{"native_frames":6912,"selected_frames":600,"selected_fraction":0.08680555555555555,"selected_human_mean":1.897,"selected_human_below3_fraction":0.9983333333333333,"threshold3_human_proxy_precision":0.0016666666666666668,"threshold3_human_proxy_recall":0.002380952380952381,"threshold3_human_proxy_f":0.00196078431372549,"AIC_score":false,"bin_expansion_is_assumption":true},"4wU_LUjG5Ic":{"native_frames":4005,"selected_frames":168,"selected_fraction":0.041947565543071164,"selected_human_mean":1.3785714285714286,"selected_human_below3_fraction":1.0,"threshold3_human_proxy_precision":0.0,"threshold3_human_proxy_recall":0.0,"threshold3_human_proxy_f":0.0,"AIC_score":false,"bin_expansion_is_assumption":true},"cjibtmSLxQ4":{"native_frames":19406,"selected_frames":0,"selected_fraction":0.0,"selected_human_mean":null,"selected_human_below3_fraction":null,"threshold3_human_proxy_precision":0,"threshold3_human_proxy_recall":0.0,"threshold3_human_proxy_f":0.0,"AIC_score":false,"bin_expansion_is_assumption":true},"EYqVtI9YWJA":{"native_frames":5939,"selected_frames":360,"selected_fraction":0.060616265364539484,"selected_human_mean":2.7083333333333335,"selected_human_below3_fraction":0.8333333333333334,"threshold3_human_proxy_precision":0.16666666666666666,"threshold3_human_proxy_recall":0.14285714285714285,"threshold3_human_proxy_f":0.15384615384615385,"AIC_score":false,"bin_expansion_is_assumption":true},"i3wAGJaaktw":{"native_frames":4700,"selected_frames":0,"selected_fraction":0.0,"selected_human_mean":null,"selected_human_below3_fraction":null,"threshold3_human_proxy_precision":0,"threshold3_human_proxy_recall":0.0,"threshold3_human_proxy_f":0.0,"AIC_score":false,"bin_expansion_is_assumption":true},"J0nA4VgnoCo":{"native_frames":14019,"selected_frames":640,"selected_fraction":0.04565232898209573,"selected_human_mean":1.4537499999999999,"selected_human_below3_fraction":1.0,"threshold3_human_proxy_precision":0.0,"threshold3_human_proxy_recall":0.0,"threshold3_human_proxy_f":0.0,"AIC_score":false,"bin_expansion_is_assumption":true},"JKpqYvAdIsw":{"native_frames":3802,"selected_frames":0,"selected_fraction":0.0,"selected_human_mean":null,"selected_human_below3_fraction":null,"threshold3_human_proxy_precision":0,"threshold3_human_proxy_recall":0.0,"threshold3_human_proxy_f":0.0,"AIC_score":false,"bin_expansion_is_assumption":true},"sTEELN-vY30":{"native_frames":4468,"selected_frames":0,"selected_fraction":0.0,"selected_human_mean":null,"selected_human_below3_fraction":null,"threshold3_human_proxy_precision":0,"threshold3_human_proxy_recall":0.0,"threshold3_human_proxy_f":0.0,"AIC_score":false,"bin_expansion_is_assumption":true},"Yi4Ij2NM7U4":{"native_frames":9731,"selected_frames":48,"selected_fraction":0.004932689343335731,"selected_human_mean":3.1458333333333326,"selected_human_below3_fraction":0.020833333333333332,"threshold3_human_proxy_precision":0.9791666666666666,"threshold3_human_proxy_recall":0.12239583333333333,"threshold3_human_proxy_f":0.2175925925925926,"AIC_score":false,"bin_expansion_is_assumption":true}},"pilot":{"-esJrBWj2d8":{"native_frames":6912,"selected_frames":600,"selected_fraction":0.08680555555555555,"selected_human_mean":1.897,"selected_human_below3_fraction":0.9983333333333333,"threshold3_human_proxy_precision":0.0016666666666666668,"threshold3_human_proxy_recall":0.002380952380952381,"threshold3_human_proxy_f":0.00196078431372549,"AIC_score":false,"bin_expansion_is_assumption":true},"4wU_LUjG5Ic":{"native_frames":4005,"selected_frames":168,"selected_fraction":0.041947565543071164,"selected_human_mean":1.3785714285714286,"selected_human_below3_fraction":1.0,"threshold3_human_proxy_precision":0.0,"threshold3_human_proxy_recall":0.0,"threshold3_human_proxy_f":0.0,"AIC_score":false,"bin_expansion_is_assumption":true},"cjibtmSLxQ4":{"native_frames":19406,"selected_frames":0,"selected_fraction":0.0,"selected_human_mean":null,"selected_human_below3_fraction":null,"threshold3_human_proxy_precision":0,"threshold3_human_proxy_recall":0.0,"threshold3_human_proxy_f":0.0,"AIC_score":false,"bin_expansion_is_assumption":true},"EYqVtI9YWJA":{"native_frames":5939,"selected_frames":360,"selected_fraction":0.060616265364539484,"selected_human_mean":2.7083333333333335,"selected_human_below3_fraction":0.8333333333333334,"threshold3_human_proxy_precision":0.16666666666666666,"threshold3_human_proxy_recall":0.14285714285714285,"threshold3_human_proxy_f":0.15384615384615385,"AIC_score":false,"bin_expansion_is_assumption":true},"i3wAGJaaktw":{"native_frames":4700,"selected_frames":0,"selected_fraction":0.0,"selected_human_mean":null,"selected_human_below3_fraction":null,"threshold3_human_proxy_precision":0,"threshold3_human_proxy_recall":0.0,"threshold3_human_proxy_f":0.0,"AIC_score":false,"bin_expansion_is_assumption":true},"J0nA4VgnoCo":{"native_frames":14019,"selected_frames":640,"selected_fraction":0.04565232898209573,"selected_human_mean":1.4537499999999999,"selected_human_below3_fraction":1.0,"threshold3_human_proxy_precision":0.0,"threshold3_human_proxy_recall":0.0,"threshold3_human_proxy_f":0.0,"AIC_score":false,"bin_expansion_is_assumption":true},"JKpqYvAdIsw":{"native_frames":3802,"selected_frames":0,"selected_fraction":0.0,"selected_human_mean":null,"selected_human_below3_fraction":null,"threshold3_human_proxy_precision":0,"threshold3_human_proxy_recall":0.0,"threshold3_human_proxy_f":0.0,"AIC_score":false,"bin_expansion_is_assumption":true},"sTEELN-vY30":{"native_frames":4468,"selected_frames":600,"selected_fraction":0.13428827215756492,"selected_human_mean":1.95,"selected_human_below3_fraction":1.0,"threshold3_human_proxy_precision":0.0,"threshold3_human_proxy_recall":0.0,"threshold3_human_proxy_f":0.0,"AIC_score":false,"bin_expansion_is_assumption":true},"Yi4Ij2NM7U4":{"native_frames":9731,"selected_frames":48,"selected_fraction":0.004932689343335731,"selected_human_mean":3.1458333333333326,"selected_human_below3_fraction":0.020833333333333332,"threshold3_human_proxy_precision":0.9791666666666666,"threshold3_human_proxy_recall":0.12239583333333333,"threshold3_human_proxy_f":0.2175925925925926,"AIC_score":false,"bin_expansion_is_assumption":true}},"production_B":{"-esJrBWj2d8":{"native_frames":6912,"selected_frames":60,"selected_fraction":0.008680555555555556,"selected_human_mean":1.4991666666666668,"selected_human_below3_fraction":1.0,"threshold3_human_proxy_precision":0.0,"threshold3_human_proxy_recall":0.0,"threshold3_human_proxy_f":0.0,"AIC_score":false,"bin_expansion_is_assumption":true},"4wU_LUjG5Ic":{"native_frames":4005,"selected_frames":168,"selected_fraction":0.041947565543071164,"selected_human_mean":1.3785714285714286,"selected_human_below3_fraction":1.0,"threshold3_human_proxy_precision":0.0,"threshold3_human_proxy_recall":0.0,"threshold3_human_proxy_f":0.0,"AIC_score":false,"bin_expansion_is_assumption":true},"cjibtmSLxQ4":{"native_frames":19406,"selected_frames":1918,"selected_fraction":0.09883541172833145,"selected_human_mean":2.0891032325338896,"selected_human_below3_fraction":0.9374348279457768,"threshold3_human_proxy_precision":0.06256517205422316,"threshold3_human_proxy_recall":0.09090909090909091,"threshold3_human_proxy_f":0.07411982705373688,"AIC_score":false,"bin_expansion_is_assumption":true},"EYqVtI9YWJA":{"native_frames":5939,"selected_frames":1259,"selected_fraction":0.2119885502609867,"selected_human_mean":1.8478554408260524,"selected_human_below3_fraction":1.0,"threshold3_human_proxy_precision":0.0,"threshold3_human_proxy_recall":0.0,"threshold3_human_proxy_f":0.0,"AIC_score":false,"bin_expansion_is_assumption":true},"i3wAGJaaktw":{"native_frames":4700,"selected_frames":959,"selected_fraction":0.20404255319148937,"selected_human_mean":2.244108446298227,"selected_human_below3_fraction":0.8123044838373306,"threshold3_human_proxy_precision":0.18769551616266944,"threshold3_human_proxy_recall":0.5,"threshold3_human_proxy_f":0.27293404094010615,"AIC_score":false,"bin_expansion_is_assumption":true},"J0nA4VgnoCo":{"native_frames":14019,"selected_frames":1743,"selected_fraction":0.12433126471217633,"selected_human_mean":1.6539013195639707,"selected_human_below3_fraction":1.0,"threshold3_human_proxy_precision":0.0,"threshold3_human_proxy_recall":0.0,"threshold3_human_proxy_f":0.0,"AIC_score":false,"bin_expansion_is_assumption":true},"JKpqYvAdIsw":{"native_frames":3802,"selected_frames":700,"selected_fraction":0.1841136244082062,"selected_human_mean":1.9929999999999999,"selected_human_below3_fraction":1.0,"threshold3_human_proxy_precision":0.0,"threshold3_human_proxy_recall":0.0,"threshold3_human_proxy_f":0.0,"AIC_score":false,"bin_expansion_is_assumption":true},"sTEELN-vY30":{"native_frames":4468,"selected_frames":1920,"selected_fraction":0.4297224709042077,"selected_human_mean":1.8827343749999998,"selected_human_below3_fraction":0.9375,"threshold3_human_proxy_precision":0.0625,"threshold3_human_proxy_recall":0.4,"threshold3_human_proxy_f":0.10810810810810811,"AIC_score":false,"bin_expansion_is_assumption":true},"Yi4Ij2NM7U4":{"native_frames":9731,"selected_frames":672,"selected_fraction":0.06905765080670023,"selected_human_mean":2.0723214285714286,"selected_human_below3_fraction":1.0,"threshold3_human_proxy_precision":0.0,"threshold3_human_proxy_recall":0.0,"threshold3_human_proxy_f":0.0,"AIC_score":false,"bin_expansion_is_assumption":true}}},"selector_threshold":{"threshold_x20":49,"rule":"TRAIN_HUMAN_FIXED_GRID_NEAREST_RANK_80TH_PERCENTILE; scores>=threshold; empty allowed","train_file_sha256":"3eb93e2585679f0c24d71b5d13ece101b79aea53b15671948362581d116db62f","fixed_bin_extension":"Entire label-independent 2-second ordinal domain; assumption not semantic boundary gold"},"development_seen_before":true,"independent_AIC_quality_reference":null,"no_validation_based_recipe_retry":true}
```


## 原文件全文：reports/annotation_iteration_20261010/contest_results/completion.json
字节=3057；SHA256=b9865a2cb079deeccc7d96f13ffd0c78a372920c4f193f2b7b1a40458d2ef3fb

```json
{
  "utc": "2026-10-09T18:55:13.023341+00:00",
  "status": "PASS_COMPLETE_ONE_426_NEW_TRAINED_IMAGE_SELECTOR_EXPERIMENTAL_ZIP",
  "nontest": {
    "status": "PASS_COMPLETE_IMAGE_SCORE_237STEP_8B_EXPERIMENTAL_ZIP",
    "scope": "nontest",
    "candidate": "/home/inspur/aic_video_work/runs/annotation_iteration_20261010_v2/contest_v1/nontest_01/candidate_IMAGE_SCORE_237STEP_8B.zip",
    "zip_bytes": 241,
    "zip_sha256": "5256ba390a52dbd45e5a75d0c66d9224cdbbbc4b3eea8e14f04d3d394971cc4f",
    "videos": 8,
    "selected_frames": 0,
    "empty_videos": 8,
    "samples": 32,
    "blocks": 8,
    "adapter_sha256": "1f39afb662f77661f008bc6000a054b9d838b988558ef0b762e2d98975d94933",
    "logical_parameters": 8774791408,
    "training_optimizer_steps": 237,
    "old_spatial_source_field": {
      "field_frames.jsonl": "c4b53cb7d95442ecaa4c8fa6b82b027fd5779370230a2b97f8c8796526386aed",
      "field_shots.jsonl": "cf4a873053bd2baf24343043eb36f835a5853ce232b409489915329f161c0375",
      "anchor_requests.jsonl": "f630e725ddff54c590a4062c39b98c1b7233773b8c0a391f271378ac157283a7",
      "anchor_output.jsonl": "1ffd45d72c723ec71f973d6b24f5e72d052ddf3f6e3b51150a2e68bacfc1532d"
    },
    "spatial_model_calls": 0,
    "official_score": null,
    "uploaded": false,
    "production_replaced": false,
    "independent_validation_sha256": "13a22aee2a8548cdb31376ca75484e4c279d0fc9ac1eba11062b5c557b2af6d4",
    "quality_evidence": "SEEN_TVSUM_DEVELOPMENT_PROXY_ONLY; NATIVE_PROXY_F_CI_CROSSES_ZERO; AIC_GENERALIZATION_UNKNOWN"
  },
  "rematch": {
    "status": "PASS_COMPLETE_IMAGE_SCORE_237STEP_8B_EXPERIMENTAL_ZIP",
    "scope": "rematch",
    "candidate": "/home/inspur/aic_video_work/runs/annotation_iteration_20261010_v2/contest_v1/rematch_01/candidate_IMAGE_SCORE_237STEP_8B.zip",
    "zip_bytes": 12384,
    "zip_sha256": "01969ab4c8221b279dfa58fe1c9f3c5c47cd01fe8cd7dea312bde93cdb3d6325",
    "videos": 426,
    "selected_frames": 3189,
    "empty_videos": 407,
    "samples": 4439,
    "blocks": 510,
    "adapter_sha256": "1f39afb662f77661f008bc6000a054b9d838b988558ef0b762e2d98975d94933",
    "logical_parameters": 8774791408,
    "training_optimizer_steps": 237,
    "old_spatial_source_field": {
      "field_frames.jsonl": "17ba37aadc4cf705e1ff95a78a58d8befcab9e34f7132ef0775f1ed1df0d8bca",
      "field_shots.jsonl": "8e81df10c685527145069cd9c65316ab6341c9da7d6e39bb282ed6c60ce12f1e",
      "anchor_requests.jsonl": "9cb7c4e36597dc8ae723ac3b686b2c3b1f04d5982503478fdf19ee72b18c4798",
      "anchor_output.jsonl": "8f83cd967d7d1f95243ac4ae3cddc7fdb78abb3d4842a78f81f6b187fb1562ab"
    },
    "spatial_model_calls": 0,
    "official_score": null,
    "uploaded": false,
    "production_replaced": false,
    "independent_validation_sha256": "5fdc30627443473133534fab61b27cd2387f1ec947fff49f49d4b5d885b491cf",
    "quality_evidence": "SEEN_TVSUM_DEVELOPMENT_PROXY_ONLY; NATIVE_PROXY_F_CI_CROSSES_ZERO; AIC_GENERALIZATION_UNKNOWN"
  },
  "production_replaced": false,
  "official_score": null,
  "uploaded": false,
  "prior_costs_preserved": true
}
```


## 原文件全文：reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/b_sft8b_package_v3/PROTOCOL.md
字节=4313；SHA256=9dfb8ecf1442568b7738dde2095b2ef4da930c6679782eba55f5c77060cd2e4d

```md
# B8B 最终 adapter 复赛候选

v3工程兼容勘误：训练max_sequence_length=8192原样冻结，不改变任何训练/开发输入或既有结果。v2把该训练内存界错误用于复赛推理；真实相同processor的64帧HD合成CPU输入为12048token，基座原生上下文262144。新独立推理合同max16384，无截断、无帧数或像素改动。真实12048token合成GPU生成/有限选择分数/输出合同、参数与全基座身份通过后才进入复赛恢复。v2成功窗口对象逐个保留，仅原明确发生于generate之前的sequence guard失败及未处理窗口各生成一次，不重跑成功窗口、开发或既有完整非测试链。新扩大的是推理入口准入界，不回写旧冻结协议和失败结果，也不能写成全量复赛原输入<=8192。

继承v2已通过的NONTEST8/427帧/65同帧8B锚点/独立严格ZIP证据；时间提示词、processor、64帧、几何、JSON约束、空间及CPU镜头算法均保持。新的12项CPU检查包含真实Windows时间格式与HD合成输入量纲，4实际native processor case复核。官网上传未授权。

用户“生成一下包中”授权生成Linux完成版8B候选；本轮不上传官网。先按训练前冻结的104/96弱开发单次比较通过停止门，再用原非测试8来源完整链路验收，最后自动426源/521窗口推理并严格打包。Mac训练保持独立。

完整模型参数8,782,459,120，唯一固定Qwen3-VL-8B基座权重在时间和空间中共享计一次。时间用最终5epoch/r16 adapter，空间使用相同8B冻结原生基座、无时间adapter、无二元头、无独立4B。两个阶段分进程加载同样权重，无重复下载。实际加载后的全部基座字节再次与训练冻结哈希比较。

时间保留原R7/A提示词、原最多64 source ordinal抽样与实际原processor默认视频像素预算、30秒窗口/末窗0.2秒资格、greedy256token。新生产版本自始使用已有A_FORMAT_CONSTRAINED_RECOVERY_V1生成时JSON合同：1–5段、有限数、排序非交叠和真实末端，最多4位小数。开发比较遵守原固定greedy无约束协议，生产加合同与开发解码不同，必须区分；不事后裁段/删段/造合法空、调提示词或时间阈值。不是为测试失败挑窗口重试，全部521窗一次确定算法。

输入沿用已审核v4 426元数据/身份/clock registry，416CFR和10native；PTS转换/分数端点/单帧与odd-padding原合同保持。CPU以新8B真实processor跑1/3/63/64合成timestamp测试；源decoder已有合成identity证据仍绑定原冻结实现，新增顺序OpenCV源ordinal读取由非测试实际shots/spatial重开像素逐字节验证。

空间保持原主体中心提示词/128token、合法最大crop几何、HSV .35/GRAY .18镜头阈值、最多8 source-frame锚点间隔与镜头内线性插值。改变基座4B至同一8B是必要参量规模变更，不能单独承诺空间或官方收益。为消除已确证随机seek身份问题，shots和space均从源ordinal0顺序消费并逐帧SHA核验，不随机定位、不用旧测试框/ROI/弱构图框/静默fallback。不展示测试像素或原始模型输出给外部模型。

原8非测试源、v4manifest与registry、代码、最终adapter/训练报告、基座文件、CPU证据逐SHA冻结。所有输出exclusive-create；门未通过或窗口/空间失败STOP并保留，禁止覆盖重试/少交源。100confirm不读取。GPU阶段必须属既有共享gpu_run.py实际祖先进程，继续追加账本与7200秒偏移，累计GPU无限。

本次开发与完整非测试链通过后才进入比赛阶段；空间按真实帧/锚点以及新8B非测试实测耗时登记单次止时与产物占用，不用旧4B速度。每阶段用Windows存活桥接刷新Mac唯一工作根实时容量，Linux动态测量，加入Mac剩余已登记产物与阶段预计输出，合计不超过80GiB，不下载权重/媒体、不抢占外部任务。

最终ZIP仅含predictions.jsonl，426源、全部选择帧合法且同源同帧、完整provenance/重建一致，独立strict loader通过、无缺失/重复/越界、ZIP CRC/最终SHA与本地交付双端一致。格式/工程通过与弱教师指标只分别说明各自证据；官方得分等待用户上传。原33.81 A包保留。

```


## 原文件全文：reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/b_sft8b_package_v3/runtime.py
字节=21797；SHA256=9d86d5f5b8248a8ba4fd97f2ff511cf6c1f3722ec8d290a7257eff95f7ee5002

```py
"""Single pinned 8B base, temporal final LoRA, native spatial base only."""
import contextlib
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

ROOT=Path('/home/inspur/aic_video_work')
RUN=ROOT/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
HERE=RUN/'b_sft8b_package_v3'
CODE=RUN/'baseline_a_pts_v1'
sys.path[:0]=[str(CODE),str(CODE/'vendor'),str(RUN/'baseline_a_format_recovery_v1'),
              str(RUN/'temporal_sft8b_v1')]

def require(ok,message):
    if not ok: raise RuntimeError(message)
def read(path):return json.loads(Path(path).read_text())
def rows(path):return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(8<<20),b''):h.update(block)
    return h.hexdigest()
def write(path,value):
    with Path(path).open('x') as f:f.write(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def verify():
    lock=read(HERE/'source_lock.json')
    for path,digest in lock['files'].items(): require(sha(path)==digest,'package source identity changed: '+path)
    a=read(RUN/'temporal_sft8b_dev_v1/admission.json')
    for path,digest in a['files'].items(): require(sha(path)==digest,'fixed training/model identity changed: '+path)
    return a
def inputs(scope):
    a=read(HERE/'inputs.json')[scope]
    require(sha(a['manifest'])==a['manifest_sha256'],'metadata manifest changed')
    from pts_contract import load_clocks
    manifest=read(a['manifest']);clocks=load_clocks(manifest,a['registry'],a['registry_sha256'])
    return a,manifest,clocks

def stage_admission(stage,scope,out):
    decision=read(RUN/'temporal_sft8b_dev_v1/decision.json')
    require(decision['status']=='PASS_FROZEN_WEAK_DEV_GATE','frozen developer gate has not passed')
    admission=read(HERE/('rematch_B8B_v3_'+scope+'_'+stage+'_01.admission.json'))
    require(admission.get('authorized') is True and admission.get('scope')==scope and admission.get('stage')==stage and
        admission.get('output')==str(Path(out)) and admission.get('source_lock_sha256')==sha(HERE/'source_lock.json') and
        admission.get('dev_decision_sha256')==sha(RUN/'temporal_sft8b_dev_v1/decision.json'),'phase admission identity mismatch')
    require(read(HERE/'processor_cpu_01.json')['status']=='PASS_ACTUAL_8B_NATIVE_PROCESSOR','native processor evidence missing')
    if scope=='rematch':
        require(read(RUN/'b_sft8b_package_v2/nontest_01/package.stage.json')['status']=='PASS_COMPLETE_8B_PACKAGE_NOT_SCORED_NOT_UPLOADED','unchanged non-test full chain gate has not passed')
        require(read(HERE/'long_probe_01/probe.stage.json')['status']=='PASS_SYNTHETIC_LONG_INPUT_8B_INFERENCE','actual long input probe has not passed')
    if stage=='spatial':require(read(Path(out)/'schedule.stage.json')['status']=='PASS_EXACT_SCHEDULING','exact scheduling missing')

class OrdinalReader:
    """Start at ordinal zero, never random seek. Selected gaps remain shot boundaries."""
    def __init__(self,item,clock):
        from pts_contract import BRANCH_NATIVE
        self.native=clock['branch']==BRANCH_NATIVE;self.item=item;self.next=0;self.last=None
        if self.native:
            from native_frames import VerifiedNativeReader
            self.reader=VerifiedNativeReader(item['source_path'],item,clock)
        else:
            import cv2
            self.reader=cv2.VideoCapture(item['source_path'])
            require(self.reader.isOpened(),'source decoder open failed')
    def get(self,ordinal,expected_sha=None):
        require(type(ordinal) is int and 0<=ordinal<self.item['n_frames'],'invalid source ordinal')
        if self.native:frame=self.reader.read(ordinal)
        else:
            require(ordinal>=self.next-1,'backward source ordinal rejected')
            while self.next<=ordinal:
                ok,self.last=self.reader.read();require(ok,'sequential decode failed');self.next+=1
            frame=self.last
        require(frame.shape==(self.item['height'],self.item['width'],3),'decoded geometry changed')
        pixel=hashlib.sha256(memoryview(frame).cast('B')).hexdigest()
        if expected_sha is not None:require(pixel==expected_sha,'same-frame byte identity changed')
        return frame,pixel
    def close(self):
        if not self.native:self.reader.release()

def temporal(scope,out):
    a=verify()
    stage_admission('temporal',scope,out)
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    # CUDA before native decoder imports, matching accepted training initialization.
    import torch
    torch.cuda.init()
    import decord
    from transformers import AutoProcessor,Qwen3VLForConditionalGeneration
    from peft import PeftModel
    from pts_contract import BRANCH_CFR,window_schedule,native_clip_plan,parse_native_segments
    from native_frames import build_native_clip
    from exact_pts import exact_native_pts,verify_native_encoding
    from constrained_json import ascii_token_candidates,make_prefix_constraint
    from train_sft import unique_parameters
    from verify_saved_smoke import canonical_frozen_hash
    bound,manifest,clocks=inputs(scope);out=Path(out);out.mkdir(exist_ok=True)
    tc=load(CODE/'vendor/temporal_common.py','package_tc')
    start_time=time.monotonic()
    base=Qwen3VLForConditionalGeneration.from_pretrained(a['model_dir'],local_files_only=True,torch_dtype=torch.bfloat16,
        device_map={'':'cuda:0'},low_cpu_mem_usage=True,attn_implementation='sdpa')
    model=PeftModel.from_pretrained(base,a['adapter'],is_trainable=False).eval()
    count=sum(p.numel() for _,p in unique_parameters(model));require(count==8782459120,'complete 8B parameter inventory changed')
    frozen=canonical_frozen_hash(model,torch)
    expected=read(RUN/'temporal_sft8b_full_v1/train_01/train_report.json')['freeze_evidence']['adapter_off']
    require(frozen==expected,'loaded frozen base differs from accepted training base')
    processor=AutoProcessor.from_pretrained(a['model_dir'],local_files_only=True,min_pixels=tc.MAX_PIXELS,max_pixels=tc.MAX_PIXELS)
    prompt=processor.apply_chat_template([{'role':'user','content':[{'type':'text','text':tc.PROMPT}]}],
        tokenize=False,add_generation_prompt=True,enable_thinking=False)
    prompt=prompt.replace('<|im_start|>user\n','<|im_start|>user\n<|vision_start|><|video_pad|><|vision_end|>',1)
    eos=model.generation_config.eos_token_id
    if isinstance(eos,int):eos=[eos]
    candidates=ascii_token_candidates(processor.tokenizer)
    failures=0;windows=0
    recovery=read(HERE/'partial_recovery_inputs.json') if scope=='rematch' else None
    previous={r['video_id']:r for r in rows(recovery['partial_path'])} if recovery else {}
    if recovery:require(sha(recovery['partial_path'])==recovery['partial_sha256'],'preserved partial output changed')
    reused=regenerated=0
    with (out/'temporal.jsonl').open('x') as stream:
        for i,item in enumerate(manifest['records'],1):
            require(sha(item['source_path'])==item['source_sha256'],'source hash changed')
            clock=clocks[item['video_id']];fps=item['fps_num']/item['fps_den']
            source=dict(video_id=item['video_id'],targetRatioWH=item['targetRatioWH'],video_path=item['source_path'],
                n_frames=item['n_frames'],fps=fps,arm='B_8B_FINAL_CONSTRAINED',windows=[])
            for j,(start,end) in enumerate(window_schedule(item,manifest['kind'],clock)):
                one=time.monotonic();windows+=1
                old=previous.get(item['video_id'],{}).get('windows',[])
                if j<len(old) and old[j].get('output_valid') is True:
                    kept=old[j]
                    require(kept['status']=='MODEL_OK' and kept['start_sec']==start and kept['end_sec']==end and not kept['parse_errors'],'old successful window identity mismatch')
                    source['windows'].append(kept);reused+=1;continue
                if j<len(old):
                    require(old[j]['status']=='INFERENCE_FAILURE' and old[j]['parse_errors']==['RuntimeError: expanded temporal sequence exceeds training contract'],'recovery admits only pre-generation input-limit failure')
                    regenerated+=1
                w=dict(index=j,start_sec=start,end_sec=end,status='INFERENCE_FAILURE',output_valid=False,
                    parsed_segments=None,parse_errors=[],parse_warnings=[],raw_output='')
                try:
                    if clock['branch']==BRANCH_CFR:
                        arr,md,info=tc.build_virtual_clip(item['source_path'],start,end)
                        require(info['source_total_frames']==item['n_frames'] and abs(info['source_fps']-fps)<=max(1e-6,fps*1e-6),'temporal source count/FPS changed')
                        require(arr.shape[1:]==(item['height'],item['width'],3),'temporal source geometry changed')
                        encoded=processor(text=[prompt],videos=[torch.from_numpy(arr).permute(0,3,1,2)],video_metadata=[md],
                            padding=True,truncation=False,do_sample_frames=False,return_tensors='pt')
                    else:
                        plan=native_clip_plan(clock,start,end);arr,md=build_native_clip(item['source_path'],item,clock,plan)
                        with exact_native_pts(processor,plan,fps) as identity:
                            encoded=processor(text=[prompt],videos=[torch.from_numpy(arr).permute(0,3,1,2)],video_metadata=[md],
                                padding=True,truncation=False,do_sample_frames=False,return_tensors='pt')
                            verify_native_encoding(processor,encoded,identity)
                        info=dict(n_sampled=plan['n_sampled'])
                        w.update(clock_branch=clock['branch'],clock_record_sha256=clock['clock_record_sha256'],
                            source_frame_ids=plan['source_frame_ids'],native_processor_identity=identity)
                    require(encoded['input_ids'].shape[1]<=16384,'expanded inference sequence exceeds separately admitted 16384 contract')
                    encoded=encoded.to('cuda');prefix=int(encoded['input_ids'].shape[1])
                    constraint=make_prefix_constraint(processor.tokenizer,prefix,end-start,candidate_token_ids=candidates,eos_token_ids=eos)
                    with torch.inference_mode():
                        generated=model.generate(**encoded,do_sample=False,max_new_tokens=256,prefix_allowed_tokens_fn=constraint)
                    torch.cuda.synchronize();ids=generated[0,prefix:];constraint.assert_complete(ids)
                    raw=processor.tokenizer.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False)
                    if clock['branch']==BRANCH_CFR:parsed,errors,warnings=tc.parse_segments(raw,end-start)
                    else:parsed,errors,warnings,events=parse_native_segments(raw,end-start);w['native_parse_representation_events']=events
                    w.update(status='MODEL_OK' if parsed is not None else 'PARSE_FAILURE',output_valid=parsed is not None,
                        parsed_segments=parsed,parse_errors=errors,parse_warnings=warnings,raw_output=raw,
                        sampled_frames=info['n_sampled'],constraint_stats=constraint.stats)
                    del encoded,generated,arr
                except Exception as exc:w['parse_errors']=[type(exc).__name__+': '+str(exc)]
                failures+=int(not w['output_valid']);w['seconds']=time.monotonic()-one;source['windows'].append(w)
            stream.write(json.dumps(source,sort_keys=True)+'\n');stream.flush()
            progress=dict(scope=scope,stage='TEMPORAL',videos=i,total=len(manifest['records']),windows=windows,failures=failures,
                wall_seconds=time.monotonic()-start_time)
            temp=out/'progress.tmp';temp.write_text(json.dumps(progress));temp.replace(out/'progress.json')
            print(json.dumps(progress),flush=True)
    report=dict(status='PASS_TEMPORAL_EXECUTION' if failures==0 else 'STOP_TEMPORAL_FAILURES',videos=len(manifest['records']),
        windows=windows,invalid_windows=failures,logical_parameters=count,base_hash=frozen,adapter_sha256=sha(Path(a['adapter'])/'adapter_model.safetensors'),
        output_sha256=sha(out/'temporal.jsonl'),manifest_sha256=bound['manifest_sha256'],wall_seconds=time.monotonic()-start_time,
        generation_time_constraint=True,posthoc_segment_rewrite=False,failure_to_empty_conversions=0,uploaded=False)
    report.update(inference_max_sequence_length=16384,training_max_sequence_length_unchanged=8192,
        reused_successful_windows=reused,regenerated_pre_generation_guard_failures=regenerated)
    if recovery:
        require(reused==recovery['successful_windows_to_keep'] and regenerated==recovery['pre_generation_guard_failures'],
            'complete preserved/recovered window denominator changed')
        report.update(original_successful_window_objects_unchanged=True,old_partial_sha256=recovery['partial_sha256'])
    write(out/'temporal.stage.json',report);require(failures==0,'temporal failures block candidate')

def spatial(scope,out):
    a=verify()
    stage_admission('spatial',scope,out)
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    import torch
    torch.cuda.init()
    bound,manifest,clocks=inputs(scope);out=Path(out)
    from pts_contract import validate_frame_request
    from train_sft import unique_parameters
    from verify_saved_smoke import canonical_frozen_hash
    from PIL import Image
    import cv2
    baseline=load(ROOT/'inference/baseline_qwen3vl.py','spatial_baseline_8b')
    started=time.monotonic()
    # Same pinned weight bytes; no separate 4B, head, temporal LoRA or optimizer.
    model=baseline.Qwen3VL(a['model_dir'],device_map={'':'cuda:0'})
    count=sum(p.numel() for _,p in unique_parameters(model.model));require(count==8767123696,'spatial base count changed')
    for p in model.model.parameters():p.requires_grad_(False)
    frozen=canonical_frozen_hash(model.model,torch)
    require(frozen==read(RUN/'temporal_sft8b_full_v1/train_01/train_report.json')['freeze_evidence']['adapter_off'],'spatial native base does not equal trained frozen base')
    metadata={r['video_id']:r for r in manifest['records']}; requests=rows(out/'anchor_requests.jsonl')
    require(requests and len({(r['video_id'],r['source_frame']) for r in requests})==len(requests),'anchor denominator invalid')
    current=None;reader=None;failures=0;measure=[]
    with (out/'anchor_output.jsonl').open('x') as stream:
        try:
            for i,request in enumerate(requests,1):
                one=time.monotonic()
                rec=dict(video_id=request['video_id'],source_frame=request['source_frame'],anchor_request_sha256=request['anchor_request_sha256'],
                    spatial_source='QWEN_ANCHOR_SAME_FRAME',used_fallback=False,box_xyw=None,raw_output='',parse_error=None,status='DECODE_OR_MODEL_FAILURE')
                try:
                    item=validate_frame_request(request,metadata)
                    if current!=item['video_id']:
                        if reader is not None:reader.close()
                        require(sha(item['source_path'])==item['source_sha256'],'spatial source bytes changed')
                        reader=OrdinalReader(item,clocks[item['video_id']]);current=item['video_id']
                    frame,pixel=reader.get(request['source_frame'],request['expected_pixel_sha256']);rec['decoded_pixel_sha256']=pixel
                    image=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB));tw,th=request['target_ratio_wh']
                    raw=model.predict_focus(image,(tw,th),max_new_tokens=baseline.DEFAULT_CROP_TOKENS);rec['raw_output']=raw
                    center=baseline.parse_focus_norm(raw,image.width,image.height)
                    require(center is not None,'no valid native focus')
                    crop_w,crop_h=baseline.compute_crop_size(image.width,image.height,tw,th)
                    box=baseline.center_to_box(center[0],center[1],image.width,image.height,crop_w,crop_h)
                    require(baseline.validate_box(box,image.width,image.height,tw,th),'illegal native crop')
                    rec.update(status='MODEL_OK',box_xyw=[int(x) for x in box],decoder_identity='SEQUENTIAL_FROM_SOURCE_ORDINAL_ZERO')
                except Exception as exc:rec['parse_error']=type(exc).__name__+': '+str(exc)
                rec['seconds']=time.monotonic()-one;measure.append(rec['seconds']);failures+=rec['status']!='MODEL_OK'
                stream.write(json.dumps(rec,sort_keys=True)+'\n');stream.flush()
                if i%25==0 or i==len(requests):
                    progress=dict(stage='SPATIAL',scope=scope,anchors=i,total=len(requests),failures=failures,wall_seconds=time.monotonic()-started)
                    temp=out/'progress.tmp';temp.write_text(json.dumps(progress));temp.replace(out/'progress.json');print(json.dumps(progress),flush=True)
        finally:
            if reader is not None:reader.close()
    report=dict(status='PASS_SAME_FRAME_NATIVE_8B_SPACE' if failures==0 else 'STOP_SPATIAL_FAILURES',rows=len(requests),invalid=failures,
        manifest_sha256=bound['manifest_sha256'],requests_sha256=sha(out/'anchor_requests.jsonl'),output_sha256=sha(out/'anchor_output.jsonl'),
        wall_seconds=time.monotonic()-started,measured_seconds_per_anchor=sum(measure)/len(measure),
        base_hash=frozen,spatial_base_parameters=count,complete_pipeline_parameters=8782459120,shared_base_counted_once=True,
        temporal_adapter_enabled=False,weak_roi_inputs_used=0,old_test_boxes_used=0,silent_fallbacks=0,uploaded=False)
    write(out/'spatial.stage.json',report);require(failures==0,'native spatial failures block candidate')

def long_probe(scope,out):
    a=verify();stage_admission('long_probe',scope,out)
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    import torch
    torch.cuda.init()
    from transformers import AutoProcessor,Qwen3VLForConditionalGeneration
    from peft import PeftModel
    from constrained_json import ascii_token_candidates,make_prefix_constraint
    from train_sft import unique_parameters
    from verify_saved_smoke import canonical_frozen_hash
    out=Path(out);out.mkdir(exist_ok=True);started=time.monotonic()
    base=Qwen3VLForConditionalGeneration.from_pretrained(a['model_dir'],local_files_only=True,torch_dtype=torch.bfloat16,
        device_map={'':'cuda:0'},low_cpu_mem_usage=True,attn_implementation='sdpa')
    model=PeftModel.from_pretrained(base,a['adapter'],is_trainable=False).eval()
    require(sum(p.numel() for _,p in unique_parameters(model))==8782459120,'long probe model parameter count changed')
    fingerprint=canonical_frozen_hash(model,torch)
    require(fingerprint==read(RUN/'temporal_sft8b_full_v1/train_01/train_report.json')['freeze_evidence']['adapter_off'],'long probe base identity changed')
    tc=load(CODE/'vendor/temporal_common.py','long_input_tc')
    p=AutoProcessor.from_pretrained(a['model_dir'],local_files_only=True,min_pixels=tc.MAX_PIXELS,max_pixels=tc.MAX_PIXELS)
    prompt=p.apply_chat_template([{'role':'user','content':[{'type':'text','text':tc.PROMPT}]}],tokenize=False,add_generation_prompt=True,enable_thinking=False)
    prompt=prompt.replace('<|im_start|>user\n','<|im_start|>user\n<|vision_start|><|video_pad|><|vision_end|>',1)
    frames=torch.zeros((64,3,1080,1920),dtype=torch.uint8)
    md=dict(fps=30,frames_indices=[14*i for i in range(64)],total_num_frames=900,video_backend='decord')
    encoded=p(text=[prompt],videos=[frames],video_metadata=[md],padding=True,truncation=False,do_sample_frames=False,return_tensors='pt').to('cuda')
    prefix=int(encoded['input_ids'].shape[1]);require(8192<prefix<=16384,'synthetic case does not exercise corrected inference bound')
    eos=model.generation_config.eos_token_id
    if isinstance(eos,int):eos=[eos]
    constraint=make_prefix_constraint(p.tokenizer,prefix,30,candidate_token_ids=ascii_token_candidates(p.tokenizer),eos_token_ids=eos)
    torch.cuda.reset_peak_memory_stats()
    with torch.inference_mode():g=model.generate(**encoded,do_sample=False,max_new_tokens=256,prefix_allowed_tokens_fn=constraint,return_dict_in_generate=True,output_scores=True)
    torch.cuda.synchronize();ids=g.sequences[0,prefix:];constraint.assert_complete(ids)
    require(all(bool(torch.isfinite(score[0,int(token)])) for score,token in zip(g.scores,ids)),'nonfinite selected generation scores')
    raw=p.tokenizer.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False);parsed,errors,warnings=tc.parse_segments(raw,30)
    require(parsed is not None and not errors,'synthetic actual inference contract failed')
    write(out/'probe.stage.json',dict(status='PASS_SYNTHETIC_LONG_INPUT_8B_INFERENCE',input_tokens=prefix,
        input_shape=[64,1080,1920,3],inference_limit=16384,training_limit_unchanged=8192,
        peak_memory_allocated_mib=torch.cuda.max_memory_allocated()/2**20,wall_seconds=time.monotonic()-started,
        logical_parameters=8782459120,base_hash=fingerprint,selected_scores_finite=True,
        synthetic_pixels_only=True,contest_media_read=False,quality_claim=False,uploaded=False))

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['temporal','spatial','long_probe']);ap.add_argument('scope',choices=['nontest','rematch']);ap.add_argument('output');args=ap.parse_args()
    globals()[args.stage](args.scope,args.output)

```


## 原文件全文：reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/b_score_aligned_package_v4/PROTOCOL.md
字节=2796；SHA256=1802b180a67928a5ed0e4f2e3d21a2f3bdfa04a8c5e2feadf0cc1cafad03fea7

```md
# B2 v4：显式原生解码修复与仅失败窗恢复

保留已经训练的B最终8B LoRA、v2统一canonical时长、原提示/64帧/16384/greedy/参数。v1/v2所有锁、raw、STOP及成功物保持。

真实provider视频97在送入processor/模型之前，PyAV17.1/libswscale9拒绝yuv420p/unknown primaries/unknown colorspace/log316 transfer，errno95。全434源头元数据仅这一个SHA为此profile，来源SHA8ec893eb5378452de6223f6c8e5878bcea044cb2f9e4feaabf708fa364871722。OpenCV亦打印同转换失败，read的返回不能当合法RGB。

这是独立登记的新像素转换配方：仅此SHA且精确格式/geometry/trc10/space2/prim2/range1匹配时，将用于转换的transfer标记临时设UNSPECIFIED(2)，明确限定范围ITU601 YUV样本映射，完成后恢复原frame元数据。原YUV样本/PTS/尺寸/range/源文件字节不变；不应用或宣称恢复摄影gamma曲线。不按图像内容选颜色参数，没有复赛视觉调参。其他所有来源保持原转换调用，额外未知错误STOP，绝不try/except自动换任意decoder。

source_color_cpu复现真实errno95、合成有限范围参考、真实64帧RGB/BGR通道完全相等/完整native ordinal与PTS/raw YUV不变；processor实际8非测试像素SHA仍通过。全529端点/529越界拒绝/原29错误及12目标无损合同保持。新source_color/recovery及CPU/processor/所有旧必要成功SHA绑定后单次启动。

v1剩余有效GPU生成继续，不重复成功物。v4在provider全426/521时间与wrapper终态完整记账后，仅准入原失败为登记source97的送模型前errno95，逐SHA/原validator核所有成功，保留旧failed raw/stage。原成功记录整行原字节复制，失败窗口在新目录用修复转换实际生成一次，B288张量/基座全SHA/原输入和原validator/CUDA有限分数都须PASS；不补标签、不将失败变空、不减少分母。新recovery stage明确原成功数/新调用数/两个真实wall成本，不修改旧STOP或借失败总stage给成功回执。

时间新完整PASS后，全源CPU镜头/同一source转换空间/恢复合成/独立strict ZIP；8非测试完整门仍先通过。最终唯一426ZIP留Linux，T0/新分未知，B2不是新教师T微调。每15分钟静默核真实provider/controller/回执，自主独立修复，最后真实大小/SHA/CRC/全部strict通过后报告一次并删除监控。共享锁/追加账本/7200offset/真实容量，Mac退出、不回传/官网提交、新大流量许可继续。

额外v4工程审计修复：完整原始新回答在有效性拒绝前先写独立raw回执，异常另写failure/traceback，避免丢失真实新失败回答。原v3仅停止等待controller，未启动恢复GPU，不重复任何新成功生成；旧冻结568文件仍保留。

```


## 原文件全文：reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/balanced_two_window_risk_v3/PROTOCOL.md
字节=2986；SHA256=dc2a645a592b5add8fcea0041737e349b6420b8427157b28ace9955490eb6b13

```md
# Balanced two-window user-authorized risk experiment v1

2026-10-09 最新用户明确要求“按照讨论出来的方案去训练打包zip，本来我们就是在试的”。据此独立执行讨论中的双窗均衡候选。保留此前讨论和全部科学STOP，当前用户接受风险的授权取代上一轮主控的G0止步决定。独立质量参考、提分和新官网分均UNKNOWN，不宣称旧科学门通过。

原B8B/288adapter、B0 prompt、0..5原grammar、greedy、原native clock/source97颜色白名单、floor64、input16384/output256、原video像素预算不变。此方案仅改变推理输入分区，新optimizer/32B/overview/空间调用0；原B已经训练过，不增加无依据的权重训练。

仅原来恰好两窗且总域严格30<duration<60秒：改为[a,(a+b)/2)、[(a+b)/2,b)。中点Fraction精确计算，不吸附PTS、不epsilon、不裁端点。其他原窗完全相同、按完整旧身份和SHA引用成功。每个新窗采样精确域内整数floor64，真实decoder/processor/token/prefix/raw/原validator和独立有理数成员核验。失败不转空、不合并模型结果、不强行补证据。

先完整NT8原请求精确引用/空间原完整源场/11strict，再真实非测试104中16个变化窗新生成与独立CPU回放；质量方向仅UNKNOWN，不按弱分改提示/门/样本。工程通过后执行完整426/521的新计划：所有变化请求真实生成、其他V14原成功exact引用。全426先完整原空间源场，再按本候选时间选择；原31295空间锚点/18723.876秒和旧V14全部GPU成本/7200offset保留。新GPU自然终态费用唯一追加。

仅独立final PASS、8/426全部11strict、ZIP实际size/SHA/CRC/唯一predictions.jsonl/426身份/原字节、全部新CPU回放和所有真实GPU账本通过才交付。新包可能低于旧最佳37.63，旧最佳不覆盖。包留Linux，不自动回传/官网提交。源/资产/代码先CPU验收再锁定/单次launcher。新工程错误保留trace/raw，在独立版本修复；不修改冻结代码或重跑成功。

工程v2仅排除运行日志与进度/CONTINUE等可变记录的冻结绑定；v1在模型前冻结阶段日志绑定故障保留。132已验输入与原CPU原字节、decoder/processor/grammar算法完全相同移交，模型调用仍0；不修改v1锁。

工程v3修复首实际回答整数范围list/tuple表示误拒绝，真实范围值完全相等，无端点或源ordinal改变。原v2有效raw原字节保留，单独native/processor/token/prefix/原parser CPU回放后exact移交一次；15开发新+1原有效恢复+96旧exact，116复赛新+405原exact。v2失败实际GPU144.4350819280371秒保留，原NT8完整11strict/ZIP原字节移交，不重复成功NT assemble/finish。新版本仅representation、失败trace导入Path及exact恢复计数/控制接口；原B模型/prompt/grammar/输入与科学分区完全不变，不修改v2冻结代码，不重复真实有效生成。

```


## 原文件全文：reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/teacher_student_autopilot_v14/PROTOCOL.md
字节=13456；SHA256=e2d9e76650deb3e2b6a7bce76af9b9e9d23225b8547d9e4eddbf3169799cf215

```md
# V14唯一接续：完成教师复查的精确阶段移交

V13完整160标签/160盲第二选择真实成功后，学生CPU准入因原pilot24的diagnostic_only=True停止。原pilot的诊断标记、原raw、标签、支持/UNKNOWN、全部SHA与STOP均保留。新版本仅允许登记完整160 manifest中原pilot24精确成功回执跨阶段作为同教师弱证据，既不把未知转负，也不宣称人工真值或质量提升。外部/修改/新增diagnostic回答继续拒绝。

先Linux CPU复现旧consumer拒绝，并验证新consumer完整160、65train/14dev弱支持及81UNKNOWN/原HTTP/模型/输入/物理帧/原validator。注册完整160精确manifest与独立冻结锁后只启动一次，无新的教师调用。后台完整CPU移交→学生准入→2–4真实更新同optimizer/RNG及288adapter重载→旧B candidate0开发→NONTEST8→426/11独立strict ZIP。未实际更新不能称新T，未全包验收不能交付；历史目录/冻结源码不改、成功模型调用不重复。新大流量先许可，Mac退出，小量SSH控制授权，共享锁/账本7200及外部任务保持。


原科学协议（保持配方、支持判定和UNKNOWN约束）：

V13额外修复：V12在任何GPU/新标注/新复查前因部署漏掉原validator的supervision/teacher_metadata_20261007.json而自然STOP。V12原14562冻结文件/失败日志保持，不重开。这里只部署V11原metadata与schema完全相同字节，并CPU执行当前28条完整verify_blind_review_projection，原13拒绝/160投影/2排序回归保持；其余V12配方原样。

# V13 独立工程修复与完整复查接续

V11 source_lock SHA0ae09ec38ff589baa5e15e16b84457b06442195de502ec7ef6a19bab9b715578。已真实完整标注160（新134/合法复用26），原第二选择28完成，原full GPU charge6748.806357712485秒、exit1/failed/stop_reason null和STOP保持。仅修旧许可V10记录从JSONL读出后对象排序与原canonical字串序列顺序错配。两条旧成功仍按exact manifest和原隔离validator核；返回原始已批准文件parsed对象的顺序，不对回答裁数、重排段或补证据。

V13 v11_resume_manifest在Linux原地逐SHA核160标签/28复查/物理PNG和RGB/原输入/raw/冻结原validator。所有原目录保持；新目录仅复制9MB左右aggregate和validator文件原字节，引用原视频/图像/模型。原学生/生产/科学比较函数原字节保持。新/旧第二选择source-lock绑定只在160原记录exact manifest内允许：新回答绑定V13真实锁；旧回答必须恰为28条已接受原对象/文件SHA，原V11锁。未知旧回答和其他锁拒绝，不放宽通用验证。

新GPU只生成余132独立盲选择；首个原阻塞窗实际新第二选择必须原validator/输入/SHA通过，失败raw不可覆盖保存。已完成标注/复查不能重复。资源预测按28条实际HTTP wall与真实产物大小外推，旧四阶段实际GPU成本分别引用，追加账本7200offset保持。不把引用当零旧成本或新调用。

原弱质量/训练准入不改。未知、分歧保留全160分母，UNKNOWN不当负类；同教师一致性不是人工真值。先完成复查，再按原门选择支持子集/可靠边界/不可用教师三条科学路线。旧B candidate0、原B LoRA lr1e-5/r16/alpha32/dropout.05/有效batch16/最多3epochs、至少2且最多4真实更新前缀/同optimizer与RNG/冻结基座及288张量重载保持。未更新不能称新T。

下列是继承的V11科学协议与历史工程记录；V13跳过已真实完成的视觉/重输入/24小试/160标注调用，只复用经原证据确认的成功；来源与窗口从V11原字节复制，不重新抽样。最终门和B/C自主裁决继续有效。

# 当前唯一接续：teacher_student_autopilot_v11

V10视觉接口8/8与2条真实重输入探针成功，但首个24窗pilot标注的两个区间缺少模型所选物理证据，原validator正确STOP；不是32B权重装载失败或新T训练失败（T仍0更新）。原639冻结文件、失败raw/STOP、两个成功记录全部保留。

V11仅修新输出接口：B前缀边界与F前缀物理帧分离，KEEP每段附模型自行选定的非空证据，固定GBNF只允许该段半开区间内的帧，保留所有合法1..5段与证据子集。程序只做精确PTS/元数据投影，不补造见证、合并/排序/裁段或将失败转空。旧高光定义prompt、原validator、固定160/24输入逐字节不变，不换seed/挑样本。

旧V10已成功2条只按 accepted_resume_manifest 和孤立原validator/全部文件SHA核后原样引用，属于full160且不在pilot24。旧visual8仅在同实际模型/运行时/输入管线与8案HTTP构造body CPU相等后引用；只算旧真实调用和旧GPU成本，新调用0。新格式必须在原失败pilot首窗真实生成通过后继续余23窗，不重复成功探针。

一次controller：真实身份/SHA和B2空间缓存核验→原视觉及重输入容量证据CPU移交→同24实际标注与盲第二选择→逐条分层支持/UNKNOWN与全分母→完整窗口监督合格时完整160标注/复查→B最终LoRA lr1e-5最多3epochs/2–4更新前缀保持optimizer→开发候选0→NONTEST8→426独立strict ZIP。仅边界监督可靠走独立B精修；教师不可靠走独立C同8B全源粗览/局部非测试对照；监控自主实现验收与登记，不盲重试语义。

冻结后不得改source_lock中的文件或重复launcher。读registration/progress/completion、legacy_handoff、pilot/new_format_real_probe、逐窗done/failure/semantic_review、student进度/prefix/完成、NONTEST/rematch全部strict、resource/queue；核真实完整命令/父子PGID/CPU/GPU/RAM/磁盘与共享锁。CPU SHA与顺序解码/合法队列不当卡死。

controller/checkpoint_teacher_v11.py每15分钟静默巡视，故障立即自助复现/独立版本修复。新大流量事先许可；小量控制直SSH、Mac退出、100confirm不读，不看复赛调参。只在真实完整最终ZIP验收后报告；旧B37.63、已交付B2用户37.32（低0.31）分别绑定旧包，新T及新官网分未知。

---

## Historical V10 engineering and retained V8 science protocol

# V10真实重叠边界生成约束修复

v9真实32B视觉接口8/8通过，但第一条非测试探针返回嵌套重叠，被原validator正确拒绝；原HTTP/raw/STOP保持。其真实13675输入token、200输出token无截断，不是下载或装载失败。旧schema仅独立ID enum，生成语言遗漏start<end及跨片段顺序/非重叠关系。

新v10以有限状态GBNF在生成时约束合法原生边界序列：1到5段全部合法选择仍可表达，段内start<end、每段含真实提供帧，下一start>=上一end。schema、提示词、高光标准、原validator和160/24选择原字节保持；直接grammar为单独登记的生成配方修复，不后处理旧重叠输出，不裁段/合并/排序/造空。原事前登记160/24保持，其中已有一条工程失败探针被观察过，不冒充全新未见24；不重新挑样本。两条真实重输入探针在新目录真实生成，旧无效响应不复用为标签。视觉inference入口新增grammar分支，重新测试8个合成接口case有工程必要性，不当作新标签或新科学通过。

先固定运行时CPU：原raw必须拒绝；合法1..5段/贴边/全端点/NO/UNKNOWN及非法重叠倒序/反向/无帧/多于5段验收，然后独立锁/单次launcher。真实24/盲审核/分层UNKNOWN/2..4更新前缀/候选0/开发及NONTEST8/426strict保持下述协议。科学门失败仍按B/C自主准备匹配对照，不无限换提示。

# V9工程修复接续

v8已在B2缓存回执字段status/stage处STOP，GPU调用0/标签0/T更新0，480冻结文件与STOP保持。v9修实际B2回执适配与缓存验收绑定并做真实CPU缓存交接验收；沿用同配方/同输入的原160/24选择原字节，不重复选择或模型生成。当前目录与source_lock/registration为准；下面v8科学协议全部保持。

# V8 独立教师修复与时间监督实验

用户2026-10-08要求按照提供审计修复并接续。旧v1..v7/context全部源码、原答、标签与STOP原样保留；此版本重新登记任务、表示与准入，不宣称旧门通过。

## 修复与成功标准

probe实际新生成且拒绝任何旧done；all/labels对同v8成功逐文件SHA、source/model/prompt/input/原validator核验后复用，只补缺失；review仅审核已有标签。CPU串联实际production函数要验证次数、残缺/失败缓存拒绝与原字节不变。

教师与学生观察相同局部自然30秒/floor64/nativePTS，不给教师额外全源摘要。模型仅输出KEEP/NO_HIGHLIGHT/UNKNOWN、整数边界ID、独立证据帧ID及简短依据；程序拥有nativePTS/原source序号/窗口尾边界。窗口尾无证据帧；禁止float拷写、裁值、补造帧、UNKNOWN当负。原模型回答与canonical程序转换记录分别保存并绑定，原validator验派生格式不冒充原短答。

## 一次有限实验

使用现存固定32B Q4_K_M+F16 projector与原CUDA运行时，不下载/升级。八个合成观察接口case（含64帧正反序）测红方块开始/中/尾、换图/反序/单帧替换；只验视觉输入，不作高光标签。完整真实NONTEST教师重输入probe先执行，随后未经旧提示词修订使用的新24（16train8dev），来源组全部排除旧160。每条独立盲判断先产生再由程序比较，保留所有原答/分歧/UNKNOWN和全分母。相同模型一致性只作弱证据，非人工真值。

整窗空例不设配额，也不作为小试继续收集的硬门。逐条工程有效性与科学可用性分开。实际无法证明完整观察/语义一致者不进入完整窗口监督，争议不转空；原正例补集不当负真值。逐条可用/拒绝/UNKNOWN、各split和来源分布全部报告，不声称过滤后代表全部数据质量。仅明确新工程原因才另立第二次匹配实验；不反复换提示词直到有NO。

小试另登记选择坍塌诊断：按每条原始完整决定累计保留时长占窗口时长，比例≥0.99的条目达到22/24，或任一split全部原始条目均恰好选择[0,duration)，判为明显整窗选择坍塌，不进入A的全量监督收集。记录24条全分母、所有比例和命中ID；该规则不要求正/空类别比例、不把争议改成空。仅程序交付全部计划帧与盲ID选择一致不能证明模型完整理解或事实真值，原记录和弱一致性限制均保留。存在可证实事件边界再独立取B证据；全窗坍塌不能自身充当B边界可靠证明。

## 路由与接续

优先A：24提供可用完整窗口弱证据且无明显整窗坍塌时，继续登记128train32dev；每条盲审核和身份核验，只有可靠完整窗口进入学生目标。无真实NO时记录拒绝行为未得到监督，不能称已解决全空识别。训练从原37.63对应B最终LoRA续训，语言q/k/v/o r16 alpha32 dropout.05，基座/视觉冻结，lr1e-5有效batch16最多3epochs。前缀2..4实际更新（min4与实际总步，至少2）验finite loss/grad、全基座冻结、288adapter保存和独立CPU重载；同optimizer/RNG/scheduler继续，不增加曝光凑20。开发candidate0保留原B，同production输入/解码比较，弱教师指标不当官网分。退化轮拒绝/科学早停，选择合格旧B或先前轮；不能自动称新T胜出。

B：完整窗口语义不成立但非测试明确事件边界可靠时，独立登记候选+B边界精修小adapter；候选外UNKNOWN不监督为负，旧B候选adapter保持。先取真实边界对照证据，不能用A剩余正样本偷偷当B完成。

C：连简单观察/边界也不可靠时停止此教师标注，不无限重跑。独立登记同8B全源粗事件表→局部定位的非测试匹配对照；无改进或全局幻觉广泛退化保留B/B2。B/C由当前真实24回执触发，监控Agent继续准备执行，不等待用户。

只改本轮时间监督，空间保持同8B基座原生模式；不加RL/稠密头/空间LoRA。保留已验B2的唯一97SHA/profile显式样本转换与canonical duration修复，其他源默认路径，未知错误STOP。全源空间仅在全部算法/模型/源/采样/请求/回执SHA同一后原样复用B2完整空间，不复用B2时间预测；复用与新GPU成本分开计。

## 资源和交付

既有SSH aic-inspur-home/Linux独立后台，Mac不参与。真实容量、共享GPU锁和追加账本7200历史偏移保持，无人为disk/RAM/VRAM额度。不抢占外部任务、不改系统/连接，不读100confirm或手看复赛调参。控制代码小量部署授权；任何新大传输先说明规模方向链路/可能机场消耗等用户许可。

真实训练/开发→NONTEST8完整独立strict→426/521时间与全源空间→独立strict ZIP才完成。实际ZIP大小/SHA/CRC/唯一JSONL/426身份全部核验；只有PASS_AUTOPILOT_FINAL_T_ZIP_ON_LINUX可报告训练路线的真实包，candidate0必须明确旧B被选、实际T更新及未胜出。不自动官网上传/回传。旧B37.63对应旧SHA86bd5301f6f6771a8451b32063781e214cdd70245ae5513f2a767eaecb9ebe54；B2已由用户截图指认37.32/DONE，对应0f8c95f01222a28a053e6f80b76b3d4d7ac3dc82077f4dd533605337bc6883a3。新候选官网分未知。

```


## 原文件全文：reports/round6_score_alignment/rematch_discussion/aic_video_post_sg8_20261009/pro-p01.md
字节=21278；SHA256=c102f3970b3451b6b93f59f4aec15d889c3de6f5a437b51bfd8bf282002d14b6

```md
# POST-SG8 技术裁决：执行一次有界G0与双窗精确计划，本轮明确NO426

**连续任务：AIC-VIDEO-REMATCH-NEXT-20261005。此次为slot5/8，本次后剩3次；不重置旧额度。**

## 读取范围与证据边界

本次读取的是**本条新上传**的索引及六卷，前五个文件使用带`(1)`的附件路径，没有误用旧四卷版本。

| 新附件 | 实际本卷读取范围 | 对应完整正文行号 | 原始字节数 |
|---|---:|---:|---:|
| `context-p01-index(1).md` | 1–69 | 索引全文 | 2,361 |
| `context-p01-part01(1).md` | 1–2066 | 1–2066 | 139,971 |
| `context-p01-part02(1).md` | 1–1924 | 2067–3990 | 139,765 |
| `context-p01-part03(1).md` | 1–1883 | 3991–5873 | 139,980 |
| `context-p01-part04(1).md` | 1–2556 | 5874–8429 | 139,996 |
| `context-p01-part05.md` | 1–2174 | 8430–10603 | 139,933 |
| `context-p01-part06.md` | 1–680 | 10604–11283 | 51,841 |

初始展示及一处长段输出曾截断，均已分段补齐；最终读至`END_REPLAN_P01`。**对本对话附件副本**按原始字节拼接核对，得到751,486字节、11,283行，SHA256与索引一致：

```text
ae94182cc4b029ae49b195776b53aa24484d59e1dad9b2e361d019003534af44
```

**这不是对Linux原件、实际媒体、模型权重或执行流水线的主机独立复验。**下文采用卷宗中的执行证据；本次没有运行模型、解码媒体、发起远端写操作或重新执行SG8验收。新旧分卷范围以本次索引为准。context-p01-index

---

## 一、唯一决策

**主控接下来只执行一个工作包：**

> **`post_sg8_reference_g0_slot5_v1`：有界的已有参考资格核验＋开放开发集双窗精确CPU计划。总计最多60分钟有效执行工作，完成后封存结果并以NO426结束本轮。**

本工作包**不启动均衡二分的16窗模型实验，不训练，不生成新426包，不自动转任何后备路线**。即使找到有潜力的参考，也只封存其适用范围和资格证据，不让“发现一个标签文件”自动触发训练或生产。

这里的60分钟是**本次投入上限，不是完成时间承诺，也不是每个入口各60分钟**。如果没有未审计且可合法读取的新入口，参考支项提前结束；仍完成已委派的双窗计划或明确记录其阻塞，到限即收口。

### 为什么这次不购买均衡二分风险包

我仍认可：**先划分输入窗口、再完整映射模型原段，与生成后裁段是不同算法。均衡二分没有被SG8证伪，也不因缺少人工真值就天然禁止研究。**

但“允许研究”不等于“当前值得投入426”。本轮可用的正向理由仍是短尾上下文不对称；可观测的新增结果仍主要是输入、采样和模型行为变化。与此同时，它会失去部分旧采样、缩短原主窗上下文，并新增中点边界。**现在没有成立的判据，能够判断这些交换更接近任务目标，而不只是更接近我们偏好的输出形态。**

上次SG8至少有一个事前明确、可以作方向比较的有限命题：是否更接近隔离的同模型逐帧输出。那个命题虽然不是真实构图质量，仍可被实验否证；它现在确实没有通过原门。均衡分区目前提出的“集合变化”“跨缝长段”“极端状态不超过若干个”，没有提供同等清楚的误差方向依据。**不能因为前一项可否证实验失败，就给下一项换成更容易通过的行为条件。**

这不是宣布“以后无真值一律不准产包”。这是本节点的投入选择：**先补齐尚未完成、且范围可以严格限定的证据资格与输入计划；本轮不购买未知方向的整包比较。**

---

## 二、先锁住SG8结论，防止把科学STOP重新包装成工程问题

| 已有证据 | 本次采纳的准确含义 |
|---|---|
| 8个登记来源组、56个隔离相位 | 统计单位是来源组，不是56个独立样本 |
| 53次真实新空间推理＋3条旧成功精确引用 | 不是56次新推理；32个原支持点未重跑 |
| 确认组3/6为正 | 未达到原定至少4/6 |
| 确认均值−0.0026950568804326776；全8组均值−0.002307551408911853 | 原方向门未通过 |
| 确认留一条件失败 | **不能扩写为“全部六个留一均值都为负”** |
| 独立原raw、parser、有理数面积、多项式及费用闭环通过 | 支持按原合同结束，不支持改公式或降门补考 |
| G2退出 | 没有真实G3新完整空间场，也没有新426包 |

以上由SG8终态及独立验收摘要支持。context-p01-part05 context-p01-part05

**SG8没有证明“高阶插值一定放大锚点噪声”，也没有测出人工构图质量下降。**它只证明这份固定方案没有取得其预先要求的支持。无需为了接受STOP，再补一个未经验证的因果故事。

费用也保持原归属：v1生成前失败的103.09017407242209秒、v2的495.22363770753145秒分别保留；原空间约18,723.876秒及7200秒历史偏移不抹除。独立closure记载的165行账本是当时终态，不是未来写入位置。context-p01-part05

V14同样不能重写历史：**15次优化器更新真实发生，但按开发选点规则选回原B；不是“没训过”，也不是“全部未来微调无效”。**原65条CE、原160教师流程、C/B1/D/Q和42次边界诊断，本轮均不重开。context-p01-part01 context-p01-part01

---

## 三、为什么新GNMC协议没有打开训练或426出口

新读到的`reference_protocol.md`第7条明确限定：

> GNMC试点仅授权本地非商业诊断；不得据此批准训练、比赛测试、打包或提交。

该文件同时要求原生目标比例、源身份、来源隔离，并规定稀疏视频只评已标帧。context-p01-part06

因此必须分开三件事：

**第一，项目登记用途。**这份协议可以证明项目曾登记过受限诊断用途，不能当作本次训练或比赛生产的准入依据。

**第二，具体资产使用权。**它是项目参考协议，不能仅凭其存在，就补齐每个源视频及派生标注的权利证据。旧四源审计中未找到的每视频许可，不因出现这份内部协议而自动变成PASS。

**第三，参考的科学用途。**原生16:9单编辑构图参考，即使资格成立，也不自动成为9:16构图真值，更不能评价均衡二分的时间高光选择。稀疏已标帧之外仍不是负例。

**“可本地诊断”“可作为某种有限参考”“可用于训练或比赛决策”必须分别登记，不能合并成一个`eligible=true`。**

这也纠正了两个相反的过度推断：

- 原inventory为0，只说明**没有已登记的独立构图authority**，不能推论全盘不存在其他参考。
- 其他资产尚未扫描，也不能推论那里一定有可用新监督。

只读核验已明确记录`UNKNOWN_NOT_SCANNED`；p1b默认未标注、987条豆包来源和未获许可的LIVE_YT_VC也不能重新算作现成独立标签。context-p01-part06

---

## 四、可直接派发的工作单

### 工作边界

执行主机仍为Linux，使用既有授权和既有连接；**本回答是工作单，不是已启动回执**。

只允许读取规定范围内的现存协议、清单、标注schema、来源登记、曝光记录和已保存的native时钟表。允许在独立新目录写入本次CPU工具、清单及报告。**不读取媒体像素、不调用decoder或processor、不加载8B/32B、不下载、不联系作者、不打开100confirm、不读取复赛预测来选配方。**

本次程序不应提供`train`、`infer`、`rematch`或`package`执行子命令，避免出现“G0通过后旧控制器自动接续”的隐含路径。

### 工作A：固定入口的参考资格核验

先由以下**已点名入口的明确本地引用**构造清单，不全盘搜索，不递归追逐外链：

| 入口 | 本次只补什么 | 已有结论如何处理 |
|---|---|---|
| `context_advisory_v1/fallback.py`及其绑定的NONTEST/developer计划、authority登记 | 是否明确指向尚未审计的本地参考资产 | 已登记authority为0直接引用，不重复跑旧inventory |
| p1b的`pilot_manifest`及其标注状态登记 | 是否有此前未核的、实际完成标注的现存文件 | 默认`UNANNOTATED`不当成标签 |
| `existing_16x9_reference_audit`及其明确引用的本地许可、映射文件 | 只补此前UNKNOWN且确有新文件支持的字段 | 原四源有效语义0、人工复核0等旧结果保留 |
| `round3 label_origin_audit`及来源登记 | 是否存在明确不同来源、未审计的新条目 | 987条`api_doubao`保持弱参考身份 |
| p2r9候选矩阵 | 是否指向已经本地存在、已有读取许可且未审计的资产 | `PERMISSION_REQUIRED`、未下载、仅外链条目直接记阻塞 |
| 新GNMC参考协议 | 精确记录用途限制及其覆盖的资产范围 | 不升级为训练、比赛测试、打包或提交许可 |

这些入口和“只补未知、不重复已知失败”的范围有卷宗依据。实际路径必须从现有登记解析，不能靠文件名猜绝对路径。context-p01-part06

**清单第一次冻结后，不因发现参考质量差而继续扩目录。**只有明确指向、当前许可允许读取、且确实尚未完成相同资格检查的条目，才进入本次增量审计。

每条资产至少逐项记录：

| 字段组 | 必须回答的问题 |
|---|---|
| 存在与身份 | 文件是否实际存在；版本、文件SHA及所引用旧回执是什么 |
| 生成来源 | 人工、模型、混合还是未知；是否完成标注；采用什么协议 |
| 任务适配 | 时间选择还是空间构图；有无query；原生目标比例是什么 |
| 映射与覆盖 | 源文件、来源组、坐标或时间基准是否可追溯；哪些范围有判断，未选含义是什么 |
| 使用范围 | 元数据读取、本地诊断、训练、比赛用途及对外共享各自有何依据 |
| 本任务曝光 | 是否参与过训练、选点、选方案或既往查看；是否由当前候选输出派生 |
| 当前结论 | 每项`PASS / FAIL / UNKNOWN`及证据位置，不只给一个总通过标志 |

其中，`PASS`只能表示对应资格字段得到证据支持，**不表示已经独立看过画面、验证语义正确**。来源隔离也不等于模型预训练绝未见过该视频。

缺少隔离依据时，不能通过打开100confirm来“补证”；只引用此前可用的保护登记，无法核清就记UNKNOWN。模型预测缓存不转为人工参考，只有正例的时间标签不把补集补成负例。

### 工作B：全部适用双窗记录的纯CPU精确计划

这部分使用开放开发manifest、原窗口计划及**已经存在的native PTS表**，不读取新旧预测答案或弱标签来挑记录。

必须先实核：

**104条记录中实际哪些旧计划恰有两窗、对应多少真实来源组、许可范围是什么。**现有证据支持8条双窗记录和8个相邻接缝，但尚不能把它写成8个独立来源组。NT8没有接缝，不移植其来源组验收作为这8条开发记录的证明。context-p01-part06

本次只规划以下规则，不扩大成任意多窗均分：

\[
W_{\rm new}=
\begin{cases}
\{[a,m),[m,b)\},&\text{旧计划恰两窗且 }30<b-a<60,\\
W_{\rm old},&\text{其他正常情况},
\end{cases}
\qquad m=\frac{a+b}{2}.
\]

时长恰60秒时，须核新旧边界及计划确实一致，才记录恒等。旧计划异常、有缺口或身份冲突则标阻塞，不能归入正常恒等分支。

**精确实现要求：**

1. 从原登记数值的规范表示构造有理数，不用报告里四舍五入的“约30.3秒”重建边界；不假设源起点为0。
2. 中点**不必落在某个物理帧PTS上**。禁止为此吸附到帧或加入epsilon。
3. 对已有PTS表 \(P_j\)，分别建立
   \[
   I(a,m)=\{j:a\le P_j<m\},\quad
   I(m,b)=\{j:m\le P_j<b\}.
   \]
   两者必须不相交，并完整覆盖原许可域中的物理帧。
4. 对一窗中连续的 \(N\) 个物理ordinal，\(N\le64\)时全部取用；否则按原floor64合同取
   \[
   j_k=j_{\rm first}+\left\lfloor\frac{k(N-1)}{63}\right\rfloor,\quad k=0,\ldots,63.
   \]
   不换为nearest64，不补插值帧。
5. 检查中点、局部时长及源时间转换能否由现有消费者保持同一语义。发现序列化或浮点接口改变半开归属时，记录具体反例并阻塞；**不为了让计划通过，静默舍入或修改旧端点。**

每条适用记录输出旧新窗口、实际来源组、旧尾长度、物理帧数、floor64计划索引，以及**新增与丢失的采样ordinal**。同时分别报告旧主窗区域和旧短尾区域中的采样间隔变化，而不是只报整体平均密度。

原30秒接缝两侧是否有计划样本、新中点两侧间隔多大，可以由现存时钟计算；**“这些样本是否含有更有效的语义信息”仍是UNKNOWN。**

原理上，生成前均分并完整投影模型段不属于输出裁段；但此工作单尚未运行模型。可以用合成区间测试消费者不裁、不延长、不混用旧新答案，不能据此声称真实模型原段已验收。

### 工作C：独立检查并关闭工作包

建议只实现四个职责明确的小模块：

| 模块 | 职责 |
|---|---|
| `qualify_references.py` | 固定入口、用途资格及曝光证据 |
| `plan_two_windows.py` | 纯元数据精确分区、native PTS归属和采样增删 |
| `verify_g0.py` | 独立重算计划与资格结论，检查禁止项和报告一致性 |
| `run_g0.py` | 一次运行、总时限、阶段结果与终态；无GPU或426分支 |

**不要导入会触发模型加载、解码或旧自动接续的通用controller。**纯计划器只接收已解析的元数据。

新CPU测试至少覆盖：非零源起点、单窗、恰60秒恒等、三窗以上保持、二分点恰有或没有物理帧、半开边界唯一归属、空物理窗口拒绝、非法数值、不同文件同来源组、禁止路径访问，以及**GNMC本地诊断资格不能使训练/比赛准入变成True**。

这些测试是本单要实施的要求，**不是本次已完成的验收结果**。旧SG8的53次CPU回放、原strict、旧完整空间场以及18104项冻结文件，不重新跑一遍来填工作量。

---

## 五、前瞻成功门与停止门

本轮不设置任何“涨分门”。设置的是**工作完整性、资格和计划门**：

| 结果 | 精确含义 | 后续动作 |
|---|---|---|
| `NO_NEW_AUDITABLE_ENTRY` | 固定入口没有指向新的可审本地资产 | 结束参考支项，完成双窗计划后NO426 |
| `NO_REFERENCE_ESTABLISHED` | 有资产，但用途、来源、监督含义、映射或曝光史仍缺证 | 列明缺项，不用UNKNOWN填充通过；NO426 |
| `REFERENCE_QUALIFIED_FOR_DECLARED_PURPOSE` | 某资产的特定用途资格成立 | 封存其适用域与证据；**本轮仍不评分、训练或426** |
| `PASS_TWO_WINDOW_PLAN_ONLY` | 既有元数据足以证明精确分区及采样计划成立 | 保存计划，不能改写为真实输入或模型验收 |
| `STOP_PLAN_CONTRACT` | 时钟、来源、许可域或消费者映射存在具体阻塞 | 保存最小反例，不修改端点救过门 |
| `STOP_G0_SCOPE_OR_BUDGET` | 越出白名单、触及禁止数据或达到总时限 | 保存已完成范围及未完成项，停止扩展 |

**本工作单所有正常和阻塞出口，最终都汇总为`NO426`。**不存在“未找到参考→风险推理”“资格PASS→自动加载模型”这两条控制流。

如果发现任务匹配、来源可追溯、用途适当的新参考，下一次可行动的信息应是**具体哪份资产、支持哪个目标、允许什么用途、还缺哪个证据**，而不是再写一句“建议找高质量标签”。是否据此开展新的有限实验，必须针对那份真实新信息重新冻结；不必为了知会消耗一次Pro，也不能把本次NO426回写成GO。

### 真实GPU和训练条件

**本单没有准入真实GPU的分支，新增优化器更新固定为0。**原因是目前没有成立的新训练目标与监督依据，而不是“模型再也不能提高”。

纯CPU计划也不能提供以下验收：

- 实际解码RGB或像素SHA一致；
- 实际processor grid、token长度、显存峰值；
- 新模型原raw及完整区间投影；
- 新NONTEST8或426的11项strict；
- 新官方成绩。

这些字段应记`NOT_RUN`或`UNKNOWN`，不填PASS，更不把0次调用写成“零失败实验成功”。

---

## 六、我为什么否决当前行为门，而不是再替它挑一个数字

### 最强反例仍然穿过原跨缝GO

考虑一个**构造例，不是本题实测标签**：

许可范围为\([0,30.3)\)，均分点为15.15秒。新右窗输出完整合法原段\([15.2,30.2)\)。它不是整窗，跨过旧30秒接缝，两侧有真实帧，也可以改变最终选择集合。

然而，这个长段可能大部分无关；新中点附近原来完整的事件可能被拆散，旧0.3秒尾窗曾密集看到的短瞬态也可能因新采样变稀而遗漏。**非整窗、跨旧缝、集合变化可以全部成立，选择质量仍然更差。**卷内Tibo已给出这一反例。context-p01-part06

Gemini后加的“至少3个新99%全选或全空才阻断”也没有补上这个缺口：刚才的误报可以低于99%，遗漏也不必表现为整窗变空。它是一个拟议的行为限制，不是已有数据支持的质量判据。

全104均值还会被96条恒等记录稀释。卷内构造例中，8条受影响记录假设分属8组，5条弱F1各降0.8，其他记录不变，全104均值仅下降约0.03846；下降组占受影响组62.5%。这足以说明原0.05／75%粗门可能放过严重的局部损失，**不是证明这些弱F1就是真实质量**。context-p01-part06

我的处理不是再换一个全选比例、组数或分母来“修好放行门”，而是**本次不让这些行为指标承担质量准入职责**。新增99%／3窗条件及“几十次调用”的成本表述，卷末主控也已明确指出缺乏依据或与190窗上界不一致。context-p01-part06

### 对本裁决最强的反对意见

**可能所有已许可资产都没有新参考，G0最终没有新包；均衡二分即使没有方向证据，仍可能实际提高官方分。**

我接受这个机会成本，不声称NO426在未知真实分数上必然最优。选择G0的理由是：它用一个短、可提前结束的工作包，补齐目前确实未完成的资格字段和真实采样交换；而不是继续购买一批无法用当前条件判断方向的新答案。

因此本轮结束后，不应自动开始“第二次寻找参考”，也不应因GPU空闲而启动均衡二分。**没有新证据就是这份工作单的终点，不是无限等待人工的起点。**

---

## 七、最终产物与费用验收

工作包应留下以下可审查产物，实际路径在新目录建立时登记：

| 产物 | 内容 |
|---|---|
| `input_scope.json` | 本次白名单、真实路径、版本／SHA、允许用途和引用来源 |
| `reference_qualification.jsonl` | 全部审计条目、逐字段结论、排除或未知原因 |
| `source_exposure.json` | 来源派生、组关系及本任务训练／选法曝光证据 |
| `two_window_plan.json` | 全部适用记录的精确边界、PTS归属、floor64及采样增删 |
| `cpu_acceptance.json` | 本次新CPU合同、独立计划重算结果及失败反例 |
| `closure.json`、简短结论 | 实际读取范围、未完成项、费用、禁止项计数及最终NO426 |

**不生成`predictions.jsonl`或候选ZIP，不重复封装旧包伪装成新候选。**

费用记录为本次实际CPU时间、文件读取量、峰值占用和产物大小；新增模型、decoder、processor及优化器调用均应为0。没有GPU作业，就不伪造一次`completed`的GPU回执。其他合法作业若追加了共享账本，应核实是正常追加，不要求整份共享账本始终不变；**旧记录、7200偏移和历史空间成本必须保留。**

旧B37.63仍保护原ZIP：

```text
86bd5301f6f6771a8451b32063781e214cdd70245ae5513f2a767eaecb9ebe54
```

本轮不比较旧B与V14逐例测试预测来决定方向。Grok已撤回该提议；只读或聚合并不会把“据测试输出选择／取消配方”变成单纯完整性检查。context-p01-part06

对席位来源另作一处明确说明：卷内`sol-r01.md`正文仍保留均衡风险与跨缝门的旧表述，**Sol最终撤回由本次用户说明及卷末`host-pre-pro.md`登记提供**；不能声称所附Sol正文已经逐字同步撤回。我的裁决不以三比一或所谓全文共识为依据。context-p01-part06 context-p01-part06

## 最终执行结论

**现在安排：一次有界的增量参考资格G0＋全部适用双窗记录的精确CPU计划。只补未知，不重验旧成功；不启动新GPU，不训练，不产新426。**

**GNMC保持本地诊断用途，SG8保持原NO426，均衡二分保持“工程上可讨论、质量方向未成立”的状态。**完成工作单后，交付具体资产资格、计划收益与损失、阻塞证据及NO426终态；没有新证据就结束本轮，不靠剩余额度、换阈值或另起同类实验延长流水线。
```


## 原文件全文：reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/next_round_v1/official_rematch_snapshot.txt
字节=4125；SHA256=c5e218ca636c4a8c102e51b8a8d223dd12b612c35e2755e9da2fa07b29db3e04

```txt
Title: 全球校园人工智能算法精英大赛 智青春·算未来

URL Source: https://www.aicomp.cn/notice/notice-3/5307.html

Markdown Content:
关于举办产业命题赛道“基于视频大模型的通用视频高光剪辑”复赛的通知

各参赛团队：

2026年第八届全球校园人工智能算法精英大赛产业命题赛道“基于视频大模型的通用视频高光剪辑”赛题报名将于9月30日11:00截止，初赛赛题结果文档提交截止时间为9月30日11:30。结合赛事整体组织安排，经大赛组委会研究决定，现将复赛有关事项通知如下：

###### 一、赛程安排

1.复赛数据集开放时间：9月30日18:00；

2.复赛赛题结果文档提交开始时间：10月1日09:00；

3.复赛赛题结果文档提交截止时间：10月23日20:00；

4.复赛作品文档提交截止时间：10月25日23:59。

###### 二、评审原则

1.初赛晋级。参赛团队须于9月30日11:30前提交初赛赛题结果文档，且在初赛排行榜上成绩得分＞0分的团队，方可进入复赛。

2.复赛数据集下载。复赛数据集开放后，各参赛团队登录大赛平台，查看“我的参赛信息—详情”，即可下载复赛数据集。

3.复赛成绩。复赛阶段，参赛团队每日可提交5次赛题结果文档，最终以复赛阶段排行榜最高得分为最终成绩（因排行榜存在算分延迟，最终成绩以组委会公示结果为准）。

4.复赛评测。复赛阶段实际推理所使用的主模型及辅助模型总参数量不得超过 9B。参赛团队须在技术报告中如实填写模型总参数量。参数统计口径及违规处理方式详见《基于视频大模型的通用视频高光剪辑算法赛题规则》（附件 1）。

5.复赛作品提交。参赛团队需在规定时间内提交参赛作品文档。作品提交截止日期后，不再接受任何形式的修改和补充。评审团队对复赛参赛作品文档进行结果复现与审核，如有疑问，将要求参赛者进行解释说明。

6.复赛评奖规则。以复赛排行榜得分为依据评选复赛一、二、三等奖，获奖作品数量分别按照不超过15%、25%、30%的比例取整计算。复赛一、二等奖获奖作品将推荐参加半决赛。

###### 三、作品提交注意事项

参赛队伍需将复赛提交内容（预测结果JSONL文件、算法代码、模型文件与运行环境、技术报告）提交至大赛平台。提交前，需按指定入口和文档命名规则仔细检查作品文档，确保内容准确且无格式错误。作品提交要求详见《基于视频大模型的通用视频高光剪辑复赛作品提交要求》（附件2）。

###### 四、联系方式

赛题QQ群：389921008

国赛组委会联系电话：025-85778806

国赛组委会仲裁邮箱：office@aicomp.cn

大赛官网：[www.aicomp.cn](https://www.aicomp.cn/)

**附件:1.**[基于视频大模型的通用视频高光剪辑算法赛题](https://www.aicomp.cn/wp-content/uploads/2026/09/%E9%99%84%E4%BB%B61-%E5%9F%BA%E4%BA%8E%E8%A7%86%E9%A2%91%E5%A4%A7%E6%A8%A1%E5%9E%8B%E7%9A%84%E9%80%9A%E7%94%A8%E8%A7%86%E9%A2%91%E9%AB%98%E5%85%89%E5%89%AA%E8%BE%91%E7%AE%97%E6%B3%95%E8%B5%9B%E9%A2%98-0930.pdf)

**[2.基于视频大模型的通用视频高光剪辑复赛作品提交要求](https://www.aicomp.cn/wp-content/uploads/2026/09/%E9%99%84%E4%BB%B62%EF%BC%9A%E5%9F%BA%E4%BA%8E%E8%A7%86%E9%A2%91%E5%A4%A7%E6%A8%A1%E5%9E%8B%E7%9A%84%E9%80%9A%E7%94%A8%E8%A7%86%E9%A2%91%E9%AB%98%E5%85%89%E5%89%AA%E8%BE%91%E5%A4%8D%E8%B5%9B%E4%BD%9C%E5%93%81%E6%8F%90%E4%BA%A4%E8%A6%81%E6%B1%82-1.pdf)**

[关于举办产业命题赛道“基于视频大模型的通用视频高光剪辑”复赛的通知](https://www.aicomp.cn/wp-content/uploads/2026/09/%E5%85%B3%E4%BA%8E%E4%B8%BE%E5%8A%9E%E4%BA%A7%E4%B8%9A%E5%91%BD%E9%A2%98%E8%B5%9B%E9%81%93%E5%9F%BA%E4%BA%8E%E8%A7%86%E9%A2%91%E5%A4%A7%E6%A8%A1%E5%9E%8B%E7%9A%84%E9%80%9A%E7%94%A8%E8%A7%86%E9%A2%91%E9%AB%98%E5%85%89%E5%89%AA%E8%BE%91%E5%A4%8D%E8%B5%9B%E7%9A%84%E9%80%9A%E7%9F%A5-1.pdf)

```


## 原文件全文：reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/baseline_a_pts_v1/vendor/temporal_common.py
字节=8859；SHA256=bb8f47896e20e069e9ddf992d94488132ccbee46dc850a2658851f4aa52946b4

```py
#!/usr/bin/env python3
"""temporal_round5 — shared query-free temporal I/O.

Virtual clip:
  The clip is taken ON THE FLY from the source video at
  [clip_start_sec, clip_end_sec]. No clip files are rendered in batch.
  `qwen_vl_utils`' own video_start/video_end slicing records ABSOLUTE frame
  indices, so the processor would label the clip with absolute source times.
  To make the model see time starting at 0 we decode the clip's frames
  ourselves and hand the processor 0-BASED `frames_indices` plus the source fps,
  which makes `_calculate_timestamps` produce clip-local seconds.

Prompt: one query-free prompt, identical for every arm and for training.
  It never receives a QVHighlights query, a teacher summary, cropRois or any
  test-set information.
"""
from __future__ import annotations

import json
import math
import re

MAX_FRAMES = 64
MAX_PIXELS = 128 * 32 * 32           # same per-frame budget as the frozen baseline

PROMPT = (
    "You are shown a short video clip. Identify every time interval in the clip that is "
    "worth keeping in a short highlight edit.\n"
    "Times are seconds measured from the START of this clip, where 0 is the clip start.\n"
    'Return ONLY JSON of the form {"segments": [[start_sec, end_sec], ...]} using '
    "clip-local seconds.\n"
    "Rules:\n"
    "- every interval must satisfy 0 <= start_sec < end_sec <= clip duration\n"
    "- return between 1 and 5 intervals\n"
    "- sort them by start time and do not let them overlap\n"
    "- output nothing except the JSON"
)

_NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)"


def build_virtual_clip(source_path, clip_start_sec, clip_end_sec, max_frames=MAX_FRAMES):
    """Decode the clip's frames and build 0-based video metadata.

    Returns (frames_uint8_THWC, metadata, info).
    """
    import numpy as np
    import decord

    vr = decord.VideoReader(str(source_path))
    total = len(vr)
    fps = float(vr.get_avg_fps())
    if fps <= 0 or total <= 0:
        raise RuntimeError(f"unreadable video {source_path}: total={total} fps={fps}")
    sf = int(math.ceil(max(0.0, clip_start_sec) * fps))
    ef = int(math.floor(clip_end_sec * fps))
    sf = max(0, min(sf, total - 1))
    ef = max(sf + 1, min(ef, total - 1))
    n_clip = ef - sf + 1
    nframes = int(max(1, min(max_frames, n_clip)))
    if nframes == 1:
        local_idx = [0]
    else:
        local_idx = [int(round(x)) for x in np.linspace(0, n_clip - 1, nframes)]
    abs_idx = [sf + i for i in local_idx]
    arr = vr.get_batch(abs_idx).asnumpy()          # (T, H, W, C) uint8
    md = {"fps": fps, "frames_indices": local_idx,
          "total_num_frames": n_clip, "video_backend": "decord"}
    info = {"source_total_frames": total, "source_fps": fps,
            "clip_start_frame_abs": sf, "clip_end_frame_abs": ef,
            "n_frames_in_clip": n_clip, "n_sampled": nframes,
            "clip_local_indices": local_idx, "absolute_indices": abs_idx,
            "clip_local_times_sec": [round(i / fps, 4) for i in local_idx],
            "clip_duration_sec": round(clip_end_sec - clip_start_sec, 6),
            "sampled_span_sec": [round(local_idx[0] / fps, 4),
                                 round(local_idx[-1] / fps, 4)]}
    return arr, md, info


# ---------------------------------------------------------------- parsing
def parse_segments(raw, clip_duration, max_segments=5):
    """Strict parse -> (segments|None, errors, warnings).

    Accepts only a single JSON object with a "segments" list of [a, b] pairs.
    Ranges must be numeric, finite, 0 <= a < b <= clip_duration.
    Overlaps are reported; the returned list is sorted and merged-free (the
    evaluator uses the UNION, so overlaps do not inflate the score).
    """
    errors, warnings = [], []
    if not isinstance(raw, str) or not raw.strip():
        return None, ["empty model output"], warnings
    objs = re.findall(r"\{(?:[^{}]|\{[^{}]*\})*\}", raw, re.S)
    found = None
    for o in objs:
        try:
            d = json.loads(o)
        except Exception:
            continue
        if isinstance(d, dict) and "segments" in d:
            if found is not None:
                return None, [f"ambiguous: more than one JSON object with 'segments'"], warnings
            found = d
    if found is None:
        return None, ["no JSON object containing 'segments'"], warnings
    segs = found["segments"]
    if not isinstance(segs, list):
        return None, [f"'segments' is not a list: {type(segs).__name__}"], warnings
    if len(segs) == 0:
        return None, ["'segments' is empty"], warnings
    if len(segs) > max_segments:
        return None, [f"{len(segs)} segments exceeds the requested maximum {max_segments}"], warnings
    out = []
    for i, s in enumerate(segs):
        if not (isinstance(s, (list, tuple)) and len(s) == 2):
            errors.append(f"segment {i} is not a 2-element list: {s!r}")
            continue
        a, b = s
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in (a, b)):
            errors.append(f"segment {i} has non-numeric bounds: {s!r}")
            continue
        a, b = float(a), float(b)
        if not (math.isfinite(a) and math.isfinite(b)):
            errors.append(f"segment {i} has non-finite bounds: {s!r}")
            continue
        if not (0 <= a < b):
            errors.append(f"segment {i} violates 0 <= start < end: [{a},{b}]")
            continue
        if b > clip_duration + 1e-3:
            errors.append(f"segment {i} exceeds clip duration {clip_duration}: [{a},{b}]")
            continue
        out.append([round(a, 4), round(min(b, clip_duration), 4)])
    if not out:
        return None, errors or ["no usable segment"], warnings
    out.sort()
    for (a1, b1), (a2, b2) in zip(out, out[1:]):
        if a2 < b1 - 1e-9:
            warnings.append(f"overlapping segments [[{a1},{b1}],[{a2},{b2}]]")
    if errors:
        return None, errors, warnings
    return out, errors, warnings


def union_length(segs):
    if not segs:
        return 0.0
    s = sorted(segs)
    tot, a, b = 0.0, s[0][0], s[0][1]
    for x, y in s[1:]:
        if x <= b + 1e-9:
            b = max(b, y)
        else:
            tot += b - a
            a, b = x, y
    return tot + (b - a)


def interval_metrics(pred_segs, gt_segs, clip_duration):
    """Union-based precision / recall / F1 in the clip's time span."""
    if clip_duration <= 0:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    pl = union_length(pred_segs or [])
    gl = union_length(gt_segs or [])
    if pl <= 0 or gl <= 0:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0,
                "pred_union_sec": round(pl, 4), "gt_union_sec": round(gl, 4),
                "inter_sec": 0.0}
    # intersection length of two union-of-intervals
    def to_segments(segs):
        s = sorted(segs)
        m, a, b = [], s[0][0], s[0][1]
        for x, y in s[1:]:
            if x <= b + 1e-9:
                b = max(b, y)
            else:
                m.append([a, b]); a, b = x, y
        m.append([a, b])
        return m
    A, B = to_segments(pred_segs), to_segments(gt_segs)
    inter, i, j = 0.0, 0, 0
    while i < len(A) and j < len(B):
        lo, hi = max(A[i][0], B[j][0]), min(A[i][1], B[j][1])
        if hi > lo:
            inter += hi - lo
        if A[i][1] < B[j][1]:
            i += 1
        else:
            j += 1
    p = inter / pl
    r = inter / gl
    f1 = (2 * p * r / (p + r)) if (p + r) > 0 else 0.0
    return {"precision": round(p, 6), "recall": round(r, 6), "f1": round(f1, 6),
            "pred_union_sec": round(pl, 4), "gt_union_sec": round(gl, 4),
            "inter_sec": round(inter, 4)}


def materialize_clip_file(source_path, clip_start_sec, clip_end_sec, out_path):
    """Write ONE temporary clip file for the virtual window.

    Needed for the Qwen3.5 (Video-ORA-4B) video path, whose processor rejects a
    directly supplied frame tensor. The file is cut with -ss/-t so its timeline
    starts at 0, i.e. the clip is still "virtual" (one file at a time, deleted
    after use; nothing is batch-rendered onto disk).
    """
    import subprocess
    from pathlib import Path
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    dur = max(0.04, clip_end_sec - clip_start_sec)
    subprocess.run(["/usr/local/bin/ffmpeg", "-nostdin", "-y", "-v", "error",
                    "-ss", f"{clip_start_sec:.6f}", "-i", str(source_path),
                    "-t", f"{dur:.6f}", "-c:v", "mpeg4", "-q:v", "3",
                    "-pix_fmt", "yuv420p", "-an", str(out)],
                   check=True, stdin=subprocess.DEVNULL)
    return str(out)


def load_split(name, r5root):
    from pathlib import Path
    p = Path(r5root) / "data" / f"{name}.jsonl"
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]

```

END_EMPTY407_R00B


## 第一轮原始完整公开回答：tibo-r00.md
SHA256=5470e02ee3f86f8de522e954db6c72bd7bbbf9203b05077ac8eb1fc426fb98d6

12:36收到。我先完整读取这份新卷宗，核清407/426空输出的实际证据，再区分校准、语义、时序和训练目标的问题，给出唯一有界路线。本轮只讨论，不联网或执行实验，也不会把声明SHA当作已独立验签。12:36

已完整分段读取 context-r00(3).md 第1–37132行，读至 END_EMPTY407_R00；展示截断处已补读。quality_result.json 的4臂×9源、共5404个评分四元组也已完整核对。841249字节及 d41e…fea0 是主控声明；本次读取的是工具提供的文本，没有独立验证原文件字节SHA。我的唯一主案：先做“可审计事件标签小试”，通过后从37.66对应原B续训一次；未通过就保留原B、NO426。停止扩训当前图片评分配方。校准检查用于辨别病因，不另开一条降阈值冲包路线。407空的病因：目前可以确定什么校准问题有实证，但不是唯一原因。阈值49来自训练集人工分数的80分位，没有证明它可直接用作模型输出的决策界。已有9源开发结果中，新模型1351点预测范围24–53，80分位38、95分位48；≥49仅48点，占3.55%。对应人工≥49有293点，占21.69%。新模型已有4/9开发源为空，这四源都有人工作为高重要性的评分点。但不能据此把阈值改成38。新模型≥49那部分平均预测50.69、平均人工50.65，尾部均值并非普遍低估；尺度压缩与具体排序错误同时存在。语义错误不能靠标量校准修好。最直接的非测试反例来自同一源 sTEELN-vY30：grid5/ordinal329，人工87、预测48，被丢；grid32/ordinal1949，人工27、预测50，被选。任何保序一维校准都不能纠正这对逆序。这里的人工分数仍只是TVSum重要性，不是AIC高光真值。时序问题是另一层：单个中点的重要性不能推出整个2秒都应保留。已有扇舞28/29秒与29.96秒行人切镜，足以推翻整格无条件扩展。反过来，短动作若根本没进入学生输入，降低阈值也无法补回信息。目标函数问题尚未排除。237步、非零梯度和权重改变证明真实训练，不能证明任务目标正确。附件的 observed_train.py 是外部训练器包装；没有展示实际collator的label mask和完整loss实现，不能独立确认prompt、padding是否正确排除。整数文本CE本身也不直接优化事件召回和边界。grammar没有强制空输出：它约束每图20–100整数，再由≥49选择；有效低分形成合法空。11项strict和回放PASS主要证明工程合同。407空是严重风险信号，但没有测试真值，不能宣称真实召回就是零。我对主控的关键批评旧投入门比较的是新评分器与base在新图片任务上的点估计，native代理F的差值区间还跨零；production_B也被放进图片评分prompt，并未与37.66原生视频系统公平比较。这个门能放行“相对很弱基线略好、绝对质量仍差”的候选。新立场仍有一个容易重犯的漏洞：“UNKNOWN不转负例”不够。若完整窗口含UNKNOWN，却把目标写成只列KEEP的完整segments列表，闭括号和停止生成仍在教学生遗漏未知区域。必须整窗排除这种样本，不能只在记录里写一句unknown_never_negative。此外，“强闭源能产高质量标签”应当是待检验假设，不能当开工前提。最小非测试判别与G0先复用已有成功raw，不重跑四臂生成：冻结上述分布、逆序例、4个开发空源及随机对照，逐项检查事件是否进入实际学生采样。分清“看见但低估”“看见却认错”“根本没看见”“单点正确但扩段错误”。已见9源和NT8只作诊断，不改名盲确认。取一条实际训练batch核input/labels、视觉占位及padding的mask、答案token数量、损失归一化；补齐外部训练器的真实合同。candidate0锁定37.66那套完整balanced_two_window_v3 native系统：原B adapter、实际展开prompt、grammar、processor、floor64、精确PTS、双窗、解码和空间场。不能拿旧CFR入口或图片评分版production_B替代。特别核实版本缝隙：最新协议写0..5，旧附录prompt写1..5。材料不足以断言当前生产冲突，必须核实际运行锁的字节；不能借核验偷偷修改candidate0。若实际prompt不支持明确空窗，须先解决新训练合同与原基线的兼容问题，本轮不得直接喂入冲突的空目标。建来源关系表：原视频、转载、裁剪、近重复及历史训练曝光归组。9已见dev、旧标注和104/96开发经历如实登记；不读100confirm，不假设库存里天然有未暴露金标。这些检查若已表明没有可审计观察路径、来源无法隔离或训练合同无法绑定，就STOP，不花训练费。标签必须怎样才可入训优先终端agy，但native MP4调用成功和“1fps/30images”自报不等于实际观察证明。现在6片90格的teacher入训仍为0，处理正确。每条事件记录至少包含：来源组、源SHA、窗口、原生ordinal/PTS、学生实际输入清单、标注规则版本。程序生成的证据帧ID与像素哈希；实际供给回执、教师声称看过的ID、独立审查确认的事实分别存储。KEEP/明确NO/UNKNOWN，可见动作事实与高光理由分开写。起止边界的内外证据ID、不确定区间、切镜关系、上下文不足或音频缺失等限制。审查者、盲审原始结论、争议及准入理由。教师引用已存在的证据ID，不自由编精确秒数。关键动作与边界补供显式连续原生帧；仍看不清就UNKNOWN。确切坐标不代表确切语义。切镜触发检查，不机械充当高光边界：跨镜事件可以成立，但两侧都须有证据；单镜头也可能早已结束事件。禁止把一侧KEEP自动扩到另一侧，禁止事后裁剪教师端点来伪造通过。独立审查先看媒体和冻结规则、后看教师答案；所有NO也审，不只审高置信KEEP。同教师复查或多个教师一致只算弱证据。闭源标签称“可审计银标”，没有人工独立裁决就不升级为金标。完整segments SFT只收全窗可监督样本：整个声明范围均有经审查KEEP或明确NO，未列区域不自动算NO。含未解决UNKNOWN整窗排除。明确全窗NO才可输出[]。边界仍只有模糊包围范围时，不取中点冒充精确标签。教师看见而学生输入不可辨认的关键事件，也不能强塞为精确监督。唯一有界工作包以下数字是我建议新冻结的投入上限，不是统计保证，也不改写旧STOP。标注阶段：先复用原六片及原raw检查新证据合同；新增请求只为新观察或独立盲审，不重复成功调用。扩展上限24个现有许可source_group，每组事前固定2个≤30秒窗口，共48窗。12组训练、6组流程开发、6组锁定确认，按来源关系和真实曝光史先冻结；不能根据模型结果选窗、换组。总计最多108次闭源请求，含48次提案、48次盲审和12次证据补查；原六片若产生新调用也计入此总额。供给视频累计上限30分钟，实际usage及费用逐项追加。至少取得8个训练组、16个完整可监督窗口才训练；明确正事件和明确NO均须跨多个来源。开发、确认集合若无法提供可评价的正事件及NO范围，就NO426，不能反复换样本凑门。缺乏足够来源、上下文或观测能力，在上限内无法解决就停止。无需无限等人工，也不拿弱参考冒充真值。训练阶段：从原B全部288个adapter张量精确加载；保持原r16/alpha32、语言q/k/v/o，基座及视觉冻结。新建优化器明确记账，不宣称恢复原优化器轨迹。一次固定lr=1e-5、3遍已接纳数据，有效batch4、最多18次更新；不扫学习率、轮数或checkpoint。采用源均衡及逐样本答案长度归一的assistant-only CE，具体公式与mask在开跑前冻结。前2步做真实梯度、冻结参数和保存重载验收，随后沿同一优化器/RNG继续，不能重启重复曝光。只评估固定终点与candidate0。新训练计费上限1200秒，非测试推理1200秒，获准的唯一426出口另限2400秒；任一阶段到限未完成即停，不拿半成品充当通过。沿用现有算力，不新增租卡。闭源费用还须按实际终端计费方式登记，次数上限不等于免费。前瞻质量门与出口先完成参考、冻结标签和规则，再揭示候选预测。开发用于一次淘汰，不用于改配方；确认只使用一次。旧曝光无法排除时如实降为锁定开发审查，不能宣称独立泛化验证。主指标是逐source等权的经审查区间F1，辅助必须同时报：事件召回、明确NO误选时长、含正事件却全空的窗口数、边界外溢及不确定范围。完整分母、拒收和UNKNOWN都报告，不能丢掉难例再报好看均值。TVSum排序、教师一致率和格式合法率单列。建议放行条件：开发均值ΔF1>0；确认6组至少4组ΔF1>0、均值>0、留一组后均值均≥0；确认宏precision、recall均不退化，正事件漏空数及明确NO误选比例均不增加。证据、来源、采样或切镜合同出现未解决违规直接STOP。以上只是小预算风险筛选，六组不能证明统计显著或官方涨分。全部通过且参考具备可审查事实依据，才允许制作一个质量UNKNOWN的426风险包：沿用冻结native管线和完整空间场后过滤，核实际总参数≤9B、全部426记录、时钟/边界/JSON严格验收和唯一成本终态。不在426结果上调整阈值、TopK或重选权重；制包不等于官网提交或替换生产授权。任何门失败则NO426，继续保留原B37.66。对我自己主案的最强反例强闭源审查也可能把“显著、热闹、有运动”系统性偏好成高光；学生在银标F1上胜原B，官方却下降。两张都正确的1fps画面还可能共同漏掉中间动作，教师一致只会强化同一个错误。上述门只能压低这种风险，不能消除共同偏差。另一种反例是：目标一致的非测试审查最终发现排序已足够好，主要只是尺度问题，那么续训不是最省钱的办法。故小试必须允许否定续训必要性；此时本轮STOP并提交新证据讨论，不能为了兑现“要训练”硬跑。最终裁决：有可靠的TVSum重要性监督，不等于已有可靠的AIC事件边界监督。当前最值得买的新信息，是可复查的事件与完整窗口监督，以及相对原B native的真实配对证据。先验证这两件事，再决定是否花那一次续训和426预算。12:44

## 第一轮原始完整公开回答：sol-r00.md
SHA256=3d2f0a034019c68bb369555108b887a645049eda68c4c8b8de0a51e5af15cb57

说：
EMPTY407-20261010｜第一轮独立会诊

任务ID： AIC-VIDEO-REMATCH-NEXT-20261005
子议题： EMPTY407-20261010
版本： r00
实际附件： context-r00(3).md

一、附件核验与读取范围

已在本地直接读取附件，并独立完成文件完整性核验：

核验项

	

结果




文件字节数

	

841,249，吻合




文件行数

	

37,132，吻合




SHA-256

	

与主控声明完全一致




文件末尾

	

END_EMPTY407_R00，存在




本轮边界

	

仅文字会诊，不执行实验、不联网

独立计算的 SHA-256：

d41e34c692283252bec48c0635d5ea3a2ac1f84f3eada219f5fcea60a570fea0

后续判断以附件中的真实结果、代码、协议及历史裁决为基础，不把报告自述的成功等同于独立实验复现。

二、独立技术判断：为什么出现407个空视频
1. 现有证据

以下数值来自附件记录及保存的代码，不是本轮重新执行的模型实验。

指标

	

历史最佳B

	

新237步评分器




复赛视频数

	

426

	

426




选中帧数

	

102,112

	

3,189




空视频数

	

未给出精确数量

	

407




非测试8源

	

旧生产链已有验收

	

8/8为空




已知官网分

	

用户反馈37.66

	

未知

新评分器空视频比例为 95.54%。它不是一个有可靠AIC质量证据支持的替代方案。
context-r00.md

我另外检查了 quality_result.json 保存的9个开发源预测分布，发现一个比总体Spearman更值得重视的现象：

新模型9源预测分数的最高值分别为：50、47、50、52、42、48、46、53、50。

9源中有4源，最高预测分仍低于冻结阈值49，所以这些源在该规则下必然全空。

新模型的排序相关系数明显提高，但它给出的绝对分数集中在较低范围，且最高分普遍只比阈值略高。

阈值49来自人工训练标签的80%分位数，并不是模型预测分数的已验证校准分位数。

这构成了当前最具体的校准失配证据。

还要注意：新模型在已见9源上的TVSum Spearman为0.522329，相对基座0.043629，确实有排序学习；但native代理F改善的配对95%区间为[-0.001096, 0.210326]，包含0。
context-r00.md

因此不能简单说模型完全没学会，也不能据此认定其具有AIC高光选择能力。

2. 四类根因必须分开

根因

	

当前证据强度

	

我的判断




分数校准失配

	

较强

	

很可能直接导致大量阈值下全空




语义任务错配

	

较强的机制证据

	

TVSum重要性与AIC可剪辑高光并非相同标签目标




时序信息与边界缺失

	

已有具体失败案例

	

单个2秒中点不能代表整格内的动作及切镜




目标函数与任务不一致

	

代码可以确认

	

训练优化评分文本的交叉熵，未直接优化高光事件召回与时间边界

我检查了 selector_contract.py、score_grammar.py 和 contest_engine.py。

新系统的实际决策结构为：

2秒格中点采样 → 每批最多16张有序静态图

预测 scores_x20，语法限制为20–100

score >= 49 保留，否则丢弃

整个2秒格选入或排除 → 复用完整空间场

这个管线具有明确的结构性限制：

即使评分器正确发现某一帧很重要，它也不能直接确定真实事件的开始、结束、动作是否完成，以及2秒范围内是否出现切镜。

407空则是另一种失败表现：绝对分数偏低时，严格阈值把弱但有价值的候选也全部过滤掉。

不能在这两种错误之间直接选择“降低阈值”。降低阈值可能增加召回，也可能仅仅增加无意义帧。

3. 校准和语义哪个是主因？

我会区分两个问题：

问题A：为什么新系统几乎不输出？
现有证据首先指向校准失配与阈值化机制。

问题B：就算让新系统多输出，能否提高AIC成绩？
现有证据不足，而且语义与边界监督不匹配仍可能造成重大损失。

因此，修复407空的输出分布，不等于修复高光质量。

我反对继续扩大相同TVSum评分配方，也反对仅通过改变分数阈值产出另一个426包。

三、唯一推荐路线：原B Native事件监督续训
推荐主案：B-NATIVE-EVENT-SFT-v1

保留37.66原B作为candidate0，以原B原生视频窗口为训练单位，利用agy产生事件候选，再通过独立视觉与边界审查获得小规模高可信监督。只有监督完整且公平对照通过，才允许一次有界LoRA续训和后续候选验收。

不继续训练TVSum图片评分器，不引入新架构，不并行探索其他模型。

这条路线的核心不是寻找更强的教师，而是把训练目标从“帧重要性打分”重新对准“可实际剪辑的高光事件区间”。

阶段A：最小根因判别，先不训练

严格限定在已有非测试资源。

检查

	

最小操作

	

判别结果




校准

	

读取冻结的train/9dev评分，统计分位数、分数范围、阈值49以上比例

	

排序尚可但分数普遍低，支持校准失配




语义

	

对少量独立审查的非测试事件，比较TVSum高分与实际可剪辑事件

	

高重要性不等于高光，支持目标错配




时序

	

比较原B64帧原生采样、新模型2秒中点与事件真实可见帧

	

有事件但采样不可见，支持时序瓶颈




输出目标

	

检查完整事件标签、缺失区间、模型格式及可表达范围

	

判断是否可用现有B协议做完整窗口监督

这里最重要的是可观察性检查。

如果独立参考确认某个关键动作发生，但原B的实际输入采样根本没有捕获该动作的可识别证据，那么增加微调步数不可能稳定解决这个特定问题。

如果原B能够观察到动作，却没有选择，才具有进一步研究语义监督的价值。

所有检查必须在训练配方冻结前完成，不读取复赛单视频输出。

阶段B：agy标注，最多24个原生窗口

建议一次前瞻试验上限：

项目

	

冻结上限




数据

	

现有且用途许可明确的非测试视频




来源组

	

最多12个彼此隔离的来源组




每组

	

2个不重叠的原B原生窗口




总视频窗口

	

24个，每窗不超过30秒




agy首次调用

	

最多24次




定点边界补查

	

最多8次




新大数据下载

	

0

预先按照来源组划分6组训练、3组校准、3组确认。相同视频、同源派生裁剪、重复素材不能跨组；还需核对历史B训练和开发曝光记录。如果找不到满足条件的来源，就缩小可用集合并明确降低证据等级，不把已见开发集冒充全新盲测。

历史已有6段90格标注保留为流程失效案例，不直接升级训练样本。
context-r00.md

新标注不再以2秒KEEP列表作为最终训练目标，而是要求agy针对原B实际窗口输出可追溯的事件及其起止证据。

阶段C：标注格式与真实观测要求

建议使用如下核心字段；具体枚举和路径应在首次模型调用前冻结。

JSON
{
  "source_id": "source-id",
  "source_group": "group-id",
  "source_sha256": "...",
  "window_id": "...",
  "clip_sha256": "...",
  "time_basis": "native_pts",
  "observation": {
    "tool": "agy/view_file",
    "actual_observed_ordinals": [],
    "coverage": "SPARSE",
    "full_observation_proven": false
  },
  "events": [
    {
      "state": "KEEP",
      "event_type": "action_or_result",
      "start_native_ordinal": 1200,
      "end_native_ordinal_exclusive": 1240,
      "positive_evidence_ordinals": [],
      "boundary_evidence_ordinals": [],
      "boundary_status": "UNVERIFIED",
      "confidence": "MEDIUM"
    }
  ],
  "unresolved_ranges": [],
  "full_window_supervision_eligible": false
}

这些是格式示意，不代表已存在对应帧或审核结果。

需要保留原模型答复、原生媒体SHA、实际输入、模型声明的观察时刻、独立核验的物理帧以及规范映射结果。教师声称看见的内容与审查人员实际验证过的内容必须分字段存储。

建议用双层观察方式：

第一层通过agy读取原生短MP4并描述候选事件。第二层基于真实native PTS提供可索引的视觉证据，尤其是事件起止和切镜附近的较密集帧序列。即使视频工具报告1fps，也不能推断模型连续观察了完整视频。

对正例区间，必须至少能够核验事件内部的正向证据，并用起止附近的前后帧支持边界。只有内部证据而没有边界证据的片段，不应取得精确时间监督资格。

切镜是硬边界问题，而不是标注格式问题。

以附件中28–30秒扇舞案例为例，28/29秒确有扇舞，29.96秒已经出现行人。不能因为28/29秒正确，就把整个28–30秒赋为KEEP。
context-r00.md

接受条件应是：

区间端点映射到合法原生ordinal，半开范围精确，无来源漂移。

每个KEEP都有真实可观察的事件依据，且原B实际采样至少具有足以识别该事件的证据。

已确认的切镜必须分段或截断；切镜位置不确定则边界保持UNKNOWN。

REJECT必须有已观察到的明确过渡或冗余证据，UNKNOWN不能当负例。

未能覆盖完整窗口时，禁止把部分KEEP列表转换为完整窗口的segments监督。

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


## 补充原文件全文：reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/teacher_student_autopilot_v14/train_student.py
字节=78139 SHA256=7b79a6713e3a406d015bc546fc45ce6172b7cf8d3967592779bfdd8c23a6fe09

```py
"""One admitted Route A run: inspect an early prefix, compare B and T on weak dev.

All model imports are deferred until authority/data/semantic admission passes.
This engine never downloads, transfers, opens confirm/test, or starts a GPU job.
"""
from __future__ import annotations

import argparse
import copy
from collections import Counter
import datetime as dt
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path, PurePosixPath
import random
import statistics
import subprocess
import sys
import time
import traceback

REVISION = "0c351dd01ed87e9c1b53cbc748cba10e6187ff3b"
HERE = Path(__file__).resolve().parent
VERSION = HERE.name
INITIAL_SHA = "8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23"
APPROVED_MANIFEST_SHA = {"train": "ef427866153a9601be01b6e12356951c2fb56730525b0d7b7c353651c2930ddf",
                         "dev": "53f7053fc3df698ce96c94b04f1af3b5c0c210ce93ecd3269b6306daf4c0a700"}
VIDEO_SIZE = {"shortest_edge": 4096, "longest_edge": 25165824}
INPUT_CONTRACT = {
    "max_frames": 64, "video_size": VIDEO_SIZE, "max_input_tokens": 16384,
    "clock": "REAL_SOURCE_PRESENTATION_PTS_RELATIVE_TO_WINDOW_START",
    "sampling": "SELECTED_WINDOW_INTEGER_FLOOR_ENDPOINTS",
    "decoder": "SEQUENTIAL_PYAV_RGB24_WITH_ACTUAL_PTS_AND_PIXEL_SHA",
    "allow_empty": True, "prompt": "NEXT_ROUND_0_TO_5", "truncation": False,
    "same_contract_train_dev_production": True,
    "endpoint_precision": "EXACT_FINITE_DECIMAL_UP_TO_18_FRACTIONAL_DIGITS_NO_ROUNDING",
    "positive_segment_realizability": "ACTUAL_SOURCE_PTS_HALF_OPEN_NONEMPTY",
}
REQUIRED_HELPERS = (
    "next_round_v1/common.py", f"{VERSION}/precision_helpers/contracts.py", "next_round_v1/video_contract.py",
    f"{VERSION}/precision_helpers/training_target.py", f"{VERSION}/precision_helpers/engine.py",
    f"{VERSION}/supervision/validate_teacher.py", f"{VERSION}/supervision/select_windows.py",
    f"{VERSION}/supervision/teacher_prompt.txt", f"{VERSION}/supervision/teacher_metadata_20261007.json",
    f"{VERSION}/supervision/teacher_response.schema.json", f"{VERSION}/precision_helpers/constrained_json.py",
    f"{VERSION}/native_segment_contract.py",
    f"{VERSION}/source_color.py",
    f"{VERSION}/teacher_label.py", f"{VERSION}/boundary_ids.py",
    f"{VERSION}/teacher_prompt.txt", f"{VERSION}/review_prompt.txt",
    "baseline_a_pts_v1/exact_pts.py", "baseline_a_pts_v1/native_frames.py", "baseline_a_pts_v1/pts_contract.py",
    "baseline_a_pts_v1/a_contract.py", "temporal_sft8b_v1/sft_contract.py",
    "temporal_sft8b_v1/train_sft.py", "temporal_sft8b_v1/verify_saved_smoke.py",
    "baseline_a_pts_v1/vendor/temporal_common.py",
)
_VERIFIED_SOURCE_STATS = {}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def record_sha(record):
    return hashlib.sha256(json.dumps(record, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def write(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def bound(ref):
    require(isinstance(ref, dict) and set(ref) == {"path", "sha256"}, "missing bound file reference")
    path = Path(ref["path"]).resolve(strict=True)
    require(path.is_file() and sha(path) == ref["sha256"], "bound file changed: " + str(path))
    return path


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def helper_paths(run):
    # Frozen modules import each other by their historical names.
    paths = [run / "next_round_v1", run / "baseline_a_pts_v1", run / "baseline_a_pts_v1/vendor",
             run / "temporal_sft8b_v1", run / VERSION / "supervision"]
    sys.path[:0] = list(map(str, paths))
    # common.py prepends old search paths. Explicit module identities, rather
    # than path priority alone, bind the entire serializer/target/generation
    # bridge to this registered version, even after a legacy import.
    precision = Path(__file__).resolve().parent / "precision_helpers"
    for name in ("contracts", "constrained_json", "engine", "training_target"):
        expected = precision / (name + ".py")
        current = sys.modules.get(name)
        if current is None or Path(current.__file__).resolve() != expected.resolve():
            load(expected, name)
        require(Path(sys.modules[name].__file__).resolve() == expected.resolve(), "precision helper binding differs: " + name)
    owner = str(Path(__file__).resolve().parent)
    if owner not in sys.path:
        sys.path.insert(0, owner)


def schedule(n, epochs=3, batch=16, seed=20261007):
    require(type(n) is int and n > 0 and type(epochs) is int and 1 <= epochs <= 3 and
            type(batch) is int and batch > 0, "invalid training schedule")
    rng = random.Random(seed)
    result = []
    for epoch in range(1, epochs + 1):
        order = list(range(n))
        rng.shuffle(order)
        for offset in range(0, n, batch):
            result.append({"epoch": epoch, "indices": order[offset:offset + batch],
                           "epoch_last": offset + batch >= n})
    require(len(result) >= 2, "STOP_T_INSUFFICIENT_ELIGIBLE_UPDATES_WITHIN_MAX_3_EPOCHS")
    return result


def prefix_update_count(batches, limit=4):
    require(type(limit) is int and 2 <= limit <= 4, "early prefix update limit must be 2..4")
    require(len(batches) >= 2, "STOP_T_INSUFFICIENT_ELIGIBLE_UPDATES_WITHIN_MAX_3_EPOCHS")
    return min(limit, len(batches))


def supervision_classes(targets):
    """Only actual admitted complete-window targets establish class availability."""
    require(targets, "STOP_T_NO_ADMITTED_TRAIN_SUPERVISION")
    counts = {"positive": 0, "explicit_no_highlight": 0}
    for target in targets:
        require(type(target.get("explicit_no_highlight")) is bool, "missing observed target class")
        segments = json.loads(target["target_json"])["segments"]
        require(isinstance(segments, list) and (not segments) == target["explicit_no_highlight"],
                "actual empty target and explicit NO semantics differ")
        counts["explicit_no_highlight" if target["explicit_no_highlight"] else "positive"] += 1
    require(counts["positive"] > 0, "STOP_T_NO_POSITIVE_SUPERVISION_FOR_ROUTE_A")
    return dict(**counts, rejection_supervision_available=counts["explicit_no_highlight"] > 0,
        whole_window_rejection_learning_claim=False,
        supervision_role="ACCEPTED_COMPLETE_WINDOW_WEAK_TEACHER_NOT_HUMAN_TRUTH")


def select_checkpoint(candidates):
    """Candidate zero is retained; a weak-metric tie always preserves original B."""
    require(candidates and any(c["epoch"] == 0 for c in candidates), "original B candidate zero missing")
    require(all(type(c["epoch"]) is int and c["epoch"] >= 0 and
                type(c["video_macro_f1"]) in (int, float) and math.isfinite(c["video_macro_f1"])
                for c in candidates), "invalid candidate development evidence")
    return max(candidates, key=lambda value: (value["video_macro_f1"], -value["epoch"]))


def floor_indices(first, stop, max_frames=64):
    require(type(first) is int and type(stop) is int and 0 <= first < stop and max_frames == 64,
            "invalid T source ordinal window")
    count = stop - first
    if count <= max_frames:
        return list(range(first, stop))
    return [first + i * (count - 1) // (max_frames - 1) for i in range(max_frames)]


def window_from_pts(source_path, source_sha256, points, start, end, window_id, **identity):
    """Public T production planner; points are raw presentation seconds.

    The controller supplies a SHA-bound full source PTS table and natural
    windows, including the packet-duration endpoint. It must preserve raw
    origin in start/end; this function never derives timestamps from FPS.
    """
    from bisect import bisect_left
    require(points and all(math.isfinite(t) for t in points) and all(b > a for a, b in zip(points, points[1:])),
            "full source native PTS required")
    require(math.isfinite(start) and math.isfinite(end) and start < end and end - start <= 30 + 1e-6,
            "invalid T natural time window")
    first, stop = bisect_left(points, start), bisect_left(points, end)
    ids = floor_indices(first, stop)
    return dict(identity, source_path=str(source_path), source_sha256=source_sha256, window_id=window_id,
        window_pts_start_sec=start, window_pts_end_exclusive_sec=end, window_duration_sec=end - start,
        planned_source_frame_ordinals=ids, planned_actual_pts_sec=[points[i] for i in ids],
        eligible_source_frame_count=stop - first, source_total_frames=len(points))


def validate_isolation(train, dev):
    require(train and dev and len(train) <= 512 and len(dev) <= 64, "invalid eligible train/dev denominator")
    all_ids = [r["window"]["window_id"] for r in train + dev]
    require(len(set(all_ids)) == len(all_ids), "duplicate eligible window")
    for split, values in (("train", train), ("dev", dev)):
        for row in values:
            w = row["window"]
            require(w.get("split") == split and w.get("source_group") == w.get("youtube_id"), "wrong split/source unit")
            p = PurePosixPath(w.get("source_path", ""))
            require(p.is_absolute() and ".." not in p.parts and
                    PurePosixPath("/home/inspur/aic_video_data/videos") in p.parents, "confirm/test/outside-media path rejected")
    for key in ("youtube_id", "source_path", "source_sha256"):
        require(not ({r["window"][key] for r in train} & {r["window"][key] for r in dev}), "train/dev leakage: " + key)


def validate_lineage(eligible, approved, split):
    identities = {(r["source_path"], r["youtube_id"]): set() for r in approved}
    for row in approved:
        require(row.get("split") == split, "approved manifest split changed")
        identities[(row["source_path"], row["youtube_id"])].add(row["sample_id"])
    for row in eligible:
        window = row["window"]
        key = (window["source_path"], window["youtube_id"])
        parents = window.get("parent_sample_ids")
        require(key in identities and isinstance(parents, list) and parents and
                set(parents) <= identities[key], "eligible source/parent not in approved original " + split + " registry")


def validate_raw_semantic(item, original):
    def pairs(values):
        result = {}
        for key, value in values:
            require(key not in result, "duplicate raw semantic review JSON key")
            result[key] = value
        return result
    def invalid_constant(value):
        raise ValueError("nonfinite raw semantic review JSON: " + value)
    value = json.loads(item["raw_response"], object_pairs_hook=pairs, parse_constant=invalid_constant)
    require(isinstance(value, dict) and set(value) == {"window_id", "observation_scope", "semantics_consistent", "uncertain", "reason", "issues"},
            "raw semantic review response schema changed")
    require(value["window_id"] == original["window_id"] and value["semantics_consistent"] is True and
            value["uncertain"] is False and value["issues"] == [] and value["reason"] == item["reason"] and
            isinstance(value["reason"], str) and value["reason"].strip(), "raw semantic review does not support receipt PASS")
    scope = value["observation_scope"]
    require(isinstance(scope, dict) and set(scope) == {"window_pts_start_sec", "window_pts_end_exclusive_sec", "sampled_pts_sec", "all_provided_frames_reviewed"}
            and scope["all_provided_frames_reviewed"] is True, "raw semantic review observation scope changed")
    window = original["window"]; observation = original["actual_observation"]
    for key in ("window_pts_start_sec", "window_pts_end_exclusive_sec"):
        require(type(scope[key]) in (int, float) and math.isfinite(scope[key]) and abs(scope[key] - window[key]) <= 1e-6,
                "raw semantic review window extent differs")
    points = scope["sampled_pts_sec"]
    require(isinstance(points, list) and len(points) == len(observation["actual_pts_sec"]) and
            all(type(a) in (int, float) and math.isfinite(a) and abs(a - b) <= 1e-6 for a, b in zip(points, observation["actual_pts_sec"])),
            "raw semantic review did not observe same actual PTS")
    require(item.get("parsed_response") == value and item.get("source_frame_pixel_sha256") == observation["frame_pixel_sha256"] and
            item.get("source_frame_ordinals") == observation["source_frame_ordinals"] and item.get("actual_pts_sec") == observation["actual_pts_sec"],
            "semantic review raw/frame identity differs from teacher observation")


def verify_semantic(review, validation_sha, file_hashes, eligible, records, verifier, validator):
    """Engineering-complete review admits only individually supported records.

    Every reviewed raw decision is checked, including disagreement/UNKNOWN.
    The full denominator and all original records remain SHA-bound.
    """
    require(review.get("schema") == "aic_automated_weak_semantic_review_v2" and
            review.get("status") == "PASS_AUTOMATED_WEAK_SEMANTIC_REVIEW" and
            review.get("mode") == "AUTOMATED_WEAK_TEACHER_REVIEW_NOT_HUMAN_GROUND_TRUTH" and
            review.get("manual_ground_truth") is False and review.get("confirm_opened") is False and
            review.get("contest_assets_opened") is False and
            review.get("second_review_same_teacher_not_independent_evidence") is True and
            review.get("review_blind_to_first_answer") is True and
            review.get("no_unknown_or_unobserved_gaps_certified_negative") is True and
            review.get("no_forced_empty_quota") is True, "STOP_T_SEMANTIC_REVIEW_REQUIRED")
    require(review.get("validation_receipt_sha256") == validation_sha and review.get("files") == file_hashes,
            "semantic review does not bind actual supervision files")
    eligible_expected = {r["teacher_record_sha256"] for r in eligible}
    expected = set(records)
    reviewed = review.get("reviewed_teacher_record_sha256", [])
    supported = review.get("supported_teacher_record_sha256", [])
    require(isinstance(reviewed, list) and len(set(reviewed)) == len(reviewed) and set(reviewed) == expected,
            "eligible semantics not exhaustively reviewed")
    require(isinstance(supported, list) and len(set(supported)) == len(supported) and set(supported) <= eligible_expected,
            "unknown/foreign/duplicate supported teacher record")
    raw_path = bound(review["raw_review_receipts"])
    raw = rows(raw_path)
    indexed = {r.get("teacher_record_sha256"): r for r in raw}
    require(len(indexed) == len(raw) and expected == set(indexed), "missing/duplicate/foreign real blind reviews")
    actual_supported = set()
    classification = {}
    actual_table = []
    for digest in expected:
        item = indexed[digest]
        original = records[digest]
        require(item.get("schema") == "aic_blind_local_window_second_selection_v1" and
                item.get("window_id") == original["window_id"] and
                item.get("program_complete_observation") is True and
                item.get("same_teacher_not_independent_truth") is True and item.get("manual_ground_truth") is False and
                (item.get("diagnostic_only") is False or verifier.approved_registered_pilot_review(item, original)) and
                isinstance(item.get("reason"), str) and item["reason"].strip() and
                item.get("reviewer_model_id") == verifier.TEACHER_ID and
                item.get("reviewer_model_revision") == verifier.TEACHER_REVISION and
                item.get("reviewer_runtime_revision") == item.get("second_teacher", {}).get("runtime_revision") and
                isinstance(item.get("raw_response"), str) and item["raw_response"].strip(),
                "STOP_T_UNBOUND_OR_UNEXPLAINABLE_BLIND_REVIEW")
        require(item.get("raw_response_sha256") == hashlib.sha256(item["raw_response"].encode()).hexdigest() and
                item["raw_response"] == item.get("model_raw_answer"),
                "semantic review raw response not bound")
        comparison = verifier.verify_blind_review_projection(item, original, validator)
        classification[digest] = comparison["support_class"]
        if comparison["supported"]:
            expected_class = ("SUPPORTED_COMPLETE_WINDOW_NO_HIGHLIGHT" if original["explicit_no_highlight"]
                              else "SUPPORTED_COMPLETE_WINDOW_POSITIVE")
            require(comparison["support_class"] == expected_class and
                    item.get("review_status") == "PASS_EXPLAINABLE_SAMPLED_WINDOW_REVIEW" and
                    item.get("uncertain") is False and item.get("semantics_consistent") is True,
                    "supported review does not agree with actual canonical target class")
            if digest in eligible_expected:
                require(original.get("sft_eligible") is True, "supported target lacks original strict eligibility")
                actual_supported.add(digest)
        else:
            require(comparison["support_class"] == "UNKNOWN" and
                    item.get("review_status") == "UNKNOWN_WEAK_SELECTION_DISAGREEMENT" and
                    item.get("uncertain") is True and item.get("semantics_consistent") is False,
                    "disagreement/UNKNOWN was changed to usable supervision")
        actual_table.append(dict(window_id=original["window_id"], split=original["split"], teacher_record_sha256=digest,
            support_class=comparison["support_class"], boundary_supported=comparison["boundary_supported"],
            reasons=comparison["reasons"]))
    require(actual_supported == set(supported), "semantic supported set differs from actual blind raw decisions")
    support_table = review.get("perrecord_support")
    require(isinstance(support_table, list) and len(support_table) == len(actual_table) and
            sorted(support_table, key=lambda value: value["teacher_record_sha256"]) ==
            sorted(actual_table, key=lambda value: value["teacher_record_sha256"]),
            "perrecord support audit differs from original blind receipts")
    selected_by_split = {split: sum(record["split"] == split for record in records.values()) for split in ("train", "dev")}
    supported_records = [records[digest] for digest in actual_supported]
    supported_count = lambda predicate: {split: sum(record["split"] == split and predicate(record)
        for record in supported_records) for split in ("train", "dev")}
    expected_counts = dict(selected_denominator=len(expected), selected_by_split=selected_by_split,
        support_class_counts=dict(Counter(classification.values())), supported_by_split=supported_count(lambda record: True),
        supported_positive_by_split=supported_count(lambda record: not record["explicit_no_highlight"]),
        supported_explicit_empty_by_split=supported_count(lambda record: record["explicit_no_highlight"]),
        unknown_count=sum(value == "UNKNOWN" for value in classification.values()),
        boundary_supported_count=sum(value["boundary_supported"] for value in actual_table))
    for key, value in expected_counts.items():
        require(review.get(key) == value, "semantic denominator/class count differs: " + key)
    return raw_path, actual_supported, dict(**expected_counts, original_eligible_records=len(eligible_expected),
        supported_records=len(actual_supported), excluded_records=len(expected - actual_supported),
        perrecord_classification=classification,
        all_original_denominators_and_bytes_bound=True,
        teacher_consistency_is_weak_evidence_not_human_truth=True)


def owns(path, run):
    """All student stages must stay under this independent version, not v1."""
    return Path(run).resolve() / Path(__file__).resolve().parent.name in Path(path).resolve().parents


def admit(args):
    run = Path(args.run_dir).resolve(strict=True)
    labels = Path(args.labels_dir).resolve(strict=True)
    out = Path(args.out_dir).resolve()
    require(owns(out, run) and not out.exists(), "fresh owned output directory required")
    config_path = Path(args.config).resolve(strict=True)
    config = read(config_path)
    require(config.get("schema") == "aic_t_student_config_v1" and config.get("authorized") is True and
            config.get("formal_C_BCE_admitted") is False and config.get("official_upload_authorized") is False,
            "student execution authority/scope missing")
    require(config.get("input_contract") == INPUT_CONTRACT, "T train/dev/production input contract differs")
    opt = config["optimization"]
    expected = {"lr": 1e-5, "optimizer": "AdamW", "betas": [0.9, 0.999], "eps": 1e-8,
                "weight_decay": 0.0, "grad_clip_norm": 1.0, "effective_batch_windows": 16,
                "microbatch_windows": 1, "gradient_accumulation_steps": 16, "max_epochs": 3,
                "prefix_update_limit": opt.get("prefix_update_limit"), "seed": 20261007, "precision": "bf16", "attn_implementation": "sdpa",
                "gradient_checkpointing_use_reentrant": False}
    require(opt == expected, "frozen student optimization recipe changed")
    require(type(opt["prefix_update_limit"]) is int and 2 <= opt["prefix_update_limit"] <= 4,
            "early prefix update limit must be 2..4")
    require(config.get("dev_stop_rule") == {"all_selected_fraction": 0.99, "widespread_degraded_group_fraction": 0.75,
                "widespread_macro_f1_drop": 0.05}, "undeclared developer stop rule")
    lock_path = bound(config["source_lock"])
    lock = read(lock_path)
    files = lock.get("files", {})
    require(files and isinstance(files, dict), "source lock files missing")
    def locked(path):
        absolute = str(Path(path).resolve(strict=True))
        require(absolute in files and sha(absolute) == files[absolute], "source helper outside dynamic source lock: " + absolute)
    for relative in REQUIRED_HELPERS:
        locked(run / relative)
    locked(__file__)
    for path, digest in files.items():
        require(sha(path) == digest, "source lock changed: " + path)
    helper_paths(run)
    import sft_contract as old
    validation_path = bound(config["data"]["validation_receipt"])
    require(validation_path == labels / "validation_receipt.json", "labels directory/validation reference differs")
    validation = read(validation_path)
    require(validation.get("schema") == "aic_complete_window_validation_receipt_v1" and
            validation.get("weak_teacher_only") is True and validation.get("confirm_opened") is False and
            validation.get("contest_assets_opened") is False and validation.get("unlabelled_windows_never_converted_to_empty") is True,
            "non-test weak supervision validation required")
    hashes = {name: sha(labels / name) for name in ("eligible_train.jsonl", "eligible_dev.jsonl", "validated_records.jsonl")}
    require(validation.get("files") == hashes, "eligible/raw validated supervision bytes changed")
    eligible = {split: rows(labels / ("eligible_" + split + ".jsonl")) for split in ("train", "dev")}
    validate_isolation(eligible["train"], eligible["dev"])
    approved_paths = {}
    for split in ("train", "dev"):
        ref = config["data"]["approved_" + split + "_manifest"]
        require(ref["sha256"] == APPROVED_MANIFEST_SHA[split], "original approved split registry changed")
        path = bound(ref); approved_paths[split] = path
        validate_lineage(eligible[split], rows(path), split)
    verifier = load(HERE / "teacher_label.py", "t_registered_teacher_label")
    require(Path(verifier.__file__).resolve() == HERE / "teacher_label.py", "teacher protocol verifier identity differs")
    require(Path(verifier.boundary.__file__).resolve() == HERE / "boundary_ids.py", "native boundary protocol identity differs")
    validator = verifier.validator_for(run)
    actual_records = rows(labels / "validated_records.jsonl")
    records = {record_sha(r): r for r in actual_records}
    require(len(records) == len(actual_records) == validation.get("record_count") and
            len({record["window_id"] for record in actual_records}) == len(actual_records), "duplicate/missing validated record")
    require({split: sum(record["split"] == split for record in actual_records) for split in ("train", "dev")} ==
            {"train": 128, "dev": 32}, "original full-window collection denominator changed")
    original_by_split = {split: [dict(window=record["window"]) for record in actual_records if record["split"] == split]
                         for split in ("train", "dev")}
    validate_isolation(original_by_split["train"], original_by_split["dev"])
    for split, targets in original_by_split.items():
        validate_lineage(targets, rows(approved_paths[split]), split)
    sources = {}
    for original in actual_records:
        require(original.get("status") in ("PASS_WEAK_COMPLETE_WINDOW_TARGET", "EXCLUDED_UNCERTAIN_NOT_AN_EMPTY_TARGET",
                "EXCLUDED_UNREPRESENTABLE_SEGMENT_COUNT") and original.get("label_status") == "WEAK_TEACHER_NOT_MANUAL_GROUND_TRUTH",
                "original collection contains engineering-invalid or foreign teacher record")
        w, obs = original["window"], original["actual_observation"]
        validator.validate_window(w); validator.validate_observation(w, obs)
        verifier.verify_model_decision_projection(original)
        # Exact legacy first-record identity already passed its original validator.
        if not verifier.approved_legacy_record(original):
            validator.validate_teacher(original["teacher"], validator.prompt_for(w, obs))
        response = validator.strict_json(original["raw_answer"])
        validator.validate_response(w, obs, response)
        require(response == original["parsed_answer"] and original["split"] == w["split"] and
                original["window_id"] == w["window_id"] and original["source_group"] == w["source_group"],
                "original complete collection canonical projection or identity differs")
        source = Path(w["source_path"]).resolve(strict=True)
        media_root = Path("/home/inspur/aic_video_data/videos").resolve(strict=True)
        require(media_root in source.parents and source.is_file(), "original source escapes approved media root")
        require(str(source) not in sources or sources[str(source)] == w["source_sha256"], "inconsistent original media SHA")
        sources[str(source)] = w["source_sha256"]
    for split, targets in eligible.items():
        for target in targets:
            require(target.get("schema") == "aic_complete_window_sft_target_v1", "foreign target schema")
            original = records.get(target.get("teacher_record_sha256"))
            require(original is not None and original.get("status") == "PASS_WEAK_COMPLETE_WINDOW_TARGET" and
                    original.get("sft_eligible") is True and original.get("uncertain") is False and
                    original.get("label_status") == "WEAK_TEACHER_NOT_MANUAL_GROUND_TRUTH", "target lacks eligible actual teacher record")
            require(original["window"] == target["window"] and original["target_json"] == target["target_json"] and
                    original["explicit_no_highlight"] == target["explicit_no_highlight"], "target projection differs from reviewed teacher")
            w, obs = original["window"], original["actual_observation"]
            verifier.verify_model_decision_projection(original)
            validator.validate_window(w); validator.validate_observation(w, obs)
            # Exact legacy first-record identity already passed its original validator.
            if not verifier.approved_legacy_record(original):
                validator.validate_teacher(original["teacher"], validator.prompt_for(w, obs))
            response = validator.strict_json(original["raw_answer"])
            validator.validate_response(w, obs, response)
            require(response == original["parsed_answer"] and original["split"] == split, "raw response differs from validator projection")
            from contracts import answer_string
            parsed = json.loads(target["target_json"])["segments"]
            require(parsed == [[s["start_sec"], s["end_sec"]] for s in response["retained_segments"]] and
                    target["explicit_no_highlight"] == response["explicit_no_highlight"],
                    "raw teacher answer/interval-only target projection differs")
            answer_string(parsed, w["window_duration_sec"], allow_empty=True)
            source = Path(w["source_path"]).resolve(strict=True)
            media_root = Path("/home/inspur/aic_video_data/videos").resolve(strict=True)
            require(media_root in source.parents and source.is_file(), "resolved source escapes approved media root")
            digest = w["source_sha256"]
            require(str(source) not in sources or sources[str(source)] == digest, "inconsistent media SHA")
            sources[str(source)] = digest
    eligible_digests = {target["teacher_record_sha256"] for targets in eligible.values() for target in targets}
    original_strict_eligible = {digest for digest, original in records.items() if original["sft_eligible"] is True}
    require(eligible_digests == original_strict_eligible and validation.get("eligible_count") == len(eligible_digests) and
            validation.get("eligible_by_split") == {split: len(targets) for split, targets in eligible.items()},
            "original strict eligible denominator or projection was reduced before blind review")
    review_path = bound(config["data"]["semantic_review_receipt"])
    raw_review_path, supported, semantic_admission = verify_semantic(read(review_path), sha(validation_path), hashes,
                                     eligible["train"] + eligible["dev"], records, verifier, validator)
    original_eligible_by_split = {split: len(targets) for split, targets in eligible.items()}
    eligible = {split: [target for target in targets if target["teacher_record_sha256"] in supported]
                for split, targets in eligible.items()}
    validate_isolation(eligible["train"], eligible["dev"])
    semantic_admission.update(original_eligible_by_split=original_eligible_by_split,
        supported_by_split={split: len(targets) for split, targets in eligible.items()})
    model = config["model"]
    require(model.get("base_id") == "Qwen/Qwen3-VL-8B-Instruct" and model.get("base_revision") == REVISION and
            Path(model["base_model_dir"]).resolve() == run / "models/Qwen3-VL-8B-Instruct" and
            Path(model["initial_adapter_dir"]).resolve() == run / "temporal_sft8b_full_v1/train_01/adapter" and
            model.get("initial_adapter_model_sha256") == INITIAL_SHA and model.get("lora_rank") == 16 and
            model.get("lora_alpha") == 32 and model.get("lora_dropout") == .05,
            "pinned B continuation identity changed")
    initial = Path(model["initial_adapter_dir"])
    require(sha(initial / "adapter_model.safetensors") == INITIAL_SHA and
            sha(initial / "adapter_config.json") == model["initial_adapter_config_sha256"], "B adapter bytes changed")
    initial_recipe = read(initial / "adapter_config.json")
    require(initial_recipe["r"] == 16 and initial_recipe["lora_alpha"] == 32 and initial_recipe["lora_dropout"] == .05 and
            initial_recipe["bias"] == "none" and initial_recipe["modules_to_save"] is None, "initial B LoRA recipe changed")
    model_receipt = bound(model["model_receipt"])
    old.verify_model_receipt(Path(model["base_model_dir"]), read(model_receipt))
    classes = supervision_classes(eligible["train"])
    batches = schedule(len(eligible["train"]), epochs=opt["max_epochs"],
                       batch=opt["effective_batch_windows"], seed=opt["seed"])
    prefix_updates = prefix_update_count(batches, opt["prefix_update_limit"])
    for path, digest in sources.items():
        require(sha(path) == digest, "source video changed: " + path)
        st = Path(path).stat()
        _VERIFIED_SOURCE_STATS[path] = (digest, st.st_size, st.st_mtime_ns)
    authorities = {str(p): sha(p) for p in (config_path, lock_path, validation_path, review_path, raw_review_path, model_receipt)}
    authorities.update({str(p): sha(p) for p in approved_paths.values()})
    authorities.update({str(initial / name): sha(initial / name) for name in ("adapter_model.safetensors", "adapter_config.json")})
    authorities.update({str(labels / name): digest for name, digest in hashes.items()})
    return dict(run=run, out=out, config=config, config_path=config_path, files=files, authorities=authorities,
                targets=eligible, records=records, sources=sources, batches=batches,
                prefix_update_count=prefix_updates, supervision_classes=classes,
                semantic_admission=semantic_admission)


def decode_window(window, observation=None):
    """Public sequential T decoder, with optional teacher-observation equality.

    Return (numpy THWC RGB, video_metadata, exact_native_pts_plan, evidence).
    This function also handles contest windows when called by the separately
    admitted production job; training never manufactures such a window.
    """
    import av
    import numpy as np
    w = window
    ids, pts = w["planned_source_frame_ordinals"], w["planned_actual_pts_sec"]
    require(ids and len(ids) == len(pts) <= 64 and ids == sorted(set(ids)) and
            all(type(i) is int and i >= 0 for i in ids) and all(math.isfinite(t) for t in pts), "invalid T frame/PTS plan")
    if "eligible_source_frame_count" in w:
        require(ids == floor_indices(ids[0], ids[0] + w["eligible_source_frame_count"]), "T sampling is not registered integer-floor rule")
    before = Path(w["source_path"]).stat()
    key = str(Path(w["source_path"]).resolve(strict=True))
    signature = (w["source_sha256"], before.st_size, before.st_mtime_ns)
    if _VERIFIED_SOURCE_STATS.get(key) != signature:
        require(sha(w["source_path"]) == w["source_sha256"], "T source byte identity changed")
        _VERIFIED_SOURCE_STATS[key] = signature
    frames, actual_pts, pixels, window_source_pts = [], [], [], []
    with av.open(w["source_path"]) as container:
        require(len(container.streams.video) == 1, "ambiguous source video stream")
        stream = container.streams.video[0]
        rate = stream.average_rate
        require(rate is not None and float(rate) > 0, "actual source FPS unavailable")
        if observation is not None:
            require(observation["fps_num"] == rate.numerator and observation["fps_den"] == rate.denominator,
                    "student/teacher source average FPS metadata differs")
        wanted = iter(ids); current = next(wanted, None)
        for ordinal, frame in enumerate(container.decode(stream)):
            if current is None:
                break
            if ids[0] <= ordinal <= ids[-1]:
                require(frame.pts is not None and frame.time_base is not None, "actual unsampled source frame PTS missing")
                window_source_pts.append(float(frame.pts * frame.time_base))
            if ordinal != current:
                continue
            require(frame.pts is not None and frame.time_base is not None, "actual source frame PTS missing")
            point = float(frame.pts * frame.time_base)
            require(abs(point - pts[len(frames)]) <= 1e-6, "actual decoded ordinal PTS differs from teacher observation")
            color_path = HERE / "source_color.py"
            color = sys.modules.get("t_registered_source_color")
            if color is None or Path(color.__file__).resolve() != color_path.resolve():
                color = load(color_path, "t_registered_source_color")
            require(Path(color.__file__).resolve() == color_path.resolve(), "source color helper identity differs")
            image = color.convert_frame(frame, w["source_sha256"], "rgb24")
            require(image.ndim == 3 and image.shape[-1] == 3, "source RGB geometry changed")
            if "height" in w and "width" in w:
                require(image.shape[:2] == (w["height"], w["width"]), "registered source geometry changed")
            digest = hashlib.sha256(image.tobytes(order="C")).hexdigest()
            if observation is not None:
                require(digest == observation["frame_pixel_sha256"][len(frames)], "student/teacher frame pixel SHA differs")
            frames.append(image); actual_pts.append(point); pixels.append(digest)
            current = next(wanted, None)
    after = Path(w["source_path"]).stat()
    require(len(frames) == len(ids) and (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns),
            "source changed or a planned frame was not decoded")
    arr = np.stack(frames)
    plan = dict(source_frame_ids=ids, source_relative_pts=actual_pts, window_start=w["window_pts_start_sec"])
    total = observation["source_total_frames"] if observation is not None else w.get("source_total_frames", w.get("n_frames"))
    require(type(total) is int and total > ids[-1], "actual full-source frame count must be declared")
    metadata = dict(fps=float(rate), frames_indices=ids, total_num_frames=total, video_backend="pyav")
    from native_frames import prepare_native_processor_input
    arr, metadata = prepare_native_processor_input(arr, metadata, plan)
    return arr, metadata, plan, dict(window_id=w["window_id"], source_sha256=w["source_sha256"],
        source_frame_ids=ids, actual_pts_sec=actual_pts, frame_pixel_sha256=pixels,
        window_source_pts_sec=window_source_pts,
        native_source_clock=True, explicit_lone_frame_copy=len(ids) == 1,
        teacher_pixel_identity_checked=observation is not None, source_fps_num=rate.numerator, source_fps_den=rate.denominator)


def decode_observed(target, record, np=None):
    return decode_window(target["window"], record["actual_observation"])


def production_encode(processor, window, observation=None):
    """Public T encode shared by fixed dev and full contest T inference."""
    import torch
    from engine import prompt_for
    from video_contract import encode, identity
    from exact_pts import exact_native_pts, verify_native_encoding
    arr, metadata, plan, decoded = decode_window(window, observation)
    with exact_native_pts(processor, plan, metadata["fps"]) as native:
        encoded = encode(processor, text=[prompt_for(processor, True)],
            videos=[torch.from_numpy(arr).permute(0, 3, 1, 2)], video_metadata=[metadata],
            video_size=VIDEO_SIZE, max_input=16384)
        verify_native_encoding(processor, encoded, native)
    return encoded, dict(**decoded, native_processor_identity=native, **identity(processor, encoded, len(arr)))


def production_generate(model, processor, window, encoded, details, candidates=None):
    from engine import generate_window
    from constrained_json import ascii_token_candidates
    if candidates is None:
        candidates = ascii_token_candidates(processor.tokenizer)
    # Output remains window-local; the controller adds source-global start for packaging.
    result = generate_window(model, processor, encoded, details, 0, window["window_duration_sec"], candidates, True)
    if result["output_valid"]:
        from native_segment_contract import native_segment_ranges
        try:
            ranges = native_segment_ranges(result["parsed_segments"], details["window_source_pts_sec"],
                window["window_pts_start_sec"], window["window_duration_sec"])
            result["native_frame_realizability"] = {"status":"PASS_ACTUAL_SOURCE_FRAME_REALIZABILITY", "ranges":ranges,
                "not_limited_to_64_teacher_samples":True}
        except (ValueError, KeyError) as error:
            result.update(status="PARSE_FAILURE", output_valid=False,
                rejected_parsed_segments=result["parsed_segments"], parsed_segments=None,
                parse_errors=["SOURCE_FRAME_CONTRACT: " + str(error)],
                native_frame_realizability={"status":"STOP_NO_ACTUAL_SOURCE_FRAME", "failure_converted_to_empty":False})
    return result


def encode_example(processor, target, record, torch, np):
    from training_target import build_target, from_teacher_record
    from engine import prompt_for
    from video_contract import identity
    arr, metadata, plan, decoded = decode_observed(target, record, np)
    video = torch.from_numpy(arr).permute(0, 3, 1, 2)
    encoded, mask = build_target(processor, prompt_for(processor, True), video, metadata,
        from_teacher_record(record), target["window"]["window_duration_sec"], VIDEO_SIZE,
        max_input=16384, native_plan=plan, source_fps=metadata["fps"])
    return encoded, dict(**decoded, assistant_mask=mask, input_identity=identity(processor, encoded, len(arr)))


def encode_dev(processor, target, record, torch, np):
    return production_encode(processor, target["window"], record["actual_observation"])


def union(segments):
    result = []
    for start, end in sorted(segments):
        if not result or start > result[-1][1]:
            result.append([start, end])
        else:
            result[-1][1] = max(end, result[-1][1])
    return result


def temporal_stats(pred, truth):
    p, g = union(pred), union(truth)
    ps, gs = sum(b - a for a, b in p), sum(b - a for a, b in g)
    overlap = sum(max(0, min(b, d) - max(a, c)) for a, b in p for c, d in g)
    return dict(f1=2 * overlap / (ps + gs) if ps + gs else 1.0,
        precision=overlap / ps if ps else float(gs == 0), recall=overlap / gs if gs else float(ps == 0),
        pred_seconds=ps, truth_seconds=gs, intersection_seconds=overlap)


def bootstrap(values, seed=20261007, draws=10000):
    rng = random.Random(seed)
    sims = sorted(statistics.mean(rng.choice(values) for _ in values) for _ in range(draws))
    return [sims[int(.025 * draws)], sims[int(.975 * draws)]]


def prefix_resume_position(batches, completed_update, report):
    """Persist work pending *after* the optimizer update, including epoch dev."""
    require(0 < completed_update <= len(batches), "invalid prefix data position")
    batch = batches[completed_update - 1]
    next_batch = batches[completed_update] if completed_update < len(batches) else None
    return dict(completed_update=completed_update, next_schedule_index=completed_update,
        completed_epoch_checkpoints=copy.deepcopy(report.get("checkpoints", [])),
        completed_epoch_devmetrics=copy.deepcopy(report.get("devmetrics", [])),
        current_epoch=batch["epoch"], current_epoch_last_batch=bool(batch["epoch_last"]),
        pending_phase="EPOCH_END_CHECKPOINT_AND_DEV_PENDING" if batch["epoch_last"] else "NEXT_TRAIN_BATCH",
        pending_epoch_end=batch["epoch"] if batch["epoch_last"] else None,
        next_epoch=next_batch["epoch"] if next_batch else None,
        report_snapshot=copy.deepcopy(report), entire_schedule=copy.deepcopy(batches))


def rng_snapshot(torch, np, *, cuda=True):
    return dict(python_rng=random.getstate(), numpy_rng=np.random.get_state(),
        torch_rng=torch.get_rng_state(), cuda_rng=torch.cuda.get_rng_state_all() if cuda else [])


def assert_tree_equal(expected, actual, torch, np, location="state"):
    """Compare real checkpoint tensor bytes/dtypes and Python/NumPy metadata."""
    if isinstance(expected, torch.Tensor):
        require(isinstance(actual, torch.Tensor) and expected.dtype == actual.dtype and
                expected.shape == actual.shape and torch.equal(expected.detach().cpu(), actual.detach().cpu()),
                "checkpoint tensor roundtrip mismatch: " + location)
    elif isinstance(expected, np.ndarray):
        require(isinstance(actual, np.ndarray) and expected.dtype == actual.dtype and
                expected.shape == actual.shape and np.array_equal(expected, actual),
                "checkpoint NumPy roundtrip mismatch: " + location)
    elif isinstance(expected, dict):
        require(isinstance(actual, dict) and set(expected) == set(actual), "checkpoint mapping mismatch: " + location)
        for key in expected:
            assert_tree_equal(expected[key], actual[key], torch, np, location + "/" + str(key))
    elif isinstance(expected, (list, tuple)):
        require(type(expected) is type(actual) and len(expected) == len(actual), "checkpoint sequence mismatch: " + location)
        for index, (left, right) in enumerate(zip(expected, actual)):
            assert_tree_equal(left, right, torch, np, location + "/" + str(index))
    else:
        require(type(expected) is type(actual) and expected == actual, "checkpoint scalar mismatch: " + location)


def trusted_state_roundtrip(path, expected, optimizer, trainable, torch, np, *, cuda=True):
    """Read this job's just-written state without replacing active objects/RNG."""
    before_rng = rng_snapshot(torch, np, cuda=cuda)
    assert_tree_equal({key: expected[key] for key in before_rng}, before_rng, torch, np, "saved_current_rng")
    optimizer_identity = id(optimizer)
    parameter_ids = [id(p) for _, p in trainable]
    # It contains Python/NumPy RNG structures; only this SHA-bound own file is
    # trusted. Loading it on CPU avoids a second CUDA optimizer allocation.
    loaded = torch.load(path, map_location="cpu", weights_only=False)
    assert_tree_equal(expected, loaded, torch, np)
    assert_tree_equal(loaded["optimizer"], optimizer.state_dict(), torch, np, "active_optimizer")
    current = {name: p.detach().cpu() for name, p in trainable}
    assert_tree_equal(loaded["lora"], current, torch, np, "active_lora")
    assert_tree_equal(before_rng, rng_snapshot(torch, np, cuda=cuda), torch, np, "unchanged_active_rng")
    require(id(optimizer) == optimizer_identity and [id(p) for _, p in trainable] == parameter_ids,
            "prefix validation replaced active optimizer/parameters")
    return dict(status="PASS_TRUSTED_PREFIX_STATE_ROUNDTRIP", state_sha256=sha(path),
        optimizer_tensor_metadata_and_bytes_equal=True, lora_tensor_metadata_and_bytes_equal=True,
        python_numpy_torch_cuda_rng_equal=True, schedule_and_pending_epoch_state_equal=True,
        active_optimizer_reference_unchanged=True, active_parameter_references_unchanged=True,
        active_rng_unchanged=True, cuda_rng_checked=cuda, loaded_on="cpu", optimizer_updates_performed=0)


def prefix_cpu_reload(args):
    """Independent CPU process; cannot alter the active CUDA model/RNG."""
    run = Path(args.run_dir).resolve(strict=True)
    helper_paths(run)
    adapter = Path(args.prefix_adapter).resolve(strict=True)
    require(owns(adapter, run), "prefix adapter outside owned run")
    config = read(args.config)
    bound(config["source_lock"])
    for path, digest in read(config["source_lock"]["path"])["files"].items():
        require(sha(path) == digest, "prefix CPU reload source changed")
    require(sha(adapter / "adapter_model.safetensors") == args.expected_adapter_sha and
            sha(adapter / "adapter_config.json") == args.expected_adapter_config_sha, "prefix adapter changed before CPU reload")
    import torch
    from transformers import Qwen3VLForConditionalGeneration
    from peft import PeftModel
    from train_sft import unique_parameters
    from verify_saved_smoke import canonical_frozen_hash
    from safetensors.torch import load_file
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == "", "independent adapter reload must be CPU-only")
    base = Qwen3VLForConditionalGeneration.from_pretrained(config["model"]["base_model_dir"], revision=REVISION,
        local_files_only=True, torch_dtype=torch.bfloat16, device_map={"": "cpu"},
        low_cpu_mem_usage=True, attn_implementation="sdpa")
    for parameter in base.parameters():
        parameter.requires_grad_(False)
    model = PeftModel.from_pretrained(base, adapter, is_trainable=False)
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    inventory = sum(p.numel() for _, p in unique_parameters(model))
    require(inventory == 8782459120, "independent prefix model parameter inventory differs")
    targets = {name.removeprefix("base_model.model.") for name, module in model.named_modules()
               if hasattr(module, "lora_A") and "default" in module.lora_A}
    expected_targets = {f"model.language_model.layers.{i}.self_attn.{proj}" for i in range(36)
                        for proj in ("q_proj", "k_proj", "v_proj", "o_proj")}
    require(targets == expected_targets, "independent prefix LoRA target modules differ")
    saved = load_file(str(adapter / "adapter_model.safetensors"))
    actual = {name.replace(".default.", "."): p.detach().cpu() for name, p in unique_parameters(model) if "lora_" in name}
    require(len(actual) == 288 and set(actual) == set(saved) and all(
        actual[name].dtype == saved[name].dtype and torch.equal(actual[name], saved[name]) for name in actual),
        "independent prefix reload tensor bytes differ")
    frozen = canonical_frozen_hash(model, torch)
    with model.disable_adapter():
        adapter_off = canonical_frozen_hash(model, torch)
    require(frozen == adapter_off and frozen["sha256"] == args.expected_base_sha,
            "independent prefix CPU reload frozen base/vision differs")
    write(args.verification_report, dict(status="PASS_INDEPENDENT_PREFIX_ADAPTER_CPU_RELOAD",
        adapter_dir=str(adapter), adapter_model_sha256=args.expected_adapter_sha,
        adapter_config_sha256=args.expected_adapter_config_sha, logical_parameters=inventory,
        language_target_modules=len(targets), lora_tensors=len(actual), base_frozen=frozen, adapter_off=adapter_off,
        optimizer_updates=0, device="cpu", active_training_objects_accessed=False,
        checked_utc=dt.datetime.now(dt.timezone.utc).isoformat()))
    return 0


def verify_prefix_adapter_in_child(contract, adapter, model, trainable, frozen, torch, np):
    import psutil
    from train_sft import unique_parameters
    frozen_bytes = sum(p.numel() * p.element_size() for name, p in unique_parameters(model) if "lora_" not in name)
    lora_bytes = sum(p.numel() * p.element_size() for _, p in trainable)
    # Fresh CPU base plus PEFT/saved/actual adapter buffers. This estimate is
    # computed from actual tensors, never a fixed RAM quota or admission line.
    estimated_additional_bytes = frozen_bytes + 4 * lora_bytes
    available = psutil.virtual_memory().available
    require(available >= estimated_additional_bytes, "STOP_T_PREFIX_RELOAD_ACTUAL_RAM_CAPACITY_INSUFFICIENT")
    before_rng = rng_snapshot(torch, np)
    optimizer_parameters = [id(p) for _, p in trainable]
    result_path = contract["out"] / "prefix_adapter_reload.json"
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES="", PYTHONDONTWRITEBYTECODE="1")
    command = [sys.executable, "-B", str(Path(__file__).resolve()), "verify-prefix-adapter",
        "--run-dir", str(contract["run"]), "--config", str(contract["config_path"]),
        "--prefix-adapter", str(adapter), "--expected-adapter-sha", sha(adapter / "adapter_model.safetensors"),
        "--expected-adapter-config-sha", sha(adapter / "adapter_config.json"),
        "--expected-base-sha", frozen["sha256"], "--verification-report", str(result_path)]
    with (contract["out"] / "prefix_adapter_reload.log").open("x", encoding="utf-8") as log:
        subprocess.run(command, env=environment, stdout=log, stderr=subprocess.STDOUT, check=True)
    result = read(result_path)
    require(result.get("status") == "PASS_INDEPENDENT_PREFIX_ADAPTER_CPU_RELOAD", "prefix CPU reload did not pass")
    assert_tree_equal(before_rng, rng_snapshot(torch, np), torch, np, "post_child_active_rng")
    require(optimizer_parameters == [id(p) for _, p in trainable], "CPU child replaced active training parameters")
    result.update(actual_ram_available_bytes=available, estimated_additional_cpu_bytes=estimated_additional_bytes,
        active_rng_unchanged=True, active_parameter_references_unchanged=True,
        verification_process="INDEPENDENT_CPU_SUBPROCESS_NO_ACTIVE_MODEL_MUTATION")
    write(result_path, result)
    return result


def dev_failure(summary, baseline, rule):
    if summary["legal_empty_windows"] == summary["windows"] and summary.get("reference_positive_windows", 1):
        return "STOP_T_SYSTEMATIC_ALL_EMPTY_DEV"
    if summary["all_selected_windows"] == summary["windows"]:
        return "STOP_T_SYSTEMATIC_ALL_SELECTED_DEV"
    if baseline is not None:
        groups = summary["group_f1"]
        fraction = sum(groups[g] < baseline["group_f1"][g] for g in groups) / len(groups)
        if fraction >= rule["widespread_degraded_group_fraction"] and baseline["video_macro_f1"] - summary["video_macro_f1"] >= rule["widespread_macro_f1_drop"]:
            return "STOP_T_WIDESPREAD_OPEN_DEV_DEGRADATION"
    return None


def evaluate(model, processor, contract, out, name, torch, np):
    from constrained_json import ascii_token_candidates
    model.eval(); model.config.use_cache = True
    candidates = ascii_token_candidates(processor.tokenizer)
    values = []
    started = time.monotonic()
    with (out / (name + ".jsonl")).open("x", encoding="utf-8") as stream:
        for target in contract["targets"]["dev"]:
            w = target["window"]; record = contract["records"][target["teacher_record_sha256"]]
            encoded, details = encode_dev(processor, target, record, torch, np)
            result = production_generate(model, processor, w, encoded, details, candidates)
            # A parse/inference failure blocks this run; it never receives an [] score.
            stream.write(json.dumps(dict(window_id=w["window_id"], result=result), ensure_ascii=False) + "\n"); stream.flush()
            require(result["output_valid"], "STOP_T_DEV_PARSE_OR_INFERENCE_FAILURE")
            values.append(dict(window_id=w["window_id"], youtube_id=w["youtube_id"], source_path=w["source_path"],
                duration=w["window_duration_sec"], pred=result["parsed_segments"],
                truth=json.loads(target["target_json"])["segments"], status=result["status"]))
            del encoded
    videos = {}
    for value in values:
        video = videos.setdefault(value["source_path"], dict(youtube_id=value["youtube_id"], pred=[], truth=[], duration=0))
        # Each selected source has one natural window. Fail if later manifests introduce more without global clocks.
        require(not video["duration"], "multiple windows/video require a separately declared global-time metric")
        video.update(pred=value["pred"], truth=value["truth"], duration=value["duration"])
    scored = [{**v, "metrics": temporal_stats(v["pred"], v["truth"])} for v in videos.values()]
    groups = sorted({v["youtube_id"] for v in scored})
    group_f1 = {g: statistics.mean(v["metrics"]["f1"] for v in scored if v["youtube_id"] == g) for g in groups}
    result = dict(name=name, windows=len(values), videos=len(scored), groups=len(groups), group_f1=group_f1,
        video_macro_f1=statistics.mean(v["metrics"]["f1"] for v in scored), group_bootstrap_ci95=bootstrap(list(group_f1.values())),
        parse_failures=0, inference_failures=0, legal_empty_windows=sum(not v["pred"] for v in values),
        reference_positive_windows=sum(bool(v["truth"]) for v in values),
        reference_explicit_no_highlight_windows=sum(not v["truth"] for v in values),
        all_selected_windows=sum(temporal_stats(v["pred"], v["truth"])["pred_seconds"] / v["duration"] >= .99 for v in values),
        local_metric_role="SAME_TEACHER_BLIND_AGREEMENT_WEAK_COMPLETE_WINDOW_SELECTION_NOT_HUMAN_TRUTH_OR_OFFICIAL_SCORE",
        confirm_opened=False, contest_assets_opened=False, seconds=time.monotonic() - started,
        same_input_contract=INPUT_CONTRACT, production_generation_function=VERSION + ".train_student.production_generate",
        independent_quality_reference_available=False)
    write(out / (name + ".metrics.json"), result)
    model.config.use_cache = False; model.train()
    for module_name, module in model.named_modules():
        if module_name.endswith(".visual"):
            module.eval()
    return result


def execute(contract):
    out = contract["out"]; out.mkdir(parents=True)
    config = contract["config"]
    prefix_updates = contract["prefix_update_count"]
    report = dict(status="RUNNING_T_STUDENT", schema="aic_t_student_completion_v2", optimizer_steps=0,
        backward_examples=0, prefix_updates=0, total_planned_updates=len(contract["batches"]),
        prefix_required_updates=prefix_updates, prefix_configured_update_limit=config["optimization"]["prefix_update_limit"],
        config_sha256=sha(contract["config_path"]), quality_claim=False, official_score=None,
        confirm_opened=False, contest_assets_opened=False, formal_C_BCE_admitted=False,
        input_contract=INPUT_CONTRACT, updates=[], devmetrics=[], checkpoints=[], candidates=[],
        supervision_classes=contract["supervision_classes"],
        semantic_admission=contract["semantic_admission"],
        learning_rate_schedule="CONSTANT_1E-5_NO_SCHEDULER_OR_RESTART",
        teacher_truth_status="SAME_32B_BLIND_SELECTION_AGREEMENT_WEAK_ONLY_NOT_HUMAN_GROUND_TRUTH")
    started = time.monotonic(); write(out / "progress.json", report)
    try:
        import sft_contract as old
        old.verify_live_gpu_reservation()
        import numpy as np
        import torch
        import transformers
        import peft
        from peft import PeftModel
        from transformers import AutoProcessor, Qwen3VLForConditionalGeneration
        from train_sft import unique_parameters, gradient_evidence
        from verify_saved_smoke import canonical_frozen_hash
        require(transformers.__version__ == "4.57.1" and peft.__version__ == "0.17.1" and torch.cuda.is_available(),
                "pinned CUDA training runtime required")
        seed = config["optimization"]["seed"]
        random.seed(seed); np.random.seed(seed); torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)
        base = Qwen3VLForConditionalGeneration.from_pretrained(config["model"]["base_model_dir"], revision=REVISION,
            local_files_only=True, torch_dtype=torch.bfloat16, device_map={"": "cuda:0"},
            low_cpu_mem_usage=True, attn_implementation="sdpa")
        for parameter in base.parameters():
            parameter.requires_grad_(False)
        model = PeftModel.from_pretrained(base, config["model"]["initial_adapter_dir"], is_trainable=True)
        trainable = [(name, p) for name, p in unique_parameters(model) if p.requires_grad]
        old.validate_trainable_names([name for name, _ in trainable])
        require(len(trainable) == 288 and sum(p.numel() for _, p in unique_parameters(model)) == 8782459120,
                "student logical parameter/LoRA inventory differs")
        targets = {name.removeprefix("base_model.model.") for name, module in model.named_modules()
                   if hasattr(module, "lora_A") and "default" in module.lora_A}
        expected_targets = {f"model.language_model.layers.{i}.self_attn.{proj}" for i in range(36)
                            for proj in ("q_proj", "k_proj", "v_proj", "o_proj")}
        require(targets == expected_targets, "student LoRA target inventory changed")
        processor = AutoProcessor.from_pretrained(config["model"]["base_model_dir"], revision=REVISION,
            local_files_only=True, min_pixels=131072, max_pixels=131072)
        require(processor.video_processor.size == VIDEO_SIZE, "legacy-equivalent processor size changed")
        frozen = canonical_frozen_hash(model, torch)
        report["base_frozen_evidence"] = {"before": frozen}
        model.eval(); model.config.use_cache = False
        # Real CE only probes classes which actually exist in admitted data.
        real_ce = {}
        for kind, empty in (("explicit_empty", True), ("positive", False)):
            target = next((t for t in contract["targets"]["train"] if t["explicit_no_highlight"] is empty), None)
            if target is None:
                real_ce[kind] = dict(status="NOT_AVAILABLE_IN_ACCEPTED_SUPERVISION", optimizer_updates=0,
                                     no_synthetic_target_created=True)
                continue
            record = contract["records"][target["teacher_record_sha256"]]
            encoded, evidence = encode_example(processor, target, record, torch, np)
            encoded = {key: value.to("cuda:0") if hasattr(value, "to") else value for key, value in encoded.items()}
            with torch.inference_mode():
                loss = model(**encoded).loss
            require(loss is not None and bool(torch.isfinite(loss)), "real empty/positive assistant CE is missing/nonfinite")
            real_ce[kind] = dict(status="PASS_REAL_ASSISTANT_CE", loss=float(loss), window_id=target["window"]["window_id"],
                teacher_record_sha256=target["teacher_record_sha256"], evidence=evidence, optimizer_updates=0)
            del encoded, loss
        report["real_assistant_ce_acceptance"] = real_ce
        # Input B developer baseline is evaluated once on the same new weak dev before updates.
        baseline = evaluate(model, processor, contract, out, "initial_B_dev", torch, np)
        report["initial_B_dev"] = baseline
        report["candidates"].append(dict(epoch=0, completed_updates=0,
            adapter_dir=config["model"]["initial_adapter_dir"], adapter_model_sha256=INITIAL_SHA,
            adapter_config_sha256=config["model"]["initial_adapter_config_sha256"],
            video_macro_f1=baseline["video_macro_f1"], candidate_role="ORIGINAL_B_37_63_ADAPTER_SAME_NEW_DEV_CONTRACT",
            candidate_eligible=True, rejection_reason=None))
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        optimizer = torch.optim.AdamW([p for _, p in trainable], lr=1e-5, betas=(.9, .999), eps=1e-8, weight_decay=0)
        before_lora = {name: p.detach().cpu().clone() for name, p in trainable}
        torch.cuda.reset_peak_memory_stats()
        with (out / "example_evidence.jsonl").open("x", encoding="utf-8") as evidence_stream:
            # Prefix inspection belongs to this same optimizer/RNG schedule.
            for update, batch in enumerate(contract["batches"], 1):
                optimizer.zero_grad(set_to_none=True); losses = []
                for index in batch["indices"]:
                    target = contract["targets"]["train"][index]
                    record = contract["records"][target["teacher_record_sha256"]]
                    encoded, evidence = encode_example(processor, target, record, torch, np)
                    encoded = {key: value.to("cuda:0") if hasattr(value, "to") else value for key, value in encoded.items()}
                    result = model(**encoded)
                    require(result.loss is not None and bool(torch.isfinite(result.loss)), "missing/nonfinite assistant CE")
                    (result.loss / len(batch["indices"])).backward()
                    loss = float(result.loss.detach().cpu()); losses.append(loss)
                    report["backward_examples"] += 1
                    evidence.update(epoch=batch["epoch"], optimizer_update=update, loss=loss,
                        accumulation_denominator=len(batch["indices"]), teacher_record_sha256=target["teacher_record_sha256"])
                    evidence_stream.write(json.dumps(evidence, ensure_ascii=False) + "\n"); evidence_stream.flush()
                    del result, encoded
                grads = gradient_evidence(trainable, torch, update)
                norm = torch.nn.utils.clip_grad_norm_([p for _, p in trainable], 1)
                require(bool(torch.isfinite(norm)) and float(norm) > 0, "invalid LoRA gradient norm")
                optimizer.step()
                current = {name: p.detach().cpu().clone() for name, p in trainable}
                require(len(current) == 288 and all(bool(torch.isfinite(value).all()) for value in current.values()),
                        "missing/nonfinite student LoRA tensor after optimizer update")
                changed = sum(not torch.equal(current[name], before_lora[name]) for name in current)
                require(changed > 0, "LoRA unchanged after genuine optimizer update")
                before_lora = current
                report["optimizer_steps"] = update
                report["prefix_updates"] = min(update, prefix_updates)
                report["updates"].append(dict(update=update, epoch=batch["epoch"], mean_loss=statistics.mean(losses),
                    windows=len(losses), gradient_norm=float(norm), changed_lora_tensors=changed, gradient_evidence=grads))
                if update == prefix_updates:
                    prefix_frozen = canonical_frozen_hash(model, torch)
                    require(prefix_frozen == frozen, "frozen base/vision changed before early-prefix gate")
                    state_path = out / "prefix_state.pt"
                    prefix_adapter = out / f"prefix_{prefix_updates}" / "adapter"
                    before_save_rng = rng_snapshot(torch, np)
                    model.save_pretrained(prefix_adapter, safe_serialization=True)
                    prefix_recipe = read(prefix_adapter / "adapter_config.json")
                    require(prefix_recipe["r"] == 16 and prefix_recipe["lora_alpha"] == 32 and prefix_recipe["lora_dropout"] == .05 and
                            prefix_recipe["bias"] == "none" and prefix_recipe["modules_to_save"] is None, "prefix adapter scalar recipe changed")
                    assert_tree_equal(before_save_rng, rng_snapshot(torch, np), torch, np, "prefix_adapter_save_rng")
                    state = dict(schema="aic_t_prefix_recovery_state_v3", optimizer=optimizer.state_dict(), lora=current,
                        prefix_required_updates=prefix_updates, learning_rate_schedule=report["learning_rate_schedule"],
                        optimizer_parameter_name_order=[name for name, _ in trainable],
                        data_config_sha256=report["config_sha256"], bound_authorities=contract["authorities"],
                        frozen_base_identity=frozen, prefix_adapter_dir=str(prefix_adapter),
                        prefix_adapter_model_sha256=sha(prefix_adapter / "adapter_model.safetensors"),
                        prefix_adapter_config_sha256=sha(prefix_adapter / "adapter_config.json"),
                        **rng_snapshot(torch, np), **prefix_resume_position(contract["batches"], prefix_updates, report))
                    torch.save(state, state_path)
                    roundtrip = trusted_state_roundtrip(state_path, state, optimizer, trainable, torch, np)
                    independent_reload = verify_prefix_adapter_in_child(contract, prefix_adapter, model, trainable, frozen, torch, np)
                    assert_tree_equal(state["optimizer"], optimizer.state_dict(), torch, np, "optimizer_after_independent_reload")
                    report["prefix_gate"] = dict(status="PASS_SAME_RUN_EARLY_UPDATE_PREFIX", completed_updates=prefix_updates,
                        state_path=str(state_path), state_sha256=sha(state_path), base_frozen=prefix_frozen,
                        same_optimizer_rng_data_position=True, extra_epochs_started=False,
                        state_roundtrip=roundtrip, independent_adapter_reload=independent_reload,
                        pending_phase=state["pending_phase"], pending_epoch_end=state["pending_epoch_end"],
                        completed_epoch_checkpoints=state["completed_epoch_checkpoints"])
                    write(out / "prefix_gate.json", report["prefix_gate"])
                    del state
                if batch["epoch_last"]:
                    epoch = batch["epoch"]
                    checkpoint = out / f"epoch_{epoch}"; model.save_pretrained(checkpoint, safe_serialization=True)
                    saved = read(checkpoint / "adapter_config.json")
                    require(saved["r"] == 16 and saved["lora_alpha"] == 32 and saved["lora_dropout"] == .05 and
                            saved["bias"] == "none" and saved["modules_to_save"] is None, "saved student LoRA recipe changed")
                    metrics = evaluate(model, processor, contract, out, f"epoch_{epoch}_dev", torch, np)
                    checkpoint_record = dict(epoch=epoch, completed_updates=update, adapter_dir=str(checkpoint),
                        adapter_model_sha256=sha(checkpoint / "adapter_model.safetensors"),
                        adapter_config_sha256=sha(checkpoint / "adapter_config.json"), video_macro_f1=metrics["video_macro_f1"])
                    failure = dev_failure(metrics, baseline, config["dev_stop_rule"])
                    checkpoint_record.update(candidate_eligible=failure is None, rejection_reason=failure,
                                             candidate_role="TRAINED_T_EPOCH")
                    report["devmetrics"].append(metrics); report["checkpoints"].append(checkpoint_record)
                    report["candidates"].append(checkpoint_record)
                    if failure is not None:
                        report.setdefault("scientific_dev_stop", dict(reason=failure, detected_update=update,
                            detected_epoch=epoch, prefix_gate_required_before_stop=prefix_updates))
                report["wall_seconds"] = time.monotonic() - started
                write(out / "progress.json", report)
                print(json.dumps(dict(stage="T_TRAINING", updates=update, total=len(contract["batches"]),
                                      backward_examples=report["backward_examples"])), flush=True)
                if report.get("scientific_dev_stop") and update >= prefix_updates:
                    report["scientific_dev_stop"].update(actual_stop_update=update,
                        original_schedule_not_expanded=True, selected_candidates_preserved=True)
                    break
        actual_batches = contract["batches"][:report["optimizer_steps"]]
        require(report["prefix_updates"] == prefix_updates and "prefix_gate" in report and
                report["backward_examples"] == sum(len(batch["indices"]) for batch in actual_batches) and
                len(report["checkpoints"]) == sum(batch["epoch_last"] for batch in actual_batches),
                "incomplete same-run prefix or actual data schedule")
        schedule_complete = report["optimizer_steps"] == len(contract["batches"])
        require(schedule_complete or "scientific_dev_stop" in report, "unexplained partial student schedule")
        final_frozen = canonical_frozen_hash(model, torch)
        require(final_frozen == frozen, "frozen base/vision changed during student training")
        selected = select_checkpoint([candidate for candidate in report["candidates"] if candidate["candidate_eligible"]])
        # Semantic reload uses real saved adapter bytes and module identities.
        trained_selected_path = Path(selected["adapter_dir"])
        del optimizer, before_lora, current, trainable
        plain = model.unload(); del model
        reloaded = PeftModel.from_pretrained(plain, trained_selected_path, is_trainable=False)
        for parameter in reloaded.parameters():
            parameter.requires_grad_(False)
        actual_targets = {name.removeprefix("base_model.model.") for name, module in reloaded.named_modules()
                          if hasattr(module, "lora_A") and "default" in module.lora_A}
        require(actual_targets == expected_targets, "selected adapter reload modules changed")
        from safetensors.torch import load_file
        saved_tensors = load_file(str(trained_selected_path / "adapter_model.safetensors"))
        actual = {name.replace(".default.", "."): p.detach().cpu() for name, p in unique_parameters(reloaded) if "lora_" in name}
        require(len(actual) == 288 and set(actual) == set(saved_tensors) and all(torch.equal(actual[n], saved_tensors[n]) and
                actual[n].dtype == saved_tensors[n].dtype for n in actual), "selected adapter reload tensor bytes differ")
        reload_frozen = canonical_frozen_hash(reloaded, torch)
        with reloaded.disable_adapter():
            adapter_off_frozen = canonical_frozen_hash(reloaded, torch)
        require(reload_frozen == adapter_off_frozen == frozen, "selected reload/adapter-off base bytes changed")
        for path, digest in {**contract["files"], **contract["authorities"], **contract["sources"]}.items():
            require(sha(path) == digest, "bound data/source/authority changed during training: " + path)
        report["base_frozen_evidence"].update(after=final_frozen, selected_reload=reload_frozen, adapter_off=adapter_off_frozen)
        report.update(status="PASS_TRAINED_SELECTED_STUDENT_ADAPTER", selected_adapter_dir=selected["adapter_dir"],
            selected_adapter_sha256=selected["adapter_model_sha256"], selected_adapter_config_sha256=selected["adapter_config_sha256"],
            selected_epoch=selected["epoch"], selected_video_macro_f1=selected["video_macro_f1"],
            selection_rule="MAX_SAME_TEACHER_WEAK_DEV_VIDEO_MACRO_F1_THEN_LOWER_EPOCH_INCLUDING_ORIGINAL_B_ZERO",
            prefix_completed_updates=prefix_updates, registered_schedule_completed=schedule_complete,
            selected_candidate_original_B=selected["epoch"] == 0, trained_candidate_selected=selected["epoch"] > 0,
            selected_new_T_improvement_claim=False,
            total_updates=report["optimizer_steps"], base_frozen=True, vision_frozen=True, adapter_reload_succeeded=True,
            actual_logical_parameters=8782459120, peak_memory_allocated_mib=torch.cuda.max_memory_allocated() / 2**20,
            student_training_completed=True, student_training_completed_under_registered_stop_rule=True,
            T_production_inference_started=False, ZIP_delivered=False)
    except Exception as exc:
        report.update(status="STOP_T_STUDENT", failure_type=type(exc).__name__, failure=str(exc), traceback=traceback.format_exc())
    report.update(wall_seconds=time.monotonic() - started, checked_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    write(out / "student_completion.json", report); write(out / "progress.json", report)
    return 0 if report["status"] == "PASS_TRAINED_SELECTED_STUDENT_ADAPTER" else 4


def main():
    if sys.argv[1:2] == ["verify-prefix-adapter"]:
        parser = argparse.ArgumentParser(description="Independent trusted prefix adapter CPU reload")
        for field in ("run-dir", "config", "prefix-adapter", "expected-adapter-sha", "expected-adapter-config-sha", "expected-base-sha", "verification-report"):
            parser.add_argument("--" + field, required=True)
        return prefix_cpu_reload(parser.parse_args(sys.argv[2:]))
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ("run-dir", "labels-dir", "out-dir", "config"):
        parser.add_argument("--" + field, required=True)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    try:
        contract = admit(args)
    except Exception as exc:
        failure = dict(schema="aic_t_student_completion_v2", status="STOP_T_BEFORE_RUNTIME_IMPORTS",
            failure=type(exc).__name__ + ": " + str(exc), training_started=False, optimizer_steps=0,
            checked_utc=dt.datetime.now(dt.timezone.utc).isoformat())
        # Preserve a concrete failure receipt without overwriting an older run.
        output = Path(args.out_dir).resolve()
        if not args.check_only and owns(output, args.run_dir) and not output.exists():
            output.mkdir(parents=True); write(output / "student_completion.json", failure)
        print(json.dumps(failure), flush=True)
        return 3
    if args.check_only:
        print(json.dumps(dict(status="PASS_T_AUTHORITY_INPUT_AND_WEAK_SEMANTIC_ADMISSION",
            train=len(contract["targets"]["train"]), dev=len(contract["targets"]["dev"]),
            total_updates=len(contract["batches"]), prefix_required_updates=contract["prefix_update_count"],
            supervision_classes=contract["supervision_classes"], training_started=False)), flush=True)
        return 0
    return execute(contract)


if __name__ == "__main__":
    raise SystemExit(main())

```


## 补充原文件全文：reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/teacher_student_autopilot_v14/precision_helpers/contracts.py
字节=8721 SHA256=2077adedce249c077738d5920059393a3ce08654d2d185e704da43fe9a4b242d

```py
"""Stdlib-only next-round prediction contracts; no output repair or inference.

Empty segments are a valid prediction when enabled. This module does not
establish complete-observation supervision and cannot turn UNKNOWN into [].
"""
from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
import json
import math


MODEL_OK = "MODEL_OK"
LEGAL_EMPTY = "LEGAL_EMPTY"
PARSE_FAILURE = "PARSE_FAILURE"
INFERENCE_FAILURE = "INFERENCE_FAILURE"

EMPTY_PROMPT = (
    "You are shown a short video clip. Identify every time interval in the clip that is "
    "worth keeping in a short highlight edit.\n"
    "Times are seconds measured from the START of this clip, where 0 is the clip start.\n"
    'Return ONLY JSON of the form {"segments": [[start_sec, end_sec], ...]} using '
    "clip-local seconds.\n"
    "Rules:\n"
    "- every interval must satisfy 0 <= start_sec < end_sec <= clip duration\n"
    "- return between 0 and 5 intervals\n"
    "- sort them by start time and do not let them overlap\n"
    '- when the clip has no worthwhile highlight, return {"segments": []}\n'
    "- uncertainty or insufficient observation is not evidence of no highlight; "
    "do not use an empty list to represent uncertainty\n"
    "- output nothing except the JSON"
)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key: " + key)
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError("nonfinite JSON constant: " + value)


def _strict_json(raw):
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("empty or non-string model output")
    # Decode the entire document. Fences, prose, multiple objects, duplicate
    # keys and JavaScript NaN/Infinity never become a prediction.
    return json.loads(raw, object_pairs_hook=_unique_object,
                      parse_float=Decimal, parse_constant=_reject_constant)


def parse_focus_norm(text, W=None, H=None):
    """Return the center in [0,1], or None for a strict-contract failure.

    W/H only preserve the old call signature. The declared coordinate unit is
    always an integer in 0..1000 for both axes, independently of image size.
    """
    del W, H
    try:
        obj = _strict_json(text)
    except (TypeError, ValueError, RecursionError):
        return None
    if not isinstance(obj, dict) or set(obj) != {"center"}:
        return None
    center = obj["center"]
    if (not isinstance(center, list) or len(center) != 2 or
            any(type(value) is not int or not 0 <= value <= 1000 for value in center)):
        return None
    return [value / 1000.0 for value in center]


def _duration_fraction(duration):
    if type(duration) is int:
        value = Fraction(duration)
    elif type(duration) is float and math.isfinite(duration):
        value = Fraction(str(duration))
    elif isinstance(duration, Fraction):
        value = duration
    else:
        raise ValueError("duration must be a finite positive number")
    if value <= 0:
        raise ValueError("duration must be a finite positive number")
    return value


def _options(duration, max_segments, allow_empty):
    value = _duration_fraction(duration)
    if type(max_segments) is not int or not 1 <= max_segments <= 5:
        raise ValueError("max_segments must be an integer in 1..5")
    if type(allow_empty) is not bool:
        raise ValueError("allow_empty must be a bool")
    return value


def validate_segments(segments, duration, max_segments=5, allow_empty=True):
    """Validate and return the original list; reject instead of repairing.

    This is only geometry/format validation. An empty *training* target still
    requires separately verified complete-observation, no-highlight evidence.
    """
    end = _options(duration, max_segments, allow_empty)
    if not isinstance(segments, list):
        raise ValueError("segments must be a list")
    if not segments and not allow_empty:
        raise ValueError("empty segments are disabled by this protocol")
    if len(segments) > max_segments:
        raise ValueError("segment count exceeds the protocol maximum")
    previous_end = Fraction(0)
    for index, segment in enumerate(segments):
        if not isinstance(segment, list) or len(segment) != 2:
            raise ValueError(f"segment {index} must be a two-element list")
        if any(type(value) not in (int, float) or
               (type(value) is float and not math.isfinite(value)) for value in segment):
            raise ValueError(f"segment {index} bounds must be finite numbers, not bools")
        start, stop = (Fraction(str(value)) for value in segment)
        if not 0 <= start < stop <= end:
            raise ValueError(f"segment {index} violates 0 <= start < end <= duration")
        if start < previous_end:
            raise ValueError(f"segment {index} is unsorted or overlaps its predecessor")
        previous_end = stop
    return segments


# Old callers used this name for target validation.
segments_valid = validate_segments


def _json_number(value):
    if type(value) is int:
        return value
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValueError("bounds must be JSON numbers, not bools or strings")
    numeric = float(value)
    if not math.isfinite(numeric) or Fraction(str(numeric)) != Fraction(value):
        raise ValueError("JSON bound cannot be represented without numeric precision loss")
    return numeric


def parse_segments(raw, duration, max_segments=5, allow_empty=True):
    """Return (segments|None, errors, warnings) with no repairs or fallback.

    A valid empty result is ([], [], []), whereas a failure is (None, [...], []).
    Original order and endpoints remain binding; excess, invalid, overlapping
    or unsorted segments fail the whole prediction.
    """
    try:
        _options(duration, max_segments, allow_empty)
        obj = _strict_json(raw)
        if not isinstance(obj, dict) or set(obj) != {"segments"}:
            raise ValueError("expected only a JSON object with the key 'segments'")
        if not isinstance(obj["segments"], list):
            raise ValueError("segments must be a list")
        segments = []
        for index, segment in enumerate(obj["segments"]):
            if not isinstance(segment, list) or len(segment) != 2:
                raise ValueError(f"segment {index} must be a two-element list")
            segments.append([_json_number(value) for value in segment])
        validate_segments(segments, duration, max_segments, allow_empty)
        return segments, [], []
    except (TypeError, ValueError, OverflowError, RecursionError) as exc:
        return None, [str(exc)], []


def _canonical_number(value):
    # str(float) is the already validated JSON numeric identity, not a request
    # to round a native PTS. Render that exact finite decimal without exponent.
    decimal = Decimal(str(value))
    if not decimal.is_finite() or max(0, -decimal.as_tuple().exponent) > 18:
        raise ValueError("target endpoint exceeds the registered lossless decimal grammar")
    text = format(decimal, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def answer_string(segments, duration, max_segments=5, allow_empty=True):
    """Serialize a valid target into the generation grammar without rounding."""
    validate_segments(segments, duration, max_segments, allow_empty)
    intervals = ["[" + ",".join(_canonical_number(value) for value in segment) + "]"
                 for segment in segments]
    return '{"segments":[' + ",".join(intervals) + "]}"


def classify_temporal_result(raw, duration, max_segments=5, allow_empty=True,
                             inference_error=None):
    """Keep legal empty, parse failure and failed execution distinct."""
    if inference_error is not None:
        return {"status": INFERENCE_FAILURE, "output_valid": False,
                "parsed_segments": None, "parse_errors": [], "parse_warnings": [],
                "inference_error": str(inference_error)}
    segments, errors, warnings = parse_segments(raw, duration, max_segments, allow_empty)
    status = PARSE_FAILURE if segments is None else LEGAL_EMPTY if not segments else MODEL_OK
    return {"status": status, "output_valid": segments is not None,
            "parsed_segments": segments, "parse_errors": errors, "parse_warnings": warnings,
            "inference_error": None}

```

END_EMPTY407_R01
