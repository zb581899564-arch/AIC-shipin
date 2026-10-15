# 冻结生产图的 deadline 吞吐审查

结论：截至 23:35:33Z，按原 v2 缓存提交与生命周期实现继续，完成全部生产、首次 QA 和最多五包的时间证据不足；最近真实提交节奏更支持超时风险。GPU 本身有完成余量的可能，最危险的是串行大张量缓存提交与后续生命周期重复解码，不能用十个 CPU 子进程当作十倍吞吐。

deadline 为 2026-10-14T11:56:40Z，CONTROL5 于前日 23:18:24Z 开始。一次只读费用元数据核实冻结图：426 source、521 window、665 event、1995 logical；实际 1328 endpoint + 664 VERIFY = 1992 MODEL，49 次加载。每批 calls 为 15..105，中位 36。没有按预测或质量改变批次/角色。

| 已有真实费用 | charged wrapper | 纯 generation |
|---|---:|---:|
| TIME37 | 487.9427 秒 | 129.3876 秒，平均 3.497 秒 |
| VERIFY20 | 301.0598 秒 | 59.4383 秒，平均 2.972 秒 |

旧 TIME CPU37 的逐 request wall 合计 371.856 秒，平均 10.050 秒；其中普通 processor 合计 71.710 秒。上述 GPU resource 分别是 RUN/controller/aic20h_charades_dev37_time_boundary_20261014_v1.resource.json 和 aic20h_charades_dev20_original_b_verify_20261014_v1.resource.json。cold load、缓存 I/O、身份签名没有独立时钟，charged 减 generation 只能称合并 overhead，不能捏造加载实测。

按旧 charged/call 分角色直接外推，GPU 约 27508 秒（7.64 小时），纯 generation 仅约 6617 秒（1.84 小时）。这是工程参考，不是保证：新完整 before/after 身份哈希、LUT 加载和 CPU I/O 竞争不同；49 个混合批也比将两个旧作业简单按 call 倍增更少冷加载。规划可考虑约 7..10 小时的 GPU 占用情景，不能把它称实测上下界。冻结保守 max 为 68580 秒（19.05 小时），另有累计 queue ceilings 5880 秒；这些上界明显不能证明剩余约 12.35 小时可完成。

只读 mtime/journal 快照：35 个 CPU proof 文件、10 个 source completion、source failure=0；第一个 GPU wrapper 已 BEGIN，尚无 COMPLETE。首 CPU proof mtime 23:19:13，最新 23:35:16。最近十个完成间隔合计 317.800 秒、平均 31.780 秒；若该节奏持续，剩余 1957 次准备单独约 17.28 小时。初始 imports/decode/RGB 成本不能线性外推，但这个最近区间已足以否定无证据的“肯定够时”。同一首次 END CPU proof request_wall=104.190 秒，含等待和 codec，不能当作锁持有时间；其 logical tensor 286.478 MB，实际永久 payload 20.847 MB，压缩比只是单例，不是全生产 fit 保证。

锁的具体影响：

- SOURCE save_input 的全局 flock 覆盖视觉 key、LUT packing/完整 roundtrip、写 gzip、加载比较和最终完整字典再重建。不同 source 的 decode/processor 可并行，这个昂贵 commit 阶段仍串行。
- first_input_replay 的 canonical load、RGB/普通 processor 重放、proof 写入不持该 flock；GPU load_input 也不持锁。两者仍与写入竞争磁盘、CPU 和内存带宽，不能说首次 QA 直接锁住 GPU。
- accept_consumer 在锁内 load_input；release_rgb 的 _closure 再对每 consumer load_input。所有 1992 个输入在首次独立输入/output QA 之后，额外约 3984 次大张量重建被放在同一串行锁中。已有单 236 MB probe 的 load+compare 为 5.287 秒，乘法量级约 5.85 小时；这不是生产实测持锁时间，但明确指出高价值冗余。SOURCE 的 store roundtrip 比该 probe 还有更多检查，不能反向以单例 8.940 秒 pack/write/load 证明整批够时。

不改冻结协议的现有调度应继续使用自然 complete 后的独立 QA、全 source 同批和双缓冲。依据实际峰值/当前容量分配 CPU；保留 GPU/QA 的资源余量，避免把更多尚未 commit 的大数组同时堆在锁外。不得通过重分批、少做 consumer、跳 QA 或重复模型救时间。后续首次真实 GPU completion/完整批 QA 会提供更可靠周转数据，读取它们即可，无需新 timing probe。

值得独立登记、只作用于未来未成功节点的基础设施优化：优先让生命周期仅核实际 canonical manifest/private/visual 文件的大小与 SHA、完整 signature 与已成功首次 input/output/GPU proof 的一致性，保留自然 ledger、retained refs、RGB SHA/inode、全部 consumer、append-only release 门；不在 accept/release 再做 Torch 解码。若生产提交仍约 32 秒，则生命周期优化单独不保证救回 deadline。其次可设计新独立 writer，将唯一输入的 LUT 打包/完整 exact roundtrip 放在锁外安全临时文件，锁内完成不可变视觉 exact 去重和首次 commit；必须解决同视觉竞争、失败临时文件保留、原 dtype/stride/alias/fullbytes 和 canonical SHA，不得热改 v2 或重做已成功/已经开始的 source 输入。此项实现和新注册有时间成本，不能未经 root 准入切换。

封包的八臂与优先顺序已固定，最多五个实际 canonical 不同结果。binder 明确等待 CONTROL5 全体 global PASS 与 controller 自然 PASS 后才写包根；MODEL 与三个 structural 分母闭合，旧 source field、七项 clock witness、历史 canonical selectors 和 payload 原 SHA 均绑定，未见当前额外接口阻塞。尚未生成实际 binding/config/admission，所以不能说封包准备已验收。renderer 会一次遍历完整锁并哈希 canonical payload、旧模型等文件；约 50 GB tensor 只是规划量级，扫描速度未测，仍需加上字段/组合、11strict、最多五次 ZIP 验收及最后传输的尾部时间。不得把这段预算吞掉，也不得因此删 canonical 或旧成功。

本轮仅从既有小费用元数据取数字、读取成功文件 mtime 与 controller journal；未读正式预测内容、媒体/RGB/tensor/权重体，未导入 framework、运行模型/processor/解码、重复旧 pure 或改变冻结生产。
