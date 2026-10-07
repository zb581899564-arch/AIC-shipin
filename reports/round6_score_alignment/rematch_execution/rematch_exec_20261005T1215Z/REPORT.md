# 复赛执行记录：Linux 开训准备

## 最新：Mac8B完整提交包已交付（2026-10-07 10:27 UTC+8实时复核）

Mac最终8B已完成开发、NONTEST8及426复赛全链推理封包。远端完成时间2026-10-07 03:12:57、本机经Mac跳板回传验收03:14:07，delivery_completion=PASS_LOCAL_UPLOADABLE_8B_PACKAGE。candidate_MAC_8B.zip实际300152字节，SHA256 `7f49ff90b5a21fd71a6036d8da0a1b78f3ab9c1d900ab2f81bc1f319e9d4533d`；本次实核大小/SHA/CRC/唯一predictions.jsonl及426记录通过，独立strict全部11检查true，101880帧/14007锚点，missing/extra/duplicate均0。控制器与桥接已完成，不重开launcher；当前GPU compute为空。

官网未上传、尚无Mac官方分数；用户可直接上传mac8b_delivery_v2/delivery_01/candidate_MAC_8B.zip。原4B33.81和Linux8B37.63分数保持各自包绑定，不赋予Mac包。下方运行进度与PID都是历史快照。


## Linux8B复赛官方成绩登记：37.63（2026-10-06，用户截图）

用户提供Linux8B结果截图，显示37.63、DONE；相对同一复赛4B的33.81提高3.82分。按用户指认与本次对话最近交付包绑定`b_sft8b_package_v3/delivery_01/candidate_B_8B.zip`，实际SHA256 `86bd5301f6f6771a8451b32063781e214cdd70245ae5513f2a767eaecb9ebe54`、310902字节已重新核验。截图未显示完整时间、名次或包名，官网未独立核验，不补造这些字段。记录与原截图见执行目录`controller/official_score_B_LINUX_37_63_20261006.json`及同名PNG。原交付receipt的uploaded=false是当时状态，保持不回写；此次提交由用户完成。

Mac独立版本继续已登记的`mac8b_delivery_v2/CONTINUE_MAC_DELIVERY.md`开发评测、推理封包接续，不依据本次线上成绩修改其冻结协议。下方状态均按各自日期理解。


## v3长输入GPU验收通过，复赛推理接续（2026-10-06 17:57，UTC+8）

真实合成64帧1080p/12048token已通过同一最终8B adapter的GPU生成、有限选择分数、JSON合同、参数8782459120及全基座冻结身份；采样allocated峰值20361.959MiB约19.89GiB。新独立推理界16384有效，训练/单次开发8192保持，未截断/降帧/调像素。共享wrapper成功receipt与本地long_input_gpu_acceptance_01已保存。

单次v3控制器已登记并进入完整426复赛时间恢复，14旧成功窗口对象不变，81原generate前guard失败及未处理窗口各一次。完成时间/CPU镜头锚点后按真实数量与同8B非测试成本另登记空间，合成、严格ZIP及Mac跳板回传独立验收自动接续。现在仍没有新8B可提交ZIP，只有delivery_completion PASS才算交付。Linux控制器915410与Windows桥接60636需实时核活；当前入口b_sft8b_package_v3/CONTINUE_B.md，不重开launcher/改68绑定文件。官网不自动上传，Mac训练独立。


## 包生成当前为v3推理上下文修复（2026-10-06 17:53，UTC+8）

Linux8B最终训练与固定104/96开发门已PASS，开发只评最终模型一次、未读取100confirm。v2完整NONTEST8/427帧/65同帧8B锚点/独立strict ZIP亦PASS；空间实测0.6497秒/锚点，完整参数8,782,459,120。

v2比赛推理把训练8192token界错误用于推理，64帧HD原processor输入12048token被generate前拒绝。主控只按实际active job name/child PID命令/独立进程组停止本任务，已失败记账与STOP；外部任务不动、旧失败保持。独立v3只将生产推理界登记为16384，不回写训练/开发8192、不截断/降帧/改视频像素/提示词/阈值。12新CPU合同+30回归+4真实processor通过，需真实12048token合成GPU探针PASS再恢复。旧78视频95窗口中的14成功对象不变，81generate前guard失败及其余未处理窗口各生成一次，最终426/521完整门保持。

唯一接续`b_sft8b_package_v3/CONTINUE_B.md`，68文件锁SHA `d1e8ac83dd07ba895f0fb90dd1ce49289585efda8955dd6faa524223a035c2bf`；Linux历史控制器PID915410、Windows Mac跳板容量/交付桥接PID60636已登记，须实时核活。禁止重开launcher/改运行绑定文件。当前尚无完整8B可提交包，以v3 latest/completion及本机delivery_completion为准。官网未授权上传、C/BCE STOP、Mac独立训练与80GiB/共享账本约束保持；v1/v2失败和下方快照仅历史。


