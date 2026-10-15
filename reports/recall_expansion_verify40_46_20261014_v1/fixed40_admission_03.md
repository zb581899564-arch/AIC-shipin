# 固定40观察点：补召回否决准入审计与纯检查器

## 当前结论

新15秒/7.5秒规则要检查全部222个已知ORDINARY观察点，最小必要范围是**9个外部来源的17个完整原源网格视图**。这是纯元数据几何规划，不是实际CPU输入、推理或质量通过。未准备这17视图、未调用模型/复核，只有一次针对R18旧成功clock的严格SSH只读核查。

当前没有可直接引用的、已经证明与这些新视图在源/时间/64帧抽样/张量/提示/模型完全相同的成功B或VERIFY调用。旧40对应45个成功B窗、56个原段可作为历史输入/输出证据，不能把它们改名为新17视图，也不能把旧D8时间集合改称VERIFY40.46基线。新首次调用及独立小量预算，只能在dev和confirm通过后另行登记。

## 原固定40到底是什么

冻结材料为 `reports/reliable_reference_20261012_v1/coverage_diagnostic_01.json`，SHA256 `37a7c93876334b3a5d0c222e3a7f99727778d50f28f3a1172e860d19d3dc82b8`。40个不同外部源共有3081个窗口内观察点：KEEP184（6源）、ORDINARY222（9源）、UNKNOWN2675，只有1个两端dense事件。`coverage_pass=false`、`reference_quality_pass=false` 原样保持。

来源是两名AI在彼此和候选预测盲态下观看既有原生画面后，对**实际观察点**的交集判断，级别是 `AI_REVIEWED_SILVER_NOT_HUMAN_GOLD`，不是人类GT。原QVHighlights查询条件标注不是这批无条件普通标签的替代物。初始/补充4Hz和已完成密集复核只作用于实际看见的同源同PTS点：同密度冲突改UNKNOWN，密集同点证据优先；窗口外上下文不进入分母。R19原声称结束被原尺寸证据否定，结束继续UNKNOWN；不能为本轮重标或扩展。

准确信息见 `improvement/reliable_reference_v1/aggregate_reference.py`、`consensus_v2.py`、`reports/reliable_reference_20261012_v1/REPORT.md`、`COMPARISON_POLICY.md`。源登记由 `source_selection.json` 和 `supplement_review_selection.json` 合成40；都属于已暴露外部开发来源，不是新盲测。旧失败、审查和费用不回写，不重新启动原材料链。

旧否决器实际位置为 `improvement/human_reference_v1/partial_silver_veto_v3.py`，其旧回执为 `reports/human_reference_iteration_20261013_v1/comparison_v3_01/partial_silver_veto.json`（`STOP_NO_ELIGIBLE_CANDIDATE`）。它依赖同一个冻结观察点文件，只对**旧B窗的预登记扩边**求差集。`improvement/videoxum_reference_v1/known_fact_veto.py` 及 `followup_fact_veto_02.py` 也是旧原窗端点变换，不能不执行新候选就证明新KEEP没有新增ORDINARY。

## 旧成功材料、源时钟与身份边界

`reports/boundary_refinement_20261012_v1/developer_readonly_export.json` 的SHA256为 `7feb4cbec6567612e99a98bca708deb5041e38cd0735500a1016263fb43cc8d6`。其中全外部导出有104任务/112窗；本固定40子集对应45个旧成功B窗和56个原段。每个固定case通过以下四元组绑定，不按名称猜同源：

`video_id + source_group + source_key + clock_sha256`，并且每个观察点的 `ordinal` 必须在同一完整clock中精确等于其 `exact_pts`。

旧成功B的 `done_path/done_sha256/raw_sha256`、原始窗口起止和段均在该导出 `entries[].windows` 中；实际路径属于既有 `context_advisory_v1/developer_01/local/.../B0/` 或 `balanced_two_window_risk_v3/developer_01/local/.../BW/`。它们只证明原调用成功与原坐标绑定。文件仍存在、实际input/CPU proof/vision cache/token prompt/model/adapter是否与新请求逐项相同，当前尚未重新验证，不能据旧raw直接跳过新调用。

原完整clock明确引用路径为：

`/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/context_advisory_v1/input_01/<source_key>.clock.json`

clock内的 `source_path` 指向原驻留媒体，原准备代码 `improvement/reliable_reference_v1/prepare_remote.py` 已以source_key核原文件，随后只取观察材料。本次不重做该测量、不读取媒体正文。旧导出只带完整PTS，没有给出旧vision cache/提示/model全部身份闭包，也没有完整导出physical end；不能从末PTS或nominal fps推断物理终点。

