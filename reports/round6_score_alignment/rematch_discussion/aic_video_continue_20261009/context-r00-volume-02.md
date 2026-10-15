**第三张：成本。**时间推理、空间调用、解码、封包分别计时。不要把每次评估都变成完整空间重推：同一非测试空间场缓存一次，可以比较多个时间 checkpoint；变化了空间模型或算法，才失效重算。

**准入标准：**工程错误必须修；全选、全空或广泛退化停止该版本；弱结果不确定但机制明确，可以登记为风险候选进行官方整包验收。无需为每个候选跑五折，也不要求所有微小改进都先取得置信区间下界大于零。

本轮候选矩阵

保留 B=37.63 不动。其余最多形成以下五个有意义的新候选，不要求同一天全部生产：

候选	内容	为什么值得做
Z	原生 8B 时间＋与 B 相同的生产解码合同和 8B 空间链	排除原开发 BASE 解析失败造成的错误判断
M	已完成训练的 Mac adapter，按它自己的固定输入协议在 Linux 生产	利用已有投入，不再重做一次 MPS 训练
T	新完整监督下的 8B 时间续训，空间保留	本轮唯一优先训练成果
S	B 的时间选择保持不变，只替换通过非测试门的空间方案	验证空间改进
TS	通过验收的 T＋S	检查组合收益与交互，不预设增益相加

Mac 版本在仓库快照中完成了开发和 NONTEST8，尚无官方成绩；它是否已经交付或得分需要执行端先查现有记录，不能把快照中的“正在推理”当成现在仍在运行。

Z、T 若改变时间集合，空间锚点也必须处理前述依赖问题。新的离线比较共用源时间空间场；和旧 37.63 的线上比较，必要时明确是完整配方差异，不冒称纯时间消融。

官方确实允许每日最多五次，并取阶段最高有效成绩。**有五个合格、有不同依据的包就可以用五次；只有两个就用两个。**不每日重复旧包，也不根据总分连续二分阈值或逐视频探测。更高的有效整包都保留，不设虚构的“不到 0.2 分不算提升”。
AICOMP

六、Linux 和 Mac 怎么安排
Linux：训练、评测、生产全部独立闭环

Linux 负责数据标注小试、唯一主训练、checkpoint 开发评估、完整空间推理及最终封包。继续用现有 GPU 作业锁，不抢占其他项目，不把历史空闲记录当当前可用资源。

**首先改掉资源控制的 Mac 心跳依赖。**当前 controller.py::capacity() 要求 Mac 的容量记录不超过 300 秒，等待超过 600 秒就停止 Linux 阶段。这是明确的运行依赖，不是抽象担忧。

新控制器应采用两机配额预留：

Linux 有明确可用上限，可以在该上限内独立启动作业。
Mac 离线时，仍保留其已知占用和已登记剩余任务的保守预留，不能当作占用为零。
两机加临时缓存的峰值仍不超过原 80 GiB；无法可靠界定 Mac 剩余写入时，不得冒险超分配。

这是改调度方式，不是取消磁盘红线。

Mac：可中断的辅助，不再承担新 8B 主训练

Mac 可做代码检查、合成合同测试、非测试统计、CPU 评分、材料整理和已有 adapter 的归档。已经完成的 Mac 模型继续由 Linux 验收与生产；不为了“Mac 不能闲着”再开一轮昂贵 MPS 适配。

Mac 不在线，上述辅助任务可以暂停，Linux 主线不应受影响。也不要把 CUDA 和 MPS 拼成异构分布式训练来增加故障面。

新作业使用新目录和注册，保留历史源码、source lock 和失败证据；旧一次性 launcher 不直接重开。仓库运行说明本身也明确要求这一点。

七、接下来 48 小时与截止前怎么收口

以下是交给执行端的新排程，不是本次已经启动的作业。

阶段	Linux 主任务	必须交付什么
前 6 小时	新建生产一致评测入口；严格坐标解析与合法空单测；解除无关的 Mac 心跳依赖	代码差异、测试结果、真实资源与磁盘预留
6–24 小时	B/Z/M 的非测试比较；空间尺度上界诊断；新完整监督首批构建	哪个低成本候选值得生产、训练数据是否真的可用
24–48 小时	数据合格则做 T 的小试；并行推进已就绪候选的自动生产	一个可执行的继续/停止决定，以及有机会形成的完整新包，而不只是计划文档
随后 3–6 天	最多一次三轮正式时间续训；选定 checkpoint；有空间证据才形成 S/TS	新时间模型、有限候选官方比较、全部哈希与成本记录
10 月 18 日前	收口结构与监督路线	不再引入新的大模型或训练机制
10 月 19–21 日	干净入口复现最高有效包、整理材料	模型、代码、环境和分数对应一致
10 月 22 日	内部交付截止	留出上传与复现故障缓冲

官方结果截止是 2026 年 10 月 23 日 20:00，作品材料截止是 10 月 25 日 23:59，UTC+8。现在不是只剩几十小时，但也不应等到最后几天才让新模型取得官方分。
AICOMP

最终决策

我不会建议你现在重租卡、换更大的参赛模型，或者把 8B 原配方延长到十几轮。

目前最有价值的三件事，顺序很明确：

先把开发评估换成真实生产链，确认 37.63 的时间 LoRA 究竟比原生 8B 强在哪里；随后用新的完整观察监督训练“该选才选、可以不选”的 8B 时间模型；空间只在尺度上界诊断支持时升级。

当前实现中，非空限制、评测解码错位、坐标单位猜测、最大尺度锁死、Mac 心跳依赖都有具体代码依据；但它们各自能贡献多少官方分还没有测量。冲 50 应靠一轮能改变监督质量和选模依据的实验，加少数完整候选的真实排序，而不是继续把同样的弱标签训得更熟。 

今天 11:21
你说：

GitHub
 浏览GitHub仓库，我们32b教师一直失败，你首先想想咋去纠正，而且我怀疑是代码的错误，你要去仓库核验一下
另外就是如果教师修复之后怎么办？教师失败了怎么办？就是要再给一个后续方案，一个或者多个

思考了 18m 52s
ChatGPT 说：

