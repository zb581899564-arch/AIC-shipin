# 旧 CFR 选择坐标与真实 native clock 的契约修复

结论：从原已接受的帧实现证据自动把旧 coarse event 投影到 source ordinals，再用原完整 PTS 给新 refiner 原生 pivot，是合理、可复现的接口纠错。它不读取测试 GT，不逐条手调或根据结果选公式，不重跑旧成功模型；按本轮规则回执的自动原帧/合法框/可复现要求判断可行。它尚未证明真实输入或生产可用，旧01/02失败、旧JSON/源码/clock和已交D8保持。

已只读新 `tp_contract` v1/v2 与 preflight recovery02 代码。v1 对 null endticks直接拒绝；v2 明确把 CFR `N/fps` 标为 planning-only，却仍要求其大于最后真实PTS。主控报告02已实际在这个严格域门STOP。不能把 `N/fps` 换个名字叫 physical end、用 epsilon 抹平、拉伸完整 PTS 或据CFR标签假定两个坐标相同。02中的 float-ceil仅是 `hypothetical_float_ceil_CFR_only`，`assumed_old_D8_converter=False`；未经真实旧converter证据绑定不能宣称该假设已复现D8。03全源聚合由source owner执行，本审查未再统计源。

建议新 schema同时保留两个明确坐标，而不覆盖原字段：

- legacy：原source/case/window/segment身份、原parsed秒区间/旧窗及其原字节SHA；原长度>=8资格、原padding数值和旧converter/schema。
- realizable：原accepted per-segment `source_first_ordinal`、`source_stop_ordinal_exclusive`（以实际原schema字段映射）、原core/padded范围及与原输入/clock/源SHA的一对一绑定。
- native：完整原 integerPTS/timebase/raworigin→规范化PTS；start pivot=`PTS[first]`，end pivot=`PTS[stop]`（stop<N）；stop=N仅在新AV实测正lastduration后为lastPTS+duration。新转换记录 provenance，不改旧成功证据。

原accepted frame realizability范围优先于重新推测ceil。若必须从旧CFR公式计算，必须锁定实际曾生成D8的converter及padding算术顺序/float行为，不用 `Fraction(str(a))+Fraction(str(b))` 的“更精确”替代自动假定结果相同。首/末序必须满足0<=first<stop<=N；若实际旧core为空或无唯一实现，不能伪造锚点，可事前登记几何不可用并保旧选择，不换event/补帧。现存旧事件是否均满足此条件以source owner现成元数据为准，本审查不声称已经核全665。

KEEP/UNKNOWN保护目标是D8实际帧keys/boxes，不是近似秒区间。将native pivot重新减/加旧padding再bisect，通常不能证明得到旧D8。需要每event冻结原padded sourceordinal cut或等价mask：KEEP、UNKNOWN、zero-shift以及pair冲突退原必须采用这些原cut；仅真正接受且有效改变的side按native cut加固定秒padding实现，另一未变side仍用旧paddedcut。pair先保护再判side变化及WINDOW/SOURCE域，跨pair失败不留下新padding。原length资格仍取旧coarse长度，不能因native长度不同重新启闭额外tail。VERIFY KEEP/UNKNOWN保持原eventmask，DROP仅删除该event，最后union不删除其他event仍支持的帧。

必要证据是完整426身份和源SHA/原帧数/真实几何/完整oldPTS/timebase/origin强绑定；所有event/window映射的一对一身份和原可实现ordinals；原D8完整122050 frame keys逐一相同且boxes逐一相同的自动baseline保护检查（仅同总数不够）；10个旧显式endticks分支与416个CFR无末duration分支分清。旧原窗若是frame-index域，其真实窗界也应由原window frame bounds投影，不能继续用lo<=nativePTS<hi否认原成功visual64。VERIFY需保原64 sourceordinals/pixelSHA和原prompt时间坐标语义；新endpoint的context-local native时间/内锚另有独立meta，不混用旧窗口时间原点。