## 当前包生成入口为v2（2026-10-06 17:35，UTC+8）

固定开发已PASS：原104/96、112窗各臂一次，来源组宏F1 BASE8B=0.3426182206、SFT8B=0.6850031671，配对增量+0.3423849465/95%CI[0.2589075960,0.4246593239]；SFT解析112/112有效、两臂推理失败0。仅弱教师指标，BASE有36解析失败，增量包含格式改善，非官方质量结论。100confirm未读，未重评开发。

v1接续在首个非测试GPU准入前因Windows 7位小数时间戳不兼容Python3.10而STOP，没有比赛推理/包；旧源码/失败completion保留。独立`b_sft8b_package_v2`只修容量时间戳为6位小数以及版本目录/作业名，实际Windows→Linux解析通过。11新CPU合同、30旧回归、4真实8B processor通过，57文件源锁SHA `b24204ec9d39779c874efa3f7575653f945b3d45c26661cc6e85546ae52748a8`；旧开发decision/resource、v1失败也绑定入新锁。

v2 Linux控制器历史PID890455已实时核存活，Windows经Mac容量/交付桥接历史PID57120已实时核存活。当前先做8非测试完整链验收，之后自动426时间/CPU镜头锚点/按真实成本登记8B空间/严格打包/经Mac回传独立复核；尚无新8B可提交包。入口`b_sft8b_package_v2/CONTINUE_B.md`，实时latest/completion/delivery_completion为准，禁止重开launcher或编辑57运行绑定文件。Mac训练、原33.81 A包与官网上传边界保持。


## Linux8B训练已完成，提交包接续已登记（2026-10-06 17:28，UTC+8）

用户要求“生成一下包中”。Linux8B固定5epochs/3620有效backward/227更新已于16:51结束，基座/视觉冻结、有限梯度与最终adapter重载均PASS，adapter SHA `8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23`。当前单次固定104/96开发比较在跑，两臂112窗口各一次；100confirm不读。本次不重训、不造UNKNOWN负类，C/BCE继续STOP。

独立`b_sft8b_package_v1`已完成10新CPU合同、30原合同回归与4真实8B processor合成case，51文件源锁SHA `6e150535072e9f5ae40f41b2fe18d7da96c7039883e2c6993ebc96aa4c4d6505`。单次Linux控制器历史PID879854实查存活；开发门通过才进入原8非测试完整链，再426比赛时间/顺序CPU镜头/锚点，空间按真实数量与8B实测成本另登记，最后完整严格ZIP。时间最终LoRA和空间无adapter共享同一8B基座，全链8,782,459,120参数，不叠4B。保持原提示词/阈值/锚点间隔，生成时沿用已验证JSON约束，shots/space从源ordinal0顺序解码并逐帧SHA核身份；生产解码约束与固定开发原greedy有区别，不能冒充相同质量协议。

Windows隐藏桥接历史PID53652实查存活，每分钟查询Mac唯一根实时容量，经Mac跳板提交fresh evidence并在远端完整包通过后自动回传、核SHA/大小/CRC和独立strict loader。合计80GiB与共享GPU/追加账本/7200秒偏移保持。当前尚无新8B提交包，不可把注册/运行当交付；以`b_sft8b_package_v1/completion.json`与`delivery_completion.json`为准。不可重复launcher、编辑运行中绑定文件。入口`b_sft8b_package_v1/CONTINUE_B.md`。

Mac64低分辨率独立v8仍正常训练，17:27实查53/227更新、861/3620有效，无失败。该Mac接续仍只到训练结束；Linux本轮生成包授权不扩展为Mac评测/测试。官网上传未授权，原4B 33.81包保留。下方旧快照为历史。


## Mac替代64帧版本已正式开训（2026-10-06 15:58，UTC+8）

内存修复与改方向完成：128帧v7有真实更新但工作集56.59GiB超过live建议51.84GiB，独立停止并保留证据；按用户授权改为8B/最多64帧/显式每帧<=32768像素的低内存B区间SFT。v8真实探针完整3更新/48backward通过，MPS采样峰值24.99GiB，有限连通梯度/实际LoRA变化、基座与视觉全字节冻结、adapter重载一致均PASS。新full已从冷基座新LoRA实际完成24/3620次backward、1/227更新，模型总参数8,782,459,120；完整训练尚未完成。保持704train/724窗口/r16/lr5e-5/seed20261006/5epochs，不造UNKNOWN负类，C/BCE仍STOP。MPS局部FP32索引、strict feature/token contiguous掩码、逐样本缓存释放与测试后恢复RNG修复保留，不改库/系统/内存上限、不CPU fallback。

