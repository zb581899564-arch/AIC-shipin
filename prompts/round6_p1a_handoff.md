# 执行任务：P1a CPU 工程修正与验收

你是执行Agent。读取G:\ai\AIC视频\AGENTS.md、ROADMAP.md、reports/round6_score_alignment/SUPERVISOR_P0_REVIEW.md。后者纠正P0报告；不要照抄phase0/NEXT_STAGE_BRIEF.md中已否决的建议。你不是独占目录，保留所有其他修改，不自行派子代理。只执行P1a，完毕停止。

## 修改范围与预算

仅可在本地round6_score_alignment/p1a/（新代码/测试）和reports/round6_score_alignment/phase1a/（报告）新增文件。目录若存在先盘点，不覆盖未知工作。历史生产代码、phase0、旧提交、原始数据、AGENTS和ROADMAP只读。不连接远端、不联网、不下载、不安装、不用GPU、不解码任何视频、不启动模型、训练、提交。CPU测试总计上限20分钟，新增文件上限100MiB；超限留档停止。

## 任务

1. 固定phase0/evidence/existing_internal_evaluator/的源码哈希，在新模块中复用/适配，不反编译旧pyc。登记偏离现有实现的规则，不标为官方evaluator。
2. 评分接口分离输入校验和数学计算。严格校验失败返回score=null及诊断，不静默删坏项后报高分。合法重复帧全部计Npred，仅首个有效框计IoU。双方空1、单方空0、按索引视频平均乘100。没有参考或参考不全为NOT_COMPUTABLE，不能默认缺失GT为空。仅稀疏空间参考则标SPARSE_DIAGNOSTIC，不生成伪全视频联合分。
3. 编写唯一时间转换模块：新策略[a,b)，CFR使用f/fps时间戳；局部时间先换到真实采样起始帧/PTS基准。VFR接口接受显式PTS；无PTS不伪称支持VFR。视频合法帧0..N-1。另保留旧ceil-halfopen与round-inclusive的独立历史兼容模式用于重放；不得改包或凭未知真值选择模式。
4. 在副本中贯通VALID_NONEMPTY、VALID_EMPTY、INVALID三态，错误有原因。提示词允许0段；训练与推理共用可配置段数约束，不为了1条7段记录静默截断或拼接标签。空结果保持空；INVALID失败退出，不自动转为空或中心80%。保留历史fallback仅在显式legacy_replay模式用于历史复算。
5. 新合成接口要求选中帧的空间来源可追溯。新模式缺同帧/已声明镜头内插值来源则报告NEEDS_SPATIAL_INFERENCE，不自动无限距离复制、偷偷丢帧或借用真值。镜头与插值的行为只用合成样例测试，不实现新模型和镜头检测。历史最近框规则仅用于legacy_replay。
6. 边界测试必须用可手算小例：双空、单空、完全匹配、部分时间交集、空间IoU=0、重复帧降低分数、宏平均≠帧微平均、bool/NaN/Infinity、越界、缺GT、缺预测行、非法JSON；时间模块包含非整数fps、窗口首帧偏移、视频末帧、相邻窗口、VFR PTS。GT框用[x,y,w]，不要将三元组叫bbox_xywh。
7. 对已保存的203个时序窗口与174行第五轮JSONL仅做CPU历史重放：legacy模式帧集合和框必须逐项一致。新时间约定报告帧集合差异；三态模块对现有合法非空文本的解析应保持一致。不得计算任何测试准确率/“时间上界”、不能把旧包当GT，也不产生新提交候选文件。新合成模式应正确识别需重新空间推理的缺口。
8. 写DATA_PILOT_BRIEF.md：只给P1b的8–16来源组试点方案、所需许可/标注/复核证据及现有材料路径，不构建数据集。人工审查未发生就写未完成，不让模型假扮人工标注员。

## 产物与验收

- REPORT.md：改动、原症状复现、通过/失败检查、限制、未完成项。
- protocol.json：内部规范版本、源码/输入哈希、各规则来源、三态与时间约定、模式。
- test_results.json：真实测试结果、用例数和执行命令；不要仅按实现自行生成expected值。
- replay_comparison.json：旧规则逐帧复现、新规则集合差、空间缺口数量；无质量分数。
- DATA_PILOT_BRIEF.md：数据试点建议。

验收标准：手算边界正确，缺GT不得得分，非法输入不得清洗后得分，历史重放174/174一致，新空间模式不再默默远距离复制；源码副本可重复运行，历史受保护输入哈希前后一致。任一失败保留证据，不绕过断言。完成后给总控报告路径和摘要，等待验收，不进入P1b/P2。
