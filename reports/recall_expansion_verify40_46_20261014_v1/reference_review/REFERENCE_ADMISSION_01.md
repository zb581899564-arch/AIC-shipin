# 新增高光召回：外部参考只读准入审计

核对时间：2026-10-14 12:46 UTC。范围：以 VERIFY40.46 的下一轮外部小样本参考为目的，只查原作者元数据；未下载具体高光标签、媒体、模型或开启实验。

## 结论

目前没有已准入、可立即执行的原生20来源独立确认集。最接近本轮任务的是 **YouTube Highlights 的原作者 MTurk 软票**：它是领域高光的人类参考，不能把自动匹配标签或未投票片段当作普通段。已形成12开发/8确认的20来源元数据草案，但原媒体可达性与旧帧号到当前媒体时间的对应关系仍未通过，不能由此启动模型。

**Mr.HiSum 不选为本轮严格人类高光确认**：其参考是观众回放统计，不是逐段人工高光判断；可以另作回放兴趣代理，但不能替代本轮人工确认。已存在的 **CoSum 排除**：作者明确要求评审按查询词选择相关镜头。

## 本地旧证据与本次新查范围

- `reports/videoxum_reference_iteration_20261013_v1/reference_admission_01.json` 已把 CoSum 记为 query-relevant shots；本次读回其证据索引所指的作者 annotation README，复核了这一限制。
- `rg` 未找到本项目既有 YouTube Highlights 或 Mr.HiSum 作者审计。
- 新查仅两个参考家族：YouTube Highlights 与 Mr.HiSum。YouTube Highlights 的2017同作者扩展代码只用于核原帧号/软票 schema，不另作为第三个数据候选。
- 未重复搜索 LIVE-YT 未变化的许可，也未联系任何作者。

## YouTube Highlights：有人工语义，尚未完成输入准入