当前入口 `mac_sft8b_64_lowres_v8/CONTINUE_MAC.md`，Mac唯一目录 `/Users/choubk/codex-workspace/projects/aic-video/mac_sft8b_64_lowres_20261006T0748Z`；源码锁 `6d42f4768e542c13c7c5d72f988c3dc84970e2a5edc0b53f2963cccc4445d9fa`。禁止重开launcher或编辑运行中33个绑定文件。controller/full_admission.json按341.4816秒真实探针训练成本登记全量止时，实际用量追加账本。查full_01/progress.json、最终train_report/controller/full_resource与pipeline_completion，PID需实时核验。启动receipt为 `controller/mac64_full_training_start_01.json`。

Linux原训练不动，最新183/227更新、2940/3620有效，无失败。当前两机后续仅机器计算；Mac接续不自动开发评测/比赛推理/空间封包/上传，8B质量与可提交包仍待后续门。共享锁、实时冲突/动态容量、合计80GiB、Mac唯一根及Linux文件传输经Mac保持；累计GPU无限但历史账本7200秒偏移不改。下方各等待/失败快照仅为历史。


## Mac改低内存64帧方向并真实更新（2026-10-06 15:52，UTC+8）

用户授权修复内存，若128帧支撑不起则换方向。128帧v7虽有真实更新，修复后仍采样56.59GiB，超出当时live MPS建议51.84GiB；主控只停止登记的本任务训练子进程组，旧结果、源码锁与账本保留，未启动其full。新独立 `mac_sft8b_64_lowres_v8/PROTOCOL.md`：同一固定8B、最多64帧、每帧实际视频处理像素<=32768、max_seq6144，704train/724已知正窗口/602组、r16/lr5e-5/seed20261006/5epochs保持。方向为低内存区间JSON SFT，含输入/解码/硬件差异，不能单独归因或承诺提分；C正式BCE未知负语义门仍STOP，不造负例。

真实codec/processor CPU8/8、继续门3/3、进程树归属2/2通过；MPS/CPU DeepStack前向梯度与掩码/错形状拒绝5/5通过。保留显式VIDEO预算和新鲜嵌套kwargs、局部FP32 DeepStack索引后转回BF16、严格token/feature行数与hidden维度检查及contiguous掩码、每microbatch同步释放缓存和测试后恢复登记RNG；不编辑安装库、不隐式CPU fallback、不提高MPS上限。实际参数8,782,459,120。

当前64帧实际探针1/3更新、26/48完成backward，首步288张量梯度连通/有限、144张量变化，采样MPS峰值24.29GiB，当前无失败；最终48microbatches/3updates的冻结与重载仍待运行结束验收，完整Mac训练尚未启动。单次控制器实查存活；全部门通过才自动从冷基座新LoRA开始5epochs/3620microbatches/227updates。源码锁 `6d42f4768e542c13c7c5d72f988c3dc84970e2a5edc0b53f2963cccc4445d9fa`，33文件已Mac核字节并在Linux归档独立核验。Mac目录 `/Users/choubk/codex-workspace/projects/aic-video/mac_sft8b_64_lowres_20261006T0748Z`；查该版本CONTINUE_MAC.md，不重开launcher、不修改运行中绑定文件。

Linux原64帧完整训练保持正常，最新178/227更新、2860/3620有效，未报失败；8B推理封包尚未开始。本Mac接续不自动开发评测、比赛推理、封包或上传。累计GPU不限、追加计费、Linux7200秒偏移、共享锁、唯一Mac工作根和合计80GiB边界不变。当前实证见 `controller/mac_memory_repair_start_01.json`。


**10/6 14:53（UTC+8）最新状态：**Mac128帧MPS第一次探针14:52:18因首次forward的SDPA注意力内存不足STOP，0有效backward/0更新，完整5轮未开始，后台控制进程已结束。719项/25.60GB资产已全SHA/size通过；probe472.7887秒独立记账，失败receipt与源码锁保留，无自动重试或关闭MPS内存保护。完整说明 `mac_sft8b_128_v1/STATUS_STOP_20261006T0653Z.md`，本地失败receipt `failure_audit_01/`。下方14:12等待为历史快照。Linux14:53:26仍正常，129/227更新、2076/3620有效，按当前吞吐粗估16:50–17:10完成训练；这不是8B包交付时间。未开始8B推理打包。

