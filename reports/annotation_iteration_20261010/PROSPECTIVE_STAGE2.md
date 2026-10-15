# 研究门之后的实际选择器投入门

新增门仅用于第二阶段投入，第一阶段原三条件和训练配方不改。此文件写入时尚未产生本轮新89行dev预测，也未读取任何新dev结果。

阈值已只从训练39源固定网格human scores的nearest-rank80分位冻结：scores_x20>=49，允许空。绝非每视频topk。15%只用于排序诊断。固定将每个2秒中点预测赋给同格全部native ordinals，这是插值假设，不称真实事件边界。

在完整9源原人类向量下，按human mean>=3定义明确标明的TVSum代理二元参考（不是AIC金标），评价扩段后的macro F、低分误选、空源和选中率，逐源报告。

仅第一阶段研究门和视觉依赖门均通过，且实际选择器macro代理F严格优于同输入同grammar基座、所有human native域完整、全dev合法，才投入非测试8实际pipeline。任何失败保留，不依据dev改阈值或换checkpoint，不冒称旧B native pipeline已被打败。

bootstrap可能跨0，要说明弱证据；源数9不足可靠官方提分推断。non-test8只验证实际输入/native时间/合法空/裁剪源场衔接，不能充当无标签质量金标。完整426只作为用户接受风险的竞争试验，在本轮授权下仅一次。

原B adapter在新imagescore prompt下的诊断结果不等于原B production pipeline成绩。最终候选如生成则明确新image score selector、原空间8B场、共享base计一次、实际新adapter参数、无旧timeadapter被加载。
