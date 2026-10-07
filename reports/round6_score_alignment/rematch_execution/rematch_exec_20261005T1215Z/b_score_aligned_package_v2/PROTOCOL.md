# B2 v2 独立端点合同修复

保持已经训练的B最终8B LoRA、全部生成算法/原生64帧输入/提示词/权重/greedy/16384界。
v1生成使用十进制Fraction差，选帧使用浮点直接减法：529真实元数据窗口56处差异，29个合法全端点被选帧误拒绝。
v2让生成、原validator和物理选帧共享同一个canonical duration，不加epsilon、不截端点、不改输出数值。
CPU须复现全部29拒绝，并在529窗逐一通过全端点真实native帧范围、原输入完全相等与12原目标无损回放。

当前v1 GPU时间生成不受此选帧错误影响，允许其原任务完成；不重生成已经成功的回答。
probe和NONTEST8时间仅在逐SHA、模型/adapter/算法/真实输入/原validator/finite score核验后原字节复用。
完整426/521时间阶段和所属wrapper记账成功后，按完整controller身份与CPU子进程PGID终止v1后续路径，保留外部handoff回执。
v1若已自然STOP，保留原STOP；若尚GPU活跃或有外部进程，等待，绝不按历史PID盲杀。
动态成功时间文件在复用前绑定独立replay/SHA回执，不编辑旧stage/source_lock。

v2单次控制器自动原样复用→重新完整NONTEST8选帧/全源空间/strict→等待原426时间并核验移交→全源CPU镜头/同8B空间→426独立strict ZIP。
科学质量STOP和T更新0保持，新的B2不是新的教师微调，官网分未知。
最终仅一ZIP留Linux；不回传/AIC提交/读100confirm/本地复刻AIC分/手看复赛内容调参。
Mac不参与；共享GPU锁/追加账本/7200偏移和实际容量保持；新大流量仍须许可。
