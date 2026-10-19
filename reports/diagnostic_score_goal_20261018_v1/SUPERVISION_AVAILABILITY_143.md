# 已有训练监督可用性：143只读备注

2026-10-18。本Goal的新实验与候选已关闭；本备注只核本地缓存规则、历史审计、训练源码及单条训练记录的字段类型，未访问测试内容/测试GT，未运行模型、训练、下载、解码或旧比较。

**结论：没有发现可直接称为“赛方提供的原始人工联合高光/构图真值”的现存监督。现行缓存规则明确赛方不提供训练集。旧名 `labels/train.jsonl` 确实含可用于构造训练目标的结构化时间与空间字段，并非只有视频或弱文本，但其自述来源是QVHighlights素材上的豆包教师生成标签；是否属于官方某版分享、是否与官方测试/样例共享来源、人工来源、精确媒体对齐和用途许可不能由文件名或旧训练成功推得。**

## 官方范围与此前已审事实

- `reports/recall_expansion_verify40_46_20261014_v1/official_current_01/task.md:50–52`：数据来源条款明确“赛方不提供训练集”，允许合规公开/自建训练数据并要求披露来源、清洗、许可证及用途；赛方提供样例和测试集。`reports/reliable_reference_20261012_v1/rules/official_rules_0930_fitz.txt:63–75` 同义。故历史“提供的分享/训练包”不能自动升格为官方人工训练集或官方联合GT。
- 本问题的标签结构与来源核心**已于本Goal之前的2026-09-17完整审计**：`reports/round6_score_alignment/TRAIN_SET_PRIORITY_CORRECTION_20260917.md`、`reports/round6_score_alignment/training_alignment_20260917/REPORT.md`。143复用这些结果，不重跑987行统计、抽帧/PTS或旧弱指标。
- 原Linux标签路径 `/home/inspur/aic_video_data/labels/train.jsonl`；历史同字节本地副本 `reports/round6_score_alignment/training_alignment_20260917/train.source_copy.jsonl`。旧审计绑定SHA为 `7177731fb7af99e8581c0ec071d116cdb9e6652a6b2b355cd8100364a004c629`。143没有重新核远端驻留或哈希。

## 与官方测试/样例的身份关系：仍有UNKNOWN

- `reports/标签来源复核_20260915.md` 已记录：`/home/inspur/aic_video_data/bddownload.log` 证明 `/高光剪辑训练集/qvhighlights-videos/train.jsonl` 与34个视频ZIP同批入队并下载；日志没有绑定分享ID，不能证明发布者身份。该报告明确“当前987条标签是否属于官方正式监督、参考弱标签或某版材料，尚未确证”。这不是143新发现的未使用人标库。
- `reports/round6_score_alignment/phase1b/source_and_license_audit.json` 记录媒体根 `/home/inspur/aic_video_data/videos`：11576文件、3243个YouTube ID，命名为公开YouTube的150秒窗口。其 `share_origin` 沿用“competition-provided”历史称谓，但证据置信度同时声明分享发布者身份不可从日志验证；不能只引用该称谓、舍去限制。
- 该审计的明确UNKNOWN包括：分享发布者身份、逐视频许可、语料是否与官方测试共享来源。`phase1b/REPORT.md` §4 的路径排除和分辨率/时长元数据弱核对仅覆盖其独立8pilot，且明确不能证明更早原始素材无重合；它**不是**987全体或TIME704父样本/602来源的测试来源隔离证明。
- `training_alignment_20260917/REPORT.md` 的“518条无测试目录路径”和TIME训练器的 `split='train'`/父集合锁只能证明路径及项目内训练分组，不能证明与官方给定测试/样例的媒体身份互斥。现存读取范围没有找到可覆盖全987或TIME704/602、同时绑定官方测试/样例来源ID/哈希的排除证书。
- 因而**既不能判定这987条就是官方测试派生，也不能判定它们已经完成合法外部数据隔离**。对于今后继续使用，原分享身份/范围、原媒体与官方给定素材的身份关系及用途许可属于具体待核项；143不靠名称作定性，不作新的违规结论，也不把旧训练历史改写为已证明合规或不合规。

## 现存标签是什么

