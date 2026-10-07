# B2：已微调 Linux B8B 的原生时钟与全源空间场封包

用户2026-10-08完全授权自主裁决、修复和接续到最终一个ZIP，阶段静默。独立版本保留已评分37.63的B最终LoRA，不增加训练更新。固定基座/adapter与原训练5epochs、227updates、r16/lr5e-5保持。时间启用B adapter，空间用相同8B原生基座，独特逻辑参数8,782,459,120；加载实际288个adapter张量与保存值、完整冻结基座字节均核验。37.63只绑定旧包，新B2官网分未知。

32B教师及所有旧尝试保持科学STOP与原raw。context v3真实8请求、3正支持/唯一NO被拒绝，没有获得支持的真实空例；有事实性时间范围误判且仍有语义争议。不能翻转审核/伪造空例/放宽门开训T。此次B2明确不是新T或新教师微调，不重复同配方盲试，不延长旧LoRA。

生产保留B原1–5段提示、greedy256token/受约束JSON、64帧HD及实际视频size4096/25165824、推理16384界。独立登记的变化为全部格式分支使用实际源PTS、窗口内整数floor端点均匀抽样、顺序PyAV RGB24、精确native processor时钟，输出端点可无损表达至18位小数；物理帧可行性使用全部源PTS，不只64样本。不截断/降帧/猜时间单位/事后修补模型数值；任何正区间无实际帧或失败STOP，不转空。训练原8192协议不回写。

空间保留同8B原生基座、原主体中心提示/greedy128token及整数0..1000合同、原最大合法框/HSV .35/GRAY .18/max_gap8镜头锚点和镜头内线性插值。空间源场在完整自然scope上计算后才取新B选择帧，不让选择断点改变镜头或插值。OrdinalReader分别保留CFR顺序OpenCV和已核native Decord身份；同帧pixel SHA必须与镜头阶段相等，不能fallback。时间RGB与空间BGR各自已登记源ordinal/PTS和图像转换，不声称不同解码器逐pixel相同。

旧Z时间实际没有B LoRA，521旧时间结果绝不复用。只有源manifest/registry/model、实际源field域、算法AST、依赖SHA、所有请求/pixel SHA和完整回执一致的旧全源CPU/同基座空间可原字节复用。域不一致独立重算；无法证实一致不接受。时间B2全部真实新推理，旧selected不复制。缓存成功/失败原记录不改，新增cache_binding与复用回执。复用空间保持实际旧model_calls/非测试耗时及本候选新增model_calls=0，不能把缓存叫本次新生成。

验收顺序：CPU合同/434真实元数据源与529自然窗（实际计数以回执为准）/原12目标无损回放→实际processor1/3/63/64、HD默认张量相等、全部8非测试源native/重开pixel SHA→模型/源/代码锁→真实B adapter长输入CUDA有限选择分数/全基座身份→完整NONTEST8时间/全源空间/恢复/独立strict ZIP→426/521实际B时间/全源CPU/空间/合成/独立strict ZIP。既有B开放104/96弱开发已通过，B2不训练/选参数，不重复弱评分；本次真实工程门为新输入的NONTEST8。100confirm不读，不手看比赛内容调参，不本地复刻官网分。

源码锁后单次后台launcher→控制器接续全部阶段。每阶段实查容量与共享任务，使用resource_unlimited_v1_20261007/gpu_run.py、共享GPU锁/追加账本/7200偏移，無人为RAM/VRAM/磁盘限额。空间和全量时间止时/产物预测依据同8B真实非测试测量与真实锚点/分母；单次止时是此次阶段成本登记，不是累计GPU额度。真实不足或外部GPU冲突等待/STOP，只停止自己进程组。

仅PASS_COMPLETE_426_B2_8B_ZIP_ON_LINUX及NONTEST8/426全部独立strict、ZIP真实大小/SHA/CRC、唯一predictions.jsonl/426身份通过才可提交。最终candidate_B2_8B.zip留Linux，不自动回传或AIC提交；新大流量先许可，Mac不参与。B2整体配方对旧B变化较多，工程PASS不等同质量提升，官网由用户最终提交获得。
