# AIC视频高光与构图：代码、失败证据及Pro交接

**模型及成绩快照：2026-10-15，保护基线为高光复核VERIFY用户40.46。** 这是已有项目的公开审阅镜像，不是新模型发布或开箱运行包。

## 2026-10-17 独立审查与代码修复

[完整代码审查、论文依据及截止前冲刺方案](docs/reviews/AIC_REVIEW_AND_SPRINT_20261017.md)。本轮修复了模型回答与接收视频之间的源SHA校验，以及运行文件真实路径校验；新增回归可在旧实现复现失败，修后通过。工程修复不代表已取得新官方成绩。

发布校验器新增[增量文件清单](docs/publication_updates.json)支持，绑定原发布清单并验证变更后的实际字节，保留 10 月 15 日历史快照。下面的统一入口运行四组独立 CPU 检查，不依赖媒体、模型或 GPU。

```bash
python3 -B tools/check_review_regressions.py
```

本轮另确认了强制相对淘汰、最终封包非空恢复、训练排除空窗口和center-only构图的行为限制。下一步建议先测候选覆盖，再对照连续选择头的分类与集合损失。原冻结运行与历史分数继续作为证据；新运行须绑定修后代码及新SHA。

## 给Pro：从这里开始

1. [完整背景与必须回答的问题](reports/github_pro_handoff_20261015_v1/PRO_REVIEW_BRIEF.md)
2. [实验和线上成绩总表](reports/github_pro_handoff_20261015_v1/EXPERIMENT_LEDGER.md)
3. [代码及证据阅读地图](reports/github_pro_handoff_20261015_v1/CODE_AND_EVIDENCE_MAP.md)
4. [可直接发送的Pro咨询词](reports/github_pro_handoff_20261015_v1/ASK_PRO.md)

用户希望获得实质不同的新方法。请先区分监督不足、推理错位与验证目标错位；当前没有证据支持某一个唯一原因。不要将历史工程PASS当语义正确，也不要再用同一批确认数据调边界或无限扩池。

## 最新线上反馈

|上传顺序|方案|用户显示分|相对原VERIFY|
|---|---|---:|---:|
|原基线|高光复核VERIFY|40.46|保护原包|
|1|ACTION动作补召回|40.44|-0.02|
|2|REACTION情绪反应补召回|40.46|显示同分|
|3|INFORMATION信息亮点补召回|40.45|-0.01|
|4|ORDINARY相对删弱|38.83|-1.63|

来源为用户截图及明确上传顺序，未独立登录官网；[逐包SHA绑定回执](reports/midnight_five_verify40_46_20261015_v1/user_score_feedback_four_20261015_01.json)。两位显示同分不证明更高精度成绩相等。原外部代理PASS保留，不能反写为线上提升。

## 当前实现与瓶颈证据

- Qwen3-VL-8B基座+TIME LoRA，实际驻留8,782,459,120参数；时间原生采样/区间JSON，空间center-only+最大合法框+镜头内稀疏锚点插值。
- TIME训练704父片段/602来源/724窗口，5轮/227次更新。审计的808条标签实际来自豆包1fps弱标注，不是Gemini；显式负目标0，没有同源教师受控对照。
- 多轮补召回提高代理recall，但precision或逐源门失败；相对删弱通过4源外部摘要代理，线上仍大幅下降。
- 外部摘要duration-F1缺赛事空间项，语义/原生帧计数也不完全相同。当前验证是否能指导正式目标，是必须独立审查的问题。
- 统一缩框、局部边界扫描和旧失败配方没有稳定突破。尚不能从这些总分判断空间/时间各占多少损失。

## 原包与代码

[原VERIFY40.46 ZIP](deliveries/AIC20H_TEMPORAL_VERIFY_20261014/candidate_TEMPORAL_VERIFY.zip)，380199B，SHA256：

```
86593725c6bad919dc0d342fe98ad65e489a13a6e492da5de3afd247a3226543
```

最新四包见[交付与成绩记录](reports/midnight_five_verify40_46_20261015_v1/DELIVERY.md)。主要代码在`improvement/`，原训练与冻结推理源码也在相应`reports/`阶段目录；先按[阅读地图](reports/github_pro_handoff_20261015_v1/CODE_AND_EVIDENCE_MAP.md)查实际入口。

今晚目标实际4/5；第五并集只做了Linux工程预览，未获新增风险范围批准，未交付。此次GitHub整理没有启动新实验、推理、训练、封包、Goal或心跳。

## 上传范围

- 包含项目源码、提示/配置、协议、可公开的聚合验收/失败记录、已交付提交ZIP及用户成绩证据。
- **不包含**原始视频/图像、完整外部标注、权重、RGB/张量缓存、环境、凭据或浏览器状态。受限第三方数据不随代码公开。
- [逐文件实际导出清单](docs/publication_manifest.json)与[未上传资产清单](docs/excluded_assets_inventory.json)给出边界；未公开的Linux绝对路径只是引用，不能从本仓库访问。没有声称将整台Linux或约30GB工作区全部上传。
- 老文件及失败历史保留；[此前README](docs/history/README_before_pro_review_20261009.md)是历史快照，其中旧最佳/在途阶段不代表当前状态。[项目AGENTS历史快照](docs/history/AGENTS_workspace_snapshot.md)也仅供证据阅读，不能当最新授权执行。
- 仓库没有统一授予第三方数据/模型再分发许可；源码中的原作者声明继续适用。需要数据或权重时按原来源和许可证取得。

## 规则与复现边界

正式测试不标注/训练/伪标签/逐条手调，不送闭源API，不按排行榜反构规则，不自动官网提交；实际主辅≤9B。现有代码中的launcher会依赖Linux资产和旧冻结注册，不应在审阅时直接执行。工程修复、科学质量和官网分数分别报告。

官方入口：[赛题正文](https://www.aicomp.cn/tracks/tracks-6/4267.html)、[通知及附件](https://www.aicomp.cn/notice/notice-3/5307.html)。提出新方案前应核当前规则；已有核查记录不等于未来持续不变。

## 精简附件

如果Pro不能完整浏览仓库，可下载并手动上传[咨询ZIP](review/AIC_PRO_REVIEW_20261015.zip)，包含上述说明、核心代码与原结果回执；它不是新的比赛提交包。
