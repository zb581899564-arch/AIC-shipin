# 当前标注流程入口

当前状态：NO_ACTIVE_ANNOTATION。旧闭源 Agent 批量标注已退役；本目录没有模型调用器。用户已授权新方向的有限诊断，诊断使用各自独立协议、源码锁及Linux共享资源执行器，批量标注尚未准入。

唯一当前控制入口为 `control.py`。`status` 只读状态；`check` 和 `run` 在当前阶段明确拒绝执行。它不导入旧 runner，不创建子进程。即使只把 policy 改为 READY，也没有可以启动的执行实现。

```powershell
& 'G:\ai\AIC视频\reports\annotation_iteration_20261010\slot6_silver24_v1\cpu_env\Scripts\python.exe' -B 'G:\ai\AIC视频\improvement\annotation_pipeline\control.py' status
```

历史脚本在原位置保留，以免破坏冻结 SHA、失败记录和可复核证据；禁止直接执行。退役范围见 policy.json 与 `reports/strategy_reset_20261011/legacy_closed_agent_inventory.json`。这是当前工作流约束，不是操作系统沙箱，不能声称旧脚本已经物理不可执行。

未来的新教师接口应由程序提供图像/视频张量和精确时间映射，一次输出短结构化结果；不让 Agent 找文件、逐组调用 view_file、写逐帧长事实表或执行 schema 修复链。只在少量固定样本上同时证明事实、取舍、边界与实际吞吐后，才登记批量阶段。普通区间须明确裁定，UNKNOWN 不转负。缓存按源、帧、模型、提示、schema 和运行时身份建立，成功条目不重复生成。

更换教师仍须有新的语义对照；已有32B的历史失败不会因为换接口而失效。方案见 `reports/strategy_reset_20261011/PROPOSED_PLAN.md`。

2026-10-11实际执行：`improvement/spatial_scale_pilot`四图12调用配方未通过固定开发门，保留集与426未运行。`improvement/open_teacher_pilot`是两个已暴露难窗的本地32B接口/事实诊断，短输出、无历史标签输入、最多2次调用；其协议在`reports/open_teacher_pilot_20261011/PROTOCOL.md`。诊断输出不直接变成训练标签，不恢复旧流程。