**10/6 14:12（UTC+8）Mac 独立版本登记：**用户要求 Mac 再微调一版。M5 Pro / 64 GiB，独立环境 torch2.5.1 / torchvision0.20.1 / transformers4.57.1 / peft0.17.1，真实 PyAV lossless 编码、帧序/PTS、128帧 processor 与掩码等 CPU 8/8 PASS；条件验收门 Windows/Mac 各 3/3。31 项最终源码/输入/环境在 Mac 逐 SHA 通过，锁 `5b80284ffdd372725ac02088098f7378d63ab013698d71aa353297a48f327257`。协议 `mac_sft8b_128_v1/PROTOCOL.md`，实际 Mac 唯一路径 `/Users/choubk/codex-workspace/projects/aic-video/mac_sft8b_20261006T054133Z`。

新 Mac 版本保持固定 8B revision、704 train / 602 组 / 724 正窗口、r16、5轮 recipe，最多128帧 / 16384 token，BF16 / MPS，不允许隐式 CPU fallback；未更改 Linux 冻结训练。3更新/48样本实探针的完整冻结、有限梯度、参数字节重载及实时资源 PASS 后，从基座新 LoRA 开始 3620有效/227更新完整训练。总参数8,782,459,120，无独立4B或辅助头，UNKNOWN不造负类，C正式BCE仍STOP。硬件、输入密度、解码器共同改变，不能把后续差异单独归因或承诺质量收益。

Mac一次性主控14:10:50已启动，14:11快照实查存活，阶段 `WAITING_REGISTERED_MAC_ASSET_TRANSFER`，5.82/25.60 GB，**Mac正式训练尚未开始**。719项（15模型文件+704非测试train媒体）均须SHA/size一致后继续。首轮Windows桥接结束STOP，失败与部分文件保留；已有Linux–Mac Tailscale直连36ms，临时Mac-peer-only/capability白名单文件发送器传输约11MB/s，自有进程完成/失败/截止后关闭，不改SSH/Tailscale/代理/服务。环境初版缺torchvision的后续补装据实收录final freeze；预备receipt生成曾因uv venv无pip失败，CPU日志保留，改用安装元数据采集版本后PASS，不全局安装pip。保守双端预计峰值81,635,122,312字节（约76.03GiB）低于80GiB，按实际阶段重核，不用固定空闲比例门。Mac实际耗时独立追加，Linux历史账本/7200偏移不动。

Linux14:11:44实查完整训练95/227更新、1520/3620有效，第三轮72/724，有限梯度/损失，未失败。当前Mac仅后台等待传输与计算接续，不自动dev/confirm/比赛测试、空间推理、封包或上传。接续见 `mac_sft8b_128_v1/CONTINUE_MAC.md`；不要改运行中源码、重复启动或把PID当成功。质量仍待各自固定开发协议另准入。

**10/6 12:20（UTC+8）最新验收：**4B复赛官方成绩33.81已按用户报告登记。新8B全量B区间SFT已真实开训，12:19:56快照实测1/227 optimizer step、23/3620有效backward；首步16微样本loss3.460375/梯度norm5.033585均有限、144 LoRA张量更新，144 A梯度首次为0符合初始化，B144非零。实际总参数8782459120；Windows/Linux各12 CPU通过、模型和704源字节门通过。共享wrapper494429/训练494462及GPU同进程实查在跑，快照SHA9fd390409f19e5b4bd3bc17605950d7e62ed3652a67637a03b17ace1862fdf51经Mac回传一致。尚未完成5轮，也没有B质量/测试结果；仅剩后台机器计算时按用户许可结束本轮，不停止训练。入口/协议 `temporal_sft8b_full_v1/PROTOCOL.md`；真实状态 `status_full.py`，最终 `train_01/train_report.json`+wrapper resource，开训验收 `controller/full8b_training_start_01.json`。源锁运行中只读、不重复启动。

**10/6 12:16（UTC+8）当前阶段：**用户报告已提交本轮4B候选，官方成绩33.81；登记 `controller/official_score_A_33_81_20261006.json`，未伪造榜名/评分时间或独立网页核验。用户明确要求登记后开8B，全量B已冻结且Windows/Linux各12项CPU合同通过，主控准入704原train/602来源组/724正窗口，5 epochs/3620 effective/227 optimizer steps；最后4微样本按实际4归一化，不能丢弃或补齐。固定8B从基座初始化新LoRA，不延续小试adapter；原C/BCE STOP不变。`temporal_sft8b_full_v1/source_lock.json` SHA88e9767ee875566c7adeb7470d89d0cd3f936c53265d640c37e536a0f98bf9b5；新的窄毫秒端点兼容只限14历史已取整窗口，不改清单/标签。开训前逐源/模型字节核验通过，新共享wrapper `rematch_sft8b_full_01` 12:16已后台启动（历史launch PID494429），当前入口重复字节核验/载入，尚待观察真实更新；不把PID当有效训练证据。查 `temporal_sft8b_full_v1/status_full.py`，真实计数 `train_01/progress.json`，最终 `train_01/train_report.json` 与 `controller/rematch_sft8b_full_01.resource.json`。当前源码/配置冻结只读，不重启、不编辑、不自动B测试/上传。原A旧NOT_UPLOADED/失败receipt为历史快照，当前评分以新登记为准。

