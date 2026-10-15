# Local boundary V3 revision03 / Charades role scopes

本版本复制 v2 的 SOURCE_EDGE_INWARD_REVISION_03，仅增加 Charades21 开发/确认 scope 与新 coarse 证据根。v3 尚未部署，不运行真实CPU、媒体或模型。v1/v2、已部署helper2原SHA及成功gzip/smoke保持不变，不重跑旧成功 smoke。端点数学、prompt、KEEP/UNKNOWN、source首/末向内、内部严格 native bracket 和 exclusive end 含义均保持 v2 revision03。

这是独立的新接口。旧 `human_reference` / `duration_guard` / `videoxum` / `sparse_context` 及 Charades/v1/v2 成功产物只读。v3 的真实请求代码未部署、未运行；新下载、真实CPU准备、模型调用、训练或封包均为 0。gzip 函数保持相同，不重复旧成功证明。

固定Linux输出根目录：`/home/inspur/aic_video_work/twenty_hour_five_20261014_v1/local_boundary_v3`。代码可部署到该目录的 `code/`。入口都必须运行在 `inspur-NP5570M5`；CPU入口只清空自己的CUDA可见性，不能在父链清空。

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
  "schema":"LOCAL_BOUNDARY_NATIVE64_V3_REVISION03",
  "contract_revision":"SOURCE_EDGE_INWARD_REVISION_03",
  "status":"FROZEN_EXTERNAL_NONTEST_LOCAL_BOUNDARY_V3_REVISION03",
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
    "original_case_id":"CH_SOURCE_W000",
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

三种 scope 明确区分：

| validation_scope | events | source_scope | 原 CPU meta source_role | exposed flag |
| --- | --- | --- | --- | --- |
| ONE_EVENT_INTERFACE_SMOKE | 1 | EXTERNAL_NONTEST_DEVELOPMENT_ONLY | dev | true |
| EXTERNAL_DEVELOPMENT_DIAGNOSTIC | 10..20 | EXTERNAL_NONTEST_DEVELOPMENT_ONLY | dev | true |
| EXTERNAL_CONFIRMATION_DIAGNOSTIC | 10..20 | EXTERNAL_NONTEST_CONFIRMATION_ONLY | confirm | false |

exposed flag 是 `existing_sources_are_exposed_development_not_new_confirmation`；开发 true 表示开发用途、不称新确认，不虚称 Charades 已测质量。所有 v3 events 仅来自已注册 Charades 原 CPU meta 的 role，不能把旧两个 dev success 改成 confirm，也不能把 SumMe/VideoXum 改名为新确认。原 input/cpu_proof/clock 必须在 Charades v1/v2 roots，原 done/raw/request/independent_replay 必须在独立 `charades_coarse_v1` root；真实 media 只能在 Charades 的 `media_01/source_id`，coarse receipt root 不能当 media。

10..20 开发和确认都必须新增：`confirmation_event_extraction_path`、`confirmation_event_extraction_sha256`、`confirmation_event_extraction_frozen_before_development_results=true`；前两字段必须以 exact path/SHA 纳入 `required_files`。确认还必须有 `development_selection_path`、`development_selection_sha256`、`confirmation_metrics_sealed_until_development_selection_frozen=true`，并把 frozen development selection 同样纳入 `required_files`。planner 只核元数据/SHA，不读取参考或指标内容；独立主控负责冻结时间顺序与解封质量指标。

主控提前冻结的抽取规则：每个固定 role 来源按 `(original_window_index, original_segment_index)` 次序，先每源第一存在候选一轮，再每源第二存在候选一轮，最多20；开发与确认使用相同轮询方式，不按 GT/预测质量选。LEGAL_EMPTY 来源保留在完整源覆盖分母，但不能捏造事件；抽取不足10就如实不足，不追加来源。确认 metadata domain/identity 核验不算质量指标曝光，实际模型匹配与端点指标在冻结 development selection 前保持 sealed。本目录不自动运行抽取或解封指标。

1event smoke 只检查接口，不作科学质量声明，旧 smoke 不重跑。每个 scope 都必须事先冻结，完整分母一次通过，不能用部分准备提前启动GPU。预算等于2倍events数。`reuse_rgb_inputs`应列出同源/同 frozen role 已完成RGB窗口，至少包括 original input。`clock_object_keys=[]`用于文件本身就是clock的情况。主代理若使用其他旧pipeline的receipt字段，需要先明确适配，不能靠异常回退跳过身份核查。

