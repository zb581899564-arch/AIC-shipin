> 当前13:41 UTC+8：v2真实32B输出坐标混用，被strict validator拒绝；原始失败保留，不修改标签。新../teacher_student_autopilot_v3/CONTINUE.md明确逐帧窗口内时间、约束生成端点为真实采样PTS/窗口端点，并修正逐窗时间数组统计；主提示词/validator/源帧/模型不变。38项CPU及preflight通过，单次启动历史PID2441375，158锁SHA273f796cf3f30fb309226fa98cd8f8b284a16b76b4eb92b73beb27acf75623ca；实际进程/探针/注册须核验，不重复launcher。教师权重/运行时已就绪，T尚未有更新，最终仍只一个ZIP留Linux。

> 13:22 UTC+8历史入口修复：v1已因后台裸ffprobe缺失STOP；v2只绑定既有ffprobe绝对路径及SHA。教师权重完整SHA和CUDA运行时均已就绪，Z因旧51GiB检查STOP并保留，不是T质量门；T仍用真实容量运行器。下方v1/v2启动和Windows桥接均是历史。

> 最新授权（2026-10-07）：用户已明确允许本次Linux原地下载约19.52GiB固定教师权重，并自动接续标注、8B微调和封包。下方Windows下载与上传桥接为已暂停的历史方案，不恢复。最终ZIP只留Linux，不自动回传/官网上传。

> 2026-10-07用户新增流量约束，优先于下方历史自动传输安排：Windows权重下载50872与上传等待27724均已按身份暂停，不自动重开。约13.7GiB部分文件保留但未验收完整SHA。其他新的大流量下载/上传/回传先说明方向、规模、链路及可能机场消耗，等确认后继续；SSH别名直连不代表网络不经代理。中间结果留Linux，最终只交付一个选定ZIP。详见../controller/network_transfer_policy_20261007.json及两份user_network_pause.json。
# 取消人为额度后的接续

用户2026-10-07明确取消本项目磁盘/RAM/VRAM人为上限，所有新作业采用ACTUAL_CAPACITY_ONLY。全局有效策略见effective_policy.json与Linux同名根策略，policy_transition_01.json记录真实原/新SHA。旧80GiB、Linux51GiB、Mac预留、此前future_quota_plan都被本授权覆盖；新运行不得继承。旧数字字段只是物理文件系统总量兼容，不是项目预算。新GPU入口gpu_run.py保留共享锁、无限累计时间、7200秒账本偏移及外部冲突检测，physical_capacity.py只检查实际剩余空间与预计剩余输出。

当前冻结Z继续，不改103绑定文件。教师权重现在已开始在Windows暂存下载，全部资源不限额，不等待旧预算放行；运行/标注仍只在Linux，Mac不参与。

- Windows下载：../teacher32b_prepare_v1/download_progress.json、download_completion.json，历史PID50872。需两个固定官方GGUF都通过完整SHA，禁止只凭文件大小验收。
- Linux运行时：../teacher32b_runtime_v2/runtime_build_progress.json、runtime_build_completion.json，历史PID2293438；同固定llama.cpp源码、本地CMake3.31.6和既有CUDA12.1。配置已PASS，实际CUDA编译中。v1因系统旧CMake配置STOP及失败桥接保留，不能反复重开。
- Windows回传：../teacher32b_bridge_v2/transfer_progress.json、transfer_completion.json，历史PID27724。等下载/运行时完成与Z终态后自动直连上传，写Linuxteacher32b_prepare_v1/assets_ready_completion.json，逐完整SHA验收。Linux真实空闲空间不足时STOP，不能从Mac迁回或删除其他资产。

这次后台准备只到PASS_TEACHER_ASSETS_READY_ON_LINUX，不把源码配置成功/编译成功/权重下载当教师视频生成通过。资产齐备后，主控从已验收的128train/32dev自然窗口注册真实CUDA视频观察探针、实际processor/token/像素合同和原始响应，再用已有validate_teacher.py审核；保留不确定、禁止强造空，测试/100confirm不读。通过真实教师与语义门后绑定实际标签、从B LoRA按既定r16/lr1e-5/最多3epochs做20更新同轮前缀及正式SFT，使用本版物理容量GPU入口。

教师始终是Qwen3-VL-32B-Instruct官方Q4_K_M+F16视觉投影器，固定模型revision保持，未改成同8B教师。教师不进入比赛<=9B部署链。官网上传仍由用户操作，当前37.63/33.81/33.46绑定各自历史包。
