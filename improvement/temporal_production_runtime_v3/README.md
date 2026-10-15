# Runtime V3 — 代码与七项新增纯检查，正式运行 0

Linux root 为 `CAMPAIGN/temporal_production_runtime_v3`，schema `TEMPORAL_PRODUCTION_RUNTIME_V3`；只接受显式 `input_root=CAMPAIGN/temporal_production_inputs_v3`。旧 runtime v1/v2 不变。所有实际 source preparation/GPU launch/admission 由 root 控制。

每批保留完整 source 的 ENDPOINT/VERIFY consumers，一次通过现有 `gpu_run.py`，一次加载原 B；endpoint role 由冻结 selection 指定，VERIFY 固定 TIME。physical 参数 8782459120，base 8767123696，TIME adapter 15335424。装载和批终态核完整 base/288 adapter；每 call 核 144 状态、frozen inventory、GPU 完整 dtype/stride/storage/token/grid signature。PEFT context 退出显式 `requires_grad_(False)`；独立 prefill，不共用跨 role KV。

新增 protocol 字段：`native_terminal_scope=NEW_PYAV17_READER_NATIVE_TERMINAL_SCOPE`、`dual_coordinate_application=LEGACY_RECIPE_KEEP_UNKNOWN_NATIVE_CUT_ONLY_MOVED_REFINE`。其余完整 code SHA、source/global graph、batch、cache policy、role、deadline、自然 terminal 与唯一 ledger 字段沿用旧接口。cache policy 的 `independent_replay_code_sha256` 必须为本版 `replay_batch.py`。

输入 stored `original_interval_exact/original_window_exact/original_endpoint_exact` 是旧 D8 recipe。native prompt/parser 使用 inputv3 `native_boundary_request(meta)` 临时副本。infer 调 `resolve_endpoint_result`；首次 output-only replay 使用旧独立 `independent_endpoint` 加本目录 `output_checks.independent_endpoint_export` 第二实现。仅 `applied_decision=REFINE` 且 native cut 实际移动才应用新 point；KEEP、UNKNOWN、几何拒绝及 native 零位移 REFINE 都输出旧 recipe endpoint。旧 recipe hi 超新 physical end 不会伪装成 physical 声明或被截断。

ENDPOINT exports 保留原键，但 `original_endpoint_exact/endpoint_exact/displacement_exact/changed` 均表示 recipe 应用坐标，另有 `legacy_recipe_original_endpoint_exact`、`original_native_cut_endpoint_exact`、`refiner_native_cut_endpoint_exact`、`native_endpoint_exact`、`native_displacement_exact`、`native_cut_actually_moved`、`original_recipe_preserved`、`dual_coordinate_schema`。request/raw/done/GPU proof/first replay 都绑定同原 event/side/coordinate metadata。坏 input/schema/model/raw/token 无 UNKNOWN fallback。

VERIFY 用原 64 ordinal/pixel 的新实际 timing window，依据 `new_verify_window_exact` 和 `original_native_cut_interval_exact` 检查可见资格；应用输出保留旧 recipe 区间。KEEP/UNKNOWN 保留，DROP 仅遵循原明确 ordinary/no-worth-retaining 语义；无音轨、讲座、静态风景或不完整动作不能自动 DROP。当前 inputv3 的新 actual <=30s 窗门保持；扩大 scope 必须另版本。

未来 root 准入后 CLI：

```text
python admit_batch.py --protocol ROOT/protocol.json --batch-id B000
# only existing shared gpu_run.py may launch infer_batch.py (parent CUDA nonempty)
python infer_batch.py --protocol ROOT/protocol.json --batch-id B000
python replay_batch.py terminal --protocol ROOT/protocol.json --batch-id B000
# inputv3 first_input_replay once per actual consumer, then output-only replay:
python replay_batch.py replay --protocol ROOT/protocol.json --batch-id B000
python close_batch.py --protocol ROOT/protocol.json --batch-id B000
```

只独立输出重放；不重新 decode/processor/full tensor encode，不重跑旧 TIME/raw/start/成功 input replay。自然 resource 与当时完整 ledger 原字节 snapshot 永久保留，原 path/SHA/UTC 另存。所有消费者第一次 ordinary-RGB input replay 和 output/GPU/weight QA 全过后，critic LeaseStore 才接受并释放本批新 ephemeral RGB；canonical/raw/proof 永存，旧文件永不删。

`pure_checks.py` 只含此次七项双坐标、旧 FAIL 保留、decoder/packet 与全 PTS mismatch、VERIFY 历史窗和 missing-cold-HWM envelope 的合成检查；旧纯套未重跑。Linux stdin 内存执行一次 PASS，media/processor/model/正式生产操作均 0。这是工程接口验证，没有科学质量或五包声明。
