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
