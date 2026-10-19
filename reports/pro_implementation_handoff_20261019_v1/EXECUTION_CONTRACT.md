# Pro代码到Linux执行的交接合同

## 两个角色

**Pro**：在GitHub直接审查、制定一个下一轮主线、实现代码及必要CPU检查，提交到分支/PR。可以复用现有实现，不能把旧机制重新命名。没有访问Linux资产时，不声称已运行真实模型/验证质量。

**执行Agent**：收到用户转来的PR/commit，先保护工作区并审差异、配置/来源/预算，部署必要小代码到Linux；完成真实小试与判定后，才决定是否正式426生产及封包。不自动合并不明改动，不重复旧成功阶段，不凭Pro建议自动扩大授权。

## Linux可引用的运行接口

这些是现存路径接口，不保证在Pro环境可读，也不是新增执行授权。不要在GitHub索取、上传或伪造资产。

|接口|位置或要求|
|---|---|
|Linux项目根|`/home/inspur/aic_video_work`|
|隔离Python|`/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python`|
|40.47原包|`semantic_context_production_20261016_v1/package/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip`，相对Linux根|
|40.47运行配置|`semantic_context_production_20261016_v1/production_registration.json`|
|10月19日外部输入/训练/证据|`bottleneck_24h_20261019_v1/`|
|纠偏20权重/输出|`bottleneck_24h_20261019_v1/summary_objective_v20/`，失败，禁止生产|
|实际最新正式输入/1044输出|`five_summary_sprint_20261019_v41/`，完成且该族STOP|
|唯一共享GPU wrapper|`round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/resource_unlimited_v1_20261007/gpu_run.py`|
|原空间/原生renderer|同一`rematch_exec_20261005T1215Z/`中的`b_score_aligned_package_v4/field_contract.py`与`baseline_a_pts_v1/pts_contract.py`|

资产manifest由执行Agent从实际文件生成或引用已验收绑定；Pro不要编造hash、revision、样本数、checkpoint路径或当前可用资源。采用已成功输入需验证身份和新用途是否相同；新映射/新监督合同仍需首次真实检查，不能借旧PASS代替。

## 新实现必须交出的最小运行结构

1. 一个明确入口，例如`python -m improvement.<new_mechanism>.run --config CONFIG --assets PRIVATE_ASSET_MANIFEST --stage pilot`。具体名称由Pro决定；不能保留模糊的“最新vN”查找。
2. 可审查配置：假设、单一变量/对照、样本/曝光范围、源级分组、原生时钟、目标/空含义、模型计数、固定更新/调用数、seed、final-only规则、预算和停止点。样例配置不带真实官方记录/预测。
3. `preflight`不启动训练；检查缺项/资源/绑定后显式报错。共享任务按当时资源和工作集动态判断，不写死空闲显存/CPU/磁盘准入门槛，不抢占外部作业。
4. `pilot`为一次有限真实实验，先验证新合同，再报告机制效果、增删/空输出/明显退化与成本；支持幂等拒绝重复启动，失败与合法空分开。
5. 正式生产/封包是独立显式阶段，要求新的admission，默认不能在pilot后自动开启426。未知效果不等于可忽略明显崩塌；不要恢复不相称的通用代理F1硬门或强制非空保底。
6. CPU检查只覆盖实际风险：映射/重叠去重、未知标签mask、序列目标与causal shift、梯度/冻结、保存重载、adapter状态或JSON严格性，按新机制选择。不为数量跑全库，不在导入时下载/联网/启动GPU。

## 科学与赛规边界

- 先核现行[官方正文](https://www.aicomp.cn/tracks/tracks-6/4267.html)、[通知及附件](https://www.aicomp.cn/notice/notice-3/5307.html)。引用正文支持的结论；规则解读不是赛方特别许可。无法访问就注明，执行Agent在真实运行前复核，不自行猜允许。
- 官方测试/样例不送闭源服务、不标注/训练/伪标签/逐条手调。不据排行榜总分反构参考偏好、阈值、题材规则或逐源开关。不自动官网提交。
- 新增监督只用来源与用途明确的公开材料；原作者标注任务、license和native映射要匹配声明范围。不得把query相关性、摘要未选、低票或稀疏未标当穷尽负例。
- 不新增模型下载；之前Tiny≤80MB是已经使用的单次例外。需要额外资产/权利时准确列出缺项，不调用、不让执行Agent盲下。
- 实际全流程主辅参数≤9B，不能只数可训练参数；含被继承预测依赖的小头，共享基座计一次。
- 40.47原包和依赖、全部历史成功/失败/raw/费用/锁不修改。新候选可单独声明允许补选/删选/替换，但不能拿“原包保护”冒充所有新包自动只增不删，也不能把风险授权当工程或科学通过。
- 数据、准备、训练、比较、独立复核、封包全部在Linux。本地只必要小代码、最终ZIP和简短回执；完整raw/模型/媒体不往返。
- 不联系作者或其他聊天；不改SSH/Tailscale/EasyTier/代理/服务、不用Mac、不建Goal或定时任务、不执行历史CONTROL5。旧期限/旧授权不能自动当新轮预算。

## 交回给执行Agent的内容

准确PR链接与commit SHA、更改文件、当前CPU检查命令/结果、未运行项、Linux依赖与明确命令、预期报告schema、最大实际模型调用/更新/墙钟与空间预算、何时停止/何时可进入生产、仍需执行端核实的资产字段。给出首个可在30–60分钟内得到的工程/机制里程碑；如果实际成本不支持这个范围，说明依据，不虚报完成时间。

目标是一个有真实新能力证据的候选，不保证官方提分，不再先规定五个包。没有支持时交回STOP及具体下一项证据缺口，不能输出相同预测改名或绕开失败门。