你的怀疑有依据：仓库里确实存在代码问题，而且我又发现了一处“前面的教师审核即使通过，后面也会必然停止”的阶段衔接错误。

但需要把两件事分开：

**最新的32B已经能正常返回结果；目前直接阻断开训的是标签审核和数据准入。与此同时，教师到学生的代码链仍有尚未走到的故障。**因此，不能简单归因成“32B能力不行”，也不能只改提示词、反复跑到出现一个空标签为止。

本次审计固定在仓库最新提交 b16edc8777f04c72250ef61dad01d18d90f1927f，重点核查了 teacher_student_autopilot_v7、teacher_context_diagnostic_v3、教师下载配方和B2接续记录。我做了CPU最小逻辑复现，没有修改你的仓库、连接Linux执行任务或重新运行32B。仓库未发布教师逐条原始回答和媒体，因此涉及实际画面语义的判断，我只采用已发布记录，不把它说成独立看过视频后的结论。

一、先把当前状态纠正清楚
项目	当前仓库支持的结论
32B教师最新运行	4个窗口，4次标注＋4次复查，共8次真实请求，0工程失败。不是8个窗口
最新标注结果	3个正例获弱复查支持；唯一 NO_HIGHLIGHT 被拒绝，没有受支持的整窗空例
新学生T	优化器更新0次，尚未训练成功
当前线上基准	Linux B为37.63
B2新包	已在Linux完成严格验收，尚无新的官方分数，不是教师微调后的T
Mac	已取得33.46，随后退出计算和中转，不应重新安排它训练
资源约束	最新记录已取消人为磁盘、内存、显存额度；按实际物理容量和共享任务安排，不再继承旧80GiB限制

这些更新很重要：现在不需要重做Mac方案，也不能把已经完成的B2重新排成“待开发”，更不能把T写成已经训过但退化。

我的总体安排是：

B2的交付不再等待教师；教师修复限定为一次明确的代码与标注协议修正。修好后走完整监督微调；只能得到部分可靠监督，就缩小训练任务；仍不可靠，就转不依赖32B的8B推理改进。

二、代码核验：哪些是真错误，哪些是设计问题？
1．新发现的确定性错误：probe → all 会撞上自己的缓存保护

这是本次最明确、应最先修的代码问题。

在 teacher_student_autopilot_v7/controller.py 中，控制器按顺序执行：

Python
teacher_command(config, admission, 'probe')
teacher_command(config, admission, 'all')

而 teacher_command() 对两个阶段都使用同一个输出目录：

Python
--out-dir .../teacher_01

也就是说，probe 成功后，会在该目录留下真实探针窗口的 done.json。

但是 teacher_label.py::main() 的逻辑是：

Python
if args.phase != "review":
    probe_windows = choose_probe_windows(...)
    for window in probe_windows:
        annotate(..., allow_prior_reuse=False)

probe和all都会进入这个分支，而且选择函数会读取已经保存的同一份探针选择记录。

接着，annotate()发现 done.json 已存在，会执行：

Python
require(
    allow_prior_reuse,
    "fresh real generation required; an existing done cache "
    "cannot count as a new heavy-input probe"
)

因为传入的是 False，所以直接失败。

结论：按当前控制器路径，即使教师小试和探针全部通过，全量阶段仍会被已成功的探针缓存阻断。

需要特别区分：它不是前面“12条全正”或最新空例被拒绝的原因，因为那些运行还没有走到这里；它是后面必遇到的潜伏故障。

我已把这段条件逻辑做成CPU最小复现，4项测试通过，其中包括确认原路径会触发上述拒绝：

这个脚本是故障逻辑复现，不是完整生产补丁，也没有模拟完整权重、媒体和缓存哈希校验。

正确修法不是把所有 allow_prior_reuse 改成 True，而是拆开阶段职责：

阶段	应有行为
probe	确实执行新的探针，不允许拿缓存冒充新生成
all / labels	核验已有探针的来源、模型、提示词、输入和输出身份，然后复用成功标注，只生成剩余窗口
review	审核已经存在的标注，不重新触发探针

新测试必须真正串起一次 pilot → probe → all → review，检查调用次数、剩余窗口数、失败缓存拒绝和成功文件不变。继续只增加零散函数测试，覆盖不到这类故障。

2．精度修复分散在不同分支，不能认为“诊断通过＝全链修好”

最新 teacher_context_diagnostic_v3/diagnostic.py 已经采用：

帧序号与对应时间成对约束；
时间端点用十进制字符串；
验证时用 Decimal。

但正式自动教师分支 teacher_student_autopilot_v7/teacher_label.py::request_schema() 仍在使用：

Python
segments[key] = {
    'type': 'number',
    'enum': boundaries
}

两条分支的输出表示仍不相同。并且context v3的代码明确写着：**不生成新训练标签，不准入学生训练。**所以不能把context v3的“请求成功”接到旧v7后面，就声称教师到学生已经完成修复。

这不是无关紧要的洁癖。仓库已经记录过两个真实症状：

**帧与时间交叉配对。**某次模型输出的帧1723，正确窗口时间为11.86345833333333，却写成12.36395833333333，差0.5005秒。原语法分别约束帧序号和时间，却没有约束二者配对。

**数值常量被运行时改写。**固定C++运行时曾把13.782041666666667转为13.782041666666666。context分支改为字符串，正是为避免这种表示冲突。

我的建议比继续扩大“小数位数上限”更直接：

模型负责选事件和边界编号；程序负责精确时间、源帧身份和数值转换。

例如模型只返回：

JSON
{
  "state": "KEEP",
  "segments": [
    {"start_boundary_id": 12, "end_boundary_id": 28}
  ],
  "evidence_frame_ids": [14, 21]
}

边界编号对应的真实PTS表在程序里固定，窗口末端额外作为一个合法边界。证据帧编号与边界编号分开定义，不能混用。程序检查排序、非交叠、半开区间和实际包含源帧，再转换成学生需要的秒数。

不要再要求模型准确抄写几十个时间戳、长小数和身份元数据，然后把抄写失败归为视觉理解失败。

3．审核器本身不可靠，却被赋予了“全部否决权”

