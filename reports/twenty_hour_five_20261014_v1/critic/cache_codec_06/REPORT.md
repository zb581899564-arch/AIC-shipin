# 新独立 exact cache 模块回执 06

实现为 `improvement/production_stream_cache_v1`：`codec.py` 完整永久 tensor manifest/视觉去重，`leases.py` 冻结 RGB 消费者图和 append-only 生命周期，`pixel_dictionary.py` 可选精确 raw-bit LUT 存储编码。没有 producer、processor/model、GPU launcher 或大生产入口，不改旧 v2/Charades/成功文件。

生产根只准当前 campaign 下新 `production_stream_vN` 和事前主控新政策。全局 consumer/RGB lease 图在模型前冻结，每个 consumer 恰好对应一个原 RGB lease；租约 SHA 与首次登记 journal 绑定，篡改或遗漏消费者会阻断释放。canonical/proof/raw/resource/ledger 全部保留，新 RGB release 只限严格相对 staging/rgb 路径，历史 path/SHA 保留，释放实际状态另追加。Linux 逐级 O_NOFOLLOW FD 相对 unlink，旧 root/外部路径/symlink/junction/reparse 不接受。

纯验证分阶段保存，不重复旧成功材料：

| 回执 | 实际覆盖 |
| --- | --- |
| `synthetic_result_01.json` | CPU bfloat16 非连续 stride、完整 token/mask exact gzip；共享实际视觉 bytes、保留不同 text；origin 不同不共享；双消费者租约、失败/重复 ledger、旧路径拒绝；一次新 synthetic RGB 释放后 canonical 可读；容量不足 STOP_RETAIN。Windows symlink 权限1314明确 SKIP |
| `linux_safety_completion_01.json` | 新 Linux fixture 的 symlink 文件/祖先拒绝、旧 root 不读、canonical 缺失阻断、O_NOFOLLOW 相对 unlink、外部 sentinel 不变；CUDA未初始化，真实媒体/processor/model/production 0 |
| `linux_contract_additions_completion_02.json` | 冻结 RGB 图缺失、遗漏/重复消费者、逃逸路径拒绝；租约消费者被篡改为空时按原 lease SHA 阻断，追加释放0 |
| `final_import_03.json` | package/direct import 与 AST；import 不加载 torch/CUDA。后续可选 LUT 增量另有独立回执 |
| `dictionary_synthetic_result_04.json` | 三块各256值 exact；257值及不支持 stride fallback；NaN payload/signed-zero bit exact；token/mask 原格式保留 |
| `dictionary_actual_completion_05.json` | 唯一授权 completed-smoke start tensor 全数组 exact 存储 roundtrip；原文件body读1次，没有RGB/processor/model/原写删 |

实际 smoke 编码：pixel `[38400,1536]` float32，三等分各256原bit值。原像素 payload235,929,600B → 索引/LUT58,985,472B。完整逻辑输入236,113,128B，旧 gzip40,216,453B → 新 gzip26,505,640B（比值0.6590745335）。pack2.493s/write1.161s/load+compare5.287s，峰RSS1,237,940KiB。所有 key/dtype/shape/stride/alias/bitbytes恢复 exact；没有改变模型精度。这个单来源比率不保证426生产 fit，overflow/unsupported仍原gzip，后续实际批次容量不足 STOP_RETAIN。

新真实 probe 全留Linux `/home/inspur/aic_video_work/twenty_hour_five_20261014_v1/cache_codec_06/dictionary_actual_probe_01`；回传只有小回执。当前代码是新 schema，旧 v1/v2 loader 不支持字典文件，不能直接替换旧缓存。后续真实生产仍需主控批准独立协议、完整 source/request/batch 表、资源预算和真实独立 replay 实现。
