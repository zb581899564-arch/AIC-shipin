# 发布范围与核验

发布时点：2026-10-07（UTC+8）。目标：`zb581899564-arch/AIC-shipin`，公共仓库。

原项目无 Git 仓库，本次在独立发布目录初始化 Git，避免移动、修改或重新锁定正在运行的实验文件。已导出 1585 个原项目文件，其中项目代码与配置 930 个；另添加首页、包清单、方案导航、运行说明和发布验证工具。实际文件清单以 `publication_manifest.json` 和 Git 提交为准。

## 包含

- 项目自有 Python、Shell、PowerShell、JavaScript、Jinja、YAML/TOML 代码及配置，包括历史失败版本、合同测试、帧工具和 vendor 辅助快照。
- 原 Markdown 方案、讨论最终裁决、论文检索结论、验收与历史归因报告。
- 固定配置、源锁、环境 freeze 和有界聚合验收/开发/完成记录。
- 八份明确登记的候选 ZIP、对应成绩证据与 Linux8B 官方结果截图。
- Linux 原生 `inference/baseline_qwen3vl.py` 已经 Mac 跳板读回，并核对冻结 source_lock 的 SHA；本地源项目缺此入口，本次补入发布副本。

## 排除

- 官方/公开视频媒体、数据集 ZIP、逐样本训练标签、完整 train/dev/confirm/holdout 清单和帧预览。
- 基座与 adapter 权重、安装环境、缓存、下载包、论文 PDF、第三方完整临时 checkout。
- 大型逐帧 selected/shots/anchors/provenance、原始模型回答、未解压预测 JSONL（已提交候选 ZIP 内的 `predictions.jsonl` 保留）。
- 临时传输能力配置、凭据、私钥、cookies、日志、PID 临时文件和本次发布工作目录。

这些资产不在仓库中，不代表已删除。冻结配置/源锁中的 SHA、方案与恢复说明保留。原始 `AGENTS.md` 操作历史放在 `docs/history/AGENTS_workspace_snapshot.md`，根 AGENTS 改为发布仓库约定；其余清单中的源文件均按字节复制，不改科学协议。

## 验证

`python tools/verify_publication.py` 检查导出文件大小与 SHA、所有 Python 语法、八包 SHA/CRC/JSON 及复赛 426 记录、排除资产扩展名、常见凭据模式。它不运行训练/推理，也不访问比赛媒体或官网。

发布前另核对核心运行绑定的源码完整性、文档入口链接、GitHub 登录账户、实际 author/committer 和远端 HEAD。工作副本与原冻结实验分离，网站上传和 GitHub 项目发布是不同操作。

## 当前模型状态

2026-10-07 00:07 UTC+8 只读核验 Linux 主机、GPU、内存、磁盘和控制器：Mac8B `RUNNING_REMATCH_TEMPORAL`，控制器存活，固定开发及 NONTEST8 收据已通过 Mac 跳板同步。此快照不承诺后续自动阶段已完成。


2026-10-07 10:27 UTC+8更新：Mac8B完整包已经03:14回传交付，本机SHA/大小/CRC/426记录和独立strict通过；新增包与6项交付证据、修正首页和包清单。GPU空闲，后台控制器已完成；尚无Mac官方成绩。

2026-10-07 13:04 UTC+8更新：新增Linux原地教师下载源码、32B标注/弱审核模块、8B训练与检查点选择模块、原生PTS生产链、一次性后台总控及CPU验收/注册证据。只导出明确列出的源码、固定配方与聚合回执，临时签名CDN地址、GGUF、运行时二进制、逐样本标签和帧不发布。149绑定文件源锁保留哈希与路径，权重字节不随仓库分发。Windows批量搬运停止，Linux新总控已注册并等待教师准备/Z终态；无新T训练完成或官方成绩。

## 2026-10-07 23:38 UTC+8全链审计更新

新增v6/v7工程修复源码、固定协议/源锁、CPU验收、独立真实教师诊断聚合回执和审计。只导出pilot选择哈希/数量、聚合分布与进度，不分发逐样本标签、原始回答、帧或权重。94 CPU/10302端点/两条真实视频通过；十二窗全正、分布拒绝，仍在弱复查，T未开训。实际数量以发布manifest和提交为准，八份历史ZIP及成绩对应关系不变。
