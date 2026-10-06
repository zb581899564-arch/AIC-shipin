# Pro请求发出后的补充只读代码核对

本文件记录新得到的本地证据，未修改已预留的context-p01.md，未另发Pro请求；不宣称Pro看过本文件。它支持讨论中已提出的合法空/覆盖核验要求，不改变已冻结旧实验。

- `reports/round6_score_alignment/r7_temporal_pool/round7_temporal_pool_20260921T090903Z/code/temporal_common.py:34` 的旧PROMPT要求return between 1 and 5 intervals；`r7_core.py:22` 的validate_segments要求1<=len<=5；`temporal_common.py:132–133` 无可用区间会返回解析失败。新链必须实现空预测与失败两态，并去掉继承的非空和5段上限；完整4B/P2-T2基线如保持旧冻结配方，须如实说明这一限制，不能把新接口功能写成基线已验证能力。
- `code/build_candidates.py:94–102` 记录clip_start_sec/clip_end_sec/clip_duration_sec、segments_clip_local和WEAK_TEACHER。这些字段提供映射起点，但它们本身不能证明教师穷尽看完并标注该span，观察范围与标注完整语义仍待M0核原流程。没有读取任何confirm标签、测试内容或解码视频。
- `code/temporal_common.py:6–10` 说明旧虚拟片段来自源clip_start/clip_end，自解码并设置从0起的frames_indices。新头的PTS格不可凭旧秒数直接相信processor时钟，仍须实际token/源PTS往返验证。

范围：本地只读代码文本；无GPU、安装、下载、远端操作、实验或提交。
