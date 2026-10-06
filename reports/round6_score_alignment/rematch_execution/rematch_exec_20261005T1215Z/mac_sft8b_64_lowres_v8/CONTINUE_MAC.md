# Mac低内存64帧方向 v8

当前唯一运行目录：`/Users/choubk/codex-workspace/projects/aic-video/mac_sft8b_64_lowres_20261006T0748Z`。环境复用只读v1 `env/bin/python`，全部命令经Mac根 `bin/run`。源码锁 `6d42f4768e542c13c7c5d72f988c3dc84970e2a5edc0b53f2963cccc4445d9fa`（33文件）。历史控制器PID79459须实时查活，不重复launcher、不编辑运行中绑定代码。

查询 `status_mac.py`、`controller/pipeline_latest.json` 和实际 `probe_01/progress.json` / `full_01/progress.json`。真实完成计数以backward/update为准，PID不是训练成功证据。探针固定3updates/48microbatches；有限连通梯度、真实LoRA变化、冻结字节、adapter重载、实测峰值不超过live recommended和共享容量门都通过才自动从冷基座新LoRA完整5epochs/3620microbatches/227updates。完整时限由实测探针成本登记。任何失败STOP，不换配置重开同一次run。

128帧虽有真实更新，最终v7采样56.59GiB超过live建议51.84GiB，按用户“支撑不起128帧就换方向”改独立64帧低分辨率区间SFT。固定8B总参数8,782,459,120、704train/724正窗口、r16/lr5e-5/seed20261006/5轮保持；显式视频处理每帧<=32768像素，不是Linux原实际视频分辨率。保留局部FP32 DeepStack索引、严格feature/token掩码、每样本缓存释放和测试后RNG恢复修复。UNKNOWN不造负例，C/BCE仍STOP，不承诺低分辨率提分。

最终收集controller/probe_resource、full_resource、pipeline_completion，probe/full train_report及adapter，双端核SHA。Mac账本追加，不改Linux历史7200秒偏移和在跑64帧源锁。当前接续仅到训练工程验收，不自动dev/confirm/比赛推理/封包/上传；完整训练通过后按固定弱开发协议再比较。Linux传输必须经Mac，唯一工作根/共享锁/动态资源/合计80GiB保持。