context v3的审核逻辑是：

Python
supported = (
    all_provided_frames_reviewed
    and semantics_consistent
    and not uncertain
    and not issues
)

只要审核提出任何问题，就不支持该样本。v7的 reviewed_gate() 更进一步：任何一个已准入样本的弱复查被拒绝或不确定，整个pilot都失败。

而最新记录已经出现审核器的可证实错误：

审核说背景overview只到119.0189秒；实际输入回执末PTS约149.9832秒，并有13张120秒以后的图片。

这说明“审核拒绝”不等于“原标签一定错”。但该拒绝还包含其他语义争议，所以也不能因为它算错一处时间，就把整个拒绝翻成PASS。

现在的流程实际混合了三个问题：

输入是否完整、时间是否合法、内容是否值得保留。

前两个应主要由程序解决，第三个才交给视觉模型。当前让同一个32B既标注、又检查时间算术、又审核长篇理由，最后一票否决整个数据批次，可靠性要求过高。

建议改为逐条、分层裁决：

情况	新协议应如何处理
来源、帧身份、PTS映射确实错误	工程失败，停止相关执行并修复
模型描述与证据帧明显不符	该条标签拒绝，保留原文
两次判断有语义争议	该条标为UNKNOWN，不转为空标签
非关键解释有瑕疵	单列问题，不能仅凭一句不准确的解释自动否定全部边界
部分样本不能使用	记录纳入率和类别分布，不让一条争议默认取消整个标注任务

这不是“降低标准让它通过”，而是不再把单条不确定性错误地升级为整个教师程序故障。

同模型第二次调用可以提供一致性证据，但不能叫独立真值。更合理的第二次判断应先独立给出事件与选择，再与第一次比较，而不是一开始就把原答案和完整理由塞给它，让它围绕原答案挑错。

4．“12条里没有整窗空例”被写成硬门，阻断了更大范围的数据获取

pilot.py::gate()明确要求12条里至少出现一个合格空例，否则停止。完整数据的 semantic_audit()又要求train/dev各自至少一个整窗空例。

这里必须纠正：

需要可靠负监督，不等于12个自然窗口中一定应该出现整窗空例。

举一个纯示例：假设自然空例比例为10%，且独立取12个窗口，全部非空的概率仍约28%。这不是对你数据分布的估计，只说明“小样本没看到空例”不能单独证明模型坏了。

同样，整窗非空，不等于窗内没有可用的负时间段。前提仍是标注流程确实观察、判断了该范围，而不是拿旧正区间的补集冒充背景。你们原讨论中正确的要求是区分已覆盖正例、教师负例和UNKNOWN，不是要求每个小试一定抽中整窗空例。
context-p01

因此，新协议应把两道门分开：

**是否可以继续收集非测试标注？**看工程是否正常、是否存在明显坍塌、审核是否有解释依据。

**是否可以训练“整窗拒绝/全空输出”？**看最终是否确实有可靠的相关监督。

不能因为后一个目标暂未满足，就禁止前一个任务继续取得证据。

5．“第20次更新冒烟”对当前小数据规模也不合适

代码要求最多3轮内必须能完成至少20次更新。128条训练窗口、有效batch16、3轮，一共只有24次更新。**第20步才做关键前缀验收，已经接近整个训练结束。**过滤后若只剩96条，3轮只有18步，代码还会直接拒绝开训。

这是工程验收与科学预算耦合，不是模型训练能力限制。

新版本建议用 2–4次真实优化更新 验证损失、梯度、冻结和adapter重载；随后保持优化器状态继续训练。训练量由有效数据和实验目标决定，不为了凑20步强迫扩大数据或重复曝光。

三、哪些历史故障已经修了，不应再次浪费时间？

仓库的全面核查已经记录了以下修复：

已发生的故障	已记录的修复
学生四位小数限制导致12条真实目标中11条被拒绝	新精度序列化及原目标无损回放
sys.path / sys.modules误加载旧helper	显式核验当前模块文件身份
数值合法的极短区间实际上不含源帧	开发和生产共享真实PTS区间检查
空间零调用时成本为空、缓存与探针重复计费	分离真实调用成本和已有缓存
服务器会话回执覆盖、监控漏掉python -B进程	会话分目录和完整进程身份检查

这些是真实工程问题，不应该被轻描淡写成“模型偶尔发挥不好”；但已经修复的部分也不应每次重新列为主要任务。现在重点是整条调用链能否衔接，而不是继续增加孤立的PASS报告。

四、32B应该怎么纠正：保留权重，先减掉不必要的任务负担

我核对了下载配方：你们用的是官方 Qwen3-VL-32B-Instruct的Q4_K_M语言权重＋F16视觉编码器，不是未注明来源的随意量化文件。官方也确实发布了这两类组件。现有证据不足以把失败归咎于“四位量化把模型弄坏了”，不建议第一步重下权重。 
Hugging Face

我建议按下面顺序修，先登记一个新的独立版本，旧源码和失败保留。

第一步：先证明它看对了图，而不是先要求它证明“什么是高光”

当前教师通过 image_url 接收64张独立图片和大量时间文本；context v3是64张全源overview再加64张目标图片。代码证明的是图片经过了处理，不是模型正确理解了所有图片及其顺序。

先用少量合成接口样本和合规非测试样本检查：开始、中间、结尾的明显可见变化能否定位；换图后回答是否跟着变化；帧顺序变化能否被识别。合成样本只测接口，不充当真实高光负例。

如果连这种简单观察都不稳定，再考虑运行时、视觉输入或量化对照。不要一开始就在“家具组装是不是摘要必要内容”上来回争论，那无法区分看错图与判断标准不同。

另外，多张独立图片不能未经验证就等同于Qwen原生视频输入；官方实现区分图片与视频处理，并有视频时间相关结构。因此，原生视频路径值得做匹配小对照，但不能直接断言它必然更好，或认为当前图片路径天然错误。
Hugging Face

第二步：模型输出短决策，程序保存长证据

保留原始图片、完整PTS、哈希和请求回执，但把它们放在程序侧。

