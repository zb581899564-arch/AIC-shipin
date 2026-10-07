# 当前Mac最终8B开发/提交包接续：v2

## 最新：Mac8B完整提交包已交付（2026-10-07 10:27 UTC+8实时复核）

Mac最终8B已完成开发、NONTEST8及426复赛全链推理封包。远端完成时间2026-10-07 03:12:57、本机经Mac跳板回传验收03:14:07，delivery_completion=PASS_LOCAL_UPLOADABLE_8B_PACKAGE。candidate_MAC_8B.zip实际300152字节，SHA256 `7f49ff90b5a21fd71a6036d8da0a1b78f3ab9c1d900ab2f81bc1f319e9d4533d`；本次实核大小/SHA/CRC/唯一predictions.jsonl及426记录通过，独立strict全部11检查true，101880帧/14007锚点，missing/extra/duplicate均0。控制器与桥接已完成，不重开launcher；当前GPU compute为空。

官网未上传、尚无Mac官方分数；用户可直接上传mac8b_delivery_v2/delivery_01/candidate_MAC_8B.zip。原4B33.81和Linux8B37.63分数保持各自包绑定，不赋予Mac包。下方运行进度与PID都是历史快照。


2026-10-06 23:44:57 UTC+8实时更新：v2实际GPU合成重载/生成PASS，64帧1080p原输入显式低分辨率后1296token、6144界、allocated峰值17170.255MiB、有限选择分数与JSON通过，288 LoRA张量/144语言目标与保存值一致、全冻结基座字节一致。单次dev已真正生成，BASE8B完成18/104视频、20窗口（11 MODEL_OK/9 PARSE_FAILURE/0 INFERENCE_FAILURE）；解析失败保留，尚无最终开发质量结论。控制器1312611和GPU开发子进程1316567实查存活。Windows桥接52752实查存活，曾一次SSH超时按登记重试，未改绑定源。只剩已登记机器计算；通过开发和NONTEST门才自动比赛推理、空间、strict ZIP与经Mac回传。尚无Mac提交ZIP。

用户授权“mac的开发测评和提交包尽早完成”。Mac最终adapter SHA1baa14a96d30d3836478295752c0b932f40f811863c28db99b56102fcfa1d5b5，仍是64帧/32768像素/6144token的原5轮/227更新模型；不重训、不选择中间epoch、100confirm不读、C/BCE STOP、官网不上传。Linux CUDA用于评测与推理，加快交付，逻辑总参数8782459120，同基座空间无adapter且共享参数只计一次。

v1在开发入口误用Mac式Linux目录检查而STOP：BASE/SFT各112窗全部在av.open/processor/model.generate前失败，生成调用0。完整原输出/决策/STOP/锁保留，不能当质量评分或改输入调参。v2审计pre_generation_failure_audit.json已PASS，新旧dev/input_contract SHA同为55eaaaffd790984403addea399558c1c142cf1f275dcd0b8186ad806a8f2eac6。仅纠正已登记Linux路径与字节身份检查，CPU2个真实PyAV开发输入/4真实processor/12新合同/30回归均PASS。新verify合并重复SHA绑定，冲突拒绝；CUDA冻结指纹只算一次，复用实际验收值。

当前远端唯一`/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/mac8b_delivery_v2`，95文件锁SHAfb9076f0bd7f95ee6e63b7d3fde44def3c5a23e2e65df6f3ff321be2a62ef3e4。adapter与training_evidence只读复用旧v1资产，已Mac原报告/锁/adapter SHA核验，不复制基座。禁止修改95绑定文件或重复launcher；v1不得重开。

23:38:06 UTC+8单次控制器历史PID1312611已登记，23:39:25实查在启动字节复核；Windows隐藏容量/交付桥接历史PID52752，实时查注册/进程/receipt与stderr。v1桥接64592与控制器1289898已STOP，此前GPU合成重载工程PASS但开发无实际生成，不能将它当当前v2开发已完成。

后续顺序：新GPU合成实际重载/有限生成/JSON → 原104视频96组112窗BASE与Mac最终模型各一次固定开发 → 完整NONTEST8时间/CPU镜头锚点/同8B空间/strict包 → 426/521完整复赛时间 → CPU镜头/真实锚点 → 按同8B本次实测成本和数量另准入空间 → 合成/strict ZIP → Mac跳板回传与Windows独立strict。任何模型/科学/完整合同/交付门失败STOP；五类传输查询失败有界重试保留UNKNOWN，不绕过Mac。

查latest.json、completion.json、long_probe_01/probe.stage.json、dev/progress.json与dev/decision.json、nontest/rematch各stage及progress、共享controller/rematch_MAC8B_v2_* resource。GPU锁/追加账本/7200秒偏移/累计不限/合计80GiB保持，Mac full已完成，剩余训练预留0。生产与开发解码/JSON约束差异已在DEV_PROTOCOL.md登记，不能承诺官方提分。

未来本机`delivery_01/candidate_MAC_8B.zip`仅在delivery_completion.json=PASS_LOCAL_UPLOADABLE_8B_PACKAGE与独立strict全部通过后算交付。当前没有Mac可提交ZIP。原4B33.81和Linux已交付8B包保留。只剩机器计算时可结束对话，控制器和桥接继续。
