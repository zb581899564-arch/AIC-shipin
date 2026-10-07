# v2：自然时间网格与可采样帧区分

**根因已在真实 Linux 来源只读复现，修复只位于 supervision_v2。**旧 `supervision/` 源码和 `selection_01` 失败记录保持原样，教师合同没有修改。新完整 128 train + 32 dev 选择由主控登记并运行 `selection_02`，本代理不重开旧 run、不启动模型/下载/训练。

## 真实失败证据

第三个冻结训练来源 `2dKTLCv__ds` 的实际文件：

`/home/inspur/aic_video_data/videos/2/2dKTLCv__ds_210.0_360.0.mp4`

文件 SHA `29e851cd72ab5a88d46cf83700ad8ddeb0b6af034e0b768a268c3b03e05e94a2`，17,307,794 bytes，3,597 帧；PTS sequence SHA `ab4b5cce254606c5e5fa73b380ec432357b2ce58da9dd0f7fcd9befb49030a8a`。首 PTS=0，末 PTS=149.983167，末帧真实 `pkt_duration_time`=0.041708，实际末端=150.024875。

原 30 秒自然网格逐格的新呈现帧数为 `[720,719,719,720,719,0]`。最后 `[150,150.024875)` 是末帧显示持续时间跨过边界后的时钟尾格，**没有新帧的呈现 PTS**。v1 的第三个来源按尾部 stratum 选择此格，导致 `spaced_indices` 拒绝空 eligible frame range。不是非零 PTS 原点，也不是视频缺失。

## 精确差异

- 保留原 seed、train/dev SHA、来源排序、每组一个来源和原始 30 秒非重叠网格；实际 source exclusive endpoint 仍为 150.024875，不裁成 150 秒。
- 新 `audit_grid()` 留存所有格子的原始范围、真实帧 ordinal 范围与计数。全部源 PTS 必须被原网格恰好覆盖一次。
- 来源开头/内部/结尾 stratum 在**有真实呈现帧的格子**中选择；无新 PTS 的格子保留在证据中，明确不可独立采样，不生成 frame，也不标无高光。
- 本失败来源的尾部选择变为 ordinal4 的 `[120,150)`，包含末帧真实 PTS 149.983167。显示到 150.024875 的额外 0.024875 秒在 metadata 中单列为 `terminal_display_remainder_outside_last_pts_cell_sec`；不能把这段独立称为已观察窗口或负样本。
- 有真实新 PTS 的短尾窗仍照常保留。内部无新 PTS 的格子也显式留档，不能偷偷填帧。任何时钟缺失、不递增、实际终点不一致或不存在真实候选仍 STOP。
- Window 的兼容 schema 仍为 `aic_complete_window_selection_v1`，所以原教师窗口校验接口不变；`window_geometry` 明确改为 `30S_NONOVERLAP_FULL_SOURCE_GRID_SELECT_NONEMPTY_PTS_V2`。Receipt schema 为 v2，并登记该选择规则差异。
- 失败时 v2 另存已完成的 partial clock/windows 和具体 failed source，均标未标注、非全量通过，不覆盖历史失败。

这只是时间网格到实际帧采样的工程修复。所有选中记录仍为 `UNLABELLED`，不意味着完成语义监督或完整观看全部来源内容；原 32B 容量 STOP 与 T 未准入边界保持。

## 独立新 run 的准确 CLI

依赖仅 Python stdlib 和既有 ffprobe；没有新增环境依赖。主控先完成实时资源/传输准入，并使用新输出目录：

```bash
PY=/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python
R7=/home/inspur/aic_video_work/round6_score_alignment/r7_temporal_pool/round7_temporal_pool_20260921T090903Z/inputs
SUP=/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/next_round_v1/supervision_v2
$PY -B "$SUP/test_selector_cpu.py" --receipt "$SUP/cpu_linux_result_01.json"
$PY -B "$SUP/select_windows.py" --train-manifest "$R7/train_temporal.jsonl" --dev-manifest "$R7/dev_temporal.jsonl" --ffprobe /home/inspur/anaconda3/envs/Andy/bin/ffprobe --tier first --out-dir "$SUP/selection_02"
```

成功必须以 `selection_02/selection_receipt.json` 的 `PASS_CPU_SELECTION_UNLABELLED`、train128/dev32、全来源实际 PTS 网格覆盖、输出 SHA 为准。启动/单个失败来源的探针通过不能当全量验收。真实 aggregate 证据见 `failure_audit_01.json`，本地 CPU 合同结果见 `cpu_contract_result_01.json`。
