# 复赛主案 C 数据准入审计

结论：**`STOP_C_FORMAL_BCE_UNKNOWN_NEGATIVE_SEMANTICS`**。现有记录有稠密教师分数，不能证明通用高光的负语义、教师实际完整观察或输出穷尽。正式 C 二分类训练不准入；同监督的 4B 二元头也不能绕过此门。工程探针可由主控按另行冻结的工程协议推进，不能将探针数据或 loss 写成可信监督验收。

本审计为 CPU、非测试、只读来源审计，唯一新写入目录是本目录。未使用 GPU、未下载、未改远端、未解码媒体、未读取复赛视频/JSONL 内容、未打开 `confirm_temporal.jsonl` 或解析其标签、未重跑 908 条 PTS、未重切 704/104/100 外层划分。原始标签只按冻结 train/dev 的 `row_index` 解析 808 行，其余行在 JSON 解码前跳过；全文件 SHA-256 只用于字节身份核验。

## 实际统计

| 项目 | train | dev | 合计 |
|---|---:|---:|---:|
| 冻结样本行 | 704 | 104 | 808 |
| YouTube 来源组 | 602 | 96 | 698 |
| clip 时长相加，秒 | 9,246.596 | 1,414.024 | 10,660.620 |
| 已选弱时间段 union 时长相加，秒 | 3,821.187 | 683.289 | 4,504.476 |
| 未选范围时长相加，秒；全部 UNKNOWN | 5,425.409 | 730.735 | 6,156.144 |
| 可证明完整观察的行 | 0 | 0 | 0 |
| 可解释通用高光 TEACHER_NEGATIVE 的行 | 0 | 0 | 0 |
| 正式 BCE 准入行 | 0 | 0 | 0 |

train/dev 的来源组交集为 0，输入 SHA-256 与 R7 原报告一致。时间总量按每条 clip 相加，没有对同源重叠 clip 去重，不能当独立观察时长。正例 union **没有**被用作教师观察范围。逐样本的机器表保留 clip 审计域、现有弱正段、未选 UNKNOWN 段；`verified_teacher_observation_spans_clip_local=[]`，`teacher_negative_spans_clip_local=[]`。

`teacher_semantics_summary.json` 保存统计、字段清单及哈希，`teacher_semantics_train_dev.jsonl` 保存 808 条审计状态和原始标签行号。

## 来源与语义证据表

| 审计项 | 实际证据 | 结论 |
|---|---|---|
| 已选时间段与来源身份 | R7 `code/build_candidates.py:47–77` 校验 clip/源时间公式，`:94–103` 搬运 clip、正段与教师来源；train/dev 808 行与允许原始行的 ID、source_vid、segments 精确一致 | 支持现有弱时间段和映射；不能推出观察范围或穷尽性 |
| 段数合同 | R7 `code/r7_core.py:20–39` 要求 1–5 段；`code/temporal_common.py:26–37` 的后续模型 prompt 要求 1–5 段，`:108–111` 拒绝空和超过 5 段 | 这是后续训练/推理及筛选合同。教师是否被强制 top-K 仍 UNKNOWN，不能把下游 prompt 冒充教师 prompt |
| 教师生成身份 | 允许原始行 `provenance` 全为 `QVHighlights` / `api_doubao_doubao-seed-2-1-pro-260628`；prompt_version、prompt_fingerprint、annotator_config_sha256 统一 | 能定位所缺生成材料；指纹不是 prompt 内容或观察证明 |
| 稠密教师分数 | 808/808 行有 timeline；共 11,611 点，10,861 点 confidence>0，138 点 confidence>0 且 score=0；750 行只有末点 confidence=0，末点 score=0；所有点的 description/phase 均为空 | 分数真实存在于加工标签，语义与后处理未知。零分或低分不能直接当二元通用高光负例 |
| 观察完整性 | 808 行自述 `temporal_fps=1.0`、`quality.timeline_coverage=1.0`，且时间点严格递增、起于 0；无实际 media 请求、抽帧 PTS/帧清单、观测域或生成源码 | 自述覆盖不是实际观测；1 Hz 分数列表不证明视频完整观察或标注穷尽 |
| 截断/补零 | 无 prompt 正文、raw response、finish_reason、token 计数或 truncate 标志；末时间比 clip 时长差范围 [-0.062042, +0.000733] 秒；存在 750 个 confidence=0 的末点 | 输出截断、补点/插值和缺帧处理均 UNKNOWN。不能把零分末点解释为负例 |
| 通用高光任务 | 原始 `source=QVHighlights`、clip 带 `qvh_window`/`used_window`/计划比例；原始记录没有 query 或教师 prompt 正文。R7 `temporal_common.py:13–15` 仅证明后续模型不接收 query/summary | 教师是否 query-free、是否以固定保留比例选择、未选是否通用高光负例均 UNKNOWN。缺 query 字段不证明教师未接收 query |
| 许可与来源 | 808/808 `provenance.license=""`；历史下载记录见 `improvement/round3_supervisor/label_origin_audit.json:188–194`，历史 user/官方分享依据见 `training_alignment_20260917/REPORT.md:7–10` | 有既有来源记录，逐项许可与完整派生链未证。许可单独为待补证门，不能由已下载/历史训练替代 |
| 已有使用边界 | `p2r_reference_gate/round6_p2r_20260919T154701Z/source_and_usage_audit.json:7–10` 只记 existing local weak-supervision research，no redistribution/no per-video license/no external service upload | 可保留既有本地弱研究的历史边界；新复赛训练/作品再分发使用依据应由主控补齐 |
| 独立 query-free 桥接 | 同份既有 registry 的 P1b 为无标注接口媒体（`:13–16`），GNMC 仅空间图像参考（`:19–22`），LIVE-YT/GAICD 未准入（`:25–34`）；`p2r_reference_gate/.../REPORT.md:15–21` 与此一致 | 在本次有界既有记录检查内未找到合法、已有的通用高光时间正负桥接。未联网检索或下载；不宣称全世界不存在该数据 |

