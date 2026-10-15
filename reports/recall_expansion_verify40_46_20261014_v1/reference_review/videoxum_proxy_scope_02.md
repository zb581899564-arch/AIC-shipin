# VERIFY40.46 补召回：VideoXum 新8源摘要代理范围

## 结论与名称

可以用新8源、4开发/4独立确认做有界的“新增候选→语义复核→补召回”工程小试。准确名称为：**无推理查询输入、带事件文本引导的人类多评审摘要代理**。它能检验新增选择是否实际覆盖更多人类摘要，同时是否牺牲摘要重合精度；不提供明确普通段标签，也不证明普适高光真值、构图质量或线上提分。

本报告采用主代理已冻结的 `new8_source_registration_01.json` 作为唯一来源/顺序/预算注册，不另登记另一组。具体新参考区间/文本、媒体、原生解码、模型和GPU均未读取或运行。本审计代理未SSH、未联网补搜相同来源许可，也未恢复旧链；主代理已只读核Linux保留原2001目录的ID/duration元数据，保存了小量选源回执。

## 人工任务和许可：复用第一方已核记录

- [VideoXum 作者数据卡](https://huggingface.co/datasets/jylins/videoxum) 将发布标注标为 Apache-2.0；固定原作者 `val_videoxum.json` revision 为 `c9f0497a3e53b6c776db8f1efcd975242ccad364`。该许可覆盖发布标注，不把原YouTube视频版权转给使用者。
- [作者论文 §3.1.2](https://arxiv.org/html/2303.12060v2#S3.SS1.SSS2) 的人工任务是在事件文字引导下缩短视频段，摘要目标约15%。所以标注任务不能称严格无查询。此次模型只接收视频，不输入 `tsum`、事件 `timestamps`、人工 `vsum` 或其他答案提示；“无查询”只描述此次推理接口。
- 原卡描述每视频多名独立评审，历史版本通常为10份摘要。新实现必须从实际合法 `vsum` 的评审轴读取 `R_i`，核所有事件的评审轴一致，保留全部实际评审，不把10或旧20来源写成新逻辑硬常数。
- 人工缩短区间来自 `vsum`。事件 `timestamps` 是 ActivityNet 事件跨度，不能替代摘要参考；`vsum_onehot` 和 `sampled_frames` 的1fps表示不等于原生逐帧GT。
- 未被 `vsum` 选择只表示摘要未覆盖，不能叫 ORDINARY。以未覆盖部分进入精度分母是代理重合指标的定义，不是赋予它明确负标签。

可核本地证据：`reports/videoxum_reference_iteration_20261013_v1/reference_admission_01.json`、`metadata_registration_02.json`、`PROTOCOL.md`；`reports/sparse_context_iteration_20261013_v1/TASK_ALIGNMENT_AUDIT_06.md`。作者正文副本在 `C:\Users\33056\AppData\Local\Temp\aic_third_reference_20261013\videoxum_card.md`、`jylins_videoxum_README.md`。

## 现有标注与ID元数据位置

| 材料 | 已有位置/绑定 | 本轮复用方法 |
| --- | --- | --- |
| Linux原作者完整val标注 | `/home/inspur/aic_video_work/videoxum_reference_iteration_20261013_v1/metadata_02/val_videoxum.json`，9,575,564B，SHA256 `2832f423ff5fd768a979665e30345a56f1723aacc1821986b5ec042bed30f556` | 不再下载整标注。后续在Linux按冻结新ID提取必要 `vsum`，确认参考只给独立评价进程；先只取ID/duration |
| 作者总source索引 | 同一val列表含2001个source；旧 `metadata_stage_v2.py` 和 `metadata_03/completion.json` 已绑定该作者文件 | 主代理从完整原目录只取ID/duration元数据，不新下载整标签、不查看具体摘要区间；以新30–60秒范围和完整排除集合选源 |
| 本次新ID-only选源回执 | `reports/recall_expansion_verify40_46_20261014_v1/new8_identity_selection_metadata_01.json`，16,144B，`ordered_candidates` 为新范围64个ID/duration记录，`eligible_count=283`，绑定上述作者原文件 | 283为本次新范围满足排除与30–60秒条件的计数；64是按固定新盐导出的候选ID前缀，不是另一个标注集。只核ID字段，不查看未见摘要区间/文本/模型结果 |
| 唯一主注册 | `reports/recall_expansion_verify40_46_20261014_v1/new8_source_registration_01.json`，12,236B | 已冻结新8、8工程替补、组、URL/bytes和新盐；状态为 `FROZEN_EXTERNAL_PROXY_IDENTITIES_BEFORE_MEDIA_MODEL_OR_METRIC_NOT_CPU_ADMISSION` |
| 公共媒体总索引 | `C:\Users\33056\AppData\Local\Temp\aic_third_reference_20261013\tornadolabs_metadata.jsonl`，4,056,380B，15,941行，已登记SHA256 `b3849e17b6b821044c87789c2b1108009a4c50a0b08d255cd908a97255916042` | 仅以原ID、URL、`size_bytes`做交集及预算；这是既有本地文件，不新下载或上传其4MB全文 |

原标注Linux路径由已有 `metadata_control_03.zip` 内 `code/metadata_reference_replay_03.py` 的 BASE/source绑定确认；本次主代理的小量只读选源回执也绑定了同一源路径/大小/SHA。审计代理只读这些本地回执，没有远端实时查看。原标注URL为 [固定作者val文件](https://huggingface.co/datasets/jylins/videoxum/resolve/c9f0497a3e53b6c776db8f1efcd975242ccad364/val_videoxum.json)，只作来源绑定，本轮不重新下载。

## 已曝光28与已知训练/test隔离

真实模型/指标已曝光28应从以下两处合并，不能直接用早期 `effective20_source_registration_05.json` 的 selection代替终态：

1. `reports/videoxum_reference_iteration_20261013_v1/cohort_external_export_08/direct_cohort_06/completion.json` 的 `accepted[].video_id`：实际原20。
2. `reports/sparse_context_iteration_20261013_v1/new_confirm_source_registration_01.json` 的 `selection[].video_id`：后来8来源。

早期有效20登记中 `v_cy-RLevyo_8/v_mh_0QLZhrSY/v_hbipKjS0G7w` 后来因真实原生端点失败分别替补为 `v_fVg3StD8LL0/v_LHewj6shKGw/v_pYbOylWZx-s`，上述终态记录保留了它们。实际28为：

```
v_2Sev8z4P7pE v_4Xvn1xXvYdU v_b_iUgvzb1-0 v_D9A_9FH7e-A
v_dSww-S8qyCM v_eWP99kNayuU v_fdd5ixvEXOE v_fVg3StD8LL0
v_htfrXrKUIzg v_InA8Xbg-hvo v_Jh07fhoPWEI v_Jz9ZxenBLa8
v_jzDXtd0__DM v_LHewj6shKGw v_m4EcgRjCpi8 v_mb1LoOTM_NI
v_OzjjQ4SZ8PY v_PDjtB578yRk v_pYbOylWZx-s v_QCj7IGUGs2Y
v_qH3HnhEaeok v_SEebwJMNMQs v_tgPjcWP7Vig v_V_Nj_BhesEY
v_WBkqGBFsdgI v_WhYyvKiwLc8 v_xBtydVn3MVI v_YL3MvJVk6u0
```

本草案还保守排除全部既有登记/替补：将 `new_confirm_source_registration_01.json` 的 `old_exposed_source_ids`（40）＋`selection`（8）＋`ordered_engineering_reserves`（16）合成64个唯一来源。这64包含实际28；其余不声称全部指标已曝光，只为避免旧来源角色和参考访问范围混淆，全部不作为本轮新8或替补。

已知身份排除文件：`reports/sparse_context_iteration_20261013_v1/known_source_exclusions_01.json`，98,784B；包含692个已知YouTube IDs、1149个已知媒体SHA256，`known_training_groups=602`、`anonymous_test_sources=426` 是计数标量。该文件绑定 `reports/human_reference_iteration_20261013_v1/known_identity_snapshot_01.json` 与 TVSum旧ID目录，旧40已知观察来源也已排除。

新8和替补须同时不在这64以及已知ID集合中。媒体取得后再独立核全文件SHA和实际来源身份；不要看赛事媒体/GT来补身份。匿名赛事别名/子片段语义重叠及底座预训练全来源仍未证明，保留原限制，不能说已全面训练/test语义隔离。

## 主代理已冻结的新8元数据范围

唯一主注册先完整排除真实accepted20、新8以及全部旧登记/工程替补和已知ID，固定 `30 <= author_duration <= 60` 节约小试预算，再按新盐 `RECALL_VERIFY40_46_VIDE0XUM_SMALL8_20261014_V1` 对原目录ID排序，结合现有pin公共媒体索引选出新8与8替补。具体算法、ID顺序与group以主注册为准。本报告表格按主注册的全局顺序读回，不改变它们。此前审计代理基于旧64候选池提出的草案**未采用、未运行**，不作为本轮来源、预算或费用。

| 主注册序号 | 组 | ID（含原作者v_前缀） | 原作者秒数元数据 | 历史媒体bytes |
| ---: | --- | --- | ---: | ---: |
| 1 | dev | v_A0R3KFXD_BU | 46.67 | 21,763,971 |
| 2 | confirm | v_EMDTvPUEr7E | 59.24 | 33,761,792 |
| 3 | dev | v_8tlLBffNjf8 | 32.56 | 5,007,737 |
| 4 | confirm | v_owLQzBg4olo | 30.33 | 3,751,833 |
| 5 | dev | v__CMIO5R_OGA | 35.06 | 2,648,882 |
| 6 | confirm | v_yVrru7t3478 | 50.37 | 3,596,707 |
| 7 | dev | v_voaGOm-rl9Y | 51.8 | 4,476,077 |
| 8 | confirm | v_IcDadC2tw5c | 30.26 | 1,099,013 |

替补也保持主注册全局顺序：1 dev `v_zT6ITDwPi0w`（2,924,229B）；2 confirm `v_rrNJt73BG_8`（4,476,707B）；3 dev `v_vfJnUQ9Tax0`（1,308,495B）；4 confirm `v_17nr8u_ze0o`（8,183,799B）；5 dev `v_isUCIXYjOXE`（4,851,500B）；6 confirm `v_IGamNJ5yIh4`（2,931,217B）；7 dev `v_NNuIaUFYGCE`（1,673,389B）；8 confirm `v_pHZogKGkc9o`（2,275,440B）。实际使用替补时按同组既定队列；共16个唯一ID。替补的subtitle URL仅是发布索引字段，不获取字幕或输入模型。

替补只处理登记的公开来源不可得、身份不符、实际原生时间/解码失败，保持原组和顺序；网络暂时失败/processor失败不能任意换源，不按摘要票、模型表现、是否有作用或指标换源。取得媒体时发现的原端点失败保持，不拉伸/截断参考，不给epsilon补合法性。所有成功阶段不重跑。

主注册已冻结元数据身份；它明确不是CPU或GPU准入。先完成当前metadata/identity准入，再决定是否获取媒体，之后核原生秒端点和真实输入。不能因本报告或主注册产生就宣布原生source lock或GPU准入通过。

## 路线、许可证据与byte边界

原作者 README允许从 ActivityNet官方来源或公开镜像获得来源媒体；本项目已有 `direct_source_scope_05.json`、`source_scope_02.json` 与 `CONTINUATION.md` 记录私人外部研究范围，以及用户对公开来源→Linux直达的持续路线许可。继续使用这条既有范围，无需重新询问相同来源许可。

实际已用媒体发布者为 [TornadoLabs/activitynet](https://huggingface.co/datasets/TornadoLabs/activitynet)，固定目录revision `bc9c567ea67be43daf443cddb832ed983e5ccae5`。已有第一方发布卡 `C:\Users\33056\AppData\Local\Temp\aic_third_reference_20261013\tornadolabs_card_05.md` 明示 academic-source-terms，原视频保留上传者产权，供可复现研究，不承诺完整覆盖或商业权利。它不等于 VideoXum作者标注许可，也不自动给原视频再分发权；此次范围为私人外部参考验证，不训练、不重新发布媒体。

URL模板为 `https://huggingface.co/buckets/TornadoLabs/staging/resolve/videos/activitynet/<youtube_id>.mp4`，其中 `<youtube_id>` 是原作者ID去掉唯一前缀 `v_`。对应逐ID、正常公共CDN→Linux；不回到3fps/42GB整TAR路线，不经Windows媒体中转或Mac，不用账号Cookie或绕过访问限制。此次没有新联网探测，历史目录存在不是当前URL可达证明。

- 初始8媒体按唯一主注册的历史 `size_bytes` 累计 **76,106,012B**（dev 33,896,667B，confirm 42,209,345B）。若把全部8工程替补也计入本次最多16来源，媒体累计上界 **104,730,788B**。这两个值是主注册的计划载荷，不是实际新下载量，也不覆盖任意新数据。
- 主注册12,236B＋ID-only选源回执16,144B，共28,380B；不上传4MB全公共索引或重新下载9.6MB原标签。此前Temp中的旧64池草案未采用，不能拿其预算或ID替换主注册。
- 建议当前metadata阶段新增跨端小回执预算限制为64KiB：只传ID、原duration字符串、组、URL、历史bytes、来源绑定、失败/排除计数。不要传具体参考区间/文本，更不传媒体。全2001 ID/duration索引若后来需要，单独明确其必要性和大小，不能默认为此次8源范围。
- 后续实际媒体获取前核当前逐IDURL/bytes和文件驻留/下载成功状态；大小变化或超上述登记范围时停止定位，不静默扩展载荷。新GPU调用和预算由主代理独立准入，本报告不授予它们。

## 动态评审平均F1的适用范围

作者评价代码逐份参考算F1再取MEAN，另报MAX，并对预测施加其top15%摘要规则。参考副本 `jylins_videoxum_utils.py` 的 `compute_f1` 及 `jylins_videoxum_eval_v2vt_sum.py` 可核；作者原代码有10评审 reshape，这不是新实现必须照抄的科学前提。

本工程小试可采用**原生时间duration重合代理**，明确不是原作者top15%基准成绩：对源i和实际评审j，先把其多个事件 `vsum` 区间组成去重并集 `G_ij`，用原视频PTS解释候选选择时间并集 `A_i`。以时间测度m定义 `F1_ij = 2m(A_i∩G_ij)/(m(A_i)+m(G_ij))`，评审平均为 `mean_j(F1_ij)`，再在该组4个source等权平均。不能合并所有评审GT、只取最佳评审、按帧/时长把长视频加权，也不手选评审。评审数、事件数均动态读实际schema；空参考/零分母和异常schema处理在首次评价前登记，不靠删除评审或换source让指标变好。

相比原始单纯扩边，此次工程问题是候选/复核是否找到了baseline未覆盖且与人工摘要有真实重合的内容。候选保存原baseline帧时，召回“不下降”在数学上通常自动成立，不能单靠它证明方案有效。因此应报告新增时间与 `G_ij` 的真实交集、严格正的平均召回增量、平均F1增量、逐source结果和真正有作用的来源数；主代理在看新参考/结果前冻结本轮独立门。4来源确认足够发现明显退化和无作用，样本小，不能把小幅正差当作统计确定性或普适增益。

新4dev只用于此方向有界开发；通过后冻结唯一候选，再首次评价新4confirm。失败停止这个冻结候选，保留原始数据/成本，不在同4confirm上调阈值或继续换源重试。本次不沿用旧20来源或旧10评审常数，也不改旧L16/GAP100/SPARSE50失败记录。

## 固定事实否决与生产边界

固定40源事实门继续独立执行：已知KEEP不删，已知ORDINARY不新增，UNKNOWN仍未知，不由VideoXum未选参考补负标签。代理上的F1通过与固定40事实否决通过各自报告，不能把其中之一代替另一项。

即使新4dev/4confirm代理和固定事实门全部通过，也只表示这次冻结工程假设在有限代理和已知观察点上得到支持，**仍不等于正式426线上质量或提分**。正式426还必须按主流程核当前赛规、原输入来源/PTS、保存VERIFY40.46基线要求、主辅总参数、自动可复现与格式/包验收；不根据榜单或测试内容反构参数，不人工逐条测试修正。新实验/426推理/封包均由主代理按另行冻结科学协议与实际准入决定。

本次实际新增：网络下载0、具体新 `vsum`/参考文本读取0、媒体0、CPU解码0、模型0、GPU0、实验0、提交ZIP0。既有路径与预算明确标为历史/计划；当前只读scope已具备，实际source/native/GPU准入尚未执行。
