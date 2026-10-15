# metric08 独立评价范围

本次产物是纯评价代码和合成检查，真实 reference freeze / role evaluation 尚未运行。当前21来源/38 coarse窗、dev11/confirm10，以及事前抽取 dev20/confirm18 事件来自主控回执，不是我重新读媒体或评价出来的数量。

原作者 README `actions` 只定义动作 class/start/end 秒区间，论文 §2.3 描述动作起止标注；没有检出密集高光、整数余量容忍或 clip-edge 官方 censoring 约定。以前实际取得的作者材料和 partial native 范围证据保持，未扩大搜索/媒体下载。当前完整落域动作可作有限内部端点代理；越域原文保留 UNKNOWN，不评分、不当负例，不把 valid union 当 whole-source F1。

对应事前固定为唯一正交集、无 censored 交集、双方交集比例严格大于1/2、两 coarse 内锚在动作内、动作含真实帧。1/2 是双向多数几何筛选，不是官方推荐阈值或“同事件”证明；动作并发及边界处其他动作导致 UNKNOWN。此条件可能极少适用，适用不足也不换来源/事件或按回答放宽。语义一律 UNKNOWN，paired 秒误差、方向与动作支持只作诊断。

原拟 BASE 总 mean MAE 更小且无“大额”移除存在两风险：均值可掩盖个别端点恶化；“大额”没有作者精度/容忍依据。实现采用 exact 零容忍的保守自动建议：每个固定 clear+target严格窗内+可调用端点的 BASE 误差都不大于 TIME 和 coarse，两个整体均值都严格改善，且所有几何对应 planned 事件的 BASE 动作支持交集覆盖 TIME 和 coarse 交集。任一新增支持移除拒绝自动建议 BASE。该条件限制代理风险，不将动作支持等同高光核心，不把动作之外视为普通，也不独自宣布严重劣化。至少3来源只是本轮实用覆盖要求；仍不构成 SCI、统计显著或高光 PASS。

原 dev20/confirm18 planned 名义分母保留。独立 clock 事前证明少于64原生帧的侧，仅以 `SHORT_NATIVE_CONTEXT_UNAVAILABLE` skip，两个角色均保留原点并明确 no call；计入名义/skip/来源覆盖，与真实 bad/missing 分开。skip 不进入固定可调用角色比较集合，不能补帧、扩大窗、换事件、降低64或事后把失败叫skip。真正 bad/missing/重复/额外投影阻断 primary comparison，主均值为 null；有效部分仅显式 partial 字段。

合成 role 检查02通过：均值不能掩盖端点坏方向、更低 MAE 不能掩盖相对 TIME 支持移除、短侧 no-call/原点/分母、可达来源不足、缺失主指标置空、事后skip/改点skip/不完整availability拒绝。原检查01不重跑。新增02早期两个人工合成例设置错误（一个落在内锚外，一个实际没有移除比较支持）已保留两个失败回执；修正例子后通过，真实数据/媒体/processor/model读取均0。5个 Python AST 通过。

角色建议 schema `CONSERVATIVE_GLOBAL_ROLE_PROXY_ADVICE_NOT_SCIENCE_PASS_V1`。结果中 `role_qualification_admitted`, `scientific_quality_claim`, `same_event_semantics_verified`, `whole_source_precision_recall_F1_admitted` 始终 false。主控可在代理不足时独立明确风险角色并事前冻结，不能修改这里的门为科学胜出，也不能逐case择优。确认只检 frozen dev 全局角色，不再选择。