## 两种几何不能混用

1. **冻结clip内部网格（本轮不采用）**：把原40观察clip当成新的0起视频来排15/7.5，可得62个overlap视图；其中28个仅在起止几何上与短clip旧B窗一致，34个为新几何。连这28个也尚未证明64帧/张量/提示相同。该62窗会移动起点和右尾，不能冒充生产完整原视频0起网格，不能拿34作为本轮GPU预算。
2. **本轮完整原源网格**：从原媒体normalized PTS零点起，长度15、步长15/2，另加物理终点右对齐的15秒尾窗并去重；每个新KEEP严格限制在产生它的原窗内，不加padding。只需执行其中可能触及已知ORDINARY观察点的窗，其余完整源窗无论怎样产生KEEP，都不可能在这些点新增选择。这个筛选只为原事实否决，不改变生产完整网格，也不据此声称模型效果。

## 最小17视图与精确点覆盖

| case | 外部video_id / 原source_group | ORDINARY点数 | 必须覆盖的完整原源窗口（半开秒区间） |
| --- | --- | ---: | --- |
| R07 | qvh_000263_9x16 / IdpHJK90VDw | 26 | [105,120), [112.5,127.5) |
| R11 | qvh_000159_9x16 / MC6y7jwenlE | 55 | [120,135), [127.5,142.5) |
| R15 | qvh_000679_9x16 / 8vUjoQd0fYY | 25 | [90,105), [97.5,112.5) |
| R18 | qvh_000750_9x16 / Y2GVVC_cD_E | 39 | [499559/4000,559559/4000) |
| R19 | qvh_000265_9x16 / p-III2A1E2o | 45 | [97.5,112.5), [105,120) |
| S08 | qvh_000882_9x16 / QXC-pnmOGnM | 3 | [0,15) |
| S30 | qvh_000729_9x16 / E6yFTWlChmE | 13 | [90,105), [97.5,112.5), [105,120) |
| S32 | qvh_000481_9x16 / iuH6szYVWw4 | 4 | [112.5,127.5), [120,135) |
| S36 | qvh_000482_9x16 / TNkHgO68F6U | 12 | [30,45), [37.5,52.5) |

共9源、222点、17个不同视图。其他8源的16个普通均匀窗，其结束不晚于已有完整clock的末PTS，故不依赖猜physical end；同8源的末PTS已在其最晚ORDINARY点15秒之后，所以任何物理右尾都不会再触这些点。R18需精确右尾，已通过下面的旧元数据核清。新native64抽样仍须按固定公式从完整原钟取64个不同真实帧并接受CPU证据，不能把这张几何表当成输入QA通过。

### R18唯一一次针对性只读回执

经既有严格 `aic-inspur-home`，先确认主机 `inspur-NP5570M5`，只读取其已成功clock（133,840B），SHA仍为 `e0869b5122f9256645167268e9472af5807370c6798aeb4555d4c44493dc3642`。source_key为 `db905f1b79ec7d3771a363a0ef9788b05170a0358a6df9d5d7d1f767a17e3638`，旧驻留source_path为 `/home/inspur/aic_video_data/videos/y/Y2GVVC_cD_E_360.0_510.0.mp4`，没有打开媒体正文。

已保存元数据：`n_frames=3354`，`raw_origin_sec=0.0`，`physical_endpoint_rational=559559/4000`（139.88975秒），`endpoint_kind=ACTUAL_LAST_DECODED_FRAME_PACKET_DURATION`，末PTS `3356353/24000`。因此R18唯一会触ORDINARY点的原源网格窗是右尾 `[499559/4000,559559/4000)`，即[124.88975,139.88975)；[127.5,142.5)及[135,150)不在该完整源内。此前17–19的元数据不确定范围已由原成功测量回执消解，不是新测量、更不是假设视频长度140或150秒。

本次SSH只返回这些小量字段，无新decode/encode/processor/model/replay，不触碰正在运行开发GPU，不枚举媒体目录或全盘。

## 不必强制重跑旧56段的充分条件

记真实VERIFY40.46式基线选择为B，新规则实际完整执行且独立QA通过的新增KEEP集合为K，固定222个明确ORDINARY观察点为O。对任意未知B：

`((B ∪ K) \ B) ⊆ K`。

若实际K与O完全不交，则 `(((B ∪ K) \ B) ∩ O) = ∅`，差分ORDINARY新增必为0。17视图涵盖完整源网格中所有可能触O的窗，其他未执行的网格窗几何上与O不交；在原段不扩边的冻结规则下，不需要为这充分条件执行无关全40视图，或强制把旧56段再复核成baseline。该证明不修改原“ORDINARY新增0”的阈值，也不把旧D8冒充VERIFY。

