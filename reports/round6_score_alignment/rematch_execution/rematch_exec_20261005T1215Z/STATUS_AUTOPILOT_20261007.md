# Linux 后台接续登记

2026-10-07 13:02 UTC+8：用户已批准约19.52GiB固定32B教师在Linux原地下载，以及标注、8B微调和最终封包自动接续。新控制器已单次启动，实际registration写出并实查命令身份；历史PID2397312，后续以实际进程与回执为准。

入口：teacher_student_autopilot_v1/CONTINUE.md。源码/固定资产149文件锁SHA：7a65ff88936295e7c51bdb37e1fbd1c2f76c965bdf8212b71eaba8ecf85fbd07。Linux教师CPU10项、学生CPU16项、总控preflight通过；运行时编译通过。13:06:38两个教师文件共20,958,945,472字节完整SHA均通过，13:06:43总控实际读取download_ready=true/runtime_ready=true/Z_terminal=false。目前等待Z调度/封包终态，尚未进行真实教师GPU生成，也没有新的T训练更新。

自动顺序：固定权重完整SHA与Z作业终态 → 真实教师探针 → 128train/32dev自然窗口标注与弱语义审核 → 从B最终LoRA以lr1e-5接续最多3epochs（20更新真实重载验收）→ 固定弱开发检查点选择 → NONTEST8 → 426复赛推理/空间/strict ZIP。32B教师仅离线使用，部署仍为8,782,459,120参数。所有阶段保留原始证据，失败STOP，不制造未知负类。

执行独立于Windows持续在线；没有项目人为磁盘/RAM/VRAM上限，使用共享GPU锁和实际容量检查。Mac不参与。Windows旧权重下载、上传桥接与Z回传继续停止，中间产物和最终candidate_T_8B.zip留Linux。未来取包先说明实际大小，官网由用户手动提交。只有PASS_AUTOPILOT_FINAL_T_ZIP_ON_LINUX及独立strict全部通过才算新T包完成，不将注册、探针或弱开发指标当官网分。
