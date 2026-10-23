# AIC视频：最后24小时生产探索实现（2026-10-23）

本轮在用户最新授权下，基于精确 `e8224c4339007790a1be383be19fdb200cc817bc` 实现三条主机制和三个固定结构对照。首个执行目标为 `g_subject` 全426可提交包；新候选跳过新增离线质量门，保留一次真实工程冒烟和全部封包检查。**当前仅公开CPU工程检查通过，尚无本轮真实Linux推理、质量验证或新成绩。**

- [冲刺计划：失败地图、八项研究筛选、六候选与24小时安排](FINAL_SPRINT_PLAN_20261023.md)
- [给GPT-6.1-sol的Linux RUNBOOK](improvement/final_sprint_v1/RUNBOOK.md)
- [机器候选注册](improvement/final_sprint_v1/candidates.json)
- [已运行/未运行检查与首跑风险](improvement/final_sprint_v1/VALIDATION.md)
- [可选CG-DETR/CLIP精确资产与直连步骤](improvement/final_sprint_v1/OPTIONAL_SPECIALIST.md)
- [此次新增公开范围](docs/publication_scope_final_sprint_20261023.json)

两份40.48/40.47原ZIP及依赖不动；不恢复CONTROL5和旧科学失败，不上传私有媒体、权重、raw、tensor、完整输入锁或新预测ZIP。赛程24小时与两天各5次来自用户最新消息，没有独立核实延期。正式提交由用户/执行端人工完成。

---

# 已完成历史：40.48反馈最佳与2026-10-23完整T分支终态

**最新同步2026-10-23：40.48删弱包为当前用户反馈最佳，原40.47及两者依赖均保护。真实局部注意力25窗8B小试与全部独立QA已完成，但选片退化；新T ZIP仍0。**

- [最新事实与接续边界](reports/github_status_20261023_v1/START_HERE.md)
- [10月21–23日完整实验增量](reports/github_status_20261023_v1/EXPERIMENT_LEDGER.md)
- [代码与证据地图](reports/github_status_20261023_v1/CODE_AND_EVIDENCE_MAP.md)
- [结构化聚合结果与短回执绑定](reports/github_status_20261023_v1/aggregate_results.json)
- [本次安全发布范围](docs/publication_scope_20261023.json)

本次基于已采纳PR #5精确提交72533ece；源码、历史预算和CPU检查不是实验启动授权。媒体、受限标注、权重、tensor、完整输入锁、raw和新预测ZIP不公开。下方为保留的旧快照，最新事实以本节入口为准。

---

# 历史：40.47保护基线与2026-10-21真实终态

**最新同步：2026-10-21。受保护最佳仍为用户反馈40.47；PR #3已实际跑完，contrast线上33.33，后续四包与固定中心均回退；最新同帧视野小试STOP，没有新提分包。**

本仓库是项目源码与研究证据镜像，不包含所需媒体、受限标注、模型权重和运行缓存。历史脚本和协议的存在不是启动授权；请从下面入口读真实终态，避免把旧计划当作尚未执行。

## 10月21日本轮审计与三天冲分计划

- **[SPRINT_PLAN_20261021：空间分布纠偏、独立裁剪判别、时间长训、声音事件与约13次提交队列](SPRINT_PLAN_20261021.md)**
- **[本轮代码修复、证据纠偏和验证范围](reports/sprint_score_plan_20261021_v1/AUDIT.md)**

本轮基于`13d30c7`审阅并修复I3D/UMT外部评价中非法标签及原生索引可被静默接受的问题；保留该历史代理的指标口径和全部旧结果。新计划特别区分width200的平均正信号与严重过缩、width1000的准备失败、以及线上39.73的另一宽度小头。候选尚未运行，没有新提分或新ZIP，40.47保护状态不变。

## 2026-10-21历史入口

- **[START_HERE：完整现状与续接边界](reports/github_status_20261021_v1/START_HERE.md)**
- **[实验和线上成绩总表](reports/github_status_20261021_v1/EXPERIMENT_LEDGER.md)**
- **[结构化聚合结果与短回执SHA绑定](reports/github_status_20261021_v1/aggregate_results.json)**
- **[代码与证据地图](reports/github_status_20261021_v1/CODE_AND_EVIDENCE_MAP.md)**
- **[本次发布范围与保留的审查修复](docs/publication_scope_20261021.json)**

