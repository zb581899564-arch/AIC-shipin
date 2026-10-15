# VERIFY40.46 新增正证据准入：科学与来源只读审查

审查日期：2026-10-15（Asia/Taipei）。范围：读取既有本地协议、来源登记、ID-only 元数据、媒体回执和旧 prompt 代码；只写本文件与 `reference_candidates.json`。未 SSH、联网、下载媒体、测 clock、解码、运行 processor/模型/QA/launcher，未读取新来源的人工摘要区间、事件文本或结果。

结论：**可登记为与旧双视角投票不同的有界假设，但尚不具有质量准入。** 旧 KEEP 规则偏保留，有直接代码证据；新增候选要求明确的关键/突出视觉证据，UNKNOWN/DROP 不新增，具有独立于那4个已曝光确认视频分数的动机。它没有经过本轮检验，不能据此声称精度会上升。仅以原4源开发，通过冻结门后首次验证新4源；全部通过与固定40事实门通过后，才考虑生产。

## 1. 新决策规则有何证据，不能推出什么

`improvement/candidate_verify_v2/cv_contract.py:63-82` 原文给出的任务是保护“existing visual candidate”：

- 71–72 行允许 `identifiable distinctive content`、`an interesting scene`、`a meaningful visual result`，或其他任一视觉支持的保留理由即可 KEEP。
- 73–74 行只有整段普通、无事件或冗余，且完全没有可保留内容的明确正证据，才 DROP。
- 75–80 行明确稀疏采样缺证据不是普通证据，静态风景、讲课、无声说话、未完成活动不自动普通；不能判断时 UNKNOWN，且 UNKNOWN 保留。
- 94、101–103 行把工程失败和 UNKNOWN 区分，原候选除 DROP 外均保留。

这与保护既有40.46候选的目的相符，但“存在任一保留理由”不是“足以新增未选内容”的相同命题。拟新 prompt 要求明确关键/突出事件证据，单纯物体存在或普通运动不足，证据不足不新增；同时保留静态不自动普通、动作不必完整的语义，构成**非对称新增准入**，不是把旧 DROP 条件改名。这一理由来自决策合同本身，不需要引用新鲜确认4源中的具体视频、标签票或错误时间点。

不过，本审查未证明旧宽 KEEP 就是先前精度下降的唯一原因，也没有独立数据证明新 prompt 的校准效果。同一8.78245912B模型、同一采样视图的再次判断会相关；“新的一次调用”不等于独立模型、独立证据或统计重复确认。新规则只能称待验假设，不能以措辞更严格代替效果验证。

必须在首个新结果前固定请求语义：复核对象是待加入的具体原候选及其相对基线的增量，不能让已有基线内的明显内容替没有证据的新增边缘背书。若实现只看较大完整段，须清楚说明何者是待加入区域，并要求该区域自身有可定位证据；若稀疏采样看不清该区域，返回 UNKNOWN 且不加。不要把已存在的基线候选重新改判、删帧或改框，也不因新规则回写旧 KEEP/UNKNOWN/DROP。

## 2. 旧失败边界保持，开发只能用原4

旧单视图140真实调用/140首次独立QA，以及双视图76真实调用/76首次独立QA均已完成；不得重做其成功 B0、VERIFY、媒体、clock、RGB、primary编码或首次QA。只允许确为新增的正证据准入工作；复用须绑定原输入、prompt、模型和缓存身份，不能因两行元数据相同就假定张量相同。

本轮开发固定为旧 `dev_completion_receipt_01.json:comparison.cases` 的原槽次序：

1. `v_vfJnUQ9Tax0`
2. `v_8tlLBffNjf8`
3. `v__CMIO5R_OGA`
4. `v_voaGOm-rl9Y`

这是原4源，不从12个已曝光源中挑表现好的4个。旧单视图确认4源及双视图确认4源都不能新称盲测，也不参与本轮挑 prompt、阈值或来源。其旧科学 STOP、费用和终态不变。

`rejected_additions_diagnosis_25.json` 已记录77个新增原生帧与原30秒基线显式 DROP 的交集为0；它们也不在原基线上下文已登记的 KEEP/UNKNOWN 事件内。因此单加“禁止复活原 DROP”不能解释或消除那次退化。该描述性结果不能用来按具体坏例添加新阈值。模型 DROP 不是人工真值，摘要未选不是 ORDINARY。

