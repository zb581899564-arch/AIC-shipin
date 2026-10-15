# CLI36 五固定窗工程恢复：独立只读意见

审查范围：唯一尚未使用的实际 global CLI36，固定 jobs19..23，共五个完整窗；本次无 AGY、训练、GPU、上传、原文件修改。本意见不构成启动门，也不将准备阶段记为实际成功。

## 结论与权限边界

**可以条件性接受独立新工程路线的设计；当前不能沿用旧 v6 门启动。** 科学固定窗和质量门中未发现每会话最多三窗的科学条款。原容量授权明确 global max36、fresh-only、7200 秒、无自动重试，同时保持每窗供给和原质量门（[容量授权 L37–40](<G:/ai/AIC视频/reports/annotation_iteration_20261010/complete_reference_supplement_v1/teacher_dispatch_capacity_v4_authorization.json:37>)，[科学不变量 L49–59](<G:/ai/AIC视频/reports/annotation_iteration_20261010/complete_reference_supplement_v1/teacher_dispatch_capacity_v4_authorization.json:49>)）。但历史 v3/v4/v5/v6 工程协议确实固定了 CLI35=[19,20]、CLI36=[21,22,23]，而旧 v6 还要求两个有效35前缀才能进入36。CLI35 实际无 ACK、无媒体、无提案，不能满足该前置条件，也不属于“全部有效提案之后的最后非媒体网络错误”例外（[旧固定路由 L5](<G:/ai/AIC视频/reports/annotation_iteration_20261010/complete_reference_supplement_v1/teacher_expansion/engineering_alias_remainder_v6_fresh_scope_prefix_v2/PROTOCOL.md:5>)，[旧停止/例外 L15](<G:/ai/AIC视频/reports/annotation_iteration_20261010/complete_reference_supplement_v1/teacher_expansion/engineering_alias_remainder_v6_fresh_scope_prefix_v2/PROTOCOL.md:15>)）。

因此，ROOT 必须在新独立目录中明确写出前瞻性的路由替代与一次启动准入：只将未成功的19..23送入唯一36；明确 supersede 尚未启动的旧36计划及其35成功前置条件，保留旧 v6 冻结、STOP、实际35原始流和费用；不回写原协议，不将本审查说成既有授权。实际36已用、隐藏模型调用、重跑35、37或自动重试均拒绝。这里是工程路由变化，不能从“没有科学三窗上限”推出旧工程硬约束不存在。

## 科学门和完整分母

当前 registry 固定24，qualified15/rejected4/pending5/acceptedtrain8（[完整登记 L12–16](<G:/ai/AIC视频/reports/annotation_iteration_20261010/complete_reference_supplement_v1/denominator24_v16.json:12>)）；现有 qualified locked 为3窗/2源，待完成19..23均为原 locked 窗。若五窗全部经 ROOT 独立参考准入，locked 结构可恢复到8窗/4源；仅教师供给成功不能保证每窗语义合格。

原质量门保持固定8 locked/4源，至少6 complete，全部4源 informative，至少3 positive源、至少2源有≥5秒NO；其余每源NO假阳性不增加、正例F1宏增益≥0.05、每正例源不退化、至少2源严格改善、precision/recall/event recall不降低、UNKNOWN保守门及正例空窗不增加全部继续适用（[冻结门 L85–99](<G:/ai/AIC视频/reports/annotation_iteration_20261010/slot6_silver24_v1/frozen_protocol_v2_explicit_empty_gate.json:85>)）。不能只对可用或有利子集择优过门，也不能把未完成/UNKNOWN/工程失败转NO或空提案。原门没有要求8/8完整；也不能把最低6完整改成只报告所选6窗。quality failure 后 NO426/no recipe retuning，37.66保底保留，官网提交与生产替换并未授权（[失败与交付边界 L101–104](<G:/ai/AIC视频/reports/annotation_iteration_20261010/slot6_silver24_v1/frozen_protocol_v2_explicit_empty_gate.json:101>)）。

每窗仍必须64原native PNG各恰好一次、按slot的16个四图组全部DONE后立即事实write、全部事实后clip一次、8原effective预览各一次、原KEEP/NO/UNKNOWN和完整域覆盖、原source/domain/PTS/clock/RGB/SHA/geometry/model/schema不变。新只读身份片和ACK可插入供给链，不能插入新视觉材料或跨窗事实（[供给不变量 L50–58](<G:/ai/AIC视频/reports/annotation_iteration_20261010/complete_reference_supplement_v1/teacher_dispatch_capacity_v4_authorization.json:50>)，[观察与语义边界 L7](<G:/ai/AIC视频/reports/annotation_iteration_20261010/complete_reference_supplement_v1/teacher_expansion/engineering_alias_remainder_v6_fresh_scope_prefix_v2/PROTOCOL.md:7>)）。五窗同会话增加上下文串扰风险；每窗proposal须只引用该窗实际事实，不能按此前结果设quota。

## 文字截断与分片

