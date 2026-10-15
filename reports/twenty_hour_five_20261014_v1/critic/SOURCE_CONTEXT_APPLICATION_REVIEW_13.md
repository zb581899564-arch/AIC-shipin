# SOURCE 域边界应用的独立评议

支持事前登记独立 `SOURCE_CONTEXT_REALIZABLE` 家族 START/END/BOTH，作为未知质量的合理风险对照。当前 `combine_events.candidate` 固定 `max(original_window_lo,a-3/4)`、`min(original_window_hi,b+tail)`，实际 refiner 却从完整源抽取 ±3s 原生上下文；合法、独立验收的跨粗窗新 cut 确实可能被旧应用截断吞掉。统一应用真实源域是不同的可复现后处理范围，不是据测试/排行榜扫扩秒系数。它可共享同已接受输入/回答，不新模型、不重复成功调用。此结论不是科学质量或实际生产准入。

必须先按 arm 选择真正使用的 side，并完成原 pair 冲突保护，再判该 side 是否满足 `applied_decision==REFINE` 且 effective exact endpoint 不等于 old。只有这样的 start 使用 source floor0，只有这样的 end 使用已验 physical_end。另一侧、KEEP、UNKNOWN、zero-shift、未使用的 side 保留原粗窗 bound。若 a>=b 导致 pair 恢复 old，两侧 domain 也一起恢复 original window，不能留下源域 padding 造成冲突后的隐藏扩展。坏输出或缺 accepted proof 仍阻断，不充当保原。

保留 lead3/4、tail1/2 与原候选长度>=8时的额外1/4；长度 eligibility 永远取原 coarse。END 半开 cut 仍由下一实际 native PTS/已验正末 duration 定义，floor/ceiling 是精确源 clock 域，不用容器时长、CFR拉伸或 epsilon。旧 WINDOW 家族/旧协议不改。source/event/side identity、实际 endpoint raw/token/native first replay、完整 source clock 和原空间场仍锁定；并集去重、空 source 保留 D8 guard 和完整 426 分母不变。

语义限制必须写明：取消 clip 不仅能恢复外移的跨窗 cut，也会让靠粗窗边缘的 inward REFINE 获得旧 D8 padding 以外的源帧。例如旧窗[30,60)、old start30，新 start30.3，旧窗 padding 是30；source bound 后变29.55。它并非纯“把新 start30.3 实现出来”，而是 changed accepted REFINE 的 source-domain D8 padding。固定 padding 还可能超过 refiner ±3s 的可见观测窗。全部新增帧可以从真实源实现，不等于全部被同事件局部语义证据支持；同事件识别/邻窗候选重叠的风险仍 UNKNOWN，不能称 dense highlight 验证。

建议名称和报告直接说明上述适用条件及 padding 外推。全源字段保证新增帧有旧场合法框，但不证明其为高光。预登记 source domain 与条件后全局自动执行，不挑正式事件、检查实际预测比例后增删条件或调整 padding。共享输出生成多个 arm 的合理性来自确定性应用差异，实际 distinct 不保证达到5；最终自动 canonical 去重、原帧/框/模型参数、11strict、CRC/memberSHA、全链锁和实际交付由主控验收。已知可信严重劣化或工程/规则反证继续 veto，未知不能包装为安全证明。

规则依据为本轮 `official_rules_01.json`（2026-10-13T16:13:01Z 官方正文4267/通知5307/目录及同日附件身份引用）：自动可复现、原帧合法框、实际主辅<=9B、不用测试GT/标注训练/闭源测试API/人工修正/排行榜反构。此为公开条款下的常规后处理解释，不是赛方对 SOURCE 家族单独许可；未重复网页/PDF或读取正式预测内容。本审查不改 root combine、旧代码或协议，不运行封包。