**10/6 12:00状态更新：**A已完整推理/打包/本地交付，使用现有4B/P2-T2链；上传 `delivery_A_SPATIAL_IDENTITY_01/recover_01/candidate_A_PTS.zip` 即复赛预测结果候选，不必等待8B，官方接收/评分以上传反馈为准。8B是独立改进路线：小试5/5更新、80有效微样本已完成，保存配置的144完整层名被PEFT压缩为4后缀，原字符串比较误判STOP且保留。独立重载补充验收通过：144实际语言层、288LoRA张量与保存字节一致，基座/视觉加载前后与adapter-off全部冻结字节一致、总参数8782459120；不额外训练。原5步执行在配置失败前已通过冻结比较，但原哈希值未持久化，验收明确使用固定源码执行顺序审计并附新重载冻结哈希，未伪造原哈希。合并receipt为 `controller/sft8b_smoke_acceptance_01.json`，原失败报告不回写；新 `saved_adapter_check_01/verification_report.json` 保留实测。完整704来源训练尚未启动，须下一阶段冻结完整协议/新准入，C原BCE负语义STOP不变。当前GPU作业均结束，8B小试不是官方质量或完整训练成功。


执行编号：`rematch_exec_20261005T1215Z`。用户已授权按讨论方案执行；当前正式上传未授权。后续状态以 `controller/execution_status.json` 和实际 receipt 为准，本文记录各项验收边界。

**10/6 11:36（UTC+8）当前状态，优先于下方历史快照：**A完整候选已交付本地，ZIP为 `delivery_A_SPATIAL_IDENTITY_01/recover_01/candidate_A_PTS.zip`，266,448字节，SHA256 `5b8a186eefc2d162d65f76267979b57a6fbb94ea64fd26461f13270acb66e313`。426视频/93,155帧/13,022锚点，严格loader、完整provenance、ZIP单成员/CRC通过，14项全产物双端SHA/字节一致。尚未上传或官方评分。

原空间运行04:02因8个CFR帧像素身份失败STOP、原8B等待队列随之STOP，两个失败保持只读。主控顺序解码恢复同一视频的8个source ordinal，8/8与既有expected_pixel_sha256一致；lossless ordinal/逆向/错误hash CPU门通过。只补8次原模型/提示词/解析/空间调用，13,014个成功原行字节完全不变，temporal/selected/shots/requests/metadata逐SHA复用；不删段/删帧/空值或中心回退。新 `spatial_identity_recovery_v1/recover_01/recovery_completion.json` PASS，61.247秒记账。首次SSH容量参数转义的Popen前启动失败另存 `spatial_identity_prelaunch_failure_01.json`，不写成GPU推理失败。旧本地等待器及其直属卡住查询已按任务PID/命令核实后结束；新交付receipt为 `controller/spatial_identity_delivery_completion_01.json`。

8B已实际开训：新 `rematch_sft8b_smoke_02` 独立后台wrapper，模型进程447305实查存活；11:36已27/80有效微样本、1/5真实optimizer更新，首步梯度范数5.4973、144个LoRA张量改变，loss有限。真实逻辑参数8,782,459,120，视觉/基座不参与优化、无二元头；最终冻结字节和adapter重载等待小试结束验收。原代码、配置、17窗口/16来源、5更新规则不变，C正式BCE仍STOP；不把小试作为完整训练或质量结果。实时查 `controller/status_sft8b_smoke02.py`，最终 `temporal_sft8b_v1/smoke_01/train_report.json` 和 `controller/rematch_sft8b_smoke_02.resource.json`，禁止重开已注册作业。小试通过后主控登记完整B训练与固定弱开发协议。

以下为当时记录，不能替代上方最新交付/开训状态。

**10/6 01:46（UTC+8）最新推进：**A 的 CPU 调度已完成：93,155 帧、1,037 镜头、13,022 锚点。Linux `rematch_format_space_01` 已真实载入原未微调4B基座并正在空间推理；`format_pipeline_latest.json` 为 WAITING_REGISTERED_SPACE_COMPOSE_PACKAGE，共享wrapper/模型进程实查存在。封包和本地Mac回传接续继续，当前完整候选尚未出。空间输出由冻结实现运行结束后统一写盘，不能把尚无输出文件解释为完成0个模型调用或进程停止。

