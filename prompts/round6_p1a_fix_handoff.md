# P1a 定向修复任务

你是执行Agent。读取AGENTS.md和reports/round6_score_alignment/SUPERVISOR_P1A_REVIEW.md。仅修复总控已复现的问题，不进入P1b/P2。你不是独占目录，保留其他工作。

允许修改本地round6_score_alignment/p1a/源码与测试；新报告只写reports/round6_score_alignment/phase1a_fix/，不覆盖phase1a首次报告。原输入/提交/生产代码/AGENTS/ROADMAP只读。不联网、不连接远端、不用GPU、不安装、不解码视频、不推理、不训练、不上传。CPU上限20分钟，新增100MiB。

1. 先补失败测试，再修load_reference：videos/frames必须为显式正确类型，缺字段、null、非列表、重复video_id都拒绝；允许明确frames:[]。非法参考不可产生OK分数；保留ReferenceError并由公开调用边界转换为明确错误/非零退出。参考元数据缺失不得伪称可信标注。
2. sparse分支只提供已标帧的匹配覆盖和空间IoU等明确诊断。删除/置null逐视频全视频precision/recall/F1/time_F1、未标帧FP、整视频空判断等无依据字段；零已标帧标为无证据，不视为负例。补测试证明未标帧不计假阳性、不会泄漏伪全视频得分。
3. 同镜头最近复制改准确名称SOURCE_SHOT_NEAREST及对应参数/统计，文档不要称线性插值；保留显式距离限制。距离参数要求有限、非bool正整数，拒绝NaN/Infinity等绕过上限的值。不实现新插值算法。
4. compose新模式增加明确顶层状态与可交付标志：INVALID窗口导致失败；合法空可成功；缺空间NEEDS_SPATIAL_INFERENCE不可交付。入口对失败使用非零退出/显式拒绝；legacy历史重放允许记录其历史fallback。补多窗口一好一坏用例，确保不把剩余有效窗口伪装成整视频成功。
5. 修正重复计数说明，以及“1条视频的1帧移除+1帧新增=对称差2帧”表述。不要改旧报告，以勘误新报告说明。
6. 重跑全部原有测试与新增回归、174/174历史重放。若runner硬编码输出到phase1a，先加可选--out-dir并指向phase1a_fix；不得覆盖旧报告。保留受保护输入前后哈希及源码前后差异清单。

交付REPORT.md、test_results.json、replay_comparison.json、协议更新和保护哈希检查。REPORT逐条对应总控问题，包含修复前失败/修复后通过证据与未完成项。不声称提分或批准下一阶段，完成后停止。
