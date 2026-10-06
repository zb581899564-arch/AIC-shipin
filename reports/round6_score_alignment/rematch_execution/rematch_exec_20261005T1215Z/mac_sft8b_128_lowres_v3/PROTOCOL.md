# Mac 128 帧低分辨率独立版本 v2

用户授权：去修复内存问题，如果mac支撑不起128帧，那你就换个微调方向。

v1 已在首次语言注意力 forward 内存不足，0 次 backward/optimizer update，保留其全部锁定源码和失败记录。v2 使用新目录、新源锁、新探针和新 adapter；Linux 正在运行的冻结实验保持原样。

具体修复：AutoProcessor 的 min_pixels/max_pixels 没有约束 Qwen3-VL 的视频路径。v2 通过 videos_kwargs.size 明确限制整个视频的像素总量：longest_edge = 实际采样帧数 * 32768，shortest_edge = 实际采样帧数 * 1024。每次 processor 调用重新建立参数字典，明确传入 video_metadata、do_sample_frames=False 和 return_metadata=True，避免嵌套参数被 pop 后第二次调用失去采样/时间戳合同。处理后检查每帧 grid_h * grid_w * patch_size² <= 32768，序列 <= 6144；禁止截断输入来通过。

这是以空间细节换取时间密度的输入方案。不能声称是严格的原实际像素预算四分之一对照：原 max_pixels 只作用于图像，原视频实际尺寸取决于视频处理器配置。CPU 无损合成 320x240 样例在同样 128 帧上，原视频设置 5770 token，新设置 2186 token、24576 像素/帧；时间戳、源序号和监督目标一致。此数据只证明处理链路，不证明比赛质量或真实训练内存峰值。

保持 704 个训练视频、602 来源组、724 个已知正例窗口、128 帧均匀源序号、assistant-only 区间 JSON SFT。UNKNOWN 空窗口不作负例；正式 C/BCE 数据门仍关闭。r16、alpha32、dropout0.05、lr5e-5、seed20261006、5 epochs、grad_accum16、3620 microbatches/227 updates 均保持。学习率与轮数由执行主控选择，沿用当前冻结版本，不声称网页讨论共同确定或已证明最优。冻结基座/视觉，仅 144 个语言 q/k/v/o 模块的 LoRA；总参数 8,782,459,120。

复用 v1 目录内已核验的模型、704 份媒体和固定环境，仅用明确绝对路径，不复制或建立链接。所有新文件、缓存、日志、训练产物均在 Mac 唯一工作根内，经 bin/run 启动。不开隐式 CPU fallback，不提高 MPS 上限，不修改系统或第三方 attention 内核。

先跑固定 20 窗口、48 microbatches、3 optimizer updates 的真实探针（最长10800秒）。记录每次 forward/backward 的 MPS driver/current/RSS 内存与真实 seq/grid；要求有限且连通的 LoRA 梯度、权重发生更新、冻结基座逐字节一致、adapter 重载一致及峰值不超过 MPS recommended memory。通过才从冷基座重新启动完整 5 epochs，不能沿用探针 adapter。完整耗时上限依据探针实测 wall/48*3620*1.75+probe_wall 登记。

共享 GPU 锁、外部计算冲突检查、Mac 工作根与 Linux 实测工作占用加两端预计产物的合计 80 GiB 边界保持。仅停止本次新建子进程组，失败保存证据并停止接续。若真实 128 帧仍无法完成，则另登记 64 帧等新方向，不静默回退。探针通过仅表示工程可训练，完整训练通过仍待非测试质量评估；不自动做比赛测试推理、打包或上传。

GPU 时间累计无限制，实际耗时追加 Mac 账本；Linux 历史 7200 秒偏移和账本不变。


## 控制器工程修正 v3

v2 首次启动15:15:34，在15.434秒后被自身外部计算守卫停止，exit -15、0 backward/0 update，未到 forward，因此不表示128帧低分辨率再次OOM。旧守卫只按命令行路径排除主训练进程，未排除其Python辅助后代；日志出现 multiprocessing.resource_tracker 清理警告。新v3以正在执行的控制器PID为根，按ps的PPID闭包识别本任务子孙，外部独立Python仍拒绝；控制器失败receipt保留最后资源快照。以合成多层进程树验证辅助后代排除与独立进程拒绝。保持同一科学输入/训练参数，重新冷启动独立probe/full目录，不回写v2源码锁或失败日志。