用户随后要求“然后推理打包开训”，结合既有近9B微调授权和原方案的8B区间B条件对照，主控登记 B 的本地弱区间SFT小试；真实授权原话与主控选B分别保存在 `temporal_sft8b_v1/training_authorization_B_SMOKE.json`，不捏造用户点选、不以无回复推断授权。C原二元BCE的STOP不变。B数据保持原704训练/602来源组，30秒几何切窗形成724个正窗口，固定原16来源为17个小试窗口，30个无已知正交集窗口不制造负标签；独立join与几何守恒验收通过。Windows和Linux均25/25 CPU检查通过，无skip；实际模型/processor/梯度更新仍由GPU小试验收。源码与输入锁 SHA `806deb54de18835ee6841a1a921f015cd0d8b82ad65268e016af3144cb19ff93` 已双端绑定，单次后台 `controller/queue_sft8b_after_a.py` 已启动，PID3587355实查存活，状态 WAITING_A_COMPLETE_CANDIDATE_BEFORE_SFT_SMOKE。它等待A严格426包PASS，再核实时资源与容量，按现有wrapper登记5次真实SFT更新/80有效微样本；当前已排队，GPU训练尚未开始。小试通过后由主控登记完整训练和固定弱开发协议，不把小试或排队当完整训练/质量通过。协议与边界见 `temporal_sft8b_v1/PROTOCOL.md`，实际receipt为 `controller/sft8b_queue.launch.json`、`sft8b_queue_latest.json` 和最终 `sft8b_queue_completion.json`。

已完成：固定 8B 权重准备、真实 processor 检查、三次真实工程更新、32 秒真实成本、4B/P2-T2 新入口与 A-PTS 兼容入口的非测试端到端回归，以及全部 426 条复赛输入的字节/时钟验收。**正式 C 二分类训练尚未开始：教师完整观察与负例语义证据缺失。**原 A-PTS 全量时间运行的 5 个解析失败完整保留；用户要求解决后，独立 A_FORMAT_CONSTRAINED_RECOVERY_V1 已通过 19 项 CPU 测试、真实 tokenizer/EOS、十个非测试生成和五窗口一次生成恢复。其余 516 成功窗口对象哈希不变，独立审计通过；新 426 视频 / 521 窗口全部合法。已选出 93,155 帧，目前进行 CPU 镜头检测。空间和严格封包有带证据门的单次后台接续，完成后自动经 Mac 回传并验双端 SHA/大小。当前不声称已有复赛候选包或官方分数。

**最新恢复实查（10/6 01:03，UTC+8）：**恢复时间文件 SHA `b816935d6e81f81878c84573b7938382d5659bdfb6c36af5f81551e54d2ac8b7`，全 426/521 保留，5 个新输出合法且没有事后改段。29 项恢复源码/测试/输出证据已双端 SHA/大小通过。当前 Linux 只做 CPU 镜头检测；空间尚未启动。后台接续实际进程 3404813 仍活跃，本地交付等待进程 62816 已登记。以 `controller/format_pipeline_latest.json`、最终 `format_pipeline_completion.json` 和本地 `format_delivery_latest.json` / `format_delivery_completion.json` 为准，不重复启动同名任务。协议见 `baseline_a_format_recovery_v1/PROTOCOL.md`，独立审计见 `controller/format_preservation_audit.json`。

**最新实查（10/6 00:31，UTC+8）：**模型时间推理 2596.525 秒（约43.28分钟），521 窗口中 516 合法、5 失败，全部为 CFR 分支解析合同错误：来源213的末端越界，来源231/259/329/396的段数超过冻结上限。未将失败裁短、删段或转空。共享 wrapper 记账 2663.970 秒，作业失败退出；后台于00:29记录 STOP。实时检查原两个进程均已退出，GPU compute 为空。最终证据为 `controller/a_pts_rematch_temporal_01_report.json`、`rematch_a_pts_temporal_01.resource.json`、`a_pts_failure_summary_latest.json`、`a_pts_pipeline_completion.json`。

**离开前刷新（10/6 00:07，UTC+8）：**已完成 233/426 条，出现 2 个 CFR 分支解析合同失败：来源213有预测区间超出窗口末端，来源231生成6段超过冻结的最多5段。只读取执行失败字段，没有展示视频/帧、标签或原始模型文本。按冻结协议继续完成本次时间阶段、保留全量结果和失败；完整门将拒绝候选，后台不会继续空间或封包，不把失败裁短/删段/转空，也不据此修改提示词或阈值。当前完整包仍不存在；最终数量以实际 run/resource receipt 为准。

