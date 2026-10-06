# GPU 累计时间预算调整

状态：APPLIED_VERIFIED_CPU_ONLY。授权：用户“GPU预算时间调整为无限制”。生效时间：2026-10-05 16:02:23（UTC+8）。

- 当前累计 GPU 时长不限，明确以 UNLIMITED + JSON null 表示，不用巨大数字或非标准 Infinity。
- 本地 AGENTS.md、ROADMAP.md、复赛方案已更新；训练机当前 resource_policy.json、coordination.json 及实际预算入口 improvement_round1/budget_run.py 已同步生效。取消原累计 86400 秒拒绝条件。
- 新作业仍要求有效单次运行时长，保留进程锁、活动作业核查、外部 GPU 进程拒绝、失败终止和资源记账。磁盘规则、阶段授权及冻结的科学协议未扩大。
- 缺少显式策略时保留历史有限默认；错误/不一致策略直接报错。每个新作业资源记录将保存策略模式、限额和策略 SHA-256。
- 安装前后同一 9 项 CPU 回归检查均通过，包括累计超过旧 24 小时上限、有限限额超出拒绝、单作业时限及非法配置处理。原源码和协调配置保存在 before/，历史报告、冻结协议和账本未改。
- 账本仍为 89 行，含 7200 秒初始偏移累计 72864.71271079406 秒（20.2401979752 小时）；账本前后 SHA-256 一致：0a8434b5db46b60a57f823c5c41bb0d087268df3d8545de870e2edfb93153426。此值是实际用量，不再据其计算当前剩余额度。
- 安装前后 GPU 无计算进程，无 active_gpu_job.json；没有启动模型下载、训练、推理或提交。
- Mac mini 实时在线，代码及证据传输使用既有 macmini 跳板和严格 SSH 主机校验。

原源码 SHA-256：90b7111e00c49c675d182908c32fe4e7cefcca06143cbbc2efa172f4c6ab89ab。

生效源码 SHA-256：de61837d38047f3dd6bd4282b0d72c07ca360ca0dccc92d1c53d07c34b255c09。

生效策略 SHA-256：74f15dc694428d5d421d58c6d790560ee6e8d86fc8847db6625b14fbeb38e8c6。

真实安装结果与测试日志见 install_result.json、install.log；双端文件核查见 sync_verification.json。