主要生成记录只检查现有原始标签的允许 train/dev 行；关联入口限已有来源/使用边界审计与教师 fingerprint 的本地代码检索。对本地 `.py/.yaml/.yml/.toml/.md` 的 exact-key 有界检索仅命中下游 `freeze_r4.py` 及报告，没有找到教师生成器、prompt 正文或配置正文。检索不包含原始/confirm/复赛 JSONL。

## 准入判断

数据正负门 **STOP**：`TEACHER_NEGATIVE=0` 是“已证明的负语义数量为 0”，不代表视频里不存在负内容。正段外范围一律 UNKNOWN；不从 timeline score 挑阈值、不用正段的补集或 union 伪造观察域，不建立正式 BCE 网格，不划正式 train 内校准组，不训练 C/D。没有确认负语义时，写网格训练脚本会把未解决的数据假设变成实现默认值，因此本次只交付审计脚本和机器状态表。

许可门 **UNRESOLVED**：既有报告支持来源来自官方分享/公开视频映射以及限定的本地弱研究历史使用，不能替代本轮所需的原始条款和教师派生依据。A 的历史配方推进由主控单独处理其数据使用依据；本审计没有重新批准 A，也没有否定赛事方可能存在的训练授权。

若后续补齐证明，应以相同 train/dev 清单补审，不重跑 PTS或重切外层 split。有效证明需同时建立真实观察域、通用高光选择语义、无强制 top-K/截断或其精确处理、逐标签生成绑定与许可。跨观察边缘格先 mask；仅完整且有已知正负语义的格才允许目标聚合。阈值/checkpoint 的校准只能在既有 704 train 来源组内另登记，并在正式 104 dev 比较前冻结。

## 远端需补读的材料

本地确切缺少下列内容；记录只携带版本和哈希，**没有给出远端生成器文件路径，不能编造文件名**。主控可在已授权根 `/home/inspur/aic_video_work` 内对这三个键做一次有界只读路径检索，找到后补读匹配文件；不要打开媒体或 confirm 标签，不因缺文件新发外部 API 请求。

主控在本次协作消息中回报：远端限定 `find(maxdepth=4, type=file)`、文件名 `*annotat*config*` / `*compact*` / `*prompt*` / `*teacher*` 未命中生成 prompt/配置，要求结束扩搜。本子审计没有复跑远端命令，此项属于 `MAIN_AGENT_CURRENT_DISCOVERY_REPORTED`；本地证据已经足以维持 STOP，不需继续搜索来完成本次数据门。

1. `prompt_version=seed_temporal_compact_v2_20260812` 的完整 system/user prompt 和渲染模板，校验 `prompt_fingerprint=32dceac323929267ec52e8d64a379013d4664fe0b3fa67a076bd39c59e1ac068`。重点确认通用高光/query、强制比例/top-K、空结果、穷尽要求。
2. 配置正文及生成/后处理源码，校验 `annotator_config_sha256=e44961c8a948f6caf53fb7adce9bbce4e3b2ec0e60886680d9409d2375e944c8`。必须解释 1 Hz timeline 的来源、confidence=0 末点、插值/补点、`timeline_coverage=1.0` 计算式、段选择/长度/数量限制。
3. 仅绑定本次 808 train/dev 行的原始请求/响应与日志：实际送入模型的帧/PTS或媒体 span、采样、query 字段、max_tokens、finish_reason、失败/截断重试、clip→所观察媒体 SHA-256 链。仅配置宣称完整不能替代真实请求。
4. **已知精确远端路径** `/home/inspur/aic_video_data/bddownload.log` 的训练分享来源/归档清单相关行，以及原始分享随附 README/LICENSE/NOTICE 的确切路径和内容。现有日志能证明排队/下载来源，不能单独补出许可；后者路径在本地记录中 UNKNOWN。`/home/inspur/aic_video_data/labels/train.jsonl` 已有哈希一致本地副本，无需重读全部标签。

## 复现与产物

`audit_teacher_semantics.py` 与 `audit_generation_record.py` 均 CPU、禁媒体读取、只解析冻结 train/dev 的原始行，输出采用 `open("x")` 防覆盖。已分别执行退出码 0。重复审计需主控另指定新的输出子目录或保留当前产物后调整写入目录；不能覆盖历史输入。

- 冻结 train SHA-256：`ef427866153a9601be01b6e12356951c2fb56730525b0d7b7c353651c2930ddf`。
- 冻结 dev SHA-256：`53f7053fc3df698ce96c94b04f1af3b5c0c210ce93ecd3269b6306daf4c0a700`。
- 原标签副本 SHA-256：`7177731fb7af99e8581c0ec071d116cdb9e6652a6b2b355cd8100364a004c629`。

本次完成的是数据门审计和机器证据表。没有有效负监督，不交付正式 BCE 网格生成器、训练校准划分或模型训练结论。可决定的状态已完成；远端生成合同和许可材料缺口交主控补证。

`verification.json` 的 10 项一致性检查全部通过：808 条机器状态、样本/生成记录绑定、来源隔离、clip 域守恒、UNKNOWN 未获 BCE 准入、已执行脚本哈希。该 PASS 只表示审计产物一致；正式数据门仍为 STOP。
