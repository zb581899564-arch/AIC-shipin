# Mac退出完成与Linux接续

Mac版本用户截图得分33.46 / DONE；Linux8B 37.63仍为当前复赛最高已确认分。

清理完成：Mac占用28,053,655,552→12,288字节，原占用释放约26.13GiB。重要源码、LoRA、训练记录、账本已备份为aic_mac_retirement_20261007.tar.gz，442个成员的大小/SHA全部核验。备份为本地私有资产，不发布GitHub；最终Mac adapter在Linux同SHA存续。其他用户文件和系统服务未修改。

本项目不再用Mac训练、推理或中转。直连aic-inspur-home已scp核验；旧等待60188及其只读SSH子进程62468按身份结束，新交付等待45736位于../next_round_v1/direct_delivery_v2。Linux控制器2234812和103文件锁保持，11:22 UTC+8实查处于RUNNING_REMATCH_TEMPORAL。所有PID只是核验时点，续接时重新核活，不重复启动。

后续32B容量投影通过，80GiB总边界不变，future_quota_plan.json只用于未来独立作业。当前Z单次冻结仍按51GiB执行，因此不能现在下载19.52GiB教师权重。待Z结束后，重新核实时容量、下载/缓存边界与教师真实视频运行，再产生128/32窗口标签、审核允许空与不确定排除，最后按既有T方案做20更新成本/梯度探针及最多3轮SFT。32B和T均未启动。

选择器已于03:06 UTC完成PASS_CPU_SELECTION02_UNLABELLED_128_32（见selection02_completion_01.json）；它没有产生标签。原26/0快照、原容量STOP与旧运行receipt保留历史。不要把弱教师诊断当AIC官方总分。
