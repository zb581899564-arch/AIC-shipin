# Local boundary V1

这是独立的新接口。旧 `human_reference` / `duration_guard` / `videoxum` / `sparse_context` 代码及成功产物只读。当前真实请求代码未部署、未运行；没有下载、真实CPU准备、模型调用、训练或封包结果。另有小量纯torch合成gzip往返检查，不使用processor、模型或媒体。

固定Linux输出根目录：`/home/inspur/aic_video_work/twenty_hour_five_20261014_v1/local_boundary_v1`。代码可部署到该目录的 `code/`。入口都必须运行在 `inspur-NP5570M5`；CPU入口只清空自己的CUDA可见性，不能在父链清空。

## 复用接口

- 原native runtime：`/home/inspur/aic_video_work/temporal_refinement_pilot_20261011/dev_01/runtime.py`，其中 `encode` / `baseline_frames` / `tensor_signature`。
- 原模型与adapter：`RUN/b_score_aligned_package_v4/config.json`、`engine.load_model`；实际模型总参数 `8782459120`，原base/adapter SHA与288张量身份均复查，optimizer始终0。
- 实际视频processor沿用 `bw_video` / `exact_pts` / `native_frames`，不采样、不截断、不按FPS拉伸。AutoProcessor的 `min/max_pixels=131072` 不是实际每帧像素声明；实际 `video_grid_thw`、`actual_pixels_per_frame`、全视频显式size及输入token以CPU证据为准。
- 输入64个不同原生帧，input最多16384 token、generation最多256 token。新prompt或实际视频网格超预算就失败，不缩帧、不截prompt后暗中继续。
- 原processor为64帧产生32个temporal grid位置，timestamp文本保留原0.1秒rounding。旧实际proof最大rounding error约0.05秒。短窗更密不代表这个文本时间精度同时改变；新CPU必须报告原生PTS与实际processor文本timestamp证据。
- 主代理使用既有共享 `gpu_run.py` 启动唯一新job。本目录没有wrapper/后台启动器。

## 输入与端点含义

每个事件必须是已独立重放通过的原B非空段，身份为 `(source_sha256, original_case_id, original_segment_index)`；注册表另给唯一 `event_id`。`original_interval_exact` 是原window起点加原B局部秒的精确十进制有理数转换，不由人工指定新边界。

每个事件固定2个请求：`event_id.start`、`event_id.end`。窗口为原端点±3秒，仅在物理源域裁到合法范围；不得为少于64帧改大窗口、补帧、重复帧或换源。按已有完整native clock的候选帧整数floor64采样，密集程度变化不代表模型定位精度已经提升。

prompt包含原case/segment、原window秒转换、窗内原端点、候选内侧方向及原候选内侧锚点；不含GT、摘要标签、音频或人工事件描述。它要求识别同候选可见内容与外侧转换，镜头切换本身不代表边界。

有限grammar仅允许：

```json
{"decision":"KEEP"}
{"decision":"UNKNOWN"}
{"decision":"REFINE","sample_index":17}
```

KEEP/UNKNOWN保留原精确端点，不删除事件。REFINE的start表示第一个纳入帧PTS；end表示最后一个纳入帧，转换为其下一真实PTS，源末帧使用已测正duration的物理末端，保持 `[start,end)`。

CPU短窗读取同时记录必要相邻帧的原duration元数据。原端点所在相邻PTS/duration或所选边界连续性未证实、缺外侧背景、index为0/63时，代码将REFINE变为有明确原因的UNKNOWN并保留原端点；模型/语法/输入/绑定失败则阻断整个阶段，不能变成UNKNOWN或空事件。起止交叉时保留两原端点并记录 `pair_conflict_preserved_original=true`，不交换它们。

## 主代理注册结构

必须先冻结protocol和当前官网规则小回执，再写本Linux根目录的 `registration.json`。此处列字段，不能把占位内容直接执行。

