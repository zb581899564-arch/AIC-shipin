# 接替审查后的实际验证边界（2026-10-23）

## 当前结论

**135项合成CPU契约测试：131通过、4因OpenCV缺失明确跳过。没有真实Linux模型加载、媒体推理、训练、全426出包、独立质量验证或新官方分数。** 数字表示代码检查数量，不是135个真实来源、模型调用或科研样本。

精确基底 `e8224c4339007790a1be383be19fdb200cc817bc`，采用其直接后继PR #7 `60bcec3c6f058acf31352dfa771a48b81b9e5bd9` 后审查修订。PR #7先前的100项/96通过/4跳过属于它当时的验证记录；本页记录接替版本实际完整重跑，不能据此改写任何历史质量结果。

## 已实际执行

| 检查 | 实际结果 | 证据的适用范围 |
|---|---|---|
| `python -m unittest discover -s tests -p 'test_final_sprint_*.py' -v` | 99项全部通过 | 原生时钟、完整参数并集/身份、失败与合法空、426封包契约、资产绑定、source/调用恢复、资源预算、owned wrapper和本轮回归 |
| `python -m unittest improvement.final_sprint_v1.test_spatial improvement.final_sprint_v1.test_specialist -v` | 36项：32通过、4跳过 | 精确几何/持续四边形、语义JSON、原生单元、无损float32缓存、CLIP token/EOT/训练前缀契约、CPU对照 |
| `python -m compileall -q improvement/final_sprint_v1 tests` | 通过 | 新源码和测试可编译；不证明CUDA或第三方真实API可运行 |
| `git diff --check` | 通过 | 无新增空白/冲突文本错误 |
| RUNBOOK及OPTIONAL_SPECIALIST全部shell代码块 | 21个 `bash -n` 通过；6个内嵌Python AST通过；1个JSON块通过 | 文档命令语法及入口一致；没有执行里面的下载或私有资产调用 |
| CLI、bootstrap、supervise、verify_received模块 `--help` | 4个通过 | 真实命令入口/选项可解析 |
| Lighthouse固定公开checkout | commit `3e841d3d662c8440afed514908566fed2d5e82a7`、tree `271085c23c2619f0336186304e7eeb5be328e4cd` | 已读原作者源码/API/特征路径；不证明权重加载、运行依赖或赛事质量 |

`python tools/verify_publication.py` 已实际返回 `PASS_PUBLICATION`：7717个有效清单文件、4377个Python语法文件、8个原有历史归档；源SHA、历史ZIP CRC、排除资产及凭据模式检查全部通过。原冻结清单字节不变，只登记增量文件。原有历史脚本产生一条无效转义SyntaxWarning，不影响通过，未为清除历史警告修改旧源码。历史归档完整不等于本轮已生成新提交包。

## 本次回归实际覆盖的故障

- 实际62注册恢复60的准确SHA链，失败60缺锁时明确停止，不搜索新目录。
- 模型目录新增优先权重、tokenizer软链接改指向均拒绝；CPU库存import不写原依赖bytecode。
- 逐步旋转不再因重复轴对齐外包扩大范围；对照精确保留父中心，原语义范围对照完全CPU派生。
- 短/长原生clip按真实分组计前向；G每源512上限以前置元数据检查确定的必要定位下界，不误称全426只512次。
- 稀疏长展示帧、非零PTS原点、原生正终点、全部帧几何和实际RGB分组一致性。
- resolution-only合法拒选、缺失/失败clip不变空，DP时间积分不偏奖短碎片，注册参数进入真实执行。
- CLIP正文token0不当padding，完整CLIP编码后明确采用CG训练查询前缀；不虚称未截断。
- claim早于state/index的中断、returned_result早于success的中断、撕裂账本末行、撕裂封包临时文件；均保留证据后按精确终态恢复，不因超时/PID重做成功。
- G固定时间成员硬约束；合法空也必须有本候选和输入证据；全空、全选、非法框/时钟、假空间、重复预测、漏辅助参数拒包。
- 总费用、同盘output/scratch峰值、tmpfs与真实RAM区别、过期共享GPU授权、SIGTERM仅处理本次实际启动进程组。

这些是有意构造的CPU数据和故障注入，不是任务质量筛选。完整修复说明见 [REVIEW_AUDIT.md](REVIEW_AUDIT.md)。

## 明确未运行，Linux首次执行仍须验证

1. 两份私有40.48/40.47原ZIP与所有依赖、426媒体、完整输入锁和原生时钟现场SHA；不得按公开规格重建原包。
2. 原TIME、monotone_head06、I3D、UMT真实CPU权重库存；Qwen原BASE实际加载、canonical冻结张量SHA、safetensors键/参数对应、A6000显存峰值。公开测试用合成张量接口，不能代替实数。
3. PyAV实际codec/色彩修复/原始PTS及终点。本环境无PyAV。
4. 真实GrabCut/LK与主体链。本环境无OpenCV，4项测试跳过；未绕过未知网络安装依赖。
5. Qwen tokenizer真实前缀round-trip、4.57.1 native视频timestamp callback、四分支KV crop及无padding参考数值QA。本环境无Torch/Transformers/CUDA；读官方源码不等于真实前向。
6. CLIP/CG-DETR实际作者权重、Torch加载、完整参数并集、GPU forward与真实显著性。未在本环境下载权重；新M组合不能套用G的参数总数。
7. 自有Linux当前GPU/磁盘/tmpfs/RAM与必要下载实际直连、全部来源吞吐/证据增长、426包、最终ZIP传输及接收端验收、人工官网提交与算分。

实际入口已包含上述工程门：bootstrap/inventory → bind → preflight → 一次smoke → forecast → 有限run → 独立package → verify_received。缺私有资产不构成伪造替代数据的授权；也不要求执行Agent补写主流程。执行Agent按RUNBOOK绑定现存资产即可开始真实检查。

## 仍有研究风险

G主体定位或前景收紧可能错误，包含真实像素不等于更符合隐藏构图。原范围对照以同一父跟踪为条件，不是独立证据。R阶段词有语言先验与自回归惯性，独立短窗不能确保局部视觉相关；积分效用是明确决策规则，不是校准的高光后验。M作者任务域和自动事件查询可能不适合比赛。三条主线均可能显著掉分。

正式总分只能决定保留或放弃预登记自动路线，不得恢复测试标签/逐源人工规则。目标约43.5没有保证；0.01显示变化不称突破。本轮质量前置按用户风险授权跳过，真实工程故障仍先修，不用坏包耗次数。
