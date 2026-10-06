# Mac 8B 独立版本接续

唯一任务目录：`/Users/choubk/codex-workspace/projects/aic-video/mac_sft8b_20261006T054133Z`。

登记 2026-10-06 14:10（UTC+8）：31 项代码/输入/环境证据已在 Mac 逐 SHA 校验，锁 SHA `5b80284ffdd372725ac02088098f7378d63ab013698d71aa353297a48f327257`。真实 CPU 验收 8/8，继续条件门 Windows/Mac 各 3/3。主控 `finish_mac.py` 已登记启动，历史 PID 74835；14:10:50 后实查存活，阶段 `WAITING_REGISTERED_MAC_ASSET_TRANSFER`，传输 5.32/25.60 GB。Mac 正式训练尚未启动，不能把后台入口 PID 写成开训成功。

只读查询：

```powershell
ssh macmini /Users/choubk/codex-workspace/bin/run /Users/choubk/codex-workspace/projects/aic-video/mac_sft8b_20261006T054133Z/env/bin/python -B /Users/choubk/codex-workspace/projects/aic-video/mac_sft8b_20261006T054133Z/status_mac.py
```

查看阶段 receipt：`controller/pipeline_latest.json`、`controller/pipeline_completion.json`、`controller/probe_resource.json` / `full_resource.json`。真实梯度/更新读 `probe_01/progress.json` 或 `full_01/progress.json`；最终验收读对应 `train_report.json`。Mac 实际计算记录追加至工作根 `runs/aic_video_mac_gpu_ledger.jsonl`；不会改写 Linux 账本。

完整流程为：资产全部哈希通过 → CPU 检查 → 3 更新 / 48 有效样本实探针 → 冻结与重载通过、实际资源够用 → 全新基座/LoRA 的完整 5 轮训练。探针上限 3 小时；全量单次 wall bound 从实测探针成本登记，暂无可信训练 ETA。

传输：719 项（15 模型文件、704 原 train 来源），25,599,530,028 字节。最初经 Windows 的桥接已因连接结束 STOP，失败与 64 MiB 部分文件保留；当前通过 Linux–Mac Tailscale 直接流式传输，不恢复不完整文件。临时发送器仅允许 Mac 地址与 capability，不更改 SSH/Tailscale/代理/服务设置，结束或截止后关闭自有进程。`http_transport_config.json` 是临时传输凭据，不打印、引用到报告或推送到代码仓库。

任何 STOP：先保留失败 receipt、日志、已运行步数和已生成产物，按实际原因注册新版本。不要重开同名 launcher、手工启动重复训练、编辑绑定源码/清单或把失败样本删除后继续。不要终止外部任务。Linux `temporal_sft8b_full_v1` 是独立在跑的冻结实验。

训练完成只是工程里程碑。当前入口不运行 dev/confirm/复赛测试、不做联合空间推理、不封包、不上传；下一阶段由主控按固定开发协议登记。