KEEP删除另由实际 `B ∪ K` 合并且原baseline所有帧/原框保留的工程证据保证；必须同时证明输出恰为baseline加执行通过的显式KEEP，UNKNOWN/DROP没有产生新增，不能只写一个“保留了baseline”布尔值就放行ORDINARY。

若K触O，只能先记 `INCONCLUSIVE_NEEDS_REAL_VERIFY_BASELINE`。这些点可能早已被真实B选中，不能直接说原差分门FAIL，也不能说PASS。只有取得绑定实际同源/同钟/同模型/同提示/同输入的真实VERIFY baseline mask和QA，才能比较 `K ∩ O` 中哪些原来不在B。若证实存在原B未选的ORDINARY点才拒绝；若仍不增加再结合真实baseline保留证据。未知点、摘要未选、动作存在和旧弱标签都不变成普通。

## 新纯否决器的边界

新增且唯一修改的实现为 `improvement/recall_expansion_verify40_46_v1/fixed40_recall_veto_v1.py`。它仅消费未来真实执行证据，不包含启动/下载/解码/processor/张量加载/模型/重放功能；CLI限定现有Linux主机执行。

它要求dev和confirm均按原 `protocol.json` 完整通过后，另登记 `FIXED40_RECALL_FACT_REGISTRATION_V1` 并绑定本检查器、原银标和原B导出SHA。候选完整执行回执与首次独立QA必须列全17视图和所有实际KEEP事件。检查器从同源完整钟及222点重算“0起完整源网格中会触点的窗”集合，缺窗、错源、改端点、缺KEEP执行证据、缺自然资源终态、缺原始raw/request/done/首次QA绑定全部拒绝，不把工程失败写EMPTY或UNKNOWN。

每条KEEP验证实际raw model_call、原始端点、输入source_key、完整native membership、KEEP决定与首次raw/grammar/native重放回执；不会凭调用方给的span或原帧保留标志PASS。真正完整执行后无KEEP可以为合法零贡献事实结果，但必须有实际完整视图和决策分母，不能用缺文件/缺执行模拟零KEEP。

结果状态明确分开：

- `SUFFICIENT_PASS_PENDING_BASELINE_RETENTION_PROOF`：K与O不交，原ORDINARY差分门充分条件成立，但实际基线帧/原框保留证明未齐，不是最终准入。
- `INCONCLUSIVE_NEEDS_REAL_VERIFY_BASELINE`：K触O且没有真实VERIFY baseline，原差分门尚不可判定；不改写为FAIL/PASS。
- `FACT_VETO_PENDING_BASELINE_RETENTION_PROOF`：已有真实VERIFY baseline足以证明差分不新增，但保留证明未齐。
- `REJECT_FIXED40_OBSERVED_FACT_VETO`：真实VERIFY baseline证明新添了明确ORDINARY点。
- `PASS_FIXED40_OBSERVED_FACT_VETO_NOT_QUALITY`：充分条件或真实差分过门，且绑定同次执行、同协议的实际保留/显式KEEP来源证明及独立QA也通过。仍是已知观察点否决通过，不恢复原参考覆盖/质量FAILED，不授权生产或宣称线上提分。

代码顶部列出未来证据adapter的明确schema/状态/必要字段。它不生成这些上游实际回执；目前并不存在此次17视图的真实运行证据，所以尚未运行该否决器。原D8/旧B扩边文件不能改字段后冒充新的baseline或执行成功。

## 后续最小范围与当前验证

dev/confirm通过后，先在Linux复用以上固定源钟和驻留source元数据，登记17个实际native64视图、检查可复用cache的精确身份。当前确认可无条件采用的新17视图成功B/VERIFY调用数为0；若没有完整identity相同的成功材料，登记17次B0首次调用和必要CPU输入准备。VERIFY调用数取决于这17次真实B0原段，尚UNKNOWN，不能拿旧56段或未经语法证实的“每窗5段”当已知实数。一次固定候选、无参数扫描；复核只改提示token时复用同次B0视觉张量，不重做成功解码/processor。

此报告与新脚本读回检查，脚本仅通过本地AST语法解析；没有运行科学检查、没有生成fixed40 PASS回执。旧冻结文件和正在执行的dev源码均未改，新脚本也没有部署到正在运行目录。下一步独立17视图预算、实际CPU/GPU准入和自然资源账本由主代理在dev/confirm通过后决定。到此停止扩展审计。
