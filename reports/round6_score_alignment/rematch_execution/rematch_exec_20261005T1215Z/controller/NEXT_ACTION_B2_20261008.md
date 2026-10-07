# 下一实际任务：B2 已微调8B的生产对齐与完整封包

用户完全授权自主路线选择、修复并接续到一个最终ZIP，期间静默。v3已2026-10-08 01:02:48 UTC+8完整8请求结束，GPU/所属server正常退出、0工程失败：3正/1NO_HIGHLIGHT，三正弱复查支持，唯一NO被拒绝。因此没有一个获得弱复查支持的真实空例，不能从这4条诊断开训T，也不能重复已知拒绝的原配方全量。

拒绝原始回答还声称整段overview仅到119.0189秒；实际顺序native回执为4496帧、64overview、末PTS149.98316666666668，包含13张>=120秒帧。该声明与输入元数据矛盾，证明同教师弱审核不是可靠人工真值。它同时提出“家具组装重复/地毯完成”等语义争议，不能因一个可证实错误就把整个拒绝改PASS或把NO当真值。所有raw/HTTP/processor/grammar、支持/拒绝与输入SHA保持，T监督仍未准入，T更新0。

自主选择先交付B2：保留已取得37.63的Linux B最终LoRA和同8B空间基座，用已修复的生产一致原生PTS/合法坐标/完整源空间场生成一个新候选。不是新教师微调，不延长旧LoRA，不向无效监督开训。B2官方分未知，37.63仍只绑定旧B包。最终报告明确这条路线和T未训练原因，不静默冒充T结果。

## 实现与一次性启动

1. 创建独立b_score_aligned_package_v1/PROTOCOL.md、CONTINUE、config、CPU合同、source_lock和一次控制器，不改旧next_round_v1/v7/已评分包/原失败。读取最新AGENTS、真实主机/任务/资源后再动作；无需用户参与。
2. 基于next_round_v1已验原生PTS/空间场与v7的precision_helpers、native_segment_contract、cost_contract工程修复实现。全部helpers显式按新目录加载，不让sys.path/sys.modules落回旧4位parser或旧空间quota。保留B原时间提示、64帧/HD/16384生产界、greedy受约束生成；不读100confirm，不手看复赛内容调参，不复刻官网分。
3. 时间模型必须启用原B LoRA SHA8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23，空间用同基座无adapter，联合逻辑参数8782459120。next_round_v1的Z生产时间在engine.py:98实际load_model(adapter=False)，所以旧Z的521时间结果不能复用于B2。不要被Z_NATIVE8B_WITH_B_TEMPORAL_DECODING命名误导成已用了B LoRA。
4. 旧Z全源CPU镜头/锚点调度、相同基座空间缓存或其他成功物可以在身份、算法参数、registry/schema及全部关键文件逐SHA相同后原样复用；时间B2必须实际新推理。若复用不满足，不修补或拼接，独立重算。失败记录保留。
5. 使用resource_unlimited_v1_20261007/gpu_run.py和真实容量预测，完整保持共享锁、追加账本/7200offset。不使用旧51/80GiB/Mac额度。阶段空间成本以真实同8B NONTEST测量与实际锚点数登记，合法全空也要有真实同模型成本依据，不用旧4B/Mac/虚构0成本。
6. 冻结前CPU合同和真实元数据/旧目标无损回放；实际8B B LoRA重载、64帧HD/长输入CUDA有限生成/参数冻结身份验收。必要开放开发诊断采用同production输入，只读允许104/96集合，不把内部弱F1当官网分，不按其CI>0强制工程门。
7. 完整NONTEST8：实际B时间、源帧恢复、全源空间场、同帧/镜头内插值、0..1000整数合法框、失败/合法空区分、独立strict ZIP；PASS后一次426/521时间→CPU调度/可合法缓存→空间→恢复合成→独立strict ZIP。所有426分母、源身份、缺失/额外/重复、模型参数、真实ZIP大小/SHA/CRC/唯一predictions.jsonl都通过才写B2终态PASS。
8. 一次启动后实核控制器/所属wrapper/子进程命令/PGID与registration，继续每15分钟静默巡检自主修复，更新automation当前入口和实际终态条件。最终candidate_B2_8B.zip留Linux，不自动回传或官网上传；大流量仍须先许可，Mac不参与。不把新的B2状态写成PASS_AUTOPILOT_FINAL_T_ZIP_ON_LINUX。

最终只提供一个选定、真实完整验收的ZIP并汇报已做的修复、实际采用的模型与训练状态、文件路径/大小/SHA及新官方分未知。T原科学STOP和所有教师产物保存，可在此次可交付版本以后再研究可靠监督；本次不要让无法验收的标签持续阻塞可提交候选。
