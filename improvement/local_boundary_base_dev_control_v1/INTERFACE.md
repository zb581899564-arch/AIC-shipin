# BASE37 唯一主控（代码交付，未部署或启动）

代码目标：`CAMPAIGN/local_boundary_base_dev_control_v1/code/`（5py）。
配对 driver：`CAMPAIGN/local_boundary_base_dev_v1/code/`（4py，使用修订02的bd_io）。
主控只负责 dev20/40名义端点、37实际调用、3原点 typed skip；不调用 TIME、prepare、
输入 encoder 或媒体 decoder，不评价或选择角色，不封包。

主控部署/核SHA后首次冻结
`CAMPAIGN/local_boundary_base_dev_control_v1/control_scope_01.json`：

```json
{
  "schema": "BASE37_TIME_THEN_BASE_UNIQUE_CONTROLLER_V1",
  "status": "FROZEN_BASE37_CONTROLLER_WAIT_TIME_NATURAL_AND_FIRST_REPLAY_V1",
  "role": "dev",
  "base_root": "CAMPAIGN/local_boundary_base_dev_v1",
  "source_root": "CAMPAIGN/local_boundary_v4/dev",
  "events": 20,
  "nominal_endpoints": 40,
  "actionable_requests": 37,
  "structural_skips": 3,
  "actual_model_call_budget": 37,
  "gpu_job_name": "aic20h_charades_dev37_base_boundary_20261014_v1",
  "max_gpu_seconds": 1500,
  "planned_output_bytes": 8388608,
  "new_input_processor_encodes": 0,
  "new_media_decodes": 0,
  "optimizer_updates": 0,
  "deadline": "2026-10-14T11:56:40Z",
  "deadline_ref": {"path": "CAMPAIGN/local_boundary_v4/dev/protocol.json", "sha256": "ACTUAL_SHA"},
  "official_rule_check_ref": {"path": "CAMPAIGN/local_boundary_v4/dev/official_rule_check.json", "sha256": "ACTUAL_SHA"},
  "TIME_controller_launch_ref": {"path": "CAMPAIGN/local_boundary_v4/dev/controller_launch_01.json", "sha256": "ACTUAL_SHA"},
  "controller_code_files": {"ABSOLUTE_DEPLOYED_CONTROL_PY": "ACTUAL_SHA"},
  "driver_code_files": {"ABSOLUTE_DEPLOYED_DRIVER_PY": "ACTUAL_SHA"},
  "no_successful_TIME_or_input_stage_repeat": true,
  "quality_selection_or_production_by_controller": false
}
```

以上 `CAMPAIGN` 必须展开为
`/home/inspur/aic_video_work/twenty_hour_five_20261014_v1`，SHA必须从已核部署文件取得，
两个 code 文件表须包含全部5/4 py。deadline 必须与真实 TIME protocol 一致；不另填新时段。
`cc_common.own_code_files()` 产生控制器表；driver 的 `bd_io.own_code_files()` 产生4py表。

唯一 CLI（由主控实际启动，父 CUDA0）：

```text
CUDA_VISIBLE_DEVICES=0 /home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python -B -u CAMPAIGN/local_boundary_base_dev_control_v1/code/controller.py --scope CAMPAIGN/local_boundary_base_dev_control_v1/control_scope_01.json
```

controller 对 TIME terminal 目录建立本进程 inotify 文件事件等待；等待时不轮询 PID/GPU、
不重复读取大 source bundle。create-x JSON 写入未关闭时不误报失败；终态 close-write 后严格读回。
TIME 任一真实 failure 直接停止。只有自然 `TIME/chain_01/completion.json`、
唯一 shared ledger completed/exit0 与37 first-input/output replays通过后，CPU注册子进程才首次
建立 BASE protocol/current-rule字节副本/registration/source_lock/gpu_admission。
所有必需 source/input/nativeavailability/knownsep/driver4py/controller5py/实际wrapper均入锁。
旧 tensor/RGB 只核引用与stat，独立输入证明引用 TIME首次成功；新 GPU 子自身核旧cache实际字节及输入。

随后另一个 CUDA空 CPU子进程调用 consuming `bd_io.admitted()` 做绑定检查，不 encode/decode/load旧tensor。
通过后唯一 chain 使用原 shared `gpu_run.py`，name固定、max1500s、output8MiB、queue900s。
启动前读实际 hostname/CPU/GPU进程argv/RAM/disk与已完成TIME峰值，保留 Linux resource receipt；
没有固定RAM/显存GiB阈值，不终止外部或Java作业。新输出重放 CPU 子仅清空自身CUDA，父保持0。

终态入口：`BASE/controller_01/completion.json`、`BASE/chain_01/completion.json`、
`BASE/gpu_01/completion.json`、`BASE/replay_01/completion.json`、`BASE/boundary_prediction_export.json`。
每阶段 launch/exit/log 保留。任何失败都无自动重启、重注册、whole-chain retry；成功/raw/partial保持，
后续只能由主控明确注册独立剩余恢复。结果仍行为/动作端点proxy，SCI=false；确认及角色选择交root metric08。

Linux stdin 内存代码纯检查通过：5py AST、37/1500/8MiB和code锁错误拒绝、Z deadline、父CUDA不变、
TIME缺终态等待/36次或failure拒绝、部分JSON需close、inotify而非live轮询、唯一wrapper argv、
新准入无tensor/RGB/processor。未部署生产代码、未运行实际source_bundle/控制器/GPU。