## 本次补齐的真实结果

| 方向 | 已发生的事实 | 决定 |
| --- | --- | --- |
| PR3 contrast | 外部时间代理微升且区间跨0；426/522生产与独立验收完整；用户反馈33.33 | 不采用 |
| PR3 critic / observation | 内容排序未胜shape/permuted；改变观测未胜原TIME | 两条原STOP保持 |
| 四个整包风险对照 | 官网实际DONE：38.63 / 40.36 / 33.47 / 37.70 | 均未超过40.47 |
| 统一中心位置 | 保持时间和尺寸，官网35.00 | 停止这次替换 |
| 冻结音频融合、耦合监督单步、视觉读出和视觉LoRA | 均有真实小试；未达到其固定对照，未按训练拟合放行 | 保留全部STOP |
| 新视觉＋原TIME43 | 原TIME F1 .275562262→.274175438 | 不生产 |
| I3D＋UMT跨数据集 | 控制F1 .271738599→.260300189，3/8来源改善 | 不生产 |
| CLIP / X-CLIP宽事件检索 | 静态仅4/8胜同视频错配；视频AP .423638764低于静态.488629118 | 不自动查询或生产 |
| 同原生帧中心 / 完整视野 | 稀疏点AP .656392668→.641352986，3/6可评分源改善 | 固定视野方案停止 |

外部摘要F1、人工宽事件查询AP、配对准确率与官网时空联合总分不是同一指标。上述小试失败只否定其固定配方，不证明所有时序、音频、视觉学习或全视野方法无效。全部已曝光外部指标如实登记，不称独立盲测；不能靠换阈值、提示、填充或逐测试来源开关包装新方向。

40.47原包384630字节，SHA256 `b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3`；426来源/123506帧、完整原管线8,782,557,449参数，原包及依赖不变。本次不新增发布任何提交ZIP、预测、媒体、标签、raw、tensor或权重。

## 代码沿革与发布方式

本次从PR #3精确提交`cb6095cc3156319054f23e5a3ad5baeb5ed9d0c1`增量更新，保留PR #1的媒体SHA/真实路径/清单修复、PR #2的DPO实现以及PR #3三候选代码。没有用工作区旧代码覆盖审查修复；没有合并或改写旧PR/提交历史。新状态在本同步分支中，旧main和未合并PR的页面不是最新运行状态。

PR3原[PLAN](improvement/content_choice_v1/PLAN.md)与[RUNBOOK](improvement/content_choice_v1/RUNBOOK.md)仍是精确实施历史，其“未运行”事项以本页最新真实终态解释。根[NEXT_PLAN](NEXT_PLAN.md)和[RUNBOOK](RUNBOOK.md)是更早DPO方案，不能当作本次启动入口。[10月19日首页快照](docs/history/README_before_status_20261021.md)保留原样。

## 核验和边界

本次是增量发布，不启动新实验。发布检查核源码语法、清单大小/SHA、资产和凭据模式，以及原有历史档案完整性；不会为刷新数字重跑成功训练、推理、重放或比较。冻结原发布清单保留，变更登记在[增量清单](docs/publication_updates.json)。

[官方正文](https://www.aicomp.cn/tracks/tracks-6/4267.html)与[通知/附件](https://www.aicomp.cn/notice/notice-3/5307.html)应在未来新实验及生产前核现行版本。实际全部主辅参数≤9B，官方数据不送闭源服务、不用测试标签训练/伪标签/逐条手调，不依据榜单反构隐藏标注，不自动官网提交。第三方模型/数据用途与原生映射需要各自证据；本仓库不转授其权利。

计算与完整证据留Linux，Windows仅部署必要小代码、接收最终ZIP和短回执。需要的数据/模型/代码/依赖下载在实际直连核实时已有长期授权；非直连或路线未知先询问。没有新的Goal、定时或作者/跨聊天联系；旧受控停止进程禁止恢复。本次发布不代表总体改进任务已经成功或所有合理方向已穷尽。