教师输出收敛到：保留／不保留／不确定，事件证据帧编号，边界编号，简短依据。

不要要求模型重复几十个固定时间戳，也不要把语法强制输出的 all_provided_frames_reviewed=true当作“模型确实看懂全部帧”。这一字段在原标注语法里本来就是结构常量，仓库审计已明确承认。

第三步：先保持教师与学生回答同一个问题

context v3的提示词已经变成：

相对于整段源片，目标内容对摘要是否必要、是否与其他部分重复。

但目前8B学生训练输入仍主要是局部30秒窗口。这意味着教师可能因为“别处已经出现同样结果”而不选当前窗口，而学生根本看不到“别处”。

我的第一轮选择是：教师先标注与学生局部输入相匹配的可见关键事件及边界；全源去重和摘要必要性另立一条方案。

若坚持做全局相对高光，学生的训练、开发和生产也要有相应全局上下文。不能只给教师更多信息，却默认局部学生一定能学出同样决策。

第四步：有限新样本验收，不再围绕同12条反复改提示词

保留原12条作为故障回归集，另外登记一批未用于这些提示词修订的非测试窗口。

我的建议是首批24条，不是要求24条全通过，而是回答：

工程能否完整执行？视觉证据是否对应？哪些标签可用？争议来自哪里？可靠监督覆盖了哪些类别？

不强造空例，不把审核拒绝转空，不只保留“容易让教师一致”的样本后声称总体质量提升。标注总量、可用量、排除原因以及来源分布都要报告。

五、修复之后怎么办：三条明确后续路线
路线A：教师能稳定提供完整窗口监督——继续8B时间微调

这是优先训练路线。

前提不是“32B能输出合法JSON”，而是输入、时间映射和审核可靠性已经通过上述检查，并形成一批真正可用的完整窗口弱监督。

设置	建议
数据起点	128个训练窗口＋32个开发窗口；来源组隔离
扩展	首批有价值再扩，当前轮最多按512／64规划，不一上来标几千条
初始化	当前37.63对应的B最终时间adapter
基座、视觉	继续冻结
LoRA	保留语言q/k/v/o，r16、alpha32、dropout0.05
学习率	1e-5，作为新实验起点
有效batch	16；微批按Linux实际显存安排
工程小试	2–4次真实更新，检查损失、梯度、冻结和重载
正式上限	最多3轮；每轮保存adapter
选择	与B使用同一生产输入和解码协议比较，保留B作为候选0
空间端	同一8B原生空间模式，先不训练空间LoRA

这些是新实验建议，不是已验证最佳超参数。

**不能只用“学生越来越像32B”作为胜出的全部依据。**新的教师一致性、旧弱标签一致性和完整生产工程指标分开报告；若没有独立质量参考，明确这个盲区。候选通过非测试完整链后，再进行固定算法的完整包比较，不靠测试逐视频修结果。

这一轮只改变时间监督和相应训练，不同时增加稠密头、空间LoRA、RL和新采样机制，否则无法判断收益来自哪里。

路线B：教师只在事件定位上可靠，整窗高光／空判断仍不可靠——做“局部边界精修”，不强训拒绝器

这是我最建议保留的降级训练路线。

教师失败未必是全面失败。可能出现这样的结果：

它能够可靠指出某个动作何时开始、结果何时出现，但不能稳定判断整窗是否值得进入摘要。

这时不要继续逼它产生全空标签。把任务收窄：

当前B负责提出候选事件区间；32B只对候选对应的已确认事件提供局部边界证据；学生学习边界精修，不学习全视频有无高光。

具体做法是，在非测试材料中对已有弱正事件或B提出的候选，先确认事件身份和可见证据，再形成“候选区间＋周围上下文→修正边界”的训练样本。争议样本不用，候选外未知区域不标负。

推理时仍由同一个8B依次完成候选和精修，最终空间也用该基座，所有额外adapter张量如实计入参数账。新边界精修可以使用独立小adapter，保留原B时间adapter不变，避免直接续训损坏原来的候选能力。

**这条路线能争取的是边界质量，不能宣称解决整窗误选或遗漏全部未知高光。**只有非测试证据显示边界确实有改善空间才训练；若教师连边界也不可靠，直接进入路线C。

同样，不能把这条路线偷偷叫作原T已经通过。它是目标更窄、监督要求不同的新实验。

路线C：教师修复后仍不可靠——停止32B标注路线，但不停止冲分

这里我不建议继续循环“换提示词—重新标12条—审核拒绝—再换提示词”。

**先把已经完成的B2转为实际外部验收。**仓库记录的B2已经完成426视频、521窗口和完整空间链，最终ZIP严格验证通过，当前缺的是新官方成绩，不是再次训练或重新生成。37.63仍只属于旧B包。

B2之后，无需32B的新机制，我优先建议：

同一8B的“全源粗览形成简短事件表→局部窗口精确定位”两阶段推理。

第一遍只提取全源主要可见事件和粗时间位置；第二遍带着这些信息读取局部窗口，产生精确区间。它针对的是“局部窗口缺少全局主线”这一可解释问题，而不是统一扩大覆盖率或扫描阈值。

这条路线先不微调、不新增独立模型。用非测试数据比较B2与新两阶段算法，检查全局摘要幻觉、遗漏和局部边界，再决定是否形成一个完整风险候选。额外前向成本按真实Linux耗时核算。

**失败出口也明确：**全局摘要错误把局部选择带偏，或相同非测试协议下广泛退化，就保留B/B2，不再加第三层自我审核补丁。

至于换教师后端，我只把它作为有证据触发的工程备选：简单视觉定位测试已经表明当前后端或输入路径异常时，才做另一条受支持路径的少量对照。不是因为审核不一致就默认重下BF16、换量化或全局升级环境。

六、现在应该怎样给Linux派任务？

**只按Linux独立闭环安排，Mac不再进入关键路径。**最新仓库已记录Mac退出、人为资源额度取消；仍保留共享任务保护、实际容量核查和GPU账本。

建议执行顺序如下：

