# T：完整四次整源更新与首次独立复核通过，开发对照在跑

40.47原ZIP在Windows/Linux均实核384630字节、SHA256 `b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3`，没有修改。Goal仍active，T新ZIP0、官网提交0。

## 训练已完成的准确范围

- 原协议44的两个拟合来源各两个整源episode，实际4次optimizer更新。
- 合计94份首次采样、69份首次新greedy；第一个episode的25份原greedy采用已有控制。94次首次冻结参考TF、94次首次actor TF/反向完整。
- 47因原2206秒阶段时限自然FAILED/exit-15，费用2206.5338779585436秒；前三次更新、第四来源5组greedy/sample完整保存，旧失败不回写。
- 50在原T1总10800秒内独立登记工程续算，精确恢复actor/Adam/RNG。已保存5组采样的CUDA随机抽样逐token复现，通过后只补余下操作；前三次更新和既有模型调用未重做。没有增加训练剂量或选择中间checkpoint。
- 唯一`T_joint4_only_missing_engineering_20261022_v50`自然completed/exit0，763.5176886226982秒，resource与唯一ledger完全相等；峰值采样26578MiB。
- 原阶段2400秒预算没有被宣称通过；全部T1费用含原失败累计4466.456665819511秒。
- 实际完整模型8797892873参数，即8.797892873B，包括共享BASE、原TIME、新TIME及冻结语义head，低于9B。
- 最终第四episode权重逐值保存重载通过，原BASE/TIME冻结检查通过。
- 首次独立CPU对4来源episode的native union、反事实奖励、token/parser、允许动作loss、94份持久梯度和最终checkpoint/Adam计数复核全部PASS。这是工程及机制通过，不是开发泛化或官方提分证明。

权威终态：Linux `t_branch_execution_20261022_v1/joint_continue50/completion.json`，其`gpu_completion.json`、`independent_CPU_audit.json`及共享GPU resource/ledger。原47、44及更早失败/raw/费用均保留。

## 当前唯一执行

原`development_wait48`已按依赖失败自然停止，0新GPU，不重启。新的`development_follow51`父842365/start562874057显式绑定50的最终权重和CPU终态，复用已冻结48科学函数及原44质量门，只改变执行根和依赖路径。

51已完成50个真实内容错位输入的首次CPU检查，采用原native64输入，无新video processor；首次2919个半秒语义图像查询、365个8图上下文CPU输入全部通过。唯一`T_joint4_dev_greedy_BASE_20261022_v51`已运行，wrapper899284/start562946319，实际子899288/start562946399。最新快照88/150份新greedy已接受，原50份greedy采用。

后续自动首次coarse输出复核→去重候选特定VERIFY文本CPU检查→原TIME VERIFY→逐条件重新计算占用率相关的冻结semantic head→完整来源全评审指标。两开发GPU阶段合计仍最多2400秒。正确/错位、两发布者收益、完整40.47强控制、合法性及空源门均不变。无开发收益结论，不自动确认或426。

## 四新发布者确认规模已查明，尚未执行

52清单入口在读取数据前语法失败，0模型/解码；原日志和源码保留。部署工具已增加上传前AST拦截，针对坏52输入实际验证“SSH之前拒绝”。53仅修一处括号并独立执行，完整native窗口清单已完成，不读取人工标签。

固定四新发布者合计198窗；原TIME和训练TIME需要396次greedy，另有11784个BASE语义查询/1474上下文批，VERIFY去重数量须由真实答案确定。不能当作4个短片或只确认局部窗口。质量仍未曝光；只有开发通过且实际剩余T1预算与成本能覆盖时才确认，不缩短来源或降低门凑数。

## 资源与边界

当前SSD快照约1.31GB空余，当前GPU阶段预估新输出100MB；tmpfs仍约49.35GB空余。后续确认/生产须按真实缓存规模重新判断，不沿用旧容量快照。数据、训练、比较、raw/tensor/梯度留Linux。

EasyTier当前无直接Linux peer，保持p2p-only和原网络设置。只沿用既有授权Tailscale小控制/短状态，未搬媒体、模型或完整中间导出。最终ZIP接收仍须重新核实实际直连或取得具体例外。CONTROL5永不恢复，无新Goal、定时、作者/跨聊天消息或自动官网提交。
