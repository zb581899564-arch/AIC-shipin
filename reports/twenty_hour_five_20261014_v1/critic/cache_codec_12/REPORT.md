# Cache v2 新锁交付回执

已完成独立 `improvement/production_stream_cache_v2`，只改运行模块 `codec.py` 的 process lock 和 `__init__.py` 导出的 backend 标识。`leases.py`、`pixel_dictionary.py` 与 v1 字节一致；v1、旧 codec 检查和所有旧成功产物保持。

canonical schema 仍为 `PRODUCTION_EXACT_STREAM_CACHE_V1`。新 policy 必须声明 `process_lock_backend: "LINUX_PERSISTENT_FLOCK_V2"`。公共 Store/LeaseStore API、精确完整输入 tensor/tokenmask/metadata 保存、视觉实际 bytes 与身份去重、首次独立 proof、自然 GPU terminal、全冻结 consumer graph、canonical SHA 和 append-only RGB release 门均不变。仅新注册的 `production_stream_vN` 使用，不补改旧 policy，不混用 v1/v2 writer。

Linux 固定空 guard inode 使用 `fcntl.flock(LOCK_EX)`；逐祖先 dir-fd/O_NOFOLLOW、regular/nlink=1、等 inode 检查防止链接逃逸与等待期间 inode 替换。context 退出或异常只解锁并关 fd，不 unlink/rename guard，不改 PID 内容。guard 永久存在是正常状态。锁非 reentrant，持锁时不得再调用内部加锁 API 或 fork。事务外 CPU 准备和独立 replay 可并行；同 root canonical/租约变更互斥，读者仍需完整 prepare/commit barrier。

本次唯一 Linux 检查在 `CAMPAIGN/cache_codec_12/synthetic_01`，两个 worker 自然 exit0：B 在 A 持锁期间阻塞，A 在 context 内抛出预期异常后 B 正常进入；同一 guard inode 在两进程和后续获取中保持；symlink/hardlink guard 拒绝，新 synthetic sentinel 未改。检查未 import Torch，不重复旧 codec 全检查，不读取真实媒体/旧 cache，不 processor/model，不释放真实或 synthetic RGB。

- code manifest SHA256：`79a73a2c13921e0257192841ba40f5ee96e5905a8b02d82080821049254e2c7e`。
- 新 codec SHA256：`bc0489c3365ddd0b5949bec093b330a27fb7277172edd62298f1634eaaebed1c`。
- Linux 首次检查 receipt SHA256：`f2c3241006893b8acfae8308f972cdda0a1677d0407717d57ad1258d83f9afd8`；本地小回执字节相同。
- 18,163B 小代码包 SHA256：`dba1719c5736b60eff759e7f7605aebfc94685482c27208b464093fb9db31e47`；Linux 安全成员、CRC、成员 SHA、AST 完成。

合成部署代码在 `CAMPAIGN/cache_codec_12/code`。实际生产 code root、policy、controller/worker 同版本 SHA 和首次 source gate 由主控另行注册，不据此自动准入生产。互斥不证明全局 CPU pool、永久累计容量或 20h 时限已经可行；资源按实时容量和实际 batch 峰值决定，不够则 STOP retain，不降精度或删 canonical。
