# V4 原 eligible ordinal 支持域 VERIFY

独立复制 v3；旧 v1/v2/v3、旧 CV v2、所有成功 pure 和五个旧 packet equality FAIL 保留。当前仅代码与新增纯检查，未执行正式 project、cache initialize、decode、processor 或模型。

SCHEMA 为 `TEMPORAL_PRODUCTION_INPUTS_V4_DUAL_RECIPE_READER_NATIVE_VERIFY_ORDINAL_CONTEXT`；reader scope 为 `NEW_PYAV17_READER_NATIVE_TERMINAL_SCOPE_V4_VERIFY_ORDINAL_CONTEXT`。root scope02 定义真实原 eligible ordinal 支持域，不把名义 30 秒当作新的 VERIFY timing 门。

`verify_request(event, meta)` 是完整的新 validator，不调用旧 `cv.request`。它根据 `verify_eligible_source_ordinal_bounds`、完整 `all_source_exact_pts` 和真实 positive `physical_end_exact` 推导唯一上下文。`window_start/window_end/new_verify_window_exact` 必须与该上下文完全一致，不能 fake hi、裁窗或扩大支持。原 64 ordinal 必须与 `verify_original_frame_ordinals` 同值同序，样本 PTS 逐项等于完整 source PTS；candidate native cuts 绑定原 accepted core ordinals 并落在实际支持域。实际原 64 pixel SHA 仍由原 prepare 中的严格验证负责。

旧 recipe 的 `original_interval_exact/original_window_exact` 和 endpoint 原点不变。REFINE 的 native-cut adapter、KEEP/UNKNOWN 原点恢复、有限 KEEP/UNKNOWN/DROP body、坏结果阻断、新 Frame.duration 精确匹配 packet、source_color 和 16384 token 门均沿用 v3。`packet_terminal_evidence.old_validation_status` 保持既有字段名；没有把五个旧 FAIL 改成 PASS。

新增元数据键：VERIFY request 保存 `verify_original_frame_ordinals` 和 `verify_eligible_source_ordinal_bounds`；实际 meta 保存 `physical_end_exact`。新 VERIFY helper 的 schema 为 `CANDIDATE_VERIFY_V4_ORIGINAL_ORDINAL_CONTEXT`，并记录 `nominal_seconds_gate_used=false`、`old_CV_v2_request_called=false`。

新根为 `CAMPAIGN/temporal_production_inputs_v4`。CLI 与 v3 相同；metadata initialize 仍不等于 source prepare 准入。最后真实 source 许可文件 status 改为 `APPROVED_ONCE_NEW_V4_FORMAL_SOURCE_DECODE_AND_PROCESSOR`，其余 input registration path/SHA、426 source、0 model 授权约束不变。

新增 pure 仅覆盖真实 32 秒支持域对应原 64 帧、旧 v3/CV 秒数门仍拒绝该新案例、fake clipped/expanded context 拒绝、PTS/ordinal/terminal 拒绝和新 request 的保守结果还原原 recipe。没有重跑 v3 的 20 项数学或 5 项 color suite。
