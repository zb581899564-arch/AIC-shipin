# 固定 HALF 的窄静态审查

结论：当前 `improvement/temporal_family_half_v1/half_math.py`、`package_half.py` 未发现阻断。只读本次代码、事前 HALF protocol 及原 full candidate 的必要接口；未读正式预测、raw、媒体或张量，未运行纯检查、生产、模型或封包。

- `ALPHA=Fraction(1,2)`；package 核独立 protocol 的固定 SHA、alpha、三臂和优先级，不提供 alpha 扫描或按结果选臂入口。计算坐标为 `old_recipe + (accepted_recipe_endpoint-old_recipe)/2`，不是 native pivot 的残差。
- 对应原 START/END/BOTH full candidate 先执行：核 event/side/original endpoint、接受决策及完整全幅 pair 冲突。即使半幅能消除全幅冲突，仍回原整个事件。失败或未接受模型输出不会转为 UNKNOWN。
- 仅 accepted REFINE 且明确 native cut 实际移动才计算半点，并核 native point 不等于原 native pivot、应用端点等于 native point。zero-native REFINE、KEEP、UNKNOWN、结构性短上下文均保原 recipe。原 KEEP 的 recipe/window 终点可以略超新 physical end，不冒称其为物理端点。
- 任一被应用的半点落在新物理域外，两个端点一起回原 recipe。该门针对新应用 cut；旧 window clipping、旧原段长度资格及固定前后 padding 不改。最终成员仍由完整 native PTS 的 bisect 自动生成，不增加虚构帧。
- VERIFY 的 DROP 仅记录，不在 HALF 应用；事件分母完整。原 eight-arm 家族不改。
- renderer 要求原 eight-arm 已自然完成且实际包数不足五，再按固定 HALF_START/END/BOTH 顺序发布至多 `min(3, remaining_slots)`。去重覆盖历史、D8、实际原家族包和本次 HALF 包；0 差异不发布、不承诺能凑齐五包。
- production accepted export/selection、原完整 source lock、packet/first decoder/full old PTS、全源场及保留 D8 框、8782459120 参数、426 非空、独立 11 strict、单 JSONL/CRC/member SHA 等门在 renderer 保留。新 package admission 必须由主控依据真实生产和风险证据签发；代码不自行准入或宣称科学/线上提分。

限制：半点是统一自动后处理的派生点，不是模型直接选中的 native sample；没有证据证明 HALF 优于全幅或 D8。当前结论仅为静态接口一致性，实际 source lock、生产终态、distinctness、格式、容量和交付均未由此回执验收。
