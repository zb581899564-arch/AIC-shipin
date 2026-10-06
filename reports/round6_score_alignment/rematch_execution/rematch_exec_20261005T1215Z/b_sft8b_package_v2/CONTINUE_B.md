# Linux8B 推理与提交包接续

本轮用户授权“生成一下包中”。Linux训练已完成3620有效backward/227更新/5epochs，冻结和adapter重载PASS，最终adapter SHA8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23。当前执行不是新训练；C/BCE仍STOP。

远端本目录：`/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/b_sft8b_package_v2`；相同执行目录`temporal_sft8b_dev_v1`包含固定104/96比较。源锁SHA `b24204ec9d39779c874efa3f7575653f945b3d45c26661cc6e85546ae52748a8`，57绑定文件，禁止编辑运行中绑定文件。CPU11新合同、30旧回归、4真实8B processor case通过。

已登记单次控制器历史PID890455，启动2026-10-06 17:33:59 UTC+8。只读核`latest.json`、`completion.json`、`controller.log`以及实际进程；PID记录不是持续存活证据。它等待既有开发wrapper rematch_sft8b_dev_01成功，再运行nontest_01完整时间/顺序shots/anchors/原生8B空间/compose/strict package，成功后rematch_01全426时间/CPU调度、按真实数量与8B实测登记空间和严格包。不可手工重复launcher或运行中间stage。

Windows经Mac桥接并自动回传的历史PID57120。只读`bridge_registration.json`、`bridge.stdout.log`/`bridge.stderr.log`、`mac_capacity_latest.json`和进程。每分钟先确认Mac主机身份，再在唯一根查询实时工作占用，经`scp -J macmini`原子提交容量receipt；无Mac连接不绕过。控制器每阶段需fresh<=300秒Mac证据以及Linux实时容量，另包含Mac剩余1.1GB有界产物与当前阶段预计输出。资源冲突由已有共享wrapper有界等待，外部作业不动。

后台所有工程/身份/质量门失败均写completion STOP并保留，不自动重试。检查dev decision与对应shared wrapper receipt，任一冻结STOP禁止比赛阶段。任何修复都需独立版本/原因与新登记，不能覆盖运行中源码、删失败窗口、强行空输出、重复跑dev选择结果。100confirm不读，测试像素/文本不发外部API。

完成候选远端`rematch_01/candidate_B_8B.zip`，ZIP仅含predictions.jsonl。本机成功交付位置`delivery_01/candidate_B_8B.zip`；只有`delivery_completion.json`为PASS_LOCAL_UPLOADABLE_8B_PACKAGE且local_independent_validation全部PASS，才能称已交付。completion PASS仅说明远端完整包；没有delivery证据不能说Windows文件存在。桥接将最终SHA/大小/CRC/JSON字节和冻结strict loader复核。

本次使用同一8B基座权重，完整参数8,782,459,120；时间adapter开、空间不用adapter。官网上传未授权，正式分数等待用户上传。原33.81 A包只读保留。Mac替代64帧v8继续独立训练，其入口`mac_sft8b_64_lowres_v8/CONTINUE_MAC.md`，不能把此Linux接续扩展为Mac评测/比赛推理。

只剩机器计算时可结束当前对话；控制器和隐藏Windows桥接仍运行。不得重启二者来代替状态读取。Windows休眠/SSH中断会影响容量刷新和交付，按实际error报告，不能臆测远端停止。

修复记录：v1在首个非测试GPU准入前时间戳7位小数解析失败，旧completion保留。v2仅容量时间戳规范化6位小数、目录与作业名变更，实际Linux复现验收通过。固定开发已成功，只读复用，不重评。所有v2 GPU作业名前缀rematch_B8B_v2_。
