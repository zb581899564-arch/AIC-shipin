# V5 原短 VERIFY 视窗的事前 UNKNOWN

独立复制 input4，保留旧源码、注册、三个已成功 binding 和失败回执。原 accepted 采样合法域为实际 1..64 帧；新 projection 保留原实际数量、ordinal 顺序、逐帧 pixel SHA、floor 采样规则与 D8 recipe，不将旧 23 帧尾窗当作数据错误。

所有实际 MODEL 输入仍为 64 个不同原生帧。原 VERIFY 数量小于 64 时，统一在首次模型结果前冻结 `execution=STRUCTURAL_UNKNOWN_ORIGINAL_VIEW_NO64` 和 `structural_verify_result`，保留原事件及旧 recipe 区间，`actual_model_call=false`、`predeclared_skip=true`。它不加入 consumers 或 RGB_groups，没有 processor、raw、GPU 或独立模型输入重放。ENDPOINT 仍按原完整 source PTS 的 ±3 秒域和 native64 floor 独立决定可调用性。

三类分母保留 nominal endpoint、nominal VERIFY、actual MODEL 和 structural counts。426 sources、521 windows、665 events、1995 nominal requests 不变；实际 MODEL 数量必须由真实冻结 plan 派生。

新根 `CAMPAIGN/temporal_production_inputs_v5`，SCHEMA=`TEMPORAL_PRODUCTION_INPUTS_V5_DUAL_RECIPE_READER_NATIVE_VERIFY_SHORT_ORIGINAL_UNKNOWN`，READER_SCOPE=`NEW_PYAV17_READER_NATIVE_TERMINAL_SCOPE_V5_VERIFY_SHORT_CONTEXT_UNKNOWN`。最终 source 许可状态为 `APPROVED_ONCE_NEW_V5_FORMAL_SOURCE_DECODE_AND_PROCESSOR`。

仅官方规则和角色选择的两个旧叶文件可继承：`INPUT4/bindings/official_rules.json` 与 `INPUT4/bindings/uniform_role_selection.json`。其他旧根路径不能因此放行；scope03 必须首次放入新根。新 reader fullPTS/count/origin/geometry、真实正 Frame.duration 精确等于 packet、原五个 equality FAIL 保留、source_color、有限 grammar、16384 tokens、KEEP/UNKNOWN 双坐标桥接及 encoder 前 RGB checkpoint 均沿用 input4。

新增 pure 只检查一个 synthetic23 案例和 AST，不重跑旧 9/5/2 suites。当前未部署或执行正式 projection、decode、processor、GPU。
