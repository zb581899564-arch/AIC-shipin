# 首次426压缩packet末端测量

独立模块 `improvement/native_terminal_packet_witness_v1` 已完成3py AST、小代码安全部署、一次纯检查、首次冻结与全部426源串行测量。Linux `CAMPAIGN/native_terminal_packet_witness_v1` 保留全部源launch/terminal、注册、原始packet技术观测、失败与全聚合；没有重测成功source，没有frame decode/RGB/processor/model/GPU，没改旧clock或失败。

唯一测量自然exit0，CPU wall23.938770729117095s、process CPU23.241733171s、peakRSS68080KiB。全部原source byte/SHA实际匹配，hash读4,781,857,740B；同一个安全fd seek0后唯一AV open/demux，SHA+demux两逻辑pass预算9,563,715,480B均Linux内部，网络新增0。实际video payload统计保Linux，不假称两pass都是一次物理磁盘读。

421成功、5普通失败、0未尝试、0源身份fatal。416 CFR_LEGACY全部成功；10 NATIVE_PTS中5成功/5失败。成功须恰好一个压缩packet exact pts*timebase等于旧最后FRAME rawPTS，且等于该video最大display packetPTS，duration真实正值、payload大小一致并保packet SHA。新末端=(oldlastPTS-oldorigin)+actualpacketduration。10旧明确endticks继续严格核相等；416旧N/fps不作为physical、不要求新末端等名义值。无none/zero/ambiguous/maxPTS失败；5失败唯一类别为与旧显式endticks不相等。

5失败只读新保存观测的诊断，未再打开媒体/demux：

- IDs78/79/107，H264720×1280、timebase1/15360。旧末duration256tick=1/60，新PyAV17.1.0匹配packet duration512tick=1/30，newend-oldend=1/60。
- IDs122/159，同codec/尺寸、timebase1/11988。旧末duration200tick=50/2997，新packet400tick=100/2997，newend-oldend=50/2997。

全部5的source bytes/SHA、lastFRAME rawPTS、唯一最大displayPTS、positive packet duration及payloadSHA都满足，但旧endticks相等门失败保持。旧terminal evidence明确自称 `NATIVE_LAST_FRAME_PACKET_AND_DECORD_END`、原packet duration正值与原decord ends绑定。新PyAV字段是同字节源下另一个实际reader/API测量，不能据新值更长就宣布旧记录错误、改旧门或静默选择“更合适”的duration；当前只能陈述这组exact duration差异。此阶段没有新fullframePTS或实际frame.duration证明，未来第一次实际decode必须独立核全PTS/origin/count/geometry及positive last frame.duration与接受witness一致。5失败如何继续需主控明确新诊断/范围，不默认重扫全体或frame decode。

- 小control：9,766B，SHA256 `ba4bf9605e52b5b3633ad69704beac1910e4f18d17ddeaca459cac65a77dfbb9`；CRC/5安全成员/memberSHA/AST通过。
- code manifest SHA256 `776283dab4047973188fce1266dd399b8300f6c8bb7fa70f4a5d5cf205c75a2d`。
- 首次pure SHA256 `c90bf86621318f68c00c76cc9816233ea9d247f108aa85bc0bb9550c0d1faccb`。
- registration SHA256 `9b77b2dd03d94dcdb0de8a5c9f0dc858bc138968048d2b9a7dba5e7b03c8ad5e`。
- Linux全completion：105017B，SHA256 `4b753f82a818c7c10c1bc0545902e4f11b473f47bca700f01b1b2a695b82dc79`。
- `technical_summary_01.json`：1578B，SHA256 `93df2ab2b4606ae6230479cb8508f13457445a7925ea8a51501f985edd6483b2`；仅此小回执回Windows且大小/SHA一致。
- Linux `failed_native_terminal_diagnosis_01.json`：13229B，SHA256 `e32a2738e5950403ddd4248872c11ab77933c178386d13ccbce12142ef8c12dd`，逐源技术字段留Linux。

这不是完整frame-clock重跑、模型输入/质量/正式生产PASS。旧D8早已用normalized窗口与exact native membership生成122050帧框并验收，不能把本次新contract terminal接入失败泛化为旧D8是假clock。主控与source owner负责独立D8normalized数学、新输入和实际生产准入；本模块没有读取测试预测、标签、GT或评分。