保持八项比较门：完整4源分母；macro F1 差≥0；每源F1差≥−0.01；macro recall 增量≥0.01；macro precision 差≥0；各实际评审baseline召回保持；全部baseline原生帧保持；至少2个来源实际新增原生帧。固定40 KEEP不删、ORDINARY不新增、UNKNOWN限制，以及工程失败不得转空/UNKNOWN继续独立适用。不能将两个确认组或开发结果合并后覆盖失败。

## 3. 来源池按既有哈希次序延伸

唯一已有 ID-only 前缀是旧 `new8_identity_selection_metadata_01.json`：原完整val目录中283个符合原30–60秒范围及旧排除的候选，只导出其中64个ID/duration/hash；这不是新建64份标注。盐保持 `RECALL_VERIFY40_46_VIDE0XUM_SMALL8_20261014_V1`，不重新选盐、改范围、按字节大小排序或读取质量标签。

旧16源登记池实际已有14份媒体：单视图旧10（含2个原生域拒绝）与双视图新4；仅剩 `v_NNuIaUFYGCE`、`v_pHZogKGkc9o` 两个未使用预留。**仅复用旧16池不足4个新确认源。** 沿上述已存在64前缀的原 `selection_hash` 顺序继续，在既有固定公共媒体库存中做ID交集，得到下列4+2。新增6池需在首次新媒体/结果前另作本轮明确登记，不能假称旧协议已登记了它们全部。

| 本轮角色 | 原ID | 作者duration原值 | 历史size_bytes |
| --- | --- | ---: | ---: |
| confirm0 | `v_NNuIaUFYGCE` | 52.08 | 1,673,389 |
| confirm1 | `v_pHZogKGkc9o` | 41.63 | 2,275,440 |
| confirm2 | `v_5FM_xJGb-Tk` | 34.67 | 18,425,235 |
| confirm3 | `v_YW3mCNKVaa4` | 43.14 | 19,389,367 |
| reserve0 | `v_1VDNFR3vQR4` | 53.22 | 4,607,018 |
| reserve1 | `v_SFfB6qvT5FI` | 31.39 | 3,549,249 |

两工程备用之间的 `v__Ga4HoMl6yM` 不在已有固定库存，记录这一元数据事实后跳过；没有尝试URL，更没有依质量跳过。候选的完整URL、原hash、全部未获取的50个已导出ID、旧64保守排除、旧14媒体身份/已知SHA、全40个既往已曝光VideoXum指标身份，均在伴随JSON中逐项列出。已核6个所选ID都不在旧64、旧14或已知692个YouTube IDs中；这只是已知ID隔离。

首4历史合计 **41,763,431B**，备用 **8,156,267B**，6池上界 **49,919,698B**。这是已核固定库存的历史 `size_bytes`，不是当前HTTP大小或已实际下载量。完整公共库存4,056,380B的当前本地SHA与原登记 `b3849e17...55916042` 相符；本轮没有再次获取它。

没有在本地回执中找到已下载且未曝光reserve的证据，不能将“未见”说成远端确定不存在。主线程应先只读核精确6个ID的驻留回执；如果发现既有同身份成功材料则复用，不能重复下载。新确认的首次媒体、clock、输入、模型均必须等原4开发通过后才开始；当前登记候选元数据不授予这些步骤准入。

当前URL可达性、实际下载大小、驻留状态、原生时间域和全文件SHA隔离均**未核实**。历史库存存在不证明今天可访问。URL只沿固定原作者ID到既有公开bucket/CDN路线，完整初始URL在JSON，不发明镜像或读取字幕。

## 4. 许可、任务匹配与隔离限制

复用既有第一方来源范围，不重复同源许可搜索：VideoXum发布标注为Apache-2.0；原YouTube媒体继续受上传者权利与TornadoLabs所述 academic source terms 约束。适用范围为私人外部参考验证，不训练、不重发布原媒体、不主张商业版权。既有用户公开来源→Linux直取的持续许可已覆盖本次6池，主线程也明确确认；不需要再问相同路线许可。

来源依据是已核 `direct_source_scope_05.json`、`source_scope_02.json` 及旧 `videoxum_proxy_scope_02.md`。本次没有重新在线核许可或官方规则；旧规则回执只作依赖，不冒充本轮新的全面官方核验。生产时仍由主线程按项目规则绑定当时正文/附件变更检查。

人工参考是**事件文字引导的人类区间摘要代理**，不是通用高光、明确ORDINARY或赛事密集双比例构图真值。模型只看视频；不能输入 `tsum`、`timestamps`、`vsum`、字幕或评审票。摘要未覆盖部分可以按预登记重合公式进入精度分母，但不能由此给它贴普通负标签；不能训练新准入器去拟合这一负标签。