优先级	任务	必须得到的结果
P0	修复probe → all；统一教师、审核、学生的时间表示；跑阶段串联测试	真实调用次数正确，缓存不冒充新生成，成功探针不重复运行
P1	少量视觉定位检查＋短输出教师接口	证明它能看对、定位对，而不只是HTTP和JSON成功
P2	新24条标注与逐条审核	可用正、负、边界与UNKNOWN的实际数量；不要求全批一致
P3-A	完整监督成立，进入路线A	一次最多3轮的8B时间微调与匹配开发比较
P3-B/C	完整监督不成立	有边界证据走B；连边界不可靠走C
独立推进	获取并验收已完成B2包的交付状态	不等待教师再修一次，不把B2冒充新T

我建议给教师修复设一个实验次数上限：完成这次接口与流程修正后，做首批新24条；只有存在一个明确、可复现、可修复的新原因，才允许第二批匹配对照。不要为了凑出空例无限开版本。这个上限是控制投入的建议，不是判断模型质量的统计定律。

最后的判断

我现在最反对的做法，是把“32B教师失败”当成一个统一结论，然后继续盲改提示词。

你们目前同时存在三类问题：

**代码衔接会失败；模型被要求承担不必要的时间与证据抄写；同模型弱审核又被当成整个数据集的绝对裁判。**其中第一类可以确定修复，第二类应该简化，第三类必须改成有记录的逐条质量处理，不能靠强迫一致解决。

我的主张是：先修这条链，再判断教师能提供哪一级监督。完整监督够，就微调时间选择；只有边界可靠，就训练边界精修；教师整体不可靠，就停它、交付B2并推进同8B的全局—局部推理。冲50分的工作不能再被一个不可靠空标签或一处未走到的缓存错误长期扣住。

reproduce_probe_handoff.py
代码
ChatGPT 可能会出错。请核查重要信息。
最新一条回复




