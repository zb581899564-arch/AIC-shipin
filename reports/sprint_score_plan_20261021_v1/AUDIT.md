# 2026-10-21 冲分前代码与证据审计

审计基准：`13d30c7cba42c74d6dec4bc8c93dbe52ecfa73a6`，即最新 `sync/20261021-execution-status`，不是停在10月15日的main，也不是尚写“未运行”的PR3原计划。改动位于独立分支 `sprint/20261021-score-audit`。

## 1. 完成范围

已按当前代码/证据地图审读生产时序合成、原生时间与JSON输出、空间最大合法框与连续中心场、PR3选择/评价/封包、I3D/UMT跨域评价、原TIME训练以及width-only SFT的实际配置、代码和回执。研究复核覆盖官方规则及三天候选的原作者来源。

这是重点调用链审计，不是声称逐行审完全部数千Python文件，更不是已清除所有技术债。本公开镜像没有原始媒体、受限标签、模型、完整raw及实时Linux状态；无法复现模型质量或重新核40.47原ZIP字节。本轮不运行旧launcher、GPU、训练、426生产、封包或提交。

## 2. 真实复现并修复的问题

| 位置 | 旧行为 | 修复 |
|---|---|---|
| `improvement/i3d_umt_v1/crossdata12/common.py::mean_pair_f1` | 直接转bool使NaN、−1、软分数变成阳性；最小例子可输出F1=1.0 | 在转换前要求有限二值、完整形状、非空评审与相同原生帧域 |
| 同目录`review.py::example` | 提前`.astype(bool)`让后续验证再也看不到非法原值 | 读取原始数组，经完整标签合同后再转换 |
| 同目录`audit.py` | 独立复算也提前bool转换，可能与主计算共同吞掉异常 | 独立验证原值及known覆盖，再作集合算术；不调用主评分函数来“独立验证”自身 |
| `common.py::rank_mask` | `groups=[-1,0]`会把−1当末项索引；整数score取负可能溢出；预算/类型约束不完整 | 要求一维有限score、合法非负整数group和整数帧预算；不对数值取负的安全稳定降序，保持原生帧顺序平分规则 |
| `common.py::native_cells` | bool/浮点帧数可在部分路径进入后才报错 | 函数边界明确拒绝非正整数原生帧数 |
| 审计模块导入 | 纯CPU集合算术被顶层Torch依赖阻挡 | Torch导入移到实际模型审计入口，允许真实NumPy定点回归 |

新增回归文件：`improvement/i3d_umt_v1/crossdata12/test_native_metrics.py`。它不读取模型、媒体或历史结果，覆盖非法标签、unknown掩码、负索引、错误预算、短末cell、零/全覆盖、平分顺序，以及有效输入与独立集合算术的一致性。

### 没有偷偷改变的指标

本I3D外部摘要代理既有口径是双方皆空为0，独立审计也如此。它与官方联合评分的双方空为1不同；这是指标口径，不在本轮静默改为1。函数文档与回归明确保留0，历史结果和STOP不改写。

尚无证据表明私有旧输入包含这些非法值，因此不能说修复解释了UMT退化，更不能声称修复提高了官网分数。它防止下一轮评价受到同类静默错误污染。

## 3. 验证入口与结果

定点CPU回归命令：

```bash
python -B -m unittest discover -s improvement/i3d_umt_v1/crossdata12 -p test_native_metrics.py -v
python -O -B -m unittest discover -s improvement/i3d_umt_v1/crossdata12 -p test_native_metrics.py -v
git diff --check
```

普通与`-O`模式验证同一组合同；第二种用于确认新显式校验不会随Python优化删除。独立实现代理实测：**12/12普通模式PASS（0.060秒），同12项`-O`模式PASS（0.037秒）**。新增整数极值用例覆盖uint8、int8最小值与uint64相邻大整数，主排序与独立集合计算一致。只使用真实NumPy/stdlib，没有Torch、媒体、模型或GPU的mock通过声明。

主审独立复跑最终版本：同12项普通模式PASS（0.074秒），`-O`模式PASS（0.035秒），`git diff --check`通过。这里是12项在两种运行模式各执行一次，不把它报告成24个不同测试。