实际35 raw tool元数据只有“261 lines,46545 bytes”，46080截断上限及范围是实际模型最终result的报告，不能混说成原始tool字段；tail marker在46499，ACK不存在，native/facts/clip/effective/proposal均0。最终AGY result SUCCESS仍是整任务REJECT（[实际截断证据 L33–52](<G:/ai/AIC视频/reports/annotation_iteration_20261010/complete_reference_supplement_v1/teacher_expansion/engineering_alias_remainder_v6_fresh_scope_prefix_v2/actual_CLI35_terminal_classification_v1.json:33>)，[任务分类 L55–69](<G:/ai/AIC视频/reports/annotation_iteration_20261010/complete_reference_supplement_v1/teacher_expansion/engineering_alias_remainder_v6_fresh_scope_prefix_v2/actual_CLI35_terminal_classification_v1.json:55>)）。

旧call35的index226175字节/literal45391字节、call36的index335344字节/literal68085字节；仅缩bootstrap还会使后续完整index供给触发同类风险。新计划应将旧巨大index/literal明确保留为program-only冻结审计源，逐个枚举所有teacher可读文字，严格<30000 UTF-8 bytes，而非字符数；每片完整无range view→该片全新唯一tail ACK，禁止marker/ACK期待值在短prompt或其他先读片中提前泄漏。ACK证明文字路径供给，不证明模型理解或事实正确。

26片设计：主指令1 + 每窗header1及native identity/literal片4，共1+5×5=26。必须逐字段证明新26片的合并供给覆盖原完整科学语义与全部必需identity/literal/路径，不得只保留摘要而丢弃ordinal/clock/目标几何/允许输出等原必需字段。片内别名与全部原PNG/clip/effective必须byteexact，程序审计的原字段不得凭“program-only”从教师原本必须获得的信息中消失。分片协议是显式工程供给表示变化，应新冻结并独立审查，旧字节不回写。

## 7200 秒可行性

无额外selfcheck时，每窗64native+16facts+clip1+effective8+proposal1=90；五窗450。26完整文字read+26ACK=52，共502真实核心tools。工具DONE数量与response数量不同；不能据batch宣称真实并发。

实际34为149 DONE tools、wall1613.016秒（[实际wall L11](<G:/ai/AIC视频/reports/annotation_iteration_20261010/complete_reference_supplement_v1/teacher_expansion/engineering_alias_remainder_v5_line_representation_controller/call34/actual_terminal_cost.json:11>)，[实际供给数 L57–58](<G:/ai/AIC视频/reports/annotation_iteration_20261010/complete_reference_supplement_v1/teacher_expansion/engineering_alias_remainder_v5_line_representation_controller/call34/actual_terminal_cost.json:57>)）。简单比例502/149×1613.016=5434.457秒。另读取实际34流中完整w18 proposal前的DONE duration区间约1272.689秒，五倍约6363.447秒；这不是实际五窗wall预测，DONE durations并非严格可加wall，且不含新分片/长上下文的可靠模型。故7200秒内完成**有合理工程可能，但没有保证**，不应把5434–5670作为硬上界。缓存token/usage不等于账单或零费用。

启动后7200原硬cap不延长、不得减少64/16/clip/8供给赶期限；timeout/早停自然保留实际partial/raw/费用，不重试。五窗每个proposal DONE时独立封存stream prefix与当时facts/proposal字节，包含全部中间窗，后续失败不篡改整会话失败分类；之前有效证据只能由ROOT原门另行认定。

## 必须完成的验收

1. 新route admission明确唯一36与五固定job身份、旧35停止及历史费用、原cap/model/环境、旧路由被前瞻替代；实际全局登记须无36 request/child/terminal，而不是仅凭历史文件“not started”。
2. 冻结每片bytes/SHA/LF/唯一tail、完整白名单与所有输入/输出路径。证明26片metadata/literal字段覆盖原教师必需集合，内容<30000 bytes，实际argv UTF16含NUL<32767；短prompt只给入口，不能泄漏尾ACK。
3. CPU dryrun失败测试：任一片缺read、错range、字节/行数/marker错误、漏ACK、换片未完成4组、乱序/重复/漏native、未满64前clip、effective错身份、facts/proposal重写、prefix/output漂移、媒体ERROR、outside路径、terminal早到/timeout、最终proposal后工具均拒绝；不得造实际观测。
4. 实际审计按新供给链逐个检查26 fullread和26 ACK、5×64 native和5×16 facts、clip/effective/完整proposal；读入实际DONE、工具参数、终态及错误顺序。全部中间窗独立prefix，实际输入RGB/geometry/SHA和alias对应原窗，不从模型叙述推断工具完成。
5. wholeCLI状态和scope结构/语义准入分开。最终费用自然终态唯一登记，旧35 wholeREJECT保留；教师一致性不是真值。ROOT逐窗语义审查与原8locked/4source完整表后，才可运行原质量门；不在新结果后改recipe/gate。

本次未审查尚未完成的新v7实际freeze/controller，也未核验任何新AGY请求已发生；本报告是条件设计审查，后续实际代码与科学条款diff须在启动前独立完成。
