# B 8B 全量区间 SFT：冻结协议

用户于2026-10-06报告本轮4B复赛分数33.81，并明确要求登记后开始8B训练。成绩来源为用户报告，提交时刻/榜名未提供，不伪造官网独立核验；与本次交付A的ZIP SHA绑定，初赛43.94不直接比较。33.81不用于阈值、覆盖率、逐视频规则或提示词调参。

本阶段只执行已有B区间SFT的全量非测试训练。原C二元BCE因负语义/完整观察证据缺失继续STOP。已有已知弱正例区间用于assistant JSON和终止token CE；UNKNOWN不制造帧级负例，教师query-free/穷尽/top-K偏差仍未知，不能据此声称真值高光质量。

使用原704训练样本/602来源组，已绑定724正窗口，30个无已知正交集窗口保持UNKNOWN。原704/104/100外层划分不变。无dev/confirm/test训练。输入字节、已登记几何、同reader抽样帧PTS与processor身份均fail closed，不能跳坏样本或改标签。

从固定Qwen3-VL-8B-Instruct revision 0c351dd01ed87e9c1b53cbc748cba10e6187ff3b重新初始化rank16语言q/k/v/o LoRA；不把16来源的小试adapter当训练起点。其余采用小试冻结配方：lr5e-5，alpha32，dropout.05，BF16/SDPA，non-reentrant checkpoint，64帧/131072pixels，8192 token上限、禁止截断，AdamW(.9,.999)/eps1e-8/weight_decay0，clip1，无scheduler/二元头/modules_to_save。基座与视觉冻结；实际总参数8782459120，完整推理链不能叠独立4B。

固定5 epochs，每轮每个724窗口恰好一次，seed20261006+epoch洗牌；共3620有效backward，grad_accum16连续跨轮累积，227 optimizer steps，最终4微样本按4归一化，不能丢弃或重复补齐。5轮沿用既有P2-T2曝光量依据并在未读新开发结果前冻结，不据33.81改变学习率/轮数。

只保存最终adapter并单次重载验收。每步记录真实loss/梯度/LoRA变化、每窗口source与processor证据；全基座/视觉字节before/after/reload/adapter-off哈希均持久化。PEFT压缩target_modules时核实际144语言模块与288张量，不以144完整名vs4后缀字符串判断失败。小试5步报告及独立重载补充不覆盖。

机器小试80有效样本总450.88秒；全量3620按该测量折算约5.7小时含保守初始化摊销。单作业冻结停止上限36000秒(10小时)，实际账另记且累计GPU无限。不是固定资源准入线。现时无外部GPU，核实际容量/共享锁，按最终adapter+3620份有界证据估算约1.14GB磁盘，不落盘optimizer或视频缓存；继续80GiB工作占用边界和7200秒账本偏移，不安装/下载/抢占。已有runner只停本任务资源冲突/失败进程。

成功标准：704/724全部五轮覆盖、3620有效/227更新、有限loss/connected梯度、冻结字节一致、adapter语义和字节重载、源/代码/权限锁不变。失败保留当前证据和原作业账，停止；不自动重跑。完成后仍只是完整训练工程通过，质量须按dev_protocol.json固定104弱开发单次比较；100confirm不读取。本次不自动复赛B推理/封包/上传。

全量准入勘误：原prepare_inputs允许毫秒源末端表示误差，但旧小试admit只允许1e-6秒，16来源小试未覆盖该差异。全量发现14正窗口末端等于round(n_frames/fps,3)，最大多0.0005秒。新row_contract仅允许精确相等的历史毫秒取整且偏差<=0.000500001秒；不能扩大到通用1毫秒/一帧越界，不能改变段目标、删样本或回写旧合同。每窗口运行时仍核真实Decord末端ordinal/PTS、processor元数据。训练和新准入均尚未开始时登记此工程兼容，不使用线上分数或测试内容。
