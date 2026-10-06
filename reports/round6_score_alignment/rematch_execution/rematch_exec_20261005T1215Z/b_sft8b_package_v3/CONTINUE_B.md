# Linux8B 当前包生成入口：v3

## Linux8B复赛官方成绩登记：37.63（2026-10-06，用户截图）

用户提供Linux8B结果截图，显示37.63、DONE；相对同一复赛4B的33.81提高3.82分。按用户指认与本次对话最近交付包绑定`b_sft8b_package_v3/delivery_01/candidate_B_8B.zip`，实际SHA256 `86bd5301f6f6771a8451b32063781e214cdd70245ae5513f2a767eaecb9ebe54`、310902字节已重新核验。截图未显示完整时间、名次或包名，官网未独立核验，不补造这些字段。记录与原截图见执行目录`controller/official_score_B_LINUX_37_63_20261006.json`及同名PNG。原交付receipt的uploaded=false是当时状态，保持不回写；此次提交由用户完成。

Mac独立版本继续已登记的`mac8b_delivery_v2/CONTINUE_MAC_DELIVERY.md`开发评测、推理封包接续，不依据本次线上成绩修改其冻结协议。下方状态均按各自日期理解。


## 最新：本机可提交8B ZIP已交付（2026-10-06 22:59 UTC+8实时复核）

Linux完整426候选21:38:31通过，Windows经Mac跳板21:41:07回传与独立验收通过，delivery_completion.json=PASS_LOCAL_UPLOADABLE_8B_PACKAGE。本机delivery_01/candidate_B_8B.zip实际310902字节，SHA256=86bd5301f6f6771a8451b32063781e214cdd70245ae5513f2a767eaecb9ebe54。22:59再次核实际大小/SHA/ZIP CRC及唯一predictions.jsonl成员通过；local_independent_validation全部11项true，426源/101985帧/13947锚点，missing/extra/duplicate均0。桥接v2曾三次传输失败后按登记重试恢复，最终交付完成，旧错误保留，不重启桥接或Linux控制器。官网未上传、未有8B官方分数，用户可自行上传本机完整ZIP。

Mac独立低内存64帧8B已22:15:30完成，pipeline status=PASS_MAC_SECOND_8B_FULL_TRAINING_ENGINEERING，full_training_completed=true、failure=null，adapter SHA1baa14a96d30d3836478295752c0b932f40f811863c28db99b56102fcfa1d5b5。Mac未开发评测、未比赛推理、无独立Mac提交包；Linux交付完成不扩大Mac授权。下方推理/等待/PID条目均为历史快照。

用户授权“生成一下包中”。Linux最终训练3620/227、全冻结与重载PASS；adapter SHA8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23。固定104/96弱开发单次比较PASS，SFT来源组宏F1 .6850031671、BASE .3426182206，配对95%CI[.2589075960,.4246593239]；不是官方分数，100confirm不读。

v2已完整通过NONTEST8：8窗口/427合法帧/65同帧8B锚点，独立strict ZIP PASS，同8B基座全部冻结参数哈希与训练一致，空间实测0.6497015056秒/锚点。v1在容量时间格式处STOP，v2比赛阶段在错误的训练8192token推理guard处STOP，均保留、已实际记账。没有完成复赛B包。

当前唯一目录`/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/b_sft8b_package_v3`，68文件源锁SHA `d1e8ac83dd07ba895f0fb90dd1ce49289585efda8955dd6faa524223a035c2bf`。训练/固定开发8192界不回写；新独立生产推理max16384，原64帧/default processor/所有像素/提示词/grammar/阈值保持，不截断。CPU合成HD为12048token，原生context262144，12新合同+30旧回归+4真实processor通过。首次真实12048token合成GPU工程探针通过才进入复赛恢复；看`long_probe_01/probe.stage.json`与共享`rematch_B8B_v3_nontest_long_probe_01.resource.json`。

已冻结旧78source/95window部分输出SHAfb36aace49c97933da51c2bbb414d8b6b920ced43ff8903e5efcb34e0b81883d；14成功window对象必须保留不变，81旧明确generate前guard失败与其余未处理窗口各一次，不重复成功model calls。恢复最终426源/521窗完整后才select/CPU顺序镜头/最多8帧锚点；空间按真实数量与同8B实测另准入；不复用4B测试框/弱ROI/隐式fallback。任何失败STOP，不删分母、不造合法空。

单次Linux控制器历史PID915410、Windows容量/回传桥接历史PID60636，PID须实际查命令/存活。已登记不可重开launcher，不改68运行绑定文件。只读`latest.json`、`completion.json`、`controller.log`和各`rematch_01`stage/progress；原v1/v2 STOP不能当当前v3状态。GPU用既有共享gpu_run.py/lock/追加ledger/7200秒偏移，累计不限；仅本任务guard故障child按真实name/PID/进程组停止，外部任务不动。

Windows桥接每分钟在Mac唯一根bin/run核主机身份、实时du工作占用，再经`scp -J macmini`原子提交容量receipt。每GPU阶段需fresh<=300秒Mac容量+Linux live，计Mac剩余1.1GB和阶段预计产物，合计<=80GiB。Mac离线不直传绕过；当前Mac独立v8继续训练，不能把Linux生成包授权扩大到Mac评测/比赛。

远端完整候选`rematch_01/candidate_B_8B.zip`，仅含predictions.jsonl。本机后台回传位置`delivery_01/candidate_B_8B.zip`，只有delivery_completion=PASS_LOCAL_UPLOADABLE_8B_PACKAGE且local_independent_validation全PASS才叫已交付。桥接验SHA/大小/CRC/JSON字节/冻结strict loader；官网上传未授权，原33.81 A包保留。接续只剩机器计算时可结束当前对话，不能把尚未生成的ZIP说成可上传。

2026-10-06 17:57 UTC+8：long_probe实际GPU PASS，12048token/20361.959MiB/all finite selected scores/同冻结基座；完整426时间恢复已登记接续，目前仍无复赛完整ZIP。

2026-10-06 17:58 UTC+8：实际426复赛前5来源推理完成、0失败，GPU runtime919994和控制器915410实查，Windows桥接60636正常。只剩后台已登记时间/CPU调度/动态空间/封包/交付计算；未生成可提交ZIP。

2026-10-06 18:58 UTC+8：时间阶段已PASS 426/521/0失败，14旧成功对象不变、81旧guard失败窗口各恢复一次。控制器915410与CPU镜头/锚点子进程989427实查存活，当前RUNNING_REMATCH_SCHEDULING。原Windows桥接60636的直属SSH56500卡住，只结束已核命令/父子关系的56500后原桥接报错退出；独立 b_sft8b_bridge_recovery_v1/CONTINUE_BRIDGE.md 登记有界新桥接历史PID52676。18:57:34 Mac live容量已通过Mac跳板注册到Linux，旧源码/失败/68文件锁不改，禁止重开原桥接。交付目录与完整验收合同保持。Mac独立训练107/227更新、无失败；当前仍无完整8B可提交ZIP。

2026-10-06 20:57 UTC+8：CPU合同已PASS 101985帧/900镜头起点/13947锚点；空间实际9850/13947、0失败，GPU子进程1034299和控制器915410实查。Mac独立177/227更新、无失败。桥接v1因SSH超时停止且PID52676不存活；独立v2接续入口b_sft8b_bridge_recovery_v2/CONTINUE_BRIDGE.md，历史PID48800已登记，传输失败在原三天界内有界重试并追加UNKNOWN证据，模型/交付验收错误仍STOP。原运行绑定文件与产物合同不改，尚无完整提交ZIP。
