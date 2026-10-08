# V10真实重叠边界生成约束修复

v9真实32B视觉接口8/8通过，但第一条非测试探针返回嵌套重叠，被原validator正确拒绝；原HTTP/raw/STOP保持。其真实13675输入token、200输出token无截断，不是下载或装载失败。旧schema仅独立ID enum，生成语言遗漏start<end及跨片段顺序/非重叠关系。

新v10以有限状态GBNF在生成时约束合法原生边界序列：1到5段全部合法选择仍可表达，段内start<end、每段含真实提供帧，下一start>=上一end。schema、提示词、高光标准、原validator和160/24选择原字节保持；直接grammar为单独登记的生成配方修复，不后处理旧重叠输出，不裁段/合并/排序/造空。原事前登记160/24保持，其中已有一条工程失败探针被观察过，不冒充全新未见24；不重新挑样本。两条真实重输入探针在新目录真实生成，旧无效响应不复用为标签。视觉inference入口新增grammar分支，重新测试8个合成接口case有工程必要性，不当作新标签或新科学通过。

先固定运行时CPU：原raw必须拒绝；合法1..5段/贴边/全端点/NO/UNKNOWN及非法重叠倒序/反向/无帧/多于5段验收，然后独立锁/单次launcher。真实24/盲审核/分层UNKNOWN/2..4更新前缀/候选0/开发及NONTEST8/426strict保持下述协议。科学门失败仍按B/C自主准备匹配对照，不无限换提示。

# V9工程修复接续

v8已在B2缓存回执字段status/stage处STOP，GPU调用0/标签0/T更新0，480冻结文件与STOP保持。v9修实际B2回执适配，补固定11strict键/状态/全分母/终态内部SHA与当前输入及基座绑定，并做真实CPU缓存交接验收；沿用同配方/同输入的原160/24选择原字节，不重复选择或模型生成。当前目录与source_lock/registration为准；下面v8科学协议全部保持。

# 唯一新增接续入口：teacher_student_autopilot_v10

先读最新AGENTS/STATUS/本PROTOCOL与source_lock/registration，核真实主机、完整命令/父子PGID/资源/共享锁。历史PID不是存活证据，CPU核SHA/顺序解码/共享队列可合法等待。

登记后一次launch.py启动 controller：八syntheticvisual（含64帧正反序）→真freshheavyprobe→新24盲标注/逐条审核→完整窗口弱监督准入时160/训练最多3epochs与earlyprefix2..4/同optimizer→候选0开发→NONTEST8→426/strictZIP。工程错误保留并独立版本修复，冻结源码不改、不重开已有launcher。质量不足由route_decision指定B边界证据或C全局局部非测试对照，监控Agent自行继续；不再向旧12盲换prompt循环。

读visual_probe_01/completion、teacher_01/probe/每窗done/failure/raw/semantic_admission、pilot_01全部24分母/route、student_01更新/prefix/开发/完成、nontest/rematch全stage+strict、所有resource/queue。记录轻量比较快照。中间正常/修复静默写项目，最终完整ZIP再汇报；新大流量许可仍必要。
