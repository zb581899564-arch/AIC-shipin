# V3 双坐标输入 ABI（代码与纯检查，尚未生产准入）

旧 `v1/v2`、D8、旧 full PTS 和五个 packet equality FAIL 均不修改。新 scope 只定义 PyAV17 reader-native 输入，不能把 scope 文件当作实际 prepare/GPU 许可。

`original_interval_exact`、`original_window_exact` 和 ENDPOINT 的 `original_endpoint_exact` 始终来自冻结的 D8 normalized recipe。native-cut 来自旧已成功的窗口 local `[first, exclusive_stop)` core 加原 `planned_source_frame_ordinals[0]`，通过原完整 PTS 映射；新的 source 最末 cut 才使用实际 packet end。

ENDPOINT 另存 `original_native_cut_interval_exact`、`original_native_cut_source_ordinals`、`original_native_cut_endpoint_exact` 和同值的 `refiner_native_cut_endpoint_exact`。`legacy_recipe_original_endpoint_exact` 与旧 `original_endpoint_exact` 同值。原 V4 prompt、continuity、parser/resolve 只能消费 `native_boundary_request(meta)` 的临时副本；存储元数据不替换旧 recipe。

正式消费者调用 `resolve_endpoint_result(decision, meta, boundary)`。只有原解析得到 `REFINE` 且 native cut 真实移动，才应用新 native point。KEEP、UNKNOWN、原语义可见性拒绝和 REFINE 零 native 位移都恢复旧 recipe 原点；零 native 位移仍保留原 `applied_decision=REFINE`，但 `native_cut_actually_moved=false`。坏模型、坏 grammar/schema 始终抛错。VERIFY 使用 `resolve_verify_result(...)`，保留原 recipe 区间或按原 DROP 语义移除贡献。

VERIFY 新上下文固定为原 full eligible ordinal `[first, stop)` 的实际 PTS 域：`stop<N` 使用 `PTS[stop]`，`stop=N` 使用新 physical end。原 64 ordinal 和 pixel SHA 不换样、不补帧。该请求明确为 `NEW_VERIFY_TIMING_CONTEXT_ORIGINAL64_PIXELS`，需要新的 processor/input/proof，不能声称旧 encoded input 复用。实际上下文超过 30 秒或装不下原 64 sample 时 STOP，不裁窗修复。

`packet_terminal_evidence` 使用 root 标准：reader、last raw/normalized PTS、positive packet duration、physical end、source SHA、unique/max display、observation ref；旧 validation status 单列并保持。首次未来 RGB decode 必须 full PTS/count/origin/geometry 与旧成功记录逐项相同，真实 positive Frame.duration 必须精确等于 packet duration。旧 N/fps/explicit endticks 不作新物理端点相等门。`first_RGB_decoder_terminal_witness` 只有实际新 decode 严格门通过才为 PASS。

首次 packet 的成功 source SHA 直接引用，未来 source decode 前后严格核同 inode/device/size/mtime/regular stat；不重复成功的 4.78GB source-SHA pass。新实际 decode 与 SHA 复用事实分开记录。RGB 统一调用原 `b_score_aligned_package_v4/source_color.py::convert_frame`；原 `common.py/config.json` 和命名空间均强绑定，special profile 或 conversion 失败没有 fallback。

CLI（仅供 root 后续部署及准入；本交付没有执行）：

```text
python project_legacy.py --registration /.../temporal_production_inputs_v3/registration.json
python prepare_source.py initialize --registration /.../registration.json
python prepare_source.py source --registration /.../registration.json --source-id <frozen-id>
```

注册新增字段：`D8_normalized_windows_ref`、`D8_original_clocks_ref`、`packet_registration_ref`、`packet_completion_ref`、`reader_native_terminal_scope_ref`、`source_color_config_ref`、`dual_coordinate_consumer_adapter_frozen=true`、`metadata_initialization_approved`、`actual_preparation_permission_path`。`required_code_files` 包含本目录全部 8 个 py 和原 source_color/common helpers。

`initialize` 只允许冻结 role/ref 后的 metadata initialization。真实 `source` 还需 `main_agent_actual_production_preparation_approved=true` 及最后 create-x 许可文件：status 为 `APPROVED_ONCE_NEW_V3_FORMAL_SOURCE_DECODE_AND_PROCESSOR`，绑定 input registration path/SHA，`source_count=426`、`model_calls_authorized=0`。该许可没有 GPU 权限。

Linux `pure_contract_01.json` 为新的双坐标合成检查，`pure_source_color_02.json` 为新增 source-color ABI 的合成 Frame 检查。两者都没有读取正式媒体/GT、执行生产 projection、decode、processor 或模型；旧成功 pure/storage 检查没有重跑。
