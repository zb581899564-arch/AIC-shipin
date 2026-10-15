# GPU启动前的新工程版本

v1源码锁 `279d9bbe894f4135e3888e742396ecfc958ff8eb846a3f225697c43c7598fde2` 和 `pre_gpu_review_rejection_v1.json` 保留；v1真实模型调用0。六源已成功的 native64 准备与CPU processor证明移交，不重复顺序解码或CPU准备。

新入口 infer_v2.py，new contract_v2.py 和 cpu_probe_v2.py：搬入CUDA后将全部实际tensor复制回CPU计算形状/dtype/SHA，与CPU预验逐项等值，才开始模型调用；交集超过五段或任何正区间没有实际原生帧即停止，绝不裁段或跨空隙合并；用Fraction完成上下文偏移与求交，再检查float结果与精确结果的全源原生membership相同。

生成前记录BEGIN_MODEL_CALL及最多12预算；raw写入后严格核token/score等长和有限、原grammar/parser、原生realizability。任何失败回执保留已开始分母。固定 case 集合 T01–T06；实际旧B基座SHA、8,767,123,696基座参数、288保存LoRA tensor等值、启用状态、LoRA SHA与完整8,782,459,120参数逐项确认。

本批六源的完整原生PTS表实时核到首PTS全部为0，原30秒域终点均小于各源最后实际PTS；新入口在模型加载前再次检查该关系。这是本批事实，不能假设所有未来视频均从0开始。

同一原B提示与新拒绝/精修提示、候选映射/观察范围、参考门失败、最多12调用和机制损害判据均保持；没有改科学配方、扩充样本或把未知改为普通。质量准入仍失败，新版本只是有限事实机制诊断的工程修复。独立CPU重放额外核GPU等值回执、真实输出token/score分母及原生帧存在性。
