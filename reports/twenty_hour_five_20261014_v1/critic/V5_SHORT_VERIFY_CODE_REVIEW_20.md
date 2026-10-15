# V5 事前短 VERIFY 的专项静态审查

结论：本轮增量接口未见剩余已知阻塞。新结构结果保留原事件和旧 D8 recipe，不降低新 MODEL 的 native64 门；这不是实际投影、正式准备或科学通过。最后 code/config SHA 冻结及实际 Linux 元数据验收由 root 完成。

仅只读新 inputs_v5、runtime_v5、control_v4、bootstrap_v2 的相关增量。inputs_v5 final manifest_02 的登记 SHA 为 `868725caa830dc385086c25228955b785cfd7b3887c11a7c92026ddc9774a390`。没有重跑已成功的 source 统计、原 pure 套件或 125 个旧依赖哈希。

原视觉证据按实际 N 严格校验：N 为 1..64 的整数，sampled_frames、source ordinal 顺序、原窗口样本及 N 个十六进制 pixel SHA 一致。合法原 23 帧输入不再被错误当作原证明损坏。只有 N=64 的 VERIFY 才进入 MODEL；N<64 统一在首次结果前生成 STRUCTURAL_UNKNOWN_ORIGINAL_VIEW_NO64，不补帧、不换窗、不建立 RGB group/canonical consumer、不调用 processor/model。

short 结果保留 event_id、原 case/seg、原 recipe interval 和 native core identity。其 decision=UNKNOWN、candidate_kept=true、retained_interval_exact=原 recipe，boundaries_changed=false、actual_model_call=false、predeclared_skip=true。prepare 按 kind 选 structural_verify_result；runtime skip 保留 kind=VERIFY；独立 replay 从冻结 source/window/event 重建 N/ordinal/pixel/无lease 条件和 UNKNOWN body，另留结构证明，不伪造 raw/token/input proof。aggregate 将其导入 verification[event_id]，最终继续要求 426 source、665 event、1330 endpoint、665 verification；actual consumer/proof 分母由首个冻结 plan 派生，logical 1995 不变。

UNKNOWN 只表示该 VERIFY 不提供 DROP 证据。已接受的独立 endpoint refinement 仍按原 START/END/BOTH/VERIFY_BOTH 因素规则作用。family 八臂、优先顺序及去重规则无需修改。

已发现并修复一处真实跨根阻塞：BOOT2 复用 INPUT4 的规则 leaf，但 CONTROL4 原 bound 只准新根。现 pc_io.official_rule_leaf 仅允许 INPUT4/bindings/official_rules.json 且硬锁已成功 b3dc...45b SHA；其他路径仍只准新根。inputs_v5 对两个 inherited leaf 同样只准精确旧文件；BOOT2 不再次 retain rules/selection，仅首次 retain 新 scope。旧失败注册及三份旧 bindings 不覆盖。

新 input/runtime/control/bootstrap 根、预算引用根、READER_SCOPE 与 native_terminal_scope 字符串已对齐 V5 短上下文协议。独立末帧 duration/全 PTS/身份门、缓存永久保留与首次独立 proof/自然 GPU terminal 的释放门不因短 VERIFY 改变。source 身份、解码、processor 或模型失败仍阻断，不能转结构 UNKNOWN。

本审查没有执行正式 project、cache initialization、解码、processor、GPU、数据评价或封包。不得据此称首次 metadata 已通过、实际 calls 已知、五包已产生或高光质量改善。