Pro
```


## V14完整独立聚合验收原文

来源与字节身份：{"path": "G:\\ai\\AIC视频\\reports\\round6_score_alignment\\rematch_execution\\rematch_exec_20261005T1215Z\\controller\\V14_final_acceptance_20261008.json", "bytes": 6962, "sha256": "f8f17dcad75dd96ff0ddcc89caf9f6531ebdcb9e0965fae81a7d4236c2ecc027"}

```json
{
  "status": "PASS_INDEPENDENT_V14_FINAL_ZIP_TRAINING_SELECTION_AND_ACCOUNTING",
  "utc": "2026-10-08T15:49:24.511694+00:00",
  "host": "inspur-NP5570M5",
  "entry": "teacher_student_autopilot_v14",
  "source_lock_sha256": "5295e8bc0f2b6a651e73321a5798b259816ccbe9a0582753dc3c200b5ef080e0",
  "frozen_files_verified": 16502,
  "verifier_source_sha256": "11479e89d5e62e4a1fdad24a2a2c7eddb54163942c364c6126a61f5079e15d53",
  "completion_sha256": "ca072f6ef922a7abd2c93684543da0caf3c427b6ca5706dd4c615ae42a190d7c",
  "completion_status": "PASS_AUTOPILOT_FINAL_T_ZIP_ON_LINUX",
  "scopes": {
    "nontest": {
      "videos": 8,
      "prediction_frames": 447,
      "strict_checks": {
        "strict_loader_ok": true,
        "video_record_set_exact": true,
        "selected_key_set_exact": true,
        "ratio_fields_exact": true,
        "frames_sorted": true,
        "provenance_key_set_exact": true,
        "provenance_boxes_match_predictions": true,
        "provenance_all_legal": true,
        "provenance_sources_allowed": true,
        "archive_single_file": true,
        "archive_roundtrip_exact": true
      },
      "independent_report_sha256": "3fd7c8d3c2e640f4d1f9781b768008bbbfb5337b5da448dfb20ebd8328cb3e0b",
      "manifest_sha256": "ba34a284183e8a079054ffe811d7ec096e6b47c94e6edf812a37fd11b92d8dd7",
      "registry_sha256": "7f57785312c94b1658cb002b2432d09b318ae2943e3297a0c45536d1bd8cd3ea",
      "candidate": "/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/teacher_student_autopilot_v14/nontest_01/candidate_T_8B.zip",
      "zip_bytes": 1977,
      "zip_sha256": "dda5699db366ac62ab55ac3fef8145d77f954f4aff8b126f21a86fb233e503be",
      "predictions_sha256": "cf94275b0c31a6e978991bf489f157c37c54ade815355e0f87499a414c5dc71d",
      "provenance_sha256": "b57cdde4a2a2b14af2aca0c56ff15545b442f2e8523e5d0bd047d3e507d29caf",
      "crc_pass": true,
      "archive_names": [
        "predictions.jsonl"
      ],
      "archive_roundtrip_exact": true,
      "source_ids_exact": true,
      "duplicate_source_ids": 0,
      "temporal_windows": 8,
      "invalid_temporal_windows": 0,
      "source_anchors": 206,
      "new_spatial_model_calls": 0,
      "original_spatial_wall_seconds": 124.7222928898409
    },
    "rematch": {
      "videos": 426,
      "prediction_frames": 102470,
      "strict_checks": {
        "strict_loader_ok": true,
        "video_record_set_exact": true,
        "selected_key_set_exact": true,
        "ratio_fields_exact": true,
        "frames_sorted": true,
        "provenance_key_set_exact": true,
        "provenance_boxes_match_predictions": true,
        "provenance_all_legal": true,
        "provenance_sources_allowed": true,
        "archive_single_file": true,
        "archive_roundtrip_exact": true
      },
      "independent_report_sha256": "4059655c82ba1544c0f722241dbcbe426a193f768c6833b4d13f7334ed379967",
      "manifest_sha256": "ceb91ee9434ce3de6a55abf727e613b83368b547d3be3d1e71b46414c2f019f8",
      "registry_sha256": "1058aba02e5e959bc8e4842cbde0eadced192a8201d5c833ae50a7c0aac07909",
      "candidate": "/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/teacher_student_autopilot_v14/rematch_01/candidate_T_8B.zip",
      "zip_bytes": 308278,
      "zip_sha256": "95173d936d09cfcf84bcff5755336e50dbfff94ac5a7e4cfba2953064022f3a2",
      "predictions_sha256": "9ebd31540b905e08da3352709cf1ff38eb241b3be6b55ea087dff7df9304c4e4",
      "provenance_sha256": "02c4745f2a0eef209d83a694a86eb4dfe3fe2ec5f32b9c470a3df3f8a58040e6",
      "crc_pass": true,
      "archive_names": [
        "predictions.jsonl"
      ],
      "archive_roundtrip_exact": true,
      "source_ids_exact": true,
      "duplicate_source_ids": 0,
      "temporal_windows": 521,
      "invalid_temporal_windows": 0,
      "source_anchors": 31295,
      "new_spatial_model_calls": 0,
      "original_spatial_wall_seconds": 18723.876517390832
    }
  },
  "actual_T_optimizer_updates": 15,
  "actual_backward_examples": 195,
  "epochs_completed": 3,
  "finite_loss_gradient_all_updates": true,
  "changed_adapter_tensors_each_update": 288,
  "frozen_base_runtime_sha256": "74bcce81cfcb0893cf4b4c25ae36ec908d6ea669583aedd0f3940063080b8b59",
  "frozen_base_receipts_equal": true,
  "prefix_state_current_sha256": "b0da6fea62453437191176a3fa32e246996d800a3f38779ed635b88eecc6099d",
  "prefix_updates": 4,
  "original_independent_CPU_reload_sha256": "ab0dd5b0274346ac4d8fb7cbad3e49e921deaa5c0226ef53d243d2346f96962e",
  "independent_CPU_reload_was_288_adapter_PASS": true,
  "CPU_reload_repeated_by_this_audit": false,
  "candidate_artifact_SHAs_pass": true,
  "weak_dev_candidates": [
    {
      "epoch": 0,
      "video_macro_f1": 0.3786251362162477
    },
    {
      "epoch": 1,
      "video_macro_f1": 0.3786251362162477
    },
    {
      "epoch": 2,
      "video_macro_f1": 0.3596785770535768
    },
    {
      "epoch": 3,
      "video_macro_f1": 0.36453995670744305
    }
  ],
  "independent_selection_recomputed": true,
  "selected_epoch": 0,
  "selected_original_B": true,
  "trained_candidate_selected": false,
  "selected_adapter_sha256": "8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23",
  "new_T_improvement_claim": false,
  "teacher_original_labels": 160,
  "teacher_original_reviews": 160,
  "supported_train": 65,
  "supported_dev": 14,
  "UNKNOWN_preserved": 81,
  "same_teacher_consistency_weak_not_truth": true,
  "resources": {
    "rematch_TAUTO_v14_student_train": {
      "receipt_sha256": "86a8e8535380e9b33f340a71808dbcbd41a67e96594d9db2ef8146ef56ef1e66",
      "charged_seconds": 2231.7791278334334,
      "sampled_peak_memory_mib": 21484,
      "ledger_exact": true,
      "exit_code": 0,
      "stop_reason": null
    },
    "rematch_TAUTO_v14_nontest_temporal": {
      "receipt_sha256": "ebb409130e66281ee9c0379ef8369ac2438ff5e87e7befcad2161c17fbfdf64f",
      "charged_seconds": 164.55463389214128,
      "sampled_peak_memory_mib": 19306,
      "ledger_exact": true,
      "exit_code": 0,
      "stop_reason": null
    },
    "rematch_TAUTO_v14_rematch_temporal": {
      "receipt_sha256": "2fe4e7f9954aaec03276a1265ffb1d7c7b86335c63b5d68b2bb72597d4c6667c",
      "charged_seconds": 5430.027779461816,
      "sampled_peak_memory_mib": 25338,
      "ledger_exact": true,
      "exit_code": 0,
      "stop_reason": null
    }
  },
  "gpu_ledger_records": 154,
  "gpu_ledger_sha256": "fce49c2d3d1ab170ee6df9315deceb0bd65cebe626d898232cf68b09919152d8",
  "gpu_ledger_not_modified": true,
  "historical_offset_seconds_preserved": 7200,
  "owned_processes": [],
  "logical_parameters": 8782459120,
  "model_calls_by_this_audit": 0,
  "optimizer_updates_by_this_audit": 0,
  "teacher_calls_by_this_audit": 0,
  "per_frame_data_exported": false,
  "raw_answers_exported": false,
  "large_transfer_bytes": 0,
  "official_score": null,
  "automatic_return": false,
  "uploaded": false
}

```


## V14继承科学与接续协议完整原文

来源与字节身份：{"path": "G:\\ai\\AIC视频\\reports\\round6_score_alignment\\rematch_execution\\rematch_exec_20261005T1215Z\\teacher_student_autopilot_v14\\PROTOCOL.md", "bytes": 13456, "sha256": "e2d9e76650deb3e2b6a7bce76af9b9e9d23225b8547d9e4eddbf3169799cf215"}

```
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


## 当前时间/空间生产函数完整原文

来源与字节身份：{"path": "G:\\ai\\AIC视频\\reports\\round6_score_alignment\\rematch_execution\\rematch_exec_20261005T1215Z\\teacher_student_autopilot_v14\\production_t.py", "bytes": 30079, "sha256": "fc232b7ba8b11999a68f237a5febd8c5fc3c3e6868580010f6a3e6b9ea682b7b"}

