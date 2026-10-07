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

## 当前自主诊断复现范围

2026-10-08 01:02 UTC+8：用户已授权完全自主裁决、修复和接续至最终 ZIP，已有监控改为每15分钟静默检查。v7于10月7日23:49:31科学STOP：12/12均正、真实空0，第二真实弱复查12/12为10支持/2拒绝，工程失败0；旧失败与标签保持，T更新0，无新T ZIP。

当前独立 [相对全源摘要必要性诊断v3](../reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/teacher_context_diagnostic_v3/CONTINUE.md)：v2完整4次有/无背景配对均正、状态未变，因此v3改为先说明整段可见主内容、与窗外比较再判断目标保留价值。剩余校准来源只按split内window_id SHA各选2条，不按旧标签或内容筛选；4次判断后全部4次真实弱复查，无配额。校准不是未触碰验证，诊断回答不成为训练标签或人工真值。324项Linux CPU（289实际固定runtime grammar、256真实native时间）和原记录逐SHA/validator回放通过；312文件锁 `f95f3a60b3ab2ac673f899103c5960f4a80ac04667f0287c4144cce2b93b9f6c`，单次launcher历史PID `3210273`。该次实查阶段 `REAL_RELATIVE_SUMMARY_WEAK_REVIEW`，判断 `4/4`、复查 `3/4`、实际命令进程 `2`、所属server `1`。

诊断v1首请求错配frame ordinal与另一帧的秒数，差0.5005秒，被独立validator正确拒绝。v2以每帧完整ordinal/time对象anyOf固定配对，时间用源数据的完整十进制字符串与Decimal验证；固定C++ JSON/runtime numeric常量变位已复现，原失败不改写/复用。见[独立修复](../reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/teacher_context_diagnostic_v2/REPAIR.md)、[科学决策](../reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller/RELATIVE_SUMMARY_DECISION_20261008.md)和[自主接续](../reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller/AUTONOMOUS_EXECUTION_20261008.md)。

完整八请求后按证据独立登记下一监督或可交付8B方案。T仍经原完整质量门推进B LoRA lr1e-5/最多3epochs、第20更新实际重载、开发、NONTEST8、426独立strict ZIP。不重复已证伪配方、不造空或弱化科学门。最终只交付一个Linux ZIP，不自动回传/官网上传；新大流量先许可，Mac不参与。Linux后台计算独立运行；本地定时诊断/修复需要Windows开机且Codex运行。旧预测失效，官网新分未知。

v7的94项CPU、10302实际端点、12原目标无损及两条真实native解码验收仍有效；工程通过不代表标签分布或CUDA训练通过。[全链审计](../reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller/COMPREHENSIVE_AUDIT_20261007.md)保留全部问题与限制。

v6/v7和context v1/v2核心源码、CPU检查、source_lock与聚合停止/验收回执随仓库发布。媒体、逐样本标签/回答、权重不分发。新机器需自行恢复授权资产并另建版本和锁，不执行历史一次性launcher。
