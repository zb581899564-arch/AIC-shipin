# Mac64帧完整探针及正式开训验收

## Mac替代64帧版本已正式开训（2026-10-06 15:58，UTC+8）

内存修复与改方向完成：128帧v7有真实更新但工作集56.59GiB超过live建议51.84GiB，独立停止并保留证据；按用户授权改为8B/最多64帧/显式每帧<=32768像素的低内存B区间SFT。v8真实探针完整3更新/48backward通过，MPS采样峰值24.99GiB，有限连通梯度/实际LoRA变化、基座与视觉全字节冻结、adapter重载一致均PASS。新full已从冷基座新LoRA实际完成24/3620次backward、1/227更新，模型总参数8,782,459,120；完整训练尚未完成。保持704train/724窗口/r16/lr5e-5/seed20261006/5epochs，不造UNKNOWN负类，C/BCE仍STOP。MPS局部FP32索引、strict feature/token contiguous掩码、逐样本缓存释放与测试后恢复RNG修复保留，不改库/系统/内存上限、不CPU fallback。

当前入口 `mac_sft8b_64_lowres_v8/CONTINUE_MAC.md`，Mac唯一目录 `/Users/choubk/codex-workspace/projects/aic-video/mac_sft8b_64_lowres_20261006T0748Z`；源码锁 `6d42f4768e542c13c7c5d72f988c3dc84970e2a5edc0b53f2963cccc4445d9fa`。禁止重开launcher或编辑运行中33个绑定文件。controller/full_admission.json按341.4816秒真实探针训练成本登记全量止时，实际用量追加账本。查full_01/progress.json、最终train_report/controller/full_resource与pipeline_completion，PID需实时核验。启动receipt为 `controller/mac64_full_training_start_01.json`。

Linux原训练不动，最新183/227更新、2940/3620有效，无失败。当前两机后续仅机器计算；Mac接续不自动开发评测/比赛推理/空间封包/上传，8B质量与可提交包仍待后续门。共享锁、实时冲突/动态容量、合计80GiB、Mac唯一根及Linux文件传输经Mac保持；累计GPU无限但历史账本7200秒偏移不改。下方各等待/失败快照仅为历史。