```python
"""Selected T adapter, floor/native-PTS input, frozen source spatial field."""
from autopilot_common import *
import argparse
from fractions import Fraction
import shutil
import sys
import time
import subprocess
from bisect import bisect_left
import math
import zipfile


STRICT_CHECKS = frozenset(('strict_loader_ok', 'video_record_set_exact', 'selected_key_set_exact',
    'ratio_fields_exact', 'frames_sorted', 'provenance_key_set_exact',
    'provenance_boxes_match_predictions', 'provenance_all_legal', 'provenance_sources_allowed',
    'archive_single_file', 'archive_roundtrip_exact'))
CACHE_FILES = ('field_frames.jsonl', 'field_shots.jsonl', 'anchor_requests.jsonl',
    'anchor_output.jsonl', 'schedule.stage.json', 'spatial.stage.json',
    'package.stage.json', 'independent_validation.json')
BASE_SHA = '74bcce81cfcb0893cf4b4c25ae36ec908d6ea669583aedd0f3940063080b8b59'
BASE_PARAMETERS = 8767123696
BASE_HASH_METHOD = 'sorted canonical names and all unique frozen parameter bytes'


def check_independent(value, scope, expected_frames):
    require(scope in ('nontest', 'rematch'), 'unknown production scope')
    require(value.get('status') == 'PASS_INDEPENDENT_STRICT_VALIDATION' and
            set(value.get('checks', {})) == STRICT_CHECKS and
            all(value['checks'][key] is True for key in STRICT_CHECKS), 'fixed 11 strict checks did not pass')
    require(value.get('video_records') == (8 if scope == 'nontest' else 426) and
            value.get('expected_frames') == value.get('prediction_frames') == expected_frames and
            value.get('strict_loader_issues') == [] and
            all(value.get(key) == 0 for key in ('duplicate_frames', 'missing', 'extra')),
            'independent denominator or issue receipt differs')
    require(value.get('strict_loader_sha256') == sha(RUN / 'baseline_a_pts_v1/vendor/frozen_strict_loader/aic6/scoring.py'),
            'independent original strict validator changed')


def check_base_hash(value, config):
    require(config.get('expected_base_sha256') == BASE_SHA and config.get('base_parameters') == BASE_PARAMETERS,
            'registered B2 base identity differs')
    require(value.get('sha256') == config['expected_base_sha256'] and
            value.get('parameters') == config['base_parameters'] and value.get('method') == BASE_HASH_METHOD,
            'spatial full frozen base identity differs')


def b2_cache_evidence(scope, source):
    """Consume the actual B2 terminal and historical receipts without inventing measurements."""
    require(scope in ('nontest', 'rematch'), 'unknown cache scope')
    b2 = RUN / 'b_score_aligned_package_v4'
    config, prior = read(b2 / 'config.json'), read(RUN / 'next_round_v1/config.json')
    terminal = read(b2 / 'completion.json')
    lock_sha = sha(b2 / 'source_lock.json')
    require(terminal.get('stage') == 'PASS_COMPLETE_426_B2_8B_ZIP_ON_LINUX' and
            terminal.get('source_lock_sha256') == lock_sha, 'B2 completion or source lock differs')
    require(read(b2 / 'source_lock.json')['files'].get(str(b2 / 'config.json')) == sha(b2 / 'config.json'),
            'B2 configuration lacks frozen byte binding')
    require(config['model_receipt'] == prior['model_receipt'] and config['model_dir'] == prior['model_dir'] and
            config.get('model_revision') == '0c351dd01ed87e9c1b53cbc748cba10e6187ff3b' and
            sha(config['model_receipt']['path']) == config['model_receipt']['sha256'], 'source spatial base receipt differs')
    require(read(HERE / 'config.json')['source_color_repair'] == config['source_color_repair'],
            'registered sample conversion changed')
    require(source == config['inputs'][scope] == prior['inputs'][scope] and
            sha(source['manifest']) == source['manifest_sha256'] and
            sha(source['registry']) == source['registry_sha256'], 'current scope inputs differ from B2')
    require(len(read(source['manifest'])['records']) == (8 if scope == 'nontest' else 426), 'scope source denominator differs')
    require(terminal.get('nontest_package_receipt_sha256') == sha(b2 / 'nontest_01/package.stage.json') and
            terminal.get('independent_validation_sha256') == sha(b2 / 'rematch_01/independent_validation.json'),
            'B2 completion internal receipt SHA differs')
    final = read(b2 / 'rematch_01/package.stage.json')
    require(terminal.get('videos') == 426 and terminal.get('crc_pass') is True and
            all(terminal.get(key) == final.get(key) for key in
                ('candidate', 'zip_bytes', 'zip_sha256', 'predictions_sha256', 'archive_names')),
            'B2 completion/package identity differs')
    measured_path = b2 / 'rematch_01/spatial.stage.json'
    measured = read(measured_path)
    require(measured.get('status') == 'PASS_STRICT_SOURCE_FIELD_SPATIAL' and measured.get('invalid') == 0 and
            measured.get('logical_parameters') == BASE_PARAMETERS and measured.get('time_adapter_enabled') is False,
            'B2 measured base authority incomplete')
    check_base_hash(measured.get('base_hash', {}), config)
    cache = b2 / (scope + '_01')
    require(all((cache / name).is_file() for name in CACHE_FILES), 'complete B2 cache lacks evidence')
    schedule, spatial = read(cache / 'schedule.stage.json'), read(cache / 'spatial.stage.json')
    package, independent = read(cache / 'package.stage.json'), read(cache / 'independent_validation.json')
    require(schedule.get('status') == 'PASS_TIME_INDEPENDENT_SOURCE_FIELD' and
            schedule.get('temporal_selection_used_for_boundaries') is False and schedule.get('max_gap') == 8,
            'source cache schedule algorithm differs')
    for name, key in (('field_frames.jsonl', 'field_frames_sha256'), ('field_shots.jsonl', 'shots_sha256'),
                      ('anchor_requests.jsonl', 'requests_sha256')):
        require(sha(cache / name) == schedule.get(key), 'source cache schedule SHA differs: ' + name)
    require(spatial.get('status') == 'PASS_STRICT_SOURCE_FIELD_SPATIAL' and spatial.get('invalid') == 0 and
            spatial.get('logical_parameters') == BASE_PARAMETERS and spatial.get('time_adapter_enabled') is False and
            spatial.get('strict_units') == 'INTEGER_0_TO_1000' and spatial.get('failure_to_empty_conversions') == 0 and
            spatial.get('rows') == spatial.get('model_calls') == schedule.get('anchors'), 'source spatial receipt differs')
    if 'base_hash' in spatial:
        check_base_hash(spatial['base_hash'], config)
    else:
        bindings_path = b2 / 'cache_bindings.json'
        require(read(b2 / 'source_lock.json')['files'].get(str(bindings_path)) == sha(bindings_path),
                'historical reuse binding is not B2-frozen')
        binding = read(bindings_path)['scopes'][scope]
        origin = Path(binding['path'])
        require(spatial.get('reused_cache') is True and spatial.get('model_calls_this_B2_candidate') == 0 and
                spatial.get('source_cache') == str(origin) and spatial.get('cache_binding_sha256') == sha(bindings_path) and
                binding.get('cpu_eligible') is True and binding.get('spatial_eligible') is True and
                origin == Path(config['cpu_cache_root']) / (scope + '_01') and
                binding['manifest_sha256'] == source['manifest_sha256'] and
                binding['registry_sha256'] == source['registry_sha256'], 'historical spatial reuse lineage differs')
        require(set(binding['files']) == set(CACHE_FILES[:6]), 'historical spatial binding file set differs')
        for name, digest in binding['files'].items():
            require(sha(origin / name) == digest, 'historical source bytes changed: ' + name)
            if name.endswith('.jsonl'):
                require(sha(cache / name) == digest, 'B2 copied source bytes differ: ' + name)
        original = read(origin / 'spatial.stage.json')
        require(all(spatial.get(key) == value for key, value in original.items()), 'B2 historical spatial receipt changed')
    require(package.get('status') == 'PASS_COMPLETE_B2_8B_PACKAGE_ON_LINUX' and package.get('scope') == scope and
            package.get('video_records') == (8 if scope == 'nontest' else 426) and package.get('issues') == [] and
            package.get('prediction_frames') == schedule['selected_frames'] and package.get('source_lock_sha256') == lock_sha and
            package.get('complete_pipeline_parameters') == 8782459120 and
            all(package.get(key) == 0 for key in ('weak_roi_inputs_used', 'old_test_boxes_used', 'silent_fallbacks')),
            'B2 package status, denominator or issues differ')
    check_independent(independent, scope, schedule['selected_frames'])
    require(package.get('candidate') == str(cache / 'candidate_B2_8B.zip'), 'B2 candidate path differs')
    for name, key in (('predictions.jsonl', 'predictions_sha256'), ('provenance.jsonl', 'provenance_sha256'),
                      ('candidate_B2_8B.zip', 'zip_sha256')):
        require(sha(cache / name) == independent.get(key) and
                (key == 'provenance_sha256' or package.get(key) == independent[key]), 'B2 accepted artifact SHA differs: ' + name)
    archive_path = cache / 'candidate_B2_8B.zip'
    require(archive_path.stat().st_size == package['zip_bytes'] and
            package.get('archive_names') == independent.get('archive_names') == ['predictions.jsonl'], 'B2 archive receipt differs')
    with zipfile.ZipFile(archive_path) as archive:
        require(archive.namelist() == ['predictions.jsonl'] and archive.testzip() is None and
                archive.read('predictions.jsonl') == (cache / 'predictions.jsonl').read_bytes(), 'B2 actual archive differs')
    return {'status': 'PASS_FROZEN_B2_SOURCE_FIELD_CACHE', 'cache': str(cache),
        'files': {name: sha(cache / name) for name in CACHE_FILES},
        'B2_completion_sha256': sha(b2 / 'completion.json'), 'B2_source_lock_sha256': lock_sha,
        'B2_config_sha256': sha(b2 / 'config.json'), 'manifest_sha256': source['manifest_sha256'],
        'clock_registry_sha256': source['registry_sha256'], 'model_receipt_sha256': config['model_receipt']['sha256'],
        'expected_base_sha256': config['expected_base_sha256'], 'base_parameters': config['base_parameters'],
        'B2_measured_base_receipt_sha256': sha(measured_path), 'base_hash_measured_in_this_scope': 'base_hash' in spatial,
        'historical_cache_binding_sha256': spatial.get('cache_binding_sha256'),
        'time_adapter_enabled': False, 'temporal_reuse_permitted': False}


def helpers():
    import train_student as student
    student.helper_paths(RUN)
    import common as old
    import frame_contract as frames
    import production as source_production
    # These adapters belong only to this process/new recipe; frozen Z files are unchanged.
    source_production.select_frames = select_native_frames
    source_production.field_frames = native_field_frames
    from source_color import authorized_source, ColorNativeReader
    original_reader = source_production.OrdinalReader
    class RegisteredReader:
        def __init__(self, item, clock):
            self.reader = ColorNativeReader(item, clock) if authorized_source(item['source_sha256']) else original_reader(item, clock)
        def get(self, index): return self.reader.get(index)
        def close(self): return self.reader.close()
    source_production.OrdinalReader = RegisteredReader
    return student, old, frames, source_production


def raw_window_bounds(arrays, start, end):
    tick = Fraction(arrays['raw_time_base'])
    origin = arrays['raw_first_pts_ticks'] * tick
    return float(origin + Fraction(str(start))), float(origin + Fraction(str(end)))


def native_field_frames(manifest, clocks):
    result = []
    for item in manifest['records']:
        clock = clocks[item['video_id']]
        points = [float(p) for p in clock['pts']]
        first = bisect_left(points, item['scope_start_sec'])
        stop = bisect_left(points, item['scope_end_sec'])
        for ordinal in range(first, stop):
            result.append(dict(video_id=item['video_id'], source_frame=ordinal,
                source_path=item['source_path'], source_width=item['width'], source_height=item['height'],
                source_n_frames=item['n_frames'], fps=item['fps_num'] / item['fps_den'],
                target_ratio_wh=item['targetRatioWH']))
    return result


def select_native_frames(manifest, temporal, clocks):
    """T uses actual PTS in every branch; nominal FPS never decides a boundary."""
    import frame_contract as frames
    from contracts import validate_segments
    metadata = {r['video_id']: r for r in manifest['records']}
    predictions = {r.get('video_id'): r for r in temporal}
    require(len(metadata) == len(manifest['records']) and len(predictions) == len(temporal) and
            set(predictions) == set(metadata) == set(clocks), 'T temporal/source/clock denominator differs')
    result = []
    for video_id in sorted(metadata):
        item, record, clock = metadata[video_id], predictions[video_id], clocks[video_id]
        fps = item['fps_num'] / item['fps_den']
