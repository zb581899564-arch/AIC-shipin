# Fresh consensus confirmation CPU interface

仅本轮 Linux 根 `/home/inspur/aic_video_work/recall_consensus_verify40_46_20261015_v1`，`group=confirm`。本目录不改旧 4+4/facts/production 程序或已成功文件；以下代码当前只通过静态/合成检查，尚未执行真实准备或获得 GPU/质量准入。

## 入口与自然输出

```
python -B code/prepare_fresh_inputs.py --root NEWROOT --group confirm
python -B code/admit_fresh_inputs.py --root NEWROOT --group confirm
```

各为独立 CPU 子进程，只对自身设置 `CUDA_VISIBLE_DEVICES=''`，不修改 GPU 父进程环境。prepare 产出 `confirm/inputs_01`；独立 admit 产出 `confirm/admission_01`、根层 `cpu_acceptance_confirm.json` 与 `source_lock_confirm_B0.json`。已有阶段不覆盖、不隐式恢复；失败保留真实 failure、frames/PNG/cache/evidence/完整 clock 和全部成功材料，不以 UNKNOWN/EMPTY 掩盖工程失败。

## 首次冻结前的依赖

- 使用本轮 `model_common.fresh_gate(root,group)`、`root_path`、`check_protocol`。独立新根的同名 `model_common` 由入口脚本目录解析，不导入旧目录的同名模块。
- `protocol.json` 是已开发前冻结的 `RECALL_CONSENSUS_TWO_VIEW_SMALL_PILOT_V1`，SHA `d71d191c2525402872a866ab513e84c1ee032fdb14858ff9034bdb32f93cb236`。candidate 为 `TWO_DISTINCT_OVERLAP_VIEWS_EXPLICIT_KEEP_INTERSECTION`，view=15、stride=15/2、support_count=2，fresh source count=4、VERIFY40.46 ZIP SHA `86593725c6bad919dc0d342fe98ad65e489a13a6e492da5de3afd247a3226543`。不要求旧 protocol 的 `sources_per_group/single_factor/gpu_budget`，不增补原 protocol。
- 单一 `fresh_confirm_registration.json`：schema `RECALL_CONSENSUS_FRESH4_REFERENCE_REGISTRATION_V1`，status `REGISTERED_FIRST_FRESH_CONFIRM_MEDIA_NATIVE_REFERENCE`，group confirm。同一次初始冻结包含 `runtime`（原模型/TIME/prompt/native64/input16384/out256/baseline30/15与7.5）与 `gpu_budget`（confirm_B0_max_seconds=1800、confirm_VERIFY_max_seconds=2400、per_group_max_B0_actual_calls=48、per_group_max_VERIFY_actual_calls=240）、独立 deadline。CPU 不写 GPU admission。
- 注册 refs：`protocol_ref/authorization_ref/development_selection_ref/development_result_ref`。selection 位于根层 `selection_before_fresh_confirmation.json`，status `FROZEN_CONSENSUS2_AFTER_DEV_PASS`、本 candidate、protocol SHA、result SHA、`fresh_confirm_metrics_examined=false`。result 位于 `development_01/result.json`，实际 `PASS_CONSENSUS_DEVELOPMENT_NEEDS_FRESH_CONFIRM`、完整已曝光8源、全部原条件为 True、原失败和门不改；不把旧 confirm 当盲测。
- 注册 source 字段：`selection`4、`ordered_engineering_reserves`2、`known_exclusions_path/sha256`、`old_exposed_and_reserved_ids`、`annotation_file_path/sha256`、`prior_media_receipts`10条 path+sha256。旧 receipt 的 `sha256` 是原媒体 SHA；独立再次排除其 ID/bytes，不能把旧成功输入重做成本轮 fresh。
- `required_files` 全部绝对路径→SHA，`required_code_files` 是其实现子集。必须首模型前包含本轮全部 `.py`（包括 media/evaluate/consensus）、stage_io/overlap_plan、原 native_profile_01/04、原 runtime/config/processor assets 和 cv_contract/cv_grammar/cv_tokens。本说明也进入实际 CPU closure。source lock 再绑定本轮实际全部媒体/clock/reference/route/receipt、plan/aliases、PNG/NPZ、input/evidence/cache/proof、CPU 检查及 acceptance。

## 媒体完成接口

`reference_completion_confirm.json` 的 path+sha256 必须精确指向 `confirm/reference_01/completion.json`。completion status 沿用 `PASS_NEW_PROXY_MEDIA_NATIVE_SECONDS_NOT_CPU_INPUT_OR_GPU`，group confirm，accepted恰4，`registration_sha256` 绑定同一个 fresh 注册，另含 `development_selection_sha256/development_result_sha256` 绑定本轮实际门。

每 accepted 含 video_id/group、media(path/sha256/bytes/video_id/group/known_ID_and_byte_separation=true)、clock_path/clock_sha256、reference_path/reference_sha256；source 目录有 route.json/media_receipt.json。完整 clock 字段沿原成功 native_seconds schema：original_exact_pts、zero-origin/first PTS、positive last duration/physical end、native_frames、width/height、fps_num/fps_den、video_stream_index/stream_time_base_exact 等。CPU 直接引用完整 clock，不测量、平移、截断、猜 fps/end、padding 或改变原端点。

## 唯一实际输入与首次 QA

旧未改 planner 提供 baseline `n=ceil(T/30)` 的 equal nonoverlap 与独立 15/7.5 overlap/右尾去重；同 source/clock/window/ordinal/PTS geometry 合并 role aliases，实际只 primary encode/model 一次。特别是 T<=15 的 baseline/overlap 同实际输入只计一次；两视角候选的支持仍由后续 distinct geometry 规则判定，角色别名不算第二票。

一源 wanted ordinal union 只做一次原尺寸 RGB 解码。各唯一视图固定原公式取 64 个不同真实帧；native<64/零长/越域拒绝，不改窗补帧。每视图只做一次原 processor primary encode，接受 BatchFeature/Mapping；返回立即 fsync `encode_evidence.json`，再作 tokens/CPU/原 runtime/config/version 和 lossless torch.save gzip cache 实际 bit-roundtrip。容量估计依据本源几何和**实际显式 video_size**，不能把 loader 131072 kwargs 当实际视频像素上限，也不写死资源百分比或 GiB 门。

entry 保持 case_id/source_name/group/window_role/view_roles/input_path+SHA/proof_path+SHA；proof 原 status `PASS_CPU_ORIGINAL_B_NATIVE64_PROCESSOR_INPUT`、input_evidence、encoded_tensor_path+SHA、token count、完整 signature。新增 origin 为 `NEW_FRESH_CONSENSUS_CONFIRM_PRIMARY_ENCODE`，`first_independent_input_replay_pending=true`；无 preQA/recovery 分支。

独立 admit 只核实际全4源、实际唯一分母<=48、原钟/native64/像素/缓存/序列化/source和实现闭包，不调用 processor。CPU acceptance 沿用原 CPU_STATUS、source_count=4、expected_input_count=实际唯一数，source_scope=EXTERNAL_NONTEST_ONLY；没有任何 GPU admission 或质量 PASS。

真正首次独立 processor input replay 在本轮 B0 后由 `pilot_runtime.replay` 做一次，继续 token/grammar/parser/native/raw QA；后续 VERIFY 沿原同视觉缓存复用。独立 admit 的 serializer 检查不是 vision replay；本轮没有成功输入或 QA 可重复。
