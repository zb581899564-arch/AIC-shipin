# v4 时钟合同

这是新增工程版本的 metadata 合同，`inference_allowed=false`、`legacy_a_admission_granted=false`；主控另行决定运行准入。原 v3 receipt、numeric、manifest 与旧 A 保持只读。

## clock_registry.json

`schema=aic_source_clock_registry_v4`。必有 `kind`（`REMATCH426` 或 `NONTEST_FROZEN8`）、`expected_count`（426 或8）、`input_manifest_sha256`、`v3_receipt_sha256`、`endpoint_addendum_sha256`（无补证时null）、`all_identity_pass`、`all_sources_usable`、`all_cfr_eligible`、`failed_video_ids`、`records`。`v3_receipt_sha256` 对8源绑定专门 collector receipt，不表示426门通过。records保持原清单顺序、完整分母，每个video_id恰好一次。

共同记录字段：

| 字段 | 含义 |
| --- | --- |
| `video_id / source_sha256 / n_frames / fps_num / fps_den` | 绑定原metadata源身份 |
| `identity_pass` | 原PTS严格单调、源数目/几何/stream start、全部Decord starts已绑定 |
| `usable` | identity及对应分支的全部必需证据通过，failures为空 |
| `cfr_eligible / cfr_evidence` | 原 `1/fps+1e-6` gate；资格失败在`cfr_evidence.failures` |
| `failures` | 仅未解决身份/证据/endpoint失败；正常native分支不放入CFR资格失败 |
| `v3_pass / v3_failures` | 保留原结果与失败，绝不回写v3 |
| `clock_branch` | `CFR_LEGACY` 或 `NATIVE_PTS`；STOP记录可能缺失 |
| `raw_time_base / raw_first_pts_ticks` | 精确有理timebase与源frame0原tick |
| `integer_evidence_kind` | 明确区分v3唯一整数重建和新raw整数交叉证实 |
| `decord_clock_mode / decord_binding` | 全帧原/relative时钟模式与绑定证据 |
| `clock_arrays:{path,sha256}` | 独立逐帧数组JSON，消费前必须验证SHA256 |
| `numeric_evidence:{path,sha256}` | 原v3/8源补读numeric绑定 |
| `endpoint_addendum_evidence` | native分支原始ffprobe JSON绑定 |
| `duration_seconds / native_end_sec / terminal_evidence` | 终点与来源证据，按下述分支解释 |

CFR记录：`status=PASS_CFR_LEGACY_BRANCH_IDENTITY`，`identity_pass=true`、`cfr_eligible=true`、`usable=true`、`native_clock_usable=false`、`native_end_sec=null`。`duration_seconds=n_frames*fps_den/fps_num`。`terminal_evidence.kind=LEGACY_CFR_N_DIV_FPS`、`native_packet_endpoint_proven=false`。`decord_binding.start_pass=true`、`end_pass=false`、`legacy_interval_pass=true`；`end_evidence.method=LEGACY_CFR_INTERVAL_CHECK` 包含原有限正interval、严格单调ends、帧duration误差及原gate。它证明旧CFR interval检查，**不证明native packet尾端**。

Native记录：`status=PASS_NATIVE_PTS_BRANCH_IDENTITY_NON_CFR`，`identity_pass=true`、`cfr_eligible=false`、`native_clock_usable=true`、`usable=true`。`native_end_sec=duration_seconds`，终点大于最后一帧relative PTS。`decord_binding.start_pass/end_pass=true`。`terminal_evidence.kind=NATIVE_LAST_FRAME_PACKET_DURATION`，`endpoint_authority=NATIVE_LAST_FRAME_PACKET_AND_DECORD_END`。实际终点为 `(last_frame_end_pts_ticks-raw_first_pts_ticks)*raw_time_base`，逐帧原整数必须与v3唯一重建一致、所有packet duration为正、所有Decord ends绑定native packet ends。header duration另存差异诊断，`stream_header_duration_used_as_endpoint=false`；不因header差异推翻实际packet/decoder终点，也不伪称header一致。

缺证、哈希失败、非单调、float alias、尾duration缺失、decoder end不匹配等记录为 `STOP_SOURCE_CLOCK_EVIDENCE`、`usable=false`。即使starts通过，native尾缺证时也不能准入。

## clock_arrays/{video_id}.clock.json

`schema=aic_source_clock_arrays_v1`。字段：`video_id`、`source_sha256`、`n_frames`、`raw_time_base`、`raw_first_pts_ticks`、`native_pts_ticks`、`source_relative_pts`、`source_relative_pts_rational`、`native_frame_end_pts_ticks`、`integer_evidence_kind`。

全部 starts 数组长为n_frames；`source_relative_pts[i]` 是 `float((native_pts_ticks[i]-raw_first_pts_ticks)*Fraction(raw_time_base))`，rational数组是该值的精确分数字符串。CFR的`native_frame_end_pts_ticks=null`；native数组长为n_frames，每项为该帧原整数PTS+原正packet duration，严格单调，最后项绑定terminal。数组没有像素或语义标签。

v3 numeric没有保留整数数组；CFR `native_pts_ticks` 是冻结worker `float(integer*Fraction(time_base))` 的**唯一重建**，要求逐项float64精确回放且相邻整数tick不出现float64 alias。不能称它是v3保存的原始整数。native分支还以新增raw ffprobe实际原整数数组逐项交叉验证。

Decord仅接受已知`float32 / epsilon=2**-23`。stored float必须恰是native raw或relative时钟的正确float32表示，邻帧量化仍唯一，实际表示误差小于最小源帧间隔的一半。没有整tick误差容限。Decord值直接除细timebase再round整数可能因float32分辨率低于tick而差一tick，该项仅作为独立诊断，不替代精确float32/native帧身份绑定。

## clean_manifest_v2.json

只有`all_sources_usable=true`时写出。`schema=aic_rematch_A_input_v2`，保留旧top字段与metadata input_contract，添加 `input_manifest_sha256` 和 `clock_registry:{path,sha256}`。每条record保留原12字段，添加 `clock_record_id=video_id` 与 `clock_branch`。

426源的native分支仅把原完整源`scope_end_sec`改为已验证nativeDuration，`scope_start_sec=0`；CFR保持原scope。8源全部限CFR，原短scope逐字段保留，不把整来源视频扩成新推理scope。新schema不能直接送旧A；由独立`baseline_a_pts_v1`读取器绑定registry并核分支，主控另授予运行准入。

## endpoint addendum输入

`schema=aic_native_endpoint_addendum_v1`，`records`每条包含 `video_id/source_sha256/source_sha256_before/source_sha256_after/source_hash_verified_before_and_after=true/ffprobe_json:{path,sha256}`。raw ffprobe JSON需完整源frames的整数`best_effort_timestamp`、文本`best_effort_timestamp_time`、正整数`pkt_duration`，若有`pkt_duration_time`须相符；stream需width/height/time_base/avg_frame_rate/start_pts/start_time。duration_ts/duration作为独立header诊断保留。
