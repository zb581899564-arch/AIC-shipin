# 原生局部注意力122范围：CPU已过，尚无GPU/训练/生产准入

依据：117真实一致重命名显示字母依赖；119/120直接视觉查询解决编码问题，但固定首发布者完整25窗仍缺乏窗内排序。新单因素固定为查询可见性：保留该原生时间组的视觉KV及全部非视觉context，遮挡其他31组视觉KV；全局前缀仍完整且只读。每查询的视觉token、Question词、位置、提示词、模型权重、原生cells全部不变。

121已完成实际HF/完整梯度与独立4D mask参考、FP64数学/等变和25个真实prefix mask的CPU检查。准备文件为localized_visual121.py、localized_visual121_cpu.py，权威ROOT/localized_visual121_CPU/completion.json，所有mask在Linux已冻结，不要重生成或重跑121。

下一先核现有官方23日直连页面的时效、仅有变化才重读更新内容/PDF，不因旧正文快照假设最新通知不变。然后新建一个明确122协议/entry/源码-输入-参数/费用/实际资源锁：完整同一ESA25窗，不选窗口；旧120unmasked控制和全部25prefix/ASR/processor/native QA采用，只有新attention operator首次执行。不运行unmasked分支，物理新模型计算须如实计费，前缀KV是未保留的临时内部激活，不能把新策略内部前向说成零推理。

建议新固定GPU预算最多800秒(须登记后才启动)，原Goal当前20965.323006/43200保持。新profile不是扩119原1800或恢复旧105；未来6000开发/8500确认/6000生产条件上限合计仍约42265秒，均非准入。原截止23日20:00(+08)不延长。

可复用119_runtime.prefix和choose实际路径，在choose外包localized_visual121.localized_kernel(该case121已验收mask.cuda())。旧choose的attention_witness会采集新的masked首层真实QKV/输出；须在新输出manifest额外绑定实际visibility矩阵/CPU ref及数据流，不能使用旧unmasked_attention的CPU期望。

新的独立CPU审查可复用119的validate_features/native_check/quantized_check；attention参考必须改为121.reference(实际保存首/末两分支的visibility[0,31])。保持原dtype两ULP+2e-6和pool误差门，不能事后调。所有新输出和原生mask在读fit标签前冻结；旧控制同mask指标采用。

正确和固定局部移位都要报告全来源/窗内AUC、F1、覆盖及相对unmasked差异，行别名必须同时移位visual pointer和visibility，明确不是额外生成。首次GPU前固定“清楚的局部信息”的判据，不能继续仅源级AUC高于.5就启动长训。仍只有一个已曝光fit来源，不称独立确认；是否原模型已有收益或需fresh原TIME克隆训练必须另作准入。新候选始终需完整2开发实际40.48强控制、真实整段内容错位、冻结后4原确认、全426工程交付。

不得加载失败105或85权重、调提示/遮挡范围/阈值以凑通过、看测试内容/GT选规则、给摘要未选贴普通标签、联系作者/其他聊天、新定时或自动提交。所有新full临时witness先注册容量和退休规则，首次CPU后才退休；原成功/raw/费用和全部基线依赖保留。
