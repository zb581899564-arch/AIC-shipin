# 当前接续状态

v6 为已审计的独立工程修复版本，禁止修改冻结 v5，不重开 v5 launcher。先看项目 AGENTS.md、STATUS_AUTOPILOT_20261007.md、本 PROTOCOL.md 和实时 Linux 身份/资源。

当前真正运行的 GPU 作业是 teacher_semantic_diagnostic_v1/diagnostic.py，复查原12条真实标签，原样保留拒绝/不确定；实时 progress.json、completion.json，diagnostic PASS 不等于训练准入。v5 已于22:18 STOP，全正12/12、0空例、0T更新、0新T ZIP。

v6 config.launch_admitted=false：尚不能把已知全正分布放行，也不能盲目重新运行全量标签。读取 audit_cpu_acceptance.json、real_bridge_cpu_acceptance.json、原teacher/student/clock/ffprobe/recipe/runtime grammar CPU回执与source_lock；任何源代码修复后须新版本、新锁。

收齐十二条真实诊断，区分可证实的坐标/程序问题与标签语义问题。v6 已修复无损精度、显式 helper 绑定、开发/生产实帧合同、增量容量估算、全空成本回执与历史服务器证据；新的科学步骤须据具体证据登记，不造空、不删门。

最终只交付 Linux 一个通过426 strict和大小/SHA/CRC的ZIP，不自动回传或官网提交。正常无变化巡检安静，重要异常/恢复/最终完成再通知。
