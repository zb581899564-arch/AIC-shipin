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