```json
{
  "schema":"LOCAL_BOUNDARY_NATIVE64_V1",
  "status":"FROZEN_EXTERNAL_NONTEST_LOCAL_BOUNDARY_PILOT",
  "source_scope":"EXTERNAL_NONTEST_DEVELOPMENT_ONLY",
  "validation_scope":"ONE_EVENT_INTERFACE_SMOKE",
  "selection_frozen_before_new_model_results":true,
  "existing_sources_are_exposed_development_not_new_confirmation":true,
  "model_parameters":8782459120,
  "optimizer_updates":0,
  "half_window_exact":"3",
  "frames_per_request":64,
  "endpoint_sides":["start","end"],
  "actual_model_call_budget":2,
  "download_media":false,
  "training":false,
  "protocol_path":"ABS_LINUX_BASE/PROTOCOL.md",
  "protocol_sha256":"ACTUAL_SHA256",
  "official_rule_check_path":"ABS_LINUX_BASE/official_rules_01.json",
  "official_rule_check_sha256":"ACTUAL_SHA256",
  "required_files":{"ABS_LINUX_BASE/PROTOCOL.md":"ACTUAL_SHA256","ABS_LINUX_BASE/official_rules_01.json":"ACTUAL_SHA256"},
  "events":[{
    "event_id":"DEV_001",
    "original_case_id":"H01_W000",
    "original_segment_index":0,
    "original_interval_exact":["ORIGINAL_WINDOW_PLUS_B_START","ORIGINAL_WINDOW_PLUS_B_END"],
    "clock_object_keys":["clock"],
    "reuse_rgb_inputs":[{"path":"OLD_ACCEPTED_INPUT_JSON","sha256":"ACTUAL_SHA256"}],
    "original_evidence":{
      "input":{"path":"OLD_ACCEPTED_INPUT_JSON","sha256":"ACTUAL_SHA256"},
      "cpu_proof":{"path":"OLD_CPU_PROOF_JSON","sha256":"ACTUAL_SHA256"},
      "done":{"path":"OLD_DONE_JSON","sha256":"ACTUAL_SHA256"},
      "raw":{"path":"OLD_RAW_JSON","sha256":"ACTUAL_SHA256"},
      "request":{"path":"OLD_REQUEST_JSON","sha256":"ACTUAL_SHA256"},
      "independent_replay":{"path":"OLD_REPLAY_PROOF_JSON","sha256":"ACTUAL_SHA256"},
      "clock":{"path":"OLD_COMPLETE_CLOCK_JSON","sha256":"ACTUAL_SHA256"},
      "source_separation":{"path":"OLD_SOURCE_SEPARATION_RECEIPT_JSON","sha256":"ACTUAL_SHA256"}
    }
  }]
}
```

`ONE_EVENT_INTERFACE_SMOKE`必须1个event/2个请求，只检查接口，不作科学质量声明；完整开发诊断使用`EXTERNAL_DEVELOPMENT_DIAGNOSTIC`和10–20个events。每个scope都必须事先冻结，完整分母一次通过，不能用部分准备提前启动GPU。预算等于2倍events数。`reuse_rgb_inputs`应列出同源已完成RGB窗口，至少包括original input。`clock_object_keys=[]`用于文件本身就是clock的情况。主代理若使用其他旧pipeline的receipt字段，需要先明确适配，不能靠异常回退跳过身份核查。

当前规则回执的本地源为 `reports/twenty_hour_five_20261014_v1/critic/official_rules_01.json`，独立批判代理报告SHA `b3dc2b7c080145efa3d72f413f4bb6fa8081f55b00bda97000fe83ed8284945b`。部署时仍以实际传入Linux文件核验。

最小1event/2requests的实际plan入口如下。注册表必须先具有上述smoke scope及真实原证据/协议绑定；该命令只读已完成clock/JSON，不重解clock，不读媒体，不启动processor。

```bash
/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python \
  /home/inspur/aic_video_work/twenty_hour_five_20261014_v1/local_boundary_v1/code/plan_local_inputs.py \
  --base /home/inspur/aic_video_work/twenty_hour_five_20261014_v1/local_boundary_v1 \
  --registration /home/inspur/aic_video_work/twenty_hour_five_20261014_v1/local_boundary_v1/registration.json
```

## 准入与执行次序

