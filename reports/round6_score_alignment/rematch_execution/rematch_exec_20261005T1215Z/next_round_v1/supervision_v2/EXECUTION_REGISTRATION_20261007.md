# selection02 已独立一次登记，完整验收运行中

在主控追加授权后，实际核验 Mac 身份、通过唯一工作根的 `bin/run` 读取 AGENTS，并实时核两机占用。新 `supervision_v2` 通过 `scp -J macmini` 传到 Linux；Mac 没有新落盘文件，没有绕过跳板。

Linux 容量准入时工作占用 50,908,573,696 bytes；Mac 28,053,655,552 bytes。为本次 CPU 输出预留 8 MiB，满足 Linux 51 GiB 与合计 80 GiB。独立运行器 `run_selection02.py` 不加载模型，先核源码/CPU 合同，再仅执行选择器。Z 的冻结文件和旧 supervision 不变。

单次登记时间 2026-10-07 02:59:42 UTC，控制器 PID **2239360**，选择器 PID **2239364**。登记源码锁 `source_lock_02.json` SHA `c76e3482f044da2500c265b0ad1e8fbd7994cfafc56c2673b2dffdc139f9486e`；不得重开 launcher 或编辑运行绑定文件。

Linux CPU 合同 **19/19 PASS**。03:00:45 UTC 回传快照为 `CPU_SELECTING_128_TRAIN_32_DEV`、**train26/dev0**；此前 `/proc` 实查两个 PID 都存活。原失败第三来源已经通过。这个快照不是最终 128+32 验收。

回传登记和快照位于 `runtime_registration_01/`，其中 latest 是上述时点的历史快照。真正的最新状态和最终门仍在远端：

```text
/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/next_round_v1/supervision_v2/selection02_latest_01.json
/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/next_round_v1/supervision_v2/selection02_completion_01.json
/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/next_round_v1/supervision_v2/selection_02/selection_receipt.json
/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/next_round_v1/supervision_v2/selection02_controller_01.log
```

最终成功必须同时为 `PASS_CPU_SELECTION02_UNLABELLED_128_32` 和底层 `PASS_CPU_SELECTION_UNLABELLED`、train128/dev32、输出 SHA。任何失败保持 STOP 并留 partial receipts。全过程没有标签生成、模型下载、环境安装、GPU 推理或训练；32B 教师容量与 T 语义训练门保持原状。
