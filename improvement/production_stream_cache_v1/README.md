# Exact stream cache v1

纯缓存库，没有 producer、视频解码、processor/model、GPU launcher 或生产入口。

`codec.Store` 保存完整实际 CPU encoded dict，视觉 payload 可无损共享，文本 token/mask 及所有其他输入仍永久保存。共享键含 source SHA、64 有序 ordinals/精确 PTS、context origin、实际 grid、processor assets/preprocessing code；还读回比较真实 tensor 字节。保留 dtype、shape、stride、storage offset 和 alias groups。跨视觉/文本 storage alias 的输入保留完整 dict，不分拆。

`leases.LeaseStore` 分开永久输入锁和新 RGB staging lease。生产根只接受当前 campaign 下新的 `production_stream_vN` 目录及事前主控政策，旧 root、绝对/逃逸 staging 路径和 symlink/junction/reparse 均拒绝。全局 policy 在首模型结果前声明完整 consumer 表及每个 RGB 的全部消费者；分批物化不能改成员。所有证明和 ledger/resource 快照都放在新永久根，路径/SHA 校验后才接受。

生产 proof schema 为 `CACHE_FIRST_INDEPENDENT_REPLAY_ACCEPTANCE_V1`：首次独立正常 processor 从原 RGB 重放、完整 CPU/GPU tensor 签名、token/grammar/parser/native 校验、不同 prepare/verifier PID、冻结独立重放代码 SHA、实际 raw 调用，以及唯一自然 completed/exit0 resource 对应 ledger。库校验这些已接受证据的绑定，不自行生成实际证明或声称质量通过。synthetic 回执无法授权生产释放。

每个 RGB 的所有冻结消费者通过且全部相关 canonical/proof/raw 文件 SHA 仍存在时，先追加 release intent，再仅 unlink 已登记的本轮 staging 文件，最后追加真实 released 回执。Linux 通过逐级 `O_NOFOLLOW` 目录 FD 的相对 unlink 拒绝逃逸。未闭合或失败保留，成功释放不可重复；intent 后中断需要明确恢复。历史 input metadata 的 RGB path/SHA 保留，不假称文件仍存在。canonical 永久不删。

`capacity` 只比较调用者提供的当前下一阶段保守字节需求与实时空间，容量不足返回 `STOP_RETAIN_ALL`。它不据压缩比推断 fit，不自动降低精度、删除 canonical 或启动生产。

可选 `policy.input_storage_codec=PIXEL_UINT8_BIT_LUT_V1` 仅为存储编码：CPU float32 二维 `pixel_values_videos` 的 lastdim 三等分，实际每块 raw uint32 bit pattern 不超过256时保存 uint8 索引和原始 bit LUT；恢复 float32 后核完整签名/字节。超过256、非标准 stride/offset、共享 storage alias、其他 dtype/shape 均明确保留原 torch/gzip，不强 cast。不改变实际模型输入精度。新 manifest 的 tensor ref 记录 codec/report，必须用本库重组；旧 v1/v2 的直接 torch dict loader 不支持此新文件，不能替换其已有缓存。

纯测试证据保存在 `reports/twenty_hour_five_20261014_v1/critic/cache_codec_06`。Windows 测试验证 exact codec、共享/不共享、租约、ledger、容量；Windows 无 symlink 特权，保留 SKIP。Linux 专用新 fixture 验证 symlink 文件/祖先拒绝、canonical 缺失阻断和安全 unlink；CUDA 未初始化，真实媒体/processor/model/production 均 0。后续生产前仍需主控冻结真实协议、输入计划和独立重放实现；本库不是生产准入。

已授权单 completed-smoke start tensor 全数组 probe：逻辑236,113,128B，原gzip40,216,453B，新精确 LUT/gzip26,505,640B。三块均256个bit值，完整dict exact恢复。只读该原文件body一次，没有RGB/processor/model/原写删；结果仅该smoke，不保证生产fit。新probe仅留Linux独立 `cache_codec_06/dictionary_actual_probe_01`。