第一方入口：[原作者项目页](https://aliensunmin.github.io/project/at-a-glance/)、[ECCV 2014 原作者仓库](https://github.com/aliensunmin/DomainSpecificHighlight)、[固定版本 README](https://github.com/aliensunmin/DomainSpecificHighlight/blob/29083d2dc8ee951986f6fb436f1be8f92c8937fd/README.md)。仓库 tree revision 为 `29083d2dc8ee951986f6fb436f1be8f92c8937fd`，GitHub `license` 元数据为 null，根目录未见独立数据 LICENSE；附带 JSONLab 的 BSD 文件只覆盖该库。

| 项目 | 第一方事实 | 本轮判断 |
| --- | --- | --- |
| 标注任务 | 六域 dog/gymnastics/parkour/skating/skiing/surfing 的领域高光；原作者区分自动匹配 raw-edited 标签与 MTurk 人工票 | 无逐视频自然语言查询输入，但仍是领域高光代理，不能称完全无条件/跨领域高光真值 |
| 原始 ID | 各域 `vlist_sel.json` 提供人工筛选的领域相关 YouTube ID，四组为 TraiTightL/TraiLooseL/TestTightL/TestLooseL | 可以事前按作者 train/test 分隔开发和独立确认；与赛事及既有参考的已知身份隔离仍须另查 |
| 人类正证据 | `mturk_label.json` 表示各 clip 被多少评审选中，并按人工区间覆盖程度产生非整数软票 | 保留原票权与 clip 支持范围；不得直接把 `score>0` 当精确二元原生帧 GT |
| 负/忽略 | 自动 `match_label.json` 的 1 为匹配、-1 为未匹配、0 为边界；人工票为0只表示没有评审选择该 clip | 自动 -1 不是人工普通标签，自动0应保持未知；零人工票也不能宣称明确 ORDINARY。需要惩罚非高光扩张时，必须冻结合适的代理指标并说明限制 |
| 时间粒度 | 作者将 clip 写为 `[start_frame,end_frame]`，每段约2秒；示例允许重叠 clip | 不是密集逐帧二元真值；重叠不能重复累计，端点的闭/开含义和原始帧时钟尚缺 |
| 原生映射 | README 和下载脚本没有给出每来源原标注时的 fps/PTS/帧数快照；脚本默认下载 YouTube 当时的最高质量版本 | 不能用当前媒体的 nominal fps 直接把2014 frame index除成秒，也不能拉伸端点、补帧或加 epsilon 放行。须取得可证明对应的媒体版本与时钟 |
| 数据用途 | 作者公开 data/code，并要求使用时引用论文；未见规范化数据许可 | 是公开研究使用邀请的第一方证据，不等于视频版权重新授权，也不产生再分发权。具体数据许可状态应如实披露为未附标准许可证，不能借代码或 JSONLab 许可补齐 |
| 媒体路线 | 作者下载脚本按原 YouTube ID获取；`missingVideos` 允许指向作者登记的备份 ID | 当前可达性必须实测；备份不同 ID还要身份/时间对应，不能仅重命名当原视频；本次未获取备份媒体 |

[作者下载脚本](https://github.com/aliensunmin/DomainSpecificHighlight/blob/29083d2dc8ee951986f6fb436f1be8f92c8937fd/code/downloadVideo.py) 只处理原 ID/缺失备份和视频格式，没有保存原标注帧时钟。2017作者扩展的 [README](https://github.com/tsenghungchen/ranking-highlights-in-personal-videos/blob/f743e7d730c7f1a06a9410812096682db663aace/README.md) 同样区分 hard match 与 soft MTurk；其 `turk` 还是作者 train 的子集，不能把那个库中未证实人工标注的 test 直接视为人类确认集。本次20草案仅来自2014仓库。

### 小20来源草案

完整 ID、原作者 split、预计元数据字节、原URL及工程替补顺序见 `youtube_small20_metadata_draft_01.json`。这是只读元数据草案，**不是实验输入锁或 GPU 准入**。

选择方法在任何具体标签/模型结果前确定：按 `SHA256("VERIFY40.46_RECALL_REF_YTH_20261014_V1|domain|video_id")` 升序，在每域作者 Trai 两组联合池取2来源为开发，形成12；在每域作者 Test 两组联合池取1来源，并按事前固定字母序对 dog/gymnastics 各加1，形成8确认。每域为两组各登记2个工程替补，仅可按媒体缺失/身份/时钟等工程失败顺序替补；不按票、指标、召回或预测换来源。这里哈希只用于与结果无关的选择排序。

| 域 | 开发 ID | 确认 ID |
| --- | --- | --- |
| dog | hseONiKKx_8; BLaQcOcDfjo | wf_qlAizlSM; 9D_Q8l_ruQk |
| gymnastics | bs3ZBcfhvKA; Iss9Ag_wQwM | s6LNwTThBgs; osTqtEzHBsc |
| parkour | e27ppPer9XY; LUhZJLY2uKc | uGLs9atTvNc |
| skating | BdemklZtYWI; FG57uCJvQLw | AJ98A2y1dVw |
| skiing | qBbqK5qlVSM; kAAvTAKkIy4 | 0AHkDElk3ws |
| surfing | CGwtinVGkVU; KzQcJrT91jU | 4RsZz_8d8Ro |

20来源的 `clip.json + mturk_label.json` Git blob size合计 **32,381字节**，六域 `vlist_sel.json` 的原blob size合计 **6,627字节**。前者尚未读取或下载；文件存在和大小不证明内容非空、参考有效、当前媒体可用。不能根据这些名称叫20源已验收。

当前媒体总字节为 **UNKNOWN**：只做了两个无下载 metadata 探测，均未得到 formats/filesize，因此不提供虚假的最小媒体流量数。后续须先获得合法可达、与原标签帧钟对应的各来源格式元数据，再按固定格式累计实际 bytes，说明公开来源→Linux 的媒体载荷。发现的第三方整包不是本次第一方许可或原生映射证据，本次未取其标签/媒体，更没有拉取整包。

### 当前可达性证据

使用 agent-reach 的已可用 `yt-dlp` 后端，只请求 metadata，`--skip-download`，未使用浏览器 Cookie/账号凭据。

1. `hseONiKKx_8`：exit 1，`Private video`。
2. `BLaQcOcDfjo`：exit 1，`Sign in to confirm you're not a bot`。

第二次已表明当前匿名获取路径遇到登录挑战，停止继续批量探测。未更新工具、修改代理/网络、导出 Cookie、绕过限制或转镜像。当前 yt-dlp 为2026.06.09，工具提示版本超过90日；没有借此擅自安装/升级，且旧版提示不抹掉本次具体失败。

### 能继续的最窄路线与缺项

可先完成基于作者邀请使用范围的元数据/软票协议登记，以及开发组的少量 schema读取；保持8确认具体票未向模型和参数选择公开。模型只看合法非测试媒体，不能看参考票。随后只有合法媒体获取、原始帧索引身份/PTS映射、已知赛事身份隔离、固定软票评价和新预算各自通过，才形成可执行20源输入锁。开发后冻结唯一候选，再首次独立确认，不把本次草案当成已经过关。

现在的具体缺项是：媒体获取能力、原标签 frame index对应哪一版媒体/时钟、端点约定，以及适合软人类票且不会把零票等同普通的冻结评价协议。若这些缺项不能以现有公开证据解决，本参考应保持未准入，不能为凑20源降低原生门或换成 weak-match 真值。

## Mr.HiSum：已核数据资产许可，但不匹配严格人工确认

第一方：[作者仓库 README](https://github.com/MRHiSum/MR.HiSum)、[DATASET.md](https://github.com/MRHiSum/MR.HiSum/blob/aeb667f71239887034c2974062a341d312762867/dataset/DATASET.md)、[NeurIPS 官方论文页](https://proceedings.neurips.cc/paper_files/paper/2023/hash/7f880e3a325b06e3601af1384a653038-Abstract-Datasets_and_Benchmarks.html)。tree revision 为 `aeb667f71239887034c2974062a341d312762867`。

- 作者称31892个 YouTube-8M 来源，`gtscore` 是0–1归一化 Most Replayed；`gtsummary` 由 KTS shots 和0/1 knapsack生成。没有查询输入，但也没有逐段人工高光正/负/忽略判定。低回放分数不能叫普通，未选 summary也不能叫普通。
- 作者 [preprocess.py](https://github.com/MRHiSum/MR.HiSum/blob/aeb667f71239887034c2974062a341d312762867/preprocess/preprocess.py) 把100个回放热度箱的分数按 `markerDurationMillis` 映到逐秒序列；这不是原媒体帧 PTS标签。`gtsummary` 不是独立人工参考。
- 作者 [crawler.py](https://github.com/MRHiSum/MR.HiSum/blob/aeb667f71239887034c2974062a341d312762867/dataset/crawler.py) 直接读取网页回放热度，明确记录回放功能可能消失；重新抓取会得到当前状态，不能自动当作论文时冻结标注。
- 作者明确数据资产 CC BY4.0，并要求遵守 YouTube/YouTube API条款；这不是替第三方视频重新授权。metadata.csv 提供 `video_id/yt8m_file/random_id/youtube_id/duration/views/labels` 的原ID映射；README指出按该映射获取 YouTube来源，没有新获授权媒体字节清单。
- 本次未下载 `mr_hisum.h5`、metadata.csv整包、YouTube-8M features、回放标签或视频。即使原媒体可达，它也只能进入另行标明的回放代理开发，不能填补本轮人类确认缺口。

## CoSum：复核旧排除，不另起路线

[作者 annotation README](https://github.com/l2ior/cosum/tree/master/annotation) 明确三评审每人获得query词，选择10%–50%觉得与query相关的shots，至少两票组成summary；列出的标注全为选中shot的1。它不是本轮无查询高光参考，也没有把其他shots标成普通。本次复用既有作者正文副本，未重新搜索同源许可、未取任何标签/视频。

## 曝光登记与工具范围

- YouTube Highlights：读取所有六域 `vlist_sel.json` 的413个原ID和作者 split，读取 Git tree中的文件名/大小；具体20源及替补的 `clip.json/mturk_label.json/match_label.json` 均未打开。READMEs中2/3/0的票例是说明性 schema示例，不能作为任何来源质量证据。项目页展示的自动排名案例及其 source ID已公开见到，不称盲测。
- Mr.HiSum：读取 README的三个具名回放展示（`hqm6r8xeAew/q89vpZ1kwpM/H-0RHqDWcJE`）的文字说明，以及 DATASET.md 的示例 ID和类别 schema；这些是已曝光展示，不能新称确认源。未读取实际回放数组或媒体。
- CoSum：只看既有作者说明/少量视频URL的文字，未看具体shot人工选择列表。
- 使用 agent-reach 的 `gh CLI`、Jina网页阅读和 `yt-dlp` 元数据后端；doctor显示可用。Exa首个检索成功，第二个返回免费额度耗尽，后续只按已发现作者链接用 gh/Jina读取，未安装/配置新服务。
- 网页/临时元数据放 `C:\Users\33056\AppData\Local\Temp\aic_recall_reference_20261014`。仅在本报告目录写报告和20源元数据草案；未改主状态/AGENTS、旧质量门、费用、实验、Goal或心跳。

**实际新增：媒体0、具体高光标签文件0、模型0、GPU0、实验0、提交ZIP0。**
