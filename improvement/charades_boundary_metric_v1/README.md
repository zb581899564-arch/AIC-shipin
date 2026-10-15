# Charades 固定几何端点诊断

这是纯评价模块，没有媒体读取、processor、模型或生产入口。原作者 `actions` 的 class/start/end 是动作时间标注，不能替代赛事高光真值。唯一时间重叠仍不能保证 coarse 与动作是同语义事件；所有对应的语义状态保持 `UNKNOWN`，本模块从不产出 SCI 或高光质量 PASS。旧完整域门和旧失败不变。

`freeze_from_coarse.py` 在全部 38 原 B0 独立重放接受后、fine 回答之前，只读冻结 metadata。21 来源（dev11/confirm10）及零 eligible 来源、合法空窗、全部 coarse 事件都保留。`coarse_events_projection.json` 不含动作标签；fine plan 按已冻结 coarse/native 规则 cap20，不能读对应质量选事件。原标注完全落入实测域才是 eligible；越域仍原文保存为 censored UNKNOWN，不截断、拉伸、平移。部分动作集合不能作为 whole-source precision/recall/F1 真值。

自动对应仅在 coarse 与恰好一个 action 有正时长交集、与任何 censored action 无正交集、双方重叠比例都严格大于 1/2、两内侧锚点位于该动作内且其实际含原帧时成立。1/2 是事前选择的双向多数几何条件，没有作者语义保证；未按结果调阈值。原边界落在其他动作内部时该侧 UNKNOWN。目标在短窗之外或短窗边缘只报告诊断，不进入可达两侧端点选择集。端点误差用原始秒区间，不虚构密集帧精度或作者允许的误差容忍。

`metric.freeze(events, sources)` / `metric.evaluate(frozen, {'TIME': rows, 'BASE': rows})` 的输入都是已独立接受的 metadata 投影。输出保留 KEEP/UNKNOWN、预登记短窗、缺失/坏结果、原全部来源覆盖、端点绝对/带符号误差、每来源误差和声明动作支持移除。误配风险、未知和未 planned coarse 数单列。缺失/坏输出不从 planned 分母消失，主 paired 均值置空；有效子集仅放 `partial_valid_*` 字段，不能据此选择角色。

固定 plan schema 为 `FROZEN_BOUNDARY_ROLE_CANDIDATES_FROM_COARSE_NATIVE_GEOMETRY_ONLY_V1`，包括 `event_ids`, `scope`, `coarse_complete_sha256`, `reference_labels_used_to_select=false`, `fine_results_available_at_freeze=false`, `availability_frozen_before_fine_results=true`, `availability_independent_clock_receipt_ref={path,sha256}` 和完整 `endpoint_availability`。后者每 planned event 的 start/end 各一条：`{event_id,side,status,native_frame_count,required_native_frames:64}`。`status` 只允许 `AVAILABLE_NATIVE_CONTEXT`（>=64）或 `SHORT_NATIVE_CONTEXT_UNAVAILABLE`（<64）。不足64是事前 clock 几何 skip，不改变事件/窗/阈值；两角色都必须输出原端点、`applied_decision=UNKNOWN_SHORT_NATIVE_CONTEXT_UNAVAILABLE`, `actual_model_call=false`, `predeclared_skip=true`。不虚构 raw/proof，不将真正可调用侧的缺失转为 skip。名义/可调用/skip 分母单列。

每角色的事件投影包括 `event_id`, `original_interval_exact`, `refined_interval_exact`, `pair_conflict_preserved_original`, `new_event_created=false`, `original_event_removed=false`, `endpoint_results`。端点各含 `event_id`, `side`, `original_endpoint_exact`, `endpoint_exact`, `applied_decision`；所有 exact 秒为规范 Fraction 字符串。已接受的 REFINE 还要通过固定上下文/内锚/源边缘方向复核。KEEP/UNKNOWN 必须保留原点，交叉起止保留原区间。

保守全局角色建议 schema 为 `CONSERVATIVE_GLOBAL_ROLE_PROXY_ADVICE_NOT_SCIENCE_PASS_V1`。固定可达集合只含几何诊断成立、目标严格在短窗内且 native 可调用的端点，不能按 fine 成败再筛。只有全部 planned 工程接受、至少3个不同对应来源、BASE 在每固定端点误差均不大于 TIME 和 coarse、两总体均值均严格改善、且 BASE 与声明动作支持的交集覆盖 TIME 和 coarse 原交集，才建议 BASE；否则 TIME。比较为 exact 有理数，零秒容忍，不发明大额移除门。3 来源仅是本轮覆盖要求，不是统计或语义证明。建议只是有限代理上的保守风险选择；动作支持移除是风险旗，不自动变为已知高光核心破坏。独立已知事实才能证明严重劣化。保持 TIME 也不证明质量。

`evaluate_roles.py` 只消费本根 SHA 锁定的 metadata witness copies。dev 后冻结全局角色再读 confirm；confirm 只检查冻结角色，不重新挑角色或 case。工程全部通过仍不产生 `role_qualification_admitted` 或 `scientific_quality_claim`。没有可明确代理/少于3来源时可由主控另行明确风险角色并冻结，不能包装科学优胜，也不能事后修改这个建议规则。

`check_metric.py` 原纯检查01保留；新 `check_role_policy_02.py` 只测试角色/支持/skip/缺失分母，没有真实数据。正式 metadata freeze 和 role evaluation 均需主控登记部署后单次运行，代码完成不代表真实评价完成。
