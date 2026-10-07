# 运行和资产说明

## 已包含

训练、开发、时间/空间推理、PTS 和源帧身份合同、受约束 JSON、CPU 镜头检测、严格 loader、封包、交付复核、资源与共享作业控制代码；固定配置、环境 freeze、科学协议、开发聚合指标、工程验收、停止原因与八份历史候选 ZIP。

`reports/.../rematch_exec_20261005T1215Z` 保留完整版本关系。代码实际导入同级公共模块和 vendor 快照，不能只复制单个 `train_full.py`。`docs/publication_manifest.json` 给出每个导出文件的原相对位置、大小、SHA 与类别。

## 需要自行恢复的资产

| 资产 | 如何确定身份 |
| --- | --- |
| 官方训练/测试/复赛媒体与元数据 | 原 intake 验收、媒体字节 SHA、PTS registry；须具备比赛/数据使用权限 |
| 来源隔离弱标签与 train/dev 清单 | 冻结 config 中的 manifest SHA 和 source_lock；UNKNOWN 不作为负类 |
| Qwen3-VL 基座、processor 与 tokenizer | 固定模型 ID/revision、下载 receipt 与文件哈希；不使用未固定的 latest |
| 训练 adapter | Linux/Mac/P2-T2 报告中的 SHA、参数名称和冻结身份；本仓库不包含 `.safetensors` |
| Python/GPU/MPS 环境 | 相应版本环境 freeze 与真实 processor/codec 合同；Linux 核心训练要求 transformers 4.57.1、peft 0.17.1 |
| 作业资源账本与锁 | 原资源策略和追加式账本，不将仓库里的历史 PID/注册当作当前存活证据 |

仓库不包含媒体、逐样本训练标签、权重或环境，所以不能宣称新机器 `git clone` 后即可完成比赛推理。源码中 `/home/inspur/aic_video_work` 等绝对路径是实际冻结实验路径；若在新位置复现，应另建独立运行目录和配置、完成输入/权重/资源验收并重新锁定，保留历史代码与证据不变。

## 建议阅读次序

1. `docs/SOLUTIONS.md` 与目标版本 `PROTOCOL.md`。
2. `temporal_sft8b_v1/sft_contract.py`、`train_sft.py`，然后 `temporal_sft8b_full_v1/full_contract.py`、`train_full.py`、`config.json`。
3. `temporal_sft8b_dev_v1` 的固定开发协议与 decision；Mac 路线另读 `mac8b_delivery_v2/DEV_PROTOCOL.md`、`lowres.py`。
4. `baseline_a_pts_v1` 的源身份/时钟和 native/CFR 分支、`baseline_a_format_recovery_v1` 的 JSON 约束。
5. `b_sft8b_package_v3/runtime.py`、`production.py`、`verify_delivery.py`；Mac 路线为对应 v2。
6. `controller/gpu_run.py` 与版本 controller：阶段成功才接续；失败保留，不删除分母或静默 fallback。

先运行不读媒体、不会启动 GPU 的发布验证：

```bash
python tools/verify_publication.py
```

历史 `launch_registration.json`、`launch.json` 与一次性控制器不可直接重开同名作业。生产推理与弱开发使用不同生成合同，日志已明确记录，不应将它们解释为同一质量协议。

## 现有提交包验收范围

仓库内 ZIP 已逐个核验 SHA、字节数、CRC 和唯一 `predictions.jsonl` 成员。Linux8B 与 4B 完整包的严格 loader 验收见原 delivery 证据。发布验证不会访问官网，不代表重新提交或评分，也不重新加载比赛媒体。

## 当前v7工程修复复现范围

2026-10-07 23:38 UTC+8：全面核查后的 [v7 接续入口](../reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/teacher_student_autopilot_v7/CONTINUE.md) 已单次启动。修复了真实 PTS 到学生目标的精度冲突、helper身份、开发/生产实帧合同、成本与回执等问题；94项CPU合同、10302真实端点、12原目标无损回放及两条真实视频解码通过。旧serializer拒绝11/12，新拒绝0，标签数值变化0。

真实小试12/12全部正、空例0，分布门 `STOP_PILOT_DISTRIBUTION`；第二弱复查2/12、2支持，其余仍在运行，不能宣称字段顺序校准解决质量问题。T更新0、无新T ZIP。完整诊断后保留原科学门，不造空/删样本/盲目全量重跑。详见[全链审计](../reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller/COMPREHENSIVE_AUDIT_20261007.md)。

当前运行234文件锁SHA `70fb36cd016c30dd837f134b907ee75f8582cc957c172ee57a57034d42d4f3dc`。v6/v7测试、precision_helpers、native_segment_contract、cost_contract、真实元数据回放脚本和冻结协议均随仓库发布；媒体、逐样本标签和权重不分发。CPU回放与真实decode证据不冒充CUDA训练或第20步重载。恢复资产后应另建目录和锁，不执行历史一次性launcher。