这对“有界摘要重合代理是否改善”的问题没有致命任务不匹配；若把PASS表述成“通用高光精度已证明提升”“已解决赛事误选”或“保证40.46提分”，则证据与结论不匹配，必须拒绝。新prompt中的关键/突出也不能偷偷改成识别人工事件文本，否则改变推理任务并泄漏答案。

引用原9,575,564B标注文件 `/home/inspur/aic_video_work/videoxum_reference_iteration_20261013_v1/metadata_02/val_videoxum.json`，SHA `2832f423...0f556`，不再下载。未来只在独立评价进程读取固定来源必要原始区间，评审轴动态读取并保留所有实际评审；不能照搬10这一历史常数，也不把1fps数组当原生逐帧GT。原秒端点越界不得截断、拉伸或加epsilon。

已知隔离清单为692个YouTube IDs与1149个媒体SHA；新获取后须再排除这1149、旧14实际SHA及本池互相重复。匿名赛事别名/子片段语义重叠、原作者与镜像编码完全相同、底座预训练全部来源隔离仍UNKNOWN，不能用ID与整文件SHA独立代替这些更强命题。

## 5. 主线程继续所需的实际条件

1. 在任何新结果前冻结新增请求、prompt、允许响应、原增量映射、相同模型资产、单次预算和上列不放宽的门。只有新增显式KEEP可以并入，UNKNOWN/DROP不加；保护40.46全部帧/框/参数。
2. 原4开发只复用已成功的原B0/VERIFY与输入QA；新准入确为新工作才运行。原4全门通过后冻结唯一候选，才允许新4确认的首次媒体/clock/输入/模型；不先看新确认标签选prompt。
3. 将伴随JSON的固定4+2与实际依赖闭包写入本轮唯一注册。Linux先检查既有驻留回执，缺失时按已许可公开来源直取；核当前URL/bytes、真实文件SHA、原生PTS/末端和每个真实CPU输入后才能上GPU。
4. 替补仅适用于预登记的真实媒体404或原生参考域工程拒绝，按reserve次序；网络超时、403/5xx、身份/字节不符、processor、模型或质量失败停止，不能静默换源。成功材料不重做。
5. 新4只确认一次；失败保持STOP，不把它们加入开发再称新盲测。通过后仍须独立固定40事实门及生产准入；本报告、元数据登记、启动成功都不等于这些PASS。

`reference_candidates.json` 已绑定本次实际读到的本地科学/来源依赖路径、字节与SHA。两个Linux `fresh_*registration.json` 本地没有副本，本审查遵守无SSH范围，只从已完成部署回执记录其既有SHA，并读生成代码与元数据输出；未声称独立打开其远端原字节。这一限制在JSON单独标明。

本次新增媒体/标签下载、模型、训练、QA重复、生产和ZIP均为0；旧文件未修改。

## 6. 执行前独立代码审查定稿：可开始工程dev，非质量PASS

主线程采纳了第1节的增量风险，于首次执行前保留未执行的 `protocol.json` 草案，另写 `protocol_v2.json`，没有回写旧结果或旧科学门。本节在运行器代理报告全部修改落盘且不再修改后短读定稿；本审查者没有运行部署器、SSH或真实阶段。

**最终结论：当前静态实现与有界原4源工程dev方案一致，可以由主线程依实时资源和实际依赖准入开始工程dev；这不是开发质量、独立确认、固定40、生产或提交包PASS。**

已核关键链：

