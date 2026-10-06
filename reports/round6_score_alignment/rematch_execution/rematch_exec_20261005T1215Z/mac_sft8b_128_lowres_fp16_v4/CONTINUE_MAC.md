# Mac 内存修复接续

实际目录：`/Users/choubk/codex-workspace/projects/aic-video/mac_sft8b_128_lowres_fp16_20261006T0724Z`。固定环境仍复用 `/Users/choubk/codex-workspace/projects/aic-video/mac_sft8b_20261006T054133Z/env/bin/python`。所有调用经 `/Users/choubk/codex-workspace/bin/run`。

只读查询 `status_mac.py`；更详细读取 `controller/pipeline_latest.json`、`probe_01/progress.json` 或 `full_01/progress.json`、`current_example.json`。PID 必须实时核对，真实计数以已完成 backward/update 为准。

源码锁 SHA-256：`4424de75341b5249fe5be2f42b428d1e0cfea9b86fc9e75e3fffa06b32454a7c`。运行期间不编辑绑定文件，不重复 launcher。`finish_mac.py` 单次后台接续先探针3 updates/48 microbatches，再按探针成本从冷基座开始完整5epochs/227updates/3620microbatches；探针冻结/重载/梯度/容量失败则 STOP。接续不做开发评测、比赛推理、封包或上传。

v1 内存不足、v2 自身辅助进程误判失败均保留。v3 已完成首次 forward，backward 因 BF16 算子类型失败；v4 改 FP16 基座/激活，FP32 LoRA，保持低分辨率128帧输入协议。每帧实际处理像素<=32768，max_sequence6144，无截断或静默帧数回退。若真实MPS仍OOM，由总控审计后另登记64帧等独立方向，不能在本运行中直接改参数。

最终读取 `controller/pipeline_completion.json`、`controller/probe_resource.json`、`controller/full_resource.json` 与最终 `train_report.json`，核验冻结字节/adapter重载/有限梯度及训练覆盖，复制adapter前双端核SHA。Linux现有训练保持原状，只读 `temporal_sft8b_full_v1/status_full.py`。累计GPU无限制、80GiB合计占用、共享锁、Mac唯一工作根和Linux传输经Mac规则保持。

