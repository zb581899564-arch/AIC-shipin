# Linux 后台接续登记

2026-10-07 13:59 UTC+8实时验收：两条真实教师探针均PASS_REAL_NONTEST_TEACHER_PROBE，逐窗耗时74.425/74.814秒；v3总控命令身份存活，13:49:47已进入RUNNING_TEACHER_FULL，最新13:59:10完成8/160自然窗口、0失败。8B T尚未开始优化器更新，最终T ZIP不存在。后续标注、同教师弱复查、微调、开发、NONTEST8、426推理/strict ZIP已自动接续登记，不依赖Windows在线。按实测和既有同8B成本粗估剩余标注/复查5–7小时、训练/开发1–2小时、全量推理/封包6–8小时，预计8B今晚20–23点、ZIP次日02–07点；这是速度外推，须各门通过，不是完成承诺。

13:41 UTC+8更新：v2首条真实32B生成混用源PTS与窗口内秒数，被原严格validator13:29拒绝；0合格标签/0 T更新，原始输入、raw与失败保留。v3维持同源帧/PNG、固定模型、主提示词和validator，逐帧明确窗口内时间，并在生成时将区间端点限定到实测窗口内采样PTS或窗口端点；不修改旧错误响应，空/不确定/语义仍由模型选择。另修复probe时间数组的统计接口。clock8/ffprobe4/teacher10/student16共38项CPU及总控preflight通过；v3历史启动PID2441375，158锁SHA273f796cf3f30fb309226fa98cd8f8b284a16b76b4eb92b73beb27acf75623ca。当前入口teacher_student_autopilot_v3/CONTINUE.md，以真实进程/回执为准。

初步耗时只作安排：首条真实32B生成prompt15.85秒、generate46.20秒，但该标签无效，不当质量通过。若有效小试与后续门通过，160标注及复查暂估5–7小时，8B微调/开发1–2小时，426推理/空间/ZIP6–8小时，合计约12–17小时；有效探针的逐窗耗时出来后再校准。GPU时间无限不等于不存在这些实际计算成本。

13:22 UTC+8更新：v1已于13:10因ffprobe未在PATH而STOP（尚无教师GPU调用/标签/T更新）。v2绑定既有ffprobe绝对路径与SHA，160真实非测试窗口的两处工具调用及CLI4检查、教师10/学生16 CPU合同、总控preflight全部通过；单次启动历史PID2421099已实查命令身份，入口改为teacher_student_autopilot_v2/CONTINUE.md，153文件锁SHA71d59c5627f3ca0e77b63033d71126bd8ccf96f63d4636d4953ebc6ba532c7b0。旧失败与科学协议保留，新源码不覆盖v1。

Z在全源CPU调度完成后因旧冻结51GiB检查STOP，实际空间约193GiB。T不依赖Z质量或包，当前不重开Z；新T仅按真实容量及共享任务冲突准入。教师权重与CUDA运行时已就绪，T仍未出现优化器更新。标签完成后8B训练/开发暂估1–2小时，随后426推理/封包暂估6–8小时，依据旧B训练4.55秒/有效样本、Z31,296源空间锚点及非测试0.605秒/锚点；新输入与实际运行可能改变耗时。教师尚无真实标注速率，当前不能确定总出包时间。

2026-10-07 13:02 UTC+8：用户已批准约19.52GiB固定32B教师在Linux原地下载，以及标注、8B微调和最终封包自动接续。新控制器已单次启动，实际registration写出并实查命令身份；历史PID2397312，后续以实际进程与回执为准。

入口：teacher_student_autopilot_v1/CONTINUE.md。源码/固定资产149文件锁SHA：7a65ff88936295e7c51bdb37e1fbd1c2f76c965bdf8212b71eaba8ecf85fbd07。Linux教师CPU10项、学生CPU16项、总控preflight通过；运行时编译通过。13:06:38两个教师文件共20,958,945,472字节完整SHA均通过，13:06:43总控实际读取download_ready=true/runtime_ready=true/Z_terminal=false。目前等待Z调度/封包终态，尚未进行真实教师GPU生成，也没有新的T训练更新。

自动顺序：固定权重完整SHA与Z作业终态 → 真实教师探针 → 128train/32dev自然窗口标注与弱语义审核 → 从B最终LoRA以lr1e-5接续最多3epochs（20更新真实重载验收）→ 固定弱开发检查点选择 → NONTEST8 → 426复赛推理/空间/strict ZIP。32B教师仅离线使用，部署仍为8,782,459,120参数。所有阶段保留原始证据，失败STOP，不制造未知负类。

执行独立于Windows持续在线；没有项目人为磁盘/RAM/VRAM上限，使用共享GPU锁和实际容量检查。Mac不参与。Windows旧权重下载、上传桥接与Z回传继续停止，中间产物和最终candidate_T_8B.zip留Linux。未来取包先说明实际大小，官网由用户手动提交。只有PASS_AUTOPILOT_FINAL_T_ZIP_ON_LINUX及独立strict全部通过才算新T包完成，不将注册、探针或弱开发指标当官网分。
