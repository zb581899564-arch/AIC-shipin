# T 整源策略首次实际更新与冻结开发接续

40.47原包和依赖未修改，Goal仍active，新ZIP为0。下面是运行快照，不是训练、质量或交付完成证明。

## 已实际完成

- 实现固定44协议的整源采样、反事实奖励、逐窗梯度累积、整源更新、恢复状态及最终精确保存重载。
- 新的CPU预检通过：附加actor的FP32微小权重变化保存重载不丢失，原reference逐值不变。
- 原44在首次rollout前调用不存在的输入梯度钩子，实际FAILED，记账193.5745952418074秒；0生成、0TF、0optimizer，失败保留。
- 新47只修复首次及重复关闭钩子的生命周期；实际Transformers CPU回归通过。采用旧预检和身份回执，唯一剩余job仅用原2400秒减失败费用后的2206秒。
- 最新实际快照：37份采样、12份新greedy、25份反向梯度已持久保存，第一整源episode自然完成一次真实optimizer更新，权重摘要已改变。第二来源仍在执行。不能把第一来源的采样效用或权重变化当作泛化收益。

## 唯一运行和终态

- Linux根：`/home/inspur/aic_video_work/t_branch_execution_20261022_v1`。
- 训练父链：`joint_remaining47`，PID795005/start_ticks562620717。
- GPU job：`T_joint_source_counterfactual_remaining_20261022_v47`，max2206秒。
- 自然终态：`joint_remaining47/gpu_completion.json`、`independent_CPU_audit.json`、`completion.json`或`failure.json`，结合共享resource与唯一ledger判断。不得按旧PID或快照重启。
- 首次独立CPU复核尚未执行；最终四episode和训练准入尚未宣告通过。

## 已实现并部署的后续

唯一`development_wait48`父811925/start562705089已注册，只等待上述精确训练终态；失败或无机制则记录依赖停止，不开始新GPU。它不是定时任务。

训练和首次独立CPU通过后，固定两开发发布者四条件：原TIME/训练TIME各自在正确内容和固定半时组错位内容上自由生成。原50个正确TIME回答采用，最多150个首次新greedy。只将coarse内容错位；所有条件的后续原TIME VERIFY和BASE semantic仍使用相同正确原生内容，明确检验coarse内容机制。

原生50个错位输入须先CPU逐bit可逆/实际grid/签名验收；新半秒原图语义上下文为第一次必要准备。coarse首次输出复核后，才形成去重的候选特定VERIFY文本CPU输入，避免再发生EMPTY提示冒充VERIFY。相同真实输入/请求的成功任务只采用；原空间与语义head冻结，每个条件重新计算占用率相关变换。

开发两GPU阶段合计最多2400秒且计入总T1≤10800秒；所有失败也计费。原协议宏收益、两发布者收益、正确内容/错位、空源和合法性条件均保持。未过不确认、不全量、不封包。开发通过仍须冻结后首次四新发布者确认、当前官方规则核对和426工程验收，不自动官网提交。

## 实际检查范围

本地所有新增脚本语法检查通过；Linux两个针对性CPU预检实际通过；真实训练第一整源更新已经发生。新开发代码只部署和注册等待，尚未执行，不能声称新GPU路径或质量通过。完整raw、梯度、恢复状态和费用留Linux，仅小量控制及简短状态在本地。