| 工作 | 已验结果 | 证据 |
|---|---|---|
| 数据审计 | 704 train + 104 dev，来源交集 0；已证负例 0，未选范围 UNKNOWN；不读 100 条 confirm 标签 | `data_audit/REPORT.md`、`gate_decision.json` |
| 8B 资产 | 15 个文件全部复核官方固定 revision 内容哈希；4 个 BF16 权重分片完整 | `controller/model_download_v2_status.json` |
| 真实参数数目 | 基座 8,767,123,696 + LoRA 15,335,424 + 小头 524,545 = 8,782,983,665 | `controller/probe8b_02_report.json` |
| processor | 真实展开后查询全部在视频之后；padding/truncation 拒绝、词表保持、帧时间检查通过 | `controller/processor_preflight_02/processor_preflight_report.json` |
| 8B 三步探针 | LoRA/head 确实改变；冻结基座/视觉逐字节不变；UNKNOWN 严格 mask、全 UNKNOWN 跳步、视频敏感性、原生空间恢复通过 | `controller/probe8b_02_report.json` |
| 正式训练入口 | 已准备；Linux 实际 STOP 拒绝，未导入 ML/decoder 框架、未解码媒体、未调用 GPU | `controller/formal_stop_linux_receipt.json`、`dense_head/FORMAL_TRAIN_PREPARATION.md` |
| A 新入口 | 8 来源、396 选中帧、14 镜头、68/68 合法锚点；独立严格校验和 ZIP 完成 | `controller/nontest_e2e_04/independent_validation.json`、`package.stage.json` |
| 复赛 M0 | 426 视频 SHA/大小/ZIP CRC 对应重新核验；426 JSONL 仅批准元数据白名单；原 ID 不变 | `controller/m0_finalize_01/repair_receipt.json` |
| 复赛 PTS v3 | 全部 426 条审完，414 PASS / 12 FAIL；10 条非 CFR、2 条粗 tick 被过度阻断，原 A 准入实际拒绝且未导入运行框架 | `controller/pts_origin_v3_01_receipt.json`、`a_original_identity_block_receipt.json` |
| 原生 PTS 时钟 | v4 426/426 时钟身份通过：416 CFR / 10 native；native 全部整数 PTS/packet end 绑定实际 Decord；旧 A 拒绝与旧失败保留 | `controller/pts_v4_scan_01/reaudit_receipt.json`、`native_endpoint_addendum_01_receipt.json` |
| A-PTS 兼容入口 | revision04 真实 processor 4/4、lossless marker decoder 2/2、Linux 完整 CLI 7/7、非测试 8 来源全部链路通过；预测/provenance 与旧 A 字节相同 | `controller/a_pts_revision04_review.json`、`nontest_e2e_02/independent_validation.json` |
| A-PTS 复赛运行 | 426 来源 / 521 窗口模型推理已完成，5 个解析失败阻断候选；选帧/空间/打包均未执行，后台已 STOP | `controller/a_pts_rematch_temporal_01_report.json`、`a_pts_pipeline_completion.json` |
| 32 秒成本 | 固定首个非测试原视频 [0,32)，64 帧、16 查询、5,330 token；3 次合成标签更新全部通过，单步 4.33–4.43 秒、峰值分配 19.6658 GiB | `controller/cost32_01_report.json`、`rematch_c_cost_32s_01.resource.json` |

8B 所有产物位于 Linux 新执行目录，模型目录为 `models/Qwen3-VL-8B-Instruct`，revision 为 `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b`。复用现有隔离环境 `env/qwen3vl_isolated_20260910/bin/python`（torch 2.5.1+cu124、transformers 4.57.1、peft 0.17.1），未改网络、驱动、系统服务或其他项目环境。双端文件传输全部经已在线核验的 Mac mini 跳板。

第一次 8B 掩码探针的 loss 相同而梯度不同。第二次先用相同标签重复 backward 证明默认 GPU 内核本身非确定性（268 个张量出现差异），再以确定性 math SDPA、同 RNG 和同输入核掩码，loss 和全部 trainable 梯度逐元素完全相同；没有扩大容差。失败记录保留，只有第二次全部门通过后保存合成 adapter/head。**合成产物不作为正式模型或候选。**

A 的回归包只包含 8 个非测试来源，不能上传为 426 条复赛结果。它保留旧 A 的非空、1–5 段和 30 秒不重叠配方，`legal_empty_supported=false`；没有用新 C 的合法空能力包装旧 A。候选 SHA-256 为 `31bee40bbc1ee3b6a468b85e8b167d3bae3df2a7e1f736886c14f8d12659109a`。工程/格式通过不表示高光质量或官方提分通过。