- `positive_io.adopted` 逐完整旧CPU/B0/VERIFY、自然GPU终态及首次QA回执绑定实际输入。候选只取旧短视图显式KEEP，唯一零作用省略条件是原生帧集合完全包含于保护baseline；未用人工摘要来筛候选。原26 B0与37 VERIFY成功工作只读采用。
- `positive_contract.novel_support` 从 `native(original candidate) - native(protected baseline)` 的完整集合计算不连续原生run，记录真实PTS/physical_end下的精确区间、局部时间、64原采样中可见的源ordinal与PTS。prompt要求**每个新增run自身**有明确正证据，原baseline高光不能替新边缘背书；KEEP仍返回原candidate端点，不裁新边界、不加padding。
- 对任何零可见run，`request` 将允许决策硬设为 `UNKNOWN/DROP`，`responses`、有限grammar、`resolve`及独立输出解析都保持该子集，不能再生成或接受KEEP。真实执行失败仍阻断，不能伪装UNKNOWN。已只读核 `novel_visibility_inventory_03.json`：当前10个开发候选共10个新增run，每run有1–8个已采样可见帧，零可见run数0；这不是新的解码或模型结果。
- `positive_metrics.baseline_prediction` 与旧 `evaluate_pilot.source_prediction` 的baseline分支逐项一致：保留原non-DROP、原前0.75秒/后0.5秒及长段额外0.25秒、原source全空guard。`positive_evaluate` 只做 `union(baseline, new explicit KEEP)`，并检查所有原生baseline帧及各实际评审召回保留；四源等权分母、动态全评审及原八门均保留，作用来源门为2。
- 标签隔离：准备/推理只读原输入和已验证视觉缓存，采用参考completion指针而不解析 `reference.json` 内容。新的人工区间只在独立评价函数中读取；文本prompt不含 `vsum`、事件文本、字幕、评审票或原KEEP判断。
- 闭包：`positive_io.registration` 在任何新CPU工作前校验新目录全部Python源码及required files，明确要求旧IO/token/metric实现引用在闭包内，并包含实际runtime dependencies、processor assets和CONFIG；新输入token准备、独立token QA、GPU输入锁和raw均再绑定。旧视觉tensor和原输入QA不重算。
- 本次审查指出的export绑定缺口已修复：`positive_evaluate.validate_export_binding` 在逐文件SHA校验后，将每个export的完整 `decision_result` 与实际GPU done及首次output-QA proof精确相等；request/case/group/event/old-event/source/native-range、raw ref和first-input-QA ref也绑定。不能只改export把真实DROP伪造成KEEP。这里只读比较既有JSON，不重复QA。

本审查者独立执行了两个短小纯合成检查：不连续run、分数端点、physical_end、可见native身份和非法ordinal输入；以及零可见KEEP否决、可见三决策、UNKNOWN/DROP不新增、KEEP原端点及执行失败否决，均通过。检查禁写bytecode，没有torch、真实媒体、模型或真实阶段调用。运行器代理另报告全8个Python AST和 `check_pure.py` 通过，包含baseline parity、八门及伪造export/raw-ref拒绝；后者是运行器代理提供的验证结果，未把它冒称本审查者重新运行。

审查定稿绑定如下；这些是科学实现快照，不是提交包完整性验收。本文件不再修改，供主线程随后纳入部署manifest。

| 相对本项目路径 | SHA256 |
| --- | --- |
| `improvement/recall_positive_admission_v1/positive_contract.py` | `b880c0fb87304a39b47cc7fe3023d6f52f905ae64b3684007bc0e5beed5df7ff` |
| `improvement/recall_positive_admission_v1/positive_io.py` | `ab0e233e400957dc81bddb9a464de7da98640b450f9d60fdb0a5e26dbfe7938f` |
| `improvement/recall_positive_admission_v1/positive_metrics.py` | `bdf88ba7c671e6e9fb3787dbf77e8d43c5bcfc3ffdc8f7458d5f1c796e8d7b42` |
| `improvement/recall_positive_admission_v1/positive_runtime.py` | `510a64a1ffb65bafe23b93b20ec42affb5d1b0572aa2bcbcdf2ea2ee19a82044` |
| `improvement/recall_positive_admission_v1/positive_evaluate.py` | `5238db3488740bcaff28ca369381e5d79bc47b67644dfbf80323a9ae3259f82f` |
| `improvement/recall_positive_admission_v1/positive_grammar.py` | `8f065604d191e0e53eed58df70a629fd5ad6af64342b57875f4122e29ee1e2c2` |
| `reports/recall_positive_admission_verify40_46_20261015_v1/protocol_v2.json` | `8736442639beb692eecfd8f3a83404f9c012575f002653e5bdc3cf7811fc00d2` |
| `reports/recall_positive_admission_verify40_46_20261015_v1/novel_visibility_inventory_03.json` | `c2cc0fb8b19fc55dad6b7d0ad5c8c38b709493dc05138f94ebb9229699a41988` |

当前限制：本审查没有执行Linux实际registration校验、真实新prompt token准备/独立QA、唯一共享GPU推理或科学比较，也没有实际验证426帧/框保留、固定40或最终封包。部署器仅检查了registration字段/路径与当前IO的静态兼容性，未执行。主线程报告的最新资源快照及动态资源判断由主线程负责，本审查不把历史峰值或静态阈值替代实时准入。后续实际工程或科学失败必须按原协议保留并停止，不能用本静态结论覆盖。