既有`tools/verify_publication.py`实测返回**PASS_PUBLICATION**：7143份有效清单文件、3889份Python语法、历史8个ZIP的SHA/大小/CRC与成员、排除资产和凭据模式扫描均通过。原`docs/publication_manifest.json`的6102条冻结记录与原文件字节不改，沿用增量清单机制，共1046条新增/更新记录。此处历史8包检查不包含未随公开镜像发布的40.47原包，不能替代后者的Linux复核。扫描出现一条历史控制器字符串的`SyntaxWarning`，不是语法失败；本轮不改写冻结历史载荷。

## 4. 已核清的设计限制与文档债

1. **main不是最新终态。** 最新同步已经包含PR3上线33.33及后续全部小试STOP；新README增加本轮计划导航，不合并或覆盖旧分支。
2. **不能把所有空间训练统称失败。** width200有平均+.020598但严重单图−.5002；width1000只有HTTP504准备失败，0新训练。线上39.73是另一个宽度小头。新计划逐项区分。
3. **空间采样先验发生人为变化。** 旧200的35/51/114被抽成134/133/133。新计划将分布权重和部署中心目标列为可检验变量，而非断言唯一根因。
4. **缺失历史索引。** 经验总表引用`ALL_PREVIOUS_STAGE_INDEX.json`，当前公开仓库未包含。新计划明确该范围，使用实际存在的台账/回执；不伪造同名历史文件。
5. **空间max_gap=8是8个原生帧，不是8秒。** 最大合法宽度是现有设计限制，不是本轮首次发现的bug。统一缩框、居中或一般平滑已有线上反证。
6. **旧源码存在不等于当前调用。** 某些历史CFR/parser/扁平导入路径仅是冻结沿革；没有调用证据不改写受保护依赖来“全仓库重构”。
7. **没有发现卡分唯一根因。** 当前主要不确定性是监督语义与部署分布、真实判别能力以及联合时空目标；工程通过和数据完备性只能解决其中一部分。

## 5. 主要实际阅读路径

### 最新状态与失败

- `reports/github_status_20261021_v1/{START_HERE,EXPERIMENT_LEDGER,CODE_AND_EVIDENCE_MAP}.md`
- `reports/github_status_20261021_v1/aggregate_results.json`
- `reports/evidence_reset_goal_20261020_v1/EXPERIENCE_AND_DECISIONS.md`
- `reports/evidence_reset_goal_20261020_v1/{VISION_ATTENTION_PLAN62,RESULTS68}.md`
- `reports/i3d_umt_cross_domain_20261021_v1/RESULT14.md`
- `reports/gnmc_width_sft_iteration_20261013_v1/{protocol.json,terminal_receipt.json}`
- `reports/gnmc_width_sft1000_iteration_20261013_v1/{current_state.json,CONTINUATION.md}`
- `reports/twenty_hour_five_20261014_v1/critic/backup_width_data_expansion_10.md`
- `reports/github_pro_handoff_20261015_v1/PRO_REVIEW_BRIEF.md`
- `reports/midnight_five_verify40_46_20261015_v1/TEACHER_BOTTLENECK.md`

### 代码

- `improvement/temporal_family_native_v3/combine_events.py`
- `improvement/temporal_production_runtime_v5/{infer_batch,output_checks,pr_contract}.py`
- `improvement/content_choice_v1/{contracts,selection,evaluate,verification,render}.py`
- `improvement/full_view_context_v1/{common,prepare,infer,review}.py`
- `improvement/independent_text_grounding_v1/prepare.py`
- `improvement/i3d_umt_v1/human_targets.py`
- `improvement/i3d_umt_v1/crossdata12/{common,prepare,train,review,audit,checks}.py`
- `improvement/scoring_spatial_audit_v1/audit_metric_cases.py`
- `improvement/gnmc_width_sft_v1/{gws_common,train_screen,prepare,evaluate}.py`
- `reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/temporal_sft8b_full_v1/{config.json,train_full.py}`
- `reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/next_round_v1/{spatial_baseline,field_contract}.py`
- 已冻结的`aic6/scoring.py`及其手算案例；本轮不修改它们。

## 6. 后续入口

唯一新计划：[SPRINT_PLAN_20261021.md](../../SPRINT_PLAN_20261021.md)。原NEXT_PLAN/RUNBOOK与历史阶段文件保留其原时间含义；这次不复制出更多可误启动的旧launcher。

当前状态是**工程修复与候选设计完成，新增效果未知**。40.47原包/权重/复现依赖和历史STOP保持；新路线由实际Linux资产核验、冻结配置与结果决定是否进入生产。
