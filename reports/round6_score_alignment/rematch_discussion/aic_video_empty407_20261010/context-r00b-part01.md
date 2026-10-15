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
