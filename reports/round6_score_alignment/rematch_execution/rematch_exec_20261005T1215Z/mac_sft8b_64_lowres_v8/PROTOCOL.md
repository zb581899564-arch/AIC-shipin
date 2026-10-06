# Mac独立8B低内存64帧方向 v8

用户授权：去修复内存问题，如果mac支撑不起128帧，那你就换个微调方向。

128帧已通过真实反向与首步LoRA更新，但修复视频像素控制/MPS索引/占位掩码/缓存之后，v7仍在27个完成backward内采样driver峰值57946.92MiB（56.59GiB），超出当时live recommended53084.667MiB（51.84GiB）。主控仅停止登记的本任务训练子进程组，完整失败/更新/账本保留，未放行full。按用户授权改变方向；不在原运行里改帧数，不放宽内存门。

v8是低内存的区间JSON SFT：固定8B基座、最多64个均匀源帧、每帧实际视频处理像素<=32768、max_sequence6144。保留704train/602组/724已知正例窗口、r16/alpha32/dropout0.05/lr5e-5/seed20261006、5epochs/grad_accum16/3620microbatches/227updates、最后4个microbatch按4归一化。BF16基座、FP32语言LoRA、冻结视觉和基座；实际总参数8,782,459,120。UNKNOWN不造负例，C正式BCE门保持STOP。学习率和轮数由主控执行时选择，保持既有设置，没有宣称网页共同裁定或最优。

科学变化是减少时间采样并限制空间细节；与Linux相比还包含硬件/解码/视频实际处理预算的差异，不能单独归因或承诺提分。Linux当前64帧原完整训练不动。另建目录、源码锁、probe/full及adapter，冷基座新LoRA，不复用失败探针adapter。

已实现的工程修复保留：明确videos_kwargs.size总预算n_sampled*32768/minn_sampled*1024，metadata/no_resampling，每次新建嵌套kwargs；CPU核验源序号/PTS/时间文本/网格/目标。实例级DeepStack索引加法转FP32后转回原BF16；占位符校验严格token数=feature行数且hidden维度相等，返回同值contiguous掩码；CPU/MPS前向/梯度/掩码/错形状拒绝5项测试。每microbatch完成backward后同步并释放空闲MPS缓存，记录释放计数和释放前后实际峰值；不更改报告低估峰值。测试后恢复全部RNG为20261006。不改安装库、模型权重或系统，不提高MPS上限，不隐式CPU fallback。

先固定20窗口/48microbatches/3updates真实探针，10800秒上限；有限连通梯度、真实LoRA变化、基座/视觉全字节冻结、adapter重载、live recommended memory与共享资源/80GiB合计占用全部通过，才从冷基座登记完整5epochs。全量壁钟上限按probe_wall/48*3620*1.75+probe_wall实测登记，保持无限累计GPU但追加账本。失败STOP，不静默删样本/改阈值/换帧数。

复用Mac唯一工作根内已验证模型/704视频/固定环境的绝对路径，不再复制权重/媒体或建链接。全部任务经bin/run，缓存/日志/产物限定工作根；Linux传输经Mac，账本7200秒初始偏移不变。不自动开发评测、测试推理、封包或上传。工程通过仍不是官方质量结果。