当前规则回执的本地源为 `reports/twenty_hour_five_20261014_v1/critic/official_rules_01.json`，独立批判代理报告SHA `b3dc2b7c080145efa3d72f413f4bb6fa8081f55b00bda97000fe83ed8284945b`。部署时仍以实际传入Linux文件核验。

最小1event/2requests的实际plan入口如下。注册表必须先具有上述smoke scope及真实原证据/协议绑定；该命令只读已完成clock/JSON，不重解clock，不读媒体，不启动processor。

```bash
/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python \
  /home/inspur/aic_video_work/twenty_hour_five_20261014_v1/local_boundary_v3/code/plan_local_inputs.py \
  --base /home/inspur/aic_video_work/twenty_hour_five_20261014_v1/local_boundary_v3 \
  --registration /home/inspur/aic_video_work/twenty_hour_five_20261014_v1/local_boundary_v3/registration.json
```

## 准入与执行次序

1. 主代理冻结 Charades role scope 的10–20事件、提前确认抽取规则、科学protocol、源合法/隔离证据和实际容量；确认另绑定 frozen development selection，指标解封由主控负责。
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

原source首端为0，须来自既有完整clock的独立已验origin映射，normalized首PTS=0且raw首PTS等于该measured origin；合法旧非零raw origin不会被改成新offset。原物理末端须由已有末native PTS加正duration证明。新chosen cut仍需新短窗的相邻真实duration连续。end所选sample表示最后included帧，其下一PTS是exclusive cut；后侧可见样本可以恰在该cut开始，不要求严格大于。sample0/63仍UNKNOWN。

示例：25fps、源[0,10)，原候选[0,4)，start短窗[0,3)，anchor1，index14对应新cut0.64，前可见sample0.60、后sample0.68。旧规则机械UNKNOWN，v2可在模型明确同候选外侧转换时REFINE。对称end候选[6,10)，index49末included9.28，exclusivecut9.32，后可见sample恰9.32，anchor9。

反例：source从0开始一直是同一动作，0.64只是更激烈阶段。即使几何/连续性全过，也不能证明外侧转换；prompt要求UNKNOWN/KEEP，开发评价需独立检验，代码不能自动把几何当语义判定。不得声称恢复源外不可见的真实动作起止，不假设高光必须有完整动作。prompt仍不含新GT。

v3 仅供通过完整 coarse 模型及独立重放的 Charades 开发/确认事件使用；当前没有这些新实际回答。Charades v1/v2 和 coarse_v1 已纳入明确证据路径范围，source separation 仍需要主代理提供完整、冻结、规范 receipt，不静默跳过。没有真实 coarse/raw/replay/身份 receipt 就不能构造可执行 plan。提前 extraction 与 frozen development selection 两份小元数据可放入本 v3 base，和 protocol 一样以原 bytes/SHA 绑定，planner 不读其质量内容。

原adapter学的是segments JSON，新有限decision/index schema存在任务迁移偏置；64帧更密不能证明它学会原候选语义。先报告KEEP/UNKNOWN/REFINE、edge输出、连续性未核实、端点位移、pair冲突，以及核心覆盖/明确非事件泄漏，不用单个摘要F1替代事件边界证据。UNKNOWN大量出现是结果，不得据此无限扩窗或调已曝光源阈值。

历史同B native64作业含加载用时：92窗880.467s、39窗466.439s、28窗362.434s。这些仅支持20事件/40请求约650–950 GPU秒的粗估，新的短输出prompt仍需实际实测；预算不是运行授权。建议主代理按新请求实测动态资源，冻结有余量的唯一作业上限，不启动多个并发B或重跑旧成功。

当前pilot接口不支持EVENT DROP，边界UNKNOWN绝不能充当候选删除。`lb_contract`另提供`verification_prompt` / `verification_responses` / `parse_verification` / `resolve_verification`草案；尚未进入plan/CPU/GPU driver或任何准入。VERIFY仅允许KEEP/UNKNOWN/DROP，清晰普通/冗余/无支持才DROP；景观、讲话无音频、不完整活动、稀疏覆盖不足按UNKNOWN保留，不要求高光必须完整动作。DROP只标记对应候选ID；主integrator必须先对其他保留候选求并集，不能删除它们共同覆盖的帧。五候选若包括事件验证，应另冻结验证语义/请求和共享回答预算。D8扩边及>=8秒条件须按主protocol明确绑定原粗段，避免端点位移同时改变padding条件。