| 字段/资产 | 字段类型和目标 | 来源、可用范围与限制 |
|---|---|---|
| `segments` | 对象列表；`start_sec/end_sec/source_start_sec/source_end_sec` 为数值，`start_frame/end_frame` 为整数，另有 `*_seed_score` | 旧审计987行均非空，共1417段。是教师高光区间，可做带噪正区间/JSON格式SFT；不是原始人工无条件高光或完整负例审查。 |
| `cropRois` | `[frame,[x,y,w,h]]` 数值列表 | 624/987行非空，共98242逐帧框；旧审计均为169×300、目标9:16。不可据条目数声称相同数量独立人工判断；不覆盖原生16:9人工训练。 |
| `crop_keyframes` | 对象列表，含 `frame:int,time_sec:number,raw_center:list[number],subject:str,visible:bool,confidence:number` | 旧审计仅9041关键帧，与大量逐帧框并存，存在关键帧派生/插值风险；不是人工轨迹真值证据。 |
| `teacher_signals` | `summary:str`，`timeline` 与 `trajectory` 对象列表，含评分/置信度/描述/中心等 | 明确是教师信号。弱文本和生成目标可存在，但不自动构成独立人工质量依据。 |
| `provenance` | `seed_model/source/license/prompt_version/prompt_fingerprint/annotator_config_sha256/video_sha256` 等字符串，采样fps为数值 | 单条schema元数据核见 `source=QVHighlights`、`seed_model=api_doubao_doubao-seed-2-1-pro-260628`、`spatial_fps=temporal_fps=1.0`；原987行来源判断复用旧完整审计。`quality` 中置信度/一致性字段也不是人标证明。 |
| 媒体映射 | `clip.source_vid/start_sec/end_sec`，历史映射 `reports/orarl_round4/evidence/mapping_rows.jsonl` | 旧审计820可映射、92时间不确定、75缺来源；标签所指加工 `qvh_*` 短片没有独立交付。原短片哈希不等于来源窗口哈希；58有框行曾出现源帧映射重号。不能把原框直接贴到任意来源帧。 |

旧审计已冻结518条/469来源的9:16弱监督候选，见 `training_alignment_20260917/weak_split_manifest.jsonl` 与 `weak_split_summary.json`。该集合也明确为 `WEAK_TEACHER_ALIGNED_CANDIDATE`，并非人工验证集；旧历史曝光和训练/验证同教师相关性保留。

## B_score / TIME实际学了什么

- `reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/temporal_sft8b_full_v1/config.json` 的 `train_manifest` 指向Linux `temporal_sft8b_v1/inputs_01/full_train.jsonl`，`r7_train_registry` 指向同目录 `r7_train_registry.json`；本地同名缓存可查。原704条父样本/602来源组由R7冻结，不是本Goal新数据。
- `temporal_sft8b_v1/sft_contract.py:242–279` 要求父记录与窗口均为 `split='train'`、`label_status='WEAK_TEACHER'`、PTS审计PASS，且父集合严格等于原704。没有把标签升级为人工。
- `temporal_sft8b_v1/train_sft.py` 的 `build_example` 将 `segments_clip_local:list[[number,number]]` 经 `answer_string` 作为assistant区间JSON，用assistant-only CE训练；不是用人工帧级二元高光、自由空间框或成对偏好训练。
- `temporal_sft8b_full_v1/PROTOCOL.md` 已声明724已知正窗口用于区间与终止token CE，30个无已知正交集窗保持UNKNOWN，不制造帧级负例；query-free/穷尽/top-K教师偏差未知。`r7_temporal_pool/.../code/temporal_common.py` 也明确输入不含QVHighlights query、教师summary或cropRois。
- `b_score_aligned_package_v4/config.json` 的 `b_adapter` 复用上述 `temporal_sft8b_full_v1/train_01/adapter`；`whole_teacher_supervision_admitted=false`、`official_score_reconstruction=false`。B_score命名不代表另有官方人工score标签。

## 可作未来方向依据的边界

现存材料支持“已经有结构化**教师弱时序/9:16空间监督**，且部分已有来源对齐证据”，不支持“缺的只是读取官方原人工标签”或“该语料已证明与官方素材隔离”这两种判断。合规训练仍须沿具体数据/标签来源、身份、许可与用途证据判断；规则允许自建数据并不自动替第三方教师输出授权，历史训练完成也不是新的用途许可。143未重新审许可证，未恢复闭源教师渠道，也没有找到新的未曝光人工联合监督。

若未来仍用此材料，应如实标为带噪教师训练目标、保留原映射/UNKNOWN和外部独立人工评价需求；本窗口不据此另起训练、改旧STOP或出包。

## 144后续限定补证

同目录 `SUPERVISION_IDENTITY_INTERSECTION_144.md/.json` 已完成新用途的纯metadata比对：TIME704个不同原媒体SHA与当前正式426身份集合的425个不同媒体SHA交集0；当前ID/SHA集合由主代理本轮只读metadata摘要绑定。该结果仅排除已知完全相同媒体字节，不证明转码/裁切/原YouTube或事件来源无交集。官方manifest无原YouTube ID，原来源交集、分享发布者与用途许可继续UNKNOWN；不以此取得新训练准入。