补查标签目录、原始下载目录及已有代码仍未找到教师 prompt 正文、真实请求观察范围或原始 response。`seed_temporal_compact_v2_20260812` 和 `timeline_coverage=1` 不能证明穷尽观察；750 个置信度为 0 的端点也不能当负例。正式入口必须取得绑定来源/观察/通用负语义/使用依据的证据，不能将 UNKNOWN 强制置零或改用同监督 4B 绕过。现有 704/104/100 外层划分保持。

真实非测试 32 秒探针用原生整数 PTS 与实际 stream timebase 选取 64 帧，Decord/processor 身份和查询索引验收通过。dense 前向约 1.27 秒，三次步骤均包含每次解码、预处理和更新；基座/视觉全字节哈希仍相同，adapter-off 最后 token logits 和 greedy suffix 仍逐元素一致。整个探针约 179.5 秒，包含模型准备、哈希和恢复诊断。峰值 reserved 为 20.2715 GiB。没有保存可复用正式 checkpoint，也未测生产裁剪锚点吞吐，不能据此外推全训练或 426 视频总时长。

32 秒成本已通过。旧 A 使用 `i/fps` 建窗、抽帧、标记模型时间及映射回源帧，不能把真实非 CFR 源直接放过。新版本把时钟身份与 CFR 资格分开：原 CFR 门仍为 `1/fps + 1e-6`，CFR 源保留旧 A；非 CFR 源按原生 PTS 对齐，仍使用同一 4B/P2-T2、相同提示词/段数/30 秒不重叠规则与空间 max-gap-8。这是不同工程版本，不称旧 A 全部行为不变。

补充元数据中 6 条源的容器头 duration 不等于末帧 PTS + packet duration。native 分支逐原生帧/packet end 与实际 Decord 时钟绑定；窗口终点依此确定，容器头差异另存，不伪造一致。旧 CFR 分支的 `n/fps` 终点保持。v4 完成全 426 条且没有跳源；416 条 CFR 保留旧 A 路径，10 条 native 使用原生 PTS。冻结 8 非测试来源也独立形成全帧时钟注册表。

实际 processor 首版只有 3/63/64 帧通过，1 帧被底层拒绝；只复制同一物理帧与同一时间一次后四 case 全过。native 分数末端经旧 parser 四位小数表示可能越过真实末帧终点，已在 native 包装层显式恢复真实终点，未扩充任意非法端点容差。revision03 的新非测试回归时间/选帧通过后，shots CLI 因局部 sha 遮蔽导入 sha 而失败；revision04 仅删除这一行，保留旧快照和失败账。30 项 CPU 合同、7 项完整子进程受控 I/O CLI、真实 lossless RGB marker 的 80 帧 CFR 与 80 帧非零原点 VFR/gap 解码全部通过。最后两项验收口径分别是 CLI/序列化和真实 codec/逐帧像素身份，不能互相冒充。

revision04 的真实 NONTEST8 完成 396 帧、14 镜头、68/68 锚点及 11 项独立严格校验，预测 SHA `607392e7b2f60743ef841661cf84a3d560c8e570ca93bc674f2c6450c89fbb43`、provenance SHA `1ea2d03078c517ed9c61d8172e5d1f3433191d8d72b7ea6f70b90b4f111b547e` 与旧 A 相同。新 ZIP 的 SHA 为 `f1c200f92b716e72350b7a3d00fb681a4df3a72ac34cd873c1bf7f393637541c`；包内文件相同，独立运行的 ZIP 成员时间戳允许不同，不能因此要求整个 ZIP 字节复现。22 项非测试产物已经双端 SHA/大小核验。这仍是非测试工程验收，不是真实高光质量评估。

A-PTS 当前已通过全量身份、非测试回归与资源准入，运行阶段仅 preflight/temporal/select/shots/anchors。用户于 10/6 允许只剩机器计算时先结束本轮；已启动单次后台接续 `controller/finish_registered_a_pts.py`，等待时间/调度完整成功后，根据真实选帧/锚点、实测成本与实时共享资源登记空间/合成/严格封包。六个控制脚本的 SHA 和生产锁已绑定，任何证据/模型/容量错误都 STOP，资源冲突有界等待；不重跑模型失败、不杀外部进程、不启动 C、不上传。结果以 `controller/a_pts_pipeline_latest.json` 和最终 `a_pts_pipeline_completion.json` 为准，接续见 `CONTINUE.md`。不会凭启动记录声称已有 426 条包。C 数据门仍停止，工程通过不会解除该门。最高分目标仍是先 50、再争取 55，目前没有复赛官方成绩。

每个 GPU 作业使用 `controller/gpu_run.py` 共用原有锁与追加式账本，累计 GPU 时间不限并保留 7200 秒偏移。容量依据当前资源和预计产物核验；失败和重试也计费。资源快照为 `controller/resource_latest.json`，工程变化及不改旧结果的原因见 `controller/protocol_changes.json`。