新AV一次完整源遍历必须保留真实全PTS、正末duration、实测尺寸、stream/timebase及新测量；完整PTS/origin/framecount/sourceidentity应与旧证据一致。416无旧末duration的情况仅表示旧physical witness缺失，不应要求新真实末端等于旧N/fps；它必须严格大于最后PTS且由正actual duration证明。10个旧真实末端有强证据则继续核相等，不普遍撤去duration门。出现新PTS/原帧数/geometry不一致或无positive duration仍STOP，不自动修改旧clock。

末stop=N的native pivot/±3s边界及actual64 ordinals不能在新duration尚未知时伪称已固定。新协议应明确登记待实测字段和确定性算法，完成实际几何/availability与请求冻结后再消费；不能按早期model回答改变后续source/event或窗口。首次普通processor输入、CPU→GPU完整tensor等值和首次独立input/output/native replay实际接受，全部graph/锁/自然资源terminal/格式包检查齐全后才可产出候选ZIP。此修复只解决坐标接口，不提供高光质量证据或生产准入，也不复活旧科学失败。

## 更正01：旧D8已有真实native membership

主控及source owner随后核到了旧D8真实入口：Linux `RUN/boundary_refinement_20261012_v1/input_export_02/{clocks.json,temporal_inputs.json}`，以及本地 `improvement/duration_guard_v1/package_duration_candidate.py:143`、`duration_intervals.py.spans(windows,F(8))` 和 `boundary_refinement_v1/intervals.py.native_membership`。本审查已只读旧D8 package段落确认它从normalized windows与原exact PTS直接计算membership，原core102112、已交D8全部122050 keys/boxes已有实际保护证据。旧D8不能被描述为假设ceil、伪physical或错误clock。本初稿的legacy/ceil讨论仅约束raw coarse入口的可实现转换，不能泛化到旧D8。

实际新prototype问题是从 balanced raw窗口和source metadata N/fps另行搭建了物理末端/候选入口；raw windows与D8所用normalized temporal_inputs是否一致需要固定元数据比较，不猜测。KEEP的权威复现输入应直接引用旧D8原normalized窗口、原padding函数和原exact native membership，再核全部keys/boxes。若与raw per-event identities拼接，必须一对一绑定原source/window/segment和字节SHA，不能按近似秒数配对或使用hypotheticalceil取代基线。

source owner现成schema证据：`native_frame_realizability.ranges` 是window-local integer `[first,exclusive_stop)`，`bw_report.py` 通过原 `planned_source_frame_ordinals[0]` 平移为sourceordinal；不是已经有source绝对序号。其全665 coverage/bounds尚由独立03聚合核验，本代理未重扫。416末duration缺失仍只表示缺实际physical witness，后续独立新packet/firstdecode测量必要；这一问题不改写原已native的D8成功或旧01/02失败。

## 更正02：03实际聚合小回执

source owner的首次03已完成，`CAMPAIGN/d8_native_arithmetic_preflight_v1/run_03/completion.json` 9200B，SHA256 `0482b180d98c4a6aec58d51d16bbcea316bbba4650d946ceb6c174f164cb7df4`；`metadata_statistics_receipt_03.json` 6584B，SHA256 `acad81016a8f54479d8584f77d2bb816c84493cd30c84f5ac93d4d10c8d316f8`。这是source owner传来的实际小汇总，本代理未重算或重读全源。旧D8normalized+exactticks与rawroot KEEP均复现122050framekeys/boxes零差；665 accepted ranges全部合法globalordinal，core102112全在D8，coarse段stop=N为0。521窗口full eligible bounds合法，其中424窗口stop=N仍需actual正末duration。58source浮点窗终点越exactplanning_end约1e-16..3e-15、64严格event拒、1CFR nominal_end<=lastPTS及1原sample64窗域异常属于新契约接入问题，不能倒推出旧D8选择错误或通过epsilon修复。116原exact_normalized字段均匹配D8normalizedwindow；5窗normalized与rawtop起/末不同但KEEP帧零差，说明近似秒数不相等与帧选择不同必须分开报告。
