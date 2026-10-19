# AIC视频：40.47保护基线与Pro实施交接

**最新状态：2026-10-19。用户反馈最佳40.47不变；最新五包全部回退，停止本次双角色摘要/集合融合族。** 本仓库是代码和研究证据镜像，不是带媒体/权重的开箱推理包。

## 本次请Pro实际改代码

从当前分支 **`review/20261017-correctness-and-score-plan`** 的最新提交开始，PR #1尚未合并；单独拉旧main得不到本次更新。用户授权Pro制定下一轮方案并实现，实际Linux/GPU小试由执行Agent接续。

1. **[最新状态及阅读入口](reports/pro_implementation_handoff_20261019_v1/START_HERE.md)**
2. **[可直接发给Pro的实施提示词](reports/pro_implementation_handoff_20261019_v1/ASK_PRO.md)**
3. [已经做过什么、失败与未知项](reports/pro_implementation_handoff_20261019_v1/EVIDENCE_AND_FAILURES.md)
4. [按机制定位代码](reports/pro_implementation_handoff_20261019_v1/CODE_MAP.md)
5. [明确Linux接口、预算及交接要求](reports/pro_implementation_handoff_20261019_v1/EXECUTION_CONTRACT.md)

下一轮只选择一个可证伪的新能力假设及必要对照。交付应包含代码、CPU检查、明确CLI/配置、有限pilot与独立生产准入；不是换名复活BCE/soft-F1、全源SFT、动量清零、LLM共识或边界扫描。不能将工程成功、外部代理和官方质量混为一谈。

## 最新五包成绩

|编号|固定机制|用户反馈分|相对40.47|
|---|---|---:|---:|
|1|基线保留＋TIME/BASE共同补选|38.10|-2.37|
|2|原选中保留至少一角色支持，保守删选|40.37|-0.10|
|3|原TIME整源重选|37.61|-2.86|
|4|关闭TIME的BASE整源重选|34.74|-5.73|
|5|支持删选＋共同补选|38.04|-2.43|

用户明确保守删选最高；其余按时间和交付顺序推定，未独立登录官网。详见[聚合成绩与身份](reports/pro_implementation_handoff_20261019_v1/latest_five_scores.json)及[复盘](reports/bottleneck_24h_20261019_v1/POSTMORTEM_FIVE_38_10_40_37_37_61_34_74_38_04.md)。五包交付5/5与提分失败分开；不采用批次最高40.37。

40.47原包384630B，SHA256 `b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3`，426来源/123506原生帧。完整BASE+TIME+语义头为8,782,557,449参数。原ZIP、权重和复现依赖保持；本次不新增发布这些资产。

## 已落实的审查修复

10月17日的媒体SHA绑定、真实路径边界、增量发布清单均保留，没有被工作区旧代码覆盖。[原审查](docs/reviews/AIC_REVIEW_AND_SPRINT_20261017.md)和旧记录是历史，不代表其后方案有效或仍在运行。

四组CPU合成回归（不读媒体/模型，不启动launcher）：

```bash
python -B tools/check_review_regressions.py
```

发布字节与资产/凭据模式检查：

```bash
python -B tools/verify_publication.py
```

## 本次同步边界

新增503份Python源码、15份历史审查/复盘及本次交接和聚合回执。3处审查修复保留；19份嵌入部署载荷的生成脚本排除。参见[本次来源清单](reports/pro_implementation_handoff_20261019_v1/publication_scope.json)。

本次没有新增上传媒体、受限标注、逐帧预测/框、提交ZIP、权重、raw、tensor、梯度/优化器、完整输入锁、浏览器状态、凭据或私密讨论。历史已公开文件未删除或改写。原[冻结快照](docs/publication_manifest.json)保留，新增/变更绑定在[增量清单](docs/publication_updates.json)。Linux未公开路径只是接口引用，Pro不能假装已读取相应资产。

## 规则与执行边界

[官方正文](https://www.aicomp.cn/tracks/tracks-6/4267.html)、[通知及附件](https://www.aicomp.cn/notice/notice-3/5307.html)需在新方案/真实运行前核现行版本。官方数据不送闭源标注服务、不用于测试标注训练/伪标签或逐条手调，不以榜单反构规则，不自动官网提交，实际主辅总参数≤9B。公开数据使用范围、原作者任务与来源独立性仍须按证据披露，不能把摘要未选称为明确普通。

用户不安排人工标注，不联系作者或其他聊天。本次只同步GitHub并交接，不启动新实验/Goal/定时任务。数据、准备、训练、评价和封包留Linux，本地只必要小代码、最终ZIP与简短回执。

[本次更新前README](docs/history/README_before_implementation_handoff_20261019.md)及10月15日咨询资料仅是历史；其中旧最佳/在途/计划不能替代此页的当前状态。