1. 主代理冻结外部开发10–20事件、科学protocol、源合法/隔离证据和实际容量。已曝光SumMe/VideoXum仅为开发，不能叫新盲确认。
2. `plan_local_inputs.py --base BASE --registration BASE/registration.json` 只读旧证据并生成 `plan_01`；不解码、不过processor、不启动GPU。
3. `prepare_local_inputs.py --base BASE` 新短窗一次真实CPU准备。旧clock不重测，旧RGB对应帧逐像素重用；新短窗RGB及必要相邻duration仅在Linux读取。每个新输入编码一次并保存无损level1 gzip CPU `encoded_tensors.pt.gz`；torch.save保留原dtype、layout和数据，SHA绑定压缩文件，tensor signature绑定展开后的原始tensor。
4. 主代理独立审查CPU completion、帧/PTS、实际网格/token、原runtime文件与所有source/request文件后写 `gpu_admission.json`。
5. 共享wrapper唯一新job运行 `infer_local_boundaries.py --base BASE`。按注册顺序写 `BEGIN_MODEL_CALL` / raw / done / `ACCEPTED_MODEL_CALL`，完整分母失败保留成功项/raw，不重新调用。
6. 唯一completed/exit0 resource与ledger一致后，独立CPU进程运行 `replay_local_boundaries.py --base BASE`。仅对新请求进行独立RGB/tensor/token/grammar/native转换重放，模型调用0。
7. 输出 `boundary_prediction_export.json` 只证明工程执行与独立重放；质量对照、新确认、5候选实际差异、426源场/空间/封包由主代理负责。

`gpu_admission.json`必要字段：`status=PASS_INDEPENDENT_LOCAL_BOUNDARY_GPU_ADMISSION`、`cpu_completion_sha256`、`registration_sha256`、`actual_model_call_budget`、`model_parameters`、`optimizer_updates=0`、`original_successful_stages_reused=true`、唯一`gpu_job_name`、`source_input_lock_files`。锁必须覆盖registration、plan completion/events/requests、CPU completion、每个新meta/proof/frames NPZ/encoded `.pt.gz`，并绑定需要的旧证据和runtime/processor资产。主代理在共享wrapper另冻结实测最大秒数，不以启动成功代替验收。

所有output阶段都以独占目录和文件`x`写入拒绝重复执行，无自动恢复。实际失败后的恢复需要主代理独立登记剩余请求，不能把已成功请求重做。

首个真实CPU input proof另记录compressed tensor文件字节、logical tensor payload字节、RGB NPZ字节、processor/压缩/请求耗时与进程peak RSS KiB。gzip不保证特定压缩率；这些真实数据必须先供主代理控制生产输入数量/磁盘/RSS/时长预算，不能用合成压缩比代替。压缩读取保留dtype，并消费gzip末尾验证CRC。

`lb_grammar.VerificationConstraint`提供VERIFY草案对应的有限token grammar，同样尚未进入任何pilot driver或准入。

## 风险和预算

原adapter学的是segments JSON，新有限decision/index schema存在任务迁移偏置；64帧更密不能证明它学会原候选语义。先报告KEEP/UNKNOWN/REFINE、edge输出、连续性未核实、端点位移、pair冲突，以及核心覆盖/明确非事件泄漏，不用单个摘要F1替代事件边界证据。UNKNOWN大量出现是结果，不得据此无限扩窗或调已曝光源阈值。

历史同B native64作业含加载用时：92窗880.467s、39窗466.439s、28窗362.434s。这些仅支持20事件/40请求约650–950 GPU秒的粗估，新的短输出prompt仍需实际实测；预算不是运行授权。建议主代理按新请求实测动态资源，冻结有余量的唯一作业上限，不启动多个并发B或重跑旧成功。

当前pilot接口不支持EVENT DROP，边界UNKNOWN绝不能充当候选删除。`lb_contract`另提供`verification_prompt` / `verification_responses` / `parse_verification` / `resolve_verification`草案；尚未进入plan/CPU/GPU driver或任何准入。VERIFY仅允许KEEP/UNKNOWN/DROP，清晰普通/冗余/无支持才DROP；景观、讲话无音频、不完整活动、稀疏覆盖不足按UNKNOWN保留，不要求高光必须完整动作。DROP只标记对应候选ID；主integrator必须先对其他保留候选求并集，不能删除它们共同覆盖的帧。五候选若包括事件验证，应另冻结验证语义/请求和共享回答预算。D8扩边及>=8秒条件须按主protocol明确绑定原粗段，避免端点位移同时改变padding条件。
